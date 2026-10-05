export interface ThemeConfig {
  lightPrimary: string;
  lightAccent: string;
  lightSecondary: string;
  lightSuccess: string;
  lightInfo: string;
  lightWarning: string;
  lightError: string;
  darkPrimary: string;
  darkAccent: string;
  darkSecondary: string;
  darkSuccess: string;
  darkInfo: string;
  darkWarning: string;
  darkError: string;
}

let __cachedTheme: ThemeConfig | undefined;

function paletteColor(configured: string | undefined, original: string, replacement: string): string {
  return configured && configured.toLowerCase() !== original.toLowerCase() ? configured : replacement;
}

async function fetchTheme(): Promise<ThemeConfig | undefined> {
  const route = "/api/app/about/theme";

  try {
    const response = await fetch(route);
    const data = await response.json();
    return data as ThemeConfig;
  }
  catch {
    return undefined;
  }
}

export default defineNuxtPlugin(async (nuxtApp) => {
  nuxtApp.hook("vuetify:before-create", async ({ vuetifyOptions }) => {
    let theme = __cachedTheme;
    if (!theme) {
      theme = await fetchTheme();
      __cachedTheme = theme;
    }
    vuetifyOptions.defaults = {
      ...vuetifyOptions.defaults,
      VBtn: { rounded: "lg", elevation: 0, style: "text-transform: none; letter-spacing: 0;" },
      VCard: { rounded: "lg", elevation: 0 },
      VTextField: { variant: "outlined", color: "primary" },
      VTextarea: { variant: "outlined", color: "primary" },
      VSelect: { variant: "outlined", color: "primary" },
      VAutocomplete: { variant: "outlined", color: "primary" },
      VDialog: { scrim: true },
      VMenu: { transition: false },
    };
    vuetifyOptions.theme = {
      defaultTheme: nuxtApp.$config.public.useDark ? "dark" : "light",
      variations: {
        colors: ["primary", "accent", "secondary", "success", "info", "warning", "error", "background"],
        lighten: 3,
        darken: 3,
      },
      themes: {
        light: {
          dark: false,
          colors: {
            "primary": paletteColor(theme?.lightPrimary, "#E58325", "#267653"),
            "accent": paletteColor(theme?.lightAccent, "#007A99", "#236A85"),
            "secondary": paletteColor(theme?.lightSecondary, "#973542", "#A84545"),
            "success": theme?.lightSuccess ?? "#43A047",
            "info": theme?.lightInfo ?? "#1976d2",
            "warning": theme?.lightWarning ?? "#FF6D00",
            "error": theme?.lightError ?? "#EF5350",
            "background": "#F6F7F8",
            "surface": "#FFFFFF",
            "surface-variant": "#E9EEF0",
            "on-background": "#242A2B",
            "on-surface": "#242A2B",
            "on-surface-variant": "#526065",
            "on-primary": "#FFFFFF",
          },
        },
        dark: {
          dark: true,
          colors: {
            "primary": paletteColor(theme?.darkPrimary, "#E58325", "#82CEAA"),
            "accent": paletteColor(theme?.darkAccent, "#007A99", "#89C9DE"),
            "secondary": paletteColor(theme?.darkSecondary, "#973542", "#EFADAA"),
            "success": theme?.darkSuccess ?? "#43A047",
            "info": theme?.darkInfo ?? "#1976d2",
            "warning": theme?.darkWarning ?? "#FF6D00",
            "error": theme?.darkError ?? "#EF5350",
            "background": "#181D1C",
            "surface": "#222927",
            "surface-variant": "#35413D",
            "on-background": "#EEF3F0",
            "on-surface": "#EEF3F0",
            "on-surface-variant": "#BCCBC4",
            "on-primary": "#153B2A",
          },
        },
      },
    };
  });
});
