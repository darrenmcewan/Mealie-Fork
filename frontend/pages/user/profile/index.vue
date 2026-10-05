<template>
  <v-container v-if="user" class="mb-8">
    <header class="d-flex align-center flex-wrap ga-4 mb-8">
      <UserAvatar
        :tooltip="false"
        size="64"
        :user-id="user.id"
      />
      <div class="flex-grow-1">
        <h1 class="text-h5 font-weight-bold">
          {{ $t('profile.welcome-user', [user.fullName]) }}
        </h1>
        <p class="text-body-2 text-medium-emphasis mb-0">
          {{ $t('profile.description') }}
        </p>
      </div>
      <div>
        <v-btn
          v-if="user.canInvite"
          variant="outlined"
          :prepend-icon="$globals.icons.createAlt"
          :text="$t('profile.get-invite-link')"
          @click="inviteDialog = true"
        />
        <UserInviteDialog v-model="inviteDialog" />
      </div>
    </header>
    <section class="my-3">
      <div>
        <h2 class="text-h6">
          {{ $t('profile.account-summary') }}
        </h2>
        <p>{{ $t('profile.account-summary-description') }}</p>
      </div>
      <section class="mt-6">
        <h3 class="text-subtitle-1 font-weight-bold">
          {{ $t('profile.household-statistics') }}
        </h3>
        <p class="text-body-2 text-medium-emphasis mb-4">
          {{ $t('profile.household-statistics-description') }}
        </p>
        <div class="d-flex flex-wrap ga-3">
          <StatsCards
            v-for="(value, key) in stats"
            :key="`${key}-${value}`"
            :min-width="$vuetify.display.xs ? '100%' : '158'"
            :icon="getStatsIcon(key)"
            :to="getStatsTo(key)"
          >
            <template #title>
              {{ getStatsTitle(key) }}
            </template>
            <template #value>
              {{ value }}
            </template>
          </StatsCards>
        </div>
      </section>
    </section>
    <v-divider class="my-7" />
    <section>
      <div>
        <h2 class="text-h6">
          {{ $t('profile.personal') }}
        </h2>
        <p>{{ $t('profile.personal-description') }}</p>
      </div>
      <v-row tag="section">
        <v-col
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.manage-user-profile'), to: `/user/profile/edit` }"
            image="/svgs/manage-profile.svg"
          >
            <template #title>
              {{ $t('profile.user-settings') }}
            </template>
            {{ $t('profile.user-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :link="{ text: $t('profile.manage-your-api-tokens'), to: `/user/profile/api-tokens` }"
              image="/svgs/manage-api-tokens.svg"
            >
              <template #title>
                {{ $t('settings.token.api-tokens') }}
              </template>
              {{ $t('profile.api-tokens-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
    <v-divider class="my-7" />
    <section>
      <div>
        <h2 class="text-h6">
          {{ $t('household.household') }}
        </h2>
        <p>{{ $t('profile.household-description') }}</p>
      </div>
      <v-row tag="section">
        <v-col
          v-if="user.canManageHousehold"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.household-settings'), to: `/household` }"
            image="/svgs/manage-group-settings.svg"
          >
            <template #title>
              {{ $t('profile.household-settings') }}
            </template>
            {{ $t('profile.household-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.manage-cookbooks'), to: `/g/${groupSlug}/cookbooks` }"
            image="/svgs/manage-cookbooks.svg"
          >
            <template #title>
              {{ $t('sidebar.cookbooks') }}
            </template>
            {{ $t('profile.cookbooks-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          v-if="user.canManage"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.manage-members'), to: `/household/members` }"
            image="/svgs/manage-members.svg"
          >
            <template #title>
              {{ $t('profile.members') }}
            </template>
            {{ $t('profile.members-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            v-if="user.advanced"
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :link="{ text: $t('profile.manage-webhooks'), to: `/household/webhooks` }"
              image="/svgs/manage-webhooks.svg"
            >
              <template #title>
                {{ $t('settings.webhooks.webhooks') }}
              </template>
              {{ $t('profile.webhooks-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :link="{ text: $t('profile.manage-notifiers'), to: `/household/notifiers` }"
              image="/svgs/manage-notifiers.svg"
            >
              <template #title>
                {{ $t('profile.notifiers') }}
              </template>
              {{ $t('profile.notifiers-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
    <v-divider class="my-7" />
    <section v-if="user.canManage || user.canOrganize || user.advanced">
      <div>
        <h2 class="text-h6">
          {{ $t('group.group') }}
        </h2>
        <p>{{ $t('profile.group-description') }}</p>
      </div>
      <v-row tag="section">
        <v-col
          v-if="user.canManage"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.group-settings'), to: `/group` }"
            image="/svgs/manage-group-settings.svg"
          >
            <template #title>
              {{ $t('profile.group-settings') }}
            </template>
            {{ $t('profile.group-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          v-if="user.canOrganize"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.manage-data'), to: `/group/data/foods` }"
            image="/svgs/manage-recipes.svg"
          >
            <template #title>
              {{ $t('profile.manage-data') }}
            </template>
            {{ $t('profile.manage-data-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :link="{ text: $t('profile.manage-data-migrations'), to: `/group/migrations` }"
              image="/svgs/manage-data-migrations.svg"
            >
              <template #title>
                {{ $t('profile.data-migrations') }}
              </template>
              {{ $t('profile.data-migrations-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
  </v-container>
</template>

<script lang="ts">
import UserProfileLinkCard from "@/components/Domain/User/UserProfileLinkCard.vue";
import { useUserApi } from "~/composables/api";
import UserAvatar from "@/components/Domain/User/UserAvatar.vue";
import { useAsyncKey } from "~/composables/use-utils";
import StatsCards from "~/components/global/StatsCards.vue";
import type { UserOut } from "~/lib/api/types/user";
import UserInviteDialog from "~/components/Domain/User/UserInviteDialog.vue";

export default defineNuxtComponent({
  name: "UserProfile",
  components: {
    UserInviteDialog,
    UserProfileLinkCard,
    UserAvatar,
    StatsCards,
  },
  scrollToTop: true,
  async setup() {
    const i18n = useI18n();
    const $auth = useMealieAuth();
    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug || $auth.user.value?.groupSlug || "");

    useSeoMeta({
      title: i18n.t("settings.profile"),
    });

    const user = computed<UserOut | null>(() => $auth.user.value);

    const inviteDialog = ref(false);
    const api = useUserApi();

    const { data: stats } = useAsyncData(useAsyncKey(), async () => {
      const { data } = await api.households.statistics();

      if (data) {
        return data;
      }
    });

    const statsText: { [key: string]: string } = {
      totalRecipes: i18n.t("general.recipes"),
      totalUsers: i18n.t("user.users"),
      totalCategories: i18n.t("sidebar.categories"),
      totalTags: i18n.t("sidebar.tags"),
      totalTools: i18n.t("tool.tools"),
    };

    function getStatsTitle(key: string) {
      return statsText[key] ?? "unknown";
    }

    const { $globals } = useNuxtApp();

    const iconText: { [key: string]: string } = {
      totalUsers: $globals.icons.user,
      totalCategories: $globals.icons.categories,
      totalTags: $globals.icons.tags,
      totalTools: $globals.icons.potSteam,
    };

    function getStatsIcon(key: string) {
      return iconText[key] ?? $globals.icons.primary;
    }

    const statsTo = computed<{ [key: string]: string }>(() => {
      return {
        totalRecipes: `/g/${groupSlug.value}/`,
        totalUsers: "/household/members",
        totalCategories: `/g/${groupSlug.value}/recipes/categories`,
        totalTags: `/g/${groupSlug.value}/recipes/tags`,
        totalTools: `/g/${groupSlug.value}/recipes/tools`,
      };
    });

    function getStatsTo(key: string) {
      return statsTo.value[key] ?? "unknown";
    }

    return {
      groupSlug,
      getStatsTitle,
      getStatsIcon,
      getStatsTo,
      inviteDialog,
      stats,
      user,
    };
  },
});
</script>
