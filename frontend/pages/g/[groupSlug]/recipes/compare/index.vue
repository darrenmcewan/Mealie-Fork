<template>
  <section ref="container" class="comparison-page">
    <header class="comparison-page__header">
      <div>
        <h1>{{ $t('recipe-comparison.title') }}</h1>
        <p role="status" aria-live="polite" aria-atomic="true">
          {{ $t('recipe-comparison.selected-count', { count: $n(selections.length) }) }}
        </p>
      </div>
      <div class="comparison-page__actions">
        <v-btn ref="browseButton" variant="text" :prepend-icon="mdiArrowLeft" :to="`/g/${groupSlug}`">
          {{ $t('recipe-comparison.browse') }}
        </v-btn>
        <v-btn variant="text" :prepend-icon="mdiClose" @click="clearSelection">
          {{ $t('recipe-comparison.clear') }}
        </v-btn>
      </div>
    </header>
    <RecipeComparisonView
      v-if="canCompare"
      :selections="selections"
      :entries="entries"
      :rows="rows"
      :group-slug="groupSlug"
      :retrying="retrying"
      @remove="removeRecipe"
      @retry="retryRecipe"
    />
    <h2 v-else class="comparison-page__empty">
      {{ $t('recipe-comparison.selection-needed') }}
    </h2>
  </section>
</template>

<script setup lang="ts">
import { mdiArrowLeft, mdiClose } from "@mdi/js";
import RecipeComparisonView from "~/components/Domain/Recipe/RecipeComparisonView.vue";
import { useRecipeComparison } from "~/composables/recipes/use-recipe-comparison";

const { selections, entries, rows, canCompare, load, loadAll, remove, clear } = useRecipeComparison();
const route = useRoute();
const i18n = useI18n();
const groupSlug = computed(() => String(route.params.groupSlug || ""));
const container = ref<HTMLElement>();
const browseButton = ref<{ $el: HTMLElement }>();
const retrying = ref<string[]>([]);
useSeoMeta({ title: () => i18n.t("recipe-comparison.title") });

onMounted(() => {
  if (canCompare.value) {
    void loadAll();
  }
});

function recipeControl(attribute: string, id: string) {
  return Array.from(container.value?.querySelectorAll<HTMLElement>(`[${attribute}]`) || [])
    .find(element => element.getAttribute(attribute) === id);
}

async function removeRecipe(id: string) {
  const index = selections.value.findIndex(recipe => recipe.id === id);
  remove(id);
  await nextTick();
  const nextId = selections.value[Math.min(index, selections.value.length - 1)]?.id;
  (nextId ? recipeControl("data-comparison-remove", nextId) : undefined)?.focus();
  if (!canCompare.value) {
    browseButton.value?.$el.focus();
  }
}

async function retryRecipe(id: string) {
  if (entries.value[id]?.status === "loading") {
    return;
  }
  retrying.value = [...retrying.value, id];
  await load(id);
  retrying.value = retrying.value.filter(recipeId => recipeId !== id);
  await nextTick();
  (recipeControl("data-comparison-retry", id) || recipeControl("data-recipe-link", id)
    || recipeControl("data-comparison-remove", id) || browseButton.value?.$el)?.focus();
}

async function clearSelection() {
  clear();
  await nextTick();
  browseButton.value?.$el.focus();
}
</script>

<style scoped>
.comparison-page {
  max-width: 1440px;
  padding: 8px 24px 40px;
  margin-inline: auto;
  color: rgb(var(--v-theme-on-surface));
}

.comparison-page__header,
.comparison-page__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.comparison-page__header {
  justify-content: space-between;
  border-bottom: 1px solid var(--mealie-border);
  padding-bottom: 20px;
}

.comparison-page h1 {
  font-family: var(--mealie-display-font) !important;
  font-size: 2rem;
  font-weight: 500;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.comparison-page__header p {
  color: var(--mealie-muted);
  font-size: 0.875rem;
  margin-top: 6px;
}

.comparison-page__actions :deep(.v-btn) {
  min-height: 44px;
  max-width: 100%;
}

.comparison-page__empty {
  margin-top: 32px;
  font-size: 1.25rem;
  font-weight: 500;
}
</style>
