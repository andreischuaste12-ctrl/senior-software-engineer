# Audit reference

An audit is read-only analysis. Use these lenses as questions to ask where they apply,
not as a form to complete. Report only findings you can tie to a plausible failure path.

## Scope and order

Bound the scope first. In a large codebase start where mistakes cost the most: code that
accepts external input, decides who may do what, moves money, persists data, runs
concurrently, or changed recently near the reported symptom.

## Report contract

Give every finding the same fields:

- **Severity:** critical, high, medium, or low, from impact and likelihood together.
- **Confidence:** confirmed (reproduced, or proven by a traced code path), probable
  (plausible path that was not exercised), or hypothesis (needs more evidence).
- **Where:** file and line.
- **Trigger:** the input or state that makes it fail.
- **Impact:** what breaks, for whom.
- **Smallest fix:** the least change that removes the cause.

Close with coverage: what was read, what was not, which checks ran, and which were
not run and why. Group low-risk maintainability notes into a single low item so they
do not bury the findings that matter. Drop suspicions that have no support.

## Lenses

**Trust boundaries.** Where does untrusted data enter, and what reaches a query, shell,
template, file path, URL fetch, deserializer, or eval? String concatenation with
external input is the usual tell.

**Access control.** Is every state-changing action checked on the server for both
identity and ownership? Look for object lookups by id with no owner check, checks that
exist only in the client, and privilege taken from request parameters.

**Secrets and data exposure.** Credentials in code, history, images, logs, and
committed environment files; personal data in logs and analytics payloads; error
messages that reveal internals.

**Persistence and concurrency.** Read-modify-write without a lock or version, check-then-act
races, transactions with the wrong scope, destructive or unreversible migrations,
cache keys that omit the user or tenant, and work that is not idempotent under retry or
redelivery.

**Errors and recovery.** Swallowed errors, broad handlers that hide programming bugs,
partial failure without rollback, retries with no limit or backoff, calls with no
timeout.

**Resources.** Unclosed files, connections, and handles; unbounded growth of lists,
caches, and queues; whole-file reads of large inputs.

**Supply chain and delivery.** Unpinned dependencies and actions, install scripts, CI
that runs untrusted code with secrets or ignores failures, containers that run as root
or bake secrets into layers, public buckets and wildcard permissions in infrastructure.

**Tests.** Tests that assert nothing, mocks that restate the implementation, missing
coverage on exactly the error, boundary, and security paths, and disabled tests.

## E-commerce lens

- **Money and totals:** binary floats for prices, rounding applied at the wrong step,
  discounts and taxes recomputed inconsistently between cart, checkout, and invoice.
- **Stock and orders:** decrement races under concurrent purchases, double submit,
  payment or shipping webhooks that arrive twice or out of order, order state machines
  that allow impossible transitions.
- **Payments:** trusting a client-side success signal, amounts not re-verified on the
  server, refunds that can exceed what was captured.
- **Tracking:** purchase events fired twice, events sent before consent, personal data
  in event payloads, identifiers that differ between the storefront and analytics.
- **Abuse:** coupon stacking, replayed discount codes, enumerable order identifiers.

## Performance claims

Report performance only with a measurement or a plausible growth argument (for example
a query inside a loop over a growing table). An optimization without a measurement is a
guess, not a finding.
