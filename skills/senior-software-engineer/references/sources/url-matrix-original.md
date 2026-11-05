# Matriz Universal de URLs e Endpoints: Todos os Ecossistemas de Código

---

## 0. APIs Unificadoras Globais (Single Point of Truth para Qualquer Pacote)

Antes de consultar cada linguagem individualmente, o agente pode usar agregadores universais que indexam **dezenas de ecossistemas** em um único endpoint JSON:

| Plataforma Global | Endpoint REST / Template de Consulta | Cobertura |
| :--- | :--- | :--- |
| **Google Open Source Insights (`deps.dev`)** | `https://api.deps.dev/v3/systems/{sistema}/packages/{pacote}`<br>*(Sistemas: `npm`, `pypi`, `go`, `cargo`, `maven`, `nuget`)* | Versão `isDefault` (latest), grafo de dependências, licenças e advisories de segurança. |
| **Ecosystems.ms (Open Source Index)** | `https://packages.ecosyste.ms/api/v1/registries/{registry}/packages/{pacote}` | **+35 gerenciadores de pacotes** (inclui `packagist`, `rubygems`, `hex`, `pub`, `cocoapods`, `cpan`, `clojars`, `cran`, `hackage`, `conda`, `brew`, `docker`). |
| **Repology (Pacotes de SO / Distros)** | `https://repology.org/api/v1/project/{nome}` | Versão mais recente de compiladores, CLIs e libs C/C++ em Linux/BSD/macOS/Windows (`apt`, `apk`, `pacman`, `brew`, `winget`, `nix`). |
| **DevDocs Universal Index** | `https://devdocs.io/docs.json` | Lista JSON completa com a versão atual e URL base de **todas as linguagens e frameworks** documentados no mundo. |

---

## 1. Sistemas, Baixo Nível e Embarcados (C, C++, Zig, Assembly, Nim)

| Linguagem / Tecnologia | Referência Oficial & Especificação | Registries de Pacotes & APIs | Changelogs / Evolução (Standards) |
| :--- | :--- | :--- | :--- |
| **C (ISO C17 / C23)** | `https://en.cppreference.com/w/c` | **vcpkg:** `https://vcpkg.io/output/vcpkg.json`<br>**Conan:** `https://conan.io/center` | `https://www.open-std.org/jtc1/sc22/wg14/` |
| **C++ (C++20 / C++23 / C++26)** | `https://en.cppreference.com/w/cpp` | **Conan Center:** `https://conan.io/center`<br>**vcpkg:** `https://vcpkg.link/` | `https://isocpp.org/std/status`<br>`https://en.cppreference.com/w/cpp/compiler_support` |
| **Zig** | `https://ziglang.org/documentation/master/` | `https://zigistry.dev/` | `https://ziglang.org/download/` (Release Notes) |
| **Nim** | `https://nim-lang.org/documentation.html` | `https://nimble.directory/packages.json` | `https://nim-lang.org/blog.html` |
| **D (Dlang)** | `https://dlang.org/spec/spec.html` | `https://code.dlang.org/api/packages/dump` | `https://dlang.org/changelog/index.html` |
| **Assembly (x86_64 / ARM / RISC-V)** | **x86:** `https://www.felixcloutier.com/x86/`<br>**ARM:** `https://developer.arm.com/documentation`<br>**RISC-V:** `https://riscv.org/technical/specifications/` | N/A (Hardware ISA) | **LLVM/Clang Target Docs:** `https://llvm.org/docs/ReleaseNotes.html` |
| **WebAssembly (Wasm / WASI)** | `https://webassembly.github.io/spec/core/` | **WAPM / Wasmer:** `https://wasmer.io/`<br>**Component Model:** `https://component-model.bytecodealliance.org/` | `https://github.com/WebAssembly/proposals` |

---

## 2. Desenvolvimento Mobile e Multiplataforma

| Linguagem / Stack | Documentação Oficial | API de Registry / Pacotes | Evolução & Release Notes |
| :--- | :--- | :--- | :--- |
| **Swift / iOS** | `https://www.swift.org/documentation/`<br>`https://developer.apple.com/documentation/` | **Swift Package Index:** `https://swiftpackageindex.com/`<br>**CocoaPods:** `https://trunk.cocoapods.org/api/v1/pods/{pod}` | **Swift Evolution:** `https://www.swift.org/swift-evolution/`<br>`https://github.com/swiftlang/swift/releases.atom` |
| **Kotlin / KMP / Android** | `https://kotlinlang.org/docs/home.html`<br>`https://developer.android.com/jetpack/androidx/explorer` | **Maven Google:** `https://maven.google.com/web/index.html`<br>**Maven Central:** `https://central.sonatype.com/` | `https://kotlinlang.org/docs/releases.html`<br>KEEP: `https://github.com/Kotlin/KEEP` |
| **Dart & Flutter** | `https://dart.dev/guides`<br>`https://docs.flutter.dev/` | **Pub.dev API:** `https://pub.dev/api/packages/{pacote}` | `https://dart.dev/guides/whats-new`<br>`https://docs.flutter.dev/release/release-notes` |
| **React Native / Expo** | `https://reactnative.dev/docs/getting-started`<br>`https://docs.expo.dev/` | **React Native Directory:** `https://reactnative.directory/api/libraries` | `https://reactnative.dev/blog`<br>**Upgrade Helper:** `https://react-native-community.github.io/upgrade-helper/` |

