import {
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getConfidenceAnalytics,
  getDashboardOverview,
  getFailedComponents,
  getRecentInvestigations,
  getRootCauses,
  getSeverityDistribution,
  getDashboardTimeline,
} from "../services/dashboardApi";

function formatConfidence(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatDuration(seconds: number) {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  return `${minutes}m ${remainingSeconds}s`;
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function getStatusClass(status: string) {
  return `status-badge status-${status
    .toLowerCase()
    .replace(/\s+/g, "-")}`;
}

function getSeverityClass(severity: string | null | undefined) {
  if (!severity) {
    return "severity-badge";
  }

  return `severity-badge severity-${severity
    .toLowerCase()
    .replace(/\s+/g, "-")}`;
}
function formatTimelineDate(value: string) {
  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function Dashboard() {
  const {
    data: overview,
    isLoading: overviewLoading,
    isError: overviewError,
    error: overviewErrorDetails,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ["dashboard", "overview"],
    queryFn: getDashboardOverview,
  });

  const queryClient = useQueryClient();

  const refreshDashboard = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["dashboard"],
    });
  };

  const {
    data: recentInvestigations,
    isLoading: recentLoading,
    isError: recentError,
    refetch: refetchRecent,
  } = useQuery({
    queryKey: ["dashboard", "recent-investigations"],
    queryFn: () => getRecentInvestigations(10, 0),
  });

  const {
    data: rootCauses,
    isLoading: rootCausesLoading,
    isError: rootCausesError,
    refetch: refetchRootCauses,
  } = useQuery({
    queryKey: ["dashboard", "root-causes"],
    queryFn: getRootCauses,
  });
  const rootCauseChartData = (rootCauses ?? []).map((item) => ({
    name:
      item.root_cause.length > 45
        ? `${item.root_cause.slice(0, 45)}...`
        : item.root_cause,
    count: item.count,
  }));
  const {
    data: severityData,
    isLoading: severityLoading,
    isError: severityError,
    refetch: refetchSeverity,
  } = useQuery({
    queryKey: ["dashboard", "severity"],
    queryFn: getSeverityDistribution,
  });

  const {
    data: confidenceAnalytics,
    isLoading: confidenceLoading,
    isError: confidenceError,
    refetch: refetchConfidence,
  } = useQuery({
    queryKey: ["dashboard", "confidence"],
    queryFn: getConfidenceAnalytics,
  });

    const {
    data: failedComponents,
    isLoading: failedComponentsLoading,
    isError: failedComponentsError,
    refetch: refetchFailedComponents,
  } = useQuery({
    queryKey: ["dashboard", "failed-components"],
    queryFn: getFailedComponents,
  });

  const {
    data: timeline,
    isLoading: timelineLoading,
    isError: timelineError,
    refetch: refetchTimeline,
  } = useQuery({
    queryKey: ["dashboard", "timeline"],
    queryFn: getDashboardTimeline,
  });

  const activeInvestigations = overview
    ? Math.max(overview.pending, 0)
    : 0;

  const isLoading =
    overviewLoading || recentLoading;

  const navigate = useNavigate();

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Dashboard</h1>

          <p>
            AI-powered incident and root cause overview.
          </p>
        </div>

        <div className="dashboard-heading-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={refreshDashboard}
          >
            Refresh
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={() => navigate("/investigations/new")}
          >
            New Investigation
          </button>
        </div>
      </div>

      {overviewError && (
        <div className="dashboard-card">
          <h2>Unable to load dashboard</h2>

          <p className="muted">
            {overviewErrorDetails instanceof Error
              ? overviewErrorDetails.message
              : "An unexpected error occurred while loading dashboard data."}
          </p>

          <button
            type="button"
            className="secondary-button"
            onClick={() => refetchOverview()}
          >
            Retry
          </button>
        </div>
      )}

      <div className="metrics-grid">
        <div className="metric-card">
          <span>Total Investigations</span>

          <strong>
            {overviewLoading
              ? "..."
              : overview?.total_investigations ?? "—"}
          </strong>
        </div>

        <div className="metric-card">
          <span>Active Investigations</span>

          <strong>
            {overviewLoading
              ? "..."
              : overview
                ? activeInvestigations
                : "—"}
          </strong>
        </div>

        <div className="metric-card">
          <span>Critical Incidents</span>

          <strong>
            {overviewLoading
              ? "..."
              : overview?.critical ?? "—"}
          </strong>
        </div>

        <div className="metric-card">
          <span>Average Confidence</span>

          <strong>
            {overviewLoading
              ? "..."
              : overview
                ? formatConfidence(
                    overview.average_confidence,
                  )
                : "—"}
          </strong>
        </div>
      </div>

      {overview && !overviewLoading && (
        <div className="dashboard-grid">
          <div className="dashboard-card">
            <h2>Investigation Status</h2>

            <div className="dashboard-stat-list">
              <div>
                <span>Resolved</span>
                <strong>{overview.resolved}</strong>
              </div>

              <div>
                <span>Pending</span>
                <strong>{overview.pending}</strong>
              </div>

              <div>
                <span>High Severity</span>
                <strong>{overview.high}</strong>
              </div>

              <div>
                <span>Medium Severity</span>
                <strong>{overview.medium}</strong>
              </div>

              <div>
                <span>Low Severity</span>
                <strong>{overview.low}</strong>
              </div>
            </div>
          </div>

          <div className="dashboard-card">
            <h2>Performance</h2>

            <div className="dashboard-stat-list">
              <div>
                <span>Average Confidence</span>
                <strong>
                  {formatConfidence(
                    overview.average_confidence,
                  )}
                </strong>
              </div>

              <div>
                <span>Average Duration</span>
                <strong>
                  {formatDuration(
                    overview.average_duration_seconds,
                  )}
                </strong>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-card recent-investigations-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Recent Investigations</h2>
            <p className="muted">
              Latest investigation activity.
            </p>
          </div>

          <Link
            to="/investigations"
            className="text-link"
          >
            View all
          </Link>
        </div>

        {recentLoading && (
          <div className="dashboard-loading">
            Loading recent investigations...
          </div>
        )}

        {recentError && !recentLoading && (
          <div className="dashboard-empty">
            <p className="muted">
              Unable to load recent investigations.
            </p>

            <button
              type="button"
              className="secondary-button"
              onClick={() => refetchRecent()}
            >
              Retry
            </button>
          </div>
        )}

        {!recentLoading &&
          !recentError &&
          recentInvestigations &&
          recentInvestigations.length === 0 && (
            <div className="dashboard-empty">
              <h3>No investigations yet</h3>
              <p className="muted">
                Create an investigation to see activity here.
              </p>
            </div>
          )}

        {!recentLoading &&
          !recentError &&
          recentInvestigations &&
          recentInvestigations.length > 0 && (
            <div className="recent-investigation-list">
              {recentInvestigations.map((investigation) => (
                <Link
                  key={investigation.id}
                  to={`/investigations/${investigation.id}`}
                  className="recent-investigation-item"
                >
                  <div className="recent-investigation-main">
                    <strong>
                      {investigation.title}
                    </strong>

                    <span className="recent-investigation-meta">
                      #{investigation.id} ·{" "}
                      {formatDate(
                        investigation.created_at,
                      )}
                    </span>
                  </div>

                  <div className="recent-investigation-details">
                    <span
                      className={getStatusClass(
                        investigation.status,
                      )}
                    >
                      {investigation.status}
                    </span>

                    {investigation.severity && (
                      <span
                        className={getSeverityClass(
                          investigation.severity,
                        )}
                      >
                        {investigation.severity}
                      </span>
                    )}

                    {investigation.confidence !==
                      null &&
                      investigation.confidence !==
                        undefined && (
                        <span className="confidence-value">
                          {formatConfidence(
                            investigation.confidence,
                          )}
                        </span>
                      )}
                  </div>
                </Link>
              ))}
            </div>
          )}
      </div>


      <div className="dashboard-card root-cause-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Root Cause Distribution</h2>
            <p className="muted">
              Distribution of identified root causes.
            </p>
          </div>
        </div>

        {rootCausesLoading && (
          <div className="dashboard-loading">
            Loading root cause analytics...
          </div>
        )}

        {rootCausesError && !rootCausesLoading && (
          <div className="dashboard-empty">
            <p className="muted">
              Unable to load root cause analytics.
            </p>

            <button
              type="button"
              className="secondary-button"
              onClick={() => refetchRootCauses()}
            >
              Retry
            </button>
          </div>
        )}

        {!rootCausesLoading &&
          !rootCausesError &&
          rootCauses &&
          rootCauses.length === 0 && (
            <div className="dashboard-empty">
              <h3>No root causes yet</h3>
              <p className="muted">
                Root cause analytics will appear after
                investigations are completed.
              </p>
            </div>
          )}

        {!rootCausesLoading &&
          !rootCausesError &&
          rootCauses &&
          rootCauses.length > 0 && (
            <div
              className="dashboard-chart root-cause-chart"
              style={{
                width: "100%",
                height: "360px",
                minHeight: "360px",
              }}
            >
              <BarChart
                width={700}
                height={360}
                data={rootCauseChartData}
                layout="vertical"
                margin={{
                  top: 10,
                  right: 30,
                  left: 20,
                  bottom: 10,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis type="number" />

                <YAxis
                  type="category"
                  dataKey="name"
                  width={220}
                  tick={{
                    fontSize: 12,
                  }}
                />

                <Tooltip />

                <Bar
                  dataKey="count"
                  name="Investigations"
                />
              </BarChart>
            </div>
          )}
      </div>

      <div className="dashboard-card severity-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Severity Distribution</h2>
            <p className="muted">
              Distribution of incidents by severity.
            </p>
          </div>
        </div>

        {severityLoading && (
          <div className="dashboard-loading">
            Loading severity analytics...
          </div>
        )}

        {severityError && !severityLoading && (
          <div className="dashboard-empty">
            <p className="muted">
              Unable to load severity analytics.
            </p>

            <button
              type="button"
              className="secondary-button"
              onClick={() => refetchSeverity()}
            >
              Retry
            </button>
          </div>
        )}

        {!severityLoading &&
          !severityError &&
          severityData &&
          severityData.length === 0 && (
            <div className="dashboard-empty">
              <h3>No severity data yet</h3>
              <p className="muted">
                Severity analytics will appear when
                investigations are available.
              </p>
            </div>
          )}

        {!severityLoading &&
          !severityError &&
          severityData &&
          severityData.length > 0 && (
            <div className="dashboard-chart">
              <ResponsiveContainer
                width="100%"
                height={300}
              >
                <BarChart
                  data={severityData.map((item) => ({
                    ...item,
                    severity:
                      item.severity ?? "Unknown",
                  }))}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 10,
                    bottom: 10,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="severity"
                  />

                  <YAxis
                    allowDecimals={false}
                  />

                  <Tooltip />

                  <Bar
                    dataKey="count"
                    name="Investigations"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
      </div>

      <div className="dashboard-card confidence-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Confidence Analytics</h2>
            <p className="muted">
              AI confidence statistics across investigations.
            </p>
          </div>
        </div>

        {confidenceLoading && (
          <div className="dashboard-loading">
            Loading confidence analytics...
          </div>
        )}

        {confidenceError && !confidenceLoading && (
          <div className="dashboard-empty">
            <p className="muted">
              Unable to load confidence analytics.
            </p>

            <button
              type="button"
              className="secondary-button"
              onClick={() => refetchConfidence()}
            >
              Retry
            </button>
          </div>
        )}

        {!confidenceLoading &&
          !confidenceError &&
          confidenceAnalytics && (
            <>
              <div className="confidence-summary">
                <div className="confidence-summary-item">
                  <span>Average Confidence</span>
                  <strong>
                    {formatConfidence(
                      confidenceAnalytics.average_confidence,
                    )}
                  </strong>
                </div>

                <div className="confidence-summary-item">
                  <span>Minimum Confidence</span>
                  <strong>
                    {formatConfidence(
                      confidenceAnalytics.minimum_confidence,
                    )}
                  </strong>
                </div>

                <div className="confidence-summary-item">
                  <span>Maximum Confidence</span>
                  <strong>
                    {formatConfidence(
                      confidenceAnalytics.maximum_confidence,
                    )}
                  </strong>
                </div>
              </div>

              <div className="confidence-breakdown">
                <div>
                  <span>High Confidence</span>
                  <strong>
                    {confidenceAnalytics.high_confidence}
                  </strong>
                </div>

                <div>
                  <span>Medium Confidence</span>
                  <strong>
                    {confidenceAnalytics.medium_confidence}
                  </strong>
                </div>

                <div>
                  <span>Low Confidence</span>
                  <strong>
                    {confidenceAnalytics.low_confidence}
                  </strong>
                </div>
              </div>
            </>
          )}
      </div>

      <div className="dashboard-card failed-components-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Failed Components</h2>
            <p className="muted">
              Components associated with investigation failures.
            </p>
          </div>
        </div>

        {failedComponentsLoading && (
          <div className="dashboard-loading">
            Loading failed component analytics...
          </div>
        )}

        {failedComponentsError &&
          !failedComponentsLoading && (
            <div className="dashboard-empty">
              <p className="muted">
                Unable to load failed component analytics.
              </p>

              <button
                type="button"
                className="secondary-button"
                onClick={() => refetchFailedComponents()}
              >
                Retry
              </button>
            </div>
          )}

        {!failedComponentsLoading &&
          !failedComponentsError &&
          failedComponents &&
          failedComponents.length === 0 && (
            <div className="dashboard-empty">
              <h3>No failed components</h3>

              <p className="muted">
                Failed component analytics will appear
                when investigation failures are recorded.
              </p>
            </div>
          )}

        {!failedComponentsLoading &&
          !failedComponentsError &&
          failedComponents &&
          failedComponents.length > 0 && (
            <div className="failed-components-list">
              {failedComponents.map((item) => (
                <div
                  key={item.component}
                  className="failed-component-row"
                >
                  <div className="failed-component-info">
                    <span className="failed-component-name">
                      {item.component}
                    </span>

                    <span className="failed-component-count">
                      {item.count}{" "}
                      {item.count === 1
                        ? "failure"
                        : "failures"}
                    </span>
                  </div>

                  <div className="failed-component-bar">
                    <div
                      className="failed-component-bar-fill"
                      style={{
                        width: `${
                          Math.max(
                            ...failedComponents.map(
                              (component) =>
                                component.count,
                            ),
                          ) > 0
                            ? (item.count /
                                Math.max(
                                  ...failedComponents.map(
                                    (component) =>
                                      component.count,
                                  ),
                                )) *
                              100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
      </div>

      <div className="dashboard-card timeline-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Investigation Timeline</h2>

            <p className="muted">
              Investigation activity over time.
            </p>
          </div>
        </div>

        {timelineLoading && (
          <div className="dashboard-loading">
            Loading investigation timeline...
          </div>
        )}

        {timelineError && !timelineLoading && (
          <div className="dashboard-empty">
            <p className="muted">
              Unable to load investigation timeline.
            </p>

            <button
              type="button"
              className="secondary-button"
              onClick={() => refetchTimeline()}
            >
              Retry
            </button>
          </div>
        )}

        {!timelineLoading &&
          !timelineError &&
          timeline &&
          timeline.length === 0 && (
            <div className="dashboard-empty">
              <h3>No timeline data yet</h3>

              <p className="muted">
                Investigation activity will appear here
                when investigations are recorded.
              </p>
            </div>
          )}

        {!timelineLoading &&
          !timelineError &&
          timeline &&
          timeline.length > 0 && (
            <div className="dashboard-chart timeline-chart">
              <ResponsiveContainer
                width="100%"
                height={320}
              >
                <LineChart
                  data={timeline}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 10,
                    bottom: 10,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="date"
                    tickFormatter={formatTimelineDate}
                  />

                  <YAxis
                    allowDecimals={false}
                  />

                  <Tooltip
                    labelFormatter={(label) =>
                      formatTimelineDate(String(label))
                    }
                  />

                  <Line
                    type="monotone"
                    dataKey="count"
                    name="Investigations"
                    strokeWidth={3}
                    dot
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
      </div>

      {!isLoading &&
        !overviewError &&
        !overview && (
          <div className="empty-state">
            <h2>No dashboard data</h2>
            <p>
              Dashboard statistics are not available yet.
            </p>
          </div>
        )}
    </section>
  );
}

export default Dashboard;