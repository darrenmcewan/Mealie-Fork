<template>
  <header class="page-title">
    <div class="page-title-heading">
      <slot name="header" />
      <h1 class="page-title-text">
        <slot name="title" />
      </h1>

      <div v-if="$slots.default" class="page-title-subtitle">
        <slot />
      </div>
    </div>
    <div v-if="$slots.content" class="page-title-content">
      <slot name="content" />
    </div>
    <v-divider
      v-if="divider"
      class="my-4"
    />
  </header>
</template>

<script lang="ts">
export default defineNuxtComponent({
  props: {
    divider: {
      type: Boolean,
      default: false,
    },
  },
});
</script>

<style scoped>
.page-title {
  margin: 16px 0 24px;
  color: rgb(var(--v-theme-on-background));
}

.page-title-heading {
  min-width: 0;
}

.page-title-text {
  font-family: "Lora", serif;
  font-size: 2rem;
  font-weight: 500;
  line-height: 1.25;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.page-title-subtitle {
  margin-top: 8px;
  font-size: 1rem;
  font-weight: normal;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-background), 0.72);
}

.page-title-content {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

@media (max-width: 600px) {
  .page-title-text {
    font-size: 1.625rem;
  }
}
</style>
