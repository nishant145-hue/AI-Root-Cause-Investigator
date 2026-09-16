import api from "./api";

import type {
  ConfidenceAnalytics,
  DashboardOverview,
  FailedComponentAnalytics,
  RecentInvestigation,
  RootCauseAnalytics,
  SeverityAnalytics,
  TimelinePoint,
} from "../types/dashboard";

export const getDashboardOverview =
  async (): Promise<DashboardOverview> => {
    const response = await api.get<DashboardOverview>(
      "/api/v1/dashboard/overview",
    );

    return response.data;
  };

export const getRecentInvestigations = async (
  limit = 10,
  offset = 0,
): Promise<RecentInvestigation[]> => {
  const response = await api.get<RecentInvestigation[]>(
    "/api/v1/dashboard/recent",
    {
      params: {
        limit,
        offset,
      },
    },
  );

  return response.data;
};

export const getDashboardTimeline =
  async (): Promise<TimelinePoint[]> => {
    const response = await api.get<TimelinePoint[]>(
      "/api/v1/dashboard/timeline",
    );

    return response.data;
  };

export const getSeverityDistribution =
  async (): Promise<SeverityAnalytics[]> => {
    const response = await api.get<SeverityAnalytics[]>(
      "/api/v1/dashboard/severity",
    );

    return response.data;
  };

export const getRootCauses =
  async (): Promise<RootCauseAnalytics[]> => {
    const response = await api.get<RootCauseAnalytics[]>(
      "/api/v1/dashboard/root-causes",
    );

    return response.data;
  };

export const getFailedComponents =
  async (): Promise<FailedComponentAnalytics[]> => {
    const response =
      await api.get<FailedComponentAnalytics[]>(
        "/api/v1/dashboard/failed-components",
      );

    return response.data;
  };

export const getConfidenceAnalytics =
  async (): Promise<ConfidenceAnalytics> => {
    const response =
      await api.get<ConfidenceAnalytics>(
        "/api/v1/dashboard/confidence",
      );

    return response.data;
  };