import { describe, expect, test, vi } from "vitest";
import { ref } from "vue";
import { buildComparisonRows, comparisonDurationSeconds, createComparisonController, newComparisonState } from "./use-recipe-comparison";
import type { Recipe } from "~/lib/api/types/recipe";

function valueFor(id: string, recipe: Recipe) {
  return buildComparisonRows([recipe]).find(row => row.id === id)?.values[0];
}

describe("comparison rows", () => {
  test.each([undefined, null, "", "   "])("keeps missing preparation time missing: %s", (prepTime) => {
    expect(valueFor("prepTime", { prepTime })).toEqual({ text: null, state: "missing" });
  });

  test("preserves recorded text and never derives total time", () => {
    expect(valueFor("prepTime", { prepTime: " overnight " })?.text).toBe(" overnight ");
    expect(valueFor("totalTime", { prepTime: "30 minutes", performTime: "20 minutes" })?.state).toBe("missing");
  });

  test("keeps servings, yield quantity, and yield text separate", () => {
    const recipe: Recipe = { recipeServings: 4, recipeYieldQuantity: 12, recipeYield: "muffins" };
    expect(valueFor("servings", recipe)?.displayNumber).toBe(4);
    expect(valueFor("yieldQuantity", recipe)?.displayNumber).toBe(12);
    expect(valueFor("yield", recipe)?.text).toBe("muffins");
    expect(valueFor("servings", recipe)?.numeric).toBeUndefined();
  });

  test.each([0, -1, Number.NaN, Number.POSITIVE_INFINITY])("rejects invalid quantity %s", (recipeServings) => {
    expect(valueFor("servings", { recipeServings })?.state).toBe("missing");
  });

  test("keeps existing cooking time separate from additional stored cook time", () => {
    const recipe: Recipe = { performTime: "20 minutes", cookTime: "PT30M" };
    expect(valueFor("performTime", recipe)?.text).toBe("20 minutes");
    expect(valueFor("cookTime", recipe)?.text).toBe("PT30M");
    expect(buildComparisonRows([{ performTime: "20 minutes", cookTime: "20 minutes" }]).some(row => row.id === "cookTime")).toBe(false);
  });

  test("keeps selection order and unknown recipe values", () => {
    const row = buildComparisonRows([{ prepTime: "30 minutes" }, undefined, { prepTime: "1 hour" }])[0];
    expect(row.values.map(value => value.text)).toEqual(["30 minutes", null, "1 hour"]);
  });
});

describe("conservative duration comparison", () => {
  test.each([
    ["PT30M", 1800], ["1 hour", 3600], ["1 HOUR 30 minutes", 5400],
    ["PT1H30M15S", 5415], ["20 secs", 20], ["0.5 hours", 1800],
    ["PT0.5H", 1800], ["0 minutes", 0], ["PT0S", 0], ["1 hr 5 min 2 sec", 3902],
  ])("recognizes %s", (text, seconds) => {
    expect(comparisonDurationSeconds(text as string)).toBe(seconds);
  });

  test.each([
    "30", "overnight", "10-20 minutes", "1 day", "P1DT2H", "-2 hours",
    "Infinity minutes", "NaN seconds", "20 minutos", "PT", "1 hour 2 hours",
    "1,5 hours", "about 20 minutes", "20 minutes or 30 minutes", "PT-1H", "",
  ])("rejects %s", (text) => {
    expect(comparisonDurationSeconds(text)).toBeUndefined();
  });

  test("retains non-comparable text and distinguishes real zero", () => {
    expect(valueFor("prepTime", { prepTime: "overnight" })).toEqual({ text: "overnight", state: "not-comparable" });
    expect(valueFor("prepTime", { prepTime: "0 minutes" })?.numeric).toBe(0);
  });
});

