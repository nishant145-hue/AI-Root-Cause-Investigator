import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  patch: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));

vi.mock("../api", () => ({
  default: {
    get: mocks.get,
    patch: mocks.patch,
    post: mocks.post,
    put: mocks.put,
    delete: mocks.delete,
  },
}));

import notificationApi from "../notificationApi";

describe("notificationApi", () => {
  beforeEach(() => {
    mocks.get.mockReset();
    mocks.patch.mockReset();
    mocks.post.mockReset();
    mocks.put.mockReset();
    mocks.delete.mockReset();
  });

  it("lists notifications with filters", async () => {
    const data = [
      {
        id: 1,
        provider: "email",
        severity: "critical",
        status: "sent",
        subject: "Critical incident",
        message: "Database unavailable",
        is_read: false,
        is_archived: false,
      },
    ];

    mocks.get.mockResolvedValueOnce({ data });

    const result = await notificationApi.list({
      skip: 0,
      limit: 20,
      is_read: false,
      is_archived: false,
    });

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/notifications",
      {
        params: {
          skip: 0,
          limit: 20,
          is_read: false,
          is_archived: false,
        },
      },
    );
    expect(result).toEqual(data);
  });

  it("gets the unread notification count", async () => {
    mocks.get.mockResolvedValueOnce({
      data: 7,
    });

    const result =
      await notificationApi.getUnreadCount();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/notifications/unread-count",
    );
    expect(result).toBe(7);
  });

  it("marks all notifications as read", async () => {
    mocks.patch.mockResolvedValueOnce({
      data: 5,
    });

    const result =
      await notificationApi.markAllRead();

    expect(mocks.patch).toHaveBeenCalledWith(
      "/api/v1/notifications/read-all",
    );
    expect(result).toBe(5);
  });

  it("marks an individual notification as read", async () => {
    const data = {
      id: 12,
      is_read: true,
    };

    mocks.patch.mockResolvedValueOnce({ data });

    const result =
      await notificationApi.markRead(12);

    expect(mocks.patch).toHaveBeenCalledWith(
      "/api/v1/notifications/12/read",
    );
    expect(result).toEqual(data);
  });

  it("archives and unarchives a notification", async () => {
    const archived = {
      id: 12,
      is_archived: true,
    };

    const unarchived = {
      id: 12,
      is_archived: false,
    };

    mocks.patch
      .mockResolvedValueOnce({ data: archived })
      .mockResolvedValueOnce({ data: unarchived });

    expect(
      await notificationApi.archive(12),
    ).toEqual(archived);

    expect(
      await notificationApi.unarchive(12),
    ).toEqual(unarchived);

    expect(mocks.patch).toHaveBeenNthCalledWith(
      1,
      "/api/v1/notifications/12/archive",
    );

    expect(mocks.patch).toHaveBeenNthCalledWith(
      2,
      "/api/v1/notifications/12/unarchive",
    );
  });

  it("marks selected notifications as read in bulk", async () => {
    mocks.patch.mockResolvedValueOnce({
      data: 3,
    });

    const result =
      await notificationApi.bulkRead([1, 2, 3]);

    expect(mocks.patch).toHaveBeenCalledWith(
      "/api/v1/notifications/bulk/read",
      {
        notification_ids: [1, 2, 3],
      },
    );
    expect(result).toBe(3);
  });

  it("archives selected notifications in bulk", async () => {
    mocks.patch.mockResolvedValueOnce({
      data: 2,
    });

    const result =
      await notificationApi.bulkArchive([4, 5]);

    expect(mocks.patch).toHaveBeenCalledWith(
      "/api/v1/notifications/bulk/archive",
      {
        notification_ids: [4, 5],
      },
    );
    expect(result).toBe(2);
  });

  it("deletes selected notifications in bulk", async () => {
    mocks.delete.mockResolvedValueOnce({
      data: 4,
    });

    const result =
      await notificationApi.bulkDelete([6, 7, 8, 9]);

    expect(mocks.delete).toHaveBeenCalledWith(
      "/api/v1/notifications/bulk",
      {
        data: {
          notification_ids: [6, 7, 8, 9],
        },
      },
    );
    expect(result).toBe(4);
  });

  it("retries a notification", async () => {
    const data = {
      id: 20,
      status: "pending",
    };

    mocks.post.mockResolvedValueOnce({ data });

    const result =
      await notificationApi.retry(20);

    expect(mocks.post).toHaveBeenCalledWith(
      "/api/v1/notifications/20/retry",
    );
    expect(result).toEqual(data);
  });

  it("gets notification preferences", async () => {
    const data = {
      id: 1,
      user_id: 7,
      email_enabled: true,
      slack_enabled: false,
      teams_enabled: true,
      critical_only: false,
      daily_digest: true,
      weekly_digest: false,
    };

    mocks.get.mockResolvedValueOnce({ data });

    const result =
      await notificationApi.getPreferences();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/notifications/preferences",
    );
    expect(result).toEqual(data);
  });

  it("updates notification preferences", async () => {
    const preferences = {
      email_enabled: true,
      slack_enabled: true,
      teams_enabled: false,
      critical_only: true,
      daily_digest: false,
      weekly_digest: true,
    };

    mocks.put.mockResolvedValueOnce({
      data: {
        id: 1,
        user_id: 7,
        ...preferences,
      },
    });

    const result =
      await notificationApi.updatePreferences(
        preferences,
      );

    expect(mocks.put).toHaveBeenCalledWith(
      "/api/v1/notifications/preferences",
      preferences,
    );
    expect(result).toEqual({
      id: 1,
      user_id: 7,
      ...preferences,
    });
  });
});
