import { afterEach, describe, expect, test, vi } from "vitest";
import { buildShoppingListSections, useShoppingListSorting } from "./use-shopping-list-sorting";
import * as sorting from "./use-shopping-list-sorting";
import type { ShoppingListItemOut, ShoppingListMultiPurposeLabelOut, ShoppingListOut } from "~/lib/api/types/household";

function setting(labelId: string, name: string, position: number): ShoppingListMultiPurposeLabelOut {
    return { id: `setting-${labelId}`, shoppingListId: "list", labelId, position, label: { id: labelId, name, color: "#123456" } };
}

function item(id: string, labelId: string | null, name?: string): ShoppingListItemOut {
    return {
        id, shoppingListId: "list", groupId: "group", householdId: "household", labelId, position: 7,
        label: labelId && name ? { id: labelId, name, color: "#123456" } : null,
    };
}

afterEach(() => vi.unstubAllGlobals());

describe("shopping aisle sections", () => {
    test("follows saved positions and retains every unchecked item by label identity without mutation", () => {
        vi.stubGlobal("useI18n", () => ({ t: (key: string) => key === "shopping-list.no-label" ? "No Label" : "Unknown Label" }));
        const shoppingList = {
            labelSettings: [setting("second", "2", 3), setting("first", "10", 0), setting("same-b", "Same", 2), setting("same-a", "Same", 1), setting("empty", "Empty", 4)],
            listItems: [item("one", "first", "10"), item("two", "second", "2"), item("three", "same-a", "Same"), item("four", "same-b", "Same"), item("five", "missing", "Custom"), item("six", null), item("seven", "unresolved"), { ...item("checked", "first", "10"), checked: true }],
        } as ShoppingListOut;
        const original = JSON.stringify(shoppingList);
        shoppingList.labelSettings?.forEach(value => Object.freeze(value));
        shoppingList.listItems?.forEach(value => Object.freeze(value));
        Object.freeze(shoppingList.labelSettings);
        Object.freeze(shoppingList.listItems);

        const sections = useShoppingListSorting().updateItemsByLabel(shoppingList);

        expect(sections).toEqual([
            expect.objectContaining({ key: "unlabeled", name: "No Label", items: [shoppingList.listItems![5]] }),
            expect.objectContaining({ key: "label:first", name: "10", items: [shoppingList.listItems![0]] }),
            expect.objectContaining({ key: "label:same-a", name: "Same", items: [shoppingList.listItems![2]] }),
            expect.objectContaining({ key: "label:same-b", name: "Same", items: [shoppingList.listItems![3]] }),
            expect.objectContaining({ key: "label:second", name: "2", items: [shoppingList.listItems![1]] }),
            expect.objectContaining({ key: "label:missing", name: "Custom", items: [shoppingList.listItems![4]] }),
            expect.objectContaining({ key: "label:unresolved", name: "Unknown Label", items: [shoppingList.listItems![6]] }),
        ]);
        expect(JSON.stringify(shoppingList)).toBe(original);
    });

    test("breaks position ties by identity and preserves item order and settings-only label details", () => {
        const shoppingList = {
            labelSettings: [setting("b", "Second", 0), setting("a", "First", 0)],
            listItems: [item("later", "a"), item("earlier", "a"), item("other", "b")],
        } as ShoppingListOut;
        expect(buildShoppingListSections(shoppingList, "No Label", "Unknown").map(section => [section.key, section.name, section.items.map(value => value.id)]))
            .toEqual([["label:a", "First", ["later", "earlier"]], ["label:b", "Second", ["other"]]]);
        expect(buildShoppingListSections({ labelSettings: [], listItems: [] } as unknown as ShoppingListOut, "No Label", "Unknown")).toEqual([]);
    });
});

describe("suggested aisle route", () => {
    test("suggests produce before ambient goods and custom aisles before chilled goods without mutating the draft", () => {
        const draft = [setting("frozen", "Frozen Foods", 0), setting("dairy", "Dairy Products", 1), setting("custom", "Custom Aisle", 2), setting("produce", "Produce", 3), setting("pantry", "Canned Goods", 4)];
        const original = JSON.stringify(draft);
        draft.forEach(value => Object.freeze(value));
        Object.freeze(draft);
        const suggested = sorting.suggestLabelOrder(draft);
        expect(suggested.map(value => value.labelId)).toEqual(["produce", "pantry", "custom", "dairy", "frozen"]);
        expect(suggested.map(value => value.position)).toEqual([0, 1, 2, 3, 4]);
        expect(JSON.stringify(draft)).toBe(original);
        expect(sorting.suggestLabelOrder(suggested)).toEqual(suggested);
    });

    test("recognizes every English seed family while keeping the input order within each family", () => {
        const names = ["Frozen Foods", "Dairy Products", "Meat Products", "Seafood", "Meat", "Other", "Household", "Alcohol", "Beverages", "Baked Goods", "Grains", "Vegetables", "Fruits", "Produce", "Spices", "Sweets", "Snacks", "Health Foods", "Confectionary", "Condiments", "Canned Goods"];
        const suggested = sorting.suggestLabelOrder(names.map((name, index) => setting(String(index), name, index)));
        expect(suggested.map(value => value.label.name)).toEqual(["Vegetables", "Fruits", "Produce", "Baked Goods", "Grains", "Spices", "Sweets", "Snacks", "Health Foods", "Confectionary", "Condiments", "Canned Goods", "Alcohol", "Beverages", "Other", "Household", "Meat Products", "Seafood", "Meat", "Dairy Products", "Frozen Foods"]);
        expect(new Set(suggested.map(value => value.labelId)).size).toBe(21);
    });

    test("normalizes exact names but retains custom and non-English labels in stable fallback order", () => {
        const draft = [setting("cold", "  frozen   FOODS  ", 0), setting("custom", "Frozen Foods Budget", 1), setting("other-language", "Obst", 2), setting("produce", "PRODUCE", 3), setting("meat", "Meat", 4)];
        expect(sorting.suggestLabelOrder(draft).map(value => value.labelId)).toEqual(["produce", "custom", "other-language", "meat", "cold"]);
        expect(draft[0].label.name).toBe("  frozen   FOODS  ");
        expect(sorting.suggestLabelOrder([])).toEqual([]);
    });
});
