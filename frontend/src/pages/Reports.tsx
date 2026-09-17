import { useEffect, useState } from "react";
import {
  Activity,
  Download,
  FileSpreadsheet,
  FileText,
  History,
  RefreshCw,
} from "lucide-react";

import {
  getRecentInvestigations,
} from "../services/dashboardApi";

import {
  getInvestigationAnalyticsDashboard,
} from "../services/investigationApi";

import type {
  RecentInvestigation,
} from "../types/dashboard";

import type {
  InvestigationAnalyticsDashboard,
} from "../services/investigationApi";

import {
  getReportHistory,
  downloadAllInvestigationsCsv,
  downloadAllInvestigationsExcel,
  downloadAllInvestigationsPdf,
  downloadInvestigationAnalyticsCsv,
  downloadInvestigationAnalyticsExcel,
  downloadInvestigationAnalyticsPdf,
} from "../services/reportApi";

import type {
  ReportHistoryItem,
} from "../services/reportApi";

function Reports() {
  const [investigations, setInvestigations] = useState<
    RecentInvestigation[]
  >([]);

  const [selectedInvestigationId, setSelectedInvestigationId] =
    useState<number | null>(null);

  const [analytics, setAnalytics] =
    useState<InvestigationAnalyticsDashboard | null>(null);

  const [loadingInvestigations, setLoadingInvestigations] =
    useState(true);

  const [loadingAnalytics, setLoadingAnalytics] =
    useState(false);

  const [loadingReport, setLoadingReport] =
    useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);

  const [reportHistory, setReportHistory] =
    useState<ReportHistoryItem[]>([]);

  const [loadingHistory, setLoadingHistory] =
    useState(true);

  /*
   * ============================================================
   * Load investigations
   * ============================================================
   */

  async function loadReportHistory() {
    try {
      setLoadingHistory(true);

      const data = await getReportHistory(50, 0);

      setReportHistory(data.items);
    } catch (err) {
      console.error(
        "Failed to load report history:",
        err,
      );

      setError(
        "Unable to load report history. Please try again.",
      );
    } finally {
      setLoadingHistory(false);
    }
  }

  useEffect(() => {
    loadReportHistory();
  }, []);

  useEffect(() => {
    async function loadInvestigations() {
      try {
        setLoadingInvestigations(true);
        setError(null);

        const data = await getRecentInvestigations(50, 0);

        setInvestigations(data);

        if (data.length > 0) {
          setSelectedInvestigationId(data[0].id);
        }
      } catch (err) {
        console.error(
          "Failed to load investigations:",
          err,
        );

        setError(
          "Unable to load investigations. Please try again.",
        );
      } finally {
        setLoadingInvestigations(false);
      }
    }

    loadInvestigations();
  }, []);

  /*
   * ============================================================
   * Load selected investigation analytics
   * ============================================================
   */

  useEffect(() => {
  if (selectedInvestigationId === null) {
    setAnalytics(null);
    return;
  }

  async function loadAnalytics() {
    const investigationId = selectedInvestigationId;

    if (investigationId === null) {
      return;
    }

    try {
      setLoadingAnalytics(true);
      setError(null);

      const data =
        await getInvestigationAnalyticsDashboard(
          investigationId,
        );

      setAnalytics(data);
    } catch (err) {
      console.error(
        "Failed to load investigation analytics:",
        err,
      );

      setAnalytics(null);

      setError(
        "Unable to load analytics for this investigation.",
      );
    } finally {
      setLoadingAnalytics(false);
    }
  }

  loadAnalytics();
}, [selectedInvestigationId]);

  /*
   * ============================================================
   * Download helper
   * ============================================================
   */

  async function saveBlob(
    blob: Blob,
    filename: string,
  ) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();

    link.remove();
    window.URL.revokeObjectURL(url);
  }

  /*
   * ============================================================
   * General report download
   * ============================================================
   */

  async function handleGeneralDownload(
    type: "csv" | "excel" | "pdf",
  ) {
    try {
      setLoadingReport(`general-${type}`);
      setError(null);

      let blob: Blob;
      let filename: string;

      if (type === "csv") {
        blob = await downloadAllInvestigationsCsv();
        filename = "investigations.csv";
      } else if (type === "excel") {
        blob = await downloadAllInvestigationsExcel();
        filename = "investigations.xlsx";
      } else {
        blob = await downloadAllInvestigationsPdf();
        filename = "investigations.pdf";
      }

      await saveBlob(blob, filename);
      await loadReportHistory();
    } catch (err) {
      console.error(
        "General report download failed:",
        err,
      );

      setError(
        "Unable to download the report. Please try again.",
      );
    } finally {
      setLoadingReport(null);
    }
  }

  /*
   * ============================================================
   * Investigation analytics report download
   * ============================================================
   */

  async function handleAnalyticsDownload(
    type: "csv" | "excel" | "pdf",
  ) {
    if (selectedInvestigationId === null) {
      return;
    }

    try {
      setLoadingReport(`analytics-${type}`);
      setError(null);

      let blob: Blob;
      let filename: string;

      if (type === "csv") {
        blob =
          await downloadInvestigationAnalyticsCsv(
            selectedInvestigationId,
          );

        filename =
          `investigation_${selectedInvestigationId}_analytics.csv`;
      } else if (type === "excel") {
        blob =
          await downloadInvestigationAnalyticsExcel(
            selectedInvestigationId,
          );

        filename =
          `investigation_${selectedInvestigationId}_analytics.xlsx`;
      } else {
        blob =
          await downloadInvestigationAnalyticsPdf(
            selectedInvestigationId,
          );

        filename =
          `investigation_${selectedInvestigationId}_analytics.pdf`;
      }

      await saveBlob(blob, filename);
      await loadReportHistory();
    } catch (err) {
      console.error(
        "Analytics report download failed:",
        err,
      );

      setError(
        "Unable to download the investigation report. Please try again.",
      );
    } finally {
      setLoadingReport(null);
    }
  }

  const selectedInvestigation =
    investigations.find(
      (investigation) =>
        investigation.id === selectedInvestigationId,
    );

  const overview = analytics?.overview;

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Reports</h1>
          <p>
            Generate and download investigation reports in
            multiple formats.
          </p>
        </div>
      </div>

      {error && (
        <div className="error-state">
          <strong>Report error</strong>
          <p>{error}</p>
        </div>
      )}

      {/* ======================================================
          All investigations
          ====================================================== */}

      <div className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>All Investigations</h2>
            <p>
              Export your investigation records for analysis,
              sharing, or archival.
            </p>
          </div>

          <FileText size={24} />
        </div>

        <div className="report-actions">
          <button
            type="button"
            className="button-secondary"
            onClick={() =>
              handleGeneralDownload("csv")
            }
            disabled={loadingReport !== null}
          >
            {loadingReport === "general-csv" ? (
              <RefreshCw size={17} className="spin" />
            ) : (
              <Download size={17} />
            )}
            CSV
          </button>

          <button
            type="button"
            className="button-secondary"
            onClick={() =>
              handleGeneralDownload("excel")
            }
            disabled={loadingReport !== null}
          >
            {loadingReport === "general-excel" ? (
              <RefreshCw size={17} className="spin" />
            ) : (
              <FileSpreadsheet size={17} />
            )}
            Excel
          </button>

          <button
            type="button"
            className="button-primary"
            onClick={() =>
              handleGeneralDownload("pdf")
            }
            disabled={loadingReport !== null}
          >
            {loadingReport === "general-pdf" ? (
              <RefreshCw size={17} className="spin" />
            ) : (
              <FileText size={17} />
            )}
            PDF
          </button>
        </div>
      </div>

      {/* ======================================================
          Investigation analytics
          ====================================================== */}

      <div className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Investigation Analytics</h2>
            <p>
              Select an investigation to preview its execution
              analytics and export the report.
            </p>
          </div>

          <Activity size={24} />
        </div>

        <div className="report-selector">
          <label htmlFor="investigation-select">
            Investigation
          </label>

          <select
            id="investigation-select"
            value={
              selectedInvestigationId ?? ""
            }
            onChange={(event) =>
              setSelectedInvestigationId(
                event.target.value
                  ? Number(event.target.value)
                  : null,
              )
            }
            disabled={
              loadingInvestigations ||
              investigations.length === 0
            }
          >
            {loadingInvestigations && (
              <option value="">
                Loading investigations...
              </option>
            )}

            {!loadingInvestigations &&
              investigations.length === 0 && (
                <option value="">
                  No investigations available
                </option>
              )}

            {investigations.map(
              (investigation) => (
                <option
                  key={investigation.id}
                  value={investigation.id}
                >
                  #{investigation.id} —{" "}
                  {investigation.title}
                </option>
              ),
            )}
          </select>
        </div>

        {loadingAnalytics && (
          <div className="loading-state">
            <RefreshCw
              size={20}
              className="spin"
            />
            <span>
              Loading investigation analytics...
            </span>
          </div>
        )}

        {!loadingAnalytics &&
          selectedInvestigation &&
          analytics && (
            <>
              <div className="report-investigation-header">
                <div>
                  <span className="report-label">
                    Investigation
                  </span>

                  <h3>
                    {selectedInvestigation.title}
                  </h3>

                  <span>
                    ID #{selectedInvestigation.id}
                  </span>
                </div>

                <span
                  className={`status-badge status-${selectedInvestigation.status.toLowerCase()}`}
                >
                  {selectedInvestigation.status}
                </span>
              </div>

              <div className="report-metrics">
                <div className="report-metric">
                  <span>Executions</span>
                  <strong>
                    {overview?.total_executions ?? 0}
                  </strong>
                </div>

                <div className="report-metric">
                  <span>Success Rate</span>
                  <strong>
                    {overview
                      ? `${(overview.success_rate * 100).toFixed(2)}%`
                      : "0.00%"}
                  </strong>
                </div>

                <div className="report-metric">
                  <span>Failures</span>
                  <strong>
                    {overview?.failed_executions ?? 0}
                  </strong>
                </div>

                <div className="report-metric">
                  <span>Retries</span>
                  <strong>
                    {overview?.retry_count ?? 0}
                  </strong>
                </div>

                <div className="report-metric">
                  <span>Avg Duration</span>
                  <strong>
                    {overview
                      ? `${overview.average_duration_ms.toFixed(2)} ms`
                      : "0.00 ms"}
                  </strong>
                </div>

                <div className="report-metric">
                  <span>Bottlenecks</span>
                  <strong>
                    {overview?.bottleneck_count ?? 0}
                  </strong>
                </div>
              </div>

              <div className="report-actions">
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() =>
                    handleAnalyticsDownload("csv")
                  }
                  disabled={
                    loadingReport !== null
                  }
                >
                  {loadingReport ===
                  "analytics-csv" ? (
                    <RefreshCw
                      size={17}
                      className="spin"
                    />
                  ) : (
                    <Download size={17} />
                  )}
                  CSV
                </button>

                <button
                  type="button"
                  className="button-secondary"
                  onClick={() =>
                    handleAnalyticsDownload(
                      "excel",
                    )
                  }
                  disabled={
                    loadingReport !== null
                  }
                >
                  {loadingReport ===
                  "analytics-excel" ? (
                    <RefreshCw
                      size={17}
                      className="spin"
                    />
                  ) : (
                    <FileSpreadsheet size={17} />
                  )}
                  Excel
                </button>

                <button
                  type="button"
                  className="button-primary"
                  onClick={() =>
                    handleAnalyticsDownload("pdf")
                  }
                  disabled={
                    loadingReport !== null
                  }
                >
                  {loadingReport ===
                  "analytics-pdf" ? (
                    <RefreshCw
                      size={17}
                      className="spin"
                    />
                  ) : (
                    <FileText size={17} />
                  )}
                  PDF
                </button>
              </div>
            </>
          )}
      </div>

            {/* ======================================================
          Report history
          ====================================================== */}

      <div className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Report History</h2>
            <p>
              View your recently generated investigation
              reports.
            </p>
          </div>

            <button
              type="button"
              className="report-history-refresh"
              onClick={loadReportHistory}
              disabled={loadingHistory}
              title="Refresh report history"
              aria-label="Refresh report history"
            >
              <RefreshCw
                size={20}
                className={
                  loadingHistory ? "spin" : ""
                }
              />
            </button>
          </div>

        {loadingHistory && (
          <div className="loading-state">
            <RefreshCw
              size={20}
              className="spin"
            />
            <span>
              Loading report history...
            </span>
          </div>
        )}

        {!loadingHistory &&
          reportHistory.length === 0 && (
            <div className="empty-state">
              <History size={22} />
              <p>
                No reports have been generated yet.
              </p>
            </div>
          )}

        {!loadingHistory &&
          reportHistory.length > 0 && (
            <div className="report-history-wrapper">
              <div className="report-history-table-container">
                <table className="report-history-table">
                  <thead>
                    <tr>
                      <th>Report</th>
                      <th>Investigation</th>
                      <th>Format</th>
                      <th>Status</th>
                      <th>Generated</th>
                    </tr>
                  </thead>

                  <tbody>
                    {reportHistory.map((item) => (
                      <tr key={item.id}>
                        <td>
                          <div className="report-history-name">
                            <FileText size={17} />
                            <span>
                              {item.filename}
                            </span>
                          </div>
                        </td>

                        <td>
                          {item.investigation_id !==
                          null
                            ? `#${item.investigation_id}`
                            : "All Investigations"}
                        </td>

                        <td>
                          <span className="report-format">
                            {item.format}
                          </span>
                        </td>

                        <td>
                          <span className="report-history-status">
                            {item.status}
                          </span>
                        </td>

                        <td>
                          {new Date(
                            item.created_at,
                          ).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="report-history-footer">
                Showing {reportHistory.length} report
                {reportHistory.length === 1
                  ? ""
                  : "s"}
              </div>
            </div>
          )}
      </div>

    </section>
  );
}

export default Reports;
