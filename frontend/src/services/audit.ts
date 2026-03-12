import { fetchApi } from "./api";

export interface AuditLogResponse {
  id: number;
  dataset: number;
  dataset_name: string;
  triggered_by: string;
  trigger_type: "manual" | "scheduled";
  score: number;
  timestamp: string;
}

/**
 * Fetches all audit logs, optionally filtered by dataset indicator.
 */
export const getAuditLogs = async (params?: {
  dataset_id?: number | string;
  start_date?: string;
  end_date?: string;
}): Promise<
  AuditLogResponse[] | { results: AuditLogResponse[]; count: number }
> => {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authentication token found");

  const urlParams = new URLSearchParams();
  if (params?.dataset_id)
    urlParams.append("dataset_id", params.dataset_id.toString());
  if (params?.start_date) urlParams.append("start_date", params.start_date);
  if (params?.end_date) urlParams.append("end_date", params.end_date);

  const options = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  const query = urlParams.toString() ? `?${urlParams.toString()}` : "";
  return fetchApi(`/audit/${query}`, options);
};
