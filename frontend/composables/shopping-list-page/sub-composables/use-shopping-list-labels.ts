import { useToggle } from "@vueuse/core";
import type { ShoppingListSection } from "./use-shopping-list-sorting";

/**
 * Composable for managing shopping list label state and operations
 */
export function useShoppingListLabels(sections: Ref<ShoppingListSection[]>) {
  const labelOpenState = ref<{ [key: string]: boolean }>({});
  const [showChecked, toggleShowChecked] = useToggle(false);

  const initializeLabelOpenStates = () => {
    const existingLabels = new Set(Object.keys(labelOpenState.value));
    let hasChanges = false;

    for (const section of sections.value) {
      if (!existingLabels.has(section.key)) {
        labelOpenState.value[section.key] = true;
        hasChanges = true;
      }
    }

    if (hasChanges) {
      labelOpenState.value = { ...labelOpenState.value };
    }
  };

  const labelKeys = computed(() => sections.value.map(section => section.key));
  watch(labelKeys, initializeLabelOpenStates, { immediate: true });

  function toggleShowLabel(key: string) {
    labelOpenState.value[key] = !labelOpenState.value[key];
  }

  function getLabelColor(key: string) {
    return sections.value.find(section => section.key === key)?.color;
  }

  const presentLabels = computed(() => sections.value.flatMap(section => section.labelId ? [{ id: section.labelId, name: section.name }] : []));

  return {
    labelOpenState,
    showChecked,
    toggleShowChecked,
    toggleShowLabel,
    getLabelColor,
    presentLabels,
    initializeLabelOpenStates,
  };
}
