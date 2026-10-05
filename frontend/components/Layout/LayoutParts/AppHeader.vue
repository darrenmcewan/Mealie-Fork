<template>
  <v-app-bar
    :height="72"
    :elevation="0"
    color="surface"
    class="mealie-header d-print-none"
  >
    <slot />
    <NuxtLink :to="routerLink" class="header-brand">
      <v-icon :icon="$globals.icons.primary" size="28" color="primary" />
      <span>Mealie</span>
    </NuxtLink>
    <RecipeDialogSearch ref="domSearchDialog" />
    <v-spacer />
    <template v-if="menu">
      <v-btn
        class="header-search"
        :class="{ 'header-search-wide': smAndUp }"
        variant="text"
        :icon="!smAndUp"
        :aria-label="$t('search.search')"
        aria-haspopup="dialog"
        @click="activateSearch"
      >
        <v-icon :start="smAndUp" :icon="$globals.icons.search" />
        <span v-if="smAndUp">{{ $t('search.search') }}</span>
      </v-btn>
      <v-btn
        v-if="loggedIn"
        class="header-account"
        variant="text"
        :icon="!smAndUp"
        :aria-label="$t('user.logout')"
        :title="$t('user.logout')"
        @click="logout()"
      >
        <v-icon :start="smAndUp" :icon="$globals.icons.logout" />
        <span v-if="smAndUp">{{ $t('user.logout') }}</span>
      </v-btn>
      <v-btn
        v-else
        class="header-account"
        variant="text"
        :icon="!smAndUp"
        :aria-label="$t('user.login')"
        :title="$t('user.login')"
        to="/login"
      >
        <v-icon :start="smAndUp" :icon="$globals.icons.user" />
        <span v-if="smAndUp">{{ $t('user.login') }}</span>
      </v-btn>
    </template>
  </v-app-bar>
</template>

<script lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import RecipeDialogSearch from "~/components/Domain/Recipe/RecipeDialogSearch.vue";

export default defineNuxtComponent({
  components: { RecipeDialogSearch },
  props: {
    menu: {
      type: Boolean,
      default: true,
    },
  },
  setup(props) {
    const $auth = useMealieAuth();
    const { loggedIn } = useLoggedInState();
    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");
    const { smAndUp } = useDisplay();

    const routerLink = computed(() => groupSlug.value ? `/g/${groupSlug.value}` : "/");
    const domSearchDialog = ref<InstanceType<typeof RecipeDialogSearch> | null>(null);

    function activateSearch() {
      domSearchDialog.value?.open();
    }

    function handleKeyEvent(e: KeyboardEvent) {
      const activeElement = document.activeElement;
      const isEditing = activeElement instanceof HTMLElement
        && (activeElement.isContentEditable || Boolean(activeElement.closest("input, textarea, select, [contenteditable='true']")));
      if (props.menu && e.key === "/" && !e.defaultPrevented && !e.ctrlKey && !e.metaKey && !e.altKey && !isEditing) {
        e.preventDefault();
        activateSearch();
      }
    }

    onMounted(() => {
      document.addEventListener("keydown", handleKeyEvent);
    });

    onBeforeUnmount(() => {
      document.removeEventListener("keydown", handleKeyEvent);
    });

    async function logout() {
      try {
        await $auth.signOut("/login?direct=1");
      }
      catch (e) {
        console.error(e);
      }
    }

    return {
      activateSearch,
      domSearchDialog,
      routerLink,
      loggedIn,
      logout,
      smAndUp,
    };
  },
});
</script>

<style scoped>
.mealie-header {
  border-bottom: 1px solid var(--mealie-border);
}

.mealie-header :deep(.v-toolbar__content) {
  gap: 12px;
  padding-inline: 24px;
}

.header-brand {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  gap: 10px;
  min-height: 44px;
  color: rgb(var(--v-theme-on-surface));
  font-family: var(--mealie-display-font);
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0;
  text-decoration: none;
}

.header-brand:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 4px;
  border-radius: 6px;
}

.mealie-header :deep(.v-btn) {
  min-width: 44px;
  min-height: 44px;
  border-radius: 6px;
}

.header-search {
  flex-shrink: 0;
  color: var(--mealie-muted);
}

.header-search-wide {
  justify-content: flex-start;
  width: min(360px, 35vw);
  border: 1px solid var(--mealie-border);
  background: rgb(var(--v-theme-background));
}

.header-search-wide :deep(.v-btn__content) {
  justify-content: flex-start;
  width: 100%;
  font-size: 14px;
}

.header-account {
  flex-shrink: 0;
}

.header-brand:active {
  transform: scale(0.98);
}

@media (max-width: 599px) {
  .mealie-header :deep(.v-toolbar__content) {
    gap: 4px;
    padding-inline: 8px;
  }

  .header-brand {
    gap: 6px;
    font-size: 22px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .header-brand:active {
    transform: none;
  }
}
</style>
