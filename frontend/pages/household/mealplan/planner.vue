<template>
  <v-container class="planner-page">
    <header class="planner-heading">
      <h1>{{ $t('meal-plan.meal-planner') }}</h1>
      <ButtonLink
        :icon="$globals.icons.calendar"
        :to="`/household/mealplan/settings`"
        :text="$t('general.settings')"
      />
    </header>
    <div class="planner-toolbar">
      <v-tabs class="planner-tabs">
        <v-tab :to="`/household/mealplan/planner/view`">
          {{ $t('general.view') }}
        </v-tab>
        <v-tab :to="`/household/mealplan/planner/edit`">
          {{ $t('general.edit') }}
        </v-tab>
      </v-tabs>
      <div class="planner-calendar-tools">
        <v-btn
          icon
          size="44"
          variant="text"
          class="planner-previous"
          :aria-label="$t('general.back')"
          :title="$t('general.back')"
          @click="shiftRange(-1)"
        >
          <v-icon>{{ $globals.icons.chevronRight }}</v-icon>
        </v-btn>
        <v-menu
          v-model="state.picker"
          :close-on-content-click="false"
          :transition="false"
          offset-y
          min-width="auto"
        >
          <template #activator="{ props }">
            <v-btn
              color="primary"
              variant="text"
              class="planner-date-range"
              min-height="44"
              :title="`${$d(weekRange.start, 'short')} - ${$d(weekRange.end, 'short')}`"
              v-bind="props"
            >
              <v-icon start>
                {{ $globals.icons.calendar }}
              </v-icon>
              {{ $d(weekRange.start, { month: "short", day: "numeric" }) }} - {{ $d(weekRange.end, { month: "short", day: "numeric", year: "numeric" }) }}
            </v-btn>
          </template>

          <v-card>
            <v-date-picker
              v-model="state.range"
              hide-header
              :multiple="'range'"
              :first-day-of-week="firstDayOfWeek"
              :local="$i18n.locale"
            />

            <v-card-text>
              <v-text-field
                v-model="numberOfDays"
                type="number"
                :label="$t('meal-plan.numberOfDays-label')"
                :hint="$t('meal-plan.numberOfDays-hint')"
                persistent-hint
              />
            </v-card-text>
          </v-card>
        </v-menu>
        <v-btn
          icon
          size="44"
          variant="text"
          :aria-label="$t('general.next')"
          :title="$t('general.next')"
          @click="shiftRange(1)"
        >
          <v-icon>{{ $globals.icons.chevronRight }}</v-icon>
        </v-btn>
      </div>
    </div>

    <div>
      <v-alert v-if="lastError" type="error" variant="tonal" class="mb-4" role="alert">
        {{ lastError.message || $t('meal-plan.save-failed') }}
        <span v-if="lastError.mealIds.length">
          {{ $t('meal-plan.linked-meal-ids', { ids: lastError.mealIds.join(', ') }) }}
        </span>
      </v-alert>
      <NuxtPage
        :mealplans="mealsByDate"
        :actions="actions"
        :mutation-error="lastError"
        :allocation-version="allocationVersion"
      />
    </div>
  </v-container>
</template>

<script lang="ts">
import { isSameDay, addDays, differenceInCalendarDays, parseISO } from "date-fns";
import { useHouseholdSelf } from "~/composables/use-households";
import { useMealplans } from "~/composables/use-group-mealplan";
import { useUserMealPlanPreferences } from "~/composables/use-users/preferences";

