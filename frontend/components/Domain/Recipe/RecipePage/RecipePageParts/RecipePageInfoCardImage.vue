<template>
  <div class="recipe-detail-media" :style="{ maxWidth }">
    <v-img
      :key="imageKey"
      :cover="!hideImage"
      width="100%"
      height="100%"
      :src="hideImage ? '/icon.png' : recipeImageUrl"
      :alt="hideImage ? '' : recipe.name"
      :class="{ 'recipe-detail-media--fallback': hideImage }"
      class="d-print-none"
      @error="hideImage = true"
    />
  </div>
</template>

<script setup lang="ts">
import { useStaticRoutes } from "~/composables/api";
import { usePageState } from "~/composables/recipe-page/shared-state";
import type { Recipe } from "~/lib/api/types/recipe";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";

interface Props {
  recipe: NoUndefinedField<Recipe>;
  maxWidth?: string;
}
const props = withDefaults(defineProps<Props>(), {
  maxWidth: undefined,
});

const { recipeImage } = useStaticRoutes();
const { imageKey } = usePageState(props.recipe.slug);
const hideImage = ref(false);

const recipeImageUrl = computed(() => {
  return recipeImage(props.recipe.id, props.recipe.image, imageKey.value);
});

watch(
  () => recipeImageUrl.value,
  () => {
    hideImage.value = false;
  },
);
</script>

<style scoped>
.recipe-detail-media {
  width: 100%;
  aspect-ratio: 4 / 3;
  max-height: 420px;
  border-radius: 8px;
  overflow: hidden;
  background: rgb(var(--v-theme-surface-variant));
}

.recipe-detail-media--fallback :deep(.v-img__img) {
  padding: 20%;
  opacity: 0.55;
}
</style>
