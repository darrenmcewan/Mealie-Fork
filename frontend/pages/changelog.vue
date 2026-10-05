<template>
  <v-container class="changelog-page">
    <BasePageTitle divider>
      <template #title>
        {{ $t("sidebar.changelog") }}
      </template>
    </BasePageTitle>

    <article :aria-label="$t('sidebar.changelog')" class="changelog-content">
      <SafeMarkdown :source="changelog" />
    </article>
  </v-container>
</template>

<script setup lang="ts">
import changelog from "~/content/changelog.md?raw";

const i18n = useI18n();

useSeoMeta({
  title: () => i18n.t("sidebar.changelog"),
});
</script>

<style scoped>
.changelog-page {
  max-width: 1040px;
}

.changelog-content {
  max-width: 80ch;
  color: rgb(var(--v-theme-on-background));
  font-size: 1rem;
  line-height: 1.75;
  overflow-wrap: anywhere;
}

.changelog-content :deep(h2) {
  margin: 40px 0 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--mealie-border);
  font-size: 1.375rem;
  font-weight: 600;
  line-height: 1.4;
}

.changelog-content :deep(h2:first-child) {
  margin-top: 0;
}

.changelog-content :deep(h3) {
  margin: 24px 0 12px;
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.5;
}

.changelog-content :deep(li) {
  margin-bottom: 12px;
}

.changelog-content :deep(a) {
  color: rgb(var(--v-theme-primary));
  text-underline-offset: 3px;
}

.changelog-content :deep(pre) {
  max-width: 100%;
  overflow-x: auto;
}

.changelog-content :deep(img) {
  max-width: 100%;
  height: auto;
}
</style>
