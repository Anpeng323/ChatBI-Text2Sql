import { useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";
import { useChatStore } from "./store/useChatStore";

export default function App() {
  const { refreshSessions, newSession } = useChatStore();

  useEffect(() => {
    void refreshSessions();
    // 首次进入若无会话则自动建一个，保证可直接提问
    if (!useChatStore.getState().activeId) void newSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-screen gap-3 p-3 md:p-4">
      <Sidebar />
      <main className="flex h-full min-w-0 flex-1 flex-col">
        <header className="glass mb-3 flex items-center gap-3 rounded-2xl px-4 py-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-teal via-brand-blue to-brand-purple text-lg shadow-glow">
            🎢
          </div>
          <div className="flex-1">
            <h1 className="gradient-title text-[17px] font-bold leading-tight">
              ChatBI · 通用数据分析平台
            </h1>
            <p className="text-[12px] text-txt-low">
              NL2SQL · 自动可视化 · 自然语言驱动的数据洞察
            </p>
          </div>
          <span className="hidden items-center gap-1.5 rounded-full bg-brand-teal/15 px-3 py-1 text-[12px] text-brand-teal sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-teal" /> 在线
          </span>
        </header>
        <ChatPanel />
      </main>
    </div>
  );
}
