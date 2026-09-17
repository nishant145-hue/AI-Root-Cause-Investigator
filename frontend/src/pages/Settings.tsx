import { useEffect, useState } from "react";
import { Bell, CheckCircle2, RefreshCw, Save, UserCircle } from "lucide-react";

import notificationApi from "../services/notificationApi";
import { getCurrentUser } from "../services/authApi";
import type {
  NotificationPreferences,
  NotificationPreferencesUpdate,
} from "../services/notificationApi";

function Settings() {
  const [preferences, setPreferences] =
    useState<NotificationPreferences | null>(null);

  const [user, setUser] =
    useState<import("../services/authApi").User | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function loadPreferences() {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const [userData, preferencesData] = await Promise.all([
        getCurrentUser(),
        notificationApi.getPreferences(),
      ]);

      setUser(userData);
      setPreferences(preferencesData);
    } catch (err) {
      console.error(
        "Failed to load notification preferences:",
        err,
      );

      setError(
        "Unable to load notification preferences. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPreferences();
  }, []);

  function updatePreference(
    field: keyof NotificationPreferencesUpdate,
    value: boolean,
  ) {
    setPreferences((current) =>
      current
        ? {
            ...current,
            [field]: value,
          }
        : current,
    );

    setSuccess(null);
    setError(null);
  }

  async function handleSave() {
    if (!preferences) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const update: NotificationPreferencesUpdate = {
        email_enabled:
          preferences.email_enabled,
        slack_enabled:
          preferences.slack_enabled,
        teams_enabled:
          preferences.teams_enabled,
        critical_only:
          preferences.critical_only,
        daily_digest:
          preferences.daily_digest,
        weekly_digest:
          preferences.weekly_digest,
      };

      const updated =
        await notificationApi.updatePreferences(
          update,
        );

      setPreferences(updated);
      setSuccess(
        "Notification preferences saved successfully.",
      );
    } catch (err) {
      console.error(
        "Failed to save notification preferences:",
        err,
      );

      setError(
        "Unable to save notification preferences. Please try again.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Settings</h1>
          <p>
            Manage your account and platform integrations.
          </p>
        </div>
      </div>

      {loading && (
        <div className="loading-state">
          <RefreshCw
            size={20}
            className="spin"
          />
          <span>
            Loading notification preferences...
          </span>
        </div>
      )}

      {error && (
        <div className="error-state">
          <strong>Settings error</strong>
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="success-state">
          <strong>Saved</strong>
          <p>{success}</p>
        </div>
      )}

      {!loading && user && (
        <div className="settings-section">
          <div className="settings-section-header">
            <div>
              <h2>
                <UserCircle size={19} />
                Account Information
              </h2>

              <p>
                View your authenticated account details.
              </p>
            </div>
          </div>

          <div className="account-details">
            <div className="account-detail">
              <span>Full name</span>
              <strong>{user.full_name || "Not provided"}</strong>
            </div>

            <div className="account-detail">
              <span>Username</span>
              <strong>{user.username}</strong>
            </div>

            <div className="account-detail">
              <span>Email</span>
              <strong>{user.email}</strong>
            </div>

            <div className="account-detail">
              <span>Role</span>
              <strong>{user.role}</strong>
            </div>

            <div className="account-detail">
              <span>Account status</span>
              <strong>
                {user.is_active ? "Active" : "Inactive"}
              </strong>
            </div>

            <div className="account-detail">
              <span>Verification</span>
              <strong>
                {user.is_verified ? "Verified" : "Not verified"}
              </strong>
            </div>

            <div className="account-detail">
              <span>Member since</span>
              <strong>
                {new Date(user.created_at).toLocaleDateString()}
              </strong>
            </div>
          </div>
        </div>
      )}

      {!loading && preferences && (
        <>
          <div className="settings-section">
            <div className="settings-section-header">
              <div>
                <h2>
                  <CheckCircle2 size={19} />
                  Integration Status
                </h2>

                <p>
                  Notification providers currently registered with the platform.
                </p>
              </div>
            </div>

            <div className="integration-status-list">
              <div className="integration-status-row">
                <div>
                  <strong>Email</strong>
                  <small>
                    Email notification provider is registered.
                  </small>
                </div>

                <span className="integration-status-badge">
                  <CheckCircle2 size={15} />
                  Registered
                </span>
              </div>

              <div className="integration-status-row">
                <div>
                  <strong>Slack</strong>
                  <small>
                    Slack notification provider is registered.
                  </small>
                </div>

                <span className="integration-status-badge">
                  <CheckCircle2 size={15} />
                  Registered
                </span>
              </div>

              <div className="integration-status-row">
                <div>
                  <strong>Microsoft Teams</strong>
                  <small>
                    Teams notification provider is registered.
                  </small>
                </div>

                <span className="integration-status-badge">
                  <CheckCircle2 size={15} />
                  Registered
                </span>
              </div>
            </div>

            <div className="integration-status-note">
              Provider registration indicates that the backend supports the
              integration. Credentials, SMTP configuration, or webhook
              configuration are managed by the backend environment.
            </div>
          </div>

        <div className="settings-section">
          <div className="settings-section-header">
            <div>
              <h2>
                <Bell size={19} />
                Notification Preferences
              </h2>

              <p>
                Choose how and when the platform
                sends notifications.
              </p>
            </div>

            <button
              type="button"
              className="button-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? (
                <RefreshCw
                  size={17}
                  className="spin"
                />
              ) : (
                <Save size={17} />
              )}
              {saving ? "Saving..." : "Save changes"}
            </button>
          </div>

          <div className="settings-preferences">
            <label className="settings-preference-row">
              <span className="settings-preference-content">
                <strong>Email notifications</strong>
                <small>
                  Receive notifications through email.
                </small>
              </span>

              <input
                type="checkbox"
                checked={preferences.email_enabled}
                onChange={(event) =>
                  updatePreference(
                    "email_enabled",
                    event.target.checked,
                  )
                }
                disabled={saving}
              />
            </label>

            <label className="settings-preference-row">
              <span className="settings-preference-content">
                <strong>Slack notifications</strong>
                <small>
                  Send notifications to your configured Slack integration.
                </small>
              </span>

              <input
                type="checkbox"
                checked={preferences.slack_enabled}
                onChange={(event) =>
                  updatePreference(
                    "slack_enabled",
                    event.target.checked,
                  )
                }
                disabled={saving}
              />
            </label>

            <label className="settings-preference-row">
              <span className="settings-preference-content">
                <strong>Microsoft Teams notifications</strong>
                <small>
                  Send notifications to your configured Teams integration.
                </small>
              </span>

              <input
                type="checkbox"
                checked={preferences.teams_enabled}
                onChange={(event) =>
                  updatePreference(
                    "teams_enabled",
                    event.target.checked,
                  )
                }
                disabled={saving}
              />
            </label>

            <label className="settings-preference-row">
              <span className="settings-preference-content">
                <strong>Critical notifications only</strong>
                <small>
                  Limit notifications to events marked as critical.
                </small>
              </span>

              <input
                type="checkbox"
                checked={preferences.critical_only}
                onChange={(event) =>
                  updatePreference(
                    "critical_only",
                    event.target.checked,
                  )
                }
                disabled={saving}
              />
            </label>

            <label className="settings-preference-row">
              <span className="settings-preference-content">
                <strong>Daily digest</strong>
                <small>
                  Receive a daily summary of relevant notifications.
                </small>
              </span>

              <input
                type="checkbox"
                checked={preferences.daily_digest}
                onChange={(event) =>
                  updatePreference(
                    "daily_digest",
                    event.target.checked,
                  )
                }
                disabled={saving}
              />
            </label>

            <label className="settings-preference-row">
              <span className="settings-preference-content">
                <strong>Weekly digest</strong>
                <small>
                  Receive a weekly summary of relevant notifications.
                </small>
              </span>

              <input
                type="checkbox"
                checked={preferences.weekly_digest}
                onChange={(event) =>
                  updatePreference(
                    "weekly_digest",
                    event.target.checked,
                  )
                }
                disabled={saving}
              />
            </label>
          </div>
        </div>
        </>
      )}
    </section>
  );
}

export default Settings;
