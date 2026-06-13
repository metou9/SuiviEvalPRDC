import { describe, expect, it, vi } from "vitest";

vi.mock("../http.js", () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

import { resource } from "../api.js";

describe("resource()", () => {
  it("builds an xlsx export url with params and format", () => {
    const r = resource("measurements");
    const url = r.exportXlsxUrl({ indicator: 3 });
    expect(url).toContain("/measurements/?");
    expect(url).toContain("indicator=3");
    expect(url).toContain("format=xlsx");
  });
});
