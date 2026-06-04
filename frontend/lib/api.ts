import { ChatResponse, ProgressData } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function sendChat(
  message: string,
  sessionId: string | null,
  token?: string | null
): Promise<ChatResponse> {
  return fetchApi<ChatResponse>(
    "/chat",
    {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    },
    token
  );
}

export async function fetchProgress(
  userId: string,
  token?: string | null
): Promise<ProgressData> {
  return fetchApi<ProgressData>(`/progress/${userId}`, {}, token);
}

export async function resetSession(
  sessionId: string,
  token?: string | null
): Promise<void> {
  await fetchApi(`/session/${sessionId}`, { method: "DELETE" }, token);
}
