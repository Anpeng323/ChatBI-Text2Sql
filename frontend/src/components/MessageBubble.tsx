import { useState } from "react";
import { Bot, ChevronDown, Database, ShieldCheck, User } from "lucide-react";
import type { ChatMessage } from "../types";
import ChartView from "./ChartView";
import Markdown from "./Markdown";

interface Props {
  msg: ChatMessage;
}

export default function MessageBubble({ msg }: Props) {
  const [showSql, setShowSql] = useState(false);
  const isUser = msg.role === "user";

  if (isUser) {
    return (
      <div className="flex animate-fadeup justify-end">
        <div className="max-w-[82%] rounded-2xl rounded-br-md bg-gradient-to-br from-brand-teal to-brand-blue px-4 py-2.5 text-white shadow-glow">
          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex animate-fadeup gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-teal/30 to-brand-purple/30 text-brand-teal">
        <Bot size={18} />
      </div>
      <div className="max-w-[88%] space-y-2">
        {msg.content && (
          <div className="rounded-2xl rounded-tl-md border border-ink-600 bg-ink-700 px-4 py-3 text-txt-hi">
            <Markdown text={msg.content} />
            {msg.streaming && (
              <span className="ml-1 inline-block h-3.5 w-1.5 animate-pulse bg-brand-teal align-middle" />
            )}
          </div>
        )}

        {msg.sql && (
          <div className="rounded-xl border border-ink-600 bg-ink-800/80">
            <button
              onClick={() => setShowSql(!showSql)}
              className="flex w-full items-center gap-2 px-3 py-2 text-[12.5px] text-txt-mid transition hover:text-txt-hi"
            >
              <Database size={14} className="text-brand-teal" />
              <span>由工具执行查询</span>
              {msg.sqlVerified && (
                <span className="flex items-center gap-1 text-[11px] text-brand-teal">
                  <ShieldCheck size={12} /> 已校验
                </span>
              )}
              <ChevronDown
                size={14}
                className={`ml-auto transition ${showSql ? "rotate-180" : ""}`}
              />
            </button>
            {showSql && (
              <pre className="max-h-60 overflow-auto border-t border-white/5 px-3 py-2 text-[12px] leading-relaxed text-txt-mid">
                <code>{msg.sql}</code>
              </pre>
            )}
          </div>
        )}

        {msg.data && (
          <div className="overflow-x-auto rounded-xl border border-ink-600 bg-ink-900/50 p-3">
            <pre className="text-[12px] leading-relaxed text-txt-mid">
              <code>{msg.data}</code>
            </pre>
          </div>
        )}

        {msg.chart && <ChartView option={msg.chart as Record<string, unknown>} />}
      </div>
    </div>
  );
}
