# ADR 0003: Verifier plus human approval

**Status:** accepted

**Context:** Small LLMs produce fluent but wrong root causes.

**Decision:** Every report passes a structural check (cited IDs exist and were retrieved) and an LLM judge (does the cited evidence support the claim). Failures return "insufficient evidence". Approval is a separate human action recorded in the audit log.

**Consequences:** Fewer confident wrong answers, at the cost of rejecting some correct ones when the judge model errs. Both failure modes are counted in the evals.
