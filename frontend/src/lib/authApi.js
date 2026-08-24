import { api, clearCsrfToken, clearGetCache } from "@/lib/apiClient";

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
  // Explicit even though api.post() above already clears the cache on
  // success -- a failed logout request must not leave the next person to
  // use this tab reading a still-logged-in user's cached responses.
  clearGetCache();
}

export function getCurrentUser() {
  return api.get("/api/auth/me");
}
