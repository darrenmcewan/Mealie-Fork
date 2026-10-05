<template>
  <section ref="toolbar" class="comparison-toolbar" :aria-label="$t('recipe-comparison.title')">
    <div class="comparison-toolbar__heading">
      <span role="status" aria-live="polite" aria-atomic="true">
        {{ $t('recipe-comparison.selected-count', { count: $n(selections.length) }) }}
      </span>
      <div class="comparison-toolbar__actions">
        <v-btn ref="clearButton" variant="text" :prepend-icon="mdiClose" @click="clear">
          {{ $t('recipe-comparison.clear') }}
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :prepend-icon="mdiCompareHorizontal"
          :disabled="!canCompare"
          :to="`/g/${groupSlug}/recipes/compare`"
        >
          {{ $t('recipe-comparison.compare') }}
        </v-btn>
      </div>
    </div>
    <ul v-if="selections.length" class="comparison-toolbar__selections">
      <li v-for="recipe in selections" :key="recipe.id">
        <span>{{ recipe.name }}</span>
        <v-btn
          :icon="mdiClose"
          variant="text"
          size="small"
          :data-remove-id="recipe.id"
          :aria-label="$t('recipe-comparison.remove', { name: recipe.name })"
          :title="$t('recipe-comparison.remove', { name: recipe.name })"
          @click="removeSelection(recipe.id)"
        />
      </li>
    </ul>
    <p v-if="limitReached" class="comparison-toolbar__notice" role="alert">
      {{ $t('recipe-comparison.limit') }}
    </p>
  </section>
</template>

<script setup lang="ts">
import { mdiClose, mdiCompareHorizontal } from "@mdi/js";
import { useRecipeComparison } from "~/composables/recipes/use-recipe-comparison";

const { selections, canCompare, limitReached, remove, clear } = useRecipeComparison();
const route = useRoute();
const groupSlug = computed(() => String(route.params.groupSlug || ""));
const toolbar = ref<HTMLElement>();
const clearButton = ref<{ $el: HTMLElement }>();

async function removeSelection(id: string) {
  const index = selections.value.findIndex(recipe => recipe.id === id);
  remove(id);
  await nextTick();
  const nextId = selections.value[Math.min(index, selections.value.length - 1)]?.id;
  const next = Array.from(toolbar.value?.querySelectorAll<HTMLElement>("[data-remove-id]") || [])
    .find(element => element.dataset.removeId === nextId);
  (next || clearButton.value?.$el)?.focus();
}
</script>

<style scoped>
.comparison-toolbar {
  margin-block: 16px;
  padding-block: 12px;
  border-block: 1px solid var(--mealie-border);
}

.comparison-toolbar__heading,
.comparison-toolbar__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.comparison-toolbar__heading {
  justify-content: space-between;
  font-weight: 600;
  font-size: 0.875rem;
}

.comparison-toolbar :deep(.v-btn) {
  min-height: 44px;
  min-width: 44px;
  max-width: 100%;
}

.comparison-toolbar__selections {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 20px;
  padding: 0;
  margin: 8px 0 0;
  list-style: none;
}

.comparison-toolbar__selections li {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  max-width: 100%;
  font-size: 0.875rem;
}

.comparison-toolbar__selections span {
  overflow-wrap: anywhere;
}

.comparison-toolbar__notice {
  margin: 8px 0 0;
  color: rgb(var(--v-theme-error));
  font-size: 0.875rem;
}
</style>
