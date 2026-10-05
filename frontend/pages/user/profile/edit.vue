<template>
  <v-container class="narrow-container settings-page">
    <header class="d-flex align-center justify-space-between flex-wrap ga-4 mb-6">
      <h1 class="text-h5 font-weight-bold">
        {{ $t("profile.user-settings") }}
      </h1>
      <div class="d-flex align-center ga-3">
        <UserAvatar
          :tooltip="false"
          size="64"
          :user-id="userCopy.id!"
        />
        <AppButtonUpload
          file-name="profile"
          accept="image/*"
          :url="`/api/users/${userCopy.id}/image`"
          @uploaded="$auth.refresh()"
        />
      </div>
    </header>

    <section class="mt-5">
      <ToggleState tag="article">
        <template #activator="{ toggle, state }">
          <v-btn
            v-if="!state"
            color="primary"
            variant="outlined"
            @click="toggle"
          >
            <v-icon start>
              {{ $globals.icons.lock }}
            </v-icon>
            {{ $t("settings.change-password") }}
          </v-btn>
          <v-btn
            v-else
            color="primary"
            variant="outlined"
            @click="toggle"
          >
            <v-icon start>
              {{ $globals.icons.user }}
            </v-icon>
            {{ $t("settings.profile") }}
          </v-btn>
        </template>
        <template #default="{ state }">
          <v-slide-x-transition
            leave-absolute
            hide-on-leave
          >
            <div
              v-if="!state"
              key="personal-info"
            >
              <BaseCardSectionTitle
                class="mt-6"
                :title="$t('profile.personal-information')"
              />
              <v-card
                tag="article"
                variant="outlined"
              >
                <v-card-text class="pb-0">
                  <v-form ref="userUpdate">
                    <v-text-field
                      v-model="userCopy.username"
                      name="username"
                      autocomplete="username"
                      :label="$t('user.username')"
                      required
                      validate-on="blur"
                      density="comfortable"
                      variant="outlined"
                    />
                    <v-text-field
                      v-model="userCopy.fullName"
                      name="fullName"
                      autocomplete="name"
                      :label="$t('user.full-name')"
                      required
                      validate-on="blur"
                      density="comfortable"
                      variant="outlined"
                    />
                    <v-text-field
                      v-model="userCopy.email"
                      name="email"
                      autocomplete="email"
                      type="email"
                      :label="$t('user.email')"
                      validate-on="blur"
                      required
                      density="comfortable"
                      variant="outlined"
                    />
                  </v-form>
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <BaseButton
                    update
                    @click="updateUser"
                  />
                </v-card-actions>
              </v-card>
            </div>
            <div
              v-else
              key="change-password"
            >
              <BaseCardSectionTitle
                class="mt-6"
                :title="$t('settings.change-password')"
              />
              <v-card variant="outlined">
                <v-card-text class="pb-0">
                  <v-form ref="passChange">
                    <v-text-field
                      v-model="password.current"
                      name="currentPassword"
                      autocomplete="current-password"
                      :prepend-inner-icon="$globals.icons.lock"
                      :label="$t('user.current-password')"
                      validate-on="blur"
                      :type="showPassword ? 'text' : 'password'"
                      :rules="[validators.minLength(1)]"
                      density="comfortable"
                      variant="outlined"
                    >
                      <template #append-inner>
                        <v-btn
                          :icon="showPassword ? $globals.icons.eyeOff : $globals.icons.eye"
                          :aria-label="`${$t('user.current-password')}: ${$t('general.toggle-view')}`"
                          :title="`${$t('user.current-password')}: ${$t('general.toggle-view')}`"
                          :aria-pressed="showPassword"
                          variant="text"
                          type="button"
                          @click="showPassword = !showPassword"
                        />
                      </template>
                    </v-text-field>
                    <v-text-field
                      v-model="password.newOne"
                      name="newPassword"
                      autocomplete="new-password"
                      :prepend-inner-icon="$globals.icons.lock"
                      :label="$t('user.new-password')"
                      :type="showPassword ? 'text' : 'password'"
                      :rules="[validators.minLength(8)]"
                      density="comfortable"
                      variant="outlined"
                    >
                      <template #append-inner>
                        <v-btn
                          :icon="showPassword ? $globals.icons.eyeOff : $globals.icons.eye"
                          :aria-label="`${$t('user.new-password')}: ${$t('general.toggle-view')}`"
                          :title="`${$t('user.new-password')}: ${$t('general.toggle-view')}`"
                          :aria-pressed="showPassword"
                          variant="text"
                          type="button"
                          @click="showPassword = !showPassword"
                        />
                      </template>
                    </v-text-field>
                    <v-text-field
                      v-model="password.newTwo"
                      name="newPasswordConfirm"
                      autocomplete="new-password"
                      :prepend-inner-icon="$globals.icons.lock"
                      :label="$t('user.confirm-password')"
                      :rules="[password.newOne === password.newTwo || $t('user.password-must-match')]"
                      validate-on="blur"
                      :type="showPassword ? 'text' : 'password'"
                      density="comfortable"
                      variant="outlined"
                    >
                      <template #append-inner>
                        <v-btn
                          :icon="showPassword ? $globals.icons.eyeOff : $globals.icons.eye"
                          :aria-label="`${$t('user.confirm-password')}: ${$t('general.toggle-view')}`"
                          :title="`${$t('user.confirm-password')}: ${$t('general.toggle-view')}`"
                          :aria-pressed="showPassword"
                          variant="text"
                          type="button"
                          @click="showPassword = !showPassword"
                        />
                      </template>
                    </v-text-field>
                    <UserPasswordStrength v-model="password.newOne" />
                  </v-form>
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <BaseButton
                    update
                    :disabled="!passwordsMatch || password.current.length < 0"
                    @click="updatePassword"
                  />
                </v-card-actions>
              </v-card>
            </div>
          </v-slide-x-transition>
        </template>
      </ToggleState>
    </section>
    <section>
      <BaseCardSectionTitle
        class="mt-10"
        :title="$t('profile.preferences')"
      />
      <v-card variant="outlined">
        <v-card-text>
          <v-combobox
            v-model="selectedDefaultActivity"
            :label="$t('user.default-activity')"
            :items="activityOptions"
            :hint="$t('user.default-activity-hint')"
            density="comfortable"
            variant="outlined"
            validate-on="blur"
            persistent-hint
          />
          <v-checkbox
            v-model="userCopy.advanced"
            :label="$t('profile.show-advanced-description')"
            color="primary"
            @change="updateUser"
          />
        </v-card-text>
      </v-card>
      <nuxt-link
        class="mt-5 d-flex flex-column justify-center text-center"
        :to="`/group`"
      > {{
        $t('profile.looking-for-privacy-settings') }} </nuxt-link>
      <div class="d-flex flex-wrap justify-center mt-5">
        <v-btn
          variant="outlined"
          class="my-1 mx-1"
          :to="`/user/profile`"
          nuxt
          exact
        >
          <v-icon start>
            {{ $globals.icons.backArrow }}
          </v-icon>
          {{ $t('profile.back-to-profile') }}
        </v-btn>
      </div>
    </section>
  </v-container>
