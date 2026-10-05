<template>
  <div>
    <!-- Create Dialog -->
    <BaseDialog
      v-if="createTarget"
      v-model="dialogStates.create"
      width="100%"
      max-width="1100px"
      :icon="$globals.icons.pages"
      :title="$t('cookbook.create-a-cookbook')"
      :submit-icon="$globals.icons.save"
      :submit-text="$t('general.save')"
      :submit-disabled="!createTarget.queryFilterString"
      can-submit
      @submit="actions.updateOne(createTarget)"
      @cancel="deleteCreateTarget()"
    >
      <v-card-text>
        <CookbookEditor :key="createTargetKey" v-model="createTarget" />
      </v-card-text>
    </BaseDialog>

    <!-- Delete Dialog -->
    <BaseDialog
      v-model="dialogStates.delete"
      :title="$t('general.delete-with-name', { name: $t('cookbook.cookbook') })"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="deleteCookbook()"
    >
      <v-card-text>
        <p>{{ $t("general.confirm-delete-generic-with-name", { name: $t("cookbook.cookbook") }) }}</p>
        <p v-if="deleteTarget" class="mt-4 ml-4">
          {{ deleteTarget.name }}
        </p>
      </v-card-text>
    </BaseDialog>

    <!-- Cookbook Page -->
    <!-- Page Title -->
    <v-container class="cookbooks-page">
      <BasePageTitle divider>
        <template #title>
          {{ $t("cookbook.cookbooks") }}
        </template>
        <template #content>
          <v-btn color="primary" min-height="44" @click="createCookbook">
            <v-icon start>
              {{ $globals.icons.createAlt }}
            </v-icon>
            {{ $t('cookbook.create-a-cookbook') }}
          </v-btn>
        </template>
      </BasePageTitle>

      <div class="cookbooks-toolbar">
        <span class="text-body-2 font-weight-medium">{{ myCookbooks.length }} {{ $t('cookbook.cookbooks') }}</span>
        <v-checkbox
          v-model="cookbookPreferences.hideOtherHouseholds"
          :label="$t('cookbook.hide-cookbooks-from-other-households')"
          hide-details
          color="primary"
          class="flex-grow-0"
        />
      </div>

      <section v-if="!myCookbooks.length" class="cookbooks-empty">
        <v-img width="80" height="80" src="/svgs/manage-cookbooks.svg" aria-hidden="true" />
        <h2>{{ $t('cookbook.cookbooks') }}</h2>
        <v-btn variant="tonal" color="primary" min-height="44" @click="createCookbook">
          <v-icon start>
            {{ $globals.icons.createAlt }}
          </v-icon>
          {{ $t('cookbook.create-a-cookbook') }}
        </v-btn>
      </section>

      <!-- Cookbook List -->
      <v-expansion-panels v-else class="cookbooks-list" variant="accordion">
        <VueDraggable
          v-model="myCookbooks"
          handle=".handle"
          :delay="250"
          :delay-on-touch-only="true"
          style="width: 100%"
          @end="updateAll(myCookbooks)"
        >
          <v-expansion-panel
            v-for="(cookbook, index) in myCookbooks"
            :key="cookbook.id"
            class="cookbook-entry"
          >
            <v-expansion-panel-title disable-icon-rotate class="cookbook-entry-heading">
              <div class="cookbook-entry-summary">
                <v-icon color="primary" aria-hidden="true">
                  {{ $globals.icons.pages }}
                </v-icon>
                <div class="cookbook-entry-copy">
                  <span class="cookbook-entry-name">{{ cookbook.name }}</span>
                  <p v-if="cookbook.description" class="cookbook-entry-description">
                    {{ cookbook.description }}
                  </p>
                </div>
              </div>
              <template #actions>
                <div class="d-flex align-center">
                  <v-icon class="mx-2" aria-hidden="true">
                    {{ $globals.icons.edit }}
                  </v-icon>
                  <v-icon class="handle cookbook-drag-handle" :size="24" :title="$t('general.sort')">
                    {{ $globals.icons.arrowUpDown }}
                  </v-icon>
                </div>
              </template>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div class="cookbook-entry-link">
                <v-btn :to="`/g/${groupSlug}/cookbooks/${cookbook.slug}`" variant="tonal" color="primary" min-height="44">
                  <v-icon start>
                    {{ $globals.icons.pages }}
                  </v-icon>
                  {{ $t('cookbook.cookbook') }}
                </v-btn>
              </div>
              <CookbookEditor
                v-model="myCookbooks[index]"
                :collapsable="false"
              />
              <v-card-actions>
                <v-spacer />
                <BaseButtonGroup
                  :buttons="[
                    {
                      icon: $globals.icons.delete,
                      text: $t('general.delete'),
                      event: 'delete',
                    },
                    {
                      icon: $globals.icons.save,
                      text: $t('general.save'),
                      event: 'save',
                      disabled: !cookbook.queryFilterString,
                    },
                  ]"
                  @delete="deleteEventHandler(myCookbooks[index])"
                  @save="actions.updateOne(myCookbooks[index])"
                />
              </v-card-actions>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </VueDraggable>
      </v-expansion-panels>
    </v-container>
  </div>
</template>