describe("recorded ingredients and complexity counts", () => {
  test("counts substantive duplicate lines, not headings or quantity placeholders", () => {
    const recipe: Recipe = {
      recipeIngredient: [
        { title: "Sauce" }, { quantity: 1 },
        { quantity: 2, food: { name: "tomato" }, unit: { name: "cup", pluralName: "cups" }, note: "chopped" },
        { quantity: 2, food: { name: "tomato" }, unit: { name: "cup", pluralName: "cups" }, note: "chopped" },
      ],
      recipeInstructions: [{ text: "  " }, { text: "Stir" }],
    };
    expect(valueFor("ingredientCount", recipe)?.numeric).toBe(2);
    expect(valueFor("stepCount", recipe)?.numeric).toBe(1);
    expect(valueFor("ingredients", recipe)?.items).toEqual([
      { text: "Sauce", heading: true }, { text: "2 cups tomato chopped" }, { text: "2 cups tomato chopped" },
    ]);
  });

  test("distinguishes omitted lists from explicitly empty lists", () => {
    for (const id of ["ingredientCount", "stepCount", "tools"]) {
      expect(valueFor(id, {})?.state).toBe("missing");
      expect(valueFor(id, { recipeIngredient: [], recipeInstructions: [], tools: [] })?.state).toBe("provided");
    }
    expect(valueFor("ingredientCount", { recipeIngredient: [] })?.numeric).toBe(0);
    expect(valueFor("stepCount", { recipeInstructions: [] })?.numeric).toBe(0);
  });

  test("preserves raw lines and recipe references without scaling or HTML", () => {
    const recipe: Recipe = {
      recipeServings: 12,
      recipeIngredient: [
        { display: "a pinch of salt" }, { originalText: "pepper to taste" },
        { quantity: 2, referencedRecipe: { name: "Stock", slug: "stock" } },
        { note: "<b>parsley</b><script>alert(1)</script>" },
      ],
      tools: [{ id: "pot", name: "Pot", slug: "pot" }],
    };
    expect(valueFor("ingredients", recipe)?.items?.map(item => item.text)).toEqual(["a pinch of salt", "pepper to taste", "2 Stock", "parsley"]);
    expect(valueFor("tools", recipe)?.items).toEqual([{ text: "Pot" }]);
  });
});

describe("rating and nutrition provenance", () => {
  test.each([null, undefined, 0, -1, 6, Number.NaN, Number.POSITIVE_INFINITY])("does not rank an invalid or absent rating: %s", (rating) => {
    expect(valueFor("rating", { rating })).toEqual({ text: null, state: "unrated" });
  });

  test("uses only the recorded group rating", () => {
    expect(valueFor("rating", { rating: 3.75 })).toMatchObject({ numeric: 3.75, displayNumber: 3.75 });
    expect(buildComparisonRows([{ rating: 3.75 }]).find(row => row.id === "rating")?.label).toBe("recipe-comparison.group-rating");
  });

  test.each([false, undefined])("excludes hidden nutrition from the row model: %s", (showNutrition) => {
    const rows = buildComparisonRows([{ settings: { showNutrition }, nutrition: { calories: "SECRET calories", sodiumContent: "SECRET sodium" } }]);
    expect(rows.find(row => row.id === "nutrition")?.values[0].state).toBe("hidden");
    expect(JSON.stringify(rows)).not.toContain("SECRET");
    expect(rows.some(row => row.id === "nutrition-calories")).toBe(false);
  });

  test("fails closed when settings are missing", () => {
    expect(JSON.stringify(buildComparisonRows([{ nutrition: { calories: "SECRET" } }]))).not.toContain("SECRET");
  });

  test("preserves entered nutrients without units, scaling, or presumed basis", () => {
    const recipe: Recipe = { recipeServings: 4, recipeYieldQuantity: 12, settings: { showNutrition: true }, nutrition: { calories: "200", proteinContent: "8 g per 100 g" } };
    expect(valueFor("nutrition-calories", recipe)).toEqual({ text: "200", state: "provided" });
    expect(valueFor("nutrition-proteinContent", recipe)?.text).toBe("8 g per 100 g");
    expect(valueFor("nutrition", recipe)?.message).toBe("recipe-comparison.as-entered");
    expect(valueFor("nutrition-calories", recipe)?.numeric).toBeUndefined();
  });
});

