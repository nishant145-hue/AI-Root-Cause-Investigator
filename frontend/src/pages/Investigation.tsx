import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  getInvestigation,
  runAIInvestigation,
  getInvestigationAnalyticsDashboard,
  getInvestigationHistory,
  type InvestigationAnalyticsDashboard,
  type InvestigationHistoryList,
} from "../services/investigationApi";

import {
  getUploads,
  type Upload,
} from "../services/uploadApi";

function getStatusLabel(status?: string | null): string {
  if (!status) {
    return "Unknown";
  }

  switch (status.toUpperCase()) {
    case "OPEN":
      return "Open";
    case "IN_PROGRESS":
      return "In Progress";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
    default:
      return status;
  }
}

function formatDate(value?: string | null): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}


function hasValidatedRootCause(
  rootCause?: string | null,
): boolean {
  return Boolean(rootCause?.trim());
}


const formatDuration = (durationMs: number | null | undefined) => {
    if (durationMs === null || durationMs === undefined) {
        return "—";
    }

    if (durationMs === 0) {
        return "0 ms";
    }

    if (durationMs < 0.01) {
        return "< 0.01 ms";
    }

    if (durationMs < 1) {
        return `${durationMs.toFixed(2)} ms`;
    }

    if (durationMs < 1000) {
        return `${durationMs.toFixed(1)} ms`;
    }

    return `${(durationMs / 1000).toFixed(2)} s`;
};

