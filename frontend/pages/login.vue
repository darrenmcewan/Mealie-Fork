<template>
  <v-container
    fluid
    class="auth-page d-flex justify-center align-center flex-column"
  >
    <v-alert
      v-if="isFirstLogin"
      class="auth-notice mb-6"
      type="info"
      variant="tonal"
      :icon="$globals.icons.information"
      :style="{ flex: 'none' }"
    >
      <div>
        <p class="mb-3">
          {{ $t('user.it-looks-like-this-is-your-first-time-logging-in') }}
        </p>
        <p class="mb-1">
          <strong>{{ $t('user.username') }}: </strong>changeme@example.com
          <AppButtonCopy
            copy-text="changeme@example.com"
            color="info"
            btn-class="h-auto"
          />
        </p>
        <p class="mb-3">
          <strong>{{ $t('user.password') }}: </strong>MyPassword
          <AppButtonCopy
            copy-text="MyPassword"
            color="info"
            btn-class="h-auto"
          />
        </p>
        <p>
          {{ $t('user.dont-want-to-see-this-anymore-be-sure-to-change-your-email') }}
        </p>
      </div>
    </v-alert>
    <section class="auth-form w-100" aria-labelledby="login-title">
      <header class="mb-8">
        <div class="d-flex align-center ga-3 mb-6">
          <AppLogo class="auth-logo" :size="40" aria-hidden="true" />
          <span class="auth-brand">Mealie</span>
        </div>
        <h1 id="login-title" class="text-h5 font-weight-bold">
          {{ $t('user.sign-in') }}
        </h1>
      </header>
      <div>
        <v-form :aria-busy="loggingIn || oidcLoggingIn" @submit.prevent="authenticate">
          <v-text-field
            v-if="$appInfo.allowPasswordLogin"
            id="login-email"
            v-model="form.email"
            :prepend-inner-icon="$globals.icons.email"
            variant="outlined"
            width="100%"
            autofocus
            autocomplete="username"
            name="login"
            :label="$t('user.email-or-username')"
            type="text"
          />
          <v-text-field
            v-if="$appInfo.allowPasswordLogin"
            id="password"
            v-model="form.password"
            :prepend-inner-icon="$globals.icons.lock"
            variant="outlined"
            autocomplete="current-password"
            name="password"
            :label="$t('user.password')"
            :type="inputType"
          >
            <template #append-inner>
              <v-tooltip :text="`${$t('user.password')}: ${$t('general.toggle-view')}`" location="top">
                <template #activator="{ props }">
                  <v-btn
                    v-bind="props"
                    :icon="passwordIcon"
                    :aria-label="`${$t('user.password')}: ${$t('general.toggle-view')}`"
                    :aria-pressed="inputType === 'text'"
                    variant="text"
                    type="button"
                    @click="togglePasswordShow"
                  />
                </template>
              </v-tooltip>
            </template>
          </v-text-field>
          <v-checkbox
            v-if="$appInfo.allowPasswordLogin"
            v-model="form.remember"
            class="mt-n2"
            :label="$t('user.remember-me')"
            hide-details
          />
          <div v-if="$appInfo.allowPasswordLogin" class="mt-4">
            <v-btn
              :loading="loggingIn"
              :disabled="oidcLoggingIn"
              variant="elevated"
              color="primary"
              type="submit"
              size="large"
              class="auth-action"
              :rounded="false"
              elevation="0"
              block
            >
              {{ $t("user.login") }}
            </v-btn>
          </div>
          <div
            v-if="$appInfo.enableOidc"
            :class="{ 'mt-3': $appInfo.allowPasswordLogin }"
          >
            <v-btn
              :loading="oidcLoggingIn"
              :disabled="loggingIn"
              color="primary"
              size="large"
              :variant="$appInfo.allowPasswordLogin ? 'outlined' : 'elevated'"
              class="auth-action"
              :rounded="false"
              elevation="0"
              block
              @click="() => oidcAuthenticate()"
            >
              {{ $t("user.login-oidc") }} {{ $appInfo.oidcProviderName }}
            </v-btn>
          </div>
        </v-form>
      </div>
      <div class="auth-links d-flex justify-center flex-wrap ga-2 mt-4">
        <v-btn
          v-if="$appInfo.allowSignup && $appInfo.allowPasswordLogin"
          variant="text"
          to="/register"
        >
          {{ $t("user.register") }}
        </v-btn>
        <span
          v-else
          class="text-body-2 text-medium-emphasis align-self-center px-4"
        >
          {{ $t("user.invite-only") }}
        </span>
        <v-btn
          v-if="$appInfo.allowPasswordLogin"
          variant="text"
          to="/forgot-password"
        >
          {{ $t("user.reset-password") }}
        </v-btn>
      </div>

      <footer class="auth-links d-flex justify-center flex-wrap ga-1 mt-8">
        <div
          v-for="link in [
            {
              text: $t('about.sponsor'),
              icon: $globals.icons.heart,
              href: 'https://github.com/sponsors/hay-kot',
            },
            {
              text: $t('about.github'),
              icon: $globals.icons.github,
              href: 'https://github.com/mealie-recipes/mealie',
            },
            {
              text: $t('about.docs'),
              icon: $globals.icons.folderOutline,
              href: 'https://docs.mealie.io/',
            },
          ]"
          :key="link.text"
          class="text-center"
        >
          <v-btn
            variant="text"
            :href="link.href"
            target="_blank"
            rel="noopener noreferrer"
            size="small"
          >
            <v-icon start>
              {{ link.icon }}
            </v-icon>
            {{ link.text }}
          </v-btn>
        </div>
      </footer>
    </section>
  </v-container>
