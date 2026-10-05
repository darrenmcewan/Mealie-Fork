<template>
  <div class="recipe-comparison" :style="{ '--comparison-count': selections.length }">
    <div class="recipe-comparison__identities">
      <div v-if="!mobile" aria-hidden="true" />
      <article v-for="recipe in selections" :key="recipe.id" class="recipe-comparison__identity">
        <div class="recipe-comparison__image">
          <RecipeCardImage
            v-if="entries[recipe.id]?.status === 'ready'"
            :recipe-id="recipe.id"
            :slug="entries[recipe.id].recipe?.slug"
            :image-version="String(entries[recipe.id].recipe?.image || '')"
            :alt="entries[recipe.id].recipe?.name || recipe.name"
            height="100%"
            small
          />
          <div v-else class="recipe-comparison__placeholder" aria-hidden="true">
            <v-icon :icon="mdiSilverwareForkKnife" size="32" />
          </div>
        </div>
        <h2>
          <NuxtLink
            v-if="entries[recipe.id]?.status === 'ready'"
            :to="`/g/${groupSlug}/r/${entries[recipe.id].recipe?.slug}`"
            :data-recipe-link="recipe.id"
          >
            {{ entries[recipe.id].recipe?.name || recipe.name }}
          </NuxtLink>
          <span v-else>{{ recipe.name }}</span>
        </h2>
        <div class="recipe-comparison__controls">
          <v-btn
            :icon="mdiClose"
            variant="text"
            :data-comparison-remove="recipe.id"
            :aria-label="$t('recipe-comparison.remove', { name: entries[recipe.id]?.recipe?.name || recipe.name })"
            :title="$t('recipe-comparison.remove', { name: entries[recipe.id]?.recipe?.name || recipe.name })"
            @click="$emit('remove', recipe.id)"
          />
          <v-btn
            v-if="entries[recipe.id]?.status === 'error' || retrying.includes(recipe.id)"
            :prepend-icon="mdiRefresh"
            variant="text"
            :data-comparison-retry="recipe.id"
            :aria-label="$t('recipe-comparison.retry-recipe', { name: entries[recipe.id]?.recipe?.name || recipe.name })"
            :aria-busy="entries[recipe.id]?.status === 'loading'"
            @click="$emit('retry', recipe.id)"
          >
            {{ $t('recipe-comparison.retry') }}
          </v-btn>
        </div>
        <p v-if="entries[recipe.id]?.status !== 'ready'" role="status" class="recipe-comparison__status">
          {{ $t(`recipe-comparison.${entries[recipe.id]?.status || 'loading'}`) }}
        </p>
      </article>
    </div>
    <div v-if="mobile" class="recipe-comparison__mobile">
      <section v-for="criterion in rows" :key="criterion.id" :aria-labelledby="`criterion-${criterion.id}`">
        <h3 :id="`criterion-${criterion.id}`">
          {{ $t(criterion.label) }}
        </h3>
        <dl>
          <div v-for="(recipe, index) in selections" :key="recipe.id">
            <dt>{{ entries[recipe.id]?.recipe?.name || recipe.name }}</dt>
            <dd><ComparisonCell :value="criterion.values[index]" :row="criterion" :status="entries[recipe.id]?.status" /></dd>
          </div>
        </dl>
      </section>
    </div>
    <table v-else class="recipe-comparison__table">
      <caption class="recipe-comparison__caption">
        {{ $t('recipe-comparison.title') }}
      </caption>
      <colgroup>
        <col class="recipe-comparison__criterion-col">
        <col v-for="recipe in selections" :key="recipe.id">
      </colgroup>
      <thead>
        <tr>
          <th scope="col">
            {{ $t('recipe-comparison.criterion') }}
          </th>
          <th v-for="recipe in selections" :key="recipe.id" scope="col">
            {{ entries[recipe.id]?.recipe?.name || recipe.name }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="criterion in rows" :key="criterion.id">
          <th scope="row">
            {{ $t(criterion.label) }}
          </th>
          <td v-for="(recipe, index) in selections" :key="recipe.id">
            <ComparisonCell :value="criterion.values[index]" :row="criterion" :status="entries[recipe.id]?.status" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { defineComponent, h, type PropType } from "vue";
import { mdiClose, mdiRefresh, mdiSilverwareForkKnife } from "@mdi/js";
import RecipeCardImage from "./RecipeCardImage.vue";
import type { ComparisonEntry, ComparisonRow, ComparisonSelection, ComparisonValue } from "~/composables/recipes/use-recipe-comparison";

withDefaults(defineProps<{
  selections: ComparisonSelection[];
  entries: Record<string, ComparisonEntry>;
  rows: ComparisonRow[];
  groupSlug: string;
  retrying?: string[];
}>(), { retrying: () => [] });
defineEmits<{ remove: [id: string]; retry: [id: string] }>();
const display = useDisplay();
const mobile = computed(() => display.smAndDown.value);
const i18n = useI18n();
const numberOptions = { maximumSignificantDigits: 12 };

function durationDifference(seconds: number): string {
  const unit = seconds % 3600 === 0 ? "hours" : seconds % 60 === 0 ? "minutes" : "seconds";
  const amount = seconds / (unit === "hours" ? 3600 : unit === "minutes" ? 60 : 1);
  return i18n.t(`recipe-comparison.${unit}`, { amount: i18n.n(amount, numberOptions) });
}

const ComparisonCell = defineComponent({
  props: {
    value: { type: Object as PropType<ComparisonValue>, required: true },
    row: { type: Object as PropType<ComparisonRow>, required: true },
    status: { type: String as PropType<ComparisonEntry["status"]>, default: undefined },
  },
  setup(cell) {
    return () => {
      if (cell.status !== "ready") {
        return h("span", { class: "recipe-comparison__status" }, i18n.t(`recipe-comparison.${cell.status || "loading"}`));
      }
      const value = cell.value;
      const content = value.items
        ? value.items.length
          ? h("ul", { class: "recipe-comparison__list" }, value.items.map((item, index) => h("li", { key: index, class: { "recipe-comparison__heading": item.heading } }, item.text)))
          : h("span", i18n.t("recipe-comparison.none-recorded"))
        : h("span", value.message
            ? i18n.t(value.message)
            : value.displayNumber !== undefined
              ? i18n.n(value.displayNumber, numberOptions)
              : value.text || i18n.t(`recipe-comparison.${value.state === "missing" ? "not-provided" : value.state}`));
      const details = [];
      if (value.state === "not-comparable") {
        details.push(h("span", { class: "recipe-comparison__meta" }, i18n.t("recipe-comparison.not-comparable")));
      }
      if (value.highlight) {
        const label = value.highlight === "equal"
          ? i18n.t("recipe-comparison.equal")
          : `${value.highlight === "tied" ? `${i18n.t("recipe-comparison.tied")}: ` : ""}${i18n.t(`recipe-comparison.${cell.row.metric === "rating" ? "highest-rating" : `lowest-${cell.row.metric}`}`)}`;
        details.push(h("span", { class: "recipe-comparison__highlight" }, label));
      }
      if (value.difference && cell.row.metric) {
        const amount = cell.row.metric === "duration" ? durationDifference(value.difference) : i18n.n(value.difference, numberOptions);
        details.push(h("span", { class: "recipe-comparison__meta" }, i18n.t(`recipe-comparison.${cell.row.metric}-difference`, { amount })));
      }
      return h("div", { class: "recipe-comparison__value" }, [content, ...details]);
    };
  },
});
</script>

<style scoped>
.recipe-comparison {
  min-width: 0;
  width: 100%;
}

.recipe-comparison__identities {
  display: grid;
  grid-template-columns: 20% repeat(var(--comparison-count), minmax(0, 1fr));
  margin-block: 24px 16px;
}

.recipe-comparison__identity {
  min-width: 0;
  padding-inline: 12px;
}

.recipe-comparison__image {
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border-radius: 6px;
  background: rgb(var(--v-theme-surface-variant));
}

.recipe-comparison__placeholder {
  display: grid;
  place-items: center;
  height: 100%;
}

.recipe-comparison__identity h2 {
  font-family: var(--mealie-display-font) !important;
  font-size: 1.0625rem;
  font-weight: 600;
  line-height: 1.5;
  margin-block: 12px 4px;
  overflow-wrap: anywhere;
}

.recipe-comparison__identity a {
  color: rgb(var(--v-theme-on-surface));
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}

.recipe-comparison__controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  min-height: 44px;
}

