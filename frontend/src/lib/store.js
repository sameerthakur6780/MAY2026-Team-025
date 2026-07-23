// Tiny localStorage-backed auth/session helpers. No real backend.
const KEY = "educore_session";

export function setSession(session) {
  localStorage.setItem(KEY, JSON.stringify(session));
}

export function getSession() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(KEY);
}

export function roleHome(role) {
  if (role === "admin") return "/admin/dashboard";
  if (role === "parent") return "/parent/dashboard";
  if (role === "student") return "/student/dashboard";
  return "/";
}

export const ROLE_LABEL = {
  admin: "Admin / Tutor",
  parent: "Parent",
  student: "Student",
};
