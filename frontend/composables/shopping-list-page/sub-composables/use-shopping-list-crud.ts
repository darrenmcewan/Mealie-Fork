import type { ShoppingListOut, ShoppingListItemOut, ShoppingListMultiPurposeLabelOut } from "~/lib/api/types/household";
import { useUserApi } from "~/composables/api";
import { uuid4 } from "~/composables/use-utils";
import { sortLabelSettings, suggestLabelOrder as getSuggestedLabelOrder } from "./use-shopping-list-sorting";

/**
 * Composable for managing shopping list item CRUD operations
 */
export function useShoppingListCrud(
  shoppingList: Ref<ShoppingListOut | null>,
  loadingCounter: Ref<number>,
  listItems: { unchecked: ShoppingListItemOut[]; checked: ShoppingListItemOut[] },
  shoppingListItemActions: any,
  refresh: () => void,
  sortCheckedItems: (a: ShoppingListItemOut, b: ShoppingListItemOut) => number,
  updateListItemOrder: () => void,
  isOffline: Ref<boolean> = ref(false),
) {
  const { t } = useI18n();
  const userApi = useUserApi();

  const createListItemData = ref<ShoppingListItemOut>(listItemFactory());
  const localLabels = ref<ShoppingListMultiPurposeLabelOut[]>([]);
  const labelEditorOpen = ref(false);
  const labelOrderSaving = ref(false);
  const labelOrderError = ref("");
  let originalLabelIds: string[] = [];
  let savePause = false;
  let disposed = false;
  const labelOrderChanged = computed(() => labelEditorOpen.value
    && localLabels.value.some((setting, index) => setting.labelId !== originalLabelIds[index]));
  const reorderLabelsDialog = computed({
    get: () => labelEditorOpen.value,
    set: (open: boolean) => {
      if (open && !labelEditorOpen.value) toggleReorderLabelsDialog();
      else if (!open) cancelLabelOrder();
    },
  });

  function listItemFactory(): ShoppingListItemOut {
    return {
      id: uuid4(),
      shoppingListId: shoppingList.value?.id || "",
      checked: false,
      position: shoppingList.value?.listItems?.length || 1,
      quantity: 0,
      note: "",
      labelId: undefined,
      unitId: undefined,
      foodId: undefined,
    } as ShoppingListItemOut;
  }

  // Check/Uncheck All operations
  function checkAllItems() {
    let hasChanged = false;
    shoppingList.value?.listItems?.forEach((item) => {
      if (!item.checked) {
        hasChanged = true;
        item.checked = true;
      }
    });
    if (hasChanged) {
      updateUncheckedListItems();
    }
  }

  function uncheckAllItems() {
    let hasChanged = false;
    shoppingList.value?.listItems?.forEach((item) => {
      if (item.checked) {
        hasChanged = true;
        item.checked = false;
      }
    });
    if (hasChanged) {
      listItems.unchecked = [...listItems.unchecked, ...listItems.checked];
      listItems.checked = [];
      updateUncheckedListItems();
    }
  }

  function deleteCheckedItems() {
    const checked = shoppingList.value?.listItems?.filter(item => item.checked);

    if (!checked || checked?.length === 0) {
      return;
    }

    loadingCounter.value += 1;
    deleteListItems(checked);
    loadingCounter.value -= 1;
    refresh();
  }

  function saveListItem(item: ShoppingListItemOut) {
    if (!shoppingList.value) {
      return;
    }

    // set a temporary updatedAt timestamp prior to refresh so it appears at the top of the checked items
    item.updatedAt = new Date().toISOString();

    // make updates reflect immediately
    if (shoppingList.value.listItems) {
      shoppingList.value.listItems.forEach((oldListItem: ShoppingListItemOut, idx: number) => {
        if (oldListItem.id === item.id && shoppingList.value?.listItems) {
          shoppingList.value.listItems[idx] = item;
        }
      });
      // Immediately update checked/unchecked arrays for UI
      listItems.unchecked = shoppingList.value.listItems.filter(i => !i.checked);
      listItems.checked = shoppingList.value.listItems.filter(i => i.checked)
        .sort(sortCheckedItems);
    }

    shoppingListItemActions.updateItem(item);
    updateListItemOrder();
  }

  function deleteListItem(item: ShoppingListItemOut) {
    if (!shoppingList.value) {
      return;
    }

    shoppingListItemActions.deleteItem(item);

    // remove the item from the list immediately so the user sees the change
    if (shoppingList.value.listItems) {
      shoppingList.value.listItems = shoppingList.value.listItems.filter(itm => itm.id !== item.id);
    }

    refresh();
  }

  function deleteListItems(items: ShoppingListItemOut[]) {
    if (!shoppingList.value) {
      return;
    }

    items.forEach((item) => {
      shoppingListItemActions.deleteItem(item);
    });
    // remove the items from the list immediately so the user sees the change
    if (shoppingList.value?.listItems) {
      const deletedItems = new Set(items.map(item => item.id));
      shoppingList.value.listItems = shoppingList.value.listItems.filter(itm => !deletedItems.has(itm.id));
    }

    refresh();
  }

  function createListItem() {
    if (!shoppingList.value) {
      return;
    }

    if (!createListItemData.value.foodId && !createListItemData.value.note) {
      // don't create an empty item
      return;
    }

    loadingCounter.value += 1;

    // ensure list id is set to the current list, which may not have loaded yet in the factory
    createListItemData.value.shoppingListId = shoppingList.value.id;

    // ensure item is inserted into the end of the list, which may have been updated
    createListItemData.value.position = shoppingList.value?.listItems?.length
      ? (shoppingList.value.listItems.reduce((a, b) => (a.position || 0) > (b.position || 0) ? a : b).position || 0) + 1
      : 0;

    createListItemData.value.createdAt = new Date().toISOString();
    createListItemData.value.updatedAt = createListItemData.value.createdAt;

    updateListItemOrder();

    shoppingListItemActions.createItem(createListItemData.value);
    loadingCounter.value -= 1;

    if (shoppingList.value.listItems) {
      // add the item to the list immediately so the user sees the change
      shoppingList.value.listItems.push(createListItemData.value);
      updateListItemOrder();
    }
    createListItemData.value = listItemFactory();
    refresh();
  }

  function updateUncheckedListItems() {
    if (!shoppingList.value?.listItems) {
      return;
    }

    // Set position for unchecked items
    listItems.unchecked.forEach((item: ShoppingListItemOut, idx: number) => {
      item.position = idx;
      shoppingListItemActions.updateItem(item);
    });

    refresh();
  }

  // Label management
  function updateLabelOrder(labelSettings: ShoppingListMultiPurposeLabelOut[]) {
    if (!labelEditorOpen.value || labelOrderSaving.value) {
      return;
    }

    localLabels.value = labelSettings.map((setting, position) => ({ ...setting, label: { ...setting.label }, position }));
  }

  function cancelLabelOrder() {
    if (!labelEditorOpen.value || labelOrderSaving.value) return;
    finishLabelOrder();
  }

  function finishLabelOrder(refreshList = true) {
    if (!labelEditorOpen.value) return;
    labelEditorOpen.value = false;
    localLabels.value = [];
    labelOrderError.value = "";
    loadingCounter.value -= 1;
    if (refreshList) refresh();
  }

  function releaseSavePause() {
    if (!savePause) return;
    savePause = false;
    loadingCounter.value -= 1;
  }

  function disposeLabelOrder() {
    disposed = true;
    releaseSavePause();
    labelOrderSaving.value = false;
    finishLabelOrder(false);
  }

  function moveLabelOrder(labelId: string, direction: -1 | 1) {
    const index = localLabels.value.findIndex(setting => setting.labelId === labelId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= localLabels.value.length) return;
    const settings = [...localLabels.value];
    [settings[index], settings[target]] = [settings[target], settings[index]];
    updateLabelOrder(settings);
  }

  function suggestLabelOrder() {
    updateLabelOrder(getSuggestedLabelOrder(localLabels.value));
  }

  async function saveLabelOrder(updateItemsByLabel: () => void) {
    if (disposed || !shoppingList.value || !labelOrderChanged.value || !localLabels.value.length || labelOrderSaving.value || isOffline.value) {
      return false;
    }

    labelOrderSaving.value = true;
    labelOrderError.value = "";
    savePause = true;
    loadingCounter.value += 1;
    let saved = false;
    try {
      const payload = localLabels.value.map(({ id, shoppingListId, labelId }, position) => ({ id, shoppingListId, labelId, position }));
      const response = await userApi.shopping.lists.updateLabelSettings(shoppingList.value.id, payload);
      if (disposed) return false;
      const data = response?.data as ShoppingListOut | undefined;
      if (!data || data.id !== shoppingList.value.id || !Array.isArray(data.labelSettings)) {
        labelOrderError.value = t("shopping-list.aisle-order-save-error");
        return false;
      }
      shoppingList.value.labelSettings = sortLabelSettings(data.labelSettings);
      updateItemsByLabel();
      saved = true;
      return true;
    }
    catch {
      if (!disposed) labelOrderError.value = t("shopping-list.aisle-order-save-error");
      return false;
    }
    finally {
      labelOrderSaving.value = false;
      releaseSavePause();
      if (saved) finishLabelOrder();
    }
  }

  function toggleReorderLabelsDialog() {
    if (labelEditorOpen.value) {
      cancelLabelOrder();
      return;
    }
    if (disposed || !shoppingList.value) return;
    localLabels.value = sortLabelSettings(shoppingList.value.labelSettings || []).map(setting => ({ ...setting, label: { ...setting.label } }));
    originalLabelIds = localLabels.value.map(setting => setting.labelId);
    labelOrderError.value = "";
    labelEditorOpen.value = true;
    loadingCounter.value += 1;
  }

  // Context menu actions
  const contextActions = {
    delete: "delete",
  };

  const contextMenu = [
    { title: t("general.delete"), action: contextActions.delete },
  ];

  return {
    createListItemData,
    localLabels,
    reorderLabelsDialog,
    labelOrderChanged,
    labelOrderSaving,
    labelOrderError,
    moveLabelOrder,
    suggestLabelOrder,
    disposeLabelOrder,
    listItemFactory,
    checkAllItems,
    uncheckAllItems,
    deleteCheckedItems,
    saveListItem,
    deleteListItem,
    deleteListItems,
    createListItem,
    updateUncheckedListItems,
    updateLabelOrder,
    cancelLabelOrder,
    saveLabelOrder,
    toggleReorderLabelsDialog,
    contextActions,
    contextMenu,
  };
}
