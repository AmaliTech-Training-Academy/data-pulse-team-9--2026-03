import { fetchApi } from "./api";

export interface AlertConfig {
  id: number;
  dataset_id: number;
  threshold: number;
  email_notifications: boolean;
  is_alert_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function getAlertConfig(
  datasetId: number
): Promise<AlertConfig | null> {
  try {
    const options = {
      headers: {
        ...(localStorage.getItem("token")
          ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
          : {}),
      },
    };
    return await fetchApi(`/api/schedules/alerts/${datasetId}/`, options);
  } catch (err) {
    const error = err as Error;
    // If method is not allowed, it means backend hasn't implemented GET yet.
    // We return a default instead of null to allow the frontend to function.
    if (
      error.message?.includes("Method") ||
      error.message?.includes("Allowed")
    ) {
      return {
        id: 0,
        dataset_id: datasetId,
        threshold: 80,
        email_notifications: true,
        is_alert_active: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
    console.error(
      `Failed to fetch alert config for dataset ${datasetId}:`,
      error
    );
    return null;
  }
}

export async function updateAlertConfig(
  datasetId: number,
  data: Partial<AlertConfig>
): Promise<AlertConfig> {
  const options = {
    method: "POST", // The backend uses POST for create/update in AlertConfigView
    headers: {
      "Content-Type": "application/json",
      ...(localStorage.getItem("token")
        ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
        : {}),
    },
    body: JSON.stringify({
      ...data,
      dataset_id: datasetId,
    }),
  };
  return await fetchApi(`/api/schedules/alerts/${datasetId}/`, options);
}