.recipe-comparison__controls :deep(.v-btn) {
  min-width: 44px;
  min-height: 44px;
}

.recipe-comparison__table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.recipe-comparison__criterion-col {
  width: 20%;
}

.recipe-comparison__table th,
.recipe-comparison__table td {
  text-align: start;
  vertical-align: top;
  padding: 16px 12px;
  border-bottom: 1px solid var(--mealie-border);
  overflow-wrap: anywhere;
  line-height: 1.65;
}

.recipe-comparison__table thead {
  background: rgb(var(--v-theme-surface-variant));
}

.recipe-comparison__caption {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}

.recipe-comparison :deep(.recipe-comparison__value) {
  font-variant-numeric: tabular-nums;
}

.recipe-comparison :deep(.recipe-comparison__meta),
.recipe-comparison :deep(.recipe-comparison__highlight),
.recipe-comparison__status {
  display: block;
  font-size: 0.8125rem;
  margin-top: 6px;
  color: var(--mealie-muted);
}

.recipe-comparison :deep(.recipe-comparison__highlight) {
  color: rgb(var(--v-theme-primary));
  font-weight: 600;
}

.recipe-comparison :deep(.recipe-comparison__list) {
  padding: 0;
  list-style: none;
}

.recipe-comparison :deep(.recipe-comparison__list li + li) {
  margin-top: 6px;
}

.recipe-comparison :deep(.recipe-comparison__heading) {
  font-weight: 600;
  margin-top: 12px;
}

.recipe-comparison__mobile section {
  padding-block: 20px;
  border-top: 1px solid var(--mealie-border);
}

.recipe-comparison__mobile h3 {
  font-size: 1rem;
  line-height: 1.5;
  margin-bottom: 12px;
}

.recipe-comparison__mobile dl > div {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  padding-block: 8px;
  font-size: 0.875rem;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.recipe-comparison__mobile dt {
  color: var(--mealie-muted);
}

.recipe-comparison__mobile dd {
  min-width: 0;
}

@media (max-width: 959px) {
  .recipe-comparison__identities {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 24px 16px;
  }

  .recipe-comparison__identity {
    padding: 0;
  }
}
</style>
