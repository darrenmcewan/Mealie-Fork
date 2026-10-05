import { computed, nextTick, ref, watch } from "vue";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { useShoppingListCrud } from "./use-shopping-list-crud";
import { useShoppingListLabels } from "./use-shopping-list-labels";
import type { ShoppingListSection } from "./use-shopping-list-sorting";
import type { ShoppingListOut } from "~/lib/api/types/household";

const { updateLabelSettings } = vi.hoisted(() => ({ updateLabelSettings: vi.fn() }));
vi.mock("~/composables/api", () => ({ useUserApi: () => ({ shopping: { lists: { updateLabelSettings } } }) }));
vi.mock("~/composables/use-utils", () => ({ uuid4: () => "new-item" }));

function createEditor(isOffline = ref(false)) {
    const shoppingList = ref({
        id: "list", groupId: "group", userId: "user", householdId: "household", recipeReferences: [],
        listItems: [{ id: "item", shoppingListId: "list", groupId: "group", householdId: "household", labelId: "produce", quantity: 2, position: 9, recipeReferences: [] }],
        labelSettings: [
            { id: "setting-frozen", shoppingListId: "list", labelId: "frozen", position: 0, label: { id: "frozen", name: "Frozen Foods" } },
            { id: "setting-produce", shoppingListId: "list", labelId: "produce", position: 1, label: { id: "produce", name: "Produce" } },
        ],
    } as ShoppingListOut);
    const loading = ref(0);
    const refresh = vi.fn();
    const updateItem = vi.fn();
    const rebuild = vi.fn();
    const editor = useShoppingListCrud(shoppingList, loading, { unchecked: [], checked: [] }, { updateItem }, refresh, () => 0, rebuild, isOffline);
    return { editor, shoppingList, loading, refresh, updateItem, rebuild };
}

beforeEach(() => {
    vi.stubGlobal("ref", ref);
    vi.stubGlobal("computed", computed);
    vi.stubGlobal("watch", watch);
    vi.stubGlobal("useI18n", () => ({ t: (key: string) => key }));
    updateLabelSettings.mockReset();
});
afterEach(() => vi.unstubAllGlobals());

