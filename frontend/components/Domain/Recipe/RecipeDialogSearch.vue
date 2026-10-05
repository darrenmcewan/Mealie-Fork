<template>
  <div>
    <slot v-bind="{ open, close }" />
    <v-dialog
      v-model="dialog"
      max-width="760px"
      transition="recipe-search"
      :aria-label="$t('search.search')"
    >
      <v-card
        ref="searchPanel"
        class="recipe-search"
        :loading="search.loading.value"
        @keydown="onUpDown"
      >
        <div class="recipe-search__header">
          <v-text-field
            ref="searchInput"
            :model-value="search.query.value"
            autofocus
            variant="outlined"
            autocomplete="off"
            color="primary"
            class="recipe-search__field"
            clearable
            hide-details
            :label="$t('search.search')"
            :aria-label="$t('search.search')"
            :prepend-inner-icon="$globals.icons.search"
            @update:model-value="updateQuery"
            @focus="selectedIndex = -1"
          />

          <v-btn
            :icon="$globals.icons.close"
            variant="text"
            :aria-label="$t('general.close')"
            :title="$t('general.close')"
            @click="close"
          />
        </div>
        <div class="recipe-search__status" role="status" aria-live="polite" aria-atomic="true">
          <span>{{ $t('search.results') }}</span>
          <span v-if="!search.loading.value">{{ search.data.value.length }}</span>
          <span v-else>{{ $t('general.loading') }}</span>
        </div>

        <div class="recipe-search__results" :aria-busy="search.loading.value">
          <RecipeCardMobile
            v-for="recipe in search.data.value"
            :key="recipe.id"
            class="mb-2"
            :height="112"
            :name="recipe.name ?? ''"
            :description="recipe.description ?? ''"
            :slug="recipe.slug ?? ''"
            :rating="recipe.rating ?? 0"
            :image="recipe.image"
            :recipe-id="recipe.id ?? ''"
            :selectable="hasSelectionListener"
            hide-actions
            @selected="hasSelectionListener ? handleSelect(recipe) : undefined"
          />
          <div v-if="!search.loading.value && !search.data.value.length" class="recipe-search__empty" role="status">
            <v-icon size="32" color="primary" aria-hidden="true">
              {{ $globals.icons.search }}
            </v-icon>
            <p>{{ $t('search.no-results') }}</p>
            <span v-if="search.query.value" class="recipe-search__query">{{ search.query.value }}</span>
          </div>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import RecipeCardMobile from "./RecipeCardMobile.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { RecipeSummary } from "~/lib/api/types/recipe";
import { useUserApi } from "~/composables/api";
import { useRecipeSearch } from "~/composables/recipes/use-recipe-search";
import { usePublicExploreApi } from "~/composables/api/api-client";

const SELECTED_EVENT = "selected";

// Define emits
const emit = defineEmits<{
  selected: [recipe: RecipeSummary];
}>();

const $auth = useMealieAuth();
const selectedIndex = ref(-1);
const searchInput = ref<{ focus: () => void } | null>(null);
const searchPanel = ref<{ $el: HTMLElement } | null>(null);
const instance = getCurrentInstance();
const attrs = useAttrs();
const hasSelectionListener = computed(() => !!instance?.vnode.props?.onSelected || typeof attrs.selected === "function");

// ===========================================================================
// Dialog State Management
const dialog = ref(false);

// Reset or Grab Recipes on Change
watch(dialog, (val) => {
  if (!val) {
    search.query.value = "";
    selectedIndex.value = -1;
    search.data.value = [];
  }
});

// ===========================================================================
// Event Handlers

function selectRecipe() {
  const recipeCards = searchPanel.value?.$el.querySelectorAll<HTMLElement>(".arrow-nav");
  if (!recipeCards?.length || selectedIndex.value < 0) {
    selectedIndex.value = -1;
    searchInput.value?.focus();
    return;
  }
  selectedIndex.value = Math.min(selectedIndex.value, recipeCards.length - 1);
  recipeCards[selectedIndex.value]?.focus();
}

function onUpDown(e: KeyboardEvent) {
  if (e.key !== "ArrowUp" && e.key !== "ArrowDown") {
    return;
  }
  const recipeCards = searchPanel.value?.$el.querySelectorAll<HTMLElement>(".arrow-nav");
  const activeIndex = Array.from(recipeCards ?? []).findIndex(card => card === document.activeElement);
  if (activeIndex >= 0) {
    selectedIndex.value = activeIndex;
  }
  if (e.key === "ArrowUp") {
    e.preventDefault();
    selectedIndex.value--;
  }
  else if (e.key === "ArrowDown") {
    e.preventDefault();
    selectedIndex.value++;
  }
  else {
    return;
  }
  selectRecipe();
}

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");
watch(route, close);

function open() {
  dialog.value = true;
  search.trigger();
}
function close() {
  dialog.value = false;
}

// ===========================================================================
// Basic Search
const { isOwnGroup } = useLoggedInState();
const api = isOwnGroup.value ? useUserApi() : usePublicExploreApi(groupSlug.value).explore;
const search = useRecipeSearch(api);

function updateQuery(query: string | null) {
  search.query.value = query ?? "";
  selectedIndex.value = -1;
}

// Select Handler
function handleSelect(recipe: RecipeSummary) {
  close();
  if (typeof attrs.selected === "function") {
    attrs.selected(recipe);
  }
  emit(SELECTED_EVENT, recipe);
}

// Expose functions to parent components
defineExpose({
  open,
  close,
});
</script>

<style scoped>
.recipe-search {
  display: flex;
  flex-direction: column;
  max-height: min(720px, 85dvh);
  background: rgb(var(--v-theme-surface));
}

.recipe-search__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 16px 16px;
}

.recipe-search__field {
  min-width: 0;
}

.recipe-search__status {
  display: flex;
  justify-content: space-between;
  padding: 12px 20px;
  border-block: 1px solid var(--mealie-border);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--mealie-muted);
}

.recipe-search__results {
  overflow-y: auto;
  padding: 12px 16px;
}

.recipe-search__empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--mealie-muted);
}

.recipe-search__empty p {
  margin-top: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.recipe-search__query {
  display: block;
  margin-top: 8px;
  overflow-wrap: anywhere;
}
</style>

<style>
.recipe-search-enter-active {
  transition:
    opacity var(--mealie-motion-enter) var(--mealie-ease-out),
    transform var(--mealie-motion-enter) var(--mealie-ease-out);
}

.recipe-search-leave-active {
  transition:
    opacity var(--mealie-motion-fast) var(--mealie-ease-in),
    transform var(--mealie-motion-fast) var(--mealie-ease-in);
}

.recipe-search-enter-from,
.recipe-search-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
