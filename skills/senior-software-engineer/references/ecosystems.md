# Ecosystem references

Read only the sections relevant to the task. These are options, not universal
installation commands. Prefer repository scripts, pins, and configuration.

## Python

Inspect `pyproject.toml`, locks, requirements, Python pins, and CI. Respect the
adopted environment manager. Use configured pytest, Ruff, mypy, or Pyright.
Type annotations do not replace boundary validation. Avoid mutable defaults and
release resources with context managers.

## JavaScript and TypeScript

Inspect `package.json`, `packageManager`, lockfile, runtime pins, `tsconfig`,
and scripts. Do not mix npm, pnpm, Yarn, Bun, Node.js, or Deno workflows. Prefer
existing build, lint, type-check, and test scripts. TypeScript types do not validate
runtime payloads.

## Go

Inspect `go.mod`, `go.sum`, `go.work`, toolchain directives, and CI. Use
relevant `go build`, `go vet`, and `go test` scopes. Vet does not replace build
or tests. Preserve error wrapping, pass `context.Context` through cancelable work,
and bound goroutines.

## Rust

Inspect `Cargo.toml`, `Cargo.lock`, `rust-toolchain`, workspace, edition, MSRV,
features, and targets. Use appropriately scoped Cargo check/test, Clippy, and
`cargo fmt --check`. Do not assume `--all-features` combinations are valid.
Avoid unjustified `unwrap`, `expect`, and cloning.

## Java

Inspect Maven or Gradle files, wrappers, toolchains, profiles, and modules. Prefer
`mvnw` or `gradlew`. Container-based tests require their runtime. Records,
sealed types, and virtual threads depend on version and workload; preserve
transaction, pool, and public-contract boundaries.

## C# and .NET

Inspect `global.json`, solutions, projects, target frameworks, NuGet configuration,
and lockfiles. Respect private sources without exposing credentials. Use repository
restore/build/test flows. Preserve cancellation, async behavior, and resource
disposal. AOT and framework migrations require explicit compatibility work.

## PHP, WordPress, and WooCommerce

Inspect `composer.json` and its lock, the PHP version in use, and any configured
PHPUnit, PHPStan, or PHPCS setup. Never read or print `wp-config` values. Treat every
request, AJAX action, and REST route that changes state as needing a nonce (or another
CSRF defense) and a capability check, with a permission callback on REST routes. Sanitize
input and escape output for the context it lands in. Pass dynamic SQL through
`$wpdb->prepare`, and prefer the platform's data APIs over writing core tables directly.
For WooCommerce, work through its CRUD objects and APIs, confirm compatibility with
the order storage in use before touching orders, and treat payment and shipping
callbacks as delivered more than once and out of order. Check hook priority and plugin
interaction before blaming one plugin, remember that scheduled actions and object caches
add state, and do not edit vendor or core files. Confirm version-specific behavior in
the target version's documentation.

## SQL

Identify the engine and version and the migration tool before writing statements.
Bind values as parameters. Remember three-valued logic (`NULL` in comparisons and
`NOT IN`), joins that multiply rows, and aggregation without a correct `GROUP BY`.
Paginate over a deterministic order. Use exact decimal types for money and be explicit
about time zones. Run `UPDATE` and `DELETE` first as a `SELECT`, or inside a transaction
on a copy that you can roll back. Support a performance claim with the plan and a
measurement, and keep migrations reversible and aware of locks.

## Shell

Quote every expansion, and decide deliberately whether strict-mode options such as
`set -euo pipefail` suit the script. Check that `cd` succeeded and that a variable used
in a deletion path is not empty. Do not parse `ls`. Note differences between `sh`, `bash`,
and `zsh`, and between GNU and BSD tools. Run the configured linter (for example
ShellCheck) when one exists.

## C and C++

Memory safety and undefined behavior dominate: bounds, lifetimes, ownership, integer
overflow, and uninitialized reads. Build with the project's warnings enabled and choose
sanitizers to match the hypothesis; some sanitizers cannot be combined in one build, so
use separate builds. Check iterator invalidation, destructor exceptions, and data races
in C++.

## Infrastructure and CI

Containers: pin the base image, run as a non-root user, keep secrets out of layers, and
keep the build context small. Infrastructure as code: read the plan before applying, look
for hidden replacements and destroys, and check state locking and encryption and the
breadth of permissions. Kubernetes: set resource limits and probes, avoid privileged
containers, and keep secrets out of configuration maps. CI: pin third-party actions to
immutable references, give the token the least permission it needs, never run untrusted
pull-request code with access to secrets, and do not let failures be ignored.

## Other languages

Discover the project's manifests, compiler or runtime, tests, and conventions.
Consult official target-version sources when needed. State execution limits and do
not transplant another language's conventions without evidence.
