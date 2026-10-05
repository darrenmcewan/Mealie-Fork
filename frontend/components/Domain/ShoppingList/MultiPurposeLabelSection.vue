<template>
  <div class="shopping-label-row">
    <div class="handle shopping-label-name">
      <span class="mr-2">
        <v-icon :color="labelColor">
          {{ $globals.icons.tags }}
        </v-icon>
      </span>
      {{ modelValue.label.name }}
    </div>
    <div class="shopping-label-controls">
      <v-btn
        ref="upButton"
        size="44"
        variant="text"
        icon
        :disabled="disabled || !canMoveUp"
        :aria-label="$t('shopping-list.move-section-up', { name: modelValue.label.name })"
        :title="$t('shopping-list.move-section-up', { name: modelValue.label.name })"
        @click="move(-1)"
      >
        <v-icon class="shopping-label-up">
          {{ $globals.icons.chevronDown }}
        </v-icon>
      </v-btn>
      <v-btn
        ref="downButton"
        size="44"
        variant="text"
        icon
        :disabled="disabled || !canMoveDown"
        :aria-label="$t('shopping-list.move-section-down', { name: modelValue.label.name })"
        :title="$t('shopping-list.move-section-down', { name: modelValue.label.name })"
        @click="move(1)"
      >
        <v-icon>{{ $globals.icons.chevronDown }}</v-icon>
      </v-btn>
      <v-btn
        size="44"
        variant="text"
        class="handle shopping-label-drag"
        icon
        :disabled="disabled"
        :aria-label="$t('shopping-list.reorder-section', { name: modelValue.label.name })"
        :title="$t('shopping-list.reorder-section', { name: modelValue.label.name })"
      >
        <v-icon>
          {{ $globals.icons.arrowUpDown }}
        </v-icon>
      </v-btn>
    </div>
  </div>
</template>

<script lang="ts">
import type { ShoppingListMultiPurposeLabelOut } from "~/lib/api/types/household";

export default defineNuxtComponent({
  props: {
    modelValue: {
      type: Object as () => ShoppingListMultiPurposeLabelOut,
      required: true,
    },
    useColor: {
      type: Boolean,
      default: false,
    },
    canMoveUp: Boolean,
    canMoveDown: Boolean,
    disabled: Boolean,
  },
  emits: ["move"],
  setup(props, context) {
    const labelColor = computed(() => props.useColor ? props.modelValue.label.color : undefined);
    const upButton = ref<{ $el: HTMLButtonElement } | null>(null);
    const downButton = ref<{ $el: HTMLButtonElement } | null>(null);

    function move(direction: -1 | 1) {
      context.emit("move", direction);
      nextTick(() => {
        const control = direction === -1
          ? props.canMoveUp ? upButton.value : downButton.value
          : props.canMoveDown ? downButton.value : upButton.value;
        control?.$el.focus();
      });
    }

    return {
      move,
      labelColor,
      upButton,
      downButton,
    };
  },
});
</script>

<style scoped>
.shopping-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.shopping-label-name {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
}

.shopping-label-controls {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.shopping-label-up {
  transform: rotate(180deg);
}

.handle {
  cursor: grab;
}
</style>
