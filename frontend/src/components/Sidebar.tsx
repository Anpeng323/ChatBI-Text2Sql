import { MessageSquarePlus, Trash2, X } from "lucide-react";
import { useChatStore } from "../store/useChatStore";

export default function Sidebar() {
  const {
    sessions,
    activeId,
    sidebarOpen,
    newSession,
    selectSession,
    deleteSession,
    toggleSidebar,
  } = useChatStore();

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={toggleSidebar}
        />
      )}
      <aside
        className={`fixed z-40 flex h-full w-64 shrink-0 flex-col gap-2 p-3 transition-transform duration-200 md:static md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } glass rounded-2xl`}
      >
        <div className="flex items-center justify-between px-1 pb-1">
          <span className="text-[13px] font-semibold text-txt-hi">历史会话</span>
          <button
            className="text-txt-low hover:text-txt-hi md:hidden"
            onClick={toggleSidebar}
          >
            <X size={16} />
          </button>
        </div>
        <button
          onClick={() => newSession()}
          className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-teal to-brand-blue py-2.5 text-sm font-semibold text-white shadow-glow transition hover:opacity-90"
        >
          <MessageSquarePlus size={16} /> 新建会话
        </button>

        <div className="mt-1 flex-1 space-y-1 overflow-y-auto pr-1">
          {sessions.length === 0 && (
            <p className="px-2 py-4 text-center text-[12px] text-txt-low">
              暂无会话，开始提问吧
            </p>
          )}
          {sessions.map((s) => (
            <div
              key={s.session_id}
              className={`group flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2.5 text-[13px] transition ${
                s.session_id === activeId
                  ? "bg-brand-teal/15 text-txt-hi"
                  : "text-txt-mid hover:bg-white/5"
              }`}
              onClick={() => selectSession(s.session_id)}
            >
              <span className="flex-1 truncate">{s.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(s.session_id);
                }}
                className="opacity-0 transition group-hover:opacity-100 hover:text-brand-red"
                title="删除"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        <div className="border-t border-white/5 pt-2 text-[11px] text-txt-low">
          通用 ChatBI · NL2SQL 平台
        </div>
      </aside>
    </>
  );
}
