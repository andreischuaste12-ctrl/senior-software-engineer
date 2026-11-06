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

## Other languages

Discover the project's manifests, compiler or runtime, tests, and conventions.
Consult official target-version sources when needed. State execution limits and do
not transplant another language's conventions without evidence.
