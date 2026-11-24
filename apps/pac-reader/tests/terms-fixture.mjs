export const termGenerator = {
  format: "pac-generator", version: "2.0", policy: { name: "Terms-first smoke fixture" },
  order: "map", duty: { parties: ["deployer"] }, constants: { fixed: "y" },
  dimensions: [
    { key: "act", fixable: false, values: { y: "In scope", n: "Out of scope" } },
    { key: "age", type: "number", unit: "years", integer: true, min: 0, max: 150 },
    { key: "disc", default: "n", values: { y: "Published", n: "Not published" } },
    { key: "fixed", values: { y: "Already verified", n: "Not verified" } },
  ],
  term_map: {
    sections: [{ name: "Example terms", terms: ["c01", "c03", "c04"] }],
    nodes: {
      c01: { title: "Scope gate", parents: [], children: ["c02"], binds: "deployer",
        keys: [{ id: "k1", role: "gate", dim: "act", in: ["y"] }] },
      c02: { title: "Underage case", parents: ["c01"], children: [], binds: "deployer",
        keys: [{ id: "k1", role: "gate", dim: "age", lt: 18 }] },
      c03: { title: "Publish disclosure", parents: [], children: [], binds: "provider",
        keys: [{ id: "k1", role: "require", dim: "disc", in: ["y"], preset: "y", why: "duty", binds: "provider" }] },
      c04: { title: "Preflight", parents: [], children: [], binds: "deployer",
        keys: [{ id: "k1", role: "gate", dim: "fixed", in: ["y"] },
          { id: "k2", role: "gate", dim: "age", ge: 0 }] },
    },
  },
};
export const termJudge = {
  format: "pac-judge", version: "2.0", semantics: "kleene-3v-2",
  terms: { c02: { section: "Example terms", text: "No use for anyone under 18 years." },
    c03: { section: "Example terms", summary: "The provider publishes a disclosure." } },
  rules: [
    { id: "T-c02", term: "c02", kind: "prohibition", source_terms: ["c02"], title: "Underage case",
      next_step: "Do not proceed.", when: { all: [{ dim: "act", in: ["y"] }, { dim: "age", lt: 18 }] } },
    { id: "T-c03", term: "c03", kind: "obligation", source_terms: ["c03"], title: "Publish disclosure",
      next_step: "Publish a disclosure.", when: { all: [] }, require: { dim: "disc", in: ["y"] } },
  ],
};
