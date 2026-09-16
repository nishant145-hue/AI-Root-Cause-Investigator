import api from "./api";

export interface HealthResponse {
  status?: string;
  [key: string]: unknown;
}

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
};
