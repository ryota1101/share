以下は **非同期 FastAPI サーバ（`async` 必須）** として、**Azure OpenAI / AWS Bedrock (Claude) / GCP Vertex AI (Gemini)** のストリーミングを受け取り、フロントエンドに逐次（トークン単位やチャンク単位で）返す「実運用に近い実装例」です。
各プロバイダの違いに合わせて実装しています（`httpx` の async ストリーム、`boto3` / Bedrock の同期ストリームをスレッド経由で非同期に渡す、Vertex の SDK をスレッドで回す）。

重要な注意点・前提（ざっくり）：

* Azure OpenAI：`stream=True` → サーバーが SSE（`data: ...`）チャンクで送る。([Microsoft Learn][1])
* AWS Bedrock：`InvokeModelWithResponseStream` / `ConverseStream` がストリーミングを返す（`application/vnd.amazon.eventstream`）。boto3 は同期APIでストリームイベントを返す。([AWS ドキュメント][2])
* GCP Vertex：Chat Completions で `stream=True` を使える（OpenAI互換のクライアント例など）。([Google Cloud][3])

---

# 目次

1. 実装コード（`main.py` — FastAPI）
2. フロントエンド受信の簡単な例（fetch + ReadableStream）
3. 説明・動作ポイント・環境変数／依存ライブラリ
4. 補足（エラー・スケーリング・セキュリティ）

---

# 1) FastAPI 実装（`main.py`）

> ファイル `main.py` を作って以下を貼り付けてください。

