import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock("../api", () => ({
  default: {
    get: mocks.get,
  },
}));

import { getIntegrationStatus } from "../integrationApi";

describe("integrationApi", () => {
  beforeEach(() => {
    mocks.get.mockReset();
  });

  it("gets the integration status for email, Slack, and Teams", async () => {
    const data = {
      email: {
        registered: true,
        configured: true,
      },
      slack: {
        registered: false,
        configured: false,
      },
      teams: {
        registered: true,
        configured: false,
      },
    };

    mocks.get.mockResolvedValueOnce({ data });

    const result = await getIntegrationStatus();

    expect(mocks.get).toHaveBeenCalledWith(
      "/api/v1/integrations/status",
    );

    expect(result).toEqual(data);
    expect(result.email.configured).toBe(true);
    expect(result.slack.registered).toBe(false);
    expect(result.teams.configured).toBe(false);
  });
});