describe("objective row differences", () => {
  test("compares compatible time formats without changing recorded text", () => {
    const row = buildComparisonRows([{ prepTime: "PT30M" }, { prepTime: "1 hour" }])[0];
    expect(row.values[0]).toMatchObject({ text: "PT30M", highlight: "lowest", difference: 0 });
    expect(row.values[1]).toMatchObject({ text: "1 hour", difference: 1800 });
    expect(row.values[1].highlight).toBeUndefined();
  });

  test.each([
    ["1.3 seconds", "1.4 seconds", 0.1],
    ["0.0000000001 seconds", "0.0000000002 seconds", 1e-10],
  ])("preserves positive decimal differences without floating-point noise: %s", (first, second, difference) => {
    const row = buildComparisonRows([{ prepTime: first as string }, { prepTime: second as string }])[0];
    expect(row.values[1].difference).toBe(difference);
  });

  test.each([undefined, {}, { prepTime: "overnight" }])("suppresses highlights for any ineligible participant", (recipe) => {
    const row = buildComparisonRows([{ prepTime: "PT30M" }, recipe])[0];
    expect(row.values.every(value => value.highlight === undefined && value.difference === undefined)).toBe(true);
  });

  test("labels ties and equality, not a unique best", () => {
    const tied = buildComparisonRows([{ prepTime: "30 minutes" }, { prepTime: "PT30M" }, { prepTime: "1 hour" }])[0];
    expect(tied.values.map(value => value.highlight)).toEqual(["tied", "tied", undefined]);
    const equal = buildComparisonRows([{ prepTime: "30 minutes" }, { prepTime: "PT30M" }])[0];
    expect(equal.values.map(value => value.highlight)).toEqual(["equal", "equal"]);
  });

  test("compares higher group ratings and fewer recorded steps, without ranking yield or nutrition", () => {
    const recipes: Recipe[] = [
      { rating: 3, recipeServings: 2, recipeYieldQuantity: 5, recipeInstructions: [], settings: { showNutrition: true }, nutrition: { calories: "200" } },
      { rating: 4, recipeServings: 4, recipeYieldQuantity: 10, recipeInstructions: [{ text: "Stir" }], settings: { showNutrition: true }, nutrition: { calories: "100" } },
    ];
    const rows = buildComparisonRows(recipes);
    expect(rows.find(row => row.id === "rating")?.values[1].highlight).toBe("highest");
    expect(rows.find(row => row.id === "stepCount")?.values[0].highlight).toBe("lowest");
    for (const id of ["servings", "yieldQuantity", "nutrition-calories"]) {
      expect(rows.find(row => row.id === id)?.values.every(value => value.difference === undefined)).toBe(true);
    }
    expect(buildComparisonRows([{ rating: 4 }, { rating: 0 }]).find(row => row.id === "rating")?.values[0].highlight).toBeUndefined();
  });

  test("recomputes after an unknown participant is removed", () => {
    const recipes: (Recipe | undefined)[] = [{ prepTime: "1 hour" }, undefined, { prepTime: "30 minutes" }];
    expect(buildComparisonRows(recipes)[0].values[2].highlight).toBeUndefined();
    expect(buildComparisonRows([recipes[0], recipes[2]])[0].values[1].highlight).toBe("lowest");
  });
});

