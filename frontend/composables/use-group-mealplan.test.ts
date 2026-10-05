import { ref } from "vue";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useMealplans } from "./use-group-mealplan";
import { MealPlanAPI } from "~/lib/api/user/group-mealplan";
import type { ApiRequestInstance } from "~/lib/api/types/non-generated";

const mocks = vi.hoisted(() => ({
    getAll: vi.fn(), createOne: vi.fn(), updateOne: vi.fn(), deleteOne: vi.fn(), getLeftovers: vi.fn(),
}));
vi.mock("~/composables/api", () => ({ useUserApi: () => ({ mealplans: mocks }) }));
vi.mock("./use-utils", () => ({ useAsyncKey: () => "mealplan-test" }));

beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("useAsyncData", () => ({ data: ref([]) }));
    mocks.getAll.mockResolvedValue({ data: { items: [] } });
});

function planner() {
    return useMealplans(ref({ start: new Date(2026, 9, 5), end: new Date(2026, 9, 11) }));
}

describe("meal-plan mutations", () => {
    test("omits absent editing IDs from discovery queries", async () => {
        const get = vi.fn().mockResolvedValue({ data: { items: [] } });
        const api = new MealPlanAPI({ get } as unknown as ApiRequestInstance, "", () => "");
        await api.getLeftovers("2026-10-06");
        const request = new URL(get.mock.calls[0][0], "http://localhost");
        expect(request.searchParams.get("target_date")).toBe("2026-10-06");
        expect(request.searchParams.has("editing_entry_id")).toBe(false);
        await api.getLeftovers("2026-10-06", 2);
        expect(new URL(get.mock.calls[1][0], "http://localhost").searchParams.get("editing_entry_id")).toBe("2");
        await api.getLeftovers("2026-10-06", 2, 1, 20, 42);
        expect(new URL(get.mock.calls[2][0], "http://localhost").searchParams.get("queryFilter")).toBe("id = 42");
    });

    test("awaits a successful save and calendar refresh", async () => {
        let finishRefresh: (value: unknown) => void = () => { };
        mocks.getAll.mockImplementation(() => new Promise((resolve) => {
            finishRefresh = resolve;
        }));
        mocks.createOne.mockResolvedValue({ data: { id: 1 } });
        const state = planner();
        let finished = false;
        const saving = state.actions.createOne({ date: "2026-10-05", title: "Dinner" }).then((success) => {
            finished = true;
            return success;
        });
        await Promise.resolve();
        expect(finished).toBe(false);
        finishRefresh({ data: { items: [{ id: 1 }] } });
        expect(await saving).toBe(true);
        expect(state.loading.value).toBe(false);
        expect(state.allocationVersion.value).toBe(1);
    });

    test("retains conflict details and refreshes saved state", async () => {
        mocks.createOne.mockResolvedValue({ data: null, error: { response: { data: { detail: { message: "Not enough portions", mealIds: [2] } } } } });
        const state = planner();
        expect(await state.actions.createOne({ date: "2026-10-06", title: "Lunch" })).toBe(false);
        expect(state.lastError.value).toEqual({ message: "Not enough portions", mealIds: [2] });
        expect(mocks.getAll).toHaveBeenCalledOnce();
        expect(state.loading.value).toBe(false);
    });

    test("preserves linked metadata without mutating the supplied meal", async () => {
        mocks.updateOne.mockResolvedValue({ data: { id: 2 } });
        const state = planner();
        const entry = { id: 2, date: "2026-10-06", title: "Lunch", groupId: "group", userId: "user", entryType: "lunch" as const, leftoverSourceId: 1, eatenPortions: 2 };
        expect(await state.actions.setType(entry, "dinner")).toBe(true);
        expect(mocks.updateOne).toHaveBeenCalledWith(2, { ...entry, entryType: "dinner" });
        expect(entry.entryType).toBe("lunch");
    });

    test("cleans up loading and returns failure after a thrown request", async () => {
        mocks.deleteOne.mockRejectedValue(new Error("Offline"));
        const state = planner();
        expect(await state.actions.deleteOne(2)).toBe(false);
        expect(state.loading.value).toBe(false);
        expect(state.lastError.value).not.toBeNull();
        expect(state.allocationVersion.value).toBe(1);
    });
});
