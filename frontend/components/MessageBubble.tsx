"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "@/lib/types";

export default function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex items-end justify-end gap-2">
        <div className="max-w-[72%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed break-words">
          {message.content}
        </div>
        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm flex-shrink-0">
          👤
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-end gap-2">
      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm flex-shrink-0">
        🩺
      </div>
      <div className="max-w-[78%] bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="prose prose-sm prose-slate max-w-none
          prose-headings:text-blue-900 prose-headings:font-bold prose-headings:mt-3 prose-headings:mb-1
          prose-p:my-1 prose-p:leading-relaxed
          prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5
          prose-hr:my-3 prose-hr:border-slate-200
          prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-blue-800 prose-code:text-xs
          prose-pre:bg-slate-100 prose-pre:rounded-xl prose-pre:p-3
          prose-strong:text-slate-800
          prose-table:text-xs prose-th:bg-blue-50 prose-th:p-2 prose-td:p-2
        ">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
