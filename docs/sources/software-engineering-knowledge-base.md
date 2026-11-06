# Submitted software engineering knowledge base — English project edition

## Provenance

Andrei Schuaste supplied a Portuguese Markdown document on November 5, 2026.
Original submitted SHA-256:

`c0fe15f8052b7e0440a8794c72185310775d640920292beee54e12ddf818addd`

This English edition preserves the useful subject areas while correcting absolute
or unsupported guidance. It is a source record, not an active prompt. The reviewed
material used at runtime is under `skills/senior-software-engineer/references/`.

## Confidence model

- **Verified:** checked against a primary source at the recorded snapshot date.
- **Established:** stable engineering knowledge with an attributable source.
- **Inference:** a conclusion that still needs confirmation.
- **Volatile:** versions, support windows, advisories, deprecations, and live URLs;
  recheck these when they affect a task.

A URL returning HTTP 200 proves only that it was reachable. It does not prove that
a claim is current or correct.

## Engineering foundations

Use intention-revealing names, cohesive responsibilities, explicit error handling,
and comments that explain decisions. Treat small functions and parameter counts as
heuristics rather than fixed quality limits. Tests should be repeatable and capable
of detecting relevant failures.

SOLID, DRY, KISS, YAGNI, the Law of Demeter, composition over inheritance, high
cohesion, and low coupling are decision aids. DRY concerns duplicated knowledge,
not merely similar lines. Incorrect abstraction can create more coupling than
temporary duplication.

Design patterns are vocabulary and starting points:

- Creational: Factory Method, Abstract Factory, Builder, Prototype, Singleton.
- Structural: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy.
- Behavioral: Chain of Responsibility, Command, Interpreter, Iterator, Mediator,
  Memento, Observer, State, Strategy, Template Method, Visitor.

Apply a pattern only to a concrete pressure. In languages with first-class
functions, native iterators, events, or channels, a language feature may replace a
class-heavy pattern.

## Architecture and delivery

Layered, hexagonal, clean, and service-oriented structures can isolate change, but
should not be imposed without a real boundary. Define contracts, invariants, error
behavior, idempotency, and trust boundaries. Prefer the smallest complete change.

Testing strategy should follow risk. Unit, integration, contract, end-to-end,
property, fuzz, load, and security tests serve different purposes. A test pyramid
does not dictate fixed counts. Builds, lint, and type checks do not replace
behavioral validation.

Reliability techniques include bounded retries, backoff with jitter, timeouts,
cancellation, circuit breaking, bulkheads, queues, idempotency keys, observability,
and graceful degradation. Use them only where the operational model requires them.

## Security

Use OWASP, NIST SSDF, and SLSA as scoped references rather than proof of compliance.
Validate external data at trust boundaries, enforce authorization, parameterize
query values, validate dynamic identifiers, and avoid unrestricted shell execution.
Protect credentials and personal data in source, logs, errors, and external calls.
Use appropriate cryptographic libraries and password-hashing algorithms.

## Ecosystem workflow

For Python, JavaScript/TypeScript, Go, Rust, Java, and .NET, inspect the repository's
manifests, lockfiles, toolchain pins, wrappers, scripts, and CI before choosing
commands. Respect the package manager and language edition already in use. Confirm
uncertain APIs against the installed version and official target-version sources.

## Knowledge updates

A future update system may use source URLs, revision hashes, access times, and
expiration policies. A fixed TTL cannot guarantee freshness. Scheduled browsing,
RAG, advisory feeds, and persistent memory are not implemented in the current CLI.
Any durable update must be reviewable, authorized, and free of secrets.