</template>

<script lang="ts">
import { whenever } from "@vueuse/core";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { usePasswordField } from "~/composables/use-passwords";
import { alert } from "~/composables/use-toast";
import { useAsyncKey } from "~/composables/use-utils";
import type { AppStartupInfo } from "~/lib/api/types/admin";
import { useUserActivityPreferences } from "~/composables/use-users/preferences";

export default defineNuxtComponent({
  setup() {
    definePageMeta({
      layout: "blank",
    });
    const router = useRouter();
    const i18n = useI18n();
    const $auth = useMealieAuth();
    const { $appInfo, $axios } = useNuxtApp();
    const { loggedIn } = useLoggedInState();
    const groupSlug = computed(() => $auth.user.value?.groupSlug);
    const isDemo = ref(false);
    const isFirstLogin = ref(false);
    const activityPreferences = useUserActivityPreferences();
    const { getDefaultActivityRoute } = useDefaultActivity();

    useSeoMeta({
      title: i18n.t("user.login"),
    });

    const form = reactive({
      email: "",
      password: "",
      remember: false,
    });

    useAsyncData(useAsyncKey(), async () => {
      const data = await $axios.get<AppStartupInfo>("/api/app/about/startup-info");
      isDemo.value = data.data.isDemo;
      isFirstLogin.value = data.data.isFirstLogin;
    });

    whenever(
      () => loggedIn.value && groupSlug.value,
      () => {
        const defaultActivityRoute = getDefaultActivityRoute(
          activityPreferences.value.defaultActivity,
          groupSlug.value,
        );
        if (!isDemo.value && isFirstLogin.value && $auth.user.value?.admin) {
          router.push("/admin/setup");
        }
        else if (defaultActivityRoute) {
          router.push(defaultActivityRoute);
        }
        else {
          router.push(`/g/${groupSlug.value || ""}`);
        }
      },
      { immediate: true },
    );

    const loggingIn = ref(false);
    const oidcLoggingIn = ref(false);

    const { passwordIcon, inputType, togglePasswordShow } = usePasswordField();

    whenever(
      () => $appInfo.enableOidc && $appInfo.oidcRedirect && !isCallback() && !isDirectLogin() /* && !$auth.check().valid */,
      () => oidcAuthenticate(),
      { immediate: true },
    );

    onBeforeMount(async () => {
      if (isCallback()) {
        await oidcAuthenticate(true);
      }
    });

    function isCallback() {
      const params = new URLSearchParams(window.location.search);
      return params.has("code") || params.has("error");
    }

    function isDirectLogin() {
      const params = new URLSearchParams(window.location.search);
      return params.has("direct") && params.get("direct") === "1";
    }

    async function oidcAuthenticate(callback = false) {
      if (callback) {
        oidcLoggingIn.value = true;
        try {
          await $auth.oauthSignIn();
        }
        catch (error) {
          await router.replace("/login?direct=1");
          alertOnError(error);
        }
        oidcLoggingIn.value = false;
      }
      else {
        navigateTo("/api/auth/oauth", { external: true }); // start the redirect process
      }
    }

    async function authenticate() {
      if (form.email.length === 0 || form.password.length === 0) {
        alert.error(i18n.t("user.please-enter-your-email-and-password"));
        return;
      }

      loggingIn.value = true;
      const formData = new FormData();
      formData.append("username", form.email);
      formData.append("password", form.password);
      formData.append("remember_me", String(form.remember));

      try {
        await $auth.signIn(formData);
      }
      catch (error) {
        console.log(error);
        alertOnError(error);
      }
      loggingIn.value = false;
    }

    function alertOnError(error: any) {
      // TODO Check if error is an AxiosError, but isAxiosError is not working right now
      // See https://github.com/nuxt-community/axios-module/issues/550
      // Import $axios from useContext()
      // if ($axios.isAxiosError(error) && error.response?.status === 401) {
      if (error.response?.status === 401) {
        alert.error(i18n.t("user.invalid-credentials"));
      }
      else if (error.response?.status === 423) {
        alert.error(i18n.t("user.account-locked-please-try-again-later"));
      }
      else {
        alert.error(i18n.t("events.something-went-wrong"));
      }
    }

    return {
      form,
      loggingIn,
      authenticate,
      oidcAuthenticate,
      oidcLoggingIn,
      passwordIcon,
      inputType,
      togglePasswordShow,
      isFirstLogin,
    };
  },
});
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  min-height: 100dvh;
  padding: 32px 24px;
  background-color: rgb(var(--v-theme-background));
}

.auth-form,
.auth-notice {
  width: 100%;
  max-width: 400px;
}

.auth-brand {
  font-family: var(--mealie-display-font);
  font-size: 1.75rem;
  font-weight: 600;
  line-height: 1.3;
}

.auth-form .auth-logo {
  flex: 0 0 40px;
  width: 40px;
  margin-top: 0;
}

.auth-logo :deep(.icon-divider) {
  display: none;
}

.auth-notice {
  border-radius: 8px;
  overflow-wrap: anywhere;
}

.auth-form :deep(.v-field__input) {
  font-size: 1rem;
}

.auth-action {
  min-height: 48px;
  height: auto !important;
  border-radius: 8px !important;
  padding-block: 12px;
}

.auth-action :deep(.v-btn__content) {
  white-space: normal;
  overflow-wrap: anywhere;
}

.auth-links :deep(.v-btn) {
  min-height: 44px;
}
</style>
