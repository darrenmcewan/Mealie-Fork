# Mealie UI

## Direction

A working kitchen library, not a marketing site. Food photography carries the
visual identity; quiet surfaces and predictable controls support repeated use.

- Plus Jakarta Sans for controls and body copy; Lora for library and recipe titles.
- Neutral white/gray light surfaces; charcoal dark surfaces. Green is the primary
  action color, blue is informational, and rose is secondary.
- Runtime palettes live in `plugins/theme.ts`. Non-default configured colors and
  persisted light/dark preferences are retained.
- Shared tokens and control states live in `assets/main.css`; fonts are bundled
  through Nuxt Fonts. Use semantic Vuetify colors rather than per-page hex values.
- Cards have at most 8px corner radii. Sections remain unframed, with cards reserved
  for individual recipes, dialogs, and genuinely framed tools.
- The desktop sidebar is persistent; mobile uses a dismissible drawer. Keep icon
  actions labeled, fields visibly labeled, and main controls at least 44px high.
- Empty-library and filtered-no-results states are distinct. Never invent recipes
  or counts; the library count describes currently loaded results.

## Changelog

The sidebar's `/changelog` page renders `content/changelog.md` through the shared
`SafeMarkdown` component. Add new dated or versioned sections at the top, with
Added, Changed, and Fixed headings as needed. Document implemented changes only;
keep unreleased work labeled Unreleased until a release is published. The content
is bundled with the frontend and updates when the app is rebuilt.

## Motion

Use the `--mealie-motion-*` and `--mealie-ease-*` tokens. Entrances settle with
ease-out in 200-260ms; exits accelerate with ease-in in 180ms. Press feedback uses
scale(0.98). Context menus open immediately. Avoid overshoot, competing focal
animations, layout-property animation, or long staggers. Reduced-motion requests
suppress movement, including view transitions. Dialogs dim the background.

## Verification

From the frontend directory, run `node_modules/.bin/vitest run` and lint changed
files with `node_modules/.bin/eslint`. Check library search/reset, recipe scaling,
planner date navigation, form validation, and drawer/dialog keyboard behavior.
Review light/dark screenshots at 375px, 768px, 1024px, and 1440px and confirm there
is no document overflow. Inspect actual loaded images and fonts, not just CSS.
Theme initialization has real-VueUse regression tests in `plugins/`.

The locally bundled empty-library kitchen photograph is from Unsplash:
https://images.unsplash.com/photo-1556911220-bff31c812dba
It is welcome-state imagery, never a substitute for actual recipe photos.
