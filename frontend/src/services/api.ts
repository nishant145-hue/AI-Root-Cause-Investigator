import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export interface ApiRequestConfig {
  signal?: AbortSignal;
}
export interface ApiValidationError {
  loc: Array<string | number>;
  msg: string;
  type: string;
}

export class ApiError extends Error {
  readonly status: number | null;
  readonly detail: unknown;
  readonly validationErrors: ApiValidationError[];

  constructor(
    message: string,
    options: {
      status?: number | null;
      detail?: unknown;
      validationErrors?: ApiValidationError[];
    } = {},
  ) {
    super(message);
    this.name = "ApiError";

    this.status = options.status ?? null;
    this.detail = options.detail ?? null;
    this.validationErrors =
      options.validationErrors ?? [];
  }
}

interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface RetryableRequestConfig
  extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

interface ErrorResponseBody {
  detail?: unknown;
  message?: unknown;
  status?: unknown;
  service?: unknown;
  dependencies?: unknown;
}

let refreshPromise: Promise<string | null> | null = null;

function getErrorMessage(
  status: number | null,
  detail: unknown,
): string {
  if (status === 0) {
    return "Unable to connect to the server. Please check that the backend is running and try again.";
  }

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (status === 400) {
    return "The request could not be processed.";
  }

  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return "The requested resource was not found.";
  }

  if (status === 409) {
    return "The request conflicts with the current state of the resource.";
  }

  if (status === 422) {
    return "Please check the submitted information.";
  }

  if (status === 429) {
    return "Too many requests. Please wait a moment and try again.";
  }

  if (status !== null && status >= 500) {
    return "The server encountered an error. Please try again later.";
  }

  return "An unexpected error occurred. Please try again.";
}

function normalizeValidationErrors(
  detail: unknown,
): ApiValidationError[] {
  if (!Array.isArray(detail)) {
    return [];
  }

  return detail.flatMap((item) => {
    if (
      typeof item !== "object" ||
      item === null
    ) {
      return [];
    }

    const value = item as Record<string, unknown>;

    const loc = Array.isArray(value.loc)
      ? value.loc.filter(
          (part): part is string | number =>
            typeof part === "string" ||
            typeof part === "number",
        )
      : [];

    const msg =
      typeof value.msg === "string"
        ? value.msg
        : "Invalid request data.";

    const type =
      typeof value.type === "string"
        ? value.type
        : "validation_error";

    return [
      {
        loc,
        msg,
        type,
      },
    ];
  });
}

export function normalizeApiError(
  error: unknown,
): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  if (!axios.isAxiosError(error)) {
    return new ApiError(
      "An unexpected error occurred. Please try again.",
      {
        status: null,
        detail: error,
      },
    );
  }

  const axiosError =
    error as AxiosError<ErrorResponseBody>;

  if (!axiosError.response) {
    return new ApiError(
      getErrorMessage(0, null),
      {
        status: 0,
        detail: null,
      },
    );
  }

  const status = axiosError.response.status;
  const data = axiosError.response.data;
  const detail = data?.detail;

  const validationErrors =
    status === 422
      ? normalizeValidationErrors(detail)
      : [];

  return new ApiError(
    getErrorMessage(status, detail),
    {
      status,
      detail,
      validationErrors,
    },
  );
}

export function getApiErrorMessage(
  error: unknown,
  fallback: string,
): string {
  const apiError = normalizeApiError(error);

  return apiError.message || fallback;
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem(
    REFRESH_TOKEN_KEY,
  );

  if (!refreshToken) {
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = axios
      .post<RefreshResponse>(
        `${API_BASE_URL}/api/v1/auth/refresh`,
        {
          refresh_token: refreshToken,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 30000,
        },
      )
      .then((response) => {
        const tokens = response.data;

        localStorage.setItem(
          ACCESS_TOKEN_KEY,
          tokens.access_token,
        );

        localStorage.setItem(
          REFRESH_TOKEN_KEY,
          tokens.refresh_token,
        );

        return tokens.access_token;
      })
      .catch(() => {
        localStorage.removeItem(
          ACCESS_TOKEN_KEY,
        );
        localStorage.removeItem(
          REFRESH_TOKEN_KEY,
        );

        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
  },
  timeout: 30000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(
      ACCESS_TOKEN_KEY,
    );

    if (token) {
      config.headers.Authorization =
        `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest =
      error.config as RetryableRequestConfig | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      const newAccessToken =
        await refreshAccessToken();

      if (newAccessToken) {
        originalRequest.headers.Authorization =
          `Bearer ${newAccessToken}`;

        return api(originalRequest);
      }
    }

    return Promise.reject(
      normalizeApiError(error),
    );
  },
);

export default api;
