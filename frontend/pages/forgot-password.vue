<template>
  <v-container
    fluid
    class="auth-page d-flex justify-center align-center"
  >
    <section class="auth-form w-100" aria-labelledby="forgot-password-title">
      <header class="mb-6">
        <div class="d-flex align-center ga-3 mb-6">
          <AppLogo class="auth-logo" :size="40" aria-hidden="true" />
          <span class="auth-brand">Mealie</span>
        </div>
        <h1 id="forgot-password-title" class="text-h5 font-weight-bold mb-3">
          {{ $t('user.forgot-password') }}
        </h1>
        <p class="text-body-2 text-medium-emphasis">
          {{ $t('user.forgot-password-text') }}
        </p>
      </header>
      <div>
        <v-form @submit.prevent="requestLink()">
          <v-text-field
            id="recovery-email"
            v-model="email"
            :prepend-inner-icon="$globals.icons.email"
            variant="outlined"
            autofocus
            name="login"
            autocomplete="email"
            :label="$t('user.email')"
            type="email"
          />
          <v-alert
            v-if="error"
            class="mb-4"
            type="error"
            variant="tonal"
            role="alert"
          >
            {{ $t('profile.error-sending-email') }}
          </v-alert>
          <div>
            <v-btn
              :loading="loading"
              color="primary"
              type="submit"
              size="large"
              :rounded="false"
              class="auth-action"
              elevation="0"
              block
            >
              <v-icon start>
                {{ $globals.icons.email }}
              </v-icon>
              {{ $t("user.reset-password") }}
            </v-btn>
          </div>
        </v-form>
      </div>
      <div class="d-flex justify-center mt-4">
        <v-btn
          class="auth-link"
          variant="text"
          to="/login"
        >
          {{ $t("user.login") }}
        </v-btn>
      </div>
    </section>
  </v-container>
</template>

<script lang="ts">
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";

export default defineNuxtComponent({
  setup() {
    definePageMeta({
      layout: "blank",
    });

    const state = reactive({
      email: "",
      loading: false,
      error: false,
    });

    const i18n = useI18n();

    // Set page title
    useSeoMeta({
      title: i18n.t("user.forgot-password"),
    });

    const api = useUserApi();

    async function requestLink() {
      state.loading = true;
      // TODO: Fix Response to send meaningful error
      const { response } = await api.email.sendForgotPassword({ email: state.email });

      if (response?.status === 200) {
        state.loading = false;
        state.error = false;
        alert.success(i18n.t("profile.email-sent"));
      }
      else {
        state.loading = false;
        state.error = true;
        alert.error(i18n.t("profile.error-sending-email"));
      }
    }

    return {
      requestLink,
      ...toRefs(state),
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

.auth-form {
  max-width: 400px;
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

.auth-link {
  min-height: 44px;
}
</style>
