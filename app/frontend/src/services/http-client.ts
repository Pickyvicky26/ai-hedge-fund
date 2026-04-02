export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const API_ADMIN_TOKEN = import.meta.env.VITE_API_ADMIN_TOKEN;

export function buildApiHeaders(headers?: HeadersInit): Headers {
  const nextHeaders = new Headers(headers ?? {});

  if (API_ADMIN_TOKEN && !nextHeaders.has('X-Admin-Token')) {
    nextHeaders.set('X-Admin-Token', API_ADMIN_TOKEN);
  }

  return nextHeaders;
}

export function apiFetch(path: string, init: RequestInit = {}) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return fetch(`${API_BASE_URL}${normalizedPath}`, {
    ...init,
    headers: buildApiHeaders(init.headers),
  });
}
