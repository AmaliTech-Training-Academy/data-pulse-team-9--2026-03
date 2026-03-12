import { fetchApi } from "./api";

export interface CheckResultResponse {
  id: number;
  dataset_id: number;
  rule_id: number;
  rule_name: string;
  passed: boolean;
  fail_count: number;
  pass_count: number;
  sample_rows: Record<string, unknown>[];
  details: string;
  checked_at: string;
}

export interface QualityScoreResponse {
  id?: number;
  dataset_id: number;
  score?: number;
  total_rules?: number;
  passed_rules?: number;
  failed_rules?: number;
  checked_at?: string;
}

/**
 * Runs all applicable validation checks on a given dataset.
 *
 * @param datasetId - The ID of the dataset to check.
 * @returns A promise that resolves to the QualityScoreResponse.
 */
export const runCheck = async (
  datasetId: number | string
): Promise<QualityScoreResponse> => {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authentication token found");

  const options = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  return fetchApi(`/checks/run/${datasetId}`, options);
};

/**
 * Gets all raw check results for a given dataset.
 * @param datasetId - The ID of the dataset to fetch results for.
 * @returns A promise that resolves to an array of CheckResultResponse.
 */
export const getCheckResults = async (
  datasetId: number | string
): Promise<CheckResultResponse[]> => {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authentication token found");

  const options = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  return fetchApi(`/checks/results/${datasetId}`, options);
};