describe("temporary group-scoped selection", () => {
  const context = { groupSlug: "home", userId: "user", ownGroup: true, groupId: "group" };
  function controller() {
    const result = createComparisonController(ref(newComparisonState()));
    result.setContext(context);
    return result;
  }

  test("preserves order, enforces four distinct selections, and gates comparison", () => {
    const result = controller();
    expect(result.canCompare.value).toBe(false);
    expect(result.add({ id: "1", slug: "first", name: "First" })).toBe(true);
    expect(result.add({ id: "1", slug: "first" })).toBe(false);
    expect(result.canCompare.value).toBe(false);
    for (const id of ["2", "3", "4"]) {
      expect(result.add({ id, slug: `recipe-${id}` })).toBe(true);
    }
    expect(result.canCompare.value).toBe(true);
    expect(result.add({ id: "5", slug: "fifth" })).toBe(false);
    expect(result.limitReached.value).toBe(true);
    expect(result.selections.value.map(item => item.id)).toEqual(["1", "2", "3", "4"]);
    result.remove("2");
    expect(result.limitReached.value).toBe(false);
    expect(result.add({ id: "5", slug: "fifth" })).toBe(true);
    result.clear();
    expect(result.canCompare.value).toBe(false);
  });

  test("rejects unusable identities and mismatched groups", () => {
    const result = controller();
    for (const recipe of [{ id: "", slug: "recipe" }, { id: "1", slug: " " }, { id: "1", slug: "recipe", groupId: "other" }]) {
      expect(result.add(recipe)).toBe(false);
    }
    expect(result.selections.value).toEqual([]);
  });

  test("same context keeps selection across browsing surface, filter, and page changes", () => {
    const result = controller();
    result.add({ id: "1", slug: "first" });
    result.setContext({ ...context });
    expect(result.selections.value[0].id).toBe("1");
  });

  test.each([
    { ...context, groupSlug: "other" }, { ...context, userId: null, ownGroup: false },
    { ...context, userId: "another-user" }, { ...context, groupId: "another-group" },
  ])("clears selection and detail data on context change", (nextContext) => {
    const result = controller();
    result.add({ id: "1", slug: "first" });
    result.state.value.entries["1"] = { status: "ready", recipe: { id: "1", nutrition: { calories: "private" } } };
    const generation = result.state.value.generation;
    result.setContext(nextContext);
    expect(result.selections.value).toEqual([]);
    expect(result.state.value.entries).toEqual({});
    expect(result.state.value.generation).toBeGreaterThan(generation);
  });

  test("new app state starts empty and removal erases details", () => {
    const result = controller();
    result.add({ id: "1", slug: "first" });
    result.state.value.entries["1"] = { status: "ready", recipe: { id: "1" } };
    result.remove("1");
    expect(result.state.value.entries["1"]).toBeUndefined();
    expect(controller().selections.value).toEqual([]);
  });
});

