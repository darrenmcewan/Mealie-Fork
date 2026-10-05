<template>
  <v-navigation-drawer
    id="mealie-navigation"
    v-model="showDrawer"
    class="mealie-sidebar d-print-none"
    :permanent="mdAndUp"
    :temporary="!mdAndUp"
    :width="264"
    :order="-1"
    :aria-label="$t('general.recipes')"
    :aria-hidden="!mdAndUp && !showDrawer"
    :inert="!mdAndUp && !showDrawer"
    touchless
    @keydown.esc.stop.prevent="showDrawer = false"
  >
    <LanguageDialog v-model="languageDialog" />
    <div class="sidebar-brand-row">
      <NuxtLink :to="homeLink" class="sidebar-brand">
        <span class="sidebar-brand-mark">
          <v-icon :icon="$globals.icons.primary" size="28" />
        </span>
        <span>Mealie</span>
      </NuxtLink>
      <v-btn
        v-if="!mdAndUp"
        variant="text"
        :icon="$globals.icons.close"
        :aria-label="$t('general.close')"
        @click="showDrawer = false"
      />
    </div>

    <div v-if="$slots.default" class="sidebar-create">
      <slot />
    </div>

    <template v-if="topLink">
      <v-list v-model:opened="openedLinks" class="sidebar-links" nav density="comfortable" color="primary">
        <template v-for="nav in topLink">
          <div v-if="!nav.restricted || isOwnGroup" :key="nav.key || nav.title">
            <!-- Multi Items -->
            <v-list-group
              v-if="nav.children"
              :key="(nav.key || nav.title) + 'multi-item'"
              :value="nav.key || nav.title"
              color="primary"
              :prepend-icon="nav.icon"
              :fluid="true"
            >
              <template #activator="{ props }">
                <v-list-item v-bind="props" :prepend-icon="nav.icon" :title="nav.title" />
              </template>

              <v-list-item
                v-for="child in nav.children"
                :key="child.key || child.title"
                exact
                :to="child.to"
                :prepend-icon="child.icon"
                :title="child.title"
                class="sidebar-child"
              />
            </v-list-group>

            <!-- Single Item -->
            <template v-else>
              <v-list-item
                :key="(nav.key || nav.title) + 'single-item'"
                exact
                link
                :to="nav.to"
                :prepend-icon="nav.icon"
                :title="nav.title"
              />
            </template>
          </div>
        </template>
      </v-list>
    </template>

    <!-- Secondary Links -->
    <template v-if="secondaryLinks.length > 0">
      <v-divider class="sidebar-divider" />
      <div class="sidebar-section-title">
        {{ secondaryHeader || $t('cookbook.cookbooks') }}
      </div>
      <v-list
        v-model:opened="openedLinks"
        class="sidebar-links"
        nav
        density="comfortable"
        color="primary"
        exact
      >
        <template v-for="nav in secondaryLinks">
          <div v-if="!nav.restricted || isOwnGroup" :key="nav.key || nav.title">
            <!-- Multi Items -->
            <v-list-group
              v-if="nav.children"
              :key="(nav.key || nav.title) + 'multi-item'"
              :value="nav.key || nav.title"
              color="primary"
              :prepend-icon="nav.icon"
              fluid
            >
              <template #activator="{ props }">
                <v-list-item v-bind="props" :prepend-icon="nav.icon" :title="nav.title" />
              </template>

              <v-list-item
                v-for="child in nav.children"
                :key="child.key || child.title"
                exact
                :to="child.to"
                class="sidebar-child"
                :prepend-icon="child.icon"
                :title="child.title"
              />
            </v-list-group>

            <!-- Single Item -->
            <v-list-item v-else :key="(nav.key || nav.title) + 'single-item'" exact link :to="nav.to">
              <template #prepend>
                <v-icon>{{ nav.icon }}</v-icon>
              </template>
              <v-list-item-title>{{ nav.title }}</v-list-item-title>
            </v-list-item>
          </div>
        </template>
      </v-list>
    </template>

    <!-- Bottom Navigation Links -->
    <template #append>
      <div class="sidebar-bottom">
        <v-list class="sidebar-links" nav density="comfortable" color="primary">
          <v-list-item to="/changelog" :prepend-icon="$globals.icons.timelineText" :title="$t('sidebar.changelog')" exact />
        </v-list>
        <v-list v-if="loggedIn && sessionUser" class="sidebar-links sidebar-user" nav density="comfortable" color="primary">
          <v-list-item v-if="isOwnGroup" :to="userFavoritesLink" :prepend-icon="$globals.icons.heart" :title="$t('user.favorite-recipes')" exact />
          <v-list-item :to="userProfileLink" :title="sessionUser.fullName || sessionUser.username" :subtitle="$t('profile.user-settings')" class="sidebar-profile" exact>
            <template #prepend>
              <UserAvatar list :user-id="sessionUser.id" :tooltip="false" />
            </template>
          </v-list-item>
        </v-list>
        <div class="sidebar-tools">
          <v-menu location="top start" :offset="8" :transition="false">
            <template #activator="{ props }">
              <v-btn v-bind="props" class="sidebar-settings" variant="text" :prepend-icon="$globals.icons.cog">
                {{ $t('general.settings') }}
              </v-btn>
            </template>
            <v-list class="shell-menu" density="comfortable" color="primary">
              <v-list-item :prepend-icon="$globals.icons.translate" :title="$t('sidebar.language')" @click="languageDialog = true" />
              <v-list-item v-if="loggedIn" :prepend-icon="$globals.icons.cog" :title="$t('profile.user-settings')" to="/user/profile" />
              <v-list-item v-if="canManage" :prepend-icon="$globals.icons.manageData" :title="$t('data-pages.data-management')" to="/group/data" />
              <v-divider v-if="isAdmin" class="my-2" />
              <v-list-item v-if="isAdmin" :prepend-icon="$globals.icons.wrench" :title="$t('settings.admin-settings')" to="/admin/site-settings" />
            </v-list>
          </v-menu>
          <v-btn
            variant="text"
            :icon="$vuetify.theme.current.dark ? $globals.icons.weatherSunny : $globals.icons.weatherNight"
            :aria-label="$vuetify.theme.current.dark ? $t('settings.theme.light-mode') : $t('settings.theme.dark-mode')"
            :title="$vuetify.theme.current.dark ? $t('settings.theme.light-mode') : $t('settings.theme.dark-mode')"
            @click="toggleDark"
          />
        </div>
      </div>
    </template>
  </v-navigation-drawer>
