import { nextTick, ref } from "vue";
import { afterEach, describe, expect, test, vi } from "vitest";
import { cookingTimeZone, useCookingInsights } from "./use-cooking-insights";
import type { CookingInsightsQuery, CookingInsightsResponse } from "~/lib/api/types/user";

function snapshot(filters: CookingInsightsQuery, days = 0): CookingInsightsResponse {
  return {
    filters,
    coverage: { cookingDays: days },
    frequentMeals: {},
    neglectedFavorites: {},
    favoritesWithoutHistory: {},
    recommendations: {},
    monthlyHabits: [],
  };
}

async function settle() {
  await nextTick();
  await Promise.resolve();
  await nextTick();
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("cooking insights requests", () => {
  test("sends bounded dates, zone, and source policy", async () => {
    const fetch = vi.fn(async (query: CookingInsightsQuery) => ({ data: snapshot(query) }));
    const state = useCookingInsights(fetch, ref("person:group"));
    await settle();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0][0]).toMatchObject({ includeInferred: false, limit: 10, timeZone: cookingTimeZone() });
    state.filters.value.includeInferred = true;
    state.setWindow(30);
    await settle();
    expect(state.data.value?.filters.includeInferred).toBe(true);
    expect(state.loading.value).toBe(false);
  });

  test("only the newest response is displayed", async () => {
    const pending: Array<(value: { data: CookingInsightsResponse }) => void> = [];
    const fetch = vi.fn(() => new Promise<{ data: CookingInsightsResponse }>(resolve => pending.push(resolve)));
    const state = useCookingInsights(fetch, ref("person:group"));
    state.filters.value.includeInferred = true;
    await nextTick();
    pending[1]({ data: snapshot(state.filters.value, 2) });
    await settle();
    pending[0]({ data: snapshot({}, 1) });
    await settle();
    expect(state.data.value?.coverage.cookingDays).toBe(2);
  });

  test("errors are distinct from empty results and can be retried", async () => {
    const fetch = vi.fn().mockRejectedValueOnce(new Error("Unavailable")).mockResolvedValue({ data: snapshot({}) });
    const state = useCookingInsights(fetch, ref("person:group"));
    await settle();
    expect(state.error.value).toBe(true);
    expect(state.data.value).toBeNull();
    await state.refresh();
    expect(state.error.value).toBe(false);
    expect(state.data.value).not.toBeNull();
  });

  test("identity changes clear personal data and ignore pending old requests", async () => {
    const pending: Array<(value: { data: CookingInsightsResponse }) => void> = [];
    const fetch = vi.fn(() => new Promise<{ data: CookingInsightsResponse }>(resolve => pending.push(resolve)));
    const identity = ref<string | null>("person:group");
    const state = useCookingInsights(fetch, identity);
    identity.value = null;
    await settle();
    pending[0]({ data: snapshot({}, 4) });
    await settle();
    expect(state.data.value).toBeNull();
    expect(state.loading.value).toBe(false);
    identity.value = "person:another-group";
    await settle();
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  test("invalid dates never show the previous result or make a new request", async () => {
    const fetch = vi.fn(async (query: CookingInsightsQuery) => ({ data: snapshot(query) }));
    const state = useCookingInsights(fetch, ref("person:group"));
    await settle();
    state.filters.value.startDate = "invalid";
    await settle();
    expect(state.validation.value).toBe("invalid-window");
    expect(state.data.value).toBeNull();
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  test("falls back to UTC when browser zone detection is unavailable", () => {
    vi.spyOn(Intl, "DateTimeFormat").mockImplementation(() => {
      throw new Error("Unavailable");
    });
    expect(cookingTimeZone()).toBe("UTC");
  });
});
