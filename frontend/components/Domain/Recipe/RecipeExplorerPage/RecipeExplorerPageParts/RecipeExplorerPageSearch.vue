<template>
  <div class="search-container">
    <form
      class="search-box"
      role="search"
      :aria-label="$t('general.recipes')"
      @submit.prevent="search"
    >
      <v-text-field
        ref="input"
        v-model="state.search"
        class="library-search-input"
        variant="outlined"
        density="comfortable"
        hide-details
        clearable
        color="primary"
        :label="$t('search.search')"
        :placeholder="$t('search.search-placeholder')"
        :prepend-inner-icon="$globals.icons.search"
        @keyup.enter="hideKeyboard"
      />
      <div class="search-row">
        <RecipeExplorerPageSearchFilters />
        <div class="search-tools">
          <v-tooltip location="bottom" :text="$t('general.sort')">
            <template #activator="{ props: tooltipProps }">
              <v-menu :transition="false" location="bottom end">
                <template #activator="{ props: menuProps }">
                  <v-btn
                    v-bind="mergeProps(tooltipProps, menuProps)"
                    class="search-sort"
                    variant="text"
                    :aria-label="`${$t('general.sort')}: ${sortText}`"
                  >
                    <v-icon start aria-hidden="true">
                      {{ state.orderDirection === "asc" ? $globals.icons.sortAscending : $globals.icons.sortDescending }}
                    </v-icon>
                    <span>{{ sortText }}</span>
                  </v-btn>
                </template>
                <v-list min-width="240">
                  <v-list-item
                    slim
                    density="comfortable"
                    :prepend-icon="state.orderDirection === 'asc' ? $globals.icons.sortDescending : $globals.icons.sortAscending"
                    :title="state.orderDirection === 'asc' ? $t('general.sort-descending') : $t('general.sort-ascending')"
                    @click="toggleOrderDirection"
                  />
                  <v-divider />
                  <v-list-item
                    v-for="option in sortable"
                    :key="option.value"
                    :active="state.orderBy === option.value"
                    :prepend-icon="option.icon"
                    slim
                    density="comfortable"
                    @click="option.value === 'random' ? setRandomOrderByWrapper() : setOrderBy(option.value)"
                  >
                    <template #title>
                      <span>{{ option.name }}</span>
                      <v-progress-circular
                        v-if="option.value === 'random' && showRandomLoading"
                        indeterminate
                        size="16"
                        width="2"
                        class="ml-3"
                      />
                    </template>
                  </v-list-item>
                </v-list>
              </v-menu>
            </template>
          </v-tooltip>
          <v-tooltip location="bottom" :text="$t('general.settings')">
            <template #activator="{ props: tooltipProps }">
              <v-menu
                location="bottom end"
                :transition="false"
                :close-on-content-click="false"
              >
                <template #activator="{ props: menuProps }">
                  <v-btn
                    v-bind="mergeProps(tooltipProps, menuProps)"
                    variant="text"
                    :icon="$globals.icons.cog"
                    :aria-label="$t('general.settings')"
                  />
                </template>
                <v-card width="280" max-width="calc(100vw - 32px)">
                  <v-card-text>
                    <v-switch
                      v-model="state.auto"
                      color="primary"
                      :label="$t('search.auto-search')"
                      hide-details
                      class="mb-4"
                    />
                    <v-btn
                      block
                      color="primary"
                      variant="tonal"
                      :prepend-icon="$globals.icons.close"
                      @click="clearSearch"
                    >
                      {{ $t("general.reset") }}
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-menu>
            </template>
          </v-tooltip>
        </div>
      </div>
      <div
        v-if="!state.auto"
        class="search-button-container"
      >
        <v-btn
          color="primary"
          variant="flat"
          type="submit"
          :prepend-icon="$globals.icons.search"
        >
          {{ $t("search.search") }}
        </v-btn>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { mergeProps } from "vue";
import RecipeExplorerPageSearchFilters from "./RecipeExplorerPageSearchFilters.vue";
import { useRecipeExplorerSearch, clearRecipeExplorerSearchState } from "~/composables/use-recipe-explorer-search";

const emit = defineEmits<{
  ready: [];
}>();

const $auth = useMealieAuth();
const route = useRoute();
const { $globals } = useNuxtApp();
const i18n = useI18n();
const showRandomLoading = ref(false);

const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

const {
  state,
  passedQueryWithSeed,
  search,
  reset,
  toggleOrderDirection,
  setOrderBy,
  setRandomOrderBy,
  filterItems,
  initialize,
} = useRecipeExplorerSearch(groupSlug);

defineExpose({
  passedQueryWithSeed,
  filterItems,
  clearSearch,
});

onMounted(async () => {
  await initialize();
  emit("ready");
});

onUnmounted(() => {
  clearRecipeExplorerSearchState(groupSlug.value);
});

const sortText = computed(() => {
  const sort = sortable.value.find(s => s.value === state.value.orderBy);
  if (!sort) return "";
  return `${sort.name}`;
});

const sortable = computed(() => [
  {
    icon: $globals.icons.orderAlphabeticalAscending,
    name: i18n.t("general.sort-alphabetically"),
    value: "name",
  },
  {
    icon: $globals.icons.newBox,
    name: i18n.t("general.created"),
    value: "created_at",
  },
  {
    icon: $globals.icons.chefHat,
    name: i18n.t("general.last-made"),
    value: "last_made",
  },
  {
    icon: $globals.icons.star,
    name: i18n.t("general.rating"),
    value: "rating",
  },
  {
    icon: $globals.icons.update,
    name: i18n.t("general.updated"),
    value: "updated_at",
  },
  {
    icon: $globals.icons.diceMultiple,
    name: i18n.t("general.random"),
    value: "random",
  },
]);

const input: Ref<any> = ref(null);

async function clearSearch() {
  reset();
  await search();
}

function hideKeyboard() {
  input.value?.blur();
}

async function setRandomOrderByWrapper() {
  showRandomLoading.value = true;
  try {
    await setRandomOrderBy();
  }
  finally {
    showRandomLoading.value = false;
  }
}
</script>

<style scoped>
.search-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.search-container {
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.search-box {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 20px;
  width: 100%;
  min-width: 0;
}

.library-search-input {
  flex: 1 1 280px;
  max-width: 560px;
}

.search-row {
  flex: 1 1 auto;
  margin-top: 0;
}

.search-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  min-width: 0;
}

.search-tools :deep(.v-btn),
.search-button-container :deep(.v-btn) {
  min-height: 44px;
  border-radius: 6px;
}

.search-sort {
  max-width: 100%;
  color: rgb(var(--v-theme-on-surface-variant));
}

.search-sort :deep(.v-btn__content) {
  white-space: normal;
  text-align: start;
}

.search-tools :deep(.v-btn:active) {
  transform: scale(0.98);
}

.search-button-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

@media (max-width: 600px) {
  .library-search-input {
    flex-basis: 100%;
    max-width: none;
  }

  .search-tools {
    justify-content: flex-end;
    flex: 1 1 100%;
  }
}
</style>
