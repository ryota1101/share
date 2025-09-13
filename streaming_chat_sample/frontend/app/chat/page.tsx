"use client";
import { useState } from "react";

export default function StreamDummy() {
    const [text, setText] = useState("");

    const handleClick = async () => {
        const response = await fetch("http://localhost:8000/stream/dummy", {
            method: "POST",
        });

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
            let result = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                result += decoder.decode(value, { stream: true });
                setText(result); // 部分的に表示（ChatGPT風）
            }
        }
    };

    return (
        <div className="p-4">
            <button
                onClick={handleClick}
                className="px-4 py-2 bg-blue-500 text-white rounded"
            >
                ダミーストリーム開始
            </button>
            <pre className="mt-4 whitespace-pre-wrap">{text}</pre>
        </div>
    );
}
