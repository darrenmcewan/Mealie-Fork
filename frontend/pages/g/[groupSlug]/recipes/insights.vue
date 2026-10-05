<template>
  <div class="cooking-insights">
    <div class="insights-heading">
      <BasePageTitle>
        <template #title>
          {{ t('cooking-insights.title') }}
        </template>
      </BasePageTitle>
      <v-tooltip :text="t('cooking-insights.refresh')">
        <template #activator="{ props }">
          <v-btn
            v-bind="props"
            variant="text"
            :icon="mdiRefresh"
            :aria-label="t('cooking-insights.refresh')"
            :disabled="loading || !!validation"
            @click="refresh"
          />
        </template>
      </v-tooltip>
    </div>
    <div class="insights-controls">
      <v-select v-model="preset" :items="presets" :label="t('cooking-insights.period')" hide-details @update:model-value="applyPreset" />
      <v-text-field v-model="filters.startDate" type="date" :label="t('cooking-insights.start-date')" :error-messages="validation ? t(`cooking-insights.${validation}`) : []" @update:model-value="preset = null" />
      <v-text-field
        v-model="filters.endDate"
        type="date"
        :label="t('cooking-insights.end-date')"
        :max="today"
        hide-details
        @update:model-value="preset = null"
      />
      <v-select v-model="filters.limit" :items="[10, 25, 50]" :label="t('cooking-insights.results')" hide-details />
    </div>
    <v-checkbox v-model="filters.includeInferred" :label="t('cooking-insights.include-inferred')" color="primary" hide-details class="mb-4" />
    <v-alert v-if="error" type="error" variant="tonal" role="alert" class="mb-5">
      {{ t('cooking-insights.error') }}
      <v-btn variant="text" :prepend-icon="mdiRefresh" @click="refresh">
        {{ t('cooking-insights.retry') }}
      </v-btn>
    </v-alert>
    <div v-else-if="loading" role="status" class="insights-loading">
      <v-progress-linear indeterminate color="primary" />
      <p>{{ t('cooking-insights.loading') }}</p>
    </div>
    <template v-else-if="data">
      <div class="insights-summary">
        <div><span>{{ t('cooking-insights.recorded-days') }}</span><strong>{{ data.coverage.recordedDays || 0 }}</strong></div>
        <div v-if="filters.includeInferred">
          <span>{{ t('cooking-insights.inferred-days') }}</span><strong>{{ data.coverage.inferredOnlyDays || 0 }}</strong>
        </div>
        <div><span>{{ t('cooking-insights.active-dates') }}</span><strong>{{ data.coverage.activeDates || 0 }}</strong></div>
      </div>
      <div class="insights-context text-body-2">
        <span>{{ t('cooking-insights.current-preferences') }}</span>
        <span>{{ t('cooking-insights.as-of', { date: displayDate(data.filters.endDate || '') }) }}</span>
        <span>{{ data.filters.timeZone }}</span>
      </div>
      <v-alert v-if="data.coverage.hasUnclassifiedEvents" type="info" variant="tonal" class="mb-3" role="status">
        {{ t('cooking-insights.coverage-note') }}
      </v-alert>
      <p v-if="filters.includeInferred" class="text-body-2 mb-3">
        {{ t('cooking-insights.inferred-note') }}
      </p>
      <p v-if="data.coverage.firstCookingDate" class="text-body-2 mb-3">
        {{ t('cooking-insights.first-record', { date: displayDate(data.coverage.firstCookingDate) }) }}
      </p>
      <p v-if="!data.coverage.cookingDays" class="text-body-2 mb-3" role="status">
        {{ t('cooking-insights.no-activity') }}
      </p>
      <v-tabs v-model="tab" color="primary" show-arrows class="insights-tabs">
        <v-tab value="frequent">
          {{ t('cooking-insights.frequent') }}
        </v-tab>
        <v-tab value="favorites">
          {{ t('cooking-insights.favorites') }}
        </v-tab>
        <v-tab value="seasonal">
          {{ t('cooking-insights.seasonal') }}
        </v-tab>
        <v-tab value="recommendations">
          {{ t('cooking-insights.recommendations') }}
        </v-tab>
      </v-tabs>
      <v-tabs-window v-model="tab" class="pt-5">
        <v-tabs-window-item value="frequent">
          <CookingInsightList :collection="data.frequentMeals" :group-slug="groupSlug" mode="frequent" :empty-text="t('cooking-insights.no-repeats')" />
        </v-tabs-window-item>
        <v-tabs-window-item value="favorites">
          <CookingInsightList :collection="data.neglectedFavorites" :group-slug="groupSlug" mode="favorites" :empty-text="t('cooking-insights.no-neglected')" />
          <section v-if="data.favoritesWithoutHistory.total" class="mt-7">
            <h2 class="insights-section-title">
              {{ t('cooking-insights.no-recorded') }}
            </h2>
            <CookingInsightList :collection="data.favoritesWithoutHistory" :group-slug="groupSlug" mode="favorites" />
          </section>
        </v-tabs-window-item>
        <v-tabs-window-item value="seasonal">
          <v-alert v-if="!data.coverage.sufficientSeasonalHistory" type="info" variant="outlined" class="mb-4" role="status">
            {{ t('cooking-insights.insufficient-seasonal') }}
          </v-alert>
          <v-table class="monthly-table">
            <thead>
              <tr>
                <th scope="col">
                  {{ t('cooking-insights.month') }}
                </th><th scope="col">
                  {{ t('cooking-insights.cooking-days') }}
                </th><th scope="col">
                  {{ t('cooking-insights.active-dates') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="month in data.monthlyHabits" :key="month.month">
                <th scope="row">
                  {{ monthName(month.month) }}
                </th>
                <td>
                  <div class="month-value">
                    <span>{{ month.cookingDays || 0 }}</span><div class="month-bar-track" aria-hidden="true">
                      <div :style="{ width: `${(month.cookingDays || 0) / maxMonthCount * 100}%` }" />
                    </div>
                  </div>
                </td>
                <td>{{ month.activeDates || 0 }}</td>
              </tr>
            </tbody>
          </v-table>
          <section v-for="month in recurringMonths" :key="month.month" class="mt-7">
            <h2 class="insights-section-title">
              {{ t('cooking-insights.recurring-month', { month: monthName(month.month) }) }}
            </h2>
            <CookingInsightList :collection="month.recurringRecipes || {}" :group-slug="groupSlug" mode="seasonal" />
          </section>
        </v-tabs-window-item>
        <v-tabs-window-item value="recommendations">
          <CookingInsightList :collection="data.recommendations" :group-slug="groupSlug" mode="recommendations" :reference-month="referenceMonth" :empty-text="t('cooking-insights.no-recommendations')" />
        </v-tabs-window-item>
      </v-tabs-window>
    </template>
  </div>
</template>

<script setup lang="ts">
import { mdiRefresh } from "@mdi/js";
import { parseISO } from "date-fns";
import CookingInsightList from "~/components/Domain/Recipe/CookingInsightList.vue";
import { useUserApi } from "~/composables/api";
import { cookingToday, useCookingInsights } from "~/composables/use-cooking-insights";

definePageMeta({ middleware: ["group-only"] });
const route = useRoute();
const { t, d, locale } = useI18n();
const { user } = useMealieAuth();
const api = useUserApi();
const groupSlug = computed(() => String(route.params.groupSlug || ""));
const identity = computed(() => user.value && user.value.groupSlug === groupSlug.value ? `${user.value.id}:${user.value.groupId}` : null);
const { filters, data, loading, error, validation, refresh, setWindow } = useCookingInsights(query => api.users.getCookingInsights(query), identity);
const tab = ref("frequent");
const preset = ref<number | null>(365);
const today = computed(() => cookingToday(filters.value.timeZone || "UTC"));
const presets = computed(() => [
  { title: t("cooking-insights.last-days", { days: 30 }), value: 30 },
  { title: t("cooking-insights.last-days", { days: 90 }), value: 90 },
  { title: t("cooking-insights.one-year"), value: 365 },
  { title: t("cooking-insights.three-years"), value: 1095 },
  { title: t("cooking-insights.custom"), value: null },
]);
const referenceMonth = computed(() => data.value?.filters.endDate ? parseISO(data.value.filters.endDate).getMonth() + 1 : 1);
const maxMonthCount = computed(() => Math.max(1, ...(data.value?.monthlyHabits.map(month => month.cookingDays || 0) || [])));
const recurringMonths = computed(() => data.value?.monthlyHabits.filter(month => month.recurringRecipes?.items?.length) || []);
const displayDate = (value: string) => value ? d(parseISO(value)) : "";
const monthName = (month: number) => new Intl.DateTimeFormat(locale.value, { month: "long" }).format(new Date(2024, month - 1, 15));
function applyPreset(value: number | null) {
  if (value) setWindow(value);
}
useSeoMeta({ title: () => t("cooking-insights.title") });
</script>

<style scoped>
.cooking-insights {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 16px 32px;
}
.insights-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.insights-controls {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr 100px;
  gap: 16px;
  align-items: start;
}
.insights-controls > * {
  min-width: 0;
}
.insights-loading {
  padding: 40px 0;
}
.insights-loading p {
  margin-top: 16px;
}
.insights-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
  padding: 16px 0 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.14);
}
.insights-summary > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.insights-summary span {
  font-size: 14px;
}
.insights-summary strong {
  font-size: 28px;
  line-height: 1.3;
}
.insights-context {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  padding: 16px 0;
}
.insights-section-title {
  font-size: 20px;
  line-height: 1.4;
  margin-bottom: 16px;
}
.insights-tabs {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.14);
}
.month-value {
  display: flex;
  gap: 16px;
  align-items: center;
}
.month-value > span {
  width: 32px;
  flex-shrink: 0;
}
.month-bar-track {
  flex: 1;
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.06);
}
.month-bar-track > div {
  height: 100%;
  background: rgb(var(--v-theme-info));
}
.monthly-table th {
  font-weight: 600;
}
@media (max-width: 700px) {
  .insights-controls {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .insights-summary {
    gap: 20px;
  }
  .month-value {
    gap: 4px;
  }
  .month-bar-track {
    min-width: 24px;
  }
  .monthly-table :deep(th),
  .monthly-table :deep(td) {
    padding: 8px;
    font-size: 13px;
  }
}
@media (max-width: 400px) {
  .insights-controls {
    grid-template-columns: 1fr;
  }
}
</style>
