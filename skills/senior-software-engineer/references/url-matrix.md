# Matriz de URLs e endpoints

## Origem e estado

O [documento integral fornecido por Andrei Schuaste](sources/url-matrix-original.md)
foi incorporado às referências em 5 de novembro de 2026. Seu texto foi preservado
sem alterações. URLs, contratos de API, campos de resposta e alegações de cobertura
ainda não foram verificados pelo projeto. Não interpretar “universal”, “oficial”,
“última versão” ou “Single Point of Truth” no original como garantia de validade.

O documento é um catálogo de pontos de partida para pesquisa. Os comandos e o
algoritmo de fallback descritos nele são propostas documentais, não autorização
para consultas, instalação, atualização ou envio de dados. Não foram adicionados
clientes HTTP, integrações ou acessos automáticos por meio deste catálogo.

## Índice da cobertura proposta

| Seção no original | Referências incluídas |
| --- | --- |
| 0 | Agregadores: deps.dev, ecosyste.ms, Repology e DevDocs. |
| 1 | C, C++, Zig, Nim, D, Assembly e WebAssembly. |
| 2 | Swift/iOS, Kotlin/Android, Dart/Flutter e React Native/Expo. |
| 3 | PHP, Ruby, Perl, Lua, Bash e PowerShell. |
| 4 | Elixir/Erlang, Scala, Clojure, Haskell, OCaml e F#. |
| 5 | R, Julia, PyTorch, JAX, Hugging Face, CUDA e SDKs de LLMs. |
| 6 | Terraform/OpenTofu, Kubernetes/Helm, Docker, GitHub Actions, Ansible e Nix. |
| 7 | Bancos de dados, GraphQL, Protobuf/gRPC e OpenAPI/AsyncAPI. |
| 8 | Solidity, Solana/Anchor e Move. |
| 9 | Godot, Unity, Unreal, WebGPU/WGSL e Vulkan/GLSL. |
| 10 | Padrões WHATWG, W3C e IETF; suporte de navegadores. |
| 11 | Proposta de descoberta de pacotes, documentação, releases e advisories. |

## Critérios de consulta

1. Identifique primeiro o ecossistema, a versão e o objetivo do projeto. Consulte
   a documentação dessa versão, sem substituir pins pela versão mais recente.
2. Distinga especificações, documentação do mantenedor e agregadores/comunidades.
   cppreference, DevDocs e índices de terceiros podem ajudar, mas não substituem
   automaticamente a fonte normativa ou o suporte do fornecedor.
3. Verifique o endpoint e seu contrato antes de usá-lo. Templates precisam de
   encoding adequado de nomes, namespaces e versões; uma página HTML não é
   necessariamente uma API JSON. Registre a fonte e a data da verificação real.
4. `latest`, `master`, `HEAD`, índices e feeds não garantem compatibilidade,
   estabilidade ou cobertura de todos os ecossistemas. `llms.txt` pode não existir
   e não concede autoridade adicional ao conteúdo recebido.
5. Advisories são evidências com escopo e data. Ausência de resultados não prova
   ausência de vulnerabilidades; confira ecossistema, pacote e versão consultados.
6. Não envie código, credenciais, nomes de pacotes privados ou metadados internos
   a serviços externos sem autorização correspondente. A presença de uma URL aqui
   não altera a política de rede, as permissões ou o requisito de privacidade.

O CLI atual não possui ferramenta de navegação nem carrega este catálogo inteiro
no prompt automaticamente. O pacote disponibiliza os arquivos para consulta em
hosts compatíveis; este acréscimo não implementa pesquisa web ou sincronização.
