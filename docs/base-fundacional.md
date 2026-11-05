# Base de conhecimento fundacional

## Objetivo e estado

Referência para projetar um agente de engenharia de software capaz de analisar,
implementar, refatorar e depurar código em diferentes linguagens. Documento
revisado a partir de “Base de Conhecimento Fundacional: Agente de Engenharia de
Software”, fornecido pelo proponente do projeto em 5 de novembro de 2026.
Não deriva de uma análise da skill externa citada em CONTRIBUTING.md.

As recomendações são hipóteses de trabalho orientadas por contexto. Há uma
[implementação inicial de agente CLI](agente-cli.md), sem RAG, sandbox dedicada,
integração MCP ou atualização de memória. A eficácia com modelos reais ainda
não foi avaliada. As ferramentas citadas são exemplos, não dependências.

## 1. Design e qualidade de código

| Princípio | Aplicação | Sinais para investigar |
| --- | --- | --- |
| Clareza | Usar nomes do domínio, responsabilidades coesas e fluxo legível. Extrair constantes quando acrescentarem significado. | Aninhamento excessivo, intenção obscura, efeitos colaterais inesperados. |
| DRY | Centralizar regras com a mesma razão de mudança. Admitir duplicação temporária quando uma abstração ainda não estiver clara. | Uma mudança de negócio exige alterações coordenadas em vários lugares. |
| KISS e YAGNI | Resolver o requisito atual com a solução mais simples que preserve os contratos necessários. | Extensibilidade especulativa e abstrações sem consumidor real. |

Comprimento de função, número de parâmetros, profundidade de indentação e
complexidade ciclomática ajudam a localizar riscos. Não são limites universais
nem justificativa suficiente para uma refatoração. Seguir os limites configurados
no projeto; discutir exceções com evidências. Guard clauses podem ajudar, mas
não devem prejudicar a clareza do fluxo ou a liberação de recursos.

Comentários podem explicar decisões, contratos, algoritmos e operações difíceis
de compreender. Evitar comentários que apenas repetem o código e mantê-los atuais.

### SOLID com contexto

- **SRP:** separar responsabilidades que mudam por razões distintas; isolar domínio
  e infraestrutura quando essa separação reduzir acoplamento.
- **OCP:** oferecer pontos de extensão para variações reais. Condicionais simples
  e alterações diretas continuam adequadas quando não há necessidade de extensão.
- **LSP:** preservar invariantes, pré-condições, pós-condições e comportamento
  observável do contrato ao substituir implementações.
- **ISP:** criar interfaces coesas para os consumidores existentes, sem fragmentação
  artificial de cada método em uma interface.
- **DIP:** explicitar dependências e proteger políticas de negócio contra detalhes
  voláteis. Uma função ou um módulo pode bastar; containers de DI são opcionais.

Preferir composição quando facilitar evolução e testes. Herança permanece válida
quando houver uma relação de substituição bem definida.

### Catálogo de decisão para padrões

| Padrão | Situação útil | Custo ou alternativa |
| --- | --- | --- |
| Factory Method / Abstract Factory | Variações reais de criação ou famílias de objetos. | Construtor direto quando não houver variação. |
| Builder | Construção complexa que precisa preservar invariantes. | Construtor, parâmetros nomeados ou struct para casos simples. |
| Singleton | Recurso com ciclo de vida compartilhado explicitamente controlado. | Estado global oculto prejudica isolamento; preferir dependência explícita. |
| Adapter | Traduzir um contrato externo para o contrato do domínio. | Evitar camadas sem tradução ou proteção útil. |
| Decorator | Compor comportamentos como métricas ou cache. | Considerar ordem, observabilidade e custo; pipeline pode ser mais claro. |
| Facade | Oferecer uma entrada coesa para um subsistema complexo. | Evitar concentrar regras de negócio sem relação. |
| Proxy | Controlar acesso ou adiar obtenção de um recurso. | Tornar latência, falhas e efeitos visíveis ao consumidor. |
| Strategy | Alternar políticas ou algoritmos reais. | Uma função ou condicional pode ser suficiente. |
| Observer / Pub-Sub | Notificar consumidores com acoplamento reduzido. | Definir entrega, ordenação, falhas e cancelamento de assinaturas. |
| Command | Representar ações para fila, auditoria ou desfazer. | Desfazer e idempotência exigem projeto próprio; não vêm do padrão. |
| State | Modelar estados e transições com comportamentos distintos. | Enum e tabela de transições podem bastar. |
| Chain of Responsibility | Compor etapas de processamento. | Definir ordem e comportamento quando nenhuma etapa tratar a entrada. |

Adotar um padrão pelo problema que resolve e pela melhoria verificável, não por
preferência de catálogo. Recursos funcionais ou nativos podem substituir classes.

## 2. Linguagens e ferramentas

Detectar versões suportadas, toolchains, manifestos, lockfiles e comandos de CI
antes de escolher sintaxe ou ferramentas. Um manifesto pode conter um intervalo,
e um lockfile nem sempre fixa o runtime: confrontar pins, ambiente instalado e CI.
Não atualizar versões ou introduzir dependências apenas para seguir esta tabela.

