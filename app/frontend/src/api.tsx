const API = import.meta.env.VITE_API_URL;

export const api = (path: string, opts: RequestInit = {}) =>
  fetch(`${API}${path}`, { credentials: "include", ...opts });

export async function initSession() {
  const res = await api("/session/init", { method: "POST" });
  if (!res.ok) throw new Error(`Session init failed: ${res.status}`);
}