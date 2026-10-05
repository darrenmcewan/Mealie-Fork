<template>
  <div>
    <p v-if="!items.length" class="insight-empty" role="status">
      {{ emptyText }}
    </p>
    <div v-else class="insight-recipes">
      <v-card
        v-for="item in items"
        :key="item.recipe.id"
        class="insight-recipe"
        variant="outlined"
        :to="`/g/${groupSlug}/r/${item.recipe.slug}`"
      >
        <RecipeCardImage
          :recipe-id="item.recipe.id"
          :image-version="item.recipe.image"
          :alt="item.recipe.name"
          :height="144"
          small
        />
        <div class="insight-recipe-body">
          <div class="insight-recipe-title">
            <h3>{{ item.recipe.name }}</h3>
            <v-icon v-if="item.isFavorite" :icon="mdiHeart" color="secondary" size="18" :title="t('cooking-insights.favorite')" />
          </div>
          <p v-if="item.reason" class="insight-reason">
            {{ reasonText(item) }}
          </p>
          <p v-if="mode === 'frequent' || mode === 'seasonal'" class="insight-count">
            {{ t('cooking-insights.days-count', { count: item.cookingDays || 0 }) }}
          </p>
          <p v-if="mode === 'seasonal' && item.yearsObserved">
            {{ t('cooking-insights.years-observed', { years: item.yearsObserved }) }}
          </p>
          <p v-if="item.lastCookingDate">
            {{ t(item.lastCookingSource === 'mealplan' ? 'cooking-insights.last-inferred' : 'cooking-insights.last-recorded', { date: displayDate(item.lastCookingDate) }) }}
          </p>
          <p v-else>
            {{ t('cooking-insights.no-recorded') }}
          </p>
          <p v-if="mode === 'favorites' && item.daysSinceLastCooking !== null && item.daysSinceLastCooking !== undefined">
            {{ t('cooking-insights.gap', { days: item.daysSinceLastCooking }) }}
          </p>
          <p v-if="item.rating !== null && item.rating !== undefined">
            {{ t('cooking-insights.rating', { rating: item.rating }) }}
          </p>
          <p v-if="item.includesInferredActivity" class="insight-source">
            {{ t('cooking-insights.sources', { recorded: item.recordedDays || 0, inferred: item.inferredOnlyDays || 0 }) }}
          </p>
        </div>
      </v-card>
    </div>
    <p v-if="collection.truncated" class="text-body-2 mt-3">
      {{ t('cooking-insights.showing', { shown: items.length, total: collection.total || 0 }) }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { mdiHeart } from "@mdi/js";
import { parseISO } from "date-fns";
import RecipeCardImage from "./RecipeCardImage.vue";
import type { CookingInsightCollection, CookingInsightItem } from "~/lib/api/types/user";

const props = withDefaults(defineProps<{
  collection: CookingInsightCollection;
  groupSlug: string;
  mode: "frequent" | "favorites" | "seasonal" | "recommendations";
  emptyText?: string;
  referenceMonth?: number;
}>(), { emptyText: "", referenceMonth: 1 });

const { t, d, locale } = useI18n();
const items = computed(() => props.collection.items || []);
const displayDate = (value: string) => d(parseISO(value));

function reasonText(item: CookingInsightItem) {
  if (item.reason === "neglected_favorite") {
    return t("cooking-insights.reason-neglected", { days: item.daysSinceLastCooking || 0 });
  }
  if (item.reason === "recurring_month") {
    const month = new Intl.DateTimeFormat(locale.value, { month: "long" }).format(new Date(2024, props.referenceMonth - 1, 15));
    return t("cooking-insights.reason-seasonal", { month, years: item.yearsObserved || 0 });
  }
  if (item.rating !== null && item.rating !== undefined) return t("cooking-insights.reason-rating", { rating: item.rating });
  return t("cooking-insights.reason-favorite");
}
</script>

<style scoped>
.insight-recipes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr));
  gap: 20px;
}
.insight-recipe {
  min-width: 0;
  border-radius: 8px;
  border-color: rgba(var(--v-theme-on-surface), 0.14);
}
.insight-recipe-body {
  padding: 16px;
}
.insight-recipe-title {
  display: flex;
  align-items: start;
  gap: 8px;
  margin-bottom: 10px;
}
.insight-recipe-title h3 {
  font-size: 18px;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
}
.insight-recipe-body p {
  margin: 5px 0;
  font-size: 14px;
  line-height: 1.5;
}
.insight-recipe-body .insight-count {
  font-size: 16px;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}
.insight-reason {
  font-weight: 600;
}
.insight-source {
  color: rgb(var(--v-theme-info));
}
.insight-empty {
  padding: 28px 0;
  color: rgba(var(--v-theme-on-surface), 0.72);
}
</style>
