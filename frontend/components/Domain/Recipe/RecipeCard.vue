<template>
  <v-card
    class="recipe-card"
    elevation="0"
    @click.self="$emit('click')"
  >
    <NuxtLink
      class="recipe-card__link"
      :to="recipeRoute || undefined"
      :aria-label="name"
      @click="$emit('click')"
    >
      <div class="recipe-card__media">
        <RecipeCardImage
          :icon-size="imageHeight"
          height="100%"
          :slug="slug"
          :recipe-id="recipeId"
          small
          :alt="name"
          :image-version="image"
        />
      </div>
      <div class="recipe-card__content">
        <h3 class="recipe-card__title">{{ name }}</h3>
      </div>
    </NuxtLink>
    <div v-if="description" class="recipe-card__description">
      <SafeMarkdown :source="description" />
    </div>

    <slot name="actions">
      <RecipeCardActions
        v-if="showRecipeContent"
        :recipe-id="recipeId"
        :slug="slug"
        :name="name"
        :rating="rating"
        :tags="tags"
        :comparison-enabled="comparisonEnabled"
        :group-id="groupId"
        @delete="$emit('delete', slug)"
      />
    </slot>
    <slot />
  </v-card>
</template>

<script setup lang="ts">
import RecipeCardActions from "./RecipeCardActions.vue";
import RecipeCardImage from "./RecipeCardImage.vue";

interface Props {
  name: string;
  slug: string;
  description?: string | null;
  rating?: number;
  ratingColor?: string;
  image?: string;
  tags?: Array<any>;
  recipeId: string;
  imageHeight?: number;
  comparisonEnabled?: boolean;
  groupId?: string;
}
const props = withDefaults(defineProps<Props>(), {
  description: null,
  rating: 0,
  ratingColor: "secondary",
  image: "abc123",
  tags: () => [],
  imageHeight: 200,
  comparisonEnabled: false,
  groupId: undefined,
});

defineEmits<{
  click: [];
  delete: [slug: string];
}>();

const $auth = useMealieAuth();

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug || $auth.user.value?.groupSlug || "");
const showRecipeContent = computed(() => props.recipeId && props.slug);
const recipeRoute = computed<string>(() => {
  return showRecipeContent.value ? `/g/${groupSlug.value}/r/${props.slug}` : "";
});
</script>

<style scoped>
.recipe-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--mealie-border);
  border-radius: 8px;
  background: rgb(var(--v-theme-surface));
  transition:
    transform var(--mealie-motion-standard) var(--mealie-ease-out),
    border-color var(--mealie-motion-standard) var(--mealie-ease-out);
}

.recipe-card__link {
  display: block;
  flex: 1;
  color: rgb(var(--v-theme-on-surface));
  text-decoration: none;
}

.recipe-card__link:focus-visible {
  outline-offset: -3px;
  border-radius: 8px;
}

.recipe-card__media {
  aspect-ratio: 4 / 3;
  overflow: hidden;
}

.recipe-card__content {
  padding: 16px 16px 12px;
}

.recipe-card .recipe-card__title {
  font-family: var(--mealie-display-font) !important;
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.4;
  min-height: 2.8em;
  overflow-wrap: anywhere;
}

.recipe-card__title,
.recipe-card__description {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.recipe-card__description {
  margin: 0 16px 12px;
  font-size: 0.8125rem;
  line-height: 1.6;
  color: var(--mealie-muted);
}

.recipe-card__description :deep(p) {
  margin: 0;
}

@media (hover: hover) and (prefers-reduced-motion: no-preference) {
  .recipe-card:hover {
    transform: translateY(-2px);
    border-color: rgb(var(--v-theme-primary));
  }
}

@media (prefers-reduced-motion: no-preference) {
  .recipe-card__link:active {
    transform: scale(0.98);
  }
}
</style>