```python
# main.py
import os
import json
import asyncio
import threading
from typing import Any, Dict, List, Optional, AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Optional OpenAI lib for Vertex pattern (the Vertex sample used openai.OpenAI)
# pip install openai
try:
    from openai import OpenAI as OpenAIClient  # new OpenAI python SDK
except Exception:
    OpenAIClient = None

app = FastAPI()

# ---------- Config via ENV ----------
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")  # e.g. https://your-resource.openai.azure.com
AZURE_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT")  # deployment name
AZURE_API_VERSION = os.environ.get("AZURE_API_VERSION", "2023-11-15-preview")
AZURE_API_KEY = os.environ.get("AZURE_API_KEY")

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
# For Bedrock, you should have AWS credentials in env or IAM role

GCP_PROJECT = os.environ.get("GCP_PROJECT")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")  # often us-central1

# ---------- Request model ----------
class ChatRequest(BaseModel):
    messages: Optional[List[Dict[str, Any]]] = None  # OpenAI-like messages
    prompt: Optional[str] = None  # for providers that accept prompt
    model: Optional[str] = None
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.2

# ---------- Helpers to extract readable text from provider events ----------
def extract_text_from_openai_chunk(chunk: Dict[str, Any]) -> str:
    """
    Best-effort extraction for 'delta' / 'choices' style chunks (OpenAI/Azure/Vertex).
    """
    out = []
    try:
        choices = chunk.get("choices") or []
        for c in choices:
            # standard streaming: choice.delta.content
            delta = c.get("delta", {})
            if isinstance(delta, str):
                out.append(delta)
            else:
                if isinstance(delta, dict):
                    cnt = delta.get("content") or delta.get("text")
                    if cnt:
                        out.append(cnt)
                # older style might have 'text' at top-level
            # sometimes 'text' or 'output_text'
            if not out:
                if "text" in c:
                    out.append(c["text"])
        # fallback: top-level 'text' / 'outputText'
        if not out:
            if "text" in chunk:
                out.append(chunk["text"])
            if "outputText" in chunk:
                out.append(chunk["outputText"])
    except Exception:
        pass
    return "".join(out)

def deep_collect_strings(value):
    out = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            out.extend(deep_collect_strings(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(deep_collect_strings(v))
    return out

def extract_text_from_generic(obj: Any) -> str:
    """
    Generic fallback: scan object for plausibly human text fields and join them.
    """
    pieces = deep_collect_strings(obj)
    return "".join(pieces)

# ---------- Azure OpenAI (async via httpx) ----------
async def azure_stream_generator(req: ChatRequest) -> AsyncGenerator[str, None]:
    if not (AZURE_ENDPOINT and AZURE_DEPLOYMENT and AZURE_API_KEY):
        raise RuntimeError("Azure OpenAI config missing")
    url = f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_API_VERSION}"

    payload = {
        "messages": req.messages or ( [{"role":"user","content": req.prompt}] if req.prompt else [] ),
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "stream": True,
    }

    headers = {
        "api-key": AZURE_API_KEY,
        "Content-Type": "application/json",
    }

    # Use httpx async stream
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as r:
            if r.status_code >= 400:
                body = await r.aread()
                raise HTTPException(status_code=502, detail=f"Azure OpenAI upstream error: {r.status_code} {body[:200]!r}")
            async for raw_line in r.aiter_lines():
                # Azure/OpenAI SSE lines typically look like: "data: {json}"
                if not raw_line:
                    continue
                if raw_line.startswith("data:"):
                    data = raw_line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        text = extract_text_from_openai_chunk(chunk)
                        if not text:
                            # fallback: collect any strings
                            text = extract_text_from_generic(chunk)
                        if text:
                            # yield plain text (client's fetch reader expects plain bytes)
                            yield text
                    except json.JSONDecodeError:
                        # if not json, yield raw
                        yield data
                else:
                    # sometimes provider can send raw json chunk
                    try:
                        chunk = json.loads(raw_line)
                        text = extract_text_from_openai_chunk(chunk) or extract_text_from_generic(chunk)
                        if text:
                            yield text
                    except Exception:
                        yield raw_line

# ---------- AWS Bedrock (sync boto3 stream wrapped to async via thread + queue) ----------
async def bedrock_stream_generator(req: ChatRequest, model_id: str) -> AsyncGenerator[str, None]:
    """
    Uses boto3.client('bedrock-runtime').invoke_model_with_response_stream or converse_stream.
    boto3 currently is sync, so we run it in a thread and shuttle events via asyncio.Queue.
    """
    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def worker():
        try:
            client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
            # Build native request depending on model. Many Bedrock text models accept:
            # {"inputText": "...", "textGenerationConfig": {...}}
            if req.prompt and not req.messages:
                native = {
                    "inputText": req.prompt,
                    "textGenerationConfig": {"maxTokenCount": req.max_tokens, "temperature": req.temperature},
                }
                body = json.dumps(native)
                resp = client.invoke_model_with_response_stream(modelId=model_id, body=body)
            else:
                # Some models support a messages-like "ConverseStream"
                # We'll attempt ConverseStream if messages provided and API supports it
                # Format conversion depends on model. Here we fallback to invoke_model_with_response_stream with inputText.
                input_text = ""
                if req.messages:
                    # flatten messages into simple prompt
                    input_text = "\n".join([f"{m.get('role','user')}: {m.get('content','')}" for m in req.messages])
                else:
                    input_text = req.prompt or ""
                native = {"inputText": input_text, "textGenerationConfig": {"maxTokenCount": req.max_tokens}}
                body = json.dumps(native)
                resp = client.invoke_model_with_response_stream(modelId=model_id, body=body)
            stream = resp.get("body")
            if stream:
                for event in stream:  # boto3 yields event dicts
                    # events can contain 'chunk' items containing bytes
                    chunk = event.get("chunk")
                    if chunk:
                        # chunk may have 'bytes'
                        b = chunk.get("bytes")
                        if b:
                            try:
                                s = b.decode("utf-8")
                            except Exception:
                                s = None
                            if s:
                                # Many events contain JSON text in the bytes, try parse -> extract
                                try:
                                    parsed = json.loads(s)
                                    text = extract_text_from_generic(parsed)
                                    if not text:
                                        text = s
                                except Exception:
                                    text = s
                                # put into async queue
                                loop.call_soon_threadsafe(q.put_nowait, text)
                    # other event types may include 'response', 'error' etc. we can handle if needed
        except Exception as e:
            loop.call_soon_threadsafe(q.put_nowait, f"[bedrock_error]{str(e)}")
        finally:
            loop.call_soon_threadsafe(q.put_nowait, None)  # sentinel

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    while True:
        chunk = await q.get()
        if chunk is None:
            break
        yield chunk

# ---------- Vertex AI (Google) streaming -- using OpenAI-like SDK pattern (wrapped in thread) ----------
async def vertex_stream_generator(req: ChatRequest, model: str) -> AsyncGenerator[str, None]:
    """
    Vertex sample from Google docs uses an OpenAI-compatible wrapper (OpenAI client pointing to Vertex endpoint).
    The OpenAI client is typically sync; we wrap in a thread and pass chunks via asyncio.Queue.
    """
    if OpenAIClient is None:
        raise RuntimeError("OpenAI SDK not installed. Install with: pip install openai")

    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def worker():
        try:
            # fetch ADC credentials and token via google.auth (but sample uses OpenAI wrapper with token)
            # For simplicity, assume user set GOOGLE_APPLICATION_CREDENTIALS or ADC and we get token programatically.
            # Here we construct base_url to talk to Vertex OpenAI-compatible endpoint:
            project = os.environ.get("GCP_PROJECT") or GCP_PROJECT
            location = os.environ.get("GCP_LOCATION") or GCP_LOCATION
            if not project or not location:
                loop.call_soon_threadsafe(q.put_nowait, "[vertex_error] GCP_PROJECT/GCP_LOCATION not set")
                loop.call_soon_threadsafe(q.put_nowait, None)
                return

            # Acquire access token via google auth
            try:
                import google.auth.transport.requests
                from google.auth import default as google_auth_default
                creds, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                creds.refresh(google.auth.transport.requests.Request())
                access_token = creds.token
            except Exception as e:
                loop.call_soon_threadsafe(q.put_nowait, f"[vertex_error] failed to get ADC token: {e}")
                loop.call_soon_threadsafe(q.put_nowait, None)
                return

            # Build OpenAI client pointing to Vertex endpoint (OpenAI-compatible path)
            base_url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/endpoints/openapi"
            client = OpenAIClient(base_url=base_url, api_key=access_token)

            # call chat completions with stream=True (sync iterator)
            messages = req.messages or ([{"role":"user","content": req.prompt}] if req.prompt else [])
            model_used = model or req.model or "google/gemini-1.5"  # user-supplied
            resp_iter = client.chat.completions.create(model=model_used, messages=messages, stream=True)
            for chunk in resp_iter:
                # chunk is usually a dict-like structure
                try:
                    text = extract_text_from_openai_chunk(chunk) or extract_text_from_generic(chunk)
                    if text:
                        loop.call_soon_threadsafe(q.put_nowait, text)
                except Exception:
                    loop.call_soon_threadsafe(q.put_nowait, json.dumps(chunk))
        except Exception as e:
            loop.call_soon_threadsafe(q.put_nowait, f"[vertex_error]{e}")
        finally:
            loop.call_soon_threadsafe(q.put_nowait, None)

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    while True:
        chunk = await q.get()
        if chunk is None:
            break
        yield chunk

# ---------- FastAPI endpoints ----------
@app.post("/stream/azure")
async def stream_azure(req: ChatRequest):
    gen = azure_stream_generator(req)
    # Return plain text chunks to client (front-end can use fetch().body.getReader())
    return StreamingResponse(gen, media_type="text/plain; charset=utf-8")

@app.post("/stream/bedrock")
async def stream_bedrock(req: ChatRequest):
    # The model id must be provided as query param or in req.model
    model_id = req.model or "anthropic.claude-v2"  # default example
    gen = bedrock_stream_generator(req, model_id)
    return StreamingResponse(gen, media_type="text/plain; charset=utf-8")

@app.post("/stream/vertex")
async def stream_vertex(req: ChatRequest):
    model = req.model or "google/gemini-2.0-flash-001"
    gen = vertex_stream_generator(req, model)
    return StreamingResponse(gen, media_type="text/plain; charset=utf-8")
```

