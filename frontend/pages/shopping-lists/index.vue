<template>
  <v-container
    v-if="shoppingListChoices && ready"
    class="shopping-overview"
  >
    <BaseDialog
      v-model="createDialog"
      :title="$t('shopping-list.create-shopping-list')"
      can-submit
      @submit="createOne"
    >
      <v-card-text>
        <v-text-field
          v-model="createName"
          autofocus
          :label="$t('shopping-list.new-list')"
        />
      </v-card-text>
    </BaseDialog>

    <!-- Settings -->
    <BaseDialog
      v-model="ownerDialog"
      :icon="$globals.icons.admin"
      :title="$t('user.edit-user')"
      can-confirm
      @confirm="updateOwner"
    >
      <v-container>
        <v-form>
          <v-select
            v-model="updateUserId"
            :items="allUsers"
            item-title="fullName"
            item-value="id"
            :label="$t('general.owner')"
            :prepend-icon="$globals.icons.user"
          />
        </v-form>
      </v-container>
    </BaseDialog>

    <BaseDialog
      v-model="deleteDialog"
      :title="$t('general.confirm')"
      color="error"
      can-confirm
      @confirm="deleteOne"
    >
      <v-card-text>{{ $t('shopping-list.are-you-sure-you-want-to-delete-this-item') }}</v-card-text>
    </BaseDialog>
    <BasePageTitle divider>
      <template #title>
        {{ $t('shopping-list.shopping-lists') }}
      </template>
      <template #content>
        <v-btn color="primary" min-height="44" @click="createDialog = true">
          <v-icon start>
            {{ $globals.icons.createAlt }}
          </v-icon>
          {{ $t('shopping-list.create-shopping-list') }}
        </v-btn>
      </template>
    </BasePageTitle>

    <div class="shopping-overview-toolbar">
      <span class="text-body-2 font-weight-medium">{{ shoppingListChoices.length }} {{ $t('shopping-list.shopping-lists') }}</span>
      <v-checkbox
        v-model="preferences.viewAllLists"
        hide-details
        :label="$t('general.show-all')"
        class="my-0 flex-grow-0"
        color="primary"
      />
    </div>

    <section v-if="!shoppingListChoices.length" class="shopping-empty">
      <v-img width="80" height="80" src="/svgs/shopping-cart.svg" aria-hidden="true" />
      <h2>{{ $t('shopping-list.no-shopping-lists-found') }}</h2>
      <v-btn variant="tonal" color="primary" min-height="44" @click="createDialog = true">
        <v-icon start>
          {{ $globals.icons.createAlt }}
        </v-icon>
        {{ $t('shopping-list.create-shopping-list') }}
      </v-btn>
    </section>

    <section v-else class="shopping-list-grid">
      <v-card
        v-for="list in shoppingListChoices"
        :key="list.id"
        class="shopping-list-card"
        variant="outlined"
      >
        <NuxtLink :to="`/shopping-lists/${list.id}`" class="shopping-list-link">
          <v-icon color="primary" aria-hidden="true">
            {{ $globals.icons.cartCheck }}
          </v-icon>
          <span>
            {{ list.name }}
          </span>
          <v-icon class="ml-auto" aria-hidden="true">{{ $globals.icons.chevronRight }}</v-icon>
        </NuxtLink>
        <div class="shopping-list-card-actions">
          <span class="text-caption">{{ $t('general.owner') }}</span>
          <v-spacer />
          <v-tooltip :text="$t('general.owner')">
            <template #activator="{ props }">
              <v-btn
                icon
                variant="text"
                size="44"
                v-bind="props"
                :aria-label="$t('general.owner')"
                @click="toggleOwnerDialog(list)"
              >
                <v-icon>
                  {{ $globals.icons.user }}
                </v-icon>
              </v-btn>
            </template>
          </v-tooltip>
          <v-tooltip :text="$t('general.delete')">
            <template #activator="{ props }">
              <v-btn
                icon
                variant="text"
                size="44"
                v-bind="props"
                :aria-label="$t('general.delete')"
                @click="openDelete(list.id)"
              >
                <v-icon>
                  {{ $globals.icons.delete }}
                </v-icon>
              </v-btn>
            </template>
          </v-tooltip>
        </div>
      </v-card>
    </section>
  </v-container>
</template>

<script lang="ts">
import type { ShoppingListOut } from "~/lib/api/types/household";
import { useUserApi } from "~/composables/api";
import { useAsyncKey } from "~/composables/use-utils";
import { useShoppingListPreferences } from "~/composables/use-users/preferences";
import type { UserOut } from "~/lib/api/types/user";

