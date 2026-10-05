import { expect, test, vi } from "vitest";
import { UserApi } from "./users";

test("cooking insights use the self-only route and preserve query fields", async () => {
  const get = vi.fn().mockResolvedValue({ data: {} });
  const api = { requests: { get } } as unknown as UserApi;
  const query = { startDate: "2024-01-01", endDate: "2024-12-31", timeZone: "Asia/Kathmandu", includeInferred: true, limit: 10 };
  await UserApi.prototype.getCookingInsights.call(api, query);
  expect(get).toHaveBeenCalledWith("/api/users/self/cooking-insights", query);
});