---

# 2) フロントエンド（Next.js）の受信サンプル

フロント側は `fetch` の `response.body.getReader()` を使って、来たチャンクをそのまま append すれば「ChatGPTのような流れる文字」が得られます。

```tsx
// React (client component) - 例
"use client";
import { useState } from "react";

export default function StreamTest() {
  const [text, setText] = useState("");

  async function callAzure() {
    setText("");
    const body = { prompt: "日本語で自己紹介してください。" };
    const res = await fetch("/stream/azure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.body) return;
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      setText((s) => s + chunk);
    }
  }

  return (
    <div>
      <button onClick={callAzure}>Azureでストリーム</button>
      <pre style={{ whiteSpace: "pre-wrap" }}>{text}</pre>
    </div>
  );
}
```

> フロント側は `text/event-stream`（SSE）で受け取る方法（`EventSource`）でも可能ですが、今回のバックエンドは**プレーンなテキストチャンク**を返すので `fetch` + `getReader()` がそのまま使えます。

---

# 3) 補足・動作ポイント（重要）

* **非同期化の理由**：多数の同時接続で I/O 待ち（ネットワーク）を効率的に扱うため。
  Azure のように `httpx.AsyncClient` が使える先は完全 async、boto3 や一部 SDK は同期実装なので **スレッドで回して asyncio.Queue に流す**パターンを採っています（上の実装）。([AWS ドキュメント][2])

