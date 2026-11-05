# Referências por ecossistema

Leia somente a seção aplicável. Exemplos abaixo não são comandos universais nem
instruções para instalar ferramentas. Primeiro use scripts, pins e configurações
do repositório. Comandos de formatadores devem operar em modo de verificação na
validação; reescrita de arquivos só no escopo da implementação autorizada.

## Python

- Inspecione pyproject.toml, lockfile, requirements, pins de Python e CI. Respeite
  uv, Poetry ou venv/pip já adotados; não misture gerenciadores.
- Use pytest, Ruff e mypy/Pyright se configurados. Ruff não substitui testes ou
  typecheck. Execute as ferramentas no ambiente do projeto.
- Anote contratos relevantes, evite defaults mutáveis e libere recursos com
  context managers. Dataclasses e bibliotecas de validação dependem do caso;
  não adicione Pydantic por padrão.

## JavaScript / TypeScript

- Inspecione package.json, packageManager, lockfile, pins de runtime, tsconfig e
  scripts. Não misture npm, pnpm, Yarn ou Bun; respeite Node.js/Bun/Deno reais.
- Prefira scripts existentes de build, lint, typecheck e testes. tsc --noEmit só
  é apropriado quando compatível com a configuração, incluindo referências entre
  projetos. Playwright é útil para fluxos de navegador quando já necessário.
- Prefira unknown e narrowing para entradas desconhecidas. Justifique usos de any
  localmente; não imponha strict ao repositório inteiro em uma correção pequena.
  Tipos TypeScript não validam payloads em runtime.

## Go

- Inspecione go.mod, go.sum, go.work quando houver, diretivas de toolchain e CI.
- Se compatíveis com o escopo, use go build ./..., go vet ./... e go test ./....
  Selecione pacotes relevantes em monorepos. go vet não substitui build ou testes.
  Use -race quando plataforma, recursos e objetivo justificarem.
- Contextualize erros preservando wrapping, propague context.Context em operações
  canceláveis e limite goroutines. Não introduza interfaces sem consumidor real.

## Rust

- Inspecione Cargo.toml, Cargo.lock, rust-toolchain e workspace. Respeite edição,
  MSRV, features e targets; não habilite --all-features sem verificar conflitos.
- Use cargo check/test e Clippy conforme o projeto; --locked é apropriado quando
  o lockfile existente deve permanecer fixo. cargo fmt --check verifica formato.
  Auditoria requer ferramenta e base disponíveis; relate quando não executada.
- Propague erros recuperáveis; unwrap/expect exigem invariantes justificáveis.
  Evite clones desnecessários sem comprometer clareza ou forçar otimização.

## Java

- Inspecione pom.xml ou arquivos Gradle, wrappers, toolchains e módulos. Use
  ./mvnw ou ./gradlew quando disponíveis, com perfis e targets documentados.
- Execute testes e build pertinentes. Testcontainers exige runtime de containers;
  não descreva testes ignorados por falta dele como aprovados.
- Records, sealed types e virtual threads dependem da versão e da carga. Preserve
  limites de pools, transações e contratos, mesmo com concorrência mais barata.

## C# / .NET

- Inspecione global.json, solution/projetos, TargetFramework(s), NuGet.Config e
  locks. Respeite fontes privadas sem exibir credenciais.
- Use dotnet restore/build/test conforme scripts e CI. --locked-mode pressupõe
  lockfile e fluxo compatíveis. Não use --no-restore sem restore válido.
- Preserve cancelamento, descarte de recursos e fluxos async. AOT e migrações de
  framework exigem compatibilidade própria, não são melhorias automáticas.

## Outras linguagens

Descubra manifestos, compilador/runtime, ferramentas e testes no próprio projeto.
Consulte documentação oficial da versão-alvo quando necessário. Declare limites
de conhecimento ou execução e não transplante convenções de outra linguagem.