<script lang="ts">
import { VueDraggable } from "vue-draggable-plus";
import { useCookbookStore } from "~/composables/store/use-cookbook-store";
import { useHouseholdSelf } from "@/composables/use-households";
import CookbookEditor from "~/components/Domain/Cookbook/CookbookEditor.vue";
import type { CreateCookBook, ReadCookBook } from "~/lib/api/types/cookbook";
import { useCookbookPreferences } from "~/composables/use-users/preferences";

export default defineNuxtComponent({
  components: { CookbookEditor, VueDraggable },
  middleware: ["group-only"],
  setup() {
    const dialogStates = reactive({
      create: false,
      delete: false,
    });

    const i18n = useI18n();

    // Set page title
    useSeoMeta({
      title: i18n.t("cookbook.cookbooks"),
    });

    const $auth = useMealieAuth();
    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug || $auth.user.value?.groupSlug || "");
    const { store: allCookbooks, actions, updateAll } = useCookbookStore();

    // Make a local reactive copy of myCookbooks
    const myCookbooks = ref<ReadCookBook[]>([]);
    watch(
      allCookbooks,
      (cookbooks) => {
        myCookbooks.value
          = cookbooks?.filter(
            cookbook => cookbook.householdId === $auth.user.value?.householdId,
          ).sort((a, b) => a.position > b.position) ?? [];
      },
      { immediate: true },
    );

    const { household } = useHouseholdSelf();
    const cookbookPreferences = useCookbookPreferences();

    // create
    const createTargetKey = ref(0);
    const createTarget = ref<ReadCookBook | null>(null);
    async function createCookbook() {
      const name = i18n.t("cookbook.household-cookbook-name", [
        household.value?.name || "",
        String((myCookbooks.value?.length ?? 0) + 1),
      ]) as string;

      const data = { name } as CreateCookBook;
      await actions.createOne(data).then((cookbook) => {
        if (!cookbook) {
          return;
        }

        myCookbooks.value.push(cookbook);
        createTarget.value = cookbook as ReadCookBook;
        createTargetKey.value++;
      });
      dialogStates.create = true;
    }

    // delete
    const deleteTarget = ref<ReadCookBook | null>(null);
    function deleteEventHandler(item: ReadCookBook) {
      deleteTarget.value = item;
      dialogStates.delete = true;
    }
    async function deleteCookbook() {
      if (!deleteTarget.value) {
        return;
      }
      await actions.deleteOne(deleteTarget.value.id);
      myCookbooks.value = myCookbooks.value.filter(c => c.id !== deleteTarget.value?.id);
      dialogStates.delete = false;
      deleteTarget.value = null;
    }

    async function deleteCreateTarget() {
      if (!createTarget.value?.id) {
        return;
      }
      await actions.deleteOne(createTarget.value.id);
      myCookbooks.value = myCookbooks.value.filter(c => c.id !== createTarget.value?.id);
      dialogStates.create = false;
      createTarget.value = null;
    }
    function handleUnmount() {
      if (!createTarget.value?.id || createTarget.value.queryFilterString) {
        return;
      }
      deleteCreateTarget();
    }
    onMounted(() => {
      window.addEventListener("beforeunload", handleUnmount);
    });
    onBeforeUnmount(() => {
      handleUnmount();
      window.removeEventListener("beforeunload", handleUnmount);
    });

    return {
      groupSlug,
      myCookbooks,
      cookbookPreferences,
      actions,
      dialogStates,
      // create
      createTargetKey,
      createTarget,
      createCookbook,

      // update
      updateAll,

      // delete
      deleteTarget,
      deleteEventHandler,
      deleteCookbook,
      deleteCreateTarget,
    };
  },
});
</script>

<style scoped>
.cookbooks-page {
  max-width: 1040px;
}

.cookbooks-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.cookbook-entry {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 6px !important;
  margin-bottom: 12px;
  background: rgb(var(--v-theme-surface));
}

.cookbook-entry-heading {
  min-height: 80px;
  padding: 16px 20px;
}

.cookbook-entry-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  padding-inline-end: 12px;
}

.cookbook-entry-copy {
  min-width: 0;
  overflow-wrap: anywhere;
}

.cookbook-entry-name {
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.5;
}

.cookbook-entry-description {
  margin-top: 4px;
  font-size: 0.875rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.72);
}

.cookbook-drag-handle {
  min-width: 44px;
  min-height: 44px;
  cursor: grab;
}

.cookbook-entry-link {
  display: flex;
  justify-content: flex-end;
  padding: 8px 0 16px;
}

.cookbooks-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 48px 16px;
  text-align: center;
  border-block: 1px solid rgba(var(--v-theme-on-background), 0.12);
}

.cookbooks-empty h2 {
  font-size: 1.125rem;
  font-weight: 600;
}

.cookbooks-page :deep(.v-btn:not(.v-btn--icon)) {
  min-height: 44px;
  border-radius: 6px;
  letter-spacing: 0;
}

@media (max-width: 600px) {
  .cookbook-entry-heading {
    padding: 12px;
  }

  .cookbook-entry-summary {
    gap: 8px;
  }

  .cookbook-entry-heading :deep(.v-expansion-panel-title__icon) {
    align-self: center;
  }
}
</style>
