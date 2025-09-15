* MCPサーバーなしで、**ツールを独立モジュール化**
* **main側では「ツールセット」を選ぶだけで LLM 呼び出しができる**
* **新しいツールを追加しても main の修正を最小限にしたい**

つまり「ツール管理レイヤー」を作って、main は **ツールセットを指定して LLM を呼ぶだけ** にするイメージです。

---

## 🔹 ディレクトリ構成例

```
project/
├─ tools/
│   ├─ __init__.py
│   ├─ sharepoint.py
│   ├─ news.py
│   ├─ tech_docs.py
│   ├─ patents.py
│   ├─ papers.py
│   ├─ web.py
└─ main.py
```

* `tools/` に各ツールの関数 + schema をまとめる
* `tools/__init__.py` で **ツールを自動登録** → main 側はセット名を選ぶだけ

---

## 🔹 例: 各ツール

### `tools/tech_docs.py`

```python
# tool(関数)を作成する
def tech_docs_search(query: str) -> str:
    return f"[社内技術文書検索結果] {query} に関する情報です。"

# LLMに渡すためのスキーマを定義
tech_docs_schema = {
    "type": "function",
    "function": {
        "name": "tech_docs_search",
        "description": "社内技術文書を検索する",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    }
}
```

### `tools/papers.py`

```python
def papers_search(query: str) -> str:
    return f"[外部論文検索結果] {query} に関する論文です。"

papers_schema = {
    "type": "function",
    "function": {
        "name": "papers_search",
        "description": "外部論文を検索する",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    }
}
```

---

## 🔹 `tools/__init__.py` で自動管理

```python
from . import sharepoint, news, tech_docs, patents, papers, web

# ツール登録用 dict
ALL_TOOLS = {
    "sharepoint": (sharepoint.sharepoint_search, sharepoint.sharepoint_schema),
    "news": (news.news_search, news.news_schema),
    "tech_docs": (tech_docs.tech_docs_search, tech_docs.tech_docs_schema),
    "patents": (patents.patent_search, patents.patent_schema),
    "papers": (papers.papers_search, papers.papers_schema),
    "web": (web.web_search, web.web_schema),
}

# ツールセット
TOOL_SETS = {
    "tech_only": ["tech_docs", "papers"],
    "all": list(ALL_TOOLS.keys())
}

def get_tool_set(name: str):
    names = TOOL_SETS.get(name, [])
    return [ALL_TOOLS[n] for n in names]
```

---

## 🔹 `main.py` の呼び出し例

```python
from openai import OpenAI
from tools import get_tool_set

client = OpenAI(api_key="YOUR_API_KEY")

def generate_answer(user_query: str, tool_set_name: str):
    # 1. 選んだツールセットを取得
    tools = get_tool_set(tool_set_name)
    schemas = [s for _, s in tools]

    # 2. LLM呼び出し
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_query}],
        tools=schemas
    )

    msg = resp.choices[0].message
    result = None
    if msg.tool_calls:
        fn_name = msg.tool_calls[0].function.name
        args = eval(msg.tool_calls[0].function.arguments)
        # 呼び出し関数を検索
        fn_dict = {name: fn for fn, _ in tools}
        result = fn_dict[fn_name](**args)

    # 3. LLMに最終回答生成
    final_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": f"検索結果: {result}"}
        ]
    )
    return final_resp.choices[0].message.content

# 使用例
print(generate_answer("テレワーク規定を教えて", "tech_only"))
print(generate_answer("テレワーク規定を教えて", "all"))
```

---

## 🔹 ポイント

1. **ツール追加は tools/ にファイル作るだけ**
2. **main はツールセット名を渡すだけ** → 修正不要
3. **ツールセットごとに選択可能** → 特定ドメインに特化も簡単
4. **MCPサーバー不要**

   * 将来的にツール内の処理を API 化すれば他アプリでも使える

---

💡 まとめると、

* この構成なら **main の修正を極力減らしてツールを増やせる**
* かつ **特定ツールセットだけ選んで回答生成可能**

---

もしよければ、次のステップとして **この構成で「LLMがどのツールを呼ぶか自動で選択する function calling のフロー」** を追加したサンプルも作れます。
作ってほしいですか？
