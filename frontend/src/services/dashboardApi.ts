import api, {
  type ApiRequestConfig,
} from "./api";

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
  async (
    config?: ApiRequestConfig,
  ): Promise<DashboardOverview> => {
    const response = await api.get<DashboardOverview>(
      "/api/v1/dashboard/overview",
      config,
    );

    return response.data;
  };

export const getRecentInvestigations = async (
  limit = 10,
  offset = 0,
  config?: ApiRequestConfig,
): Promise<RecentInvestigation[]> => {
  const response = await api.get<RecentInvestigation[]>(
    "/api/v1/dashboard/recent",
    {
      params: {
        limit,
        offset,
      },
      ...config,
    },
  );

  return response.data;
};

export const getDashboardTimeline =
  async (
    config?: ApiRequestConfig,
  ): Promise<TimelinePoint[]> => {
    const response = await api.get<TimelinePoint[]>(
      "/api/v1/dashboard/timeline",
      config,
    );

    return response.data;
  };

export const getSeverityDistribution =
  async (
    config?: ApiRequestConfig,
  ): Promise<SeverityAnalytics[]> => {
    const response = await api.get<SeverityAnalytics[]>(
      "/api/v1/dashboard/severity",
      config,
    );

    return response.data;
  };

export const getRootCauses =
  async (
    config?: ApiRequestConfig,
  ): Promise<RootCauseAnalytics[]> => {
    const response = await api.get<RootCauseAnalytics[]>(
      "/api/v1/dashboard/root-causes",
      config,
    );

    return response.data;
  };

export const getFailedComponents =
  async (
    config?: ApiRequestConfig,
  ): Promise<FailedComponentAnalytics[]> => {
    const response =
      await api.get<FailedComponentAnalytics[]>(
        "/api/v1/dashboard/failed-components",
        config,
      );

    return response.data;
  };

export const getConfidenceAnalytics =
  async (
    config?: ApiRequestConfig,
  ): Promise<ConfidenceAnalytics> => {
    const response =
      await api.get<ConfidenceAnalytics>(
        "/api/v1/dashboard/confidence",
        config,
      );

    return response.data;
  };