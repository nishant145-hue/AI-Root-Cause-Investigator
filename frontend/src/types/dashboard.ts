export interface DashboardOverview {
  total_investigations: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  resolved: number;
  pending: number;
  average_confidence: number;
  average_duration_seconds: number;
}

export interface RecentInvestigation {
  id: number;
  title: string;
  status: string;
  severity?: string | null;
  confidence?: number | null;
  root_cause?: string | null;
  failed_component?: string | null;
  created_at: string;
}

export interface TimelinePoint {
  date: string;
  count: number;
}

export interface SeverityAnalytics {
  severity?: string | null;
  count: number;
}

export interface RootCauseAnalytics {
  root_cause: string;
  count: number;
}

export interface FailedComponentAnalytics {
  component: string;
  count: number;
}

export interface ConfidenceAnalytics {
  average_confidence: number;
  minimum_confidence: number;
  maximum_confidence: number;
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
}