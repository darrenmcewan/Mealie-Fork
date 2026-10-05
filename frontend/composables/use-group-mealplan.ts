import { format } from "date-fns";
import { ref, watch } from "vue";
import type { Ref } from "vue";
import { useAsyncKey } from "./use-utils";
import { useUserApi } from "~/composables/api";
import type { CreatePlanEntry, PlanEntryType, ReadPlanEntry, UpdatePlanEntry } from "~/lib/api/types/meal-plan";
import type { RequestResponse } from "~/lib/api/types/non-generated";

type PlanOption = {
  text: string;
  value: PlanEntryType;
};
export function usePlanTypeOptions() {
  const i18n = useI18n();

  return [
    { text: i18n.t("meal-plan.breakfast"), value: "breakfast" },
    { text: i18n.t("meal-plan.lunch"), value: "lunch" },
    { text: i18n.t("meal-plan.dinner"), value: "dinner" },
    { text: i18n.t("meal-plan.side"), value: "side" },
  ] as PlanOption[];
}

export function getEntryTypeText(value: PlanEntryType) {
  const i18n = useI18n();
  return i18n.t("meal-plan." + value);
}
export interface DateRange {
  start: Date;
  end: Date;
}

export const useMealplans = function (range: Ref<DateRange>) {
  const api = useUserApi();
  const loading = ref(false);
  const validForm = ref(true);
  const lastError = ref<{ message: string; mealIds: number[] } | null>(null);
  const allocationVersion = ref(0);

  async function mutate(operation: () => Promise<RequestResponse<ReadPlanEntry>>) {
    loading.value = true;
    lastError.value = null;
    try {
      const result = await operation();
      if (!result.data) {
        const detail = result.error?.response?.data?.detail;
        lastError.value = {
          message: typeof detail?.message === "string" ? detail.message : "",
          mealIds: Array.isArray(detail?.mealIds) ? detail.mealIds : [],
        };
      }
      await actions.refreshAll();
      return !!result.data;
    }
    catch {
      lastError.value = { message: "", mealIds: [] };
      return false;
    }
    finally {
      allocationVersion.value += 1;
      loading.value = false;
    }
  }

  const actions = {
    getAll() {
      loading.value = true;
      const { data: units } = useAsyncData(useAsyncKey(), async () => {
        const query = {
          start_date: format(range.value.start, "yyyy-MM-dd"),
          end_date: format(range.value.end, "yyyy-MM-dd"),
        };
        const { data } = await api.mealplans.getAll(1, -1, { start_date: query.start_date, end_date: query.end_date });

        if (data) {
          return data.items;
        }
        else {
          return null;
        }
      });

      loading.value = false;
      return units;
    },
    async refreshAll() {
      loading.value = true;
      try {
        const query = {
          start_date: format(range.value.start, "yyyy-MM-dd"),
          end_date: format(range.value.end, "yyyy-MM-dd"),
        };
        const { data } = await api.mealplans.getAll(1, -1, query);
        if (data && data.items) {
          mealplans.value = data.items;
        }
      }
      finally {
        loading.value = false;
      }
    },
    async createOne(payload: CreatePlanEntry) {
      return await mutate(() => api.mealplans.createOne(payload));
    },
    async updateOne(updateData: UpdatePlanEntry) {
      if (!updateData.id) {
        return false;
      }
      return await mutate(() => api.mealplans.updateOne(updateData.id, updateData));
    },

    async deleteOne(id: string | number) {
      return await mutate(() => api.mealplans.deleteOne(id));
    },

    async setType(payload: UpdatePlanEntry, type: PlanEntryType) {
      return await this.updateOne({ ...payload, entryType: type });
    },
    getLeftovers: api.mealplans.getLeftovers.bind(api.mealplans),
  };

  const mealplans = actions.getAll();

  watch(range, actions.refreshAll);

  return { mealplans, actions, validForm, loading, lastError, allocationVersion };
};