</template>

<script lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { SidebarLinks } from "~/types/application-types";
import UserAvatar from "~/components/Domain/User/UserAvatar.vue";
import { useToggleDarkMode } from "~/composables/use-utils";

export default defineNuxtComponent({
  components: {
    UserAvatar,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: false,
      default: false,
    },
    user: {
      type: Object,
      default: null,
    },
    topLink: {
      type: Array as () => SidebarLinks,
      required: true,
    },
    secondaryLinks: {
      type: Array as () => SidebarLinks,
      required: false,
      default: () => [],
    },
    secondaryHeader: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue"],
  setup(props, context) {
    const $auth = useMealieAuth();
    const route = useRoute();
    const { mdAndUp } = useDisplay();
    const { loggedIn, isOwnGroup } = useLoggedInState();
    const isAdmin = computed(() => $auth.user.value?.admin);
    const canManage = computed(() => $auth.user.value?.canManage);

    const userFavoritesLink = computed(() => $auth.user.value ? `/user/${$auth.user.value.id}/favorites` : undefined);
    const userProfileLink = computed(() => $auth.user.value ? "/user/profile" : undefined);
    const homeLink = computed(() => {
      const groupSlug = route.params.groupSlug as string || $auth.user.value?.groupSlug;
      return groupSlug ? `/g/${groupSlug}` : "/";
    });

    const toggleDark = useToggleDarkMode();

    const state = reactive({
      openedLinks: [] as string[],
      languageDialog: false as boolean,
    });
    // model to control the drawer
    const showDrawer = computed({
      get: () => mdAndUp.value || props.modelValue,
      set: value => context.emit("update:modelValue", value),
    });

    const allLinks = computed(() => [...props.topLink, ...props.secondaryLinks]);
    watch([allLinks, () => route.path], ([links]) => {
      const openedLinks = new Set(state.openedLinks);
      links.forEach((link) => {
        if (link.childrenStartExpanded || link.children?.some(child => child.to && (route.path === child.to || route.path.startsWith(`${child.to}/`)))) {
          openedLinks.add(link.key || link.title);
        }
      });
      state.openedLinks = [...openedLinks];
    }, { immediate: true });

    watch(() => route.fullPath, () => {
      if (!mdAndUp.value) showDrawer.value = false;
    });
    watch(mdAndUp, () => context.emit("update:modelValue", false));

    return {
      ...toRefs(state),
      userFavoritesLink,
      userProfileLink,
      homeLink,
      mdAndUp,
      showDrawer,
      loggedIn,
      isAdmin,
      canManage,
      isOwnGroup,
      sessionUser: $auth.user,
      toggleDark,
    };
  },
});
</script>

