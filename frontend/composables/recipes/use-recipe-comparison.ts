import DOMPurify from "isomorphic-dompurify";
import { computed, watch, type Ref } from "vue";
import { parseIngredientText } from "./use-recipe-ingredients";
import { usePublicExploreApi, useUserApi } from "~/composables/api/api-client";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { Nutrition, Recipe, RecipeSummary } from "~/lib/api/types/recipe";

export interface ComparisonValue {
  text: string | null;
  state: "provided" | "missing" | "not-comparable" | "hidden" | "unrated";
  numeric?: number;
  displayNumber?: number;
  message?: string;
  items?: { text: string; heading?: boolean }[];
  difference?: number;
  highlight?: "lowest" | "highest" | "tied" | "equal";
}

export interface ComparisonRow {
  id: string;
  label: string;
  values: ComparisonValue[];
  metric?: "duration" | "count" | "rating";
}

export interface ComparisonContext {
  groupSlug: string;
  userId: string | null;
  ownGroup: boolean;
  groupId?: string;
}

export interface ComparisonSelection {
  id: string;
  slug: string;
  name: string;
  groupId?: string;
}

export interface ComparisonEntry {
  status: "loading" | "ready" | "unavailable" | "error";
  recipe?: Recipe;
}

export interface ComparisonState {
  context: ComparisonContext | null;
  selections: ComparisonSelection[];
  entries: Record<string, ComparisonEntry>;
  generation: number;
  limitReached: boolean;
}

export function newComparisonState(): ComparisonState {
  return { context: null, selections: [], entries: {}, generation: 0, limitReached: false };
}

export interface ComparisonReader {
  getOne: (slug: string) => Promise<{ data: Recipe | null; error?: unknown }>;
}

export interface ComparisonClients {
  ownGroup: () => ComparisonReader;
  publicGroup: (groupSlug: string) => ComparisonReader;
}

const readSlots = new WeakMap<ComparisonState, { active: number; waiting: (() => void)[] }>();

async function acquireReadSlot(state: ComparisonState) {
  let slots = readSlots.get(state);
  if (!slots) {
    slots = { active: 0, waiting: [] };
    readSlots.set(state, slots);
  }
  if (slots.active < 4) {
    slots.active++;
  }
  else {
    await new Promise<void>(resolve => slots!.waiting.push(resolve));
  }
  return () => {
    const next = slots!.waiting.shift();
    if (next) {
      next();
    }
    else {
      slots!.active--;
    }
  };
}

export function createComparisonController(state: Ref<ComparisonState>, clients?: ComparisonClients) {
  function clear() {
    state.value.selections = [];
    state.value.entries = {};
    state.value.limitReached = false;
    state.value.generation++;
  }

  function setContext(context: ComparisonContext) {
    const previous = state.value.context;
    if (!previous || previous.groupSlug !== context.groupSlug || previous.userId !== context.userId
      || previous.ownGroup !== context.ownGroup || previous.groupId !== context.groupId) {
      clear();
      state.value.context = { ...context };
    }
  }

  function add(recipe: Pick<RecipeSummary, "id" | "slug" | "name" | "groupId">): boolean {
    const id = recipe.id?.trim();
    const slug = recipe.slug?.trim();
    if (!id || !slug || !state.value.context || state.value.selections.some(item => item.id === id)) {
      return false;
    }
    const groupId = state.value.context.groupId || state.value.selections.find(item => item.groupId)?.groupId;
    if (recipe.groupId && groupId && recipe.groupId !== groupId) {
      return false;
    }
    if (state.value.selections.length >= 4) {
      state.value.limitReached = true;
      return false;
    }
    state.value.selections.push({ id, slug, name: recipe.name?.trim() || slug, groupId: recipe.groupId });
    state.value.limitReached = false;
    return true;
  }

  function remove(id: string) {
    state.value.selections = state.value.selections.filter(item => item.id !== id);
    state.value.entries = Object.fromEntries(Object.entries(state.value.entries).filter(([entryId]) => entryId !== id));
    state.value.limitReached = false;
  }

  async function load(id: string) {
    const selection = state.value.selections.find(item => item.id === id);
    const context = state.value.context;
    if (!selection || !context || !clients || state.value.entries[id]?.status === "loading") {
      return;
    }
    state.value.entries[id] = { status: "loading" };
    const pending = state.value.entries[id];
    const generation = state.value.generation;
    const isCurrent = () => state.value.generation === generation && state.value.entries[id] === pending
      && state.value.selections.some(item => item.id === id);
    const release = await acquireReadSlot(state.value);
    try {
      if (!isCurrent()) {
        return;
      }
      const api = context.ownGroup ? clients.ownGroup() : clients.publicGroup(context.groupSlug);
      const { data, error } = await api.getOne(selection.slug);
      if (!isCurrent()) {
        return;
      }
      if (error || !data) {
        const status = (error as { response?: { status?: number } } | null)?.response?.status;
        state.value.entries[id] = { status: status === 401 || status === 403 || status === 404 ? "unavailable" : "error" };
        return;
      }
      const groupId = context.groupId || selection.groupId;
      state.value.entries[id] = data.id !== id || data.slug !== selection.slug || (groupId && data.groupId !== groupId)
        ? { status: "unavailable" }
        : { status: "ready", recipe: data };
    }
    catch (error) {
      if (isCurrent()) {
        const status = (error as { response?: { status?: number } } | null)?.response?.status;
        state.value.entries[id] = { status: status === 401 || status === 403 || status === 404 ? "unavailable" : "error" };
      }
    }
    finally {
      release();
    }
  }

  async function loadAll() {
    state.value.generation++;
    state.value.entries = {};
    await Promise.all(state.value.selections.map(selection => load(selection.id)));
  }

  return {
    state,
    selections: computed(() => state.value.selections),
    canCompare: computed(() => state.value.selections.length >= 2 && state.value.selections.length <= 4),
    limitReached: computed(() => state.value.limitReached),
    setContext,
    add,
    remove,
    clear,
    load,
    loadAll,
    entries: computed(() => state.value.entries),
    rows: computed(() => buildComparisonRows(state.value.selections.map(selection => state.value.entries[selection.id]?.status === "ready" ? state.value.entries[selection.id].recipe : undefined))),
  };
}

