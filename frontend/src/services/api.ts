export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers({
    "Content-Type": "application/json",
    ...options.headers,
  });

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || data?.non_field_errors?.[0] || response.statusText || "An error occurred");
  }

  return data;
}