</template>

<script lang="ts">
import { useUserApi } from "~/composables/api";
import UserAvatar from "~/components/Domain/User/UserAvatar.vue";
import UserPasswordStrength from "~/components/Domain/User/UserPasswordStrength.vue";
import { validators } from "~/composables/use-validators";
import type { VForm } from "~/types/auto-forms";
import { useUserActivityPreferences } from "~/composables/use-users/preferences";
import useDefaultActivity from "~/composables/use-default-activity";
import { ActivityKey } from "~/lib/api/types/activity";

export default defineNuxtComponent({
  components: {
    UserAvatar,
    UserPasswordStrength,
  },
  setup() {
    const i18n = useI18n();
    const $auth = useMealieAuth();
    const { getDefaultActivityLabels, getActivityLabel, getActivityKey } = useDefaultActivity();
    const user = computed(() => $auth.user.value);

    useSeoMeta({
      title: i18n.t("settings.profile"),
    });

    const activityPreferences = useUserActivityPreferences();
    const activityOptions = getDefaultActivityLabels(i18n);
    const selectedDefaultActivity = ref(getActivityLabel(i18n, activityPreferences.value.defaultActivity));
    watch(selectedDefaultActivity, () => {
      activityPreferences.value.defaultActivity = getActivityKey(i18n, selectedDefaultActivity.value) ?? ActivityKey.RECIPES;
    });

    watch(user, () => {
      userCopy.value = { ...user.value };
    });

    const userCopy = ref({ ...user.value });

    const api = useUserApi();

    const domUpdatePassword = ref<VForm | null>(null);
    const password = reactive({
      current: "",
      newOne: "",
      newTwo: "",
    });

    const passwordsMatch = computed(() => password.newOne === password.newTwo && password.newOne.length > 0);

    async function updateUser() {
      if (!userCopy.value?.id) return;
      const { response } = await api.users.updateOne(userCopy.value.id, userCopy.value);
      if (response?.status === 200) {
        $auth.refresh();
      }
    }

    async function updatePassword() {
      if (!userCopy.value?.id) {
        return;
      }
      const { response } = await api.users.changePassword({
        currentPassword: password.current,
        newPassword: password.newOne,
      });

      if (response?.status === 200) {
        console.log("Password Changed");
      }
    }

    const state = reactive({
      hideImage: false,
      passwordLoading: false,
      showPassword: false,
      loading: false,
    });

    return {
      ...toRefs(state),
      updateUser,
      updatePassword,
      userCopy,
      selectedDefaultActivity,
      activityOptions,
      password,
      domUpdatePassword,
      passwordsMatch,
      validators,
      $auth,
    };
  },
});
</script>

<style scoped>
.settings-page :deep(.v-field__input) {
  font-size: 1rem;
}

.settings-page :deep(.slide-x-transition-enter-active) {
  transition-duration: var(--mealie-motion-enter) !important;
  transition-timing-function: var(--mealie-ease-out) !important;
}

.settings-page :deep(.slide-x-transition-leave-active) {
  transition-duration: 180ms !important;
  transition-timing-function: var(--mealie-ease-in) !important;
}

@media (prefers-reduced-motion: reduce) {
  .settings-page :deep(.slide-x-transition-enter-active),
  .settings-page :deep(.slide-x-transition-leave-active) {
    transition-duration: 0.01ms !important;
  }
}
</style>