export default defineNuxtComponent({
  setup() {
    const route = useRoute();
    const router = useRouter();
    const i18n = useI18n();
    const { household } = useHouseholdSelf();

    useSeoMeta({
      title: i18n.t("meal-plan.dinner-this-week"),
    });

    const mealPlanPreferences = useUserMealPlanPreferences();
    const numberOfDays = ref<number>(mealPlanPreferences.value.numberOfDays || 7);
    watch(numberOfDays, (val) => {
      mealPlanPreferences.value.numberOfDays = Number(val);
    });

    // Force to /view if current route is /planner
    if (route.path === "/household/mealplan/planner") {
      router.push("/household/mealplan/planner/view");
    }

    const requestedStart = typeof route.query.date === "string" ? parseISO(route.query.date) : new Date();
    const initialStart = Number.isNaN(requestedStart.getTime()) ? new Date() : requestedStart;
    const state = ref({
      range: [initialStart, addDays(initialStart, adjustForToday(numberOfDays.value))] as [Date, Date],
      start: new Date(),
      picker: false,
      end: addDays(new Date(), adjustForToday(numberOfDays.value)),
    });

    const firstDayOfWeek = computed(() => {
      return household.value?.preferences?.firstDayOfWeek || 0;
    });

    const weekRange = computed(() => {
      const sorted = [...state.value.range].sort((a, b) => a.getTime() - b.getTime());

      const start = sorted[0];
      const end = sorted[sorted.length - 1];

      if (start && end) {
        return { start, end };
      }
      return {
        start: new Date(),
        end: addDays(new Date(), adjustForToday(numberOfDays.value)),
      };
    });

    const { mealplans, actions, lastError, allocationVersion } = useMealplans(weekRange);

    watch(() => route.query.date, (date) => {
      if (typeof date !== "string") return;
      const start = parseISO(date);
      if (!Number.isNaN(start.getTime())) {
        state.value.range = [start, addDays(start, adjustForToday(numberOfDays.value))];
      }
    });

    function filterMealByDate(date: Date) {
      if (!mealplans.value) return [];
      return mealplans.value.filter((meal) => {
        const mealDate = parseISO(meal.date);
        return isSameDay(mealDate, date);
      });
    }

    function adjustForToday(days: number) {
      // The use case for this function is "how many days are we adding to 'today'?"
      // e.g. If the user wants 7 days, we substract one to do "today + 6"
      return days > 0 ? days - 1 : days + 1;
    }

    const days = computed(() => {
      const numDays = differenceInCalendarDays(weekRange.value.end, weekRange.value.start) + 1;

      // Calculate absolute value
      if (numDays < 0) return [];

      return Array.from(Array(numDays).keys()).map(
        (i) => {
          const date = new Date(weekRange.value.start.getTime());
          date.setDate(date.getDate() + i);
          return date;
        },
      );
    });

    const mealsByDate = computed(() => {
      return days.value.map((day) => {
        return { date: day, meals: filterMealByDate(day) };
      });
    });

    function shiftRange(direction: -1 | 1) {
      const offset = direction * Math.max(days.value.length, 1);
      state.value.range = [addDays(weekRange.value.start, offset), addDays(weekRange.value.end, offset)];
    }

    return {
      state,
      actions,
      lastError,
      allocationVersion,
      mealsByDate,
      weekRange,
      firstDayOfWeek,
      numberOfDays,
      shiftRange,
    };
  },
});
</script>

<style scoped>
.planner-page {
  max-width: 1504px;
}

.planner-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 28px;
}

.planner-heading h1 {
  font-family: var(--mealie-display-font) !important;
  font-size: 2.25rem;
  font-weight: 500;
  line-height: 1.25;
  overflow-wrap: anywhere;
  color: rgb(var(--v-theme-on-background));
}

.planner-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-background), 0.12);
}

.planner-tabs {
  max-width: 100%;
  height: 54px;
  padding: 4px;
  border: 1px solid var(--mealie-border);
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.planner-tabs :deep(.v-tab) {
  min-width: 88px;
  height: 44px;
  border-radius: 5px;
  color: var(--mealie-muted);
}

.planner-tabs :deep(.v-tab--selected) {
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  box-shadow: 0 1px 3px rgba(var(--v-theme-on-surface), 0.08);
}

.planner-tabs :deep(.v-tab__slider) {
  display: none;
}

.planner-calendar-tools {
  display: flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  padding: 4px;
  border: 1px solid var(--mealie-border);
  border-radius: 8px;
  background: rgb(var(--v-theme-surface));
}

.planner-heading :deep(.v-btn) {
  min-height: 44px;
  border-radius: 6px;
}

.planner-previous :deep(.v-icon) {
  transform: rotate(180deg);
}

.planner-date-range {
  max-width: 100%;
  border-radius: 6px;
  letter-spacing: 0;
}

.planner-date-range :deep(.v-btn__content) {
  white-space: normal;
  line-height: 1.5;
}

@media (max-width: 600px) {
  .planner-heading {
    align-items: flex-start;
  }

  .planner-heading h1 {
    font-size: 1.875rem;
  }

  .planner-calendar-tools {
    width: 100%;
  }

  .planner-date-range {
    flex: 1;
    min-width: 0;
  }
}
</style>

<style lang="css">
.left-color-border {
  border-left: 5px solid var(--v-primary-base) !important;
}

.bottom-color-border {
  border-bottom: 2px solid var(--v-primary-base) !important;
}
</style>