* **プロバイダ別注意**：

  * Azure：SSE 形式（`data: ...`）でチャンクが来ます。`data: [DONE]` で終了。([Microsoft Learn][1])
  * Bedrock：`invoke_model_with_response_stream` や `converse_stream` が使える（出力は Amazon event stream）。boto3 のストリームイベントをループで取得して処理します。([AWS ドキュメント][2])
  * Vertex：OpenAI互換の client を用いて `stream=True` でイテレータを受け取るパターンが公式サンプルにあります。([Google Cloud][3])

* **セキュリティ**：API キーは絶対にフロントに出さない。上のコードはサーバ側でAPIキー／認証を保持します。

* **エラー処理**：上の実装は基本形です。実運用では client disconnect の検知、タイムアウト、トークン消費計測、ログ、メトリクスなどを追加してください。

* **フォールバック**：あるモデルが streaming をサポートしない場合は同期レスポンスを扱う必要あり（`invoke_model` など）。

---

# 4) 実行・依存

* 必要ライブラリ（例）:

```
pip install fastapi uvicorn httpx boto3 openai google-auth
```

* 環境変数（例）:

```
export AZURE_OPENAI_ENDPOINT="https://your-azure-resource.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="your-deployment"
export AZURE_API_KEY="sk-..."
export AWS_REGION="us-east-1"
export GCP_PROJECT="your-gcp-project"
export GCP_LOCATION="us-central1"
# AWS creds via env or IAM role
# GCP credentials via GOOGLE_APPLICATION_CREDENTIALS or ADC
```

* 起動:

```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

# 5) 最後に（実運用への注意点）

* Bedrock / Vertex は**SDKのバージョンやモデルID、エンドポイント仕様が変わる**ことがあるため、最新ドキュメントを追ってください（上で使った API 名は公式ドキュメントのサンプルに基づいています）。([AWS ドキュメント][2])
* ストリーミング中にユーザーが「中断」した場合（ブラウザを閉じる等）、サーバが検知してバックエンド接続（LLM）をキャンセルする仕組みがあるとコスト効率が良いです（リクエストのキャンセレーション管理）。
* 高負荷を想定するなら、**ワーカー数（uvicorn/gunicorn/ASGI worker）とスレッドプール／キュー設計**を慎重に。

---

# 参考（ドキュメント）

* Azure OpenAI — Content streaming / chat completions (stream=True). ([Microsoft Learn][1])
* Amazon Bedrock — `InvokeModelWithResponseStream` / `ConverseStream` streaming examples (boto3). ([AWS ドキュメント][2])
* Google Vertex AI — Chat Completions streaming sample (OpenAI-compatible usage). ([Google Cloud][3])

---

必要なら、次は **(A)** あなたの実際のモデルID・エンドポイントを埋めた `docker-compose` でのデプロイ例、**(B)** フロント側で途中キャンセル（ユーザーが stop を押したとき）の仕組み、**(C)** 生成中に部分的にDBへ書き出して履歴を即時表示するやり方（SSR/CSRF対策含む）を詳述できます。どれが優先で欲しいか言ってください — すぐコードを書きます。

[1]: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/content-streaming?utm_source=chatgpt.com "Content Streaming in Azure OpenAI | Microsoft Learn"
[2]: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-invoke.html "Submit a single prompt with InvokeModel - Amazon Bedrock"
[3]: https://cloud.google.com/vertex-ai/generative-ai/docs/samples/generativeaionvertexai-gemini-chat-completions-streaming "Generate streaming text by using Gemini and the Chat Completions API  |  Generative AI on Vertex AI  |  Google Cloud"
