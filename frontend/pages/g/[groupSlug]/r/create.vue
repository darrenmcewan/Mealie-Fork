<template>
  <div>
    <v-container class="recipe-create-page">
      <BasePageTitle divider>
        <template #title>
          {{ $t('recipe.recipe-creation') }}
        </template>
      </BasePageTitle>
      <v-tabs
        v-model="subpage"
        color="primary"
        show-arrows
        class="recipe-create-tabs"
        :aria-label="$t('recipe.recipe-creation')"
      >
        <v-tab
          v-for="method in subpages.filter(item => !item.hide)"
          :key="method.value"
          :value="method.value"
          min-height="44"
        >
          <v-icon start>
            {{ method.icon }}
          </v-icon>
          {{ method.text }}
        </v-tab>
      </v-tabs>
      <section class="recipe-create-form">
        <NuxtPage />
      </section>
    </v-container>

    <AdvancedOnly>
      <v-container class="d-flex justify-center align-center my-4">
        <router-link
          :to="`/group/migrations`"
          class="text-primary"
        > {{ $t('recipe.looking-for-migrations') }}</router-link>
      </v-container>
    </AdvancedOnly>
  </div>
</template>

<script lang="ts">
import type { MenuItem } from "~/components/global/BaseOverflowButton.vue";
import AdvancedOnly from "~/components/global/AdvancedOnly.vue";

export default defineNuxtComponent({
  components: { AdvancedOnly },
  middleware: ["group-only"],
  setup() {
    const i18n = useI18n();
    const $auth = useMealieAuth();
    const { $appInfo, $globals } = useNuxtApp();

    useSeoMeta({
      title: i18n.t("general.create"),
    });

    const subpages = computed<MenuItem[]>(() => [
      {
        icon: $globals.icons.link,
        text: i18n.t("recipe.import-with-url"),
        value: "url",
      },
      {
        icon: $globals.icons.link,
        text: i18n.t("recipe.bulk-url-import"),
        value: "bulk",
      },
      {
        icon: $globals.icons.codeTags,
        text: i18n.t("recipe.import-from-html-or-json"),
        value: "html",
      },
      {
        icon: $globals.icons.fileImage,
        text: i18n.t("recipe.create-from-images"),
        value: "image",
        hide: !$appInfo.enableOpenaiImageServices,
      },
      {
        icon: $globals.icons.edit,
        text: i18n.t("recipe.create-recipe"),
        value: "new",
      },
      {
        icon: $globals.icons.zip,
        text: i18n.t("recipe.import-with-zip"),
        value: "zip",
      },
      {
        icon: $globals.icons.robot,
        text: i18n.t("recipe.debug-scraper"),
        value: "debug",
      },
    ]);

    const route = useRoute();
    const router = useRouter();
    const groupSlug = computed(() => route.params.groupSlug || $auth.user.value?.groupSlug || "");

    const subpage = computed({
      set(subpage: string) {
        router.push({ path: `/g/${groupSlug.value}/r/create/${subpage}`, query: route.query });
      },
      get() {
        return route.path.split("/").pop() ?? "url";
      },
    });

    return {
      groupSlug,
      subpages,
      subpage,
    };
  },
});
</script>

<style scoped>
.recipe-create-page {
  max-width: 1120px;
}

.recipe-create-tabs {
  margin-bottom: 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-background), 0.12);
}

.recipe-create-tabs :deep(.v-tab) {
  letter-spacing: 0;
  text-transform: none;
}

.recipe-create-form {
  max-width: 760px;
  color: rgb(var(--v-theme-on-background));
}

.recipe-create-form :deep(.v-field),
.recipe-create-form :deep(.v-btn) {
  border-radius: 6px !important;
}

.recipe-create-form :deep(.v-btn) {
  min-height: 44px;
  letter-spacing: 0;
}

.recipe-create-form :deep(.v-card-title) {
  padding: 0 0 16px;
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.5;
  white-space: normal;
}

.recipe-create-form :deep(.v-card-text) {
  padding: 0 0 16px;
  line-height: 1.6;
}

.recipe-create-form :deep(.v-card-actions) {
  padding: 16px 0;
  justify-content: flex-start !important;
}

@media (max-width: 600px) {
  .recipe-create-form :deep(.v-card-actions > div) {
    width: 100% !important;
  }
}
</style>
