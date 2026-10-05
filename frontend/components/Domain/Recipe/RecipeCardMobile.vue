<template>
  <v-card
    class="recipe-row"
    :class="{ 'recipe-row--vertical': vertical, 'recipe-row--flat': isFlat, 'recipe-row--quiet': disableHighlight }"
    elevation="0"
    :style="{ '--recipe-row-height': `${height}px` }"
  >
    <div class="recipe-row__body">
      <div class="recipe-row__media">
        <slot name="avatar">
          <RecipeCardImage
            :slug="slug"
            :recipe-id="recipeId"
            :image-version="image"
            :alt="name"
            small
            height="100%"
          />
        </slot>
      </div>
      <div class="recipe-row__content">
        <h3 class="recipe-row__title">
          <component
            :is="selectionMode ? 'button' : NuxtLink"
            :to="selectionMode ? undefined : recipeRoute || undefined"
            :type="selectionMode ? 'button' : undefined"
            class="recipe-row__link arrow-nav"
            :aria-label="name"
            @click="selectRecipe"
          >
            {{ name }}
          </component>
        </h3>
        <div v-if="description" class="recipe-row__description">
          <SafeMarkdown :source="description" />
        </div>
      </div>
      <v-icon class="recipe-row__arrow" color="primary" aria-hidden="true">
        {{ selectionMode ? $globals.icons.check : $globals.icons.chevronRight }}
      </v-icon>
    </div>
    <slot name="actions">
      <RecipeCardActions
        v-if="showRecipeContent && !hideActions && !selectionMode"
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
import { NuxtLink } from "#components";
import RecipeCardActions from "./RecipeCardActions.vue";
import RecipeCardImage from "./RecipeCardImage.vue";

interface Props {
  name: string;
  slug: string;
  description: string;
  rating?: number;
  image?: string;
  tags?: Array<any>;
  recipeId: string;
  vertical?: boolean;
  isFlat?: boolean;
  height?: number;
  disableHighlight?: boolean;
  selectable?: boolean;
  hideActions?: boolean;
  comparisonEnabled?: boolean;
  groupId?: string;
}
const props = withDefaults(defineProps<Props>(), {
  rating: 0,
  image: "abc123",
  tags: () => [],
  vertical: false,
  isFlat: false,
  height: 150,
  disableHighlight: false,
  selectable: false,
  hideActions: false,
  comparisonEnabled: false,
  groupId: undefined,
});

const emit = defineEmits<{
  selected: [];
  delete: [slug: string];
}>();

const attrs = useAttrs();
const $auth = useMealieAuth();

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug || $auth.user.value?.groupSlug || "");
const showRecipeContent = computed(() => props.recipeId && props.slug);
const recipeRoute = computed<string>(() => {
  return showRecipeContent.value ? `/g/${groupSlug.value}/r/${props.slug}` : "";
});
const selectionMode = computed(() => props.selectable || !!attrs.selected);

function selectRecipe() {
  if (typeof attrs.selected === "function") {
    attrs.selected();
  }
  emit("selected");
}
</script>

<style scoped>
.recipe-row {
  border-radius: 8px;
  border: 1px solid var(--mealie-border);
  background: rgb(var(--v-theme-surface));
}

.recipe-row__body {
  display: flex;
  align-items: center;
  position: relative;
  width: 100%;
  min-height: var(--recipe-row-height);
  padding: 0;
  color: rgb(var(--v-theme-on-surface));
  background: transparent;
  border: 0;
  text-align: start;
  text-decoration: none;
  cursor: pointer;
  transition:
    background-color var(--mealie-motion-fast) var(--mealie-ease-out),
    transform var(--mealie-motion-fast) var(--mealie-ease-out);
}

.recipe-row__link {
  color: inherit;
  padding: 0;
  background: transparent;
  border: 0;
  text-decoration: none;
  text-align: start;
  font: inherit;
  cursor: pointer;
}

.recipe-row__link::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 8px;
}

.recipe-row__link:focus-visible {
  outline: none;
}

.recipe-row__link:focus-visible::after {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -3px;
  border-radius: 8px;
}

.recipe-row__media {
  width: 112px;
  height: var(--recipe-row-height);
  flex-shrink: 0;
  overflow: hidden;
}

.recipe-row__content {
  flex: 1;
  min-width: 0;
  padding: 16px;
}

.recipe-row .recipe-row__title {
  font-family: var(--mealie-display-font) !important;
  font-size: 1rem;
  line-height: 1.5;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.recipe-row__description {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.recipe-row__description {
  margin-top: 6px;
  color: var(--mealie-muted);
  font-size: 0.8125rem;
  line-height: 1.6;
}

.recipe-row__description :deep(p) {
  margin: 0;
}

.recipe-row__description :deep(a) {
  position: relative;
  z-index: 1;
}

.recipe-row__arrow {
  margin-inline-end: 16px;
}

.recipe-row--flat {
  background: transparent;
}

.recipe-row--vertical .recipe-row__body {
  flex-direction: column;
  align-items: stretch;
}

.recipe-row--vertical .recipe-row__media {
  width: 100%;
  height: auto;
  aspect-ratio: 4 / 3;
}

.recipe-row--vertical .recipe-row__arrow {
  display: none;
}

@media (hover: hover) {
  .recipe-row:not(.recipe-row--quiet) .recipe-row__body:hover {
    background: rgba(var(--v-theme-primary), 0.06);
  }
}

@media (prefers-reduced-motion: no-preference) {
  .recipe-row__body:has(.recipe-row__link:active) {
    transform: scale(0.98);
  }
}

@media (max-width: 599px) {
  .recipe-row__media {
    width: 88px;
  }

  .recipe-row__content {
    padding: 12px;
  }
}
</style>
