# Documentation and endpoint routing matrix

This catalog routes research; it does not authorize network access or installation.
Verify every URL, endpoint schema, authentication rule, rate limit, and target
version before relying on it. Prefer official maintainers and primary registries.

| Ecosystem | Primary sources |
| --- | --- |
| Python | docs.python.org, packaging.python.org, PyPI |
| JavaScript/TypeScript | nodejs.org, npm, MDN, TC39, typescriptlang.org |
| Go | go.dev specification, module reference, package docs, release notes |
| Rust | doc.rust-lang.org, Cargo docs, crates.io, docs.rs, RFCs |
| Java/Kotlin/Scala | OpenJDK/vendor docs, Maven Central, Gradle/Maven, language docs |
| C#/.NET | learn.microsoft.com/dotnet, NuGet, runtime and language repositories |
| C/C++ | ISO working groups, cppreference, compiler docs, Conan, vcpkg |
| Mobile | Android Developers, Apple Developer, Swift packages, CocoaPods |
| Web frameworks | Maintainer documentation and the project's pinned release notes |
| Databases | Vendor manuals for the deployed server and driver versions |
| Cloud/IaC | Provider docs, Terraform/OpenTofu Registry, Kubernetes docs |
| Security | OSV, NVD, GitHub Advisories, vendor advisories, OWASP, NIST |
| Observability | OpenTelemetry and the selected backend's versioned docs |

Cross-ecosystem services such as deps.dev, Ecosyste.ms, Repology, and DevDocs may
help discovery. They do not replace maintainer documentation for critical choices.

Before a lookup, inspect local manifests, locks, source, types, and cached docs.
Avoid sending proprietary identifiers to public endpoints. Record the URL, revision,
access date, and exact conclusion. If evidence conflicts, prefer target-version
runtime behavior and primary documentation, and state unresolved uncertainty.

The English edition of the owner-supplied catalog is preserved at
[sources/url-matrix-submitted.md](sources/url-matrix-submitted.md). Its original
Portuguese file hash is recorded there; the endpoint claims were not fully audited.
