<template>
  <div class="recipe-card-actions">
    <label
      v-if="comparisonEnabled"
      class="recipe-card-actions__compare"
      :title="$t('recipe-comparison.select', { name })"
    >
      <input
        type="checkbox"
        :checked="isCompared"
        :disabled="!recipeId.trim() || !slug.trim()"
        :aria-label="$t('recipe-comparison.select', { name })"
        @click.stop
        @change="toggleComparison"
      >
    </label>
    <RecipeFavoriteBadge
      v-if="isOwnGroup"
      :recipe-id="recipeId"
      :aria-label="isFavorite ? $t('recipe.remove-from-favorites') : $t('recipe.add-to-favorites')"
      :aria-pressed="isFavorite"
      show-always
    />
    <RecipeCardRating :model-value="rating" :recipe-id="recipeId" />
    <v-spacer />
    <RecipeChips
      :truncate="true"
      :items="tags"
      :title="false"
      :limit="2"
      small
      url-prefix="tags"
    />
    <v-menu v-if="isOwnGroup" v-model="menuOpen" :eager="menuLoaded" :transition="false" @update:model-value="menuLoaded ||= $event">
      <template #activator="{ props: activatorProps }">
        <v-btn
          v-bind="activatorProps"
          variant="text"
          color="on-surface"
          :icon="$globals.icons.dotsVertical"
          :aria-label="$t('general.actions') + ': ' + name"
          :title="$t('general.actions')"
        />
      </template>
      <RecipeContextMenuContent
        v-if="menuLoaded"
        :slug="slug"
        :name="name"
        :recipe-id="recipeId"
        :use-items="{
          delete: false,
          edit: false,
          download: true,
          duplicate: false,
          mealplanner: true,
          shoppingList: true,
          print: false,
          printPreferences: false,
          share: true,
          recipeActions: false,
        }"
        @deleted="$emit('delete', $event)"
      />
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import RecipeFavoriteBadge from "./RecipeFavoriteBadge.vue";
import RecipeCardRating from "./RecipeCardRating.vue";
import RecipeChips from "./RecipeChips.vue";
import RecipeContextMenuContent from "./RecipeContextMenu/RecipeContextMenuContent.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useUserSelfRatings } from "~/composables/use-users";
import { useRecipeComparison } from "~/composables/recipes/use-recipe-comparison";

const props = withDefaults(defineProps<{
  recipeId: string;
  slug: string;
  name: string;
  rating?: number;
  tags?: Array<any>;
  comparisonEnabled?: boolean;
  groupId?: string;
}>(), {
  rating: 0,
  tags: () => [],
  comparisonEnabled: false,
  groupId: undefined,
});

defineEmits<{ delete: [slug: string] }>();
const { isOwnGroup } = useLoggedInState();
const { userRatings } = useUserSelfRatings();
const isFavorite = computed(() => userRatings.value.find(rating => rating.recipeId === props.recipeId)?.isFavorite ?? false);
const menuOpen = ref(false);
const menuLoaded = ref(false);
const comparison = props.comparisonEnabled ? useRecipeComparison() : null;
const isCompared = computed(() => comparison?.selections.value.some(item => item.id === props.recipeId) ?? false);

function toggleComparison(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.checked) {
    comparison?.add({ id: props.recipeId, slug: props.slug, name: props.name, groupId: props.groupId });
  }
  else {
    comparison?.remove(props.recipeId);
  }
  input.checked = isCompared.value;
}
</script>

<style scoped>
.recipe-card-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  min-height: 52px;
  padding: 4px 8px;
  border-top: 1px solid var(--mealie-border);
}

.recipe-card-actions :deep(.v-btn) {
  min-width: 44px;
  min-height: 44px;
}

.recipe-card-actions__compare {
  display: grid;
  place-items: center;
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
}

.recipe-card-actions__compare input {
  width: 20px;
  height: 20px;
  accent-color: rgb(var(--v-theme-primary));
  cursor: pointer;
}

.recipe-card-actions__compare input:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 4px;
}

.recipe-card-actions :deep(.v-chip--link) {
  min-height: 44px;
}
</style>
