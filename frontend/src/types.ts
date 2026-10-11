export interface SessionInfo {
  session_id: string;
  title: string;
  created_at: number;
  updated_at: number;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sql?: string;
  sqlVerified?: boolean;
  data?: string;
  chart?: Record<string, unknown> | null;
  suggestions?: string[];
  streaming?: boolean;
  error?: boolean;
}

export type StreamEventType =
  | "thinking"
  | "sql"
  | "data"
  | "chart"
  | "answer"
  | "suggestions"
  | "error"
  | "done";

export interface StreamEvent {
  type: StreamEventType;
  payload: Record<string, any>;
}
