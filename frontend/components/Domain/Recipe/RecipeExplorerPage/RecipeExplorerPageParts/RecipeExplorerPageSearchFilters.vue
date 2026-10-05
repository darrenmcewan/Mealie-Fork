<template>
  <v-defaults-provider :defaults="filterDefaults">
    <SearchFilter
      v-if="categories?.length || selectedCategories.length"
      v-model="selectedCategories"
      v-model:require-all="state.requireAllCategories"
      class="library-filter"
      :class="{ 'library-filter-active': selectedCategories.length }"
      :items="categories"
    >
      <v-icon start>
        {{ $globals.icons.categories }}
      </v-icon>
      {{ $t("category.categories") }}
    </SearchFilter>

    <SearchFilter
      v-if="tags?.length || selectedTags.length"
      v-model="selectedTags"
      v-model:require-all="state.requireAllTags"
      class="library-filter"
      :class="{ 'library-filter-active': selectedTags.length }"
      :items="tags"
    >
      <v-icon start>
        {{ $globals.icons.tags }}
      </v-icon>
      {{ $t("tag.tags") }}
    </SearchFilter>

    <SearchFilter
      v-if="tools?.length || selectedTools.length"
      v-model="selectedTools"
      v-model:require-all="state.requireAllTools"
      class="library-filter"
      :class="{ 'library-filter-active': selectedTools.length }"
      :items="tools"
    >
      <v-icon start>
        {{ $globals.icons.potSteam }}
      </v-icon>
      {{ $t("tool.tools") }}
    </SearchFilter>

    <SearchFilter
      v-if="foods?.length || selectedFoods.length"
      v-model="selectedFoods"
      v-model:require-all="state.requireAllFoods"
      class="library-filter"
      :class="{ 'library-filter-active': selectedFoods.length }"
      :items="foods"
    >
      <v-icon start>
        {{ $globals.icons.foods }}
      </v-icon>
      {{ $t("general.foods") }}
    </SearchFilter>

    <SearchFilter
      v-if="households.length > 1"
      v-model="selectedHouseholds"
      class="library-filter"
      :class="{ 'library-filter-active': selectedHouseholds.length }"
      :items="households"
      radio
    >
      <v-icon start>
        {{ $globals.icons.household }}
      </v-icon>
      {{ $t("household.households") }}
    </SearchFilter>
  </v-defaults-provider>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useRecipeExplorerSearch } from "~/composables/use-recipe-explorer-search";
import {
  useCategoryStore,
  usePublicCategoryStore,
  useFoodStore,
  usePublicFoodStore,
  useHouseholdStore,
  usePublicHouseholdStore,
  useTagStore,
  usePublicTagStore,
  useToolStore,
  usePublicToolStore,
} from "~/composables/store";

const $auth = useMealieAuth();
const route = useRoute();

const filterDefaults = {
  VMenu: { maxWidth: "calc(100vw - 32px)", transition: false },
  VCard: { maxWidth: "calc(100vw - 32px)" },
  VBtn: { variant: "tonal" },
};

const { isOwnGroup } = useLoggedInState();
const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

const {
  state,
  selectedCategories,
  selectedFoods,
  selectedHouseholds,
  selectedTags,
  selectedTools,
} = useRecipeExplorerSearch(groupSlug);

const { store: categories } = isOwnGroup.value ? useCategoryStore() : usePublicCategoryStore(groupSlug.value);
const { store: tags } = isOwnGroup.value ? useTagStore() : usePublicTagStore(groupSlug.value);
const { store: tools } = isOwnGroup.value ? useToolStore() : usePublicToolStore(groupSlug.value);
const { store: foods } = isOwnGroup.value ? useFoodStore() : usePublicFoodStore(groupSlug.value);
const { store: households } = isOwnGroup.value ? useHouseholdStore() : usePublicHouseholdStore(groupSlug.value);
</script>

<style scoped>
.library-filter {
  max-width: 100%;
}

.library-filter :deep(.v-btn) {
  min-height: 44px;
  max-width: 100%;
  padding-inline: 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 6px;
  background-color: rgba(var(--v-theme-on-surface), 0.04) !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  box-shadow: none;
}

.library-filter :deep(.v-btn__content) {
  white-space: normal;
  font-size: 0.875rem;
}

.library-filter-active :deep(.v-btn) {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background-color: rgba(var(--v-theme-primary), 0.1) !important;
  color: rgb(var(--v-theme-primary)) !important;
}

.library-filter :deep(.v-btn:active) {
  transform: scale(0.98);
}
</style>
