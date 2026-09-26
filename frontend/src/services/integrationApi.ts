import api from "./api";

export interface IntegrationStatus {
  registered: boolean;
  configured: boolean;
}

export interface IntegrationStatusResponse {
  email: IntegrationStatus;
  slack: IntegrationStatus;
  teams: IntegrationStatus;
}

export const getIntegrationStatus =
  async (): Promise<IntegrationStatusResponse> => {
    const response = await api.get<IntegrationStatusResponse>(
      "/api/v1/integrations/status",
    );

    return response.data;
  };