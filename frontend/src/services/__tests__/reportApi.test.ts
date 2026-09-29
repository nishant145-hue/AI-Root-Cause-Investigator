import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock("../api", () => ({
  default: {
    get: mocks.get,
  },
}));

import {
  downloadAllInvestigationsCsv,
  downloadAllInvestigationsExcel,
  downloadAllInvestigationsPdf,
  downloadInvestigationAnalyticsCsv,
  downloadInvestigationAnalyticsExcel,
  downloadInvestigationAnalyticsPdf,
  getReportHistory,
} from "../reportApi";

describe("reportApi", () => {
  beforeEach(() => {
    mocks.get.mockReset();
  });

  it("gets report history with pagination", async () => {
    const data = {
      items: [
        {
          id: 1,
          user_id: 7,
          investigation_id: 101,
          report_type: "analytics",
          format: "xlsx",
          filename: "investigation-101.xlsx",
          status: "completed",
          created_at: "2026-09-29T00:00:00Z",
        },
      ],
      total: 1,
    };

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getReportHistory(20, 10);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/reports/history",
      {
        params: {
          limit: 20,
          offset: 10,
        },
      },
    );

    expect(result).toEqual(data);
  });

  it("downloads all investigations as CSV", async () => {
    const blob = new Blob(["csv data"], {
      type: "text/csv",
    });

    mocks.get.mockResolvedValueOnce({
      data: blob,
    });

    const result = await downloadAllInvestigationsCsv();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/reports/csv",
      {
        responseType: "blob",
      },
    );

    expect(result).toBe(blob);
  });

  it("downloads all investigations as Excel", async () => {
    const blob = new Blob(["excel data"], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    mocks.get.mockResolvedValueOnce({
      data: blob,
    });

    const result = await downloadAllInvestigationsExcel();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/reports/excel",
      {
        responseType: "blob",
      },
    );

    expect(result).toBe(blob);
  });

  it("downloads all investigations as PDF", async () => {
    const blob = new Blob(["pdf data"], {
      type: "application/pdf",
    });

    mocks.get.mockResolvedValueOnce({
      data: blob,
    });

    const result = await downloadAllInvestigationsPdf();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/reports/pdf",
      {
        responseType: "blob",
      },
    );

    expect(result).toBe(blob);
  });

  it("downloads investigation analytics as CSV", async () => {
    const blob = new Blob(["csv data"], {
      type: "text/csv",
    });

    mocks.get.mockResolvedValueOnce({
      data: blob,
    });

    const result =
      await downloadInvestigationAnalyticsCsv(2701);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/investigations/2701/analytics/export/csv",
      {
        responseType: "blob",
      },
    );

    expect(result).toBe(blob);
  });

  it("downloads investigation analytics as Excel", async () => {
    const blob = new Blob(["excel data"], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    mocks.get.mockResolvedValueOnce({
      data: blob,
    });

    const result =
      await downloadInvestigationAnalyticsExcel(2701);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/investigations/2701/analytics/export/excel",
      {
        responseType: "blob",
      },
    );

    expect(result).toBe(blob);
  });

  it("downloads investigation analytics as PDF", async () => {
    const blob = new Blob(["pdf data"], {
      type: "application/pdf",
    });

    mocks.get.mockResolvedValueOnce({
      data: blob,
    });

    const result =
      await downloadInvestigationAnalyticsPdf(2701);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/investigations/2701/analytics/export/pdf",
      {
        responseType: "blob",
      },
    );

    expect(result).toBe(blob);
  });
});
