import { useEffect, useState } from "react";
import {
  Archive,
  Bell,
  Check,
  CheckCheck,
  Trash2,
  Inbox,
  RefreshCw,
} from "lucide-react";

import notificationApi from "../services/notificationApi";
import type {
  Notification,
} from "../services/notificationApi";

function Notifications() {
  const [notifications, setNotifications] = useState<
    Notification[]
  >([]);

  const [showArchived, setShowArchived] =
    useState(false);

  const [loading, setLoading] = useState(true);

  const [actionLoading, setActionLoading] =
    useState<number | null>(null);

  const [markingAllRead, setMarkingAllRead] =
    useState(false);

  const [error, setError] = useState<string | null>(
    null,
  );

  async function loadNotifications() {
    try {
      setLoading(true);
      setError(null);

      const data = await notificationApi.list({
        limit: 50,
        skip: 0,
        is_archived: showArchived,
      });

      setNotifications(data);
    } catch (err) {
      console.error(
        "Failed to load notifications:",
        err,
      );

      setError(
        "Unable to load notifications. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNotifications();
  }, [showArchived]);

  async function handleMarkRead(
    notificationId: number,
  ) {
    try {
      setActionLoading(notificationId);
      setError(null);

      const updated =
        await notificationApi.markRead(
          notificationId,
        );

      setNotifications((current) =>
        current.map((notification) =>
          notification.id === notificationId
            ? updated
            : notification,
        ),
      );
    } catch (err) {
      console.error(
        "Failed to mark notification as read:",
        err,
      );

      setError(
        "Unable to mark the notification as read.",
      );
    } finally {
      setActionLoading(null);
    }
  }

  async function handleMarkAllRead() {
    try {
      setMarkingAllRead(true);
      setError(null);

      await notificationApi.markAllRead();

      setNotifications((current) =>
        current.map((notification) => ({
          ...notification,
          is_read: true,
          read_at:
            notification.read_at ??
            new Date().toISOString(),
        })),
      );
    } catch (err) {
      console.error(
        "Failed to mark all notifications as read:",
        err,
      );

      setError(
        "Unable to mark all notifications as read.",
      );
    } finally {
      setMarkingAllRead(false);
    }
  }

  async function handleArchive(
    notificationId: number,
  ) {
    try {
      setActionLoading(notificationId);
      setError(null);

      await notificationApi.archive(
        notificationId,
      );

      setNotifications((current) =>
        current.filter(
          (notification) =>
            notification.id !== notificationId,
        ),
      );
    } catch (err) {
      console.error(
        "Failed to archive notification:",
        err,
      );

      setError(
        "Unable to archive the notification.",
      );
    } finally {
      setActionLoading(null);
    }
  }

  async function handleUnarchive(
    notificationId: number,
  ) {
    try {
      setActionLoading(notificationId);
      setError(null);

      await notificationApi.unarchive(
        notificationId,
      );

      setNotifications((current) =>
        current.filter(
          (notification) =>
            notification.id !== notificationId,
        ),
      );
    } catch (err) {
      console.error(
        "Failed to unarchive notification:",
        err,
      );

      setError(
        "Unable to unarchive the notification.",
      );
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(
    notificationId: number,
  ) {
    const confirmed = window.confirm(
      "Delete this notification permanently?",
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionLoading(notificationId);
      setError(null);

      await notificationApi.delete(
        notificationId,
      );

      setNotifications((current) =>
        current.filter(
          (notification) =>
            notification.id !== notificationId,
        ),
      );
    } catch (err) {
      console.error(
        "Failed to delete notification:",
        err,
      );

      setError(
        "Unable to delete the notification.",
      );
    } finally {
      setActionLoading(null);
    }
  }

  const unreadCount = notifications.filter(
    (notification) => !notification.is_read,
  ).length;

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Notifications</h1>
          <p>
            Manage investigation and system notifications.
          </p>
        </div>

        <div className="notifications-page-actions">
          {!showArchived &&
            unreadCount > 0 && (
              <button
                type="button"
                className="button-secondary"
                onClick={handleMarkAllRead}
                disabled={
                  markingAllRead ||
                  actionLoading !== null
                }
              >
                {markingAllRead ? (
                  <RefreshCw
                    size={17}
                    className="spin"
                  />
                ) : (
                  <CheckCheck size={17} />
                )}
                Mark all read
              </button>
            )}

          <button
            type="button"
            className="button-secondary"
            onClick={loadNotifications}
            disabled={
              loading ||
              markingAllRead ||
              actionLoading !== null
            }
            title="Refresh notifications"
          >
            <RefreshCw
              size={17}
              className={loading ? "spin" : ""}
            />
            Refresh
          </button>
        </div>
      </div>

      <div className="notifications-toolbar">
        <button
          type="button"
          className={`notification-view-button ${
            !showArchived
              ? "active"
              : ""
          }`}
          onClick={() =>
            setShowArchived(false)
          }
          disabled={
            loading ||
            actionLoading !== null
          }
        >
          <Inbox size={16} />
          Active
        </button>

        <button
          type="button"
          className={`notification-view-button ${
            showArchived
              ? "active"
              : ""
          }`}
          onClick={() =>
            setShowArchived(true)
          }
          disabled={
            loading ||
            actionLoading !== null
          }
        >
          <Archive size={16} />
          Archived
        </button>
      </div>

      {error && (
        <div className="error-state">
          <strong>Notification error</strong>
          <p>{error}</p>
        </div>
      )}

      {loading && (
        <div className="loading-state">
          <RefreshCw
            size={20}
            className="spin"
          />
          <span>
            Loading notifications...
          </span>
        </div>
      )}

      {!loading &&
        !error &&
        notifications.length === 0 && (
          <div className="empty-state">
            {showArchived ? (
              <Archive size={24} />
            ) : (
              <Bell size={24} />
            )}

            <div>
              <h2>
                {showArchived
                  ? "No archived notifications"
                  : "No notifications"}
              </h2>

              <p>
                {showArchived
                  ? "Archived notifications will appear here."
                  : "You do not have any active notifications."}
              </p>
            </div>
          </div>
        )}

      {!loading &&
        notifications.length > 0 && (
          <div className="notifications-section">
            <div className="notifications-section-header">
              <div>
                <h2>
                  {showArchived
                    ? "Archived Notifications"
                    : "Recent Notifications"}
                </h2>

                <p>
                  {showArchived
                    ? `${notifications.length} archived notification${
                        notifications.length === 1
                          ? ""
                          : "s"
                      }`
                    : unreadCount > 0
                      ? `${unreadCount} unread notification${
                          unreadCount === 1
                            ? ""
                            : "s"
                        }`
                      : "All notifications have been read."}
                </p>
              </div>

              <span className="notifications-count">
                {notifications.length}
              </span>
            </div>

            <div className="notifications-list">
              {notifications.map(
                (notification) => (
                  <article
                    key={notification.id}
                    className={`notification-item ${
                      notification.is_read
                        ? "notification-read"
                        : "notification-unread"
                    }`}
                  >
                    <div className="notification-icon">
                      {showArchived ? (
                        <Archive size={18} />
                      ) : (
                        <Bell size={18} />
                      )}
                    </div>

                    <div className="notification-content">
                      <div className="notification-top">
                        <div>
                          <h3>
                            {notification.subject}
                          </h3>

                          <div className="notification-meta">
                            <span>
                              {notification.provider}
                            </span>

                            <span>
                              {notification.severity}
                            </span>

                            <span>
                              {notification.status}
                            </span>
                          </div>
                        </div>

                        <div className="notification-actions">
                          {!notification.is_read &&
                            !showArchived && (
                              <button
                                type="button"
                                className="notification-action-button"
                                onClick={() =>
                                  handleMarkRead(
                                    notification.id,
                                  )
                                }
                                disabled={
                                  actionLoading ===
                                    notification.id ||
                                  markingAllRead
                                }
                                title="Mark as read"
                              >
                                {actionLoading ===
                                notification.id ? (
                                  <RefreshCw
                                    size={15}
                                    className="spin"
                                  />
                                ) : (
                                  <Check size={15} />
                                )}
                                <span>
                                  Mark read
                                </span>
                              </button>
                            )}

                          <button
                            type="button"
                            className="notification-action-button"
                            onClick={() =>
                              showArchived
                                ? handleUnarchive(
                                    notification.id,
                                  )
                                : handleArchive(
                                    notification.id,
                                  )
                            }
                            disabled={
                              actionLoading ===
                              notification.id
                            }
                            title={
                              showArchived
                                ? "Unarchive"
                                : "Archive"
                            }
                          >
                            {actionLoading ===
                            notification.id ? (
                              <RefreshCw
                                size={15}
                                className="spin"
                              />
                            ) : showArchived ? (
                              <Inbox size={15} />
                            ) : (
                              <Archive size={15} />
                            )}

                            <span>
                              {showArchived
                                ? "Unarchive"
                                : "Archive"}
                            </span>
                          </button>

                          <button
                            type="button"
                            className="notification-action-button notification-delete-button"
                            onClick={() =>
                              handleDelete(
                                notification.id,
                              )
                            }
                            disabled={
                              actionLoading ===
                              notification.id
                            }
                            title="Delete notification"
                          >
                            {actionLoading ===
                            notification.id ? (
                              <RefreshCw
                                size={15}
                                className="spin"
                              />
                            ) : (
                              <Trash2 size={15} />
                            )}
                            <span>Delete</span>
                          </button>

                          {!notification.is_read &&
                            !showArchived && (
                              <span className="notification-unread-badge">
                                Unread
                              </span>
                            )}
                        </div>
                      </div>

                      <p>
                        {notification.message}
                      </p>

                      <time
                        dateTime={
                          notification.created_at
                        }
                      >
                        {new Date(
                          notification.created_at,
                        ).toLocaleString()}
                      </time>

                      {notification.archived_at && (
                        <span className="notification-archived-time">
                          Archived{" "}
                          {new Date(
                            notification.archived_at,
                          ).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </article>
                ),
              )}
            </div>
          </div>
        )}
    </section>
  );
}

export default Notifications;