export function useRecipeComparison() {
  const state = useState<ComparisonState>("recipe-comparison", newComparisonState);
  const auth = useMealieAuth();
  const route = useRoute();
  const { isOwnGroup } = useLoggedInState();
  const controller = createComparisonController(state, {
    ownGroup: () => useUserApi().recipes,
    publicGroup: groupSlug => usePublicExploreApi(groupSlug).explore.recipes,
  });
  watch(() => ({
    groupSlug: String(route.params.groupSlug || auth.user.value?.groupSlug || ""),
    userId: auth.loggedIn.value ? auth.user.value?.id || null : null,
    ownGroup: isOwnGroup.value,
    groupId: isOwnGroup.value ? auth.user.value?.groupId : undefined,
  }), controller.setContext, { immediate: true, flush: "sync" });
  return controller;
}

function recordedText(value: string | null | undefined): ComparisonValue {
  return value?.trim()
    ? { text: value, state: "provided" }
    : { text: null, state: "missing" };
}

function recordedQuantity(value: number | undefined): ComparisonValue {
  return typeof value === "number" && Number.isFinite(value) && value > 0
    ? { text: null, state: "provided", displayNumber: value }
    : { text: null, state: "missing" };
}

export function comparisonDurationSeconds(input: string | null | undefined): number | undefined {
  const text = input?.trim();
  if (!text) {
    return undefined;
  }
  const iso = /^PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?$/i.exec(text);
  if (iso && iso.slice(1).some(value => value !== undefined)) {
    const seconds = Number(iso[1] || 0) * 3600 + Number(iso[2] || 0) * 60 + Number(iso[3] || 0);
    return Number.isFinite(seconds) ? seconds : undefined;
  }
  if (!/^(?:\d+(?:\.\d+)?\s*(?:hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)\s*)+$/i.test(text)) {
    return undefined;
  }
  const units = new Set<string>();
  let seconds = 0;
  for (const token of text.matchAll(/(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)/gi)) {
    const unit = token[2].toLowerCase().charAt(0);
    if (units.has(unit)) {
      return undefined;
    }
    units.add(unit);
    seconds += Number(token[1]) * (unit === "h" ? 3600 : unit === "m" ? 60 : 1);
  }
  return Number.isFinite(seconds) ? seconds : undefined;
}

function recordedDuration(text: string | null | undefined): ComparisonValue {
  const value = recordedText(text);
  if (value.state === "missing") {
    return value;
  }
  const numeric = comparisonDurationSeconds(text);
  return numeric === undefined ? { ...value, state: "not-comparable" } : { ...value, numeric };
}

function plainText(text: string): string {
  return DOMPurify.sanitize(text, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] }).trim();
}

function recordedIngredients(recipe: Recipe | undefined): ComparisonValue {
  if (!recipe?.recipeIngredient) {
    return { text: null, state: "missing" };
  }
  const items: NonNullable<ComparisonValue["items"]> = [];
  for (const ingredient of recipe.recipeIngredient) {
    const heading = ingredient.title && plainText(ingredient.title);
    if (heading) {
      items.push({ text: heading, heading: true });
    }
    const structured = ingredient.food?.name?.trim() || ingredient.referencedRecipe?.name?.trim() || ingredient.note?.trim();
    const raw = ingredient.display?.trim() || ingredient.originalText?.trim();
    const text = plainText(structured ? parseIngredientText(ingredient, 1, false) : raw || "");
    if (text) {
      items.push({ text });
    }
  }
  return { text: null, state: "provided", items };
}

