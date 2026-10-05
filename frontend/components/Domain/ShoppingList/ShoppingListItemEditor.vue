<template>
  <div class="shopping-item-editor">
    <div>
      <v-card-text class="pb-3 pt-1">
        <div class="shopping-editor-fields">
          <div class="shopping-editor-quantity">
            <InputQuantity v-model="listItem.quantity" />
          </div>
          <InputLabelType
            v-model="listItem.unit"
            v-model:item-id="listItem.unitId!"
            :items="units"
            :label="$t('recipe.unit')"
            :icon="$globals.icons.units"
            create
            @create="createAssignUnit"
          />
          <InputLabelType
            v-model="listItem.food"
            v-model:item-id="listItem.foodId!"
            :items="foods"
            :label="$t('shopping-list.food')"
            :icon="$globals.icons.foods"
            create
            @create="createAssignFood"
          />
        </div>
        <div class="shopping-editor-note">
          <v-textarea
            v-model="listItem.note"
            hide-details
            :label="$t('shopping-list.note')"
            rows="1"
            auto-grow
            autofocus
            @keypress="handleNoteKeyPress"
          />
        </div>
        <div class="shopping-editor-labels">
          <div class="shopping-editor-label-field">
            <div class="mt-3 flex-grow-1">
              <InputLabelType
                v-model="listItem.label"
                v-model:item-id="listItem.labelId!"
                :items="labels"
                :label="$t('shopping-list.label')"
              />
            </div>

            <v-menu
              v-if="listItem.recipeReferences && listItem.recipeReferences.length > 0"
              open-on-hover
              :transition="false"
              offset-y
              start
              top
            >
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon
                  size="44"
                  variant="text"
                  color="warning"
                  :aria-label="$t('shopping-list.linked-item-warning')"
                  :title="$t('shopping-list.linked-item-warning')"
                >
                  <v-icon>{{ $globals.icons.alert }}</v-icon>
                </v-btn>
              </template>
              <v-card max-width="350px" class="left-warning-border">
                <v-card-text>
                  {{ $t("shopping-list.linked-item-warning") }}
                </v-card-text>
              </v-card>
            </v-menu>
          </div>
          <BaseButton
            v-if="listItem.labelId && listItem.food && listItem.labelId !== listItem.food.labelId"
            small
            color="info"
            :icon="$globals.icons.tagArrowRight"
            :text="$t('shopping-list.save-label')"
            class="mt-2 align-items-flex-start"
            @click="assignLabelToFood"
          />
          <v-spacer />
        </div>
      </v-card-text>
      <div class="shopping-editor-actions">
        <v-btn
          v-if="allowDelete"
          icon
          size="44"
          variant="text"
          color="error"
          :aria-label="$t('general.delete')"
          :title="$t('general.delete')"
          @click="$emit('delete')"
        >
          <v-icon>{{ $globals.icons.delete }}</v-icon>
        </v-btn>
        <v-spacer />
        <v-btn variant="text" min-height="44" @click="$emit('cancel')">
          {{ $t('general.cancel') }}
        </v-btn>
        <v-btn color="primary" min-height="44" @click="$emit('save')">
          <v-icon start>
            {{ $globals.icons.save }}
          </v-icon>
          {{ $t('general.save') }}
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import type { ShoppingListItemCreate, ShoppingListItemOut } from "~/lib/api/types/household";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { IngredientFood, IngredientUnit } from "~/lib/api/types/recipe";
import { useFoodStore, useFoodData, useUnitStore, useUnitData } from "~/composables/store";

export default defineNuxtComponent({
  props: {
    modelValue: {
      type: Object as () => ShoppingListItemCreate | ShoppingListItemOut,
      required: true,
    },
    labels: {
      type: Array as () => MultiPurposeLabelOut[],
      required: true,
    },
    units: {
      type: Array as () => IngredientUnit[],
      required: true,
    },
    foods: {
      type: Array as () => IngredientFood[],
      required: true,
    },
    allowDelete: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  emits: ["update:modelValue", "save", "cancel", "delete"],
  setup(props, context) {
    const foodStore = useFoodStore();
    const foodData = useFoodData();

    const unitStore = useUnitStore();
    const unitData = useUnitData();

    const listItem = computed({
      get: () => {
        return props.modelValue;
      },
      set: (val) => {
        context.emit("update:modelValue", val);
      },
    });

    watch(
      () => props.modelValue.food,
      (newFood) => {
        listItem.value.label = newFood?.label || null;
        listItem.value.labelId = listItem.value.label?.id || null;
      },
    );

    async function createAssignFood(val: string) {
      // keep UI reactive
      // eslint-disable-next-line @typescript-eslint/no-unused-expressions
      listItem.value.food ? (listItem.value.food.name = val) : (listItem.value.food = { name: val });

      foodData.data.name = val;
      const newFood = await foodStore.actions.createOne(foodData.data);
      if (newFood) {
        listItem.value.food = newFood;
        listItem.value.foodId = newFood.id;
      }
      foodData.reset();
    }

    async function createAssignUnit(val: string) {
      // keep UI reactive
      // eslint-disable-next-line @typescript-eslint/no-unused-expressions
      listItem.value.unit ? (listItem.value.unit.name = val) : (listItem.value.unit = { name: val });

      unitData.data.name = val;
      const newUnit = await unitStore.actions.createOne(unitData.data);
      if (newUnit) {
        listItem.value.unit = newUnit;
        listItem.value.unitId = newUnit.id;
      }
      unitData.reset();
    }

    async function assignLabelToFood() {
      if (!(listItem.value.food && listItem.value.foodId && listItem.value.labelId)) {
        return;
      }

      listItem.value.food.labelId = listItem.value.labelId;
      await foodStore.actions.updateOne(listItem.value.food);
    }

    return {
      listItem,
      createAssignFood,
      createAssignUnit,
      assignLabelToFood,
    };
  },
  methods: {
    handleNoteKeyPress(event) {
      // Save on Enter
      if (!event.shiftKey && event.key === "Enter") {
        event.preventDefault();
        this.$emit("save");
      }
    },
  },
});
</script>

<style scoped>
.shopping-item-editor {
  padding: 16px 0;
  border-block: 1px solid rgba(var(--v-theme-on-surface), 0.14);
}

.shopping-item-editor :deep(.v-card-text) {
  padding-inline: 0;
}

.shopping-editor-fields {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) minmax(0, 2fr);
  align-items: start;
  gap: 16px;
}

.shopping-editor-quantity {
  min-width: 0;
}

.shopping-editor-note {
  margin-top: 8px;
}

.shopping-editor-labels {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}

.shopping-editor-label-field {
  display: flex;
  align-items: flex-end;
  flex: 1;
  min-width: 0;
  max-width: 360px;
}

.shopping-editor-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.shopping-item-editor :deep(.v-field),
.shopping-item-editor :deep(.v-btn:not(.v-btn--icon)) {
  border-radius: 6px;
}

.shopping-item-editor :deep(.v-btn) {
  min-height: 44px;
  letter-spacing: 0;
}

@media (max-width: 600px) {
  .shopping-editor-fields {
    grid-template-columns: 96px minmax(0, 1fr);
    gap: 8px;
  }

  .shopping-editor-fields > :last-child {
    grid-column: 1 / -1;
  }
}
</style>
