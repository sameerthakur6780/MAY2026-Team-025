import { ApiError, BASE_URL, formatErrorMessage, getCsrfToken } from "@/lib/apiClient";

export function uploadWithProgress(path, formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE_URL}${path}`);
    xhr.withCredentials = true;

    const csrfToken = getCsrfToken();
    if (csrfToken) {
      xhr.setRequestHeader("X-CSRF-TOKEN", csrfToken);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let data = null;
      try {
        data = xhr.responseText ? JSON.parse(xhr.responseText) : null;
      } catch {
        data = null;
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
      } else {
        reject(
          new ApiError(formatErrorMessage(data && data.message, xhr.statusText || "Upload failed"), {
            status: xhr.status,
            code: data && data.error,
            details: data,
          })
        );
      }
    };

    xhr.onerror = () => reject(new ApiError("Network error during upload", { status: 0, code: "network_error" }));

    xhr.send(formData);
  });
}
