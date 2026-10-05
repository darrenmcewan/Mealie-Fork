import { effectScope, nextTick } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";

describe("theme initialization", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.doUnmock("@vueuse/core");
    document.documentElement.classList.remove("dark");
  });

  it.each(["light", "dark"])("initializes %s mode without a callback error", async (mode) => {
    vi.resetModules();
    vi.doMock("@vueuse/core", async (importOriginal) => {
      const actual = await importOriginal<typeof import("@vueuse/core")>();
      return {
        ...actual,
        useDark: (options: Parameters<typeof actual.useDark>[0]) => actual.useDark({
          ...options,
          storageKey: null,
          initialValue: mode,
        }),
      };
    });
    vi.stubGlobal("defineNuxtPlugin", (plugin: unknown) => plugin);
    const { default: plugin } = await import("./dark-mode.client");
    const change = vi.fn();
    const hook = vi.fn((_name, callback) => callback({ theme: { change } }));
    const scope = effectScope();

    try {
      expect(() => scope.run(() => plugin({ hook } as unknown as Parameters<typeof plugin>[0]))).not.toThrow();
      await nextTick();
      expect(hook).toHaveBeenCalledWith("vuetify:ready", expect.any(Function));
      expect(change).toHaveBeenCalledWith(mode);
      expect(document.documentElement.classList.contains("dark")).toBe(mode === "dark");
    }
    finally {
      scope.stop();
    }
  });
});
