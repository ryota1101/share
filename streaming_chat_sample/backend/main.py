from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from pathlib import Path

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ここを ["http://192.168.11.3:3000"] に限定してもOK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ダミーデータを読み込む関数
def load_text_file(filepath: str) -> str:
    file_path = Path(filepath)
    if not file_path.exists():
        return "## Dummy file not found\nPlease create a markdown or text file."
    return file_path.read_text(encoding="utf-8")


# 非同期ジェネレータでテキストをチャンクに分けて返す
async def stream_text(filepath: str, chunk_size: int = 30, delay: float = 0.1):
    text = load_text_file(filepath)
    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        yield chunk
        await asyncio.sleep(delay)  # 擬似的に遅延を入れてChatGPT風にする


@app.post("/stream/dummy")
async def stream_dummy():
    filepath = "dummy.md"  # 適当なテキスト or マークダウンファイル
    return StreamingResponse(
        stream_text(filepath),
        media_type="text/plain; charset=utf-8"
    )
