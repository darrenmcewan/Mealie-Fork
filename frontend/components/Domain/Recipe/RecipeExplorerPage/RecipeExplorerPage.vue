<template>
  <v-container
    fluid
    class="recipe-library"
  >
    <header class="library-header">
      <div>
        <h1 class="library-title">
          {{ $t("general.recipes") }}
        </h1>
        <p class="library-count" role="status" aria-live="polite">
          {{ recipesLoaded ? `${$t('search.results')}: ${$n(recipes.length)}` : $t('general.loading-recipes') }}
        </p>
      </div>
      <v-btn
        v-if="isOwnGroup"
        color="primary"
        variant="flat"
        class="library-add"
        :to="`/g/${groupSlug}/r/create`"
        :prepend-icon="$globals.icons.createAlt"
      >
        {{ $t("new-recipe.add-recipe") }}
      </v-btn>
    </header>
    <RecipeComparisonToolbar />
    <RecipeExplorerPageSearch
      ref="searchComponent"
      @ready="onSearchReady"
    />
    <section
      class="library-results"
      :aria-label="$t('search.results')"
      :aria-busy="!recipesLoaded"
    >
      <RecipeCardSection
        v-if="ready"
        :icon="$globals.icons.silverwareForkKnife"
        :title="$t('general.recipes')"
        :recipes="recipes"
        :query="searchQuery"
        :disable-toolbar="!recipes.length"
        comparison-enabled
        disable-sort
        @item-selected="onItemSelected"
        @replace-recipes="onReplaceRecipes"
        @append-recipes="appendRecipes"
      >
        <template #title>
          <span class="library-results-label">{{ $t("search.results") }}</span>
        </template>
      </RecipeCardSection>
      <div v-if="!recipesLoaded" class="library-loading" role="status">
        <v-progress-circular indeterminate color="primary" size="28" />
        <span>{{ $t("general.loading-recipes") }}</span>
      </div>
      <div v-else-if="!recipes.length && hasActiveFilters" class="library-no-results">
        <v-icon size="36" color="primary" aria-hidden="true">
          {{ $globals.icons.search }}
        </v-icon>
        <h2>{{ $t("search.no-results") }}</h2>
        <v-btn
          color="primary"
          variant="tonal"
          :prepend-icon="$globals.icons.close"
          @click="searchComponent?.clearSearch()"
        >
          {{ $t("general.reset") }}
        </v-btn>
      </div>
      <div v-else-if="!recipes.length" class="library-empty">
        <img
          class="library-empty-image"
          :src="`${$config.app.baseURL.replace(/\/$/, '')}/kitchen-welcome.jpg`"
          alt=""
          width="1200"
          height="600"
          decoding="async"
        >
        <div class="library-empty-content">
          <h2>{{ $t("general.no-recipe-found") }}</h2>
          <div v-if="isOwnGroup" class="library-empty-actions">
            <v-btn
              color="primary"
              variant="flat"
              :to="`/g/${groupSlug}/r/create/new`"
              :prepend-icon="$globals.icons.createAlt"
            >
              {{ $t("recipe.create-recipe") }}
            </v-btn>
            <v-btn
              color="primary"
              variant="outlined"
              :to="`/g/${groupSlug}/r/create/url`"
              :prepend-icon="$globals.icons.link"
            >
              {{ $t("new-recipe.from-url") }}
            </v-btn>
          </div>
        </div>
      </div>
    </section>
  </v-container>
</template>

<script lang="ts">
import RecipeExplorerPageSearch from "./RecipeExplorerPageParts/RecipeExplorerPageSearch.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import RecipeCardSection from "~/components/Domain/Recipe/RecipeCardSection.vue";
import RecipeComparisonToolbar from "~/components/Domain/Recipe/RecipeComparisonToolbar.vue";
import { useLazyRecipes } from "~/composables/recipes";
import type { Recipe } from "~/lib/api/types/recipe";
import type { RecipeSearchQuery } from "~/lib/api/user/recipes/recipe";

export default defineNuxtComponent({
  components: { RecipeCardSection, RecipeExplorerPageSearch, RecipeComparisonToolbar },
  setup() {
    const $auth = useMealieAuth();
    const route = useRoute();

    const { isOwnGroup } = useLoggedInState();
    const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

    const { recipes, appendRecipes, replaceRecipes } = useLazyRecipes(isOwnGroup.value ? null : groupSlug.value);

    const ready = ref(false);
    const recipesLoaded = ref(false);
    const searchComponent = ref<InstanceType<typeof RecipeExplorerPageSearch>>();

    const searchQuery = computed<RecipeSearchQuery>(() => {
      return searchComponent.value?.passedQueryWithSeed || {};
    });

    const hasActiveFilters = computed(() => {
      const query = searchQuery.value;
      return Boolean(query.search || query.categories?.length || query.tags?.length
        || query.tools?.length || query.foods?.length || query.households?.length || query.queryFilter);
    });

    watch(searchQuery, () => {
      recipesLoaded.value = false;
    });

    function onReplaceRecipes(value: Recipe[]) {
      replaceRecipes(value);
      recipesLoaded.value = true;
    }

    function onSearchReady() {
      ready.value = true;
    }

    function onItemSelected(item: any, urlPrefix: string) {
      searchComponent.value?.filterItems(item, urlPrefix);
    }

    return {
      isOwnGroup,
      groupSlug,
      ready,
      recipesLoaded,
      hasActiveFilters,
      searchComponent,
      searchQuery,
      recipes,
      appendRecipes,
      onReplaceRecipes,
      onSearchReady,
      onItemSelected,
    };
  },
});
</script>

<style scoped>
.recipe-library {
  max-width: 1440px;
  padding: 8px 24px 40px;
  color: rgb(var(--v-theme-on-surface));
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}

.library-title {
  font-family: var(--mealie-display-font) !important;
  font-size: 2rem;
  font-weight: 500;
  line-height: 1.25;
  margin: 0 0 8px;
}

.library-count {
  margin: 0;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface-variant));
}

.library-add,
.library-empty-actions :deep(.v-btn) {
  min-height: 44px;
  max-width: 100%;
}

.library-results {
  margin-top: 24px;
}

.library-results-label {
  font-weight: 600;
  font-size: 0.875rem;
}

.library-loading,
.library-no-results {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px 16px;
}

.library-no-results {
  flex-direction: column;
  min-height: 240px;
}

.library-no-results h2,
.library-empty h2 {
  margin: 0;
  font-family: var(--mealie-display-font) !important;
  font-weight: 500;
  font-size: 1.5rem;
  line-height: 1.4;
}

.library-empty {
  max-width: 920px;
  margin: 24px auto 0;
  animation: library-enter var(--mealie-motion-enter) var(--mealie-ease-out) both;
}

.library-empty-image {
  display: block;
  width: 100%;
  height: auto;
  max-height: 300px;
  aspect-ratio: 2 / 1;
  object-fit: cover;
  object-position: center 70%;
  border-radius: 8px;
  background: rgb(var(--v-theme-surface));
}

.library-empty-content {
  padding: 24px 0 0;
  text-align: center;
}

.library-empty-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}

@keyframes library-enter {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 600px) {
  .recipe-library {
    padding: 20px 16px 32px;
  }

  .library-header {
    align-items: flex-start;
    margin-bottom: 20px;
  }

  .library-title {
    font-size: 1.75rem;
  }

  .library-empty-image {
    aspect-ratio: 4 / 3;
  }

  .library-empty-actions {
    flex-direction: column;
  }
}
</style>
