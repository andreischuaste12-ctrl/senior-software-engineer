# Revisão da segunda base de conhecimento

Material fornecido por Andrei Schuaste, com revisão documental registrada em 5 de
novembro de 2026. O [novo anexo original](fontes/base-conhecimento-engenharia-software-v2-original.md)
foi preservado integralmente, sem sobrescrever a primeira versão. É material
de referência não aprovado integralmente; seu bloco de system prompt não foi
adotado como instrução do agente.

## Resultado da revisão

O delta em relação ao primeiro anexo acrescenta identificação de versão-alvo,
regras de deprecação, verificação de pacotes, migradores e métricas de avaliação.
A [referência operacional revisada](../skills/senior-software-engineer/references/api-currency.md)
aproveita esses pontos com as correções abaixo e é carregada pelo CLI.

| Afirmação ou orientação do anexo | Conclusão e tratamento |
| --- | --- |
| `go` e `edition` definem os recursos disponíveis. | Parcial. `go` afeta recursos da linguagem e versão mínima; Rust exige distinguir edição, rust-version, toolchain, targets e features. |
| Toda deprecação deve falhar e nunca pode ser usada. | Regra excessiva. Distinguir remoção, disponibilidade, política de CI, origem e necessidade de compatibilidade. |
| API inexistente comprova erro da memória do modelo. | Causa não demonstrada. Verificar import, versão, configuração, target e ambiente. |
| Migradores determinísticos garantem uma migração adequada. | Não garantem. Conferir versões, escopo, diff, configurações e testes. Ruff fix não é migrador universal. |
| Java 17 está em EOL em setembro de 2026. | Generalização incorreta. O roadmap Oracle distingue Premier até setembro de 2026 e Extended até setembro de 2029; termos e distribuidores variam. |
| Downloads, cooldown ou ausência de CVEs demonstram segurança. | Não demonstram. São sinais com limitações; nenhuma dessas medidas garante pacote seguro. |
| Há evidências em um estudo na mesma pasta. | Estudo não fornecido. Referências a ICSE, VersiCode, CodeUpdateArena, GitChameleon e USENIX não foram avaliadas e não sustentam métricas neste projeto. |
| Etiquetas `[V]` certificam os fatos para o projeto. | Não. São alegações do autor do anexo; somente consultas documentadas nesta revisão contam como verificações próprias, com escopo explícito. |

## Verificações pontuais do snapshot

As consultas abaixo foram realizadas em 5 de novembro de 2026. Não impõem upgrades
nem certificam toda a tabela ou todos os recursos listados no anexo:

| Fonte consultada | Observação efetiva | Limite |
| --- | --- | --- |
| [Downloads Python](https://www.python.org/downloads/) | A página apresentou Python 3.15.2 para download. | Não revalida cada PEP, data de patch ou política de suporte do anexo. |
| [Downloads Go](https://go.dev/dl/) | A parte recebida apresentou go1.27.3 como estável. | A leitura foi truncada em 1500001 bytes; não foi uma auditoria do arquivo completo. |
| [Rust latest](https://blog.rust-lang.org/releases/latest/) e [anúncio de 1.99.1](https://blog.rust-lang.org/2026/10/15/Rust-1.99.1/) | O índice usa redirecionamento HTML para o anúncio; o destino confirma o point release e a data de 15 de outubro de 2026. | HTTP 200 no índice, sozinho, não valida o anúncio. Não revalida todos os recursos atribuídos ao Rust 1.96. |
| [Anúncio TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) | Confirma publicação em 8 de julho de 2026, mudanças de defaults e ausência de API programática nessa versão. | Não foi avaliada toda a tabela de breaking changes nem validado o beta 7.1. |
| [Node.js Releases](https://nodejs.org/en/about/previous-releases) | A página apresentou v26.13.0 como Latest LTS e v27 como Alpha. | Não confirma por si só todos os codinomes, EOLs e condições do snapshot. |
| [Oracle Support Roadmap](https://www.oracle.com/java/technologies/java-se-support-roadmap.html) | Distingue Premier, Extended e Sustaining; planeja Java 29 LTS para setembro de 2027. | Plano não equivale a release entregue e não descreve suporte de todos os fornecedores. |

## Evidências e pendências

O [registro de consultas](verificacoes/base-v2-2026-11-05.json) contém URLs,
status, hashes dos bytes recebidos, trechos e indicação de truncamento. Hash de
uma página identifica a resposta recebida, não comprova suas afirmações. Os HTMLs
completos não estão versionados; os hashes não substituem um arquivo arquivado.

A página OpenJDK e a documentação Ruff no site retornaram HTTP 403. Para os pontos
de Ruff foi possível consultar a documentação no repositório oficial; para suporte
Java, foi consultado o roadmap Oracle. Não inferir indisponibilidade da documentação
em outros ambientes nem validar automaticamente conteúdo que não foi recebido.

Não foram revalidados todos os links, livros, datas, APIs, PEPs/JEPs, CVEs ou
artigos do anexo. Não houve execução das toolchains de todas as linguagens nem
avaliação de um modelo real. Os cenários comportamentais continuam pendentes.
Nenhum status nesta revisão significa “100% assertivo”.
