import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { getApiErrorMessage } from "../services/api";
import { getInvestigations } from "../services/investigationApi";
import type { InvestigationStatus } from "../types/investigation";

const PAGE_SIZE = 10;

const STATUS_OPTIONS: Array<{
  value: "" | InvestigationStatus;
  label: string;
}> = [
  { value: "", label: "All statuses" },
  { value: "OPEN", label: "Open" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "COMPLETED", label: "Completed" },
  { value: "FAILED", label: "Failed" },
];

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function getStatusClass(status: InvestigationStatus) {
  return `status-badge status-${status
    .toLowerCase()
    .replace(/_/g, "-")}`;
}

function getStatusLabel(status: InvestigationStatus) {
  return status
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function Investigations() {
  const navigate = useNavigate();

  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<"" | InvestigationStatus>("");

  const skip = page * PAGE_SIZE;

  const {
    data,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: [
      "investigations",
      { page, search, statusFilter },
    ],
    queryFn: ({ signal }) =>
      getInvestigations(
        {
          skip,
          limit: PAGE_SIZE,
          search: search.trim() || undefined,
          status_filter: statusFilter || undefined,
        },
        { signal },
      ),
    retry: 1,
  });

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(0);
  };

  const handleStatusChange = (
    value: "" | InvestigationStatus,
  ) => {
    setStatusFilter(value);
    setPage(0);
  };

  const totalPages = data
    ? Math.max(1, Math.ceil(data.total / PAGE_SIZE))
    : 1;

  const canGoPrevious = page > 0;
  const canGoNext = data?.has_next ?? false;

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Investigations</h1>
          <p>
            Review incidents, investigate failures, and
            inspect AI root cause results.
          </p>
        </div>

        <div className="dashboard-heading-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            {isFetching ? "Refreshing..." : "Refresh"}
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={() =>
              navigate("/investigations/new")
            }
          >
            New Investigation
          </button>
        </div>
      </div>

      <div className="dashboard-card">
        <div className="investigation-form">
          <div className="form-field">
            <label htmlFor="investigation-search">
              Search investigations
            </label>

            <input
              id="investigation-search"
              type="search"
              value={search}
              onChange={(event) =>
                handleSearchChange(event.target.value)
              }
              placeholder="Search by title or description"
            />
          </div>

          <div className="form-field">
            <label htmlFor="investigation-status">
              Status
            </label>

            <select
              id="investigation-status"
              value={statusFilter}
              onChange={(event) =>
                handleStatusChange(
                  event.target.value as
                    | ""
                    | InvestigationStatus,
                )
              }
            >
              {STATUS_OPTIONS.map((option) => (
                <option
                  key={option.value || "all"}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {isError && (
        <div className="dashboard-card" role="alert">
          <h2>Unable to load investigations</h2>

          <p className="muted">
            {getApiErrorMessage(
              error,
              "Unable to load investigations. Please try again.",
            )}
          </p>

          <button
            type="button"
            className="secondary-button"
            onClick={() => refetch()}
          >
            Try Again
          </button>
        </div>
      )}

      {isLoading && (
        <div className="dashboard-card">
          <p>Loading investigations...</p>
        </div>
      )}

      {!isLoading &&
        !isError &&
        data?.items.length === 0 && (
          <div className="empty-state">
            <h2>No investigations found</h2>

            <p>
              {search.trim() || statusFilter
                ? "Try changing your search or status filter."
                : "Create your first investigation to begin analyzing an incident."}
            </p>

            {!search.trim() && !statusFilter && (
              <button
                type="button"
                className="primary-button"
                onClick={() =>
                  navigate("/investigations/new")
                }
              >
                Create Investigation
              </button>
            )}
          </div>
        )}

      {!isLoading &&
        !isError &&
        data &&
        data.items.length > 0 && (
          <>
            <div className="dashboard-card">
              <div className="page-heading">
                <div>
                  <h2>Investigation List</h2>

                  <p className="muted">
                    Showing {data.items.length} of{" "}
                    {data.total} investigation
                    {data.total === 1 ? "" : "s"}.
                  </p>
                </div>
              </div>

              <div>
                {data.items.map((investigation) => (
                  <article
                    key={investigation.id}
                    className="dashboard-card"
                  >
                    <div className="page-heading">
                      <div>
                        <h2>
                          <Link
                            to={`/investigations/${investigation.id}`}
                          >
                            {investigation.title}
                          </Link>
                        </h2>

                        <p className="muted">
                          Investigation #
                          {investigation.id} · Created{" "}
                          {formatDate(
                            investigation.created_at,
                          )}
                        </p>
                      </div>

                      <span
                        className={getStatusClass(
                          investigation.status,
                        )}
                      >
                        {getStatusLabel(
                          investigation.status,
                        )}
                      </span>
                    </div>

                    {investigation.description && (
                      <p>
                        {investigation.description}
                      </p>
                    )}

                    <div className="result-row">
                      <span>Root Cause</span>

                      <strong>
                        {investigation.root_cause ||
                          "Not identified"}
                      </strong>
                    </div>

                    <div className="result-row">
                      <span>Failed Component</span>

                      <strong>
                        {investigation.failed_component ||
                          "Not identified"}
                      </strong>
                    </div>

                    <div className="form-actions">
                      <Link
                        className="secondary-button"
                        to={`/investigations/${investigation.id}`}
                      >
                        View Investigation
                      </Link>
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <div className="dashboard-card">
              <div className="form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    setPage((current) => current - 1)
                  }
                  disabled={
                    !canGoPrevious || isFetching
                  }
                >
                  Previous
                </button>

                <span className="muted">
                  Page {page + 1} of {totalPages}
                </span>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    setPage((current) => current + 1)
                  }
                  disabled={!canGoNext || isFetching}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
    </section>
  );
}

export default Investigations;
