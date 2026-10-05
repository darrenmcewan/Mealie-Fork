<template>
  <div
    class="section-title"
    :class="{
      'mt-8': section,
    }"
  >
    <h2 class="section-title-heading">
      <v-icon
        v-if="icon"
        size="small"
        start
      >
        {{ icon }}
      </v-icon>
      {{ title }}
    </h2>
    <div
      v-if="$slots.default"
      class="section-title-description"
    >
      <p class="pb-0 mb-0">
        <slot />
      </p>
    </div>
    <v-divider class="mt-1 mb-3" />
  </div>
</template>

<script lang="ts">
export default defineNuxtComponent({
  props: {
    title: {
      type: String,
      required: true,
    },
    icon: {
      type: String,
      default: "",
    },
    section: {
      type: Boolean,
      default: false,
    },
  },
});
</script>

<style scoped>
.section-title {
  padding-bottom: 8px;
  color: rgb(var(--v-theme-on-background));
}

.section-title-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.section-title-description {
  margin-top: 8px;
  color: rgba(var(--v-theme-on-background), 0.72);
  line-height: 1.5;
}
</style>
