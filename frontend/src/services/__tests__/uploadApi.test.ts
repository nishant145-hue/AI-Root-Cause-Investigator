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
  getUploads,
  uploadLog,
} from "../uploadApi";

describe("uploadApi", () => {
  beforeEach(() => {
    mocks.post.mockReset();
    mocks.get.mockReset();
  });

  it("uploads a file as multipart FormData", async () => {
    mocks.post.mockResolvedValueOnce({
      data: {
        id: 1869,
        filename: "application.log",
        content_type: "text/plain",
        size: 1024,
        parsed_logs: 29,
        status: "uploaded",
        uploaded_at: "2026-09-29T00:00:00Z",
        saved_as: "application.log",
        file_path: "/uploads/application.log",
        message: "File uploaded successfully",
      },
    });

    const file = new File(
      ["log entry"],
      "application.log",
      {
        type: "text/plain",
      },
    );

    const result = await uploadLog(file);

    expect(mocks.post).toHaveBeenCalledTimes(1);

    const [url, body] = mocks.post.mock.calls[0];

    expect(url).toBe("/api/v1/uploads");
    expect(body).toBeInstanceOf(FormData);
    expect(body.get("file")).toBe(file);

    expect(result.id).toBe(1869);
    expect(result.parsed_logs).toBe(29);
    expect(result.status).toBe("uploaded");
  });

  it("gets uploaded files with the supplied request config", async () => {
    const config = {
      signal: new AbortController().signal,
    };

    mocks.get.mockResolvedValueOnce({
      data: [],
    });

    const result = await getUploads(config);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/uploads",
      config,
    );
    expect(result).toEqual([]);
  });
});
