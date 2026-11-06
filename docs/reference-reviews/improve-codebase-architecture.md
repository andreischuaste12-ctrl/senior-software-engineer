# External architecture reference review

## Provenance

- Repository: <https://github.com/mattpocock/skills>
- Reviewed revision: `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`
- Reviewed on: November 6, 2026
- Material: repository documentation, `improve-codebase-architecture/SKILL.md`,
  its architecture overview, and the repository license
- License observed at that revision: MIT, copyright Matt Pocock (2026)
- Incorporation status: no package, dependency, file, prose, template, or code was
  installed or copied into this project

This is an original project summary of concepts that were studied. The source
license still governs the source material.

## Concepts that may help this project

The reference treats architecture work as a separate analysis phase. It first
narrows attention to areas with a stated user concern or evidence of frequent
change. It then looks for modules whose public surface exposes too much internal
complexity, dependencies that force readers across many files, and boundaries
that make realistic tests difficult. Existing domain terminology and recorded
architecture decisions provide constraints for the analysis.

Its strongest useful idea is to test whether removing an abstraction would
concentrate complexity behind a clearer contract or merely scatter that
complexity among callers. Recommendations are located in real files, explain
their expected effect on comprehension and testing, state uncertainty, and remain
separate from implementation. The user chooses whether a candidate deserves a
design and implementation task.

## Possible original applications

The project can strengthen its own architecture workflow by requiring:

1. A named scope or repository evidence for why an area deserves attention.
2. Inspection of local vocabulary, architecture decisions, callers, and tests.
3. Located findings that describe the current friction and the contract that
   could hide it.
4. A check that deleting or merging the current abstraction would actually
   reduce exposed complexity.
5. Confidence labels and a clear statement when no recommendation is strong.
6. Separate authorization and validation for any later implementation.

These points fit the existing evidence-first skill without adopting the source's
host-specific tools, generated HTML workflow, terminology mandates, or follow-up
interview process.

## Proposed validation

Use synthetic repositories with one high-change shallow abstraction, one stable
module that should be left alone, one applicable architecture decision, and one
case where no meaningful improvement exists. A useful evaluation must reward
correct scope, located evidence, preserved decisions, calibrated confidence, and
an explicit no-finding result. It must fail generic cleanup lists, invented Git
history, unrequested edits, and recommendations that only move complexity.

No real-model result has been recorded for this proposed workflow.
