<template>
  <v-img
    class="recipe-image"
    :height="height"
    :cover="!fallBackImage"
    :src="fallBackImage ? '/icon.png' : getImage(recipeId)"
    :alt="fallBackImage ? '' : alt"
    :class="{ 'recipe-image--fallback': fallBackImage }"
    @click="$emit('click')"
    @error="fallBackImage = true"
  >
    <slot />
  </v-img>
</template>

<script setup lang="ts">
import { useStaticRoutes } from "~/composables/api";

interface Props {
  tiny?: boolean | null;
  small?: boolean | null;
  large?: boolean | null;
  iconSize?: number | string;
  slug?: string | null;
  recipeId: string;
  imageVersion?: string | null;
  height?: number | string;
  alt?: string;
}
const props = withDefaults(defineProps<Props>(), {
  tiny: null,
  small: null,
  large: null,
  iconSize: 100,
  slug: null,
  imageVersion: null,
  height: "100%",
  alt: "",
});

defineEmits<{
  click: [];
}>();

const { recipeImage, recipeSmallImage, recipeTinyImage } = useStaticRoutes();

const fallBackImage = ref(false);
const imageSize = computed(() => {
  if (props.tiny) return "tiny";
  if (props.small) return "small";
  if (props.large) return "large";
  return "large";
});

watch(
  () => [props.recipeId, props.imageVersion],
  () => {
    fallBackImage.value = false;
  },
);

function getImage(recipeId: string) {
  switch (imageSize.value) {
    case "tiny":
      return recipeTinyImage(recipeId, props.imageVersion);
    case "small":
      return recipeSmallImage(recipeId, props.imageVersion);
    case "large":
      return recipeImage(recipeId, props.imageVersion);
  }
}
</script>

<style scoped>
.recipe-image {
  width: 100%;
  background: rgb(var(--v-theme-surface-variant));
}

.recipe-image--fallback :deep(.v-img__img) {
  padding: 20%;
  opacity: 0.55;
}
</style>
