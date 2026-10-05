<template>
  <v-container
    v-if="shoppingList"
    class="shopping-detail"
  >
    <BaseDialog
      v-model="state.checkAllDialog"
      :title="$t('general.confirm')"
      can-confirm
      @confirm="checkAll"
    >
      <v-card-text>
        {{ $t('shopping-list.are-you-sure-you-want-to-check-all-items') }}
      </v-card-text>
    </BaseDialog>

    <BaseDialog
      v-model="state.uncheckAllDialog"
      :title="$t('general.confirm')"
      can-confirm
      @confirm="uncheckAll"
    >
      <v-card-text>
        {{ $t('shopping-list.are-you-sure-you-want-to-uncheck-all-items') }}
      </v-card-text>
    </BaseDialog>

    <BaseDialog
      v-model="state.deleteCheckedDialog"
      :title="$t('general.confirm')"
      can-confirm
      @confirm="deleteChecked"
    >
      <v-card-text>
        {{ $t('shopping-list.are-you-sure-you-want-to-delete-checked-items') }}
      </v-card-text>
    </BaseDialog>

    <!-- Reorder Labels -->
    <BaseDialog
      v-model="reorderLabelsDialog"
      :icon="$globals.icons.tagArrowUp"
      :title="$t('shopping-list.aisle-order')"
      :loading="labelOrderSaving"
      keep-open
      disable-submit-on-enter
      @close="cancelLabelOrder"
    >
      <v-alert v-if="labelOrderError" type="error" variant="tonal" class="ma-4" role="alert">
        {{ labelOrderError }}
      </v-alert>
      <v-alert v-if="isOffline" type="warning" variant="tonal" class="ma-4">
        {{ $t('shopping-list.you-are-offline') }}
      </v-alert>
      <div class="shopping-label-order">
        <div v-if="!localLabels.length" class="pa-4">
          <p class="mb-3">
            {{ $t('shopping-list.no-aisle-labels') }}
          </p>
          <ButtonLink to="/group/data/labels" :text="$t('shopping-list.manage-labels')" :icon="$globals.icons.tags" />
        </div>
        <VueDraggable
          v-else
          :model-value="localLabels"
          handle=".handle"
          :delay="250"
          :delay-on-touch-only="true"
          :disabled="labelOrderSaving"
          class="my-2"
          @update:model-value="updateLabelOrder"
          @end="announceRouteDrag"
        >
          <div v-for="(labelSetting, index) in localLabels" :key="labelSetting.id" :data-label-id="labelSetting.labelId">
            <MultiPurposeLabelSection
              :model-value="labelSetting"
              :can-move-up="index > 0"
              :can-move-down="index < localLabels.length - 1"
              :disabled="labelOrderSaving"
              use-color
              @move="moveAisle(labelSetting.labelId, $event)"
            />
          </div>
        </VueDraggable>
      </div>
      <p class="route-announcement" aria-live="polite" aria-atomic="true">
        {{ routeAnnouncement }}
      </p>
      <template #card-actions>
        <div class="shopping-route-actions">
          <v-btn variant="text" :disabled="labelOrderSaving" @click="cancelLabelOrder">
            {{ $t('general.cancel') }}
          </v-btn>
          <v-btn variant="text" :disabled="!localLabels.length || labelOrderSaving" @click="suggestAisleOrder">
            <v-icon start>
              {{ $globals.icons.sort }}
            </v-icon>
            {{ $t('shopping-list.suggest-aisle-order') }}
          </v-btn>
          <v-btn color="primary" variant="flat" :loading="labelOrderSaving" :disabled="!labelOrderChanged || !localLabels.length || labelOrderSaving || isOffline" @click="saveLabelOrder">
            <v-icon start>
              {{ $globals.icons.save }}
            </v-icon>
            {{ $t('general.save') }}
          </v-btn>
        </div>
      </template>
    </BaseDialog>

    <BasePageTitle divider>
      <template #header>
        <div class="shopping-detail-navigation">
          <ButtonLink
            :to="`/shopping-lists?disableRedirect=true`"
            :text="$t('shopping-list.all-lists')"
            :icon="$globals.icons.backArrow"
          />
          <v-btn variant="text" min-height="44" @click="toggleReorderLabelsDialog()">
            <v-icon start>
              {{ $globals.icons.tagArrowUp }}
            </v-icon>
            {{ $t('shopping-list.aisle-order') }}
          </v-btn>
          <v-menu :transition="false">
            <template #activator="{ props }">
              <v-btn
                v-bind="props"
                icon
                size="44"
                variant="text"
                :aria-label="$t('general.actions')"
                :title="$t('general.actions')"
              >
                <v-icon>{{ $globals.icons.dotsVertical }}</v-icon>
              </v-btn>
            </template>
            <v-list>
              <v-list-item :prepend-icon="$globals.icons.contentCopy" :title="$t('shopping-list.copy-as-text')" @click="copyListItems('plain')" />
              <v-list-item :prepend-icon="$globals.icons.contentCopy" :title="$t('shopping-list.copy-as-markdown')" @click="copyListItems('markdown')" />
              <v-divider />
              <v-list-item :prepend-icon="$globals.icons.checkboxOutline" :title="$t('shopping-list.check-all-items')" :disabled="!listItems.unchecked.length" @click="openCheckAll" />
              <v-list-item :prepend-icon="$globals.icons.tags" :title="$t('shopping-list.reorder-labels')" @click="toggleReorderLabelsDialog()" />
              <v-list-item :prepend-icon="$globals.icons.tags" :title="$t('shopping-list.manage-labels')" to="/group/data/labels" />
            </v-list>
          </v-menu>
        </div>
      </template>
      <template #title>
        {{ shoppingList.name }}
      </template>
      <template #content>
        <div class="shopping-progress">
          <span class="text-body-2">{{ $t('shopping-list.items-checked-count', listItems.checked.length) }}</span>
          <v-progress-linear
            :model-value="listItems.checked.length + listItems.unchecked.length ? listItems.checked.length / (listItems.checked.length + listItems.unchecked.length) * 100 : 0"
            color="primary"
            height="4"
            :aria-label="$t('shopping-list.items-checked-count', listItems.checked.length)"
          />
        </div>
        <v-btn v-if="!createEditorOpen" color="primary" min-height="44" @click="createEditorOpen = true">
          <v-icon start>
            {{ $globals.icons.createAlt }}
          </v-icon>
          {{ $t('general.add') }}
        </v-btn>
      </template>
    </BasePageTitle>
    <BannerWarning
      v-if="isOffline"
      :title="$t('shopping-list.you-are-offline')"
      :description="$t('shopping-list.you-are-offline-description')"
    />

    <!-- Viewer -->
    <section v-if="!edit" class="py-2 d-flex flex-column ga-4">
      <!-- Create Item -->
      <div v-if="createEditorOpen">
        <ShoppingListItemEditor
          v-model="createListItemData"
          class="my-4"
          :labels="allLabels || []"
          :units="allUnits || []"
          :foods="allFoods || []"
          :allow-delete="false"
          @delete="createEditorOpen = false"
          @cancel="createEditorOpen = false"
          @save="createListItem"
        />
      </div>
      <div v-if="!listItems.unchecked.length && !listItems.checked.length && !createEditorOpen" class="shopping-items-empty">
        <v-icon size="40" color="primary">
          {{ $globals.icons.cartCheck }}
        </v-icon>
        <h2>{{ $t('shopping-list.shopping-list') }}</h2>
        <v-btn variant="tonal" color="primary" min-height="44" @click="createEditorOpen = true">
          <v-icon start>
            {{ $globals.icons.createAlt }}
          </v-icon>
          {{ $t('general.add') }}
        </v-btn>
      </div>

      <BaseExpansionPanels v-for="section in itemsByLabel" :key="section.key" :v-model="0" start-open>
        <v-expansion-panel class="shopping-list-section">
          <v-expansion-panel-title
            :color="section.color || undefined"
            class="body-1 font-weight-bold section-title"
          >
            {{ section.name }}
            <span class="ml-3 text-caption">{{ section.items.length }}</span>
          </v-expansion-panel-title>
          <v-expansion-panel-text eager>
            <VueDraggable
              :model-value="section.items"
              handle=".handle"
              :delay="250"
              :delay-on-touch-only="true"
              @start="loadingCounter += 1"
              @end="loadingCounter -= 1"
              @update:model-value="updateIndexUncheckedByLabel(section.key, $event)"
            >
              <ShoppingListItem
                v-for="(item, index) in section.items"
                :key="item.id"
                v-model="section.items[index]"
                class="shopping-item-row"
                :labels="allLabels || []"
                :units="allUnits || []"
                :foods="allFoods || []"
                :recipes="recipeMap"
                @checked="saveListItem"
                @save="saveListItem"
                @delete="deleteListItem(item)"
              />
            </VueDraggable>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </BaseExpansionPanels>
      <!-- Checked Items -->
      <v-expansion-panels flat>
        <v-expansion-panel v-if="listItems.checked && listItems.checked.length > 0">
          <v-expansion-panel-title class="border-solid border-thin py-1">
            <div class="d-flex align-center flex-0-1-100">
              <div class="flex-1-0">
                {{ $t('shopping-list.items-checked-count', listItems.checked ? listItems.checked.length : 0) }}
              </div>
              <div class="justify-end">
                <BaseButtonGroup
                  :buttons="[
                    {
                      icon: $globals.icons.checkboxBlankOutline,
                      text: $t('shopping-list.uncheck-all-items'),
                      event: 'uncheck',
                    },
                    {
                      icon: $globals.icons.delete,
                      text: $t('shopping-list.delete-checked'),
                      event: 'delete',
                    },
                  ]"
                  @uncheck="openUncheckAll"
                  @delete="openDeleteChecked"
                />
              </div>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text eager>
            <div v-for="(item, idx) in listItems.checked" :key="item.id">
              <ShoppingListItem
                v-model="listItems.checked[idx]"
                class="strike-through-note"
                :labels="allLabels || []"
                :units="allUnits || []"
                :foods="allFoods || []"
                @checked="saveListItem"
                @save="saveListItem"
                @delete="deleteListItem(item)"
              />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </section>

    <!-- Recipe References -->
    <v-lazy
      v-if="shoppingList.recipeReferences && shoppingList.recipeReferences.length > 0"
      class="mt-6"
    >
      <section>
        <div>
          <span>
            <v-icon start class="mb-1">
              {{ $globals.icons.primary }}
            </v-icon>
          </span>
          {{ $t('shopping-list.linked-recipes-count', shoppingList.recipeReferences
            ? shoppingList.recipeReferences.length
            : 0) }}
        </div>
        <v-divider />
        <RecipeList
          :recipes="recipeList"
          show-description
          :disabled="isOffline"
        >
          <template
            v-for="(recipe, index) in recipeList"
            #[`actions-${recipe.id}`]
            :key="'item-actions-decrease' + recipe.id"
          >
            <v-list-item-action>
              <v-btn
                v-if="recipe"
                icon
                flat
                class="bg-transparent"
                :disabled="isOffline"
                :aria-label="$t('general.delete')"
                :title="$t('general.delete')"
                @click.prevent="removeRecipeReferenceToList(recipe.id!)"
              >
                <v-icon color="grey-lighten-1">
                  {{ $globals.icons.minus }}
                </v-icon>
              </v-btn>
            </v-list-item-action>
            <div class="pl-3">
              {{ shoppingList.recipeReferences[index].recipeQuantity }}
            </div>
            <v-list-item-action>
              <v-btn
                icon
                :disabled="isOffline"
                :aria-label="$t('general.add')"
                :title="$t('general.add')"
                flat
                class="bg-transparent"
                @click.prevent="addRecipeReferenceToList(recipe.id!)"
              >
                <v-icon color="grey-lighten-1">
                  {{ $globals.icons.createAlt }}
                </v-icon>
              </v-btn>
            </v-list-item-action>
          </template>
        </RecipeList>
      </section>
    </v-lazy>
    <WakelockSwitch />
  </v-container>
