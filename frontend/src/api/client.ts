import type { SessionInfo, StreamEvent } from "../types";

const BASE = "/api";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`请求失败 ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  async listSessions(): Promise<SessionInfo[]> {
    return json(await fetch(`${BASE}/sessions`));
  },
  async createSession(title?: string): Promise<SessionInfo> {
    return json(
      await fetch(`${BASE}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title ?? null }),
      })
    );
  },
  async deleteSession(id: string): Promise<void> {
    await fetch(`${BASE}/sessions/${id}`, { method: "DELETE" });
  },
  async getSchema(): Promise<{ schema: any; prompt_text: string }> {
    return json(await fetch(`${BASE}/schema`));
  },
};

/** 流式对话：逐事件回调。返回 Promise 在流结束时 resolve。 */
export async function streamChat(
  sessionId: string,
  message: string,
  onEvent: (e: StreamEvent) => void
): Promise<void> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, stream: true }),
  });
  if (!res.ok || !res.body) throw new Error(`对话请求失败 ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    // SSE：以空行分隔
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const line = raw.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      const data = line.slice(5).trim();
      if (!data) continue;
      try {
        const ev = JSON.parse(data) as StreamEvent;
        onEvent(ev);
      } catch {
        /* 忽略心跳/坏帧 */
      }
    }
  }
}

export function exportCsvUrl(sql: string, filename = "chatbi_export"): string {
  return `${BASE}/export/csv?sql=${encodeURIComponent(sql)}&filename=${encodeURIComponent(
    filename
  )}`;
}
