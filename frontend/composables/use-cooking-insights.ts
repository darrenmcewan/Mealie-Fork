import { computed, ref, watch } from "vue";
import type { Ref } from "vue";
import { differenceInCalendarDays, formatISO, isValid, parseISO, subDays } from "date-fns";
import type { CookingInsightsQuery, CookingInsightsResponse } from "~/lib/api/types/user";

type FetchInsights = (query: CookingInsightsQuery) => Promise<{ data?: CookingInsightsResponse | null }>;

export function cookingTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  }
  catch {
    return "UTC";
  }
}

export function cookingToday(timeZone: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  return ["year", "month", "day"].map(type => parts.find(part => part.type === type)?.value).join("-");
}

export function useCookingInsights(fetchInsights: FetchInsights, identity: Ref<string | null>) {
  const timeZone = cookingTimeZone();
  const today = cookingToday(timeZone);
  const filters = ref<CookingInsightsQuery>({
    startDate: formatISO(subDays(parseISO(today), 364), { representation: "date" }),
    endDate: today,
    timeZone,
    includeInferred: false,
    limit: 10,
  });
  const data = ref<CookingInsightsResponse | null>(null);
  const loading = ref(false);
  const error = ref(false);
  let requestSequence = 0;

  const validation = computed(() => {
    const { startDate, endDate, limit } = filters.value;
    if (!startDate || !endDate || !isValid(parseISO(startDate)) || !isValid(parseISO(endDate)) || startDate > endDate) {
      return "invalid-window";
    }
    if (endDate > cookingToday(filters.value.timeZone || "UTC")) return "future-window";
    if (differenceInCalendarDays(parseISO(endDate), parseISO(startDate)) >= 1827) return "long-window";
    if (!limit || limit < 1 || limit > 50) return "invalid-limit";
    return null;
  });

  async function refresh() {
    const request = ++requestSequence;
    const currentIdentity = identity.value;
    data.value = null;
    error.value = false;
    if (!currentIdentity || validation.value) {
      loading.value = false;
      return;
    }
    loading.value = true;
    try {
      const result = await fetchInsights({ ...filters.value });
      if (request !== requestSequence || currentIdentity !== identity.value) return;
      if (result.data) data.value = result.data;
      else error.value = true;
    }
    catch {
      if (request === requestSequence && currentIdentity === identity.value) error.value = true;
    }
    finally {
      if (request === requestSequence) loading.value = false;
    }
  }

  function setWindow(days: number) {
    const endDate = cookingToday(filters.value.timeZone || "UTC");
    filters.value = {
      ...filters.value,
      startDate: formatISO(subDays(parseISO(endDate), days - 1), { representation: "date" }),
      endDate,
    };
  }

  watch([identity, filters], () => {
    void refresh();
  }, { immediate: true, deep: true });

  return { filters, data, loading, error, validation, refresh, setWindow };
}
