<template>
  <div class="manual-recipe-form">
    <h2 class="recipe-form-heading">
      {{ $t('recipe.create-recipe') }}
    </h2>
    <v-card-text>
      <v-form
        ref="domCreateByName"
        @submit.prevent="createByName(newRecipeName)"
      >
        <v-text-field
          v-model="newRecipeName"
          :label="$t('recipe.recipe-name')"
          :prepend-inner-icon="$globals.icons.primary"
          validate-on="blur"
          autofocus
          variant="outlined"
          clearable
          class="mt-2"
          color="primary"
          :rules="[validators.required]"
          :hint="$t('recipe.new-recipe-names-must-be-unique')"
          persistent-hint
        />
      </v-form>
    </v-card-text>
    <v-alert v-if="error" type="error" variant="tonal" role="alert" class="mb-4">
      {{ $t('recipe.recipe-creation-failed') }}
    </v-alert>
    <v-card-actions>
      <BaseButton
        :disabled="newRecipeName.trim() === '' || loading"
        :text="$t('recipe.create-recipe')"
        color="primary"
        min-height="44"
        :loading="loading"
        @click="createByName(newRecipeName)"
      />
    </v-card-actions>
  </div>
</template>

<script lang="ts">
import type { AxiosResponse } from "axios";
import { useUserApi } from "~/composables/api";
import { validators } from "~/composables/use-validators";
import type { VForm } from "~/types/auto-forms";

export default defineNuxtComponent({
  setup() {
    const state = reactive({
      error: false,
      loading: false,
    });
    const $auth = useMealieAuth();
    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

    const api = useUserApi();
    const router = useRouter();

    function handleResponse(response: AxiosResponse<string> | null, edit = false) {
      if (response?.status !== 201) {
        state.error = true;
        state.loading = false;
        return;
      }
      router.push(`/g/${groupSlug.value}/r/${response.data}?edit=${edit.toString()}`);
    }

    const newRecipeName = ref("");
    const domCreateByName = ref<VForm | null>(null);

    async function createByName(name: string) {
      if (!name.trim() || state.loading) {
        return;
      }
      const validation = await domCreateByName.value?.validate();
      if (!validation?.valid || state.loading) {
        return;
      }
      state.loading = true;
      state.error = false;
      try {
        const { response } = await api.recipes.createOne({ name });
        handleResponse(response as any, true);
      }
      catch {
        state.error = true;
      }
      finally {
        state.loading = false;
      }
    }
    return {
      domCreateByName,
      newRecipeName,
      createByName,
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

@media (max-width: 600px) {
  .manual-recipe-form :deep(.v-card-actions .v-btn) {
    width: 100%;
  }
}
</style>
