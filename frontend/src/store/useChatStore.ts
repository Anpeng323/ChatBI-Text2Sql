import { create } from "zustand";
import { api, streamChat } from "../api/client";
import type { ChatMessage, SessionInfo } from "../types";

function uid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

interface ChatState {
  sessions: SessionInfo[];
  activeId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  suggestions: string[];
  sidebarOpen: boolean;

  refreshSessions: () => Promise<void>;
  newSession: () => Promise<void>;
  selectSession: (id: string) => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  send: (text: string) => Promise<void>;
  toggleSidebar: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeId: null,
  messages: [],
  isStreaming: false,
  suggestions: [],
  sidebarOpen: false,

  async refreshSessions() {
    try {
      const list = await api.listSessions();
      set({ sessions: list });
    } catch {
      /* 后端未就绪时静默 */
    }
  },

  async newSession() {
    const created = await api.createSession();
    set({ activeId: created.session_id, messages: [], suggestions: [] });
    await get().refreshSessions();
  },

  async selectSession(id: string) {
    const sess = await (await fetch(`/api/sessions/${id}`)).json();
    const msgs: ChatMessage[] = (sess.messages ?? []).map((m: any) => ({
      id: uid(),
      role: m.role,
      content: m.content ?? "",
      sql: m.sql,
      chart: m.chart,
      suggestions: m.suggestions,
    }));
    set({ activeId: id, messages: msgs, suggestions: [], sidebarOpen: false });
    await get().refreshSessions();
  },

  async   deleteSession(id: string) {
    await api.deleteSession(id);
    if (get().activeId === id) {
      set({ activeId: null, messages: [], suggestions: [] });
    }
    await get().refreshSessions();
  },

  toggleSidebar() {
    set({ sidebarOpen: !get().sidebarOpen });
  },

  async send(text: string) {
    if (get().isStreaming || !text.trim()) return;
    let sid = get().activeId;
    if (!sid) {
      const created = await api.createSession();
      sid = created.session_id;
      set({ activeId: sid, messages: [] });
      await get().refreshSessions();
    }
    const userMsg: ChatMessage = {
      id: uid(),
      role: "user",
      content: text,
    };
    const botId = uid();
    const botMsg: ChatMessage = {
      id: botId,
      role: "assistant",
      content: "",
      streaming: true,
    };
    set({
      messages: [...get().messages, userMsg, botMsg],
      isStreaming: true,
      suggestions: [],
    });

    const patch = (p: Partial<ChatMessage>) =>
      set({
        messages: get().messages.map((m) => (m.id === botId ? { ...m, ...p } : m)),
      });

    try {
      await streamChat(sid!, text, (e) => {
        switch (e.type) {
          case "sql":
            patch({ sql: e.payload.sql, sqlVerified: e.payload.verified });
            break;
          case "data":
            patch({ data: e.payload.markdown });
            break;
          case "chart":
            patch({ chart: e.payload.option });
            break;
          case "answer":
            set({
              messages: get().messages.map((m) =>
                m.id === botId ? { ...m, content: m.content + e.payload.delta } : m
              ),
            });
            break;
          case "suggestions":
            set({ suggestions: e.payload.items ?? [] });
            patch({ suggestions: e.payload.items ?? [] });
            break;
          case "error":
            patch({ error: true, streaming: false, content: e.payload.message ?? "出错了" });
            break;
          case "done":
            patch({ streaming: false });
            break;
        }
      });
    } catch (err) {
      patch({ error: true, streaming: false, content: `连接失败：${(err as Error).message}` });
    } finally {
      set({ isStreaming: false });
    }
  },
}));