---

## 3. Linguagens Web Backend, Scripting e Automação

| Linguagem / Ecossistema | Documentação Oficial | API de Registry (Última Versão) | RFCs, Changelogs & Migração |
| :--- | :--- | :--- | :--- |
| **PHP (8.3 / 8.4+) & Laravel/Symfony** | `https://www.php.net/manual/en/`<br>`https://laravel.com/docs`<br>`https://symfony.com/doc/current/index.html` | **Packagist API:** `https://repo.packagist.org/p2/{vendor}/{pkg}.json` | **PHP RFCs:** `https://wiki.php.net/rfc`<br>**Migration:** `https://www.php.net/manual/en/appendices.php` |
| **Ruby & Rails** | `https://docs.ruby-lang.org/en/master/`<br>`https://guides.rubyonrails.org/` | **RubyGems API:** `https://rubygems.org/api/v1/gems/{gem}.json` | `https://www.ruby-lang.org/en/downloads/releases/`<br>`https://guides.rubyonrails.org/upgrading_ruby_on_rails.html` |
| **Perl** | `https://perldoc.perl.org/` | **MetaCPAN API:** `https://fastapi.metacpan.org/v1/release/{modulo}` | `https://perldoc.perl.org/perldelta` |
| **Lua / LuaJIT** | `https://www.lua.org/manual/` | **LuaRocks:** `https://luarocks.org/m/root/manifest.json` | `https://www.lua.org/versions.html` |
| **Bash / POSIX Shell** | `https://www.gnu.org/software/bash/manual/` | **ShellCheck Wiki (Boas Práticas):** `https://www.shellcheck.net/wiki/` | `https://tiswww.case.edu/php/chet/bash/CHANGES` |
| **PowerShell (7.x+)** | `https://learn.microsoft.com/en-us/powershell/` | **PSGallery API:** `https://www.powershellgallery.com/api/v2/FindPackagesById()?id='{modulo}'` | `https://learn.microsoft.com/en-us/powershell/scripting/whats-new/overview` |

---

## 4. Linguagens Funcionais, BEAM e JVM Alternativas

| Linguagem | Documentação Oficial | API de Registry / Pacotes | Changelogs / Releases |
| :--- | :--- | :--- | :--- |
| **Elixir / Erlang (BEAM)** | `https://hexdocs.pm/elixir/Kernel.html`<br>`https://www.erlang.org/doc/` | **Hex.pm API:** `https://hex.pm/api/packages/{pacote}`<br>**Docs por Pacote:** `https://hexdocs.pm/{pacote}` | `https://github.com/elixir-lang/elixir/releases.atom` |
| **Scala (Scala 3)** | `https://docs.scala-lang.org/scala3/` | **Scaladex API:** `https://index.scala-lang.org/api/project?organization={org}&repository={repo}` | `https://www.scala-lang.org/news/` |
| **Clojure** | `https://clojure.org/reference/documentation` | **Clojars API:** `https://clojars.org/api/artifacts/{grupo}/{artefato}` | `https://clojure.org/releases/releases` |
| **Haskell** | `https://www.haskell.org/documentation/` | **Hackage API:** `https://hackage.haskell.org/package/{pacote}/preferred.json`<br>**Stackage:** `https://www.stackage.org/` | **GHC Users Guide:** `https://downloads.haskell.org/ghc/latest/docs/users_guide/` |
| **OCaml** | `https://ocaml.org/docs` | **OPAM Packages:** `https://ocaml.org/packages` | `https://ocaml.org/releases` |
| **F#** | `https://learn.microsoft.com/en-us/dotnet/fsharp/` | **NuGet:** `https://api.nuget.org/v3-flatcontainer/{pacote}/index.json` | `https://learn.microsoft.com/en-us/dotnet/fsharp/whats-new/` |

---

## 5. Ciência de Dados, IA/ML, Computação Científica e GPU

