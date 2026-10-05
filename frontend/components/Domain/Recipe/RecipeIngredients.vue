<template>
  <section v-if="value && value.length > 0" class="recipe-ingredients" :aria-label="$t('recipe.ingredients')" @click.stop>
    <div
      v-if="!isCookMode"
      class="recipe-ingredients__header"
    >
      <h2 class="recipe-ingredients__title">
        {{ $t("recipe.ingredients") }}
      </h2>
      <AppButtonCopy
        btn-class="ml-auto"
        :copy-text="ingredientCopyText"
      />
    </div>
    <div>
      <div
        v-for="(ingredient, index) in value"
        :key="'ingredient' + index"
      >
        <template v-if="!isCookMode">
          <h3
            v-if="showTitleEditor[index]"
            class="recipe-ingredients__group"
          >
            {{ ingredient.title }}
          </h3>
          <v-divider v-if="showTitleEditor[index]" />
        </template>
        <v-checkbox
          v-model="checked[index]"
          hide-details
          color="primary"
          class="recipe-ingredients__item"
          :class="{ 'recipe-ingredients__item--checked': checked[index] }"
          :aria-label="parseIngredientText(ingredient, scale, false)"
        >
          <template #label>
            <RecipeIngredientListItem
              :ingredient="ingredient"
              :scale="scale"
            />
          </template>
        </v-checkbox>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";
import { parseIngredientText } from "~/composables/recipes";
import type { RecipeIngredient } from "~/lib/api/types/recipe";

interface Props {
  value?: RecipeIngredient[];
  scale?: number;
  isCookMode?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  value: () => [],
  scale: 1,
  isCookMode: false,
});

function validateTitle(title?: string | null) {
  return !(title === undefined || title === "" || title === null);
}

const checked = ref(props.value.map(() => false));
const showTitleEditor = computed(() => props.value.map(x => validateTitle(x.title)));

const ingredientCopyText = computed(() => {
  const components: string[] = [];
  props.value.forEach((ingredient) => {
    if (ingredient.title) {
      if (components.length) {
        components.push("");
      }

      components.push(`[${ingredient.title}]`);
    }

    components.push(parseIngredientText(ingredient, props.scale, false));
  });

  return components.join("\n");
});
</script>

<style scoped>
.recipe-ingredients__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.recipe-ingredients .recipe-ingredients__title {
  font-family: var(--mealie-display-font) !important;
  font-size: 1.375rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.recipe-ingredients__group {
  margin-block: 20px 8px;
  font-size: 0.875rem;
  font-weight: 650;
  color: rgb(var(--v-theme-primary));
  overflow-wrap: anywhere;
}

.recipe-ingredients__item {
  padding-block: 4px;
  border-bottom: 1px solid var(--mealie-border);
}

.recipe-ingredients__item :deep(.v-selection-control) {
  min-height: 44px;
  align-items: flex-start;
}

.recipe-ingredients__item :deep(.v-label) {
  opacity: 1;
  flex: 1;
  min-width: 0;
  padding-block: 10px;
  white-space: normal;
}

.recipe-ingredients__item--checked :deep(.ingredient-item) {
  color: var(--mealie-muted);
  text-decoration: line-through;
}

.recipe-ingredients__item :deep(.v-btn) {
  min-width: 44px;
  min-height: 44px;
}
</style>
