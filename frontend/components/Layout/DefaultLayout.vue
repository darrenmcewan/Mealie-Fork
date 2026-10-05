<template>
  <v-app class="mealie-shell">
    <a class="shell-skip-link" href="#main-content">
      {{ $t("general.skip-to-content") }}
    </a>
    <TheSnackbar />

    <AppHeader>
      <v-btn
        class="d-md-none"
        variant="text"
        :icon="$globals.icons.menu"
        :aria-label="$t('general.menu')"
        :aria-expanded="sidebar"
        aria-controls="mealie-navigation"
        @click.stop="sidebar = !sidebar"
      />
    </AppHeader>

    <AppSidebar
      v-model="sidebar"
      :top-link="topLinks"
      :secondary-links="cookbookLinks || []"
    >
      <v-menu
        location="bottom start"
        :offset="8"
        :transition="false"
      >
        <template #activator="{ props }">
          <v-btn
            v-if="isOwnGroup"
            block
            :height="48"
            class="shell-create-button"
            v-bind="props"
            variant="flat"
            color="primary"
          >
            <v-icon
              start
              size="22"
            >
              {{ $globals.icons.createAlt }}
            </v-icon>
            {{ $t("general.create") }}
          </v-btn>
        </template>
        <v-list
          density="comfortable"
          class="shell-create-menu"
          variant="flat"
        >
          <template v-for="(item, index) in createLinks">
            <div
              v-if="!item.hide"
              :key="item.title"
            >
              <v-divider
                v-if="item.insertDivider"
                :key="index"
                class="mx-2"
              />
              <v-list-item
                v-if="!item.restricted || isOwnGroup"
                :key="item.title"
                :to="item.to"
                exact
                class="shell-create-item"
              >
                <template #prepend>
                  <v-icon
                    size="22"
                    :icon="item.icon"
                  />
                </template>
                <v-list-item-title class="font-weight-medium">
                  {{ item.title }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ item.subtitle }}
                </v-list-item-subtitle>
              </v-list-item>
            </div>
          </template>
        </v-list>
      </v-menu>
    </AppSidebar>
    <v-main id="main-content" tabindex="-1" class="shell-main">
      <div class="shell-page">
        <NuxtPage />
      </div>
    </v-main>
  </v-app>
</template>

<script lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { SideBarLink } from "~/types/application-types";
import { useCookbookPreferences } from "~/composables/use-users/preferences";
import { useCookbookStore, usePublicCookbookStore } from "~/composables/store/use-cookbook-store";
import type { ReadCookBook } from "~/lib/api/types/cookbook";

