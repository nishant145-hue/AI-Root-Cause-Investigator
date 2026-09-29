import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock("../api", () => ({
  default: {
    get: mocks.get,
  },
}));

import { getHealth } from "../systemApi";

describe("systemApi", () => {
  beforeEach(() => {
    mocks.get.mockReset();
  });

  it("gets the system health status", async () => {
    const data = {
      status: "ok",
      database: "healthy",
      qdrant: "healthy",
    };

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getHealth();

    expect(mocks.get).toHaveBeenCalledWith("/health");
    expect(result).toEqual(data);
    expect(result.status).toBe("ok");
  });
});
