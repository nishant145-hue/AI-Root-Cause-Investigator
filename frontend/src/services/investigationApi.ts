import api from "./api";

import type {
  Investigation,
  InvestigationCreate,
} from "../types/investigation";

export interface RunAIInvestigationRequest {
  log_file_id: number;
}

/*
 * ============================================================
 * Investigation History
 * ============================================================
 */

export type InvestigationAction = string;

export interface InvestigationHistory {
  id: number;
  investigation_id: number;
  user_id: number;
  action: InvestigationAction;
  old_value?: string | null;
  new_value?: string | null;
  created_at: string;
}

export interface InvestigationHistoryList {
  items: InvestigationHistory[];
  total: number;
}

/*
 * ============================================================
 * Analytics
 * ============================================================
 */

export interface AnalyticsOverview {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  total_duration_ms: number;
  average_duration_ms: number;
  retry_count: number;
  success_rate: number;
  failure_rate: number;
  efficiency_score: number;
  slowest_agent: string | null;
  bottleneck_count: number;
  total_agents: number;
}

export interface AgentPerformance {
  agent: string;
  executions: number;
  successful_executions: number;
  failed_executions: number;
  total_duration_ms: number;
  average_duration_ms: number;
  failure_rate: number;
}

export interface Bottleneck {
  agent: string;
  average_duration_ms: number;
  execution_count: number;
  threshold_ms: number;
  slowdown_ratio: number;
  is_bottleneck: boolean;
}

export interface FailureRetryMetrics {
  total_failures: number;
  total_retries: number;
  failed_agents: Record<string, number>;
  retry_by_agent: Record<string, number>;
}

export interface ExecutionTimelineEntry {
  agent: string | null;
  action: string | null;
  status: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  metadata: Record<string, unknown>;
}

export interface InvestigationAnalyticsDashboard {
  investigation_id: number;
  overview: AnalyticsOverview;
  agent_performance?: AgentPerformance[];
  bottlenecks?: Bottleneck[];
  failure_retry_metrics: FailureRetryMetrics;
  timeline?: ExecutionTimelineEntry[];
  critical_path?: {
    critical_path_ms: number;
    executions: string[];
  };
}

/*
 * ============================================================
 * Generic Analytics
 * ============================================================
 */

export interface InvestigationAnalytics {
  investigation_id: number;
  analytics: Record<string, unknown>;
}

/*
 * ============================================================
 * Observability
 *
 * The backend declares these responses as arbitrary JSON
 * objects, so we intentionally keep them flexible instead
 * of inventing fields that aren't guaranteed by OpenAPI.
 * ============================================================
 */

export type InvestigationObservability =
  Record<string, unknown>;

export type InvestigationTimeline =
  Record<string, unknown>;

export type InvestigationCriticalPath =
  Record<string, unknown>;

/*
 * ============================================================
 * Create Investigation
 * ============================================================
 */

export const createInvestigation = async (
  data: InvestigationCreate,
): Promise<Investigation> => {
  const response = await api.post<Investigation>(
    "/api/v1/investigations",
    data,
  );

  return response.data;
};

/*
 * ============================================================
 * Get Investigation
 * ============================================================
 */

export const getInvestigation = async (
  investigationId: number,
): Promise<Investigation> => {
  const response = await api.get<Investigation>(
    `/api/v1/investigations/${investigationId}`,
  );

  return response.data;
};

/*
 * ============================================================
 * Run AI Investigation
 * ============================================================
 */

export const runAIInvestigation = async (
  investigationId: number,
  data: RunAIInvestigationRequest,
): Promise<Investigation> => {
  const response = await api.post<Investigation>(
    `/api/v1/investigations/${investigationId}/run`,
    data,
  );

  return response.data;
};

/*
 * ============================================================
 * Investigation History
 * ============================================================
 */

export const getInvestigationHistory = async (
  investigationId: number,
): Promise<InvestigationHistoryList> => {
  const response =
    await api.get<InvestigationHistoryList>(
      `/api/v1/investigations/${investigationId}/history`,
    );

  return response.data;
};

/*
 * ============================================================
 * Investigation Analytics
 * ============================================================
 */

export const getInvestigationAnalytics = async (
  investigationId: number,
): Promise<InvestigationAnalytics> => {
  const response =
    await api.get<InvestigationAnalytics>(
      `/api/v1/investigations/${investigationId}/analytics`,
    );

  return response.data;
};

/*
 * ============================================================
 * Investigation Analytics Dashboard
 * ============================================================
 */

export const getInvestigationAnalyticsDashboard =
  async (
    investigationId: number,
  ): Promise<InvestigationAnalyticsDashboard> => {
    const response =
      await api.get<InvestigationAnalyticsDashboard>(
        `/api/v1/investigations/${investigationId}/analytics/dashboard`,
      );

    return response.data;
  };

/*
 * ============================================================
 * Observability
 * ============================================================
 */

export const getInvestigationObservability =
  async (
    investigationId: number,
  ): Promise<InvestigationObservability> => {
    const response =
      await api.get<InvestigationObservability>(
        `/api/v1/observability/investigations/${investigationId}`,
      );

    return response.data;
  };

/*
 * ============================================================
 * Observability Timeline
 * ============================================================
 */

export const getInvestigationTimeline =
  async (
    investigationId: number,
  ): Promise<InvestigationTimeline> => {
    const response =
      await api.get<InvestigationTimeline>(
        `/api/v1/observability/investigations/${investigationId}/timeline`,
      );

    return response.data;
  };

/*
 * ============================================================
 * Observability Critical Path
 * ============================================================
 */

export const getInvestigationCriticalPath =
  async (
    investigationId: number,
  ): Promise<InvestigationCriticalPath> => {
    const response =
      await api.get<InvestigationCriticalPath>(
        `/api/v1/observability/investigations/${investigationId}/critical-path`,
      );

    return response.data;
  };

export interface ObservabilityHealth {
  [key: string]: unknown;
}

export interface ObservabilityRuntime {
  [key: string]: unknown;
}

export interface ObservabilityFailures {
  [key: string]: unknown;
}

export interface InvestigationObservabilitySummary {
  [key: string]: unknown;
}

export const getObservabilityHealth =
  async (): Promise<ObservabilityHealth> => {
    const response =
      await api.get<ObservabilityHealth>(
        "/api/v1/observability/health",
      );

    return response.data;
  };

export const getObservabilityRuntime =
  async (): Promise<ObservabilityRuntime> => {
    const response =
      await api.get<ObservabilityRuntime>(
        "/api/v1/observability/runtime",
      );

    return response.data;
  };

export const getObservabilityFailures =
  async (): Promise<ObservabilityFailures> => {
    const response =
      await api.get<ObservabilityFailures>(
        "/api/v1/observability/failures",
      );

    return response.data;
  };

export const getInvestigationObservabilitySummary =
  async (
    investigationId: number,
  ): Promise<InvestigationObservabilitySummary> => {
    const response =
      await api.get<InvestigationObservabilitySummary>(
        `/api/v1/observability/investigations/${investigationId}/summary`,
      );

    return response.data;
  };