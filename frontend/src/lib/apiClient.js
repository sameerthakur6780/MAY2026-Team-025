
export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

const NO_REFRESH_PATHS = new Set(["/api/auth/login", "/api/auth/refresh", "/api/auth/logout"]);

export class ApiError extends Error {
  constructor(message, { status, code, details } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : null;
}

export function formatErrorMessage(rawMessage, fallback) {
  if (typeof rawMessage === "string") return rawMessage;
  if (rawMessage && typeof rawMessage === "object") {
    return Object.entries(rawMessage)
      .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(" ") : errors}`)
      .join(" ");
  }
  return fallback;
}

async function rawRequest(path, { method = "GET", body } = {}) {
  const headers = {};
  let finalBody = body;

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    finalBody = JSON.stringify(body);
  }

  if (!SAFE_METHODS.has(method.toUpperCase())) {
    const csrfToken = getCookie("csrf_access_token");
    if (csrfToken) {
      headers["X-CSRF-TOKEN"] = csrfToken;
    }
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: finalBody,
    credentials: "include", 
  });

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    throw new ApiError(formatErrorMessage(data && data.message, response.statusText), {
      status: response.status,
      code: data && data.error,
      details: data,
    });
  }

  return data;
}

let refreshPromise = null;

function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = rawRequest("/api/auth/refresh", { method: "POST" }).finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function apiRequest(path, options = {}) {
  try {
    return await rawRequest(path, options);
  } catch (err) {
    const canRetryWithRefresh =
      err instanceof ApiError &&
      err.status === 401 &&
      err.code === "token_expired" &&
      !NO_REFRESH_PATHS.has(path);

    if (!canRetryWithRefresh) {
      throw err;
    }

    try {
      await refreshAccessToken();
    } catch {
      // refresh failed -- surface the original 401 so the caller can send the user to /login
      throw err; 
    }

    return rawRequest(path, options);
  }
}

export const api = {
  get: (path) => apiRequest(path, { method: "GET" }),
  post: (path, body) => apiRequest(path, { method: "POST", body }),
  patch: (path, body) => apiRequest(path, { method: "PATCH", body }),
  delete: (path) => apiRequest(path, { method: "DELETE" }),
};