describe("aisle order draft", () => {
    test("cancel discards draft positions without changing the saved route", () => {
        const { editor, shoppingList, loading } = createEditor();
        const original = JSON.stringify(shoppingList.value);
        editor.toggleReorderLabelsDialog();
        editor.updateLabelOrder([...editor.localLabels.value!].reverse());
        expect(JSON.stringify(shoppingList.value)).toBe(original);
        editor.cancelLabelOrder();
        expect(JSON.stringify(shoppingList.value)).toBe(original);
        expect(loading.value).toBe(0);
        expect(updateLabelSettings).not.toHaveBeenCalled();
    });

    test("blocks dismissal while saving and adopts only the server-confirmed route without item writes", async () => {
        const { editor, shoppingList, loading, refresh, updateItem, rebuild } = createEditor();
        const originalItems = JSON.stringify(shoppingList.value.listItems);
        let completeSave: (response: { data: ShoppingListOut }) => void = () => { };
        updateLabelSettings.mockReturnValueOnce(new Promise<{ data: ShoppingListOut }>((resolve) => {
            completeSave = resolve;
        }));
        editor.toggleReorderLabelsDialog();
        editor.suggestLabelOrder();
        const confirmed = { ...shoppingList.value, labelSettings: [...editor.localLabels.value] };
        const saving = editor.saveLabelOrder(rebuild);
        expect(editor.labelOrderSaving.value).toBe(true);
        expect(loading.value).toBe(2);
        editor.cancelLabelOrder();
        editor.reorderLabelsDialog.value = false;
        expect(editor.reorderLabelsDialog.value).toBe(true);
        expect(shoppingList.value.labelSettings?.[0].labelId).toBe("frozen");
        completeSave({ data: confirmed });
        await saving;
        expect(shoppingList.value.labelSettings?.map(setting => setting.labelId)).toEqual(["produce", "frozen"]);
        expect(editor.reorderLabelsDialog.value).toBe(false);
        expect(loading.value).toBe(0);
        expect(rebuild).toHaveBeenCalledOnce();
        expect(refresh).toHaveBeenCalledOnce();
        expect(updateItem).not.toHaveBeenCalled();
        expect(JSON.stringify(shoppingList.value.listItems)).toBe(originalItems);
        expect(updateLabelSettings).toHaveBeenCalledWith("list", [
            { id: "setting-produce", shoppingListId: "list", labelId: "produce", position: 0 },
            { id: "setting-frozen", shoppingListId: "list", labelId: "frozen", position: 1 },
        ]);
    });

    test("reopening restores saved order and reversing a move restores unchanged state", async () => {
        const { editor, loading, refresh, shoppingList } = createEditor();
        editor.toggleReorderLabelsDialog();
        expect(editor.localLabels.value[0]).not.toBe(shoppingList.value.labelSettings![0]);
        expect(editor.localLabels.value[0].label).not.toBe(shoppingList.value.labelSettings![0].label);
        editor.moveLabelOrder("frozen", -1);
        expect(editor.labelOrderChanged.value).toBe(false);
        editor.moveLabelOrder("frozen", 1);
        expect(editor.labelOrderChanged.value).toBe(true);
        editor.moveLabelOrder("frozen", -1);
        expect(editor.labelOrderChanged.value).toBe(false);
        await editor.saveLabelOrder(vi.fn());
        expect(updateLabelSettings).not.toHaveBeenCalled();
        editor.suggestLabelOrder();
        editor.reorderLabelsDialog.value = false;
        editor.cancelLabelOrder();
        expect(loading.value).toBe(0);
        expect(refresh).toHaveBeenCalledOnce();
        editor.toggleReorderLabelsDialog();
        expect(editor.localLabels.value.map(setting => setting.labelId)).toEqual(["frozen", "produce"]);
        editor.cancelLabelOrder();
    });

    test.each(["throw", "empty", "denied"])("retains the draft after %s failure and permits retry without leaking polling state", async (failure) => {
        const { editor, shoppingList, loading, rebuild } = createEditor();
        const original = JSON.stringify(shoppingList.value);
        editor.toggleReorderLabelsDialog();
        editor.suggestLabelOrder();
        if (failure === "throw") updateLabelSettings.mockRejectedValueOnce(new Error("Connection failed"));
        else if (failure === "denied") updateLabelSettings.mockResolvedValueOnce({ data: null, error: { status: 403 } });
        else updateLabelSettings.mockResolvedValueOnce(undefined);
        expect(await editor.saveLabelOrder(rebuild)).toBe(false);
        expect(JSON.stringify(shoppingList.value)).toBe(original);
        expect(editor.labelOrderError.value).toBe("shopping-list.aisle-order-save-error");
        expect(editor.reorderLabelsDialog.value).toBe(true);
        expect(editor.localLabels.value.map(setting => setting.labelId)).toEqual(["produce", "frozen"]);
        expect(editor.labelOrderSaving.value).toBe(false);
        expect(loading.value).toBe(1);
        updateLabelSettings.mockResolvedValueOnce({ data: { ...shoppingList.value, labelSettings: [...editor.localLabels.value] } });
        expect(await editor.saveLabelOrder(rebuild)).toBe(true);
        expect(loading.value).toBe(0);
        expect(editor.labelOrderError.value).toBe("");
    });

    test("offline and duplicate pending saves send no additional request", async () => {
        const offline = ref(true);
        const { editor, shoppingList, loading, rebuild } = createEditor(offline);
        editor.toggleReorderLabelsDialog();
        editor.suggestLabelOrder();
        expect(await editor.saveLabelOrder(rebuild)).toBe(false);
        expect(updateLabelSettings).not.toHaveBeenCalled();
        offline.value = false;
        let completeSave: (response: { data: ShoppingListOut }) => void = () => { };
        updateLabelSettings.mockReturnValueOnce(new Promise<{ data: ShoppingListOut }>((resolve) => {
            completeSave = resolve;
        }));
        const saving = editor.saveLabelOrder(rebuild);
        expect(await editor.saveLabelOrder(rebuild)).toBe(false);
        expect(updateLabelSettings).toHaveBeenCalledOnce();
        completeSave({ data: { ...shoppingList.value, labelSettings: [...editor.localLabels.value] } });
        await saving;
        expect(loading.value).toBe(0);
    });

    test("unmount releases both pause contributions once and does not adopt a late response", async () => {
        const { editor, shoppingList, loading, refresh, rebuild } = createEditor();
        const original = JSON.stringify(shoppingList.value);
        editor.toggleReorderLabelsDialog();
        editor.suggestLabelOrder();
        const confirmed = { ...shoppingList.value, labelSettings: [...editor.localLabels.value] };
        let completeSave: (response: { data: ShoppingListOut }) => void = () => { };
        updateLabelSettings.mockReturnValueOnce(new Promise<{ data: ShoppingListOut }>((resolve) => {
            completeSave = resolve;
        }));
        const saving = editor.saveLabelOrder(rebuild);
        editor.disposeLabelOrder();
        editor.disposeLabelOrder();
        expect(loading.value).toBe(0);
        completeSave({ data: confirmed });
        await saving;
        expect(loading.value).toBe(0);
        expect(JSON.stringify(shoppingList.value)).toBe(original);
        expect(rebuild).not.toHaveBeenCalled();
        expect(refresh).not.toHaveBeenCalled();
    });
});

describe("label presentation identity", () => {
    test("equal display names retain independent colors and open state across renaming", async () => {
        const sections = ref<ShoppingListSection[]>([
            { key: "label:a", labelId: "a", name: "Same", color: "red", items: [] },
            { key: "label:b", labelId: "b", name: "Same", color: "green", items: [] },
        ]);
        const labels = useShoppingListLabels(sections);
        labels.toggleShowLabel("label:a");
        sections.value[0].name = "Renamed";
        await nextTick();
        expect(labels.labelOpenState.value).toEqual({ "label:a": false, "label:b": true });
        expect(labels.getLabelColor("label:a")).toBe("red");
        expect(labels.getLabelColor("label:b")).toBe("green");
    });
});
