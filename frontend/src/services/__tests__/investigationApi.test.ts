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
  createInvestigation,
  getInvestigation,
  getInvestigations,
  runAIInvestigation,
} from "../investigationApi";

describe("investigationApi", () => {
  beforeEach(() => {
    mocks.post.mockReset();
    mocks.get.mockReset();
  });

  it("creates an investigation", async () => {
    const investigation = {
      id: 101,
      title: "Database outage",
      description: "Investigate the production database outage.",
      status: "pending",
    };

    mocks.post.mockResolvedValueOnce({
      data: investigation,
    });

    const payload = {
      title: investigation.title,
      description: investigation.description,
    };

    const result = await createInvestigation(payload);

    expect(mocks.post).toHaveBeenCalledWith(
      "/api/v1/investigations",
      payload,
    );
    expect(result).toEqual(investigation);
  });

  it("gets an investigation by id", async () => {
    const investigation = {
      id: 101,
      title: "Database outage",
      description: "Investigate the production database outage.",
      status: "pending",
    };

    const config = {
      signal: new AbortController().signal,
    };

    mocks.get.mockResolvedValueOnce({
      data: investigation,
    });

    const result = await getInvestigation(101, config);

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/investigations/101",
      config,
    );
    expect(result).toEqual(investigation);
  });

  it("gets paginated investigations with filters", async () => {
    const response = {
      items: [
        {
          id: 101,
          title: "Database outage",
          description: "Investigate the production database outage.",
          status: "pending",
        },
      ],
      total: 1,
      skip: 0,
      limit: 10,
      has_next: false,
    };

    mocks.get.mockResolvedValueOnce({
      data: response,
    });

    const config = {
      signal: new AbortController().signal,
    };

    const result = await getInvestigations(
      {
        skip: 0,
        limit: 10,
        search: "database",
        status_filter: "pending",
      },
      config,
    );

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/investigations",
      {
        ...config,
        params: {
          skip: 0,
          limit: 10,
          search: "database",
          status_filter: "pending",
        },
      },
    );

    expect(result).toEqual(response);
  });

  it("runs an AI investigation", async () => {
    const investigation = {
      id: 101,
      title: "Database outage",
      description: "Investigate the production database outage.",
      status: "completed",
    };

    const payload = {
      log_file_id: 1869,
    };

    mocks.post.mockResolvedValueOnce({
      data: investigation,
    });

    const result = await runAIInvestigation(
      101,
      payload,
    );

    expect(mocks.post).toHaveBeenCalledWith(
      "/api/v1/investigations/101/run",
      payload,
    );
    expect(result).toEqual(investigation);
  });
});
