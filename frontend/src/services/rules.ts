import { fetchApi } from "./api";

export interface ValidationRule {
  id: number;
  name: string;
  dataset_type: string;
  field_name: string;
  rule_type: "NOT_NULL" | "DATA_TYPE" | "RANGE" | "UNIQUE" | "REGEX";
  parameters: string | null;
  severity: "HIGH" | "MEDIUM" | "LOW";
  is_active: boolean;
  created_at: string;
}

export interface RuleCreateData {
  name: string;
  dataset_type: string;
  field_name: string;
  rule_type: string;
  parameters: string | null;
  severity: string;
}

export interface GetRulesParams {
  dataset_type?: string;
  search?: string;
  field_name?: string;
  rule_type?: string;
  severity?: string;
}

export async function getRules(
  params?: GetRulesParams
): Promise<ValidationRule[]> {
  const queryParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) queryParams.append(key, value);
    });
  }
  const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
  return fetchApi(`/rules/${query}`);
}

export async function createRule(
  data: RuleCreateData
): Promise<ValidationRule> {
  return fetchApi("/rules/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateRule(
  id: number,
  data: Partial<RuleCreateData>
): Promise<ValidationRule> {
  return fetchApi(`/rules/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteRule(id: number): Promise<void> {
  await fetchApi(`/rules/${id}`, {
    method: "DELETE",
  });
}