describe("scoped comparison detail reads", () => {
  const recipe = (id: string): Recipe => ({ id, slug: `recipe-${id}`, groupId: "group", prepTime: "30 minutes" });
  function setup(ownGroup = true) {
    const ownRead = vi.fn(async (slug: string) => ({ data: recipe(slug.replace("recipe-", "")), error: null }));
    const publicRead = vi.fn(async (slug: string) => ({ data: recipe(slug.replace("recipe-", "")), error: null }));
    const ownClient = vi.fn(() => ({ getOne: ownRead }));
    const publicClient = vi.fn(() => ({ getOne: publicRead }));
    const result = createComparisonController(ref(newComparisonState()), { ownGroup: ownClient, publicGroup: publicClient });
    result.setContext({ groupSlug: "home", userId: ownGroup ? "user" : null, ownGroup, groupId: "group" });
    result.add(recipe("1"));
    result.add(recipe("2"));
    return { result, ownRead, publicRead, ownClient, publicClient };
  }

  test("reads at most four selected details in the own-group scope", async () => {
    const { result, ownRead, publicRead } = setup();
    result.add(recipe("3"));
    result.add(recipe("4"));
    result.add(recipe("5"));
    await result.loadAll();
    expect(ownRead).toHaveBeenCalledTimes(4);
    expect(publicRead).not.toHaveBeenCalled();
    expect(Object.values(result.entries.value).every(entry => entry.status === "ready")).toBe(true);
  });

  test("public reads never fall back to the private client", async () => {
    const { result, publicRead, ownClient, publicClient } = setup(false);
    publicRead.mockResolvedValue({ data: null, error: { response: { status: 403 } } } as never);
    await result.loadAll();
    expect(publicClient).toHaveBeenCalledWith("home");
    expect(ownClient).not.toHaveBeenCalled();
    expect(result.entries.value["1"]).toEqual({ status: "unavailable" });
  });

  test.each([401, 403, 404, 500])("classifies response status %s without stale details", async (status) => {
    const { result, ownRead } = setup();
    await result.loadAll();
    ownRead.mockResolvedValue({ data: null, error: { response: { status } } } as never);
    await result.load("1");
    expect(result.entries.value["1"]).toEqual({ status: status === 500 ? "error" : "unavailable" });
    expect(result.entries.value["2"].status).toBe("ready");
  });

  test("retries only the failed recipe and clears old values on re-entry", async () => {
    const { result, ownRead } = setup();
    ownRead.mockRejectedValueOnce(new Error("network"));
    await result.loadAll();
    expect(result.entries.value["1"].status).toBe("error");
    ownRead.mockClear();
    await result.load("1");
    expect(ownRead).toHaveBeenCalledTimes(1);
    expect(result.entries.value["1"].status).toBe("ready");
    await result.loadAll();
    expect(ownRead).toHaveBeenCalledTimes(3);
  });

  test.each([
    { ...recipe("1"), id: "other" }, { ...recipe("1"), slug: "other" }, { ...recipe("1"), groupId: "other" },
  ])("rejects a mismatched detail identity", async (data) => {
    const { result, ownRead } = setup();
    ownRead.mockResolvedValueOnce({ data, error: null });
    await result.loadAll();
    expect(result.entries.value["1"]).toEqual({ status: "unavailable" });
  });

  test.each(["remove", "reset", "replace"])("discards a late response after %s", async (action) => {
    const { result, ownRead } = setup();
    let finish!: (value: { data: Recipe; error: null }) => void;
    ownRead.mockImplementationOnce(() => new Promise(resolve => finish = resolve));
    const pending = result.load("1");
    await Promise.resolve();
    if (action === "remove") {
      result.remove("1");
    }
    else if (action === "reset") {
      result.setContext({ groupSlug: "other", userId: null, ownGroup: false });
    }
    else {
      await result.loadAll();
      result.entries.value["1"].recipe!.prepTime = "new value";
    }
    finish({ data: recipe("1"), error: null });
    await pending;
    if (action === "replace") {
      expect(result.entries.value["1"].recipe?.prepTime).toBe("new value");
    }
    else {
      expect(result.entries.value["1"]).toBeUndefined();
    }
  });

  test("does not issue duplicate retries during loading", async () => {
    const { result, ownRead } = setup();
    let finish!: (value: { data: Recipe; error: null }) => void;
    ownRead.mockImplementationOnce(() => new Promise(resolve => finish = resolve));
    const pending = result.load("1");
    await result.load("1");
    expect(ownRead).toHaveBeenCalledTimes(1);
    finish({ data: recipe("1"), error: null });
    await pending;
  });

  test("bounds reads across overlapping re-entry requests", async () => {
    const { result, ownRead } = setup();
    result.add(recipe("3"));
    result.add(recipe("4"));
    const finish: (() => void)[] = [];
    let active = 0;
    let peak = 0;
    ownRead.mockImplementation(async (slug) => {
      active++;
      peak = Math.max(peak, active);
      if (finish.length < 4) {
        await new Promise<void>(resolve => finish.push(resolve));
      }
      active--;
      return { data: recipe(slug.replace("recipe-", "")), error: null };
    });
    const first = result.loadAll();
    await Promise.resolve();
    const second = result.loadAll();
    await Promise.resolve();
    expect(ownRead).toHaveBeenCalledTimes(4);
    finish.forEach(resolve => resolve());
    await Promise.all([first, second]);
    expect(peak).toBe(4);
    expect(ownRead).toHaveBeenCalledTimes(8);
    expect(Object.values(result.entries.value).every(entry => entry.status === "ready")).toBe(true);
  });
});
