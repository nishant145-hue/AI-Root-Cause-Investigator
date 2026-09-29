import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
}));

vi.mock("../api", () => ({
  default: {
    post: mocks.post,
    get: mocks.get,
  },
}));

import {
  getCurrentUser,
  login,
  logout,
  refreshToken,
  register,
} from "../authApi";

describe("authApi", () => {
  beforeEach(() => {
    mocks.post.mockReset();
    mocks.get.mockReset();
  });

  it("sends login credentials as form data", async () => {
    mocks.post.mockResolvedValueOnce({
      data: {
        access_token: "access-token",
        refresh_token: "refresh-token",
        token_type: "bearer",
      },
    });

    const result = await login({
      username: "testuser",
      password: "password123",
    });

    expect(mocks.post).toHaveBeenCalledTimes(1);

    const [url, body, config] = mocks.post.mock.calls[0];

    expect(url).toBe("/api/v1/auth/login");
    expect(body).toBeInstanceOf(URLSearchParams);
    expect(body.get("username")).toBe("testuser");
    expect(body.get("password")).toBe("password123");
    expect(body.get("grant_type")).toBe("password");
    expect(config).toEqual({
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    expect(result.access_token).toBe("access-token");
  });

  it("sends registration data to the register endpoint", async () => {
    mocks.post.mockResolvedValueOnce({
      data: {
        id: 1,
        username: "testuser",
        email: "test@example.com",
        full_name: "Test User",
        role: "user",
        is_active: true,
        is_verified: false,
        created_at: "2026-09-29T00:00:00Z",
      },
    });

    const registration = {
      username: "testuser",
      email: "test@example.com",
      password: "password123",
      full_name: "Test User",
    };

    const result = await register(registration);

    expect(mocks.post).toHaveBeenCalledTimes(1);
    expect(mocks.post).toHaveBeenCalledWith(
      "/api/v1/auth/register",
      registration,
    );
    expect(result.username).toBe("testuser");
    expect(result.email).toBe("test@example.com");
  });

  it("gets the current authenticated user", async () => {
    mocks.get.mockResolvedValueOnce({
      data: {
        id: 1,
        username: "testuser",
        email: "test@example.com",
        role: "user",
        is_active: true,
        is_verified: true,
        created_at: "2026-09-29T00:00:00Z",
      },
    });

    const result = await getCurrentUser();

    expect(mocks.get).toHaveBeenCalledTimes(1);
    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/auth/me",
    );
    expect(result.username).toBe("testuser");
  });

  it("refreshes the access token", async () => {
    mocks.post.mockResolvedValueOnce({
      data: {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
        token_type: "bearer",
      },
    });

    const result = await refreshToken({
      refresh_token: "old-refresh-token",
    });

    expect(mocks.post).toHaveBeenCalledWith(
      "/api/v1/auth/refresh",
      {
        refresh_token: "old-refresh-token",
      },
    );
    expect(result.access_token).toBe("new-access-token");
  });

  it("logs out using the refresh token", async () => {
    mocks.post.mockResolvedValueOnce({
      data: {},
    });

    await logout("refresh-token");

    expect(mocks.post).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      {
        refresh_token: "refresh-token",
      },
    );
  });
});
