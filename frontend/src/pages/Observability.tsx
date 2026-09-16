import {
  useQuery,
} from "@tanstack/react-query";

import { useState } from "react";
import {
  getObservabilityFailures,
  getObservabilityHealth,
  getObservabilityRuntime,
  getInvestigationAnalyticsDashboard,
} from "../services/investigationApi";

import { getRecentInvestigations } from "../services/dashboardApi";

import type {
  InvestigationAnalyticsDashboard,
} from "../services/investigationApi";

type JsonObject = Record<string, unknown>;

const isObject = (value: unknown): value is JsonObject => {
  return typeof value === "object" && value !== null;
};

const getObject = (
  source: JsonObject | undefined,
  key: string,
): JsonObject => {
  const value = source?.[key];

  return isObject(value) ? value : {};
};

const getNumber = (
  source: JsonObject | undefined,
  key: string,
): number => {
  const value = source?.[key];

  return typeof value === "number" ? value : 0;
};

const getString = (
  source: JsonObject | undefined,
  key: string,
): string => {
  const value = source?.[key];

  return typeof value === "string" ? value : "—";
};

const formatNumber = (value: number): string => {
  return new Intl.NumberFormat().format(value);
};

const formatDuration = (
  durationMs: number,
): string => {
  if (durationMs === 0) {
    return "0 ms";
  }

  if (durationMs < 1) {
    return `${durationMs.toFixed(2)} ms`;
  }

  if (durationMs < 1000) {
    return `${durationMs.toFixed(1)} ms`;
  }

  return `${(durationMs / 1000).toFixed(2)} s`;
};
const formatTimestamp = (
  timestamp: string | null | undefined,
): string => {
  if (!timestamp) {
    return "—";
  }

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleString();
};
function MetricCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string | number;
  description?: string;
}) {
  return (
    <div className="observability-metric-card">
      <div className="observability-metric-card-label">
        {label}
      </div>

      <div className="observability-metric-card-value">
        {value}
      </div>

      {description && (
        <div className="observability-metric-card-description">
          {description}
        </div>
      )}
    </div>
  );
}

