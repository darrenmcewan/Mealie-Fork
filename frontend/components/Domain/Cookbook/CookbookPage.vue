<template>
  <div>
    <!-- Edit Dialog -->
    <BaseDialog
      v-if="editTarget"
      v-model="dialogStates.edit"
      width="100%"
      max-width="1100px"
      :icon="$globals.icons.pages"
      :title="$t('general.edit')"
      :submit-icon="$globals.icons.save"
      :submit-text="$t('general.save')"
      :submit-disabled="!editTarget.queryFilterString"
      can-submit
      @submit="editCookbook"
    >
      <v-card-text>
        <CookbookEditor
          v-model="editTarget"
        />
      </v-card-text>
    </BaseDialog>

    <v-container
      v-if="book"
      class="my-0 cookbook-detail"
    >
      <BasePageTitle divider>
        <template #title>
          {{ book.name }}
        </template>
        <span v-if="book.description">{{ book.description }}</span>
        <template #content>
          <BaseButton
            v-if="canEdit"
            min-height="44"
            color="primary"
            secondary
            :edit="true"
            @click="handleEditCookbook"
          />
        </template>
      </BasePageTitle>

      <v-container class="pa-0">
        <RecipeCardSection
          class="mb-5 mx-1"
          :recipes="recipes"
          :query="{ cookbook: slug }"
          @sort-recipes="assignSorted"
          @replace-recipes="replaceRecipes"
          @append-recipes="appendRecipes"
          @delete="removeRecipe"
        />
      </v-container>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { useLazyRecipes } from "~/composables/recipes";
import RecipeCardSection from "@/components/Domain/Recipe/RecipeCardSection.vue";
import { useCookbookStore } from "~/composables/store/use-cookbook-store";
import { useCookbook } from "~/composables/use-group-cookbooks";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { ReadCookBook } from "~/lib/api/types/cookbook";
import CookbookEditor from "~/components/Domain/Cookbook/CookbookEditor.vue";

const $auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

const { recipes, appendRecipes, assignSorted, removeRecipe, replaceRecipes } = useLazyRecipes(isOwnGroup.value ? null : groupSlug.value);
const slug = route.params.slug as string;
const { getOne } = useCookbook(isOwnGroup.value ? null : groupSlug.value);
const { actions } = useCookbookStore();
const router = useRouter();

const book = getOne(slug);

const isOwnHousehold = computed(() => {
  if (!($auth.user.value && book.value?.householdId)) {
    return false;
  }

  return $auth.user.value.householdId === book.value.householdId;
});
const canEdit = computed(() => isOwnGroup.value && isOwnHousehold.value);

const dialogStates = reactive({
  edit: false,
});

const editTarget = ref<ReadCookBook | null>(null);
function handleEditCookbook() {
  dialogStates.edit = true;
  editTarget.value = book.value;
}

async function editCookbook() {
  if (!editTarget.value) {
    return;
  }
  const response = await actions.updateOne(editTarget.value);

  if (response?.slug && book.value?.slug !== response?.slug) {
    // if name changed, redirect to new slug
    router.push(`/g/${route.params.groupSlug}/cookbooks/${response?.slug}`);
  }
  else {
    // otherwise reload the page, since the recipe criteria changed
    router.go(0);
  }
  dialogStates.edit = false;
  editTarget.value = null;
}

useSeoMeta({
  title: book?.value?.name || "Cookbook",
});
</script>

<style scoped>
.cookbook-detail :deep(.v-btn:not(.v-btn--icon)) {
  border-radius: 6px;
  letter-spacing: 0;
}
</style>