<style scoped>
.mealie-sidebar {
  background: rgb(var(--v-theme-surface));
  border-right: 1px solid var(--mealie-border);
  transition: transform var(--mealie-motion-enter, 260ms) var(--mealie-ease-out, ease-out);
}

.mealie-sidebar:not(.v-navigation-drawer--active) {
  transition-duration: 180ms;
  transition-timing-function: var(--mealie-ease-in, ease-in);
}

.sidebar-brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 80px;
  padding: 16px 20px;
}

.sidebar-brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  color: rgb(var(--v-theme-on-surface));
  font-family: var(--mealie-display-font);
  font-size: 26px;
  font-weight: 600;
  letter-spacing: 0;
  text-decoration: none;
}

.sidebar-brand-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
}

.sidebar-create {
  padding: 4px 20px 20px;
}

.sidebar-links {
  padding: 8px 12px;
  background: transparent;
}

.sidebar-links :deep(.v-list-item) {
  min-height: 48px;
  padding-inline: 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  transition:
    background-color var(--mealie-motion-fast, 120ms) ease-out,
    transform var(--mealie-motion-fast, 120ms) ease-out;
}

.sidebar-links :deep(.v-list-item-title) {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
}

.sidebar-links :deep(.v-list-item--active) {
  box-shadow: inset 3px 0 0 rgb(var(--v-theme-primary));
}

.sidebar-links :deep(.v-list-item--active .v-list-item-title) {
  font-weight: 700;
}

.sidebar-links :deep(.v-list-item__prepend > .v-icon ~ .v-list-item__spacer) {
  width: 14px;
}

.sidebar-links :deep(.sidebar-child) {
  padding-inline-start: 24px !important;
}

.sidebar-divider {
  margin: 12px 24px 16px;
}

.sidebar-section-title {
  padding: 0 24px;
  color: var(--mealie-muted);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
}

.sidebar-bottom {
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  border-top: 1px solid var(--mealie-border);
  background: rgb(var(--v-theme-surface));
}

.sidebar-profile :deep(.v-list-item__prepend) {
  margin-inline-end: 12px;
}

.sidebar-profile :deep(.v-list-item-subtitle) {
  color: var(--mealie-muted);
  opacity: 1;
  font-size: 12px;
}

.sidebar-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
}

.sidebar-settings {
  flex: 1;
  justify-content: flex-start;
}

.sidebar-tools :deep(.v-btn),
.sidebar-brand-row :deep(.v-btn) {
  min-width: 44px;
  min-height: 44px;
  border-radius: 6px;
}

:global(.mealie-sidebar + .v-navigation-drawer__scrim.fade-transition-enter-active) {
  transition: opacity var(--mealie-motion-standard, 200ms) ease-out !important;
}

:global(.mealie-sidebar + .v-navigation-drawer__scrim.fade-transition-leave-active) {
  transition: opacity 180ms ease-in !important;
}

.shell-menu {
  font-family: var(--mealie-font, "Plus Jakarta Sans", sans-serif);
}

.shell-menu :deep(.v-list-item) {
  min-height: 48px;
}

.sidebar-brand:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 4px;
  border-radius: 6px;
}

.sidebar-brand:active,
.sidebar-links :deep(.v-list-item:active),
.shell-menu :deep(.v-list-item:active),
.sidebar-tools :deep(.v-btn:active) {
  transform: scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
  .mealie-sidebar,
  .sidebar-links :deep(.v-list-item),
  :global(.mealie-sidebar + .v-navigation-drawer__scrim) {
    transition: none !important;
  }

  .sidebar-brand:active,
  .sidebar-links :deep(.v-list-item:active),
  .shell-menu :deep(.v-list-item:active),
  .sidebar-tools :deep(.v-btn:active) {
    transform: none;
  }
}
</style>
