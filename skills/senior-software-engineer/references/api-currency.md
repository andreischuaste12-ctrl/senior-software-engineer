# Atualidade de APIs e migrações

Revisão das adições do segundo arquivo “base-conhecimento-engenharia-software.md”
fornecido por Andrei Schuaste em 5 de novembro de 2026. Usar estas orientações
revisadas, sem promover tabelas de versões ou etiquetas `[V]` do anexo a fatos
verificados. Nenhuma base ou modelo garante acerto integral.

## [A1] Versão-alvo antes de sintaxe nova

Determine separadamente runtime/compilador, dependências resolvidas, edição ou
nível de linguagem, targets e flags. Manifestos podem declarar intervalos; locks
e pins não dispensam conferir a ferramenta instalada e a configuração de CI.

- Em Go, a diretiva `go` estabelece a versão mínima requerida nas versões atuais
  da ferramenta e afeta os recursos de linguagem aceitos no módulo. A diretiva
  `toolchain` e a configuração do ambiente também influenciam a ferramenta usada.
  Não é correto interpretar `go.mod` como um pin exato universal de runtime.
- Em Rust, `edition` escolhe uma edição, `rust-version` declara a versão mínima
  suportada e a toolchain instalada determina recursos estabilizados disponíveis.
  Uma edição antiga pode ser usada com um compilador novo; edição não equivale
  à versão do compilador nem basta para escolher toda API da biblioteca padrão.
- No Windows, confirme também launcher, arquitetura, SDK e sintaxe do terminal.
  Não transplante comandos Bash para PowerShell sem adaptação.

## [A2] Diagnósticos e deprecações

Investigue warnings relevantes e sua origem. Diferencie API removida de API
depreciada ainda disponível; trate como falha quando a política do projeto ou o
risco exigir. Evite migrar dependências inteiras por um aviso de terceiro fora
do escopo. Documente pendências sem suprimir diagnósticos apenas para passar.

Em Python, DeprecationWarning pode ser ignorado por padrão fora de __main__.
Use a configuração de warnings apropriada ao teste e à versão do projeto; não
presuma que silêncio significa ausência de deprecações. Um erro de símbolo também
pode resultar de imports, flags, target ou ambiente incorretos. Confirme a causa
antes de atribuí-lo a uma API inventada ou removida.

## [A3] Existência e procedência de dependências

Antes de instalar um pacote novo, confirme identidade, registry, versão compatível,
licença e evidência de segurança disponível. Downloads e recência são sinais de
contexto, não prova de legitimidade. Ausência de advisories não garante segurança.
Sem acesso suficiente, declare o que não foi verificado; não invente metadados.
Não exponha nomes de pacotes internos ou credenciais em consultas externas.

## [A4] Migrações revisáveis

Quando um upgrade estiver autorizado, considere migradores oficiais compatíveis
com a versão e revise seu alcance. `cargo fix --edition` é parte de um processo,
não uma migração completa: alvos, configurações, manifesto e testes importam.
Não use flags que permitam modificar um checkout sujo para ignorar trabalho alheio.

`ruff check --fix` corrige regras habilitadas; não é um migrador geral de runtime
ou framework. Ruff distingue fixes seguros e inseguros. Revise o diff e rode
checks pertinentes mesmo com correções classificadas como seguras.

Separe mudanças quando isso facilitar diagnóstico, mas respeite matrizes que
exijam atualização coordenada de runtime e bibliotecas. Não configure bots,
cooldown, cron ou alterações de CI automaticamente: dependem do escopo autorizado.
Uma janela de espera não garante que uma versão esteja livre de problemas.

## [A5] Evidência e limites

Para cada afirmação volátil usada, indique fonte, versão-alvo, data da consulta
e se foi observada, inferida ou não verificada. Diferencie suporte do fornecedor,
suporte estendido, atualização gratuita e fim de uma fase comercial.

Links e etiquetas do anexo não comprovam leitura de artigos ou resultados de
benchmarks. O estudo `estudo-atualizacao-continua-de-codigo.md` citado no anexo
não foi fornecido. Não atribua conclusões ou métricas a esse estudo ausente.
Esta referência não ativa navegação, pesquisa, cache nem atualizações automáticas.

## Fontes consultadas para esta revisão

Consulta em 5 de novembro de 2026, restrita aos pontos descritos acima:

- [Go Modules Reference](https://go.dev/ref/mod#go-mod-file-go): diretivas go e toolchain.
- [Cargo Manifest](https://doc.rust-lang.org/cargo/reference/manifest.html): edition e rust-version.
- [Python warnings](https://docs.python.org/3/library/warnings.html): filtros e DeprecationWarning.
- [cargo fix](https://doc.rust-lang.org/cargo/commands/cargo-fix.html): migração de edição e cuidados com o checkout.
- [Documentação Ruff no repositório do mantenedor](https://raw.githubusercontent.com/astral-sh/ruff/main/docs/linter.md): correções seguras e inseguras. A branch main não fixa a versão instalada.
- [Oracle Java SE Support Roadmap](https://www.oracle.com/java/technologies/java-se-support-roadmap.html): fases e modalidades de suporte Oracle, não de todos os distribuidores.

Essas consultas sustentam os pontos identificados, não uma auditoria integral
das fontes e afirmações do anexo. Páginas podem mudar após a consulta.