export default defineNuxtComponent({
  setup() {
    const $auth = useMealieAuth();
    const i18n = useI18n();
    const ready = ref(false);
    const userApi = useUserApi();
    const route = useRoute();

    useSeoMeta({
      title: i18n.t("shopping-list.shopping-list"),
    });

    const groupSlug = computed(() => route.params.groupSlug || $auth.user.value?.groupSlug || "");
    const overrideDisableRedirect = ref(false);
    const disableRedirect = computed(() => route.query.disableRedirect === "true" || overrideDisableRedirect.value);
    const preferences = useShoppingListPreferences();

    const state = reactive({
      createName: "",
      createDialog: false,
      deleteDialog: false,
      deleteTarget: "",
      ownerDialog: false,
      ownerTarget: ref<ShoppingListOut | null>(null),
    });

    const { data: shoppingLists } = useAsyncData(useAsyncKey(), async () => {
      return await fetchShoppingLists();
    });

    const shoppingListChoices = computed(() => {
      if (!shoppingLists.value) {
        return [];
      }

      return shoppingLists.value.filter(list => preferences.value.viewAllLists || list.userId === $auth.user.value?.id);
    });

    // This has to appear before the shoppingListChoices watcher, otherwise that runs first and the redirect is not disabled
    watch(
      () => preferences.value.viewAllLists,
      () => {
        overrideDisableRedirect.value = true;
      },
    );

    watch(
      () => shoppingListChoices,
      () => {
        if (!disableRedirect.value && shoppingListChoices.value.length === 1) {
          navigateTo(`/shopping-lists/${shoppingListChoices.value[0].id}`);
        }
        else {
          ready.value = true;
        }
      },
      {
        deep: true,
      },
    );

    async function fetchShoppingLists() {
      const { data } = await userApi.shopping.lists.getAll(1, -1, { orderBy: "name", orderDirection: "asc" });

      if (!data) {
        return [];
      }

      return data.items;
    }

    async function refresh() {
      shoppingLists.value = await fetchShoppingLists();
    }

    async function createOne() {
      const { data } = await userApi.shopping.lists.createOne({ name: state.createName });

      if (data) {
        refresh();
        state.createName = "";
      }
    }

    async function toggleOwnerDialog(list: ShoppingListOut) {
      if (!state.ownerDialog) {
        state.ownerTarget = list;
        await fetchAllUsers();
      }
      state.ownerDialog = !state.ownerDialog;
    }

    // ===============================================================
    // Shopping List Edit User/Owner

    const allUsers = ref<UserOut[]>([]);
    const updateUserId = ref<string | undefined>();
    async function fetchAllUsers() {
      const { data } = await userApi.households.fetchMembers();
      if (!data) {
        return;
      }

      // update current user
      allUsers.value = data.items.sort((a, b) => ((a.fullName || "") < (b.fullName || "") ? -1 : 1));
      updateUserId.value = state.ownerTarget?.userId;
    }

    async function updateOwner() {
      if (!state.ownerTarget || !updateUserId.value) {
        return;
      }
      // user has not changed, so we should not update
      if (state.ownerTarget.userId === updateUserId.value) {
        return;
      }
      // get full list, so the move does not delete shopping list items
      const { data: fullList } = await userApi.shopping.lists.getOne(state.ownerTarget.id);
      if (!fullList) {
        return;
      }
      const { data } = await userApi.shopping.lists.updateOne(
        state.ownerTarget.id,
        { ...fullList, userId: updateUserId.value },
      );

      if (data) {
        refresh();
      }
    }

    function openDelete(id: string) {
      state.deleteDialog = true;
      state.deleteTarget = id;
    }

    async function deleteOne() {
      const { data } = await userApi.shopping.lists.deleteOne(state.deleteTarget);
      if (data) {
        refresh();
      }
    }

    return {
      ...toRefs(state),
      ready,
      groupSlug,
      preferences,
      shoppingListChoices,
      createOne,
      toggleOwnerDialog,
      allUsers,
      updateUserId,
      updateOwner,
      deleteOne,
      openDelete,
    };
  },
});
</script>

<style scoped>
.shopping-overview {
  max-width: 1040px;
}

.shopping-overview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.shopping-list-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
  gap: 16px;
}

.shopping-list-card {
  border: 1px solid rgba(var(--v-theme-on-background), 0.14);
  border-radius: 8px;
  background: rgb(var(--v-theme-surface));
}

.shopping-list-link {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 88px;
  padding: 20px;
  color: rgb(var(--v-theme-on-surface));
  font-size: 1.125rem;
  font-weight: 600;
  text-decoration: none;
  overflow-wrap: anywhere;
}

.shopping-list-link span {
  min-width: 0;
}

.shopping-list-link:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -3px;
}

.shopping-list-card-actions {
  display: flex;
  align-items: center;
  padding: 4px 12px 4px 20px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.shopping-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 48px 16px;
  text-align: center;
  border-block: 1px solid rgba(var(--v-theme-on-background), 0.12);
}

.shopping-empty h2 {
  font-size: 1.125rem;
  font-weight: 600;
}

.shopping-overview :deep(.v-btn:not(.v-btn--icon)) {
  border-radius: 6px;
  letter-spacing: 0;
}
</style>
