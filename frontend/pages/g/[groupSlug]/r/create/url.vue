<template>
  <div>
    <v-form
      ref="domUrlForm"
      @submit.prevent="createByUrl(recipeUrl, importKeywordsAsTags)"
    >
      <div class="url-import-form">
        <h2 class="recipe-form-heading">
          {{ $t('recipe.import-with-url') }}
        </h2>
        <v-card-text>
          <v-text-field
            v-model="recipeUrl"
            :label="$t('new-recipe.recipe-url')"
            :prepend-inner-icon="$globals.icons.link"
            validate-on="blur"
            autofocus
            variant="outlined"
            clearable
            class="mt-2"
            :rules="[validators.url]"
            :hint="$t('new-recipe.url-form-hint')"
            persistent-hint
          />
        </v-card-text>
        <fieldset class="recipe-import-options">
          <legend>{{ $t('general.options') }}</legend>
          <v-checkbox
            v-model="importKeywordsAsTags"
            color="primary"
            hide-details
            :label="$t('recipe.import-original-keywords-as-tags')"
          />
          <v-checkbox
            v-model="stayInEditMode"
            color="primary"
            hide-details
            :label="$t('recipe.stay-in-edit-mode')"
          />
          <v-checkbox
            v-model="parseRecipe"
            color="primary"
            hide-details
            :label="$t('recipe.parse-recipe-ingredients-after-import')"
          />
        </fieldset>
        <v-card-actions>
          <BaseButton
            :disabled="!recipeUrl?.trim() || loading"
            :text="$t('recipe.import-with-url')"
            :icon="$globals.icons.link"
            min-height="44"
            color="primary"
            type="submit"
            :loading="loading"
          />
        </v-card-actions>
      </div>
    </v-form>
    <Transition name="recipe-feedback">
      <v-alert
        v-if="error"
        color="error"
        class="mt-6"
        variant="tonal"
        role="alert"
      >
        <v-card-title class="ma-0 pa-0">
          <v-icon
            start
            size="x-large"
          >
            {{ $globals.icons.robot }}
          </v-icon>
          {{ $t("new-recipe.error-title") }}
        </v-card-title>
        <v-divider class="my-3 mx-2" />

        <p>
          {{ $t("new-recipe.error-details") }}
        </p>
        <div class="recipe-error-links">
          <a
            class="dark"
            href="https://developers.google.com/search/docs/data-types/recipe"
            target="_blank"
            rel="noreferrer nofollow"
          >
            {{ $t("new-recipe.google-ld-json-info") }}
          </a>
          <a
            href="https://github.com/mealie-recipes/mealie/issues"
            target="_blank"
            rel="noreferrer nofollow"
          >
            {{ $t("new-recipe.github-issues") }}
          </a>
          <a
            href="https://schema.org/Recipe"
            target="_blank"
            rel="noreferrer nofollow"
          >
            {{ $t("new-recipe.recipe-markup-specification") }}
          </a>
        </div>
      </v-alert>
    </Transition>
  </div>
</template>

<script lang="ts">
import type { AxiosResponse } from "axios";
import { useUserApi } from "~/composables/api";
import { useTagStore } from "~/composables/store/use-tag-store";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import { validators } from "~/composables/use-validators";
import type { VForm } from "~/types/auto-forms";

export default defineNuxtComponent({
  setup() {
    definePageMeta({
      key: route => route.path,
    });
    const state = reactive({
      error: false,
      loading: false,
    });

    const $auth = useMealieAuth();
    const api = useUserApi();
    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

    const router = useRouter();
    const tags = useTagStore();

    const {
      importKeywordsAsTags,
      stayInEditMode,
      parseRecipe,
      navigateToRecipe,
    } = useNewRecipeOptions();

    function handleResponse(response: AxiosResponse<string> | null, refreshTags = false) {
      if (response?.status !== 201) {
        state.error = true;
        state.loading = false;
        return;
      }
      if (refreshTags) {
        tags.actions.refresh();
      }

      navigateToRecipe(response.data, groupSlug.value, `/g/${groupSlug.value}/r/create/url`);
    }

    const recipeUrl = computed({
      set(recipe_import_url: string | null) {
        router.replace({ query: { ...route.query, recipe_import_url: recipe_import_url?.trim() || undefined } });
      },
      get() {
        return typeof route.query.recipe_import_url === "string" ? route.query.recipe_import_url : null;
      },
    });

    onMounted(() => {
      if (recipeUrl.value && recipeUrl.value.includes("https")) {
        // Check if we have a query params for using keywords as tags or staying in edit mode.
        // We don't use these in the app anymore, but older automations such as Bookmarklet might still use them,
        // and they're easy enough to support.
        const importKeywordsAsTagsParam = route.query.use_keywords;
        if (importKeywordsAsTagsParam === "1") {
          importKeywordsAsTags.value = true;
        }
        else if (importKeywordsAsTagsParam === "0") {
          importKeywordsAsTags.value = false;
        }

        const stayInEditModeParam = route.query.edit;
        if (stayInEditModeParam === "1") {
          stayInEditMode.value = true;
        }
        else if (stayInEditModeParam === "0") {
          stayInEditMode.value = false;
        }

        createByUrl(recipeUrl.value, importKeywordsAsTags.value);
        return;
      }
    });

    const domUrlForm = ref<VForm | null>(null);

    async function createByUrl(url: string | null, importKeywordsAsTags: boolean) {
      if (!url?.trim() || state.loading) {
        return;
      }

      const validation = await domUrlForm.value?.validate();
      if (!validation?.valid || state.loading) {
        return;
      }
      state.loading = true;
      state.error = false;
      try {
        const { response } = await api.recipes.createOneByUrl(url, importKeywordsAsTags);
        handleResponse(response, importKeywordsAsTags);
      }
      catch {
        state.error = true;
      }
      finally {
        state.loading = false;
      }
    }

    return {
      recipeUrl,
      importKeywordsAsTags,
      stayInEditMode,
      parseRecipe,
      domUrlForm,
      createByUrl,
      ...toRefs(state),
      validators,
    };
  },
});
</script>

<style scoped>
.recipe-form-heading {
  margin-bottom: 16px;
  font-size: 1.125rem;
  font-weight: 600;
}

.recipe-import-options {
  border: 0;
  padding: 8px 0;
  min-width: 0;
}

.recipe-import-options legend {
  font-size: 0.875rem;
  font-weight: 600;
}

.recipe-import-options :deep(.v-label) {
  white-space: normal;
  line-height: 1.5;
}

.recipe-error-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
  margin-top: 16px;
}

.recipe-error-links a {
  color: rgb(var(--v-theme-on-surface));
  text-decoration: underline;
}

.recipe-feedback-enter-active {
  transition: opacity 220ms ease-out;
}

.recipe-feedback-leave-active {
  transition: opacity 160ms ease-in;
}

.recipe-feedback-enter-from,
.recipe-feedback-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .recipe-feedback-enter-active,
  .recipe-feedback-leave-active {
    transition: none;
  }
}

@media (max-width: 600px) {
  .url-import-form :deep(.v-card-actions .v-btn) {
    width: 100%;
  }
}
</style>
