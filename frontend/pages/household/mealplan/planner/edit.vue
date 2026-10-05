<template>
  <div class="planner-editor">
    <!-- Create Meal Dialog -->
    <BaseDialog
      v-model="state.dialog"
      :title="newMeal.existing ? $t('meal-plan.update-this-meal-plan') : $t('meal-plan.create-a-new-meal-plan')"
      :submit-text="newMeal.existing ? $t('general.update') : $t('general.create')"
      color="primary"
      :icon="$globals.icons.foods"
      :submit-disabled="isCreateDisabled"
      :loading="dialog.loading"
      keep-open
      can-submit
      @submit="saveMeal"
      @close="resetDialog()"
    >
      <v-card-text>
        <v-alert v-if="dialog.error" type="error" variant="tonal" class="mb-4" role="alert">
          {{ mutationError?.message || $t('meal-plan.save-failed') }}
          <span v-if="mutationError?.mealIds.length">
            {{ $t('meal-plan.linked-meal-ids', { ids: mutationError.mealIds.join(', ') }) }}
          </span>
        </v-alert>
        <v-menu
          v-model="state.pickerMenu!"
          :close-on-content-click="false"
          :transition="false"
          offset-y
          max-width="290px"
          min-width="auto"
        >
          <template #activator="{ props }">
            <v-text-field
              :model-value="$d(newMeal.date)"
              :label="$t('general.date')"
              persistent-hint
              :prepend-icon="$globals.icons.calendar"
              v-bind="props"
              readonly
            />
          </template>
          <v-date-picker
            v-model="newMeal.date"
            hide-header
            :first-day-of-week="firstDayOfWeek"
            :local="$i18n.locale"
            @update:model-value="state.pickerMenu = false"
          />
        </v-menu>
        <v-card-text>
          <v-select
            v-model="newMeal.entryType"
            :return-object="false"
            :items="planTypeOptions"
            :label="$t('recipe.entry-type')"
            item-title="text"
            item-value="value"
          />
          <v-switch v-model="leftoverMode" :label="$t('meal-plan.use-leftovers')" />
          <template v-if="leftoverMode">
            <v-select
              v-model="newMeal.leftoverSourceId"
              :items="leftoverSources"
              :loading="sourcesLoading"
              :label="$t('meal-plan.leftover-source')"
              :no-data-text="$t('meal-plan.no-leftovers')"
              :item-title="sourceLabel"
              item-value="id"
              @update:model-value="selectSource"
            />
            <div v-if="sourcePages > 1" class="d-flex align-center justify-space-between mb-3">
              <v-btn
                icon
                size="44"
                variant="text"
                :disabled="sourcePage <= 1 || sourcesLoading"
                :aria-label="$t('general.back')"
                @click="loadSources(sourcePage - 1)"
              >
                <v-icon>{{ $globals.icons.chevronLeft }}</v-icon>
              </v-btn>
              <span>{{ sourcePage }} / {{ sourcePages }}</span>
              <v-btn
                icon
                size="44"
                variant="text"
                :disabled="sourcePage >= sourcePages || sourcesLoading"
                :aria-label="$t('general.next')"
                @click="loadSources(sourcePage + 1)"
              >
                <v-icon>{{ $globals.icons.chevronRight }}</v-icon>
              </v-btn>
            </div>
            <p v-if="selectedSource" class="text-body-2 mb-3">
              {{ $t('meal-plan.portions-allocatable', { count: selectedSource.allocatablePortions }) }}
            </p>
            <v-text-field
              v-model.number="newMeal.eatenPortions"
              type="number"
              min="1"
              step="1"
              :label="$t('meal-plan.portions-to-use')"
              :rules="[reservationRule]"
            />
          </template>
          <v-autocomplete
            v-else-if="!dialog.note"
            v-model="newMeal.recipeId"
            v-model:search="search.query.value"
            :label="$t('meal-plan.meal-recipe')"
            :items="search.data.value"
            :loading="search.loading.value"
            cache-items
            item-title="name"
            item-value="id"
            :return-object="false"
            :rules="[requiredRule]"
          />
          <template v-else-if="!leftoverMode">
            <v-text-field v-model="newMeal.title" :rules="[requiredRule]" :label="$t('meal-plan.meal-title')" />
            <v-textarea v-model="newMeal.text" rows="2" :label="$t('meal-plan.meal-note')" />
          </template>
          <template v-if="!leftoverMode">
            <v-switch v-model="trackPortions" :label="$t('meal-plan.track-portions')" />
            <template v-if="trackPortions">
              <v-text-field
                v-model.number="newMeal.preparedPortions"
                type="number"
                min="1"
                step="1"
                :label="$t('meal-plan.prepared-portions')"
                :rules="[preparedRule]"
              />
              <v-text-field
                v-model.number="newMeal.eatenPortions"
                type="number"
                min="0"
                step="1"
                :label="$t('meal-plan.eaten-portions')"
                :rules="[eatenRule]"
              />
              <p v-if="validOrdinaryPortions" class="text-body-2" aria-live="polite">
                {{ $t('meal-plan.expected-leftovers-count', { count: newMeal.preparedPortions! - newMeal.eatenPortions! }) }}
              </p>
            </template>
          </template>
        </v-card-text>
        <v-card-actions v-if="!leftoverMode" class="my-0 py-0">
          <v-switch v-model="dialog.note" class="mt-n3" :label="$t('meal-plan.note-only')" />
        </v-card-actions>
      </v-card-text>
    </BaseDialog>
    <div class="planner-editor-actions">
      <v-btn color="primary" min-height="44" @click="openDialog(mealplans[0]?.date || new Date())">
        <v-icon start>
          {{ $globals.icons.createAlt }}
        </v-icon>
        {{ $t('meal-plan.add-meal') }}
      </v-btn>
    </div>
    <div class="planner-edit-grid">
      <section
        v-for="(plan, index) in mealplans"
        :key="index"
        class="planner-edit-day"
        :class="{ 'planner-edit-day--today': isToday(plan.date) }"
      >
        <header class="planner-edit-day-heading">
          <h2>
            <time :datetime="format(plan.date, 'yyyy-MM-dd')" :aria-current="isToday(plan.date) ? 'date' : undefined">
              <span class="planner-day-number">{{ $d(plan.date, { day: "numeric" }) }}</span>
              <span class="planner-day-date">
                <span>{{ $d(plan.date, { weekday: "long" }) }}</span>
                <span class="planner-day-month">{{ $d(plan.date, { month: "long", year: "numeric" }) }}</span>
              </span>
            </time>
          </h2>
          <span v-if="mealplansByDate[plan.date.toString()]?.length" class="planner-day-count">
            {{ mealplansByDate[plan.date.toString()].length }}
          </span>
        </header>
        <VueDraggable
          v-model="mealplansByDate[plan.date.toString()]"
          tag="div"
          handle=".handle"
          :delay="250"
          :delay-on-touch-only="true"
          group="meals"
          :data-index="index"
          :data-box="plan.date"
          class="planner-drop-zone"
          @end="onMoveCallback"
        >
          <v-card
            v-for="mealplan in mealplansByDate[plan.date.toString()]"
            :key="mealplan.id"
            class="planner-meal-entry"
          >
            <button type="button" class="planner-meal-open" @click="editMeal(mealplan)">
              <RecipeCardImage
                v-if="mealplan.recipe"
                :recipe-id="mealplan.recipe.id!"
                small
                :height="160"
                :slug="mealplan.recipe.slug"
              />
              <div class="planner-meal-copy">
                <h3>
                  {{ mealplan.recipe ? mealplan.recipe.name : mealplan.title }}
                </h3>
                <p v-if="mealplan.recipe?.description || mealplan.text">
                  {{ mealplan.recipe ? mealplan.recipe.description : mealplan.text }}
                </p>
              </div>
            </button>
            <div v-if="mealplan.expectedLeftovers != null" class="planner-portion-summary">
              {{ $t('meal-plan.expected-leftovers-count', { count: mealplan.expectedLeftovers }) }}
              <br>{{ $t('meal-plan.portions-unallocated', { count: mealplan.availableLeftovers }) }}
              <br>{{ $t('meal-plan.portions-reserved', { count: mealplan.reservedLeftovers }) }}
            </div>
            <div v-if="mealplan.leftoverSource" class="planner-portion-summary">
              {{ $t('meal-plan.leftover-meal-count', { count: mealplan.eatenPortions }) }}
              <br>
              <NuxtLink :to="{ path: '/household/mealplan/planner/edit', query: { date: mealplan.leftoverSource.date } }">
                {{ $t('meal-plan.source-meal-date', { date: mealplan.leftoverSource.date }) }}
              </NuxtLink>
            </div>
            <v-btn
              v-if="mealplan.expectedLeftovers != null"
              variant="text"
              color="primary"
              min-height="44"
              class="planner-schedule-button"
              :disabled="!mealplan.availableLeftovers"
              @click="scheduleLeftovers(mealplan)"
            >
              <v-icon start>
                {{ $globals.icons.calendar }}
              </v-icon>
              {{ $t('meal-plan.schedule-leftovers') }}
            </v-btn>
            <v-divider class="mx-2" />
            <div class="planner-meal-tools">
              <v-btn
                size="44"
                icon
                variant="text"
                class="handle"
                :aria-label="$t('general.sort')"
                :title="$t('general.sort')"
              >
                <v-icon>
                  {{ $globals.icons.arrowUpDown }}
                </v-icon>
              </v-btn>
              <v-menu offset-y :transition="false">
                <template #activator="{ props }">
                  <v-btn
                    v-bind="props"
                    variant="text"
                    min-height="44"
                    color="primary"
                    @click.prevent
                  >
                    <v-icon start>
                      {{ $globals.icons.tags }}
                    </v-icon>
                    {{ getEntryTypeText(mealplan.entryType!) }}
                  </v-btn>
                </template>
                <v-list>
                  <v-list-item
                    v-for="mealType in planTypeOptions"
                    :key="mealType.value"
                    @click="actions.setType(mealplan, mealType.value)"
                  >
                    <v-list-item-title> {{ mealType.text }} </v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
              <v-btn
                class="ml-auto"
                size="44"
                variant="text"
                icon
                :aria-label="$t('general.delete')"
                :title="$t('general.delete')"
                @click="actions.deleteOne(mealplan.id)"
              >
                <v-icon>{{ $globals.icons.delete }}</v-icon>
              </v-btn>
            </div>
          </v-card>
        </VueDraggable>
        <!-- Day Column Actions -->
        <p v-if="!mealplansByDate[plan.date.toString()]?.length" class="planner-edit-empty">
          {{ $t('meal-plan.no-meal-plan-defined-yet') }}
        </p>
        <div class="planner-day-actions">
          <v-btn variant="tonal" color="primary" min-height="44" @click="openDialog(plan.date)">
            <v-icon start>
              {{ $globals.icons.createAlt }}
            </v-icon>
            {{ $t('general.add') }}
          </v-btn>
          <v-menu :transition="false">
            <template #activator="{ props }">
              <v-btn
                v-bind="props"
                icon
                size="44"
                variant="text"
                :aria-label="$t('meal-plan.random-meal')"
                :title="$t('meal-plan.random-meal')"
              >
                <v-icon>{{ $globals.icons.diceMultiple }}</v-icon>
              </v-btn>
            </template>
            <v-list>
              <v-list-item v-for="mealType in planTypeOptions" :key="mealType.value" :title="mealType.text" @click="randomMeal(plan.date, mealType.value)" />
            </v-list>
          </v-menu>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts">