function Observability() {
  const [selectedInvestigationId, setSelectedInvestigationId] =
    useState<number | null>(null);
  const healthQuery = useQuery({
    queryKey: ["observability", "health"],
    queryFn: getObservabilityHealth,
    refetchInterval: 30000,
  });

  const runtimeQuery = useQuery({
    queryKey: ["observability", "runtime"],
    queryFn: getObservabilityRuntime,
    refetchInterval: 30000,
  });

  const failuresQuery = useQuery({
    queryKey: ["observability", "failures"],
    queryFn: getObservabilityFailures,
    refetchInterval: 30000,
  });

  const investigationsQuery = useQuery({
    queryKey: ["observability", "investigations"],
    queryFn: () => getRecentInvestigations(50, 0),
  });

  const analyticsQuery =
    useQuery<InvestigationAnalyticsDashboard>({
      queryKey: [
        "observability",
        "investigation-analytics",
        selectedInvestigationId,
      ],
      queryFn: () =>
        getInvestigationAnalyticsDashboard(
          selectedInvestigationId as number,
        ),
      enabled: selectedInvestigationId !== null,
      refetchInterval: 30000,
    });
  const health = healthQuery.data;
  const runtime = runtimeQuery.data;
  const failures = failuresQuery.data;

  const investigations = investigationsQuery.data ?? [];

  const investigationAnalytics =
    analyticsQuery.data;

  const agentPerformance =
    investigationAnalytics?.agent_performance ?? [];

  const executionTimeline =
    investigationAnalytics?.timeline ?? [];

  const bottlenecks =
    investigationAnalytics?.bottlenecks ?? [];

  const criticalPath =
    investigationAnalytics?.critical_path;

  const criticalPathMs =
    criticalPath?.critical_path_ms ?? 0;

  const criticalPathExecutions =
    criticalPath?.executions ?? [];
  /*
   * Health payload
   *
   * {
   *   status,
   *   shutdown: {...},
   *   execution: {...},
   *   investigations: {...},
   *   failures: {...}
   * }
   */
  const healthExecution = getObject(health, "execution");

  /*
   * Runtime payload
   *
   * {
   *   version,
   *   execution: {...},
   *   resource: {...},
   *   failures: {...}
   * }
   */
  const runtimeExecution = getObject(runtime, "execution");
  const runtimeResource = getObject(runtime, "resource");


  /*
   * Failure payload
   *
   * {
   *   failures: {...},
   *   aggregate: {...}
   * }
   */
  const failureAggregate = getObject(failures, "aggregate");

  const status = getString(health, "status");

  const activeExecutions = getNumber(
    healthExecution,
    "active",
  );

  const totalExecutions = getNumber(
    runtimeExecution,
    "total_executions",
  );

  const failureCount = getNumber(
    failureAggregate,
    "failure_count",
  );

  const retryCount = getNumber(
    failureAggregate,
    "retry_count",
  );

  const timeoutCount = getNumber(
    failureAggregate,
    "timeout_count",
  );

  const activeWorkers = getNumber(
    runtimeResource,
    "active_workers",
  );

  const availableWorkers = getNumber(
    runtimeResource,
    "available_workers",
  );

  const queueDepth = getNumber(
    runtimeResource,
    "queued_count",
  );

  const workerUtilization = getNumber(
    runtimeResource,
    "worker_utilization",
  );

  const isLoading =
    healthQuery.isLoading ||
    runtimeQuery.isLoading ||
    failuresQuery.isLoading;

  const hasError =
    healthQuery.isError ||
    runtimeQuery.isError ||
    failuresQuery.isError;

  if (isLoading) {
    return (
      <section className="page">
        <div className="page-heading">
          <div>
            <h1>Observability</h1>
            <p>
              Monitor system health, runtime activity, and failures.
            </p>
          </div>
        </div>

        <div className="empty-state">
          <h2>Loading observability data...</h2>
          <p>
            Fetching current system metrics.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Observability</h1>

          <p>
            Monitor system health, runtime activity, and failures.
          </p>
        </div>

        <div className="observability-live-indicator">
          <span className="observability-live-dot" />
          Auto-refresh: 30s
        </div>
      </div>

      {hasError && (
        <div className="observability-error">
          <strong>
            Some observability data could not be loaded.
          </strong>

          <span>
            Check the backend connection and authentication session.
          </span>
        </div>
      )}

      {/* ============================= */}
      {/* System Overview */}
      {/* ============================= */}

      <div className="observability-section">
        <div className="observability-section-heading">
          <div>
            <h2>System Overview</h2>

            <p>
              Current health and execution state.
            </p>
          </div>
        </div>

        <div className="observability-card-grid">
          <MetricCard
            label="System Health"
            value={status}
            description="Current backend health status"
          />

          <MetricCard
            label="Active Executions"
            value={formatNumber(activeExecutions)}
            description="Currently running executions"
          />

          <MetricCard
            label="Total Executions"
            value={formatNumber(totalExecutions)}
            description="Recorded runtime executions"
          />

          <MetricCard
            label="Failures"
            value={formatNumber(failureCount)}
            description="Recorded execution failures"
          />

          <MetricCard
            label="Retries"
            value={formatNumber(retryCount)}
            description="Recorded execution retries"
          />

          <MetricCard
            label="Timeouts"
            value={formatNumber(timeoutCount)}
            description="Recorded execution timeouts"
          />
        </div>
      </div>

      {/* ============================= */}
      {/* Runtime Resources */}
      {/* ============================= */}

      <div className="observability-section">
        <div className="observability-section-heading">
          <div>
            <h2>Runtime Resources</h2>

            <p>
              Execution workers and queue utilization.
            </p>
          </div>
        </div>

        <div className="observability-card-grid">
          <MetricCard
            label="Active Workers"
            value={formatNumber(activeWorkers)}
            description="Workers currently processing tasks"
          />

          <MetricCard
            label="Available Workers"
            value={formatNumber(availableWorkers)}
            description="Workers available for execution"
          />

          <MetricCard
            label="Queue Depth"
            value={formatNumber(queueDepth)}
            description="Tasks currently waiting"
          />

          <MetricCard
            label="Worker Utilization"
            value={formatNumber(workerUtilization)}
            description="Current worker utilization"
          />
        </div>
      </div>

      {/* ============================= */}
      {/* Failure Monitoring */}
      {/* ============================= */}

      <div className="observability-section">
        <div className="observability-section-heading">
          <div>
            <h2>Failure Monitoring</h2>

            <p>
              Execution failures, retries, and timeout activity.
            </p>
          </div>
        </div>

        <div className="observability-failure-panel">
          <div className="observability-failure-row">
            <span>Failures</span>
            <strong>
              {formatNumber(failureCount)}
            </strong>
          </div>

          <div className="observability-failure-row">
            <span>Retries</span>
            <strong>
              {formatNumber(retryCount)}
            </strong>
          </div>

          <div className="observability-failure-row">
            <span>Timeouts</span>
            <strong>
              {formatNumber(timeoutCount)}
            </strong>
          </div>
        </div>
      </div>

      {/* ============================= */}
      {/* Investigation Observability */}
      {/* ============================= */}

      <div className="observability-section">
        <div className="observability-section-heading">
          <div>
            <h2>Investigation Observability</h2>

            <p>
              Inspect agent execution performance for a
              specific investigation.
            </p>
          </div>
        </div>

        <div className="observability-investigation-selector">
          <label
            htmlFor="observability-investigation"
          >
            Investigation
          </label>

          <select
            id="observability-investigation"
            value={
              selectedInvestigationId ?? ""
            }
            onChange={(event) => {
              const value = event.target.value;

              setSelectedInvestigationId(
                value ? Number(value) : null,
              );
            }}
            disabled={
              investigationsQuery.isLoading ||
              investigationsQuery.isError
            }
          >
            <option value="">
              Select an investigation...
            </option>

            {investigations.map((investigation) => (
              <option
                key={investigation.id}
                value={investigation.id}
              >
                #{investigation.id} —{" "}
                {investigation.title}
              </option>
            ))}
          </select>

          {investigationsQuery.isLoading && (
            <span className="observability-selector-help">
              Loading investigations...
            </span>
          )}

          {investigationsQuery.isError && (
            <span className="observability-selector-error">
              Unable to load investigations.
            </span>
          )}
        </div>

        {!selectedInvestigationId && (
          <div className="observability-selection-empty">
            <h3>
              Select an investigation
            </h3>

            <p>
              Choose an investigation above to view
              agent performance metrics.
            </p>
          </div>
        )}

        {selectedInvestigationId &&
          analyticsQuery.isLoading && (
            <div className="observability-selection-empty">
              <h3>
                Loading investigation analytics...
              </h3>

              <p>
                Fetching agent execution metrics.
              </p>
            </div>
          )}

        {selectedInvestigationId &&
          analyticsQuery.isError && (
            <div className="observability-error">
              <strong>
                Unable to load investigation analytics.
              </strong>

              <span>
                The selected investigation analytics
                could not be retrieved.
              </span>
            </div>
          )}

        {selectedInvestigationId &&
          !analyticsQuery.isLoading &&
          !analyticsQuery.isError &&
          investigationAnalytics && (
            <div className="observability-agent-panel">
              <div className="observability-agent-header">
                <div>
                  <h3>
                    Agent Performance
                  </h3>

                  <p>
                    Investigation #
                    {selectedInvestigationId}
                  </p>
                </div>

                <span>
                  {agentPerformance.length} agents
                </span>
              </div>

              {agentPerformance.length === 0 ? (
                <div className="observability-selection-empty">
                  <h3>
                    No agent performance data
                  </h3>

                  <p>
                    Agent execution metrics are not
                    available for this investigation yet.
                  </p>
                </div>
              ) : (
                <div className="observability-agent-table-wrapper">
                  <table className="observability-agent-table">
                    <thead>
                      <tr>
                        <th>Agent</th>
                        <th>Executions</th>
                        <th>Successful</th>
                        <th>Failed</th>
                        <th>Avg. Duration</th>
                        <th>Failure Rate</th>
                      </tr>
                    </thead>

                    <tbody>
                      {agentPerformance.map(
                        (agent) => (
                          <tr key={agent.agent}>
                            <td>
                              <strong>
                                {agent.agent}
                              </strong>
                            </td>

                            <td>
                              {formatNumber(
                                agent.executions,
                              )}
                            </td>

                            <td>
                              {formatNumber(
                                agent.successful_executions,
                              )}
                            </td>

                            <td>
                              {formatNumber(
                                agent.failed_executions,
                              )}
                            </td>

                            <td>
                              {formatDuration(
                                agent.average_duration_ms,
                              )}
                            </td>

                            <td>
                              {(
                                agent.failure_rate *
                                100
                              ).toFixed(1)}
                              %
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
      </div>

      {/* ============================= */}
      {/* Execution Timeline */}
      {/* ============================= */}

        {selectedInvestigationId &&
          !analyticsQuery.isLoading &&
          !analyticsQuery.isError &&
          investigationAnalytics && (
            <div className="observability-timeline-panel">
              <div className="observability-agent-header">
                <div>
                  <h3>Execution Timeline</h3>

                  <p>
                    Chronological agent execution activity.
                  </p>
                </div>

                <span>
                  {executionTimeline.length} events
                </span>
              </div>

              {executionTimeline.length === 0 ? (
                <div className="observability-selection-empty">
                  <h3>No timeline data</h3>

                  <p>
                    Execution timeline data is not available
                    for this investigation yet.
                  </p>
                </div>
              ) : (
                <div className="observability-timeline">
                  {executionTimeline.map(
                    (entry, index) => (
                      <div
                        className="observability-timeline-item"
                        key={`${entry.agent ?? "unknown"}-${entry.started_at ?? index}-${index}`}
                      >
                        <div className="observability-timeline-marker">
                          <span />
                        </div>

                        <div className="observability-timeline-content">
                          <div className="observability-timeline-top">
                            <div>
                              <strong>
                                {entry.agent ?? "Unknown agent"}
                              </strong>

                              {entry.action && (
                                <span className="observability-timeline-action">
                                  {entry.action}
                                </span>
                              )}
                            </div>

                            <span
                              className={`observability-status observability-status-${(entry.status ?? "unknown").toLowerCase()}`}
                            >
                              {entry.status ?? "UNKNOWN"}
                            </span>
                          </div>

                          <div className="observability-timeline-details">
                            <span>
                              Started:{" "}
                              {formatTimestamp(
                                entry.started_at,
                              )}
                            </span>

                            <span>
                              Completed:{" "}
                              {formatTimestamp(
                                entry.completed_at,
                              )}
                            </span>

                            <span>
                              Duration:{" "}
                              {formatDuration(
                                entry.duration_ms ?? 0,
                              )}
                            </span>
                          </div>
                        </div>
                      </div>
                    ),
                  )}
                </div>
              )}
            </div>
          )}

        {/* ============================= */}
        {/* Bottlenecks */}
        {/* ============================= */}

        {selectedInvestigationId &&
          !analyticsQuery.isLoading &&
          !analyticsQuery.isError &&
          investigationAnalytics && (
            <div className="observability-agent-panel">
              <div className="observability-agent-header">
                <div>
                  <h3>Performance Bottlenecks</h3>

                  <p>
                    Agent execution performance identified by
                    the analytics engine.
                  </p>
                </div>

                <span>
                  {bottlenecks.length} agents
                </span>
              </div>

              {bottlenecks.length === 0 ? (
                <div className="observability-selection-empty">
                  <h3>No bottleneck data</h3>

                  <p>
                    No bottleneck analysis is available for
                    this investigation yet.
                  </p>
                </div>
              ) : (
                <div className="observability-agent-table-wrapper">
                  <table className="observability-agent-table">
                    <thead>
                      <tr>
                        <th>Agent</th>
                        <th>Avg. Duration</th>
                        <th>Executions</th>
                        <th>Threshold</th>
                        <th>Slowdown Ratio</th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {bottlenecks.map(
                        (bottleneck) => (
                          <tr key={bottleneck.agent}>
                            <td>
                              <strong>
                                {bottleneck.agent}
                              </strong>
                            </td>

                            <td>
                              {formatDuration(
                                bottleneck.average_duration_ms,
                              )}
                            </td>

                            <td>
                              {formatNumber(
                                bottleneck.execution_count,
                              )}
                            </td>

                            <td>
                              {formatDuration(
                                bottleneck.threshold_ms,
                              )}
                            </td>

                            <td>
                              {bottleneck.slowdown_ratio.toFixed(
                                2,
                              )}
                              ×
                            </td>

                            <td>
                              <span
                                className={
                                  bottleneck.is_bottleneck
                                    ? "observability-bottleneck-flag"
                                    : "observability-normal-flag"
                                }
                              >
                                {bottleneck.is_bottleneck
                                  ? "BOTTLENECK"
                                  : "NORMAL"}
                              </span>
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

      {/* ============================= */}
      {/* Critical Path */}
      {/* ============================= */}

      {selectedInvestigationId &&
        !analyticsQuery.isLoading &&
        !analyticsQuery.isError &&
        investigationAnalytics && (
          <div className="observability-critical-path-panel">
            <div className="observability-agent-header">
              <div>
                <h3>Critical Path</h3>

                <p>
                  Longest execution path identified by the
                  investigation analytics engine.
                </p>
              </div>
            </div>

            <div className="observability-critical-path-content">
              <div className="observability-critical-path-metric">
                <span>Critical Path Duration</span>

                <strong>
                  {formatDuration(criticalPathMs)}
                </strong>
              </div>

              <div className="observability-critical-path-executions">
                <span className="observability-critical-path-label">
                  Executions
                </span>

                {criticalPathExecutions.length === 0 ? (
                  <div className="observability-selection-empty">
                    <p>
                      No critical-path execution data is
                      available.
                    </p>
                  </div>
                ) : (
                  <div className="observability-critical-path-list">
                    {criticalPathExecutions.map(
                      (execution, index) => (
                        <div
                          className="observability-critical-path-item"
                          key={`${execution}-${index}`}
                        >
                          <span className="observability-critical-path-index">
                            {index + 1}
                          </span>

                          <span>
                            {execution}
                          </span>
                        </div>
                      ),
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

    </section>
  );
}

export default Observability;
