<template>
  <v-container
    fluid
    class="auth-page d-flex justify-center align-center flex-column"
  >
    <section class="auth-form w-100" aria-labelledby="registration-title">
      <header class="mb-6">
        <div class="d-flex align-center ga-3 mb-6">
          <AppLogo class="auth-logo" :size="40" aria-hidden="true" />
          <span class="auth-brand">Mealie</span>
        </div>
        <h1 id="registration-title" class="text-h5 font-weight-bold">
          {{ $t("user-registration.user-registration") }}
        </h1>
      </header>

      <div class="registration-step">
        <template v-if="state.ctx.state === States.Initial">
          <div class="d-flex flex-column ga-3">
            <v-btn
              class="auth-action"
              color="primary"
              :rounded="false"
              :prepend-icon="$globals.icons.group"
              elevation="0"
              block
              @click="initial.joinGroup"
            >
              {{ $t("user-registration.join-a-group") }}
            </v-btn>
            <v-btn
              class="auth-action"
              color="primary"
              variant="outlined"
              :rounded="false"
              :prepend-icon="$globals.icons.user"
              block
              @click="initial.createGroup"
            >
              {{ $t("user-registration.create-a-new-group") }}
            </v-btn>
          </div>
        </template>

        <template v-else-if="state.ctx.state === States.ProvideToken">
          <div>
            <h2 class="text-h6 mb-3">
              <v-icon
                size="large"
                class="mr-3"
              >
                {{ $globals.icons.group }}
              </v-icon>
              <span> {{ $t("user-registration.join-a-group") }} </span>
            </h2>
            <v-card-text>
              {{ $t("user-registration.provide-registration-token-description") }}
              <v-form
                ref="domTokenForm"
                class="mt-4"
                @submit.prevent
              >
                <v-text-field
                  id="registration-token"
                  v-model="token"
                  v-bind="inputAttrs"
                  name="registrationToken"
                  :label="$t('group.group-token')"
                  :rules="[validators.required]"
                />
              </v-form>
            </v-card-text>
            <v-card-actions class="registration-actions">
              <BaseButton
                cancel
                @click="state.back"
              >
                <template #icon>
                  {{ $globals.icons.back }}
                </template>
                {{ $t("general.back") }}
              </BaseButton>
              <BaseButton
                icon-right
                @click="provideToken.next"
              >
                <template #icon>
                  {{ $globals.icons.forward }}
                </template>
                {{ $t("general.next") }}
              </BaseButton>
            </v-card-actions>
          </div>
        </template>

        <template v-else-if="state.ctx.state === States.ProvideGroupDetails">
          <div class="preferred-width">
            <h2 class="text-h6 mb-3">
              <v-icon
                size="large"
                class="mr-3"
              >
                {{ $globals.icons.group }}
              </v-icon>
              <span> {{ $t("user-registration.group-details") }}</span>
            </h2>
            <v-card-text>
              {{ $t("user-registration.group-details-description") }}
            </v-card-text>
            <v-card-text>
              <v-form
                ref="domGroupForm"
                @submit.prevent
              >
                <v-text-field
                  id="registration-group-name"
                  v-model="groupDetails.groupName.value"
                  v-bind="inputAttrs"
                  name="groupName"
                  :label="$t('group.group-name')"
                  :rules="[validators.required]"
                  :error-messages="groupErrorMessages"
                  @blur="validGroupName"
                />
                <div class="mt-n4 px-2">
                  <v-checkbox
                    v-model="groupDetails.groupPrivate.value"
                    hide-details
                    :label="$t('group.settings.keep-my-recipes-private')"
                  />
                  <p class="text-caption mt-1">
                    {{ $t("group.settings.keep-my-recipes-private-description") }}
                  </p>
                  <v-checkbox
                    v-model="groupDetails.groupSeed.value"
                    hide-details
                    :label="$t('data-pages.seed-data')"
                  />
                  <p class="text-caption mt-1">
                    {{ $t("user-registration.use-seed-data-description") }}
                  </p>
                </div>
              </v-form>
            </v-card-text>
            <v-card-actions class="registration-actions">
              <BaseButton
                cancel
                @click="state.back"
              >
                <template #icon>
                  {{ $globals.icons.back }}
                </template>
                {{ $t("general.back") }}
              </BaseButton>
              <BaseButton
                icon-right
                @click="groupDetails.next"
              >
                <template #icon>
                  {{ $globals.icons.forward }}
                </template>
                {{ $t("general.next") }}
              </BaseButton>
            </v-card-actions>
          </div>
        </template>

        <template v-else-if="state.ctx.state === States.ProvideAccountDetails">
          <div>
            <UserRegistrationForm />
            <v-card-actions class="registration-actions">
              <BaseButton
                cancel
                @click="state.back"
              >
                <template #icon>
                  {{ $globals.icons.back }}
                </template>
                {{ $t("general.back") }}
              </BaseButton>
              <BaseButton
                icon-right
                @click="accountDetailsNext"
              >
                <template #icon>
                  {{ $globals.icons.forward }}
                </template>
                {{ $t("general.next") }}
              </BaseButton>
            </v-card-actions>
          </div>
        </template>

        <template v-else-if="state.ctx.state === States.Confirmation">
          <div class="preferred-width">
            <h2 class="text-h6 mb-3">
              <v-icon
                size="large"
                class="mr-3"
              >
                {{ $globals.icons.user }}
              </v-icon>
              <span>{{ $t("general.confirm") }}</span>
            </h2>
            <v-list>
              <template v-for="(item, idx) in confirmationData">
                <v-list-item
                  v-if="item.display"
                  :key="idx"
                >
                  <v-list-item-title> {{ item.text }} </v-list-item-title>
                  <v-list-item-subtitle> {{ item.value }} </v-list-item-subtitle>
                </v-list-item>
                <v-divider
                  v-if="idx !== confirmationData.length - 1"
                  :key="`divider-${idx}`"
                />
              </template>
            </v-list>

            <v-card-actions class="registration-actions">
              <BaseButton
                cancel
                @click="state.back"
              >
                <template #icon>
                  {{ $globals.icons.back }}
                </template>
                {{ $t("general.back") }}
              </BaseButton>
              <BaseButton @click="submitRegistration">
                <template #icon>
                  {{ $globals.icons.check }}
                </template>
                {{ $t("general.submit") }}
              </BaseButton>
            </v-card-actions>
          </div>
        </template>
      </div>

      <footer class="auth-links d-flex justify-center flex-wrap ga-2 mt-6">
        <v-btn
          variant="text"
          to="/login"
        >
          {{ $t("user.login") }}
        </v-btn>
        <v-btn
          variant="text"
          color="primary"
          :prepend-icon="$globals.icons.translate"
          @click="langDialog = true"
        >
          {{ $t("language-dialog.choose-language") }}
        </v-btn>
      </footer>
    </section>
    <LanguageDialog v-model="langDialog" />
  </v-container>
