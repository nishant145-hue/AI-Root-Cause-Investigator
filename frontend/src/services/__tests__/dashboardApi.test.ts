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
  getConfidenceAnalytics,
  getDashboardOverview,
  getDashboardTimeline,
  getFailedComponents,
  getRecentInvestigations,
  getRootCauses,
  getSeverityDistribution,
} from "../dashboardApi";

describe("dashboardApi", () => {
  beforeEach(() => {
    mocks.get.mockReset();
  });

  it("gets dashboard overview", async () => {
    const data = {
      total_investigations: 12,
      completed_investigations: 9,
      failed_investigations: 2,
      running_investigations: 1,
    };

    mocks.get.mockResolvedValueOnce({ data });

    const config = {
      signal: new AbortController().signal,
    };

    const result = await getDashboardOverview(config);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/overview",
      config,
    );
    expect(result).toEqual(data);
  });

  it("gets recent investigations with pagination", async () => {
    const data = [
      {
        id: 101,
        title: "Database outage",
      },
    ];

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getRecentInvestigations(5, 10);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/recent",
      {
        params: {
          limit: 5,
          offset: 10,
        },
      },
    );
    expect(result).toEqual(data);
  });

  it("gets timeline data", async () => {
    const data = [
      {
        date: "2026-09-29",
        count: 3,
      },
    ];

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getDashboardTimeline();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/timeline",
      undefined,
    );
    expect(result).toEqual(data);
  });

  it("gets severity distribution", async () => {
    const data = [
      {
        severity: "high",
        count: 4,
      },
    ];

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getSeverityDistribution();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/severity",
      undefined,
    );
    expect(result).toEqual(data);
  });

  it("gets root cause analytics", async () => {
    const data = [
      {
        root_cause: "Database",
        count: 5,
      },
    ];

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getRootCauses();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/root-causes",
      undefined,
    );
    expect(result).toEqual(data);
  });

  it("gets failed component analytics", async () => {
    const data = [
      {
        component: "database",
        count: 3,
      },
    ];

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getFailedComponents();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/failed-components",
      undefined,
    );
    expect(result).toEqual(data);
  });

  it("gets confidence analytics", async () => {
    const data = {
      average_confidence: 0.87,
      high_confidence_count: 8,
      medium_confidence_count: 3,
      low_confidence_count: 1,
    };

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getConfidenceAnalytics();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/dashboard/confidence",
      undefined,
    );
    expect(result).toEqual(data);
  });
});
