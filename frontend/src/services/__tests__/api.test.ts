import { describe, expect, it } from "vitest";
import axios from "axios";

import {
  ApiError,
  normalizeApiError,
} from "../api";

describe("normalizeApiError", () => {
  it("normalizes a 400 error", () => {
    const error = new axios.AxiosError(
      "Bad request",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 400,
        statusText: "Bad Request",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {},
      },
    );

    const result = normalizeApiError(error);

    expect(result).toBeInstanceOf(ApiError);
    expect(result.status).toBe(400);
    expect(result.message).toBe(
      "The request could not be processed.",
    );
  });

  it("normalizes a 401 error", () => {
    const error = new axios.AxiosError(
      "Unauthorized",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 401,
        statusText: "Unauthorized",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {},
      },
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(401);
    expect(result.message).toBe(
      "Your session has expired. Please sign in again.",
    );
  });

  it("normalizes a 403 error", () => {
    const error = new axios.AxiosError(
      "Forbidden",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 403,
        statusText: "Forbidden",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {},
      },
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(403);
    expect(result.message).toBe(
      "You do not have permission to perform this action.",
    );
  });

  it("normalizes a 404 error", () => {
    const error = new axios.AxiosError(
      "Not found",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 404,
        statusText: "Not Found",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {},
      },
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(404);
    expect(result.message).toBe(
      "The requested resource was not found.",
    );
  });

  it("normalizes a 409 error", () => {
    const error = new axios.AxiosError(
      "Conflict",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 409,
        statusText: "Conflict",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {},
      },
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(409);
    expect(result.message).toBe(
      "The request conflicts with the current state of the resource.",
    );
  });

  it("normalizes 422 validation errors", () => {
    const error = new axios.AxiosError(
      "Validation failed",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 422,
        statusText: "Unprocessable Entity",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {
          detail: [
            {
              loc: ["body", "name"],
              msg: "Field required",
              type: "missing",
            },
          ],
        },
      },
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(422);
    expect(result.message).toBe(
      "Please check the submitted information.",
    );
    expect(result.validationErrors).toEqual([
      {
        loc: ["body", "name"],
        msg: "Field required",
        type: "missing",
      },
    ]);
  });

  it("normalizes a 429 error", () => {
    const error = new axios.AxiosError(
      "Too many requests",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 429,
        statusText: "Too Many Requests",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {},
      },
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(429);
    expect(result.message).toBe(
      "Too many requests. Please wait a moment and try again.",
    );
  });

  it("normalizes a 500 error", () => {
    const error = new axios.AxiosError(
      "Server error",
      "ERR_BAD_RESPONSE",
      undefined,
      undefined,
      {
        status: 500,
        statusText: "Internal Server Error",
        headers: new axios.AxiosHeaders(),
        config: { headers: new axios.AxiosHeaders() },
        data: {},
      },
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(500);
    expect(result.message).toBe(
      "The server encountered an error. Please try again later.",
    );
  });

  it("normalizes a network error", () => {
    const error = new axios.AxiosError(
      "Network Error",
      "ERR_NETWORK",
    );

    const result = normalizeApiError(error);

    expect(result.status).toBe(0);
    expect(result.message).toBe(
      "Unable to connect to the server. Please check that the backend is running and try again.",
    );
  });

  it("returns an existing ApiError unchanged", () => {
    const error = new ApiError(
      "Existing API error",
      {
        status: 409,
        detail: "Conflict",
      },
    );

    const result = normalizeApiError(error);

    expect(result).toBe(error);
  });
});