| Ecossistema / Stack | Documentação & API Reference | Registry / Hub | Release Notes & Migração |
| :--- | :--- | :--- | :--- |
| **R (Estatística/Dados)** | `https://cran.r-project.org/manuals.html` | **CRANDB API:** `https://crandb.r-pkg.org/{pacote}` | `https://cran.r-project.org/doc/manuals/r-release/NEWS.html` |
| **Julia** | `https://docs.julialang.org/en/v1/` | **JuliaHub:** `https://juliahub.com/ui/Packages` | `https://julialang.org/downloads/` |
| **PyTorch** | `https://pytorch.org/docs/stable/index.html` | `https://pypi.org/pypi/torch/json` | `https://github.com/pytorch/pytorch/releases.atom` |
| **JAX / Flax** | `https://jax.readthedocs.io/en/latest/` | `https://pypi.org/pypi/jax/json` | `https://jax.readthedocs.io/en/latest/changelog.html` |
| **Hugging Face (Transformers)** | `https://huggingface.co/docs/transformers/index` | **HF Hub API:** `https://huggingface.co/api/models` | `https://github.com/huggingface/transformers/releases.atom` |
| **CUDA / NVIDIA Compute** | `https://docs.nvidia.com/cuda/` | `https://developer.nvidia.com/cuda-downloads` | `https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/` |
| **SDKs de LLMs (Gemini, OpenAI, Anthropic)** | • **Gemini:** `https://ai.google.dev/gemini-api/docs`<br>• **OpenAI:** `https://platform.openai.com/docs`<br>• **Anthropic:** `https://docs.anthropic.com/` | • `https://pypi.org/pypi/google-genai/json`<br>• `https://pypi.org/pypi/openai/json`<br>• `https://pypi.org/pypi/anthropic/json` | • `https://ai.google.dev/gemini-api/docs/changelog`<br>• `https://platform.openai.com/docs/changelog`<br>• `https://docs.anthropic.com/en/release-notes/overview` |

---

## 6. Cloud, DevOps, Infraestrutura como Código (IaC) e Containers

| Ferramenta / Plataforma | Documentação Oficial | API de Registry de Módulos/Imagens | Changelogs / Depreciações |
| :--- | :--- | :--- | :--- |
| **Terraform / OpenTofu** | `https://developer.hashicorp.com/terraform/docs`<br>`https://opentofu.org/docs/` | **Terraform Registry API:**<br>`https://registry.terraform.io/v1/providers/{namespace}/{type}` | `https://github.com/hashicorp/terraform/releases.atom` |
| **Kubernetes (K8s) & Helm** | `https://kubernetes.io/docs/reference/` | **ArtifactHub API (Helm/K8s):**<br>`https://artifacthub.io/api/v1/packages/helm/{repo}/{chart}` | **K8s Deprecation Guide (CRÍTICO):**<br>`https://kubernetes.io/docs/reference/using-api/deprecation-guide/` |
| **Docker / Containers** | `https://docs.docker.com/reference/` | **Docker Hub Tags API:**<br>`https://hub.docker.com/v2/repositories/library/{imagem}/tags?page_size=10` | `https://docs.docker.com/engine/release-notes/` |
| **GitHub Actions** | `https://docs.github.com/en/actions` | **GitHub Marketplace Actions:**<br>`https://api.github.com/repos/actions/{action-name}/releases/latest` | `https://github.blog/changelog/label/actions/` |
| **Ansible** | `https://docs.ansible.com/` | **Ansible Galaxy API:**<br>`https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/{namespace}/{name}/` | `https://docs.ansible.com/ansible/latest/porting_guides/porting_guides.html` |
| **Nix / NixOS** | `https://nixos.org/manual/nixpkgs/stable/` | **NixOS Search:** `https://search.nixos.org/packages` | `https://nixos.org/manual/nixos/stable/release-notes` |

---

## 7. Bancos de Dados, Query Languages e Contratos de API

| Tecnologia | Documentação & Sintaxe Atual | Release Notes & Novas Features |
| :--- | :--- | :--- |
| **PostgreSQL** | `https://www.postgresql.org/docs/current/` | `https://www.postgresql.org/docs/current/release.html` |
| **MySQL / MariaDB** | `https://dev.mysql.com/doc/refman/en/` | `https://dev.mysql.com/doc/relnotes/mysql/8.4/en/` |
| **SQLite** | `https://www.sqlite.org/docs.html` | `https://www.sqlite.org/changes.html` |
| **DuckDB (OLAP)** | `https://duckdb.org/docs/` | `https://github.com/duckdb/duckdb/releases.atom` |
| **Redis / Valkey** | `https://redis.io/docs/latest/commands/`<br>`https://valkey.io/commands/` | `https://github.com/valkey-io/valkey/releases.atom` |
| **MongoDB** | `https://www.mongodb.com/docs/manual/` | `https://www.mongodb.com/docs/manual/release-notes/` |
| **GraphQL** | `https://spec.graphql.org/` | `https://github.com/graphql/graphql-spec/releases` |
| **Protocol Buffers / gRPC** | `https://protobuf.dev/`<br>`https://grpc.io/docs/` | `https://protobuf.dev/news/` (Editions 2023+) |
| **OpenAPI / AsyncAPI** | `https://spec.openapis.org/oas/latest.html`<br>`https://www.asyncapi.com/docs/reference/specification/latest` | `https://github.com/OAI/OpenAPI-Specification/releases` |