function recordedCount(count: number | undefined): ComparisonValue {
  return count === undefined
    ? { text: null, state: "missing" }
    : { text: null, state: "provided", numeric: count, displayNumber: count };
}

const nutrients: (keyof Nutrition)[] = [
  "calories", "carbohydrateContent", "cholesterolContent", "fatContent", "fiberContent",
  "proteinContent", "saturatedFatContent", "sodiumContent", "sugarContent", "transFatContent", "unsaturatedFatContent",
];

function visibleNutrition(recipe: Recipe | undefined): Nutrition | null | undefined {
  return recipe?.settings?.showNutrition === true ? recipe.nutrition : undefined;
}

function recordedRating(rating: number | null | undefined): ComparisonValue {
  return typeof rating === "number" && Number.isFinite(rating) && rating > 0 && rating <= 5
    ? { text: null, state: "provided", numeric: rating, displayNumber: rating }
    : { text: null, state: "unrated" };
}

export function buildComparisonRows(recipes: (Recipe | undefined)[]): ComparisonRow[] {
  const ingredients = recipes.map(recordedIngredients);
  const rows: ComparisonRow[] = [
    { id: "prepTime", label: "recipe.prep-time", values: recipes.map(recipe => recordedDuration(recipe?.prepTime)), metric: "duration" },
    { id: "performTime", label: "recipe.perform-time", values: recipes.map(recipe => recordedDuration(recipe?.performTime)), metric: "duration" },
    { id: "totalTime", label: "recipe.total-time", values: recipes.map(recipe => recordedDuration(recipe?.totalTime)), metric: "duration" },
    { id: "servings", label: "recipe.servings", values: recipes.map(recipe => recordedQuantity(recipe?.recipeServings)) },
    { id: "yieldQuantity", label: "recipe-comparison.yield-quantity", values: recipes.map(recipe => recordedQuantity(recipe?.recipeYieldQuantity)) },
    { id: "yield", label: "recipe.recipe-yield", values: recipes.map(recipe => recordedText(recipe?.recipeYield)) },
    { id: "rating", label: "recipe-comparison.group-rating", values: recipes.map(recipe => recordedRating(recipe?.rating)), metric: "rating" },
    { id: "ingredientCount", label: "recipe-comparison.ingredient-count", values: ingredients.map(value => recordedCount(value.items?.filter(item => !item.heading).length)), metric: "count" },
    { id: "stepCount", label: "recipe-comparison.step-count", values: recipes.map(recipe => recordedCount(recipe?.recipeInstructions?.filter(step => step.text?.trim()).length)), metric: "count" },
    { id: "ingredients", label: "recipe.ingredients", values: ingredients },
    { id: "tools", label: "tool.required-tools", values: recipes.map(recipe => recipe?.tools ? { text: null, state: "provided", items: recipe.tools.filter(tool => tool.name?.trim()).map(tool => ({ text: tool.name })) } : { text: null, state: "missing" }) },
  ];

  if (recipes.some(recipe => recipe?.cookTime?.trim() && recipe.cookTime !== recipe.performTime)) {
    rows.splice(2, 0, {
      id: "cookTime",
      label: "recipe-comparison.additional-cook-time",
      values: recipes.map(recipe => recordedText(recipe?.cookTime)),
    });
  }

  rows.push({
    id: "nutrition",
    label: "recipe-comparison.nutrition-basis",
    values: recipes.map((recipe) => {
      if (recipe && recipe.settings?.showNutrition !== true) {
        return { text: null, state: "hidden" };
      }
      return nutrients.some(key => visibleNutrition(recipe)?.[key]?.trim())
        ? { text: null, state: "provided", message: "recipe-comparison.as-entered" }
        : { text: null, state: "missing" };
    }),
  });
  for (const key of nutrients) {
    if (recipes.some(recipe => visibleNutrition(recipe)?.[key]?.trim())) {
      rows.push({
        id: `nutrition-${key}`,
        label: `recipe-comparison.nutrients.${key}`,
        values: recipes.map(recipe => recipe && recipe.settings?.showNutrition !== true
          ? { text: null, state: "hidden" }
          : recordedText(visibleNutrition(recipe)?.[key])),
      });
    }
  }

  return rows.map((row) => {
    if (!row.metric || recipes.length < 2 || recipes.some(recipe => !recipe)
      || row.values.some(value => value.numeric === undefined || !Number.isFinite(value.numeric))) {
      return row;
    }
    const numbers = row.values.map(value => value.numeric!);
    const target = row.metric === "rating" ? Math.max(...numbers) : Math.min(...numbers);
    const matches = numbers.filter(value => value === target).length;
    return {
      ...row,
      values: row.values.map(value => ({
        ...value,
        difference: Number(Math.abs(value.numeric! - target).toPrecision(12)),
        highlight: matches === numbers.length
          ? "equal"
          : value.numeric === target
            ? matches > 1 ? "tied" : row.metric === "rating" ? "highest" : "lowest"
            : undefined,
      })),
    };
  });
}
