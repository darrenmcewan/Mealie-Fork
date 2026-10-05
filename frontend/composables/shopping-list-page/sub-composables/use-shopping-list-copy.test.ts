import { describe, expect, test, vi } from "vitest";
import { buildShoppingListSections } from "./use-shopping-list-sorting";
import { useShoppingListCopy } from "./use-shopping-list-copy";
import type { ShoppingListOut } from "~/lib/api/types/household";

const { copyPlain } = vi.hoisted(() => ({ copyPlain: vi.fn() }));
vi.mock("~/composables/use-copy", () => ({ useCopyList: () => ({ copyPlain }) }));

describe("copy the visible aisle route", () => {
    test.each(["plain", "markdown"] as const)("copies %s in visible order including repeated headings and fallback items", (format) => {
        const shoppingList = {
            labelSettings: [
                { labelId: "a", position: 0, label: { id: "a", name: "Same" } },
                { labelId: "b", position: 1, label: { id: "b", name: "Same" } },
            ],
            listItems: [
                { id: "one", labelId: "a", display: "Apples" },
                { id: "two", labelId: "b", display: "Bread" },
                { id: "three", labelId: null, display: "Bag" },
                { id: "four", labelId: "missing", label: { id: "missing", name: "Custom" }, display: "Soap" },
                { id: "five", labelId: "a", checked: true, display: "Checked" },
            ],
        } as ShoppingListOut;
        const sections = buildShoppingListSections(shoppingList, "No Label", "Unknown");
        useShoppingListCopy().copyListItems(sections, format);
        expect(copyPlain).toHaveBeenLastCalledWith(format === "plain"
            ? ["[No Label]", "Bag", "", "[Same]", "Apples", "", "[Same]", "Bread", "", "[Custom]", "Soap"]
            : ["# No Label", "- [ ] Bag", "", "# Same", "- [ ] Apples", "", "# Same", "- [ ] Bread", "", "# Custom", "- [ ] Soap"]);
    });
});