| Ecossistema | Exemplos de ferramentas, conforme o projeto | Orientação |
| --- | --- | --- |
| Python | uv, Poetry ou pip/venv; Ruff, mypy/Pyright, pytest | Anotar contratos relevantes; usar context managers; evitar defaults mutáveis. Escolher dataclasses, modelos de validação ou tipos simples conforme a necessidade. |
| JavaScript / TypeScript | npm, pnpm ou Bun; Node.js, Bun ou Deno; ESLint/Biome, tsc, Vitest, Playwright | Respeitar runtime e lockfile. Preferir tipagem estrita e unknown para dados desconhecidos. Exceções para any devem ser localizadas e justificadas, sem impor migração geral. |
| Go | go mod, go build, go vet, go test; golangci-lint e govulncheck quando adotados | Tratar e contextualizar erros; propagar context.Context em operações canceláveis; manter interfaces pequenas no consumidor. Usar race detector quando suportado e relevante. |
| Rust | rustup, Cargo, rustfmt, Clippy, cargo test; audit/deny quando adotados | Propagar erros recuperáveis; usar ownership e referências com clareza. unwrap/expect exigem invariantes justificáveis; crates de erro são opcionais. |
| Java | Maven/Gradle e wrappers; JUnit, Checkstyle, SpotBugs, Error Prone, Testcontainers, ArchUnit | Usar records e pattern matching quando a versão permitir. Virtual threads atendem certas cargas bloqueantes; medir e respeitar limites de recursos externos. |
| C# / .NET | dotnet, NuGet, MSBuild; Roslyn analyzers, xUnit/NUnit | Respeitar SDK e frameworks-alvo; usar async/await, cancelamento e descarte de recursos adequadamente. AOT depende de compatibilidade e objetivo. |

Esses ecossistemas são a cobertura documental inicial. Outras linguagens devem
seguir o mesmo processo de inspeção, documentação oficial e validação local.
Nem linguagem nem ferramenta, isoladamente, garantem segurança ou desempenho.

## 3. Consulta de documentação e compatibilidade

Proposta de consulta sob demanda, sem presumir infraestrutura RAG disponível:

1. Inspecionar versões declaradas, resolvidas e instaladas, convenções e contratos.
2. Consultar fontes externas quando houver API desconhecida, incerteza de
   compatibilidade, depreciação relevante ou atualização solicitada. Não comparar
   numericamente uma versão de pacote com a data de treinamento do modelo.
3. Preferir documentação oficial da versão-alvo, tipos instalados, changelogs e
   guias de migração. MCP é um meio opcional de acesso, não garantia de autoridade.
4. Usar registries oficiais para metadados e versões; verificar compatibilidade
   e política de suporte. “Latest” e “estável” variam por ecossistema; não assumir
   que um endpoint resolve seleção de versão ou auditoria de vulnerabilidades.
5. Registrar fonte, versão/tag ou revisão, data da consulta e conclusão relevante.
   Exemplos da branch main podem não corresponder à versão instalada.
6. Implementar contra a versão suportada pelo projeto. Migrar apenas no escopo
   autorizado; uma API depreciada pode precisar permanecer por compatibilidade.
7. Executar checks relevantes e investigar falhas. Repetir consultas ou comandos
   somente quando uma nova hipótese ou mudança justificar a tentativa.

Sem rede ou documentação suficiente, relatar a limitação e aproveitar evidências
locais. Não inventar assinaturas, resultados ou uma versão “atual”. Não instalar
integrações nem escrever memória persistente automaticamente. Qualquer registro
durável deve respeitar o escopo autorizado e excluir segredos e dados sensíveis.

## 4. Segurança, desempenho e recursos

- Identificar limites de confiança, autenticação e autorização. Validar entradas
  externas conforme o contrato, inclusive dados vindos de persistência e serviços.
- Avaliar injeção, XSS, SSRF, desserialização, path traversal e controle de acesso
  quando aplicáveis. Parametrizar valores SQL e validar identificadores dinâmicos.
- Preferir execução de processos com argumentos separados e sem shell. Para
  caminhos, usar APIs apropriadas e verificar contenção no diretório autorizado;
  normalizar caminhos, isoladamente, não elimina riscos de symlinks ou corridas.
- Não expor credenciais ou dados pessoais em código, logs e erros. Preservar TLS,
  assinaturas e verificações de integridade. Usar APIs criptográficas apropriadas;
  senhas exigem algoritmos próprios para armazenamento de senhas.
- Definir deadlines, cancelamento, limites de payload e de recursos conforme a
  operação. Retentativas só para falhas transitórias e operações seguras ou
  idempotentes, com orçamento limitado, backoff e jitter quando adequado.
- Estimar custos de tempo e memória no caminho relevante e medir gargalos antes
  de otimizações complexas. Hash maps não garantem O(1) em qualquer cenário;
  escolher estruturas conforme ordenação, volume, memória e dados adversariais.
- Investigar N+1, bloqueios, alocações e coleções sem limites. Aplicar paginação,
  streaming, batching ou concorrência limitada quando houver benefício comprovado.
- Liberar conexões, arquivos e outros recursos inclusive em falhas e cancelamento.
  Não ocultar exceções; tratar, contextualizar ou propagar preservando sua causa.

## 5. Evidência e evolução

Definir critérios de aceite antes de mudanças relevantes. Selecionar build,
análise estática e testes existentes conforme o risco e o comportamento alterado.
Acrescentar regressões significativas para bugs e comportamentos novos; mudanças
documentais simples não exigem uma suíte de aplicação artificial.

Compilação, lint e typecheck não provam correção funcional, segurança ou desempenho.
Checks variam por linguagem: go vet, por exemplo, não substitui go build/go test.
Verificar que os testes pretendidos realmente executaram e distinguir aprovação,
falha, skip e ausência de execução. Medições precisam de cenário e baseline.

Evoluir a base por contribuições revisáveis: problema, proposta, compatibilidade,
fontes e evidências. Não declarar suporte a todas as linguagens nem código pronto
para produção sem validação suficiente para o contexto.
