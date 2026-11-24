// An artificial policy for checking citations without depending on a live policy page.
export const policyText = "A <b>test action</b> is prohibited without written permission.";
export const exceptionText = "Written permission makes this test action permissible.";
export const policySummary = "A plain <b>summary</b>\nabout getting permission.";
export const exceptionSummary = "A summary of the permission exception.";
export const definitionSummary = "An explanation of a simulated action.";

export function citationJudge(judge) {
  const copy = structuredClone(judge);
  const rule = copy.rules.find((r) => r.id === "P-cyber");
  rule.source_terms = ["test-rule", "test-exception"];
  rule.exceptions[0].source_terms = ["test-exception"];
  copy.terms = {
    "test-rule": { text: policyText, section: "Example rules", class: "prohibition", source: "Test policy",
      refs: [{ to: "test-definition", kind: "uses_definition" }] },
    "test-exception": { text: exceptionText, section: "Example exceptions", class: "exception", source: "Test policy",
      refs: [{ to: "test-rule", kind: "modifies" }] },
    "test-definition": { text: "A test action means a simulated action.", section: "Example terms", class: "definition",
      source: "Test policy", refs: [] },
  };
  return copy;
}

export function summaryJudge(judge) {
  const copy = citationJudge(judge);
  // Explicit, legacy, and malformed dual-form terms are all loaded without validation.
  const rule = copy.terms["test-rule"];
  delete rule.text;
  rule.summary = policySummary;
  copy.terms["test-exception"].text = "  sUmMaRy (not verbatim): " + exceptionSummary;
  copy.terms["test-definition"].summary = definitionSummary;
  return copy;
}