import { addDays, format, isToday, parseISO } from "date-fns";
import type { SortableEvent } from "sortablejs";
import { VueDraggable } from "vue-draggable-plus";
import type { MealsByDate } from "./types";
import type { useMealplans } from "~/composables/use-group-mealplan";
import { usePlanTypeOptions, getEntryTypeText } from "~/composables/use-group-mealplan";
import RecipeCardImage from "~/components/Domain/Recipe/RecipeCardImage.vue";
import type { LeftoverPlanEntry, PlanEntryType, ReadPlanEntry } from "~/lib/api/types/meal-plan";
import { useUserApi } from "~/composables/api";
import { useHouseholdSelf } from "~/composables/use-households";
import { useRecipeSearch } from "~/composables/recipes/use-recipe-search";

export default defineNuxtComponent({
  components: {
    VueDraggable,
    RecipeCardImage,
  },
  props: {
    mealplans: {
      type: Array as () => MealsByDate[],
      required: true,
    },
    actions: {
      type: Object as () => ReturnType<typeof useMealplans>["actions"],
      required: true,
    },
    mutationError: {
      type: Object as () => { message: string; mealIds: number[] } | null,
      default: null,
    },
    allocationVersion: { type: Number, default: 0 },
  },
  setup(props) {
    const api = useUserApi();
    const $auth = useMealieAuth();
    const { household } = useHouseholdSelf();
    const i18n = useI18n();
    const requiredRule = (value: any) => !!value || "Required.";

    const state = ref({
      dialog: false,
      pickerMenu: null as null | boolean,
    });

    const firstDayOfWeek = computed(() => {
      return household.value?.preferences?.firstDayOfWeek || 0;
    });

    // Local mutable meals object
    const mealplansByDate = reactive<{ [date: string]: ReadPlanEntry[] }>({});
    watch(
      () => props.mealplans,
      (plans) => {
        for (const plan of plans) {
          mealplansByDate[plan.date.toString()] = plan.meals ? [...plan.meals] : [];
        }
        // Remove any dates that no longer exist
        Object.keys(mealplansByDate).forEach((date) => {
          if (!plans.find(p => p.date.toString() === date)) {
            mealplansByDate[date] = [];
          }
        });
      },
      { immediate: true, deep: true },
    );

    async function onMoveCallback(evt: SortableEvent) {
      const supportedEvents = ["drop", "touchend"];

      // Adapted From https://github.com/SortableJS/Vue.Draggable/issues/1029
      const ogEvent: DragEvent = (evt as any).originalEvent;

      if (ogEvent && ogEvent.type in supportedEvents) {
        // The drop was cancelled, unsure if anything needs to be done?
        console.log("Cancel Move Event");
      }
      else {
        // A Meal was moved, set the new date value and make an update request and refresh the meals
        const fromMealsByIndex = parseInt(evt.from.getAttribute("data-index") ?? "");
        const toMealsByIndex = parseInt(evt.to.getAttribute("data-index") ?? "");

        if (!isNaN(fromMealsByIndex) && !isNaN(toMealsByIndex)) {
          const destDate = props.mealplans[toMealsByIndex].date;
          const mealData = mealplansByDate[destDate.toString()][evt.newIndex as number];

          await props.actions.updateOne({ ...mealData, date: format(destDate, "yyyy-MM-dd") });
        }
      }
    }

    // =====================================================
    // New Meal Dialog

    const dialog = reactive({
      loading: false,
      error: false,
      note: false,
    });

    watch(() => dialog.note, (note) => {
      if (note && !leftoverMode.value) {
        newMeal.recipeId = undefined;
      }
    });

    const newMeal = reactive({
      date: new Date(Date.now() - new Date().getTimezoneOffset() * 60000),
      title: "",
      text: "",
      recipeId: undefined as string | undefined,
      entryType: "dinner" as PlanEntryType,
      existing: false,
      id: 0,
      groupId: "",
      userId: $auth.user.value?.id || "",
      preparedPortions: null as number | null,
      eatenPortions: null as number | null,
      leftoverSourceId: null as number | null,
    });
    const trackPortions = ref(false);
    const leftoverMode = ref(false);
    const leftoverSources = ref<LeftoverPlanEntry[]>([]);
    const selectedSource = ref<LeftoverPlanEntry | null>(null);
    const sourcesLoading = ref(false);
    const sourcePage = ref(1);
    const sourcePages = ref(0);
    let sourceRequest = 0;

    const whole = (value: unknown, minimum: number): value is number => typeof value === "number" && Number.isInteger(value) && value >= minimum && value <= 2147483647;
    const validOrdinaryPortions = computed(() => whole(newMeal.preparedPortions, 1) && whole(newMeal.eatenPortions, 0) && newMeal.eatenPortions <= newMeal.preparedPortions);
    const preparedRule = (value: unknown) => whole(value, 1) || i18n.t("meal-plan.invalid-portions");
    const eatenRule = () => validOrdinaryPortions.value || i18n.t("meal-plan.invalid-portions");
    const reservationRule = () => (whole(newMeal.eatenPortions, 1) && newMeal.eatenPortions <= (selectedSource.value?.allocatablePortions ?? 0)) || i18n.t("meal-plan.invalid-portions");
    const sourceLabel = (source: LeftoverPlanEntry) => source?.date
      ? `${source.recipe?.name || source.title} - ${source.date}`
      : newMeal.title || i18n.t("meal-plan.leftover-source");

    async function loadSources(page = 1) {
      if (!state.value.dialog || !leftoverMode.value) return;
      const request = ++sourceRequest;
      sourcesLoading.value = true;
      try {
        const { data } = await props.actions.getLeftovers(newMealDateString.value, newMeal.existing ? newMeal.id : undefined, page);
        if (request !== sourceRequest) return;
        if (!data) dialog.error = true;
        leftoverSources.value = data?.items || [];
        sourcePage.value = data?.page || 1;
        sourcePages.value = data?.total_pages || 0;
        if (newMeal.leftoverSourceId != null) {
          selectedSource.value = leftoverSources.value.find(source => source.id === newMeal.leftoverSourceId) || null;
          if (!selectedSource.value && data) {
            const selected = await props.actions.getLeftovers(
              newMealDateString.value, newMeal.existing ? newMeal.id : undefined, 1, 20, newMeal.leftoverSourceId,
            );
            if (request !== sourceRequest) return;
            selectedSource.value = selected.data?.items[0] || null;
            if (selectedSource.value) leftoverSources.value.push(selectedSource.value);
          }
        }
      }
      catch {
        if (request === sourceRequest) dialog.error = true;
      }
      finally {
        if (request === sourceRequest) sourcesLoading.value = false;
      }
    }

    function selectSource(sourceId: number | null) {
      selectedSource.value = leftoverSources.value.find(source => source.id === sourceId) || null;
      if (selectedSource.value) {
        newMeal.recipeId = selectedSource.value.recipeId || undefined;
        newMeal.title = selectedSource.value.title || "";
        newMeal.text = selectedSource.value.text || "";
      }
    }

    watch([() => state.value.dialog, leftoverMode, () => newMeal.date, () => props.allocationVersion], () => {
      void loadSources();
    });
    watch(leftoverMode, (enabled) => {
      newMeal.preparedPortions = null;
      newMeal.eatenPortions = null;
      if (!enabled) {
        newMeal.leftoverSourceId = null;
        selectedSource.value = null;
        trackPortions.value = false;
        dialog.note = !newMeal.recipeId;
      }
    }, { flush: "sync" });

    const newMealDateString = computed(() => {
      return format(newMeal.date, "yyyy-MM-dd");
    });

    const isCreateDisabled = computed(() => {
      if (dialog.loading || sourcesLoading.value) return true;
      if (leftoverMode.value) {
        return !selectedSource.value || reservationRule() !== true || newMealDateString.value <= selectedSource.value.date;
      }
      if (trackPortions.value && !validOrdinaryPortions.value) return true;
      if (dialog.note) {
        return !newMeal.title.trim();
      }
      return !newMeal.recipeId;
    });

    function openDialog(date: Date) {
      newMeal.date = date;
      state.value.dialog = true;
    }

    function editMeal(mealplan: ReadPlanEntry) {
      const { date, title, text, entryType, recipeId, id, groupId, userId } = mealplan;
      if (!entryType) return;

      const [year, month, day] = date.split("-").map(Number);
      newMeal.date = new Date(year, month - 1, day);
      newMeal.title = title || "";
      newMeal.text = text || "";
      newMeal.recipeId = recipeId || undefined;
      newMeal.entryType = entryType;
      newMeal.existing = true;
      newMeal.id = id;
      newMeal.groupId = groupId;
      newMeal.userId = userId || $auth.user.value?.id || "";
      leftoverMode.value = !!mealplan.leftoverSourceId;
      trackPortions.value = mealplan.preparedPortions != null;
      newMeal.preparedPortions = mealplan.preparedPortions ?? null;
      newMeal.eatenPortions = mealplan.eatenPortions ?? null;
      newMeal.leftoverSourceId = mealplan.leftoverSourceId ?? null;
      dialog.error = false;

      state.value.dialog = true;
      dialog.note = !recipeId;
    }

    function resetDialog() {
      sourceRequest += 1;
      leftoverMode.value = false;
      trackPortions.value = false;
      selectedSource.value = null;
      leftoverSources.value = [];
      sourcesLoading.value = false;
      dialog.error = false;
      dialog.note = false;
      newMeal.date = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
      newMeal.title = "";
      newMeal.text = "";
      newMeal.entryType = "dinner";
      newMeal.recipeId = undefined;
      newMeal.existing = false;
      newMeal.preparedPortions = null;
      newMeal.eatenPortions = null;
      newMeal.leftoverSourceId = null;
    }

    async function saveMeal() {
      if (isCreateDisabled.value) return;
      dialog.loading = true;
      dialog.error = false;
      try {
        const payload = {
          ...newMeal,
          date: newMealDateString.value,
          preparedPortions: !leftoverMode.value && trackPortions.value ? newMeal.preparedPortions : null,
          eatenPortions: leftoverMode.value || trackPortions.value ? newMeal.eatenPortions : null,
          leftoverSourceId: leftoverMode.value ? newMeal.leftoverSourceId : null,
        };
        const saved = newMeal.existing ? await props.actions.updateOne(payload) : await props.actions.createOne(payload);
        if (saved) {
          state.value.dialog = false;
          resetDialog();
        }
        else {
          dialog.error = true;
          await loadSources();
        }
      }
      finally {
        dialog.loading = false;
      }
    }

    function scheduleLeftovers(source: ReadPlanEntry) {
      resetDialog();
      leftoverMode.value = true;
      newMeal.date = addDays(parseISO(source.date), 1);
      newMeal.entryType = "lunch";
      newMeal.leftoverSourceId = source.id;
      newMeal.eatenPortions = source.availableLeftovers ?? null;
      newMeal.recipeId = source.recipeId || undefined;
      newMeal.title = source.title || "";
      newMeal.text = source.text || "";
      state.value.dialog = true;
    }

    async function randomMeal(date: Date, type: PlanEntryType) {
      const { data } = await api.mealplans.setRandom({
        date: format(date, "yyyy-MM-dd"),
        entryType: type,
      });

      if (data) {
        props.actions.refreshAll();
      }
    }

    // =====================================================
    // Search

    const search = useRecipeSearch(api);
    const planTypeOptions = usePlanTypeOptions();

    onMounted(async () => {
      await search.trigger();
    });

    return {
      state,
      format,
      isToday,
      onMoveCallback,
      planTypeOptions,
      getEntryTypeText,
      requiredRule,
      isCreateDisabled,

      // Dialog
      dialog,
      newMeal,
      newMealDateString,
      openDialog,
      editMeal,
      resetDialog,
      saveMeal,
      scheduleLeftovers,
      leftoverMode,
      trackPortions,
      leftoverSources,
      selectedSource,
      sourcesLoading,
      sourcePage,
      sourcePages,
      loadSources,
      selectSource,
      sourceLabel,
      validOrdinaryPortions,
      preparedRule,
      eatenRule,
      reservationRule,
      randomMeal,

      // Search
      search,
      firstDayOfWeek,
      mealplansByDate,
    };
  },
});
</script>