</template>

<script lang="ts">
import { States, RegistrationType, useRegistration } from "./states";
import { useUserRegistrationForm } from "~/composables/use-users/user-registration-form";
import { useRouteQuery } from "~/composables/use-router";
import { validators, useAsyncValidator } from "~/composables/use-validators";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import type { CreateUserRegistration } from "~/lib/api/types/user";
import { usePasswordField } from "~/composables/use-passwords";
import { usePublicApi } from "~/composables/api/api-client";
import { useLocales } from "~/composables/use-locales";
import UserRegistrationForm from "~/components/Domain/User/UserRegistrationForm.vue";
import type { VForm } from "~/types/auto-forms";

const inputAttrs = {
  variant: "outlined",
  validateOnBlur: true,
};

export default defineNuxtComponent({
  components: { UserRegistrationForm },
  setup() {
    definePageMeta({
      layout: "blank",
    });

    const i18n = useI18n();

    function safeValidate(form: Ref<VForm | null>) {
      if (form.value && form.value.validate) {
        return form.value.validate();
      }
      return false;
    }
    // ================================================================
    // Registration Context
    //
    // State is used to manage the registration process states and provide
    // a state machine esq interface to interact with the registration workflow.
    const state = useRegistration();
    // ================================================================
    // Handle Token URL / Initialization
    //
    const token = useRouteQuery("token");
    // TODO: We need to have some way to check to see if the site is in a state
    // Where it needs to be initialized with a user, in that case we'll handle that
    // somewhere...
    function initialUser() {
      return false;
    }
    onMounted(() => {
      if (token.value) {
        state.setState(States.ProvideAccountDetails);
        state.setType(RegistrationType.JoinGroup);
      }
      if (initialUser()) {
        state.setState(States.ProvideGroupDetails);
        state.setType(RegistrationType.InitialGroup);
      }
    });
    // ================================================================
    // Initial
    const initial = {
      createGroup: () => {
        state.setState(States.ProvideGroupDetails);
        state.setType(RegistrationType.CreateGroup);
        if (token.value != null) {
          token.value = null;
        }
      },
      joinGroup: () => {
        state.setState(States.ProvideToken);
        state.setType(RegistrationType.JoinGroup);
      },
    };
    // ================================================================
    // Provide Token
    const domTokenForm = ref<VForm | null>(null);
    function validateToken() {
      return true;
    }
    const provideToken = {
      next: () => {
        if (!safeValidate(domTokenForm as Ref<VForm>)) {
          return;
        }
        if (validateToken()) {
          state.setState(States.ProvideAccountDetails);
        }
      },
    };
    // ================================================================
    // Provide Group Details
    const publicApi = usePublicApi();
    const domGroupForm = ref<VForm | null>(null);
    const groupName = ref("");
    const groupSeed = ref(false);
    const groupPrivate = ref(false);
    const groupErrorMessages = ref<string[]>([]);
    const { validate: validGroupName, valid: groupNameValid } = useAsyncValidator(
      groupName,
      (v: string) => publicApi.validators.group(v),
      i18n.t("validation.group-name-is-taken"),
      groupErrorMessages,
    );
    const groupDetails = {
      groupName,
      groupSeed,
      groupPrivate,
      next: () => {
        if (!safeValidate(domGroupForm as Ref<VForm>) || !groupNameValid.value) {
          return;
        }
        state.setState(States.ProvideAccountDetails);
      },
    };
    const pwFields = usePasswordField();
    const {
      accountDetails,
      credentials,
      domAccountForm,
      emailErrorMessages,
      usernameErrorMessages,
      validateUsername,
      validateEmail,
    } = useUserRegistrationForm();
    async function accountDetailsNext() {
      if (!await accountDetails.validate()) {
        return;
      }
      state.setState(States.Confirmation);
    }
    // ================================================================
    // Locale
    const { locale } = useLocales();
    const langDialog = ref(false);
    // ================================================================
    // Confirmation
    const confirmationData = computed(() => {
      return [
        {
          display: state.ctx.type === RegistrationType.CreateGroup,
          text: i18n.t("group.group"),
          value: groupName.value,
        },
        {
          display: state.ctx.type === RegistrationType.CreateGroup,
          text: i18n.t("data-pages.seed-data"),
          value: groupSeed.value ? i18n.t("general.yes") : i18n.t("general.no"),
        },
        {
          display: state.ctx.type === RegistrationType.CreateGroup,
          text: i18n.t("group.settings.keep-my-recipes-private"),
          value: groupPrivate.value ? i18n.t("general.yes") : i18n.t("general.no"),
        },
        {
          display: true,
          text: i18n.t("user.email"),
          value: accountDetails.email.value,
        },
        {
          display: true,
          text: i18n.t("user.full-name"),
          value: accountDetails.fullName.value,
        },
        {
          display: true,
          text: i18n.t("user.username"),
          value: accountDetails.username.value,
        },
        {
          display: true,
          text: i18n.t("user.enable-advanced-content"),
          value: accountDetails.advancedOptions.value ? i18n.t("general.yes") : i18n.t("general.no"),
        },
      ];
    });
    const api = useUserApi();
    const router = useRouter();
    async function submitRegistration() {
      const payload: CreateUserRegistration = {
        email: accountDetails.email.value,
        username: accountDetails.username.value,
        fullName: accountDetails.fullName.value,
        password: credentials.password1.value,
        passwordConfirm: credentials.password2.value,
        locale: locale.value,
        advanced: accountDetails.advancedOptions.value,
      };
      if (state.ctx.type === RegistrationType.CreateGroup) {
        payload.group = groupName.value;
        payload.private = groupPrivate.value;
        payload.seedData = groupSeed.value;
      }
      else {
        payload.groupToken = token.value;
      }
      const { response } = await api.register.register(payload);
      if (response?.status === 201) {
        accountDetails.reset();
        credentials.reset();
        alert.success(i18n.t("user-registration.registration-success"));
        router.push("/login");
      }
      else {
        alert.error(i18n.t("events.something-went-wrong"));
      }
    }
    return {
      accountDetails,
      accountDetailsNext,
      confirmationData,
      credentials,
      emailErrorMessages,
      groupDetails,
      groupErrorMessages,
      initial,
      inputAttrs,
      langDialog,
      provideToken,
      pwFields,
      RegistrationType,
      state,
      States,
      token,
      usernameErrorMessages,
      validators,
      submitRegistration,
      // Validators
      validGroupName,
      validateUsername,
      validateEmail,
      // Dom Refs
      domAccountForm,
      domGroupForm,
      domTokenForm,
    };
  },
});
</script>

