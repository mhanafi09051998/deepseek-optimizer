import assert from "node:assert/strict";
import test from "node:test";

import { slugify } from "../slug.ts";

test("collapses runs of separators", () => {
  assert.equal(slugify("Hello   World"), "hello-world");
});

test("strips punctuation and edge dashes", () => {
  assert.equal(slugify("--Foo!!  Bar??--"), "foo-bar");
});

test("removes diacritics", () => {
  assert.equal(slugify("Café Déjà Vu"), "cafe-deja-vu");
});

test("returns empty for symbol-only input", () => {
  assert.equal(slugify("   "), "");
  assert.equal(slugify("!!!"), "");
});