---

## 8. Web3, Smart Contracts e Criptografia

| Linguagem / Rede | Documentação Oficial | Padrões & Bibliotecas | Releases / Compilador |
| :--- | :--- | :--- | :--- |
| **Solidity (EVM)** | `https://docs.soliditylang.org/en/latest/` | **OpenZeppelin Contracts:** `https://docs.openzeppelin.com/contracts`<br>**Foundry:** `https://book.getfoundry.sh/` | `https://binaries.soliditylang.org/bin/list.json` (JSON oficial com última versão do `solc`) |
| **Rust / Anchor (Solana)** | `https://solana.com/docs`<br>`https://www.anchor-lang.com/docs` | `https://crates.io/api/v1/crates/anchor-lang` | `https://github.com/coral-xyz/anchor/releases.atom` |
| **Move (Sui / Aptos)** | `https://move-book.com/`<br>`https://docs.sui.io/` | `https://aptos.dev/en/build/smart-contracts` | `https://github.com/MystenLabs/sui/releases.atom` |

---

## 9. Game Dev, Computação Gráfica e Shaders

| Engine / API Gráfica | Documentação & Scripting Reference | Changelogs / Especificações |
| :--- | :--- | :--- |
| **Godot (GDScript / C#)** | `https://docs.godotengine.org/en/stable/` | `https://godotengine.org/releases/` |
| **Unity (C#)** | `https://docs.unity3d.com/ScriptReference/` | `https://unity.com/releases/editor/whats-new` |
| **Unreal Engine (C++)** | `https://dev.epicgames.com/documentation/en-us/unreal-engine/` | `https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-release-notes` |
| **WebGPU & WGSL** | `https://www.w3.org/TR/webgpu/`<br>`https://www.w3.org/TR/WGSL/` | `https://developer.chrome.com/blog/new-in-webgpu` |
| **Vulkan / GLSL** | `https://docs.vulkan.org/spec/latest/index.html` | `https://github.com/KhronosGroup/Vulkan-Docs/releases.atom` |

---

## 10. Padrões Universais da Web e Internet (W3C, WHATWG, IETF)

Para validar protocolos de rede, headers HTTP, APIs nativas do navegador e formatos de dados:

* **HTML Living Standard (WHATWG):** `https://html.spec.whatwg.org/multipage/`
* **DOM & Fetch Living Standards:** `https://dom.spec.whatwg.org/` | `https://fetch.spec.whatwg.org/`
* **W3C Technical Reports (CSS, WebAPIs, Acessibilidade WCAG):** `https://www.w3.org/TR/`
* **Can I Use (JSON de suporte de features CSS/JS em navegadores):** `https://raw.githubusercontent.com/Fyrd/caniuse/main/data.json`
* **IETF Datatracker (RFCs de Protocolos — HTTP, TLS, OAuth, JWT):** `https://datatracker.ietf.org/doc/rfc{numero}/` | API: `https://datatracker.ietf.org/api/v1/doc/document/`

---

## 11. Algoritmo Universal de Resolução para o Agente (Fallback em 4 Passos)

Sempre que o Agente encontrar **qualquer linguagem ou biblioteca desconhecida**, ele deve executar esta sequência determinística:

1. **Consultar API Unificadora (`Ecosystems.ms` ou `deps.dev`):**
   * `GET https://packages.ecosyste.ms/api/v1/registries/{registry}/packages/{pacote}`
   * Extrair `latest_release_number` e `repository_url`.
2. **Tentar Ingestão Direta via `llms.txt`:**
   * `GET https://{dominio_oficial}/llms.txt`
3. **Consultar Última Release e Changelog no Repositório Git:**
   * `GET https://api.github.com/repos/{owner}/{repo}/releases/latest`
   * `GET https://raw.githubusercontent.com/{owner}/{repo}/HEAD/CHANGELOG.md`
4. **Verificar Advisories de Segurança (`OSV.dev`):**
   * `POST https://api.osv.dev/v1/query` com `{"package": {"name": "{pacote}", "ecosystem": "{ecossistema}"}, "version": "{versao}"}`.