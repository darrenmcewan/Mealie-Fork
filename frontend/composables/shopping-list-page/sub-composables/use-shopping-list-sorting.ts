import type { ShoppingListOut, ShoppingListItemOut, ShoppingListMultiPurposeLabelOut } from "~/lib/api/types/household";

export interface ShoppingListSection {
  key: string;
  labelId: string | null;
  name: string;
  color?: string | null;
  items: ShoppingListItemOut[];
}

export function sortLabelSettings(settings: readonly ShoppingListMultiPurposeLabelOut[]) {
  return [...settings].sort((first, second) => (first.position ?? 0) - (second.position ?? 0)
    || (first.labelId < second.labelId ? -1 : first.labelId > second.labelId ? 1 : 0));
}

const aisleRanks = new Map([
  ["produce", 0], ["fruits", 0], ["vegetables", 0],
  ["baked goods", 1], ["grains", 1],
  ["canned goods", 2], ["condiments", 2], ["confectionary", 2], ["health foods", 2], ["snacks", 2], ["spices", 2], ["sweets", 2],
  ["beverages", 3], ["alcohol", 3],
  ["household", 4], ["other", 4],
  ["meat", 6], ["meat products", 6], ["seafood", 6],
  ["dairy products", 7], ["frozen foods", 8],
]);

export function suggestLabelOrder(settings: readonly ShoppingListMultiPurposeLabelOut[]): ShoppingListMultiPurposeLabelOut[] {
  return settings.map((setting, index) => ({
    setting,
    index,
    rank: aisleRanks.get(setting.label.name.normalize("NFKC").trim().replace(/\s+/g, " ").toLowerCase()) ?? 5,
  }))
    .sort((first, second) => first.rank - second.rank || first.index - second.index)
    .map(({ setting }, position) => ({ ...setting, label: { ...setting.label }, position }));
}

export function buildShoppingListSections(shoppingList: ShoppingListOut, noLabelName: string, unknownLabelName: string): ShoppingListSection[] {
  const settings = sortLabelSettings(shoppingList.labelSettings || []);
  const labels = new Map(settings.map(setting => [setting.labelId, setting.label]));
  const sections = new Map<string, ShoppingListSection>();

  for (const item of shoppingList.listItems || []) {
    if (item.checked) continue;
    const labelId = item.labelId || item.label?.id || null;
    const key = labelId ? `label:${labelId}` : "unlabeled";
    let section = sections.get(key);
    if (!section) {
      const label = item.label || (labelId ? labels.get(labelId) : undefined);
      section = { key, labelId, name: labelId ? label?.name || unknownLabelName : noLabelName, color: label?.color, items: [] };
      sections.set(key, section);
    }
    section.items.push(item);
  }

  const ordered: ShoppingListSection[] = [];
  function append(key: string) {
    const section = sections.get(key);
    if (section) {
      ordered.push(section);
      sections.delete(key);
    }
  }
  append("unlabeled");
  settings.forEach(setting => append(`label:${setting.labelId}`));
  [...sections.keys()].sort().forEach(append);
  return ordered;
}

interface ListItemGroup {
  position: number;
  createdAt: string;
  items: ShoppingListItemOut[];
}

/**
 * Composable for managing shopping list item sorting and organization
 */
export function useShoppingListSorting() {
  const { t } = useI18n();

  function sortItems(a: ShoppingListItemOut | ListItemGroup, b: ShoppingListItemOut | ListItemGroup) {
    // Sort by position ASC, then by createdAt ASC
    const posA = a.position ?? 0;
    const posB = b.position ?? 0;
    if (posA !== posB) {
      return posA - posB;
    }
    const createdA = a.createdAt ?? "";
    const createdB = b.createdAt ?? "";
    if (createdA !== createdB) {
      return createdA < createdB ? -1 : 1;
    }
    return 0;
  }

  function groupAndSortListItemsByFood(shoppingList: ShoppingListOut) {
    if (!shoppingList?.listItems?.length) {
      return;
    }

    const checkedItemKey = "__checkedItem";
    const listItemGroupsMap = new Map<string, ListItemGroup>();
    listItemGroupsMap.set(checkedItemKey, { position: Number.MAX_SAFE_INTEGER, createdAt: "", items: [] });

    // group items by checked status, food, or note
    shoppingList.listItems.forEach((item) => {
      const key = item.checked
        ? checkedItemKey
        : item.food?.name
          ? item.food.name
          : item.note || "";

      const group = listItemGroupsMap.get(key);
      if (!group) {
        listItemGroupsMap.set(key, { position: item.position || 0, createdAt: item.createdAt || "", items: [item] });
      }
      else {
        group.items.push(item);
      }
    });

    const listItemGroups = Array.from(listItemGroupsMap.values());
    listItemGroups.sort(sortItems);

    // sort group items, then aggregate them
    const sortedItems: ShoppingListItemOut[] = [];
    let nextPosition = 0;
    listItemGroups.forEach((listItemGroup) => {
      listItemGroup.items.sort(sortItems);
      listItemGroup.items.forEach((item) => {
        item.position = nextPosition;
        nextPosition += 1;
        sortedItems.push(item);
      });
    });

    shoppingList.listItems = sortedItems;
  }

  function sortListItems(shoppingList: ShoppingListOut) {
    if (!shoppingList?.listItems?.length) {
      return;
    }

    shoppingList.listItems.sort(sortItems);
  }

  function updateItemsByLabel(shoppingList: ShoppingListOut) {
    return buildShoppingListSections(shoppingList, t("shopping-list.no-label"), t("shopping-list.unknown-label"));
  }

  return {
    sortItems,
    groupAndSortListItemsByFood,
    sortListItems,
    updateItemsByLabel,
  };
}
