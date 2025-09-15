"use client";

import { useState, useRef, useEffect, FC } from "react";
import React from "react";

// --- アイコンコンポーネント ---
// 実際のプロジェクトでは`lucide-react`などのライブラリを使用することをお勧めします
const UserIcon: FC<{ className?: string }> = ({ className }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
    </svg>
);

const BotIcon: FC<{ className?: string }> = ({ className }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" />
        <path d="M20 14h2" />
        <path d="M15 13v2" />
        <path d="M9 13v2" />
    </svg>
);

const SendIcon: FC<{ className?: string }> = ({ className }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <path d="m22 2-7 20-4-9-9-4Z" />
        <path d="M22 2 11 13" />
    </svg>
);

const CopyIcon: FC<{ className?: string }> = ({ className }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
        <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
);


// --- 型定義 ---
type Message = {
    role: "user" | "assistant";
    content: string;
};

// --- Markdownレンダラーコンポーネント ---
// 簡易的なMarkdownパーサーです。
// `react-markdown`などのライブラリを使用すると、より多くの記法に対応できます。
const SimpleMarkdown: FC<{ content: string }> = ({ content }) => {
    const codeBlockRegex = /```(\w+)?\n([\s\S]+?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
        // コードブロックより前のテキスト部分
        if (match.index > lastIndex) {
            parts.push(
                <div key={`text-${lastIndex}`} className="prose prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: formatText(content.slice(lastIndex, match.index)) }} />
            );
        }
        // コードブロック部分
        const language = match[1] || 'plaintext';
        const code = match[2];
        parts.push(
            <CodeBlock key={`code-${match.index}`} language={language} code={code} />
        );
        lastIndex = match.index + match[0].length;
    }

    // 最後のコードブロックより後のテキスト部分
    if (lastIndex < content.length) {
        parts.push(
            <div key={`text-${lastIndex}`} className="prose prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: formatText(content.slice(lastIndex)) }} />
        );
    }

    return <>{parts}</>;
};

const formatText = (text: string) => {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // 太字
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // 斜体
        .replace(/`([^`]+)`/g, '<code class="bg-gray-700 rounded-sm px-1 py-0.5 text-sm">$1</code>') // インラインコード
        .replace(/(\n|^)- (.*)/g, '$1<ul><li class="ml-4">$2</li></ul>') // リスト
        .replace(/(\n|^)# (.*)/g, '$1<h1 class="text-2xl font-bold mt-4 mb-2">$2</h1>') // H1
        .replace(/(\n|^)## (.*)/g, '$1<h2 class="text-xl font-semibold mt-3 mb-1">$2</h2>') // H2
        .replace(/\n/g, '<br />'); // 改行
};


const CodeBlock: FC<{ language: string, code: string }> = ({ language, code }) => {
    const [isCopied, setIsCopied] = useState(false);

    const handleCopy = () => {
        const textArea = document.createElement("textarea");
        textArea.value = code;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            setIsCopied(true);
            setTimeout(() => setIsCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
        document.body.removeChild(textArea);
    };

    return (
        <div className="bg-gray-900 rounded-lg my-2">
            <div className="flex justify-between items-center px-4 py-2 bg-gray-800 rounded-t-lg">
                <span className="text-xs text-gray-400 font-sans">{language}</span>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
                >
                    <CopyIcon className="w-4 h-4" />
                    {isCopied ? "Copied!" : "Copy code"}
                </button>
            </div>
            <pre className="p-4 text-sm overflow-x-auto"><code className={`language-${language}`}>{code}</code></pre>
        </div>
    );
};

// --- メインのチャットコンポーネント ---
export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // メッセージリストの最下部に自動スクロール
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        // AIの応答用に空のメッセージを追加
        setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

        try {
            // ここでバックエンドにPOSTリクエストを送信します。
            // bodyにはユーザーの入力やメッセージ履歴を含めるのが一般的です。
            const response = await fetch("http://localhost:8000/stream/dummy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: input, history: messages }),
            });

            if (!response.body) {
                throw new Error("Response body is null");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });

                // 最後のメッセージ（AIの応答）を更新
                //【修正点】stateを直接変更せず、mapを使用して新しい配列を生成する
                setMessages(prevMessages =>
                    prevMessages.map((msg, index) => {
                        if (index === prevMessages.length - 1 && msg.role === 'assistant') {
                            return { ...msg, content: msg.content + chunk };
                        }
                        return msg;
                    })
                );
            }
        } catch (error) {
            console.error("Streaming error:", error);
            setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage && lastMessage.role === 'assistant') {
                    lastMessage.content = "エラーが発生しました。もう一度お試しください。";
                }
                return newMessages;
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-800 text-white font-sans">
            {/* ヘッダー */}
            <header className="p-4 border-b border-gray-700">
                <h1 className="text-xl font-bold text-center">AI Chat</h1>
            </header>

            {/* メッセージ表示エリア */}
            <main className="flex-1 overflow-y-auto p-4 md:p-6">
                <div className="max-w-4xl mx-auto">
                    {messages.map((msg, index) => (
                        <div
                            key={index}
                            className={`flex items-start gap-3 my-4 ${msg.role === "user" ? "justify-end" : ""
                                }`}
                        >
                            {msg.role === "assistant" && (
                                <div className="w-8 h-8 flex-shrink-0 bg-blue-500 rounded-full flex items-center justify-center">
                                    <BotIcon className="w-5 h-5" />
                                </div>
                            )}
                            <div
                                className={`max-w-xl p-3 rounded-lg ${msg.role === "user"
                                        ? "bg-blue-600"
                                        : "bg-gray-700"
                                    }`}
                            >
                                {msg.role === 'assistant' && msg.content === '' && isLoading ? (
                                    <div className="animate-pulse flex space-x-1">
                                        <div className="w-1.5 h-1.5 bg-blue-300 rounded-full"></div>
                                        <div className="w-1.5 h-1.5 bg-blue-300 rounded-full"></div>
                                        <div className="w-1.5 h-1.5 bg-blue-300 rounded-full"></div>
                                    </div>
                                ) : (
                                    <SimpleMarkdown content={msg.content} />
                                )}
                            </div>
                            {msg.role === "user" && (
                                <div className="w-8 h-8 flex-shrink-0 bg-gray-600 rounded-full flex items-center justify-center">
                                    <UserIcon className="w-5 h-5" />
                                </div>
                            )}
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
            </main>

            {/* 入力フォームエリア */}
            <footer className="p-4 md:p-6 border-t border-gray-700">
                <div className="max-w-4xl mx-auto">
                    <form onSubmit={handleSubmit} className="flex items-center gap-3">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e as any);
                                }
                            }}
                            placeholder="メッセージを入力してください..."
                            rows={1}
                            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="bg-blue-600 text-white rounded-full p-3 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                        >
                            <SendIcon className="w-5 h-5" />
                        </button>
                    </form>
                </div>
            </footer>
        </div>
    );
}

