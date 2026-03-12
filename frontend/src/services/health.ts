import { fetchApi } from "./api";

export interface SystemHealth {
  status: "healthy" | "unhealthy";
  database: "up" | "down";
  redis: "up" | "down";
}

export async function getSystemHealth(): Promise<SystemHealth> {
  try {
    const response = await fetchApi("/health/", { skipAuth: true });
    return {
      status: response.status || "unhealthy",
      database: response.database || "down",
      redis: response.redis || "down",
    };
  } catch (err) {
    console.error("Health check failed:", err);
    return {
      status: "unhealthy",
      database: "down",
      redis: "down",
    };
  }
}
