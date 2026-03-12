import { fetchApi } from "./api";

export interface Schedule {
  id?: number;
  dataset: number;
  cron_expression: string;
  created_at?: string;
  updated_at?: string;
}

export async function getSchedules(): Promise<Schedule[]> {
  const options = {
    headers: {
      ...(localStorage.getItem("token")
        ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
        : {}),
    },
  };
  const response = await fetchApi("/api/schedules/", options);
  if (response && response.results && Array.isArray(response.results)) {
    return response.results;
  }
  if (Array.isArray(response)) {
    return response;
  }
  return [];
}

export async function createOrUpdateSchedule(data: {
  dataset_id: number;
  cron_expression: string;
}): Promise<Schedule> {
  const options = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(localStorage.getItem("token")
        ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
        : {}),
    },
    body: JSON.stringify(data),
  };
  return await fetchApi("/api/schedules/", options);
}

export async function deleteSchedule(id: number): Promise<void> {
  const options = {
    method: "DELETE",
    headers: {
      ...(localStorage.getItem("token")
        ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
        : {}),
    },
  };
  await fetchApi(`/api/schedules/${id}/`, options);
}

export async function toggleSchedule(
  id: number,
  action: "pause" | "resume"
): Promise<{ status: string; schedule_id: number }> {
  const options = {
    method: "PATCH",
    headers: {
      ...(localStorage.getItem("token")
        ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
        : {}),
    },
  };
  return await fetchApi(`/api/schedules/${id}/${action}/`, options);
}