</template>

<script lang="ts">
import { VueDraggable } from "vue-draggable-plus";
import RecipeList from "~/components/Domain/Recipe/RecipeList.vue";
import MultiPurposeLabelSection from "~/components/Domain/ShoppingList/MultiPurposeLabelSection.vue";
import ShoppingListItem from "~/components/Domain/ShoppingList/ShoppingListItem.vue";
import ShoppingListItemEditor from "~/components/Domain/ShoppingList/ShoppingListItemEditor.vue";
import { useShoppingListPage } from "~/composables/shopping-list-page/use-shopping-list-page";
import { useFoodStore, useLabelStore, useUnitStore } from "~/composables/store";
import { getTextColor } from "~/composables/use-text-color";
import { useShoppingListPreferences } from "~/composables/use-users/preferences";

export default defineNuxtComponent({
  components: {
    VueDraggable,
    MultiPurposeLabelSection,
    ShoppingListItem,
    RecipeList,
    ShoppingListItemEditor,
  },
  setup() {
    const i18n = useI18n();
    const $auth = useMealieAuth();
    const preferences = useShoppingListPreferences();

    useSeoMeta({
      title: i18n.t("shopping-list.shopping-list"),
    });

    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");
    const id = route.params.id as string;

    const shoppingListPage = useShoppingListPage(id);
    const routeAnnouncement = ref("");

    function announceAisle(labelId: string) {
      const index = shoppingListPage.localLabels.value.findIndex(setting => setting.labelId === labelId);
      if (index < 0) return;
      routeAnnouncement.value = i18n.t("shopping-list.aisle-position", {
        name: shoppingListPage.localLabels.value[index].label.name,
        position: index + 1,
        total: shoppingListPage.localLabels.value.length,
      });
    }

    function moveAisle(labelId: string, direction: -1 | 1) {
      shoppingListPage.moveLabelOrder(labelId, direction);
      announceAisle(labelId);
    }

    function suggestAisleOrder() {
      shoppingListPage.suggestLabelOrder();
      routeAnnouncement.value = i18n.t("shopping-list.aisle-order-suggested");
    }

    function announceRouteDrag(event: { item: HTMLElement }) {
      const labelId = event.item.dataset.labelId;
      if (labelId) announceAisle(labelId);
      nextTick(() => event.item.querySelector<HTMLButtonElement>(".shopping-label-drag")?.focus());
    }

    watch(shoppingListPage.reorderLabelsDialog, () => {
      routeAnnouncement.value = "";
    });
    const { store: allLabels } = useLabelStore();
    const { store: allUnits } = useUnitStore();
    const { store: allFoods } = useFoodStore();

    return {
      groupSlug,
      preferences,
      allLabels,
      allUnits,
      allFoods,
      getTextColor,
      ...shoppingListPage,
      routeAnnouncement,
      moveAisle,
      suggestAisleOrder,
      announceRouteDrag,
    };
  },
});
</script>

<style scoped>
.shopping-detail {
  max-width: 960px;
}

.shopping-detail-navigation {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.shopping-label-order {
  max-height: 60vh;
  overflow-y: auto;
}

.shopping-route-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}

.route-announcement {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.shopping-progress {
  flex: 1;
  min-width: 160px;
  max-width: 400px;
  align-self: center;
}

.shopping-progress .v-progress-linear {
  margin-top: 8px;
}

.shopping-items-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 16px;
  text-align: center;
  border-block: 1px solid rgba(var(--v-theme-on-background), 0.12);
}

.shopping-items-empty h2 {
  font-size: 1.125rem;
  font-weight: 600;
}

.shopping-item-row {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.shopping-detail :deep(.v-btn:not(.v-btn--icon)) {
  min-height: 44px;
  border-radius: 6px;
  letter-spacing: 0;
}

.shopping-detail :deep(.v-expansion-panel) {
  border-radius: 6px;
}

.number-input-container {
  max-width: 50px;
}

.shopping-list-section {
  .section-title {
    font-size: 1rem;
    min-height: 48px !important;
  }

  :deep(.v-expansion-panel-text__wrapper) {
    padding: 0;
  }
}
</style>
