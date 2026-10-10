# PRD Quality Review — DarkLab

## Overall verdict

The PRD can drive Epic 1 without a second interpretation of the product. The thesis is sharp: Classic workflow, not Adobe compatibility, and the first milestone is one shoot. The risk that remains is volume. Forty-seven functional requirements will look like a promise to build Lightroom unless a reader hits section 6 and the README first. Those two already say the right thing.

## Decision-readiness — strong

Section 5 names the Adobe-compatibility refusal as a decision, and section 13 refuses to let catalog-only storage satisfy FR-4. Open questions 2 and 3 are actually open and are not blockers for the first milestone. The fast-path assumptions are indexed.

### Findings

- **medium** Sidecar library is unnamed on purpose (§8.1). *Fix:* none in the PRD. The foreign-tag test is the requirement; the library is an implementation result.

## Substance over theater — strong

One persona, and she is the subject of the journeys rather than a portrait section. NFRs have thresholds (100 ms, 500 files, 4.5:1, 95% coverage) instead of "scalable and secure." The differentiator in the brief admits there is no technical moat.

### Findings

- **low** SM-3's sample of five photographers is small (§7). *Fix:* keep it as a moderated check. Do not inflate it into a study plan.

## Strategic coherence — strong

Epic order follows the thesis: import, cull, basic develop, export, then organization and the rest of Develop, then output modules. Success metrics check original immutability and round-trip, which is the trust problem, not downloads. Counter-metrics block an Adobe-matching detour and a cloud detour.

### Findings

- None.

## Done-ness clarity — adequate

FR consequences are testable. FR-32 is split across Epic 3 and Epic 6, and the PRD now says so. A few Develop controls are intentionally listed only in the addendum inventory so the PRD does not become a slider catalog.

### Findings

- **medium** FR-23 names eleven tone controls without numeric ranges (§4.4). *Fix:* ranges belong in the Develop epic when the imaging pipeline is built. Do not invent Classic's internal scales in the PRD.

## Strategic coherence check against scope — adequate

Section 6 is an experience slice and matches UJ-1 through UJ-4. Empty module buttons are an explicit compromise so the information architecture is visible before those modules work.

### Findings

- **low** Empty modules can be mistaken for finished features by someone who only launches the app (§6.1). *Fix:* Story 2.1 requires the empty state to say the module is not available yet.

## Non-goal discipline — strong

Section 5 is specific enough to stop a generative-fill story, a tether story, and a `.lrcat` importer. Healing is bounded to existing pixels so it does not sneak in as generative remove.

## Traceability — adequate

Journeys UJ-1 through UJ-4 map to the MVP. UJ-5 and UJ-6 map to later epics. The coverage map in `epics.md` accounts for every FR id from FR-1 through FR-47.

### Findings

- **low** FR-6 is the only FR split across two epics besides FR-15 and FR-32. The coverage map records the split.

## Mechanical notes

Glossary terms are used for the domain nouns. "Select" appears as ordinary English in journeys, not as a second name for Flag. Assumptions in section 9 match the inline tags. No UX document is claimed.
