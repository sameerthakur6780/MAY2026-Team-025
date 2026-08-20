import { api, clearCsrfToken } from "@/lib/apiClient";

export async function login(email, password) {
  await api.post("/api/auth/login", { email, password });
  return api.get("/api/auth/me");
}

export async function logout() {
  try {
    await api.post("/api/auth/logout");
  } catch {
    // Best-effort -- cookies get cleared server-side regardless; the
    // caller clears client state whether or not this succeeds.
  }
  clearCsrfToken();
}

export function getCurrentUser() {
  return api.get("/api/auth/me");
}
