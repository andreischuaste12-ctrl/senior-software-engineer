# Conhecimento complementar revisado

Síntese do arquivo “base-conhecimento-engenharia-software.md” fornecido pelo
proponente em 5 de novembro de 2026. As etiquetas de verificação e as versões
do original não foram verificadas pelo projeto; não são fatos certificados.
Esta referência complementa a skill sem substituir a política do host.

## [S1] Conhecimento estável e volátil

Princípios de design são heurísticas relativamente estáveis; versões, suporte,
CVEs, deprecações e sintaxe nova exigem evidência específica da versão-alvo.
Não importar tabelas de “versão atual” para uma implementação sem conferir.
Uma proposta PEP/JEP/RFC aprovada não comprova entrega na versão instalada.
Políticas de suporte podem variar por distribuidor, especialmente no Java.

Ao citar um fato externo, distinguir observação própria, relato da fonte e
inferência. Registrar URL, versão/revisão, data da consulta e alcance da leitura.
HTTP 200 comprova acesso, não a veracidade ou atualidade de uma afirmação.
Agregadores como endoflife.date ajudam a descobrir informações; decisões críticas
devem confrontar a documentação do fornecedor pertinente.

## [S2] Catálogo adicional de padrões

Além do catálogo básico, considerar Prototype para cópia de objetos com semântica
clara de estado compartilhado; Bridge para eixos independentes de variação;
Composite para árvores; Flyweight para estado compartilhado imutável com benefício
medido; Iterator para percurso, preferindo recursos nativos.

Mediator pode centralizar comunicação, mas também concentrar responsabilidades.
Memento exige definir o que um snapshot captura e como restaurar recursos externos.
Template Method depende de herança; Strategy pode facilitar composição. Visitor
favorece novas operações em estruturas estáveis, com custo quando os tipos mudam.
Interpreter só é adequado a gramáticas pequenas; parsers dedicados podem ser mais
apropriados. Nenhum desses padrões é um requisito para código de qualidade.

## [S3] Arquitetura, confiabilidade e testes

Portas/adaptadores e camadas podem proteger domínio e fronteiras de mudança,
sem exigir uma arquitetura inteira para uma tarefa pequena. Twelve-Factor é uma
referência para certos serviços, não regra universal para CLI, embarcados ou desktop.

Escolher o equilíbrio entre testes unitários, integração, contrato e E2E conforme
os riscos. Uma pirâmide não impõe contagens fixas. Para serviços, definir SLI/SLO
e orçamento de erro quando isso ajudar decisões operacionais. Relacionar medições
a cenários reais e, se pertinente, custo ou resultado do negócio.

Consultar OWASP ASVS/Top 10, NIST SSDF e SLSA conforme a superfície de risco.
Verificar edição e requisitos aplicáveis antes de declarar conformidade; uma
checklist preenchida não equivale a certificação ou auditoria completa.

## [S4] Atualização futura de conhecimento

Cache com fonte, revisão/hash, data e expiração pode reduzir consultas; TTL depende
do risco. Não transformar sugestões como 6h ou 7d em garantias de segurança.
Datas de publicação antigas não invalidam documentação da versão instalada.
Quando execução e documentação divergirem, investigar configuração, flags,
plataforma e versão; um teste isolado não substitui a especificação.

Registro de fontes, feeds, consulta a advisories, cache, cron e RAG são propostas
futuras. O CLI inicial não implementa essas integrações nem atualiza a base
silenciosamente. Mudanças de conhecimento devem gerar um diff revisável no escopo
autorizado, sem gravar dados sensíveis.