<style lang="css" scoped>
.auth-page {
  min-height: 100vh;
  min-height: 100dvh;
  padding: 32px 24px;
  background-color: rgb(var(--v-theme-background));
}

.auth-form {
  max-width: 480px;
}

.auth-form :deep(.v-field__input) {
  font-size: 1rem;
}

.auth-form .auth-logo {
  flex: 0 0 40px;
  width: 40px;
  margin-top: 0;
}

.auth-logo :deep(.icon-divider) {
  display: none;
}

.auth-brand {
  font-family: var(--mealie-display-font);
  font-size: 1.75rem;
  font-weight: 600;
  line-height: 1.3;
}

.preferred-width {
  width: 100%;
}

.registration-step :deep(.v-card-text),
.registration-step :deep(.v-card-title) {
  padding-inline: 0;
}

.registration-actions {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  padding: 16px 0 0;
}

.auth-action,
.registration-actions :deep(.v-btn) {
  min-height: 48px;
  height: auto !important;
  border-radius: 8px !important;
  padding-block: 12px;
}

.auth-form :deep(.v-btn__content),
.auth-form :deep(.v-list-item-subtitle) {
  white-space: normal;
  overflow-wrap: anywhere;
}

.auth-links :deep(.v-btn) {
  min-height: 44px;
}
</style>