function getErrorMessage(error: unknown): string {
  if (
    error &&
    typeof error === "object" &&
    "response" in error
  ) {
    const response = (
      error as {
        response?: {
          data?: {
            detail?: string | Array<{ msg?: string }>;
          };
        };
      }
    ).response;

    const detail = response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join(", ");
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

function Investigation() {
  const { investigationId } = useParams<{
    investigationId: string;
  }>();

  const queryClient = useQueryClient();

  const [selectedLogFileId, setSelectedLogFileId] =
    useState<number | null>(null);

  const parsedInvestigationId = Number(investigationId);

  const validInvestigationId =
    Number.isInteger(parsedInvestigationId) &&
    parsedInvestigationId > 0;

  /*
   * --------------------------------------------------------------------------
   * Investigation
   * --------------------------------------------------------------------------
   */

  const investigationQuery = useQuery({
    queryKey: [
      "investigation",
      parsedInvestigationId,
    ],
    queryFn: () =>
      getInvestigation(parsedInvestigationId),
    enabled: validInvestigationId,
  });

  /*
   * --------------------------------------------------------------------------
   * Uploaded log files
   * --------------------------------------------------------------------------
   */

  const uploadsQuery = useQuery<Upload[]>({
    queryKey: ["uploads"],
    queryFn: getUploads,
  });

  /*
   * --------------------------------------------------------------------------
   * AI Analytics Dashboard
   * --------------------------------------------------------------------------
   */

  const analyticsQuery =
    useQuery<InvestigationAnalyticsDashboard>({
      queryKey: [
        "investigation-analytics-dashboard",
        parsedInvestigationId,
      ],
      queryFn: () =>
        getInvestigationAnalyticsDashboard(
          parsedInvestigationId,
        ),
      enabled: validInvestigationId,
    });

  /*
   * --------------------------------------------------------------------------
   * Investigation History
   * --------------------------------------------------------------------------
   */

  const historyQuery =
    useQuery<InvestigationHistoryList>({
      queryKey: [
        "investigation-history",
        parsedInvestigationId,
      ],
      queryFn: () =>
        getInvestigationHistory(
          parsedInvestigationId,
        ),
      enabled: validInvestigationId,
    });

  /*
   * --------------------------------------------------------------------------
   * Automatically select first uploaded log
   * --------------------------------------------------------------------------
   */

  useEffect(() => {
    if (
      selectedLogFileId === null &&
      uploadsQuery.data &&
      uploadsQuery.data.length > 0
    ) {
      setSelectedLogFileId(
        uploadsQuery.data[0].id,
      );
    }
  }, [
    uploadsQuery.data,
    selectedLogFileId,
  ]);

  /*
   * --------------------------------------------------------------------------
   * Run AI investigation
   * --------------------------------------------------------------------------
   */

  const runMutation = useMutation({
    mutationFn: () => {
      if (selectedLogFileId === null) {
        throw new Error(
          "Please select a log file before running the investigation.",
        );
      }

      return runAIInvestigation(
        parsedInvestigationId,
        {
          log_file_id: selectedLogFileId,
        },
      );
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [
          "investigation",
          parsedInvestigationId,
        ],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "investigation-analytics-dashboard",
          parsedInvestigationId,
        ],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "investigation-history",
          parsedInvestigationId,
        ],
      });
    },
  });

  /*
   * --------------------------------------------------------------------------
   * Invalid ID
   * --------------------------------------------------------------------------
   */

  if (!validInvestigationId) {
    return (
      <div className="page-container">
        <section className="investigation-section">
          <h1>Invalid Investigation</h1>

          <p className="error-text">
            The investigation ID is invalid.
          </p>

          <Link
            to="/investigations"
            className="button"
          >
            Back to Investigations
          </Link>
        </section>
      </div>
    );
  }

  /*
   * --------------------------------------------------------------------------
   * Loading
   * --------------------------------------------------------------------------
   */

  if (investigationQuery.isLoading) {
    return (
      <div className="page-container">
        <section className="investigation-section">
          <h1>Investigation</h1>
          <p className="muted-text">
            Loading investigation...
          </p>
        </section>
      </div>
    );
  }

  /*
   * --------------------------------------------------------------------------
   * Error
   * --------------------------------------------------------------------------
   */

  if (investigationQuery.isError) {
    return (
      <div className="page-container">
        <section className="investigation-section">
          <h1>Investigation</h1>

          <p className="error-text">
            {getErrorMessage(
              investigationQuery.error,
            )}
          </p>

          <Link
            to="/investigations"
            className="button"
          >
            Back to Investigations
          </Link>
        </section>
      </div>
    );
  }

  const investigation =
    investigationQuery.data;

  if (!investigation) {
    return (
      <div className="page-container">
        <section className="investigation-section">
          <h1>Investigation Not Found</h1>

          <p className="muted-text">
            The requested investigation could not
            be found.
          </p>

          <Link
            to="/investigations"
            className="button"
          >
            Back to Investigations
          </Link>
        </section>
      </div>
    );
  }

  const analytics =
    analyticsQuery.data;

  const criticalPath = analytics?.critical_path;

  const overview =
    analytics?.overview;

  const failureRetryMetrics =
    analytics?.failure_retry_metrics;

  /*
   * --------------------------------------------------------------------------
   * Render
   * --------------------------------------------------------------------------
   */

  return (
    <div className="page-container investigation-page">
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                             */}
      {/* ------------------------------------------------------------------ */}

      <div className="investigation-page-header">
        <div>
          <Link
            to="/investigations"
            className="back-link"
          >
            ← Back to Investigations
          </Link>

          <h1>{investigation.title}</h1>

          {investigation.description && (
            <p className="investigation-description">
              {investigation.description}
            </p>
          )}
        </div>

        <div className="investigation-status-badge">
          {getStatusLabel(
            investigation.status,
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Investigation Information                                          */}
      {/* ------------------------------------------------------------------ */}

      <section className="investigation-section">
        <div className="section-header">
          <div>
            <h2>Investigation Details</h2>

            <p>
              Basic information about this
              investigation.
            </p>
          </div>
        </div>

        <div className="investigation-details-grid">
          <div className="result-row">
            <span>Investigation ID</span>
            <strong>
              {investigation.id}
            </strong>
          </div>

          <div className="result-row">
            <span>Status</span>
            <strong>
              {getStatusLabel(
                investigation.status,
              )}
            </strong>
          </div>

          <div className="result-row">
            <span>Created</span>
            <strong>
              {formatDate(
                investigation.created_at,
              )}
            </strong>
          </div>

          <div className="result-row">
            <span>Updated</span>
            <strong>
              {formatDate(
                investigation.updated_at,
              )}
            </strong>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Run AI Investigation                                                */}
      {/* ------------------------------------------------------------------ */}

      <section className="investigation-section investigation-run-card">
        <div className="section-header">
          <div>
            <h2>Run AI Investigation</h2>

            <p>
              Select a parsed log file and run the
              AI root cause investigation.
            </p>
          </div>
        </div>

        <div className="investigation-run-controls">
          <div className="form-group">
            <label htmlFor="log-file">
              Log File
            </label>

            <select
              id="log-file"
              value={
                selectedLogFileId ?? ""
              }
              onChange={(event) => {
                const value =
                  Number(event.target.value);

                setSelectedLogFileId(
                  Number.isInteger(value) &&
                    value > 0
                    ? value
                    : null,
                );
              }}
              disabled={
                uploadsQuery.isLoading ||
                runMutation.isPending
              }
            >
              <option value="">
                Select a log file
              </option>

              {uploadsQuery.data?.map(
                (upload) => (
                  <option
                    key={upload.id}
                    value={upload.id}
                  >
                    #{upload.id} —{" "}
                    {upload.filename}{" "}
                    ({upload.parsed_logs} parsed
                    logs)
                  </option>
                ),
              )}
            </select>
          </div>

          <button
            type="button"
            className="button primary-button"
            onClick={() =>
              runMutation.mutate()
            }
            disabled={
              selectedLogFileId === null ||
              runMutation.isPending ||
              uploadsQuery.isLoading
            }
          >
            {runMutation.isPending
              ? "Running AI Investigation..."
              : "Run AI Investigation"}
          </button>
        </div>

        {uploadsQuery.isLoading && (
          <p className="muted-text">
            Loading uploaded log files...
          </p>
        )}

        {uploadsQuery.isError && (
          <p className="error-text">
            Unable to load uploaded log files:{" "}
            {getErrorMessage(
              uploadsQuery.error,
            )}
          </p>
        )}

        {!uploadsQuery.isLoading &&
          uploadsQuery.data &&
          uploadsQuery.data.length === 0 && (
            <p className="muted-text">
              No uploaded log files are
              available. Upload a log file first.
            </p>
          )}

        {runMutation.isPending && (
          <div className="investigation-running">
            <div className="loader-spinner" />

            <div>
              <strong>
                AI investigation is running
              </strong>

              <p>
                The backend is analyzing the
                selected logs. This may take some
                time.
              </p>
            </div>
          </div>
        )}

        {runMutation.isError && (
          <div className="investigation-error">
            <strong>
              Investigation failed
            </strong>

            <p>
              {getErrorMessage(
                runMutation.error,
              )}
            </p>
          </div>
        )}

        {runMutation.isSuccess && (
          <div className="investigation-success">
            <strong>
              {hasValidatedRootCause(
                investigation.root_cause,
              )
                ? "AI investigation completed"
                : "AI investigation completed without a validated root cause"}
            </strong>

            <p>
              {hasValidatedRootCause(
                investigation.root_cause,
              )
                ? "The AI identified and validated a likely root cause. The investigation results have been refreshed below."
                : "The investigation completed successfully, but the available evidence was insufficient to validate a root cause."}
            </p>
          </div>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* AI Root Cause Results                                               */}
      {/* ------------------------------------------------------------------ */}

      <section className="investigation-section">
        <div className="section-header">
          <div>
            <h2>AI Root Cause Results</h2>

            <p>
              {hasValidatedRootCause(
                investigation.root_cause,
              )
                ? "Findings produced and validated by the AI investigation."
                : "Results from the AI investigation and evidence analysis."}
            </p>
          </div>
        </div>

        <div className="investigation-details-grid">
          <div className="result-row">
            <span>Severity</span>

            <strong>
              {investigation.severity ?? "Not determined"}
            </strong>
          </div>

          <div className="result-row">
            <span>Confidence</span>

            <strong>
              {
                investigation.confidence ??"Not determined"
              }
            </strong>
          </div>

          <div className="result-row">
            <span>Failed Component</span>

            <strong>
              {investigation.failed_component ??
                "Not determined"}
            </strong>
          </div>

          <div className="result-row">
            <span>Status</span>

            <strong>
              {hasValidatedRootCause(
                investigation.root_cause,
              )
                ? getStatusLabel(investigation.status)
                : investigation.status?.toUpperCase() ===
                  "COMPLETED"
                ? "Completed — No Root Cause"
                : getStatusLabel(investigation.status)}
            </strong>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Root Cause                                                          */}
      {/* ------------------------------------------------------------------ */}

      <section className="investigation-section">
        <div className="section-header">
          <div>
            <h2>Root Cause</h2>

            <p>
              AI-generated root cause assessment.
            </p>
          </div>
        </div>

        <div className="root-cause-result">
          {investigation.root_cause ? (
            <p>
              {investigation.root_cause}
            </p>
          ) : investigation.status?.toUpperCase() ===
            "COMPLETED" ? (
            <p className="muted-text">
              No root cause could be validated from the
              available evidence.
            </p>
          ) : (
            <p className="muted-text">
              No root cause has been generated yet.
            </p>
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Summary                                                             */}
      {/* ------------------------------------------------------------------ */}

      <section className="investigation-section">
        <div className="section-header">
          <div>
            <h2>Investigation Summary</h2>

            <p>
              Summary of the AI investigation.
            </p>
          </div>
        </div>

        <div className="investigation-text-block">
          {investigation.summary ? (
            <p>
              {investigation.summary}
            </p>
          ) : (
            <p className="muted-text">
              No summary is available yet.
            </p>
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Additional Notes                                                    */}
      {/* ------------------------------------------------------------------ */}

      {investigation.additional_notes && (
        <section className="investigation-section">
          <div className="section-header">
            <div>
              <h2>Additional Notes</h2>
            </div>
          </div>

          <div className="investigation-text-block">
            <p>
              {investigation.additional_notes}
            </p>
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* AI Execution Analytics                                              */}
      {/* ------------------------------------------------------------------ */}

      <section className="investigation-section">
        <div className="section-header">
          <div>
            <h2>AI Execution Analytics</h2>

            <p>
              Performance information from the
              investigation agents.
            </p>
          </div>
        </div>

        {analyticsQuery.isLoading && (
          <p className="muted-text">
            Loading analytics...
          </p>
        )}

        {analyticsQuery.isError && (
          <p className="error-text">
            Analytics are currently
            unavailable.
          </p>
        )}

        {analyticsQuery.isSuccess &&
          !analytics && (
            <p className="muted-text">
              No analytics data is available yet.
            </p>
          )}

        {overview && (
          <>
            <div className="analytics-grid">
              <div className="analytics-card">
                <span>
                  Total Executions
                </span>

                <strong>
                  {overview.total_executions}
                </strong>
              </div>

              <div className="analytics-card">
                <span>
                  Successful
                </span>

                <strong>
                  {
                    overview.successful_executions
                  }
                </strong>
              </div>

              <div className="analytics-card">
                <span>Failed</span>

                <strong>
                  {
                    overview.failed_executions
                  }
                </strong>
              </div>

              <div className="analytics-card">
                <span>Retries</span>

                <strong>
                  {overview.retry_count}
                </strong>
              </div>

              <div className="analytics-card">
                <span>
                  Average Duration
                </span>

                <strong>
                  {formatDuration(overview.average_duration_ms)}{" "}

                </strong>
              </div>

              <div className="analytics-card">
                <span>
                  Efficiency Score
                </span>

                <strong>
                  {overview.efficiency_score.toFixed(
                    1,
                  )}
                  %
                </strong>
              </div>

              <div className="analytics-card">
                <span>
                  Success Rate
                </span>

                <strong>
                  {(
                    overview.success_rate * 100
                  ).toFixed(1)}
                  %
                </strong>
              </div>

              <div className="analytics-card">
                <span>
                  Failure Rate
                </span>

                <strong>
                  {(
                    overview.failure_rate * 100
                  ).toFixed(1)}
                  %
                </strong>
              </div>

              <div className="analytics-card">
                <span>
                  Total Agents
                </span>

                <strong>
                  {overview.total_agents}
                </strong>
              </div>
            </div>

            <div className="investigation-details-grid analytics-extra-details">
              <div className="result-row">
                <span>
                  Slowest Agent
                </span>

                <strong>
                  {overview.slowest_agent ??
                    "—"}
                </strong>
              </div>

              <div className="result-row">
                <span>
                  Bottleneck Count
                </span>

                <strong>
                  {overview.bottleneck_count}
                </strong>
              </div>

              <div className="result-row">
                <span>
                  Total Duration
                </span>

                <strong>
                  {formatDuration(
                    overview.total_duration_ms,
                  )}
                </strong>
              </div>
            </div>
          </>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Agent Performance                                                   */}
      {/* ------------------------------------------------------------------ */}

      {analytics?.agent_performance &&
        analytics.agent_performance.length > 0 && (
          <section className="investigation-section">
            <div className="section-header">
            <div>
              <h2>Agent Performance</h2>
                <p>
                  Execution performance and reliability metrics for each AI
                  agent.
                </p>
            </div>
          </div>

          <div className="analytics-table-wrapper">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Executions</th>
                  <th>Successful</th>
                  <th>Failed</th>
                  <th>Total Duration</th>
                  <th>Avg Duration</th>
                  <th>Failure Rate</th>
                </tr>
              </thead>

              <tbody>
                {analytics.agent_performance.map((agent) => (
                  <tr key={agent.agent}>
                    <td>
                      <strong>{agent.agent}</strong>
                    </td>

                    <td>{agent.executions}</td>

                    <td>{agent.successful_executions}</td>

                    <td>{agent.failed_executions}</td>

                    <td>
                      {formatDuration(agent.total_duration_ms)}
                    </td>

                    <td>
                      {formatDuration(agent.average_duration_ms)}
                    </td>

                    <td>
                      {(agent.failure_rate * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Failure and Retry Metrics                                           */}
      {/* ------------------------------------------------------------------ */}

      {failureRetryMetrics && (
        <section className="investigation-section">
          <div className="section-header">
            <div>
              <h2>Failure & Retry Metrics</h2>
                <p>
                  Agent execution failures and retry activity for this
                  investigation.
                </p>
            </div>
          </div>

          <div className="analytics-grid">
            <div className="analytics-card">
              <span>Total Failures</span>

              <strong>
                {failureRetryMetrics.total_failures}
              </strong>
            </div>

            <div className="analytics-card">
              <span>Total Retries</span>

              <strong>
                {failureRetryMetrics.total_retries}
              </strong>
            </div>
          </div>

          {Object.keys(failureRetryMetrics.failed_agents).length > 0 ? (
            <div className="analytics-subsection">
              <h3>Failed Agents</h3>

              <div className="analytics-table-wrapper">
                <table className="analytics-table">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Failures</th>
                    </tr>
                  </thead>

                  <tbody>
                    {Object.entries(
                      failureRetryMetrics.failed_agents,
                    ).map(([agent, count]) => (
                    <tr key={agent}>
                      <td>
                        <strong>{agent}</strong>
                      </td>

                      <td>{count}</td>
                    </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="analytics-subsection">
              <h3>Failed Agents</h3>
              <p className="muted-text">
                No agent execution failures recorded.
              </p>
            </div>
          )}

          {Object.keys(failureRetryMetrics.retry_by_agent).length > 0 ? (
            <div className="analytics-subsection">
              <h3>Retries by Agent</h3>

              <div className="analytics-table-wrapper">
                <table className="analytics-table">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Retries</th>
                    </tr>
                  </thead>

                  <tbody>
                    {Object.entries(
                      failureRetryMetrics.retry_by_agent,
                    ).map(([agent, count]) => (
                      <tr key={agent}>
                        <td>
                          <strong>{agent}</strong>
                        </td>

                        <td>{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="analytics-subsection">
              <h3>Retries by Agent</h3>
                <p className="muted-text">
                  No retry activity recorded.
                </p>
            </div>
          )}
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Bottlenecks                                                         */}
      {/* ------------------------------------------------------------------ */}

      {analytics?.bottlenecks &&
        analytics.bottlenecks.length >
          0 && (
          <section className="investigation-section">
            <div className="section-header">
              <div>
                <h2>
                  Performance Bottlenecks
                </h2>

                <p>
                  Agents exceeding their
                  configured execution
                  threshold.
                </p>
              </div>
            </div>

            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>
                      Average Duration
                    </th>
                    <th>
                      Executions
                    </th>
                    <th>
                      Threshold
                    </th>
                    <th>Slowdown Ratio</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {analytics.bottlenecks.map(
                    (bottleneck) => (
                      <tr
                        key={
                          bottleneck.agent
                        }
                      >
                        <td>
                          <strong>
                            {
                              bottleneck.agent
                            }
                          </strong>
                        </td>

                        <td>
                          {formatDuration(
                            bottleneck.average_duration_ms,
                          )}
                        </td>

                        <td>
                          {
                            bottleneck.execution_count
                          }
                        </td>

                        <td>
                          {formatDuration(
                            bottleneck.threshold_ms,
                          )}
                        </td>

                        <td>
                          {Number.isFinite(bottleneck.slowdown_ratio)
                            ? `${bottleneck.slowdown_ratio.toFixed(1)}×`
                            : "—"}
                        </td>

                        <td>
                          {bottleneck.is_bottleneck
                            ? "Bottleneck"
                            : "Normal"}
                        </td>

                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}


      {/* Execution Timeline */}
      <section className="analytics-section">
        <div className="section-header">
          <div>
            <h2>Execution Timeline</h2>
            <p>
              Chronological view of AI agent execution during this investigation.
            </p>
          </div>
        </div>

        {!analytics?.timeline ||
          analytics.timeline.length === 0 ? (
            <div className="analytics-empty-state">
              <strong>No execution timeline available.</strong>
                <p>
                  Timeline events will appear after the investigation has executed.
                </p>
            </div>
          ) : (
            <div className="execution-timeline">
              {analytics.timeline.map((entry, index) => (
                <div
                  className="execution-timeline-item"
                  key={`${entry.agent ?? "agent"}-${entry.action ?? "action"}-${index}`}
                >
                <div className="execution-timeline-marker">
                  {index + 1}
                </div>

                <div className="execution-timeline-content">
                  <div className="execution-timeline-header">
                    <div>
                      <strong>
                        {entry.agent ?? "Unknown agent"}
                      </strong>

                      {entry.action && (
                        <span className="execution-timeline-action">
                          {entry.action}
                        </span>
                      )}
                    </div>

                    <span
                      className={`execution-status execution-status-${(
                        entry.status ?? "unknown"
                      ).toLowerCase()}`}
                    >
                      {entry.status ?? "Unknown"}
                    </span>
                  </div>

                  <div className="execution-timeline-details">
                    <span>
                      <strong>Started:</strong>{" "}
                      {entry.started_at
                        ? new Date(entry.started_at).toLocaleString()
                        : "—"}
                    </span>

                    <span>
                      <strong>Completed:</strong>{" "}
                      {entry.completed_at
                        ? new Date(entry.completed_at).toLocaleString()
                        : "—"}
                    </span>

                    <span>
                      <strong>Duration:</strong>{" "}
                        {formatDuration(entry.duration_ms)}
                    </span>
                  </div>

                  {Object.keys(entry.metadata ?? {}).length > 0 && (
                    <details className="execution-timeline-metadata">
                      <summary>Metadata</summary>

                      <pre>
                        {JSON.stringify(
                        entry.metadata,
                        null,
                        2,
                        )}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="analytics-section">
        <div className="section-header">
          <div>
            <h2>Critical Path</h2>
            <p>
              Execution path contributing to the investigation&apos;s
              critical duration.
            </p>
          </div>
        </div>

        {!criticalPath || criticalPath.executions.length === 0 ? (
          <div className="analytics-empty-state">
            <strong>No critical path available.</strong>
            <p>
              Critical-path data will appear after the investigation has
              executed.
            </p>
          </div>
        ) : (
          <div className="critical-path-card">
            <div className="critical-path-duration">
              <span>Critical Path Duration</span>
              <strong>
                {formatDuration(criticalPath.critical_path_ms)}
              </strong>
            </div>

            <div className="critical-path-executions">
              <h3>Execution Path</h3>

              <div className="critical-path-list">
                {criticalPath.executions.map((execution, index) => (
                  <div
                    className="critical-path-item"
                    key={`${execution}-${index}`}
                  >
                    <span className="critical-path-number">
                      {index + 1}
                    </span>

                    <span className="critical-path-execution">
                      {execution}
                    </span>

                    {index < criticalPath.executions.length - 1 && (
                      <span className="critical-path-arrow">
                        →
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Investigation History                                               */}
      {/* ------------------------------------------------------------------ */}

      <section className="investigation-section">
        <div className="section-header">
          <div>
            <h2>
              Investigation History
            </h2>

            <p>
              Actions recorded during this
              investigation.
            </p>
          </div>
        </div>

        {historyQuery.isLoading && (
          <p className="muted-text">
            Loading history...
          </p>
        )}

        {historyQuery.isError && (
          <p className="error-text">
            Investigation history is
            currently unavailable.
          </p>
        )}

        {historyQuery.data &&
          historyQuery.data.items.length ===
            0 && (
            <p className="muted-text">
              No history entries have been
              recorded.
            </p>
          )}

        {historyQuery.data &&
          historyQuery.data.items.length >
            0 && (
            <div className="history-list">
              {historyQuery.data.items.map(
                (item) => (
                  <div
                    className="history-item"
                    key={item.id}
                  >
                    <div>
                      <strong>
                        {item.action}
                      </strong>

                      {item.old_value !==
                        null &&
                        item.old_value !==
                          undefined && (
                          <span>
                            Previous:{" "}
                            {
                              item.old_value
                            }
                          </span>
                        )}

                      {item.new_value !==
                        null &&
                        item.new_value !==
                          undefined && (
                          <span>
                            New:{" "}
                            {
                              item.new_value
                            }
                          </span>
                        )}
                    </div>

                    <time>
                      {formatDate(
                        item.created_at,
                      )}
                    </time>
                  </div>
                ),
              )}
            </div>
          )}
      </section>
    </div>
  );
}

export default Investigation;