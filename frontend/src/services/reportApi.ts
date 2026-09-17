import api from "./api";

/*
 * ============================================================
 * Report History
 * ============================================================
 */

export interface ReportHistoryItem {
  id: number;
  user_id: number;
  investigation_id: number | null;
  report_type: string;
  format: string;
  filename: string;
  status: string;
  created_at: string;
}

export interface ReportHistoryResponse {
  items: ReportHistoryItem[];
  total: number;
}

export const getReportHistory = async (
  limit = 50,
  offset = 0,
): Promise<ReportHistoryResponse> => {
  const response = await api.get<ReportHistoryResponse>(
    "/api/v1/reports/history",
    {
      params: {
        limit,
        offset,
      },
    },
  );

  return response.data;
};

/*
 * ============================================================
 * Report Downloads
 * ============================================================
 *
 * All report endpoints return files, so Axios must use
 * responseType: "blob".
 * ============================================================
 */

export const downloadAllInvestigationsCsv = async (): Promise<Blob> => {
  const response = await api.get("/api/v1/reports/csv", {
    responseType: "blob",
  });

  return response.data;
};

export const downloadAllInvestigationsExcel = async (): Promise<Blob> => {
  const response = await api.get("/api/v1/reports/excel", {
    responseType: "blob",
  });

  return response.data;
};

export const downloadAllInvestigationsPdf = async (): Promise<Blob> => {
  const response = await api.get("/api/v1/reports/pdf", {
    responseType: "blob",
  });

  return response.data;
};

/*
 * ============================================================
 * Investigation Analytics Reports
 * ============================================================
 */

export const downloadInvestigationAnalyticsCsv = async (
  investigationId: number,
): Promise<Blob> => {
  const response = await api.get(
    `/api/v1/investigations/${investigationId}/analytics/export/csv`,
    {
      responseType: "blob",
    },
  );

  return response.data;
};

export const downloadInvestigationAnalyticsExcel = async (
  investigationId: number,
): Promise<Blob> => {
  const response = await api.get(
    `/api/v1/investigations/${investigationId}/analytics/export/excel`,
    {
      responseType: "blob",
    },
  );

  return response.data;
};

export const downloadInvestigationAnalyticsPdf = async (
  investigationId: number,
): Promise<Blob> => {
  const response = await api.get(
    `/api/v1/investigations/${investigationId}/analytics/export/pdf`,
    {
      responseType: "blob",
    },
  );

  return response.data;
};
