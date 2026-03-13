export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  fieldErrors?: Record<string, string[]>;

  constructor(
    message: string,
    status: number,
    fieldErrors?: Record<string, string[]>
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

export async function fetchApi(
  endpoint: string,
  options: RequestInit & { skipAuth?: boolean } = {}
) {
  const { skipAuth, ...fetchOptions } = options;
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers = new Headers({
    "Content-Type": "application/json",
    ...(token && !skipAuth ? { Authorization: `Bearer ${token}` } : {}),
    ...fetchOptions.headers,
  });

  console.log(
    `📡 API Request: ${fetchOptions.method || "GET"} ${API_URL}${endpoint}`
  );
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    console.error(`❌ API Error: ${response.status} ${endpoint}`, data);
    const fieldErrors = data?.field_errors || data;
    const errorMessage =
      data?.detail ||
      data?.non_field_errors?.[0] ||
      (typeof data === "string" ? data : "An error occurred");

    throw new ApiError(errorMessage, response.status, fieldErrors);
  }

  console.log(`✅ API Success: ${endpoint}`, data);
  return data;
}