<style scoped>
.planner-editor-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.planner-editor-actions .v-btn {
  min-width: 128px;
}

.planner-portion-summary {
  padding: 0 16px 12px;
  font-size: 0.8125rem;
  overflow-wrap: anywhere;
}

.planner-schedule-button {
  max-width: 100%;
  height: auto;
  white-space: normal;
}

.planner-edit-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 32px 24px;
  align-items: start;
}

.planner-edit-day {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.planner-edit-day-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
  gap: 8px;
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--mealie-border);
}

.planner-edit-day-heading h2 {
  min-width: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.planner-edit-day-heading time {
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

.planner-edit-day--today .planner-day-number {
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

.planner-day-count {
  color: var(--mealie-muted);
  font-size: 0.8125rem;
  font-variant-numeric: tabular-nums;
}

.planner-drop-zone {
  min-height: 12px;
}

.planner-meal-entry {
  margin-bottom: 12px;
  overflow: hidden;
}

.planner-meal-open {
  display: block;
  width: 100%;
  text-align: start;
  color: inherit;
}

.planner-meal-open:focus-visible {
  outline-offset: -3px;
}

.planner-meal-copy {
  padding: 16px;
}

.planner-meal-copy h3 {
  overflow-wrap: anywhere;
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.5;
}

.planner-meal-copy p {
  display: -webkit-box;
  margin-top: 8px;
  overflow: hidden;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  color: var(--mealie-muted);
  font-size: 0.8125rem;
  line-height: 1.6;
}

.planner-meal-tools {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
}

.planner-meal-tools :deep(.v-btn:not(.v-btn--icon)) {
  min-width: 0;
  max-width: calc(100% - 96px);
  padding-inline: 8px;
}

.planner-meal-tools :deep(.v-btn__content),
.planner-schedule-button :deep(.v-btn__content) {
  white-space: normal;
  overflow-wrap: anywhere;
}

.planner-day-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-background), 0.1);
}

.planner-edit-empty {
  padding-block: 8px;
  margin-bottom: 16px;
  font-size: 0.8125rem;
  color: var(--mealie-muted);
}

.planner-editor :deep(.v-btn:not(.v-btn--icon)) {
  border-radius: 6px;
  letter-spacing: 0;
}

@media (max-width: 1199px) {
  .planner-edit-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 699px) {
  .planner-edit-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 28px;
  }

  .planner-editor-actions .v-btn {
    width: 100%;
  }
}
</style>