export default defineNuxtComponent({
  setup() {
    const i18n = useI18n();
    const { $appInfo, $globals } = useNuxtApp();
    const $auth = useMealieAuth();
    const { isOwnGroup } = useLoggedInState();

    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

    const cookbookPreferences = useCookbookPreferences();
    const ownCookbookStore = useCookbookStore(i18n);
    const publicCookbookStoreCache = ref<Record<string, ReturnType<typeof usePublicCookbookStore>>>({});

    function getPublicCookbookStore(slug: string) {
      if (!publicCookbookStoreCache.value[slug]) {
        publicCookbookStoreCache.value[slug] = usePublicCookbookStore(slug, i18n);
      }
      return publicCookbookStoreCache.value[slug];
    }

    const cookbooks = computed(() => {
      if (isOwnGroup.value) {
        return ownCookbookStore.store.value;
      }
      else if (groupSlug.value) {
        const publicStore = getPublicCookbookStore(groupSlug.value);
        return unref(publicStore.store);
      }
      return [];
    });

    const showImageImport = computed(() => $appInfo.enableOpenaiImageServices);
    const languageDialog = ref<boolean>(false);

    const sidebar = ref<boolean>(false);

    function cookbookAsLink(cookbook: ReadCookBook): SideBarLink {
      return {
        key: cookbook.slug || "",
        icon: $globals.icons.pages,
        title: cookbook.name,
        to: `/g/${groupSlug.value}/cookbooks/${cookbook.slug || ""}`,
        restricted: false,
      };
    }

    const currentUserHouseholdId = computed(() => $auth.user.value?.householdId);
    const cookbookLinks = computed<SideBarLink[]>(() => {
      if (!cookbooks.value?.length) {
        return [];
      }

      const sortedCookbooks = [...cookbooks.value].sort((a, b) => (a.position || 0) - (b.position || 0));

      const ownLinks: SideBarLink[] = [];
      const links: SideBarLink[] = [];
      const cookbooksByHousehold = sortedCookbooks.reduce((acc, cookbook) => {
        const householdName = cookbook.household?.name || "";
        (acc[householdName] ||= []).push(cookbook);
        return acc;
      }, {} as Record<string, ReadCookBook[]>);

      Object.entries(cookbooksByHousehold).forEach(([householdName, cookbooks]) => {
        if (!cookbooks.length) {
          return;
        }
        if (cookbooks[0].householdId === currentUserHouseholdId.value) {
          ownLinks.push(...cookbooks.map(cookbookAsLink));
        }
        else {
          links.push({
            key: householdName,
            icon: $globals.icons.book,
            title: householdName,
            children: cookbooks.map(cookbookAsLink),
            restricted: false,
          });
        }
      });

      links.sort((a, b) => a.title.localeCompare(b.title));
      if ($auth.user.value && cookbookPreferences.value.hideOtherHouseholds) {
        return ownLinks;
      }
      else {
        return [...ownLinks, ...links];
      }
    });

    const createLinks = computed(() => [
      {
        insertDivider: false,
        icon: $globals.icons.link,
        title: i18n.t("general.import"),
        subtitle: i18n.t("new-recipe.import-by-url"),
        to: `/g/${groupSlug.value}/r/create/url`,
        restricted: true,
        hide: false,
      },
      {
        insertDivider: false,
        icon: $globals.icons.fileImage,
        title: i18n.t("recipe.create-from-images"),
        subtitle: i18n.t("recipe.create-recipe-from-an-image"),
        to: `/g/${groupSlug.value}/r/create/image`,
        restricted: true,
        hide: !showImageImport.value,
      },
      {
        insertDivider: true,
        icon: $globals.icons.edit,
        title: i18n.t("general.create"),
        subtitle: i18n.t("new-recipe.create-manually"),
        to: `/g/${groupSlug.value}/r/create/new`,
        restricted: true,
        hide: false,
      },
    ]);

    const topLinks = computed<SideBarLink[]>(() => [
      {
        icon: $globals.icons.silverwareForkKnife,
        to: `/g/${groupSlug.value}`,
        title: i18n.t("general.recipes"),
        restricted: false,
      },
      {
        icon: $globals.icons.search,
        to: `/g/${groupSlug.value}/recipes/finder`,
        title: i18n.t("recipe-finder.recipe-finder"),
        restricted: false,
      },
      {
        icon: $globals.icons.calendarMultiselect,
        title: i18n.t("meal-plan.meal-planner"),
        to: "/household/mealplan/planner/view",
        restricted: true,
      },
      {
        icon: $globals.icons.formatListCheck,
        title: i18n.t("shopping-list.shopping-lists"),
        to: "/shopping-lists",
        restricted: true,
      },
      {
        icon: $globals.icons.timelineText,
        title: i18n.t("recipe.timeline"),
        to: `/g/${groupSlug.value}/recipes/timeline`,
        restricted: true,
      },
      {
        icon: $globals.icons.chefHat,
        title: i18n.t("cooking-insights.title"),
        to: `/g/${groupSlug.value}/recipes/insights`,
        restricted: true,
      },
      {
        icon: $globals.icons.book,
        to: `/g/${groupSlug.value}/cookbooks`,
        title: i18n.t("cookbook.cookbooks"),
        restricted: true,
      },
      {
        icon: $globals.icons.organizers,
        title: i18n.t("general.organizers"),
        restricted: true,
        children: [
          {
            icon: $globals.icons.categories,
            to: `/g/${groupSlug.value}/recipes/categories`,
            title: i18n.t("sidebar.categories"),
            restricted: true,
          },
          {
            icon: $globals.icons.tags,
            to: `/g/${groupSlug.value}/recipes/tags`,
            title: i18n.t("sidebar.tags"),
            restricted: true,
          },
          {
            icon: $globals.icons.potSteam,
            to: `/g/${groupSlug.value}/recipes/tools`,
            title: i18n.t("tool.tools"),
            restricted: true,
          },
        ],
      },
    ]);

    return {
      groupSlug,
      cookbookLinks,
      createLinks,
      topLinks,
      isOwnGroup,
      languageDialog,
      sidebar,
    };
  },
});
</script>

<style scoped>
.shell-skip-link {
  position: fixed;
  z-index: 3000;
  inset-block-start: 8px;
  inset-inline-start: 16px;
  padding: 12px 16px;
  border-radius: 6px;
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  font-weight: 600;
  transform: translateY(-180%);
}

.shell-skip-link:focus {
  transform: none;
}

.shell-main {
  min-width: 0;
}

.shell-page {
  min-width: 0;
  min-height: calc(100dvh - 72px);
  padding: 12px 12px 32px;
  animation: shell-entrance var(--mealie-motion-standard, 200ms) var(--mealie-ease-out, ease-out) both;
}

.shell-create-button {
  border-radius: 6px;
}

.shell-create-menu {
  min-width: 264px;
  max-width: min(360px, calc(100vw - 32px));
  padding: 8px;
  font-family: var(--mealie-font, "Plus Jakarta Sans", sans-serif);
}

.shell-create-item {
  min-height: 64px;
  border-radius: 6px;
}

.shell-create-item :deep(.v-list-item-title) {
  font-size: 14px;
}

.shell-create-item :deep(.v-list-item-subtitle) {
  margin-top: 4px;
  color: var(--mealie-muted, rgb(var(--v-theme-on-surface-variant)));
  font-size: 12px;
  line-height: 1.5;
  white-space: normal;
  opacity: 1;
}

.shell-create-item:active {
  transform: scale(0.98);
}

@keyframes shell-entrance {
  from {
    opacity: 0;
    transform: translateY(6px);
  }

  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 959px) {
  .shell-page {
    padding: 4px 0 24px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .shell-page {
    animation: none;
  }

  .shell-create-item:active {
    transform: none;
  }
}
</style>
