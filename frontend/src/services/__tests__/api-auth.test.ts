import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => {
  const requestHandlers: {
    fulfilled?: (config: any) => any;
    rejected?: (error: unknown) => any;
  } = {};

  const responseHandlers: {
    fulfilled?: (response: unknown) => unknown;
    rejected?: (error: unknown) => unknown;
  } = {};

  const refreshRequest = vi.fn();
  const apiInstance = Object.assign(
    vi.fn(),
    {
      interceptors: {
        request: {
          use: vi.fn((fulfilled, rejected) => {
            requestHandlers.fulfilled = fulfilled;
            requestHandlers.rejected = rejected;
          }),
        },
        response: {
          use: vi.fn((fulfilled, rejected) => {
            responseHandlers.fulfilled = fulfilled;
            responseHandlers.rejected = rejected;
          }),
        },
      },
    },
  );

  return {
    requestHandlers,
    responseHandlers,
    refreshRequest,
    apiInstance,
  };
});


vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => mocks.apiInstance),
    post: mocks.refreshRequest,
    isAxiosError: vi.fn(() => true),
  },
}));

import "../api";


const createLocalStorageMock = () => {
  const store = new Map<string, string>();

  return {
    getItem: (key: string) =>
      store.get(key) ?? null,

    setItem: (
      key: string,
      value: string,
    ) => {
      store.set(key, value);
    },

    removeItem: (key: string) => {
      store.delete(key);
    },

    clear: () => {
      store.clear();
    },
  };
};

describe("central API authentication handling", () => {
  beforeEach(() => {
    globalThis.localStorage =
      createLocalStorageMock() as Storage;

    mocks.refreshRequest.mockReset();
    mocks.apiInstance.mockReset();
  });

  it("adds the access token to authenticated requests", () => {
    localStorage.setItem(
      "access_token",
      "access-token-123",
    );

    const config = {
      headers: {},
    };

    const result =
      mocks.requestHandlers.fulfilled?.(config);

    expect(
      result.headers.Authorization,
    ).toBe("Bearer access-token-123");
  });

  it("does not add Authorization when no access token exists", () => {
    const config = {
      headers: {},
    };

    const result =
      mocks.requestHandlers.fulfilled?.(config);

    expect(
      result.headers.Authorization,
    ).toBeUndefined();
  });

  it("refreshes the token after a 401 response", async () => {
    localStorage.setItem(
      "access_token",
      "expired-token",
    );

    localStorage.setItem(
      "refresh_token",
      "refresh-token",
    );

    mocks.refreshRequest.mockResolvedValueOnce({
      data: {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
        token_type: "bearer",
      },
    });

    mocks.apiInstance.mockResolvedValueOnce({
      data: {
        success: true,
      },
    });

    const originalRequest: {
      headers: Record<string, string>;
      _retry: boolean;
    } = {
      headers: {},
      _retry: false,
    };

    const error = {
      config: originalRequest,
      response: {
        status: 401,
        data: {},
      },
    };

    const result =
      await mocks.responseHandlers.rejected?.(
        error,
      );

    expect(
      mocks.refreshRequest,
    ).toHaveBeenCalledTimes(1);

    expect(
      localStorage.getItem("access_token"),
    ).toBe("new-access-token");

    expect(
      localStorage.getItem("refresh_token"),
    ).toBe("new-refresh-token");

    expect(originalRequest._retry).toBe(true);

    expect(
      originalRequest.headers.Authorization,
    ).toBe("Bearer new-access-token");

    expect(result).toEqual({
      data: {
        success: true,
      },
    });
  });

  it("clears tokens when token refresh fails", async () => {
    localStorage.setItem(
      "access_token",
      "expired-token",
    );

    localStorage.setItem(
      "refresh_token",
      "invalid-refresh-token",
    );

    mocks.refreshRequest.mockRejectedValueOnce(
      new Error("Refresh failed"),
    );

    const originalRequest: {
      headers: Record<string, string>;
      _retry: boolean;
    } = {
      headers: {},
      _retry: false,
    };

    const error = {
      config: originalRequest,
      response: {
        status: 401,
        data: {},
      },
    };

    await expect(
      mocks.responseHandlers.rejected?.(error),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
    });

    expect(
      localStorage.getItem("access_token"),
    ).toBeNull();

    expect(
      localStorage.getItem("refresh_token"),
    ).toBeNull();

    expect(originalRequest._retry).toBe(true);
  });
});



