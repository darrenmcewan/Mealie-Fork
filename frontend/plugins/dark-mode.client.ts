import { useDark } from "@vueuse/core";

export default defineNuxtPlugin((nuxtApp) => {
  let changeTheme: ((dark: boolean) => void) | undefined;
  const isDark = useDark({
    onChanged: (dark, applyClass, mode) => {
      applyClass(mode);
      changeTheme?.(dark);
    },
  });

  nuxtApp.hook("vuetify:ready", (vuetify) => {
    changeTheme = dark => vuetify.theme.change(dark ? "dark" : "light");
    changeTheme(isDark.value);
  });

  return {
    provide: {},
  };
});
