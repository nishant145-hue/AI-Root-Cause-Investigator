import api from "./api";

export type NotificationProvider =
  | "email"
  | "slack"
  | "teams";

export type NotificationSeverity =
  | "info"
  | "warning"
  | "critical";

export type NotificationStatus =
  | "pending"
  | "sent"
  | "failed";

export interface Notification {
  id: number;
  user_id: number | null;
  provider: NotificationProvider;
  severity: NotificationSeverity;
  status: NotificationStatus;
  subject: string;
  message: string;
  metadata_json: Record<string, unknown>;
  retry_count: number;
  error_message: string | null;
  created_at: string;
  sent_at: string | null;
  is_read: boolean;
  read_at: string | null;
  is_archived: boolean;
  archived_at: string | null;
}

export interface NotificationListParams {
  skip?: number;
  limit?: number;
  is_read?: boolean;
  is_archived?: boolean;
}

export interface NotificationPreferences {
  id: number;
  user_id: number;
  email_enabled: boolean;
  slack_enabled: boolean;
  teams_enabled: boolean;
  critical_only: boolean;
  daily_digest: boolean;
  weekly_digest: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferencesUpdate {
  email_enabled?: boolean;
  slack_enabled?: boolean;
  teams_enabled?: boolean;
  critical_only?: boolean;
  daily_digest?: boolean;
  weekly_digest?: boolean;
}

export interface NotificationBulkRequest {
  notification_ids: number[];
}

const notificationApi = {
  async list(
    params: NotificationListParams = {},
  ): Promise<Notification[]> {
    const response = await api.get<Notification[]>(
      "/api/v1/notifications",
      { params },
    );

    return response.data;
  },

  async getUnreadCount(): Promise<number> {
    const response = await api.get<number>(
      "/api/v1/notifications/unread-count",
    );

    return response.data;
  },

  async markAllRead(): Promise<number> {
    const response = await api.patch<number>(
      "/api/v1/notifications/read-all",
    );

    return response.data;
  },

  async markRead(
    notificationId: number,
  ): Promise<Notification> {
    const response = await api.patch<Notification>(
      `/api/v1/notifications/${notificationId}/read`,
    );

    return response.data;
  },

  async archive(
    notificationId: number,
  ): Promise<Notification> {
    const response = await api.patch<Notification>(
      `/api/v1/notifications/${notificationId}/archive`,
    );

    return response.data;
  },

  async unarchive(
    notificationId: number,
  ): Promise<Notification> {
    const response = await api.patch<Notification>(
      `/api/v1/notifications/${notificationId}/unarchive`,
    );

    return response.data;
  },

  async archiveAll(): Promise<number> {
    const response = await api.patch<number>(
      "/api/v1/notifications/archive-all",
    );

    return response.data;
  },

  async delete(
    notificationId: number,
  ): Promise<void> {
    await api.delete(
      `/api/v1/notifications/${notificationId}`,
    );
  },

  async bulkRead(
    notificationIds: number[],
  ): Promise<number> {
    const response = await api.patch<number>(
      "/api/v1/notifications/bulk/read",
      { notification_ids: notificationIds },
    );

    return response.data;
  },

  async bulkUnread(
    notificationIds: number[],
  ): Promise<number> {
    const response = await api.patch<number>(
      "/api/v1/notifications/bulk/unread",
      { notification_ids: notificationIds },
    );

    return response.data;
  },

  async bulkArchive(
    notificationIds: number[],
  ): Promise<number> {
    const response = await api.patch<number>(
      "/api/v1/notifications/bulk/archive",
      { notification_ids: notificationIds },
    );

    return response.data;
  },

  async bulkUnarchive(
    notificationIds: number[],
  ): Promise<number> {
    const response = await api.patch<number>(
      "/api/v1/notifications/bulk/unarchive",
      { notification_ids: notificationIds },
    );

    return response.data;
  },

  async bulkDelete(
    notificationIds: number[],
  ): Promise<number> {
    const response = await api.delete<number>(
      "/api/v1/notifications/bulk",
      {
        data: {
          notification_ids: notificationIds,
        },
      },
    );

    return response.data;
  },

  async retry(
    notificationId: number,
  ): Promise<Notification> {
    const response = await api.post<Notification>(
      `/api/v1/notifications/${notificationId}/retry`,
    );

    return response.data;
  },

  async getPreferences(): Promise<NotificationPreferences> {
    const response =
      await api.get<NotificationPreferences>(
        "/api/v1/notifications/preferences",
      );

    return response.data;
  },

  async updatePreferences(
    data: NotificationPreferencesUpdate,
  ): Promise<NotificationPreferences> {
    const response =
      await api.put<NotificationPreferences>(
        "/api/v1/notifications/preferences",
        data,
      );

    return response.data;
  },
};

export default notificationApi;
