import { useState } from "react";
import { Menu, Send } from "lucide-react";
import { useChatStore } from "../store/useChatStore";

export default function InputBar() {
  const { send, isStreaming, toggleSidebar } = useChatStore();
  const [text, setText] = useState("");

  const submit = () => {
    const t = text.trim();
    if (!t || isStreaming) return;
    setText("");
    void send(t);
  };

  return (
    <div className="glass rounded-2xl p-2.5">
      <div className="flex items-end gap-2.5">
        <button
          onClick={toggleSidebar}
          className="hidden h-11 w-11 shrink-0 items-center justify-center rounded-xl text-txt-mid transition hover:bg-white/5 hover:text-txt-hi md:flex"
          title="历史会话"
        >
          <Menu size={18} />
        </button>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          rows={1}
          placeholder="用自然语言提问，例如：2023年7月各省份入园人数…"
          className="max-h-32 min-h-[44px] flex-1 resize-none border-0 bg-transparent px-2 py-2.5 text-[14px] text-txt-hi outline-none placeholder:text-txt-low"
        />
        <button
          onClick={submit}
          disabled={isStreaming || !text.trim()}
          className="flex h-11 shrink-0 items-center gap-1.5 rounded-xl bg-gradient-to-r from-brand-teal to-brand-blue px-4 text-sm font-semibold text-white shadow-glow transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send size={16} /> 发送
        </button>
      </div>
    </div>
  );
}
