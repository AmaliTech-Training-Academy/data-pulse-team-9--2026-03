import { fetchApi } from "./api";

export interface Dataset {
  id: number;
  name: string;
  file_type: string;
  row_count: number;
  column_count: number;
  column_names: string[] | null;
  status: string;
  uploaded_at: string;
  score?: number | null;
  uploaded_by?: number | { id: number; email: string; full_name?: string };
  failed_rules?: number;
}

export async function getDatasets(userId?: number): Promise<Dataset[]> {
  const endpoint = userId
    ? `/api/datasets/?uploaded_by=${userId}`
    : "/api/datasets/";
  const response = await fetchApi(endpoint);
  if (response && response.results && Array.isArray(response.results)) {
    return response.results;
  }
  if (response && response.datasets && Array.isArray(response.datasets)) {
    return response.datasets;
  }
  if (Array.isArray(response)) {
    return response;
  }
  return [];
}
