import { useEffect, useRef } from "react";
import { useChatStore } from "../store/useChatStore";
import MessageBubble from "./MessageBubble";
import SuggestChips from "./SuggestChips";
import InputBar from "./InputBar";

const STARTERS = [
  "2023年7月不同省份的入园人数统计",
  "2023年4、5、6月一日票、二日票销量，按周统计",
  "2023年10月1-7日各销售渠道订单金额排名",
];

export default function ChatPanel() {
  const { messages, suggestions, isStreaming, send, activeId } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const pick = (t: string) => {
    if (!isStreaming) void send(t);
  };

  return (
    <div className="flex h-full flex-1 flex-col gap-3">
      <div className="glass flex-1 space-y-5 overflow-y-auto rounded-2xl p-4 md:p-5">
        {messages.length === 0 ? (
          <EmptyState onPick={pick} />
        ) : (
          messages.map((m) => <MessageBubble key={m.id} msg={m} />)
        )}
        {messages.length > 0 && (
          <SuggestChips items={suggestions} onPick={pick} />
        )}
        <div ref={bottomRef} />
      </div>
      <InputBar />
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (t: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <div className="mb-3 text-5xl">🎢</div>
      <h2 className="gradient-title text-2xl font-bold">环球影城 · 门票数据助手</h2>
      <p className="mt-2 max-w-md text-[13px] text-txt-low">
        用自然语言提问，AI 自动生成 SQL 查询数据库、可视化结果并给出分析。
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {STARTERS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="rounded-full border border-ink-600 bg-ink-800 px-3.5 py-2 text-[12.5px] text-txt-mid transition duration-150 hover:border-brand-teal hover:bg-brand-teal/10 hover:text-brand-teal"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
