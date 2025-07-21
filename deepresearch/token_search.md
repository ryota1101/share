はい、承知いたしました。現状の整理と今後の設計に関するヒントをまとめます。

---

### **現状の整理とトークン数取得に関する設計のまとめ**

現在、トークン数の計算と取得に関する全体像は以下のようになっています。

#### **1. トークン数を計算・保持する主体**

* **`CompletionUsage` クラス**:
    * これは、OpenAIなどのLLM APIが返すトークン使用量情報を格納するためのデータモデルです。
    * `prompt_tokens` (プロンプトのトークン数) と `completion_tokens` (モデルが生成した応答のトークン数) を持ち、これらを合計した `total_tokens` も含みます。
    * また、`__add__` メソッドを持つため、複数の `CompletionUsage` インスタンスのトークン数を簡単に合計することができます。
    * `from_openai` クラスメソッドを持つことから、OpenAIのAPIレスポンスに含まれる使用量情報をこのクラスのインスタンスに変換するために使用されることが意図されています。

* **`AzureAIInferenceChatCompletion` クラス (`ChatCompletionClientBase` の具体的な実装)**:
    * このクラスが、実際にAzure AI Inferenceサービスと通信を行い、LLMの応答を受け取ります。
    * `_inner_get_chat_message_contents` メソッド内で、Azure AI InferenceサービスのAPI (`self.client.complete`) を呼び出しています。
    * APIからの応答 (`response: ChatCompletions`) には、`response.usage` という形でトークン使用量情報が含まれています。
    * `_get_metadata_from_response` ヘルパーメソッド内で、この `response.usage` を使用して `CompletionUsage` オブジェクトを構築し、それを`"usage"`というキーで辞書 (`response_metadata`) に格納しています。
    * 最終的に、この `response_metadata` は、API呼び出しの戻り値である `ChatMessageContent` オブジェクトの `metadata` 属性にセットされます。

#### **2. トークン数を要求・利用する主体**

* **`StandardMagenticManager` クラス**:
    * このクラスは、オーケストレーションのロジック（計画、再計画、進行状況の作成、最終回答の準備など）を管理します。
    * 内部で `chat_completion_service` (インスタンス化された `AzureAIInferenceChatCompletion` のようなオブジェクト) を使用して、LLMとの対話を行います。
    * 具体的には、`plan()` や `replan()` などの各メソッド内で、`self.chat_completion_service.get_chat_message_content()` を呼び出してLLMからの応答を取得します。
    * `get_chat_message_content()` メソッドは `ChatMessageContent` オブジェクトを返します。

#### **3. トークン情報の流れとアクセス方法**

1.  `StandardMagenticManager` のメソッド (例: `plan()`) が `self.chat_completion_service.get_chat_message_content()` を呼び出す。
2.  `AzureAIInferenceChatCompletion` (具体的な `ChatCompletionClientBase` の実装) の `get_chat_message_content()` メソッドが `_inner_get_chat_message_contents()` を呼び出す。
3.  `_inner_get_chat_message_contents()` の中で、実際のAzure AI Inference API呼び出しが行われ、応答 (`response`) が返される。
4.  この `response` オブジェクトには、APIによって提供されるトークン使用量情報 (`response.usage`) が含まれている。
5.  `_get_metadata_from_response` メソッドが `response.usage` から `semantic_kernel` の `CompletionUsage` オブジェクトを生成し、`{"usage": CompletionUsage_object}` の形式で辞書に格納する。
6.  この辞書が `ChatMessageContent` オブジェクトの `metadata` 属性として設定され、`get_chat_message_content()` の戻り値として `StandardMagenticManager` に返される。
7.  したがって、`StandardMagenticManager` のメソッド内で、`get_chat_message_content()` の戻り値である `ChatMessageContent` オブジェクトの `metadata` 属性にアクセスすることで、**`response_object.metadata["usage"]`** の形で `CompletionUsage` インスタンスを取得できます。

#### **今後の設計に関するヒント**

1.  **トークン使用量の集計方法の決定**:
    * `StandardMagenticManager` の各LLM呼び出し (`plan`, `replan`, `create_progress_ledger`, `prepare_final_answer`) は、それぞれ独立したトークン使用量を持ちます。
    * これらのトークン使用量を**合計して追跡**するか、**各呼び出しごとの使用量を個別に記録**するかを決定する必要があります。
    * **提案**: `StandardMagenticManager` クラスに `total_completion_usage: CompletionUsage` のような属性を追加し、各LLM呼び出しの後に取得した `CompletionUsage` オブジェクトを `+=` 演算子で加算していくのが、最もシンプルで効果的な方法です。これにより、マネージャーインスタンスがそのライフサイクル中に消費した合計トークン数をいつでも参照できるようになります。

2.  **トークン使用量へのアクセスポイント**:
    * マネージャーの操作が完了した後（例: `plan()` メソッドが終了した後）、その操作で消費されたトークン量、またはそれまでの合計トークン量を取得できるように設計します。
    * **提案**:
        * `StandardMagenticManager` に `get_total_token_usage()` のようなパブリックメソッドを追加し、`total_completion_usage` 属性の値を返すようにします。
        * あるいは、`plan()` や `replan()` といったメソッド自体が、`ChatMessageContent` に加えてトークン使用量も戻り値として返すように変更することも考えられます（ただし、既存のシグネチャ変更が必要になります）。

3.  **ストリーミング応答の場合の考慮**:
    * `_inner_get_streaming_chat_message_contents` メソッドも `_get_metadata_from_response` を利用していますが、ストリーミングの場合は `usage` 情報が最後に一度だけ提供されるか、またはチャンクごとに提供されるかはAPIの挙動によります。
    * Azure AI Inference の場合、`StreamingChatCompletionsUpdate` オブジェクトにも `usage` が含まれる可能性があるため、ストリーミングの場合も同様に `chunk.usage` からトークンを取得し、合計していくロジックが必要になる場合があります。ただし、一般的にストリーミングでは完了後に使用量が確定するため、最終的な使用量を取得する方が実用的です。

4.  **エラーハンドリングと`None`の可能性**:
    * `response.usage` が `None` の場合や、`ChatMessageContent.metadata["usage"]` が存在しない（または `None` の）場合を適切に処理する必要があります。`CompletionUsage` の初期化時にデフォルト値を設定したり、`None` チェックを行うことで、堅牢なコードになります。

この整理が、今後の実装と設計の明確化に役立つことを願っています。