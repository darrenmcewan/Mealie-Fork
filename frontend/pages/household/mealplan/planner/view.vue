<template>
  <div class="planner-view-grid">
    <section
      v-for="(day, index) in plan"
      :key="index"
      class="planner-day"
      :class="{ 'planner-day--today': isToday(day.date) }"
    >
      <header class="planner-day-heading">
        <h2>
          <time :datetime="format(day.date, 'yyyy-MM-dd')" :aria-current="isToday(day.date) ? 'date' : undefined">
            <span class="planner-day-number">{{ $d(day.date, { day: "numeric" }) }}</span>
            <span class="planner-day-date">
              <span>{{ $d(day.date, { weekday: "long" }) }}</span>
              <span class="planner-day-month">{{ $d(day.date, { month: "long", year: "numeric" }) }}</span>
            </span>
          </time>
        </h2>
        <GroupMealPlanDayContextMenu v-if="day.recipes.length" :recipes="day.recipes" />
      </header>
      <div v-if="!day.sections.length" class="planner-day-empty">
        <p>{{ $t('meal-plan.no-meal-plan-defined-yet') }}</p>
        <v-btn
          :to="{ path: '/household/mealplan/planner/edit', query: { date: format(day.date, 'yyyy-MM-dd') } }"
          variant="tonal"
          color="primary"
          min-height="44"
        >
          <v-icon start>
            {{ $globals.icons.createAlt }}
          </v-icon>
          {{ $t('general.add') }}
        </v-btn>
      </div>
      <div v-for="section in day.sections" :key="section.title">
        <div class="planner-meal-type">
          <h3>
            {{ section.title }}
          </h3>
          <span>{{ section.meals.length }}</span>
        </div>

        <div v-for="mealplan in section.meals" :key="mealplan.id" class="mb-3">
          <RecipeCardMobile
            :recipe-id="mealplan.recipe ? mealplan.recipe.id! : ''"
            :rating="mealplan.recipe ? mealplan.recipe.rating! : 0"
            :slug="mealplan.recipe ? mealplan.recipe.slug! : mealplan.title!"
            :description="mealplan.recipe ? mealplan.recipe.description! : mealplan.text!"
            :name="mealplan.recipe ? mealplan.recipe.name! : mealplan.title!"
            :tags="mealplan.recipe ? mealplan.recipe.tags! : []"
          />
          <p v-if="mealplan.expectedLeftovers != null" class="planner-portion-summary">
            {{ $t('meal-plan.expected-leftovers-count', { count: mealplan.expectedLeftovers }) }}
            <br>{{ $t('meal-plan.portions-unallocated', { count: mealplan.availableLeftovers }) }}
            <br>{{ $t('meal-plan.portions-reserved', { count: mealplan.reservedLeftovers }) }}
          </p>
          <p v-if="mealplan.leftoverSource" class="planner-portion-summary">
            {{ $t('meal-plan.leftover-meal-count', { count: mealplan.eatenPortions }) }}
            <br>
            <NuxtLink :to="{ path: '/household/mealplan/planner/view', query: { date: mealplan.leftoverSource.date } }">
              {{ $t('meal-plan.source-meal-date', { date: mealplan.leftoverSource.date }) }}
            </NuxtLink>
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { format, isToday } from "date-fns";
import type { MealsByDate } from "./types";
import type { ReadPlanEntry } from "~/lib/api/types/meal-plan";
import GroupMealPlanDayContextMenu from "~/components/Domain/Household/GroupMealPlanDayContextMenu.vue";
import RecipeCardMobile from "~/components/Domain/Recipe/RecipeCardMobile.vue";
import type { RecipeSummary } from "~/lib/api/types/recipe";

const props = defineProps<{
  mealplans: MealsByDate[];
}>();

type DaySection = {
  title: string;
  meals: ReadPlanEntry[];
};

type Days = {
  date: Date;
  sections: DaySection[];
  recipes: RecipeSummary[];
};

const i18n = useI18n();

const plan = computed<Days[]>(() => {
  return props.mealplans.reduce((acc, day) => {
    const out: Days = {
      date: day.date,
      sections: [
        { title: i18n.t("meal-plan.breakfast"), meals: [] },
        { title: i18n.t("meal-plan.lunch"), meals: [] },
        { title: i18n.t("meal-plan.dinner"), meals: [] },
        { title: i18n.t("meal-plan.side"), meals: [] },
      ],
      recipes: [],
    };

    for (const meal of day.meals) {
      if (meal.entryType === "breakfast") {
        out.sections[0].meals.push(meal);
      }
      else if (meal.entryType === "lunch") {
        out.sections[1].meals.push(meal);
      }
      else if (meal.entryType === "dinner") {
        out.sections[2].meals.push(meal);
      }
      else if (meal.entryType === "side") {
        out.sections[3].meals.push(meal);
      }

      if (meal.recipe) {
        out.recipes.push(meal.recipe);
      }
    }

    // Drop empty sections
    out.sections = out.sections.filter(section => section.meals.length > 0);

    acc.push(out);

    return acc;
  }, [] as Days[]);
});
</script>

<style scoped>
.planner-view-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 32px 24px;
  align-items: start;
}

.planner-day {
  min-width: 0;
}

.planner-portion-summary {
  margin: 8px 0;
  font-size: 0.8125rem;
  overflow-wrap: anywhere;
}

.planner-day-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--mealie-border);
}

.planner-day-heading h2 {
  min-width: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.planner-day-heading time {
  display: flex;
  align-items: center;
  gap: 12px;
}

.planner-day-number {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  font-size: 1.5rem;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.planner-day--today .planner-day-number {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
}

.planner-day-date {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.planner-day-month {
  color: var(--mealie-muted);
  font-size: 0.75rem;
  font-weight: 400;
}

.planner-day-empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  padding-block: 20px 12px;
  font-size: 0.8125rem;
  color: var(--mealie-muted);
}

.planner-meal-type {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 16px 0 8px;
  color: rgb(var(--v-theme-primary));
}

.planner-meal-type h3,
.planner-meal-type span {
  font-size: 0.8125rem;
  font-weight: 600;
}

.planner-view-grid :deep(.v-card) {
  border-radius: 6px;
}

.planner-view-grid :deep(.v-btn) {
  min-width: 44px;
  min-height: 44px;
  letter-spacing: 0;
}

@media (max-width: 1199px) {
  .planner-view-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 699px) {
  .planner-view-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 28px;
  }
}
</style>
