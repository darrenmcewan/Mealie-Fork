<template>
  <v-list class="recipe-list" :class="{ 'recipe-list--tile': tile, 'recipe-list--small': small }">
    <v-sheet
      v-for="recipe, index in recipes"
      :key="recipe.id"
      :elevation="0"
      :class="attrs.class.sheet"
      :style="tile ? 'max-width: 100%; width: fit-content;' : 'width: 100%;'"
    >
      <v-list-item
        :to="disabled ? '' : '/g/' + groupSlug + '/r/' + recipe.slug"
        :class="attrs.class.listItem"
        :disabled="disabled"
        class="recipe-list__item"
      >
        <template #prepend>
          <v-avatar rounded="sm" :size="small ? 44 : 56" :class="attrs.class.avatar">
            <RecipeCardImage :recipe-id="recipe.id ?? ''" :image-version="recipe.image" :alt="recipe.name ?? ''" tiny height="100%" />
          </v-avatar>
        </template>
        <div :class="attrs.class.text">
          <v-list-item-title
            :class="listItem && listItemDescriptions[index] ? '' : 'pr-4'"
            :style="attrs.style.text.title"
          >
            {{ recipe.name }}
          </v-list-item-title>
          <v-list-item-subtitle v-if="showDescription">
            {{ recipe.description }}
          </v-list-item-subtitle>
          <v-list-item-subtitle
            v-if="listItem && listItemDescriptions[index]"
            :style="attrs.style.text.subTitle"
          >
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div v-html="listItemDescriptions[index]" />
          </v-list-item-subtitle>
        </div>
        <template #append>
          <slot
            :name="'actions-' + recipe.id"
            :v-bind="{ item: recipe }"
          />
        </template>
      </v-list-item>
    </v-sheet>
  </v-list>
</template>

<script setup lang="ts">
import DOMPurify from "dompurify";
import RecipeCardImage from "./RecipeCardImage.vue";
import { useFraction } from "~/composables/recipes/use-fraction";
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { RecipeSummary } from "~/lib/api/types/recipe";

interface Props {
  recipes: RecipeSummary[];
  listItem?: ShoppingListItemOut;
  small?: boolean;
  tile?: boolean;
  showDescription?: boolean;
  disabled?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  listItem: undefined,
  small: false,
  tile: false,
  showDescription: false,
  disabled: false,
});

const $auth = useMealieAuth();
const { frac } = useFraction();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug || $auth.user?.value?.groupSlug || "");

const attrs = computed(() => {
  return props.small
    ? {
        class: {
          sheet: props.tile ? "mb-1 me-1 justify-center align-center" : "mb-1 justify-center align-center",
          listItem: "px-0",
          avatar: "ma-0",
          icon: "ma-0 pa-0 primary",
          text: "pa-0",
        },
        style: {
          text: {
            title: "font-size: small;",
            subTitle: "font-size: 0.75rem;",
          },
        },
      }
    : {
        class: {
          sheet: props.tile ? "mx-1 justify-center align-center" : "mb-1 justify-center align-center",
          listItem: "px-4",
          avatar: "",
          icon: "pa-1 primary",
          text: "",
        },
        style: {
          text: {
            title: "",
            subTitle: "",
          },
        },
      };
});

function sanitizeHTML(rawHtml: string) {
  return DOMPurify.sanitize(rawHtml, {
    USE_PROFILES: { html: true },
    ALLOWED_TAGS: ["strong", "sup"],
  });
}

const listItemDescriptions = computed<string[]>(() => {
  if (
    props.recipes.length === 1 // we don't need to specify details if there's only one recipe ref
    || !props.listItem?.recipeReferences
    || props.listItem.recipeReferences.length !== props.recipes.length
  ) {
    return props.recipes.map(_ => "");
  }

  const listItemDescriptions: string[] = [];
  for (let i = 0; i < props.recipes.length; i++) {
    const itemRef = props.listItem?.recipeReferences[i];
    const quantity = (itemRef.recipeQuantity || 1) * (itemRef.recipeScale || 1);

    let listItemDescription = "";
    if (props.listItem.unit?.fraction) {
      const fraction = frac(quantity, 10, true);
      if (fraction[0] !== undefined && fraction[0] > 0) {
        listItemDescription += fraction[0];
      }

      if (fraction[1] > 0) {
        listItemDescription += ` <sup>${fraction[1]}</sup>&frasl;<sub>${fraction[2]}</sub>`;
      }
      else {
        listItemDescription = (quantity).toString();
      }
    }
    else {
      listItemDescription = (Math.round(quantity * 100) / 100).toString();
    }

    if (props.listItem.unit) {
      const unitDisplay = props.listItem.unit.useAbbreviation && props.listItem.unit.abbreviation
        ? props.listItem.unit.abbreviation
        : props.listItem.unit.name;

      listItemDescription += ` ${unitDisplay}`;
    }

    if (itemRef.recipeNote) {
      listItemDescription += `, ${itemRef.recipeNote}`;
    }

    listItemDescriptions.push(sanitizeHTML(listItemDescription));
  }

  return listItemDescriptions;
});
</script>

<style scoped>
.recipe-list {
  background: transparent;
  padding: 0;
}

.recipe-list--tile {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recipe-list__item {
  min-height: 72px;
  border-bottom: 1px solid var(--mealie-border);
  transition: background-color var(--mealie-motion-fast) var(--mealie-ease-out);
}

.recipe-list__item :deep(.v-list-item-title) {
  font-weight: 600;
  white-space: normal;
  overflow-wrap: anywhere;
  line-height: 1.5;
}

.recipe-list__item :deep(.v-list-item-subtitle) {
  white-space: normal;
  color: var(--mealie-muted);
  opacity: 1;
}

.recipe-list--small .recipe-list__item {
  min-height: 52px;
}

.recipe-list__item :deep(.v-btn) {
  min-height: 44px;
  min-width: 44px;
}
</style>
