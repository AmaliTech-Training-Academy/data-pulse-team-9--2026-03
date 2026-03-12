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
    return await fetchApi(`/schedules/alerts/${datasetId}/`, options);
  } catch (err) {
    console.error(
      `Failed to fetch alert config for dataset ${datasetId}:`,
      err
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
    body: JSON.stringify(data),
  };
  return await fetchApi(`/schedules/alerts/${datasetId}/`, options);
}
