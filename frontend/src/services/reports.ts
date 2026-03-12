import { fetchApi } from "./api";
import { CheckResultResponse, QualityScoreResponse } from "./checks";

export interface QualityReport {
  report_id: number;
  dataset_id: number;
  dataset_name: string;
  columns: string[];
  score: number;
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
  results: CheckResultResponse[];
  checked_at: string;
}

/**
 * Gets the dashboard summary containing the latest quality scores for all available datasets.
 *
 * @returns A promise that resolves to an array of QualityScoreResponse.
 */
export const getDashboardReports = async (): Promise<
  QualityScoreResponse[]
> => {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authentication token found");

  const options = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  return fetchApi("/reports/dashboard", options);
};

/**
 * Gets the detailed quality report for a specific dataset.
 *
 * @param datasetId - The ID of the dataset to fetch the report for.
 * @returns A promise that resolves to the QualityReport.
 */
export const getDatasetReport = async (
  datasetId: number | string
): Promise<QualityReport> => {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authentication token found");

  const options = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  return fetchApi(`/reports/${datasetId}`, options);
};

/**
 * Gets the quality trends over time for a specific dataset.
 *
 * @param datasetId - The ID of the dataset.
 * @param params - Optional pagination and filtering parameters.
 * @returns A promise that resolves to the trend data (usually an paginated array of QualityScoreResponse).
 */
export const getQualityTrends = async (
  datasetId: number | string,
  params?: {
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
  }
): Promise<
  | {
      count: number;
      next: string;
      previous: string;
      results: QualityScoreResponse[];
    }
  | QualityScoreResponse[]
> => {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authentication token found");

  let query = "";
  if (params) {
    const urlParams = new URLSearchParams();
    if (params.start_date) urlParams.append("start_date", params.start_date);
    if (params.end_date) urlParams.append("end_date", params.end_date);
    if (params.page !== undefined)
      urlParams.append("page", params.page.toString());
    if (params.limit !== undefined)
      urlParams.append("limit", params.limit.toString());

    const queryString = urlParams.toString();
    if (queryString) {
      query = `?${queryString}`;
    }
  }

  const options = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  return fetchApi(`/reports/${datasetId}/trends${query}`, options);
};

/**
 * Gets the quality trends over time for multiple datasets.
 *
 * @param datasetIds - Array of dataset IDs.
 * @param params - Optional filtering parameters.
 * @returns A promise that resolves to an array of QualityScoreResponse.
 */
export const getBulkQualityTrends = async (
  datasetIds: (number | string)[],
  params?: {
    start_date?: string;
    end_date?: string;
  }
): Promise<QualityScoreResponse[]> => {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authentication token found");

  const urlParams = new URLSearchParams();
  urlParams.append("dataset_ids", datasetIds.join(","));
  if (params?.start_date) urlParams.append("start_date", params.start_date);
  if (params?.end_date) urlParams.append("end_date", params.end_date);

  const options = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  return fetchApi(`/reports/bulk-trends?${urlParams.toString()}`, options);
};
