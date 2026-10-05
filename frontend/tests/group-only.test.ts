import { afterEach, expect, test, vi } from "vitest";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});

test.each(["home", "other", null])("group-only middleware enforces authenticated group %s", async (groupSlug) => {
  vi.stubGlobal("defineNuxtRouteMiddleware", (middleware: unknown) => middleware);
  vi.stubGlobal("useMealieAuth", () => ({ user: { value: groupSlug ? { groupSlug } : null } }));
  const redirect = { redirected: true };
  const navigate = vi.fn(() => redirect);
  vi.stubGlobal("navigateTo", navigate);
  const { default: middleware } = await import("../middleware/group-only");
  const result = middleware({ params: { groupSlug: "home" } } as never, {} as never);
  if (groupSlug === "home") {
    expect(result).toBeUndefined();
    expect(navigate).not.toHaveBeenCalled();
  }
  else {
    expect(result).toBe(redirect);
    expect(navigate).toHaveBeenCalledWith("/");
  }
});
