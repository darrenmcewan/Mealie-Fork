<template>
  <dl v-if="_showCards" class="recipe-times" :class="{ 'recipe-times--small': small }">
    <div v-for="time in times" :key="time.name" class="recipe-times__item">
      <v-icon color="primary" size="20" aria-hidden="true">
        {{ time.icon }}
      </v-icon>
      <div>
        <dt>{{ time.name }}</dt>
        <dd>{{ time.value }}</dd>
      </div>
    </div>
  </dl>
</template>

<script setup lang="ts">
interface Props {
  prepTime?: string | null;
  totalTime?: string | null;
  performTime?: string | null;
  color?: string;
  small?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  prepTime: null,
  totalTime: null,
  performTime: null,
  color: "accent custom-transparent",
  small: false,
});

const i18n = useI18n();

function isEmpty(str: string | null) {
  return !str || str.length === 0;
}

const _showCards = computed(() => {
  return [props.prepTime, props.totalTime, props.performTime].some(x => !isEmpty(x));
});

const validateTotalTime = computed(() => {
  return !isEmpty(props.totalTime) ? { name: i18n.t("recipe.total-time"), value: props.totalTime } : null;
});

const validatePrepTime = computed(() => {
  return !isEmpty(props.prepTime) ? { name: i18n.t("recipe.prep-time"), value: props.prepTime } : null;
});

const validatePerformTime = computed(() => {
  return !isEmpty(props.performTime) ? { name: i18n.t("recipe.perform-time"), value: props.performTime } : null;
});

const { $globals } = useNuxtApp();
const times = computed(() => [
  validateTotalTime.value && { ...validateTotalTime.value, icon: $globals.icons.clockOutline },
  validatePrepTime.value && { ...validatePrepTime.value, icon: $globals.icons.knife },
  validatePerformTime.value && { ...validatePerformTime.value, icon: $globals.icons.potSteam },
].filter((time): time is { name: string; value: string; icon: string } => !!time));
</script>

<style scoped>
.recipe-times {
  display: flex;
  flex-wrap: wrap;
  gap: 20px 28px;
  margin: 0;
}

.recipe-times__item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.recipe-times dt {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--mealie-muted);
  line-height: 1.5;
}

.recipe-times dd {
  margin: 4px 0 0;
  font-size: 0.9375rem;
  font-weight: 650;
  line-height: 1.5;
  font-variant-numeric: tabular-nums;
  color: rgb(var(--v-theme-on-surface));
  overflow-wrap: anywhere;
}

.recipe-times--small {
  gap: 12px 16px;
}

.recipe-times--small dd {
  font-size: 0.8125rem;
}
</style>
