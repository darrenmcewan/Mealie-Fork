<template>
  <section class="recipe-overview" :class="{ 'recipe-overview--landscape': landscape }">
    <div class="recipe-overview__layout">
      <RecipePageInfoCardImage
        :recipe="recipe"
        class="recipe-overview__image"
      />
      <div class="recipe-overview__content">
        <div class="recipe-overview__heading">
          <h1 class="recipe-overview__title">
            {{ recipe.name }}
          </h1>
          <RecipeRating
            :key="recipe.slug"
            :value="recipe.rating"
            :recipe-id="recipe.id"
            :slug="recipe.slug"
          />
        </div>
        <SafeMarkdown v-if="recipe.description" :source="recipe.description" class="recipe-overview__description" />
        <div class="recipe-overview__metadata">
          <div v-if="recipe.recipeYieldQuantity || recipe.recipeYield || isOwnGroup" class="recipe-overview__yield">
            <RecipeYield
              v-if="recipe.recipeYieldQuantity || recipe.recipeYield"
              :yield-quantity="recipe.recipeYieldQuantity"
              :yield-text="recipe.recipeYield"
              :scale="recipeScale"
              class="recipe-overview__yield-value"
            />
            <RecipeLastMade
              v-if="isOwnGroup"
              :recipe="recipe"
            />
          </div>
          <RecipeTimeCard
            :prep-time="recipe.prepTime"
            :total-time="recipe.totalTime"
            :perform-time="recipe.performTime"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import RecipeRating from "~/components/Domain/Recipe/RecipeRating.vue";
import RecipeLastMade from "~/components/Domain/Recipe/RecipeLastMade.vue";
import RecipeTimeCard from "~/components/Domain/Recipe/RecipeTimeCard.vue";
import RecipeYield from "~/components/Domain/Recipe/RecipeYield.vue";
import RecipePageInfoCardImage from "~/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageInfoCardImage.vue";
import type { Recipe } from "~/lib/api/types/recipe";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";

interface Props {
  recipe: NoUndefinedField<Recipe>;
  recipeScale?: number;
  landscape: boolean;
}

withDefaults(defineProps<Props>(), {
  recipeScale: 1,
});

const { isOwnGroup } = useLoggedInState();
</script>

<style scoped>
.recipe-overview__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: center;
  gap: 32px;
}

.recipe-overview__content {
  min-width: 0;
  padding-block: 20px;
}

.recipe-overview .recipe-overview__title {
  font-family: var(--mealie-display-font) !important;
  font-size: 2rem;
  font-weight: 600;
  line-height: 1.3;
  color: rgb(var(--v-theme-on-surface));
  overflow-wrap: anywhere;
  margin-bottom: 12px;
}

.recipe-overview__description {
  margin-block: 16px 24px;
  color: var(--mealie-muted);
  font-size: 0.9375rem;
  line-height: 1.75;
  overflow-wrap: anywhere;
  max-width: 65ch;
}

.recipe-overview__metadata {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--mealie-border);
}

.recipe-overview__yield {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 24px;
}

.recipe-overview__yield-value {
  margin: 0;
}

.recipe-overview__yield :deep(.text-center) {
  text-align: start !important;
}

.recipe-overview--landscape .recipe-overview__layout {
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}

@media (max-width: 599px) {
  .recipe-overview__layout {
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
  }

  .recipe-overview .recipe-overview__title {
    font-size: 1.625rem;
  }

  .recipe-overview__content {
    padding-block: 0;
  }
}
</style>
