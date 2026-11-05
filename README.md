# senior-software-engineer

Projeto para desenvolver um agente de engenharia de software capaz de construir,
analisar, otimizar e refatorar código em diferentes linguagens de programação.
A eficácia deverá ser demonstrada por validações específicas para cada tarefa,
como testes relevantes, compilação, análise estática e medições de desempenho
quando aplicáveis.

## Estado atual

O projeto contém um agente CLI em Python, uma skill própria em formato `SKILL.md`
e bases de conhecimento revisadas. O agente usa uma API de IA com ferramentas
locais controladas pelo operador. A eficácia por linguagem permanece a validar
com modelos reais; testes de integração simulados não demonstram essa eficácia.

## Executar o agente

Requer Python 3.11+ em Linux/macOS, chave de API e modelo com function calling.
Não exige pacotes externos. Configure `SSE_API_KEY` (ou `OPENAI_API_KEY`) e
`SSE_MODEL` no ambiente; nunca grave credenciais no repositório.

```bash
python -m sse_agent --workspace /caminho/do/projeto "Analise este projeto e proponha melhorias"
```

Por padrão, as ferramentas de arquivo são somente leitura. Consulte o
[guia do CLI](docs/agente-cli.md) para habilitar escrita, definir checks, selecionar
o provedor e entender os limites de execução e de envio de código à API.

Para executar os testes locais, sem credenciais ou chamadas a um modelo real:

```bash
python -m unittest discover -s tests -v
```

## Usar a skill

A skill [senior-software-engineer](skills/senior-software-engineer/SKILL.md) orienta
correção de bugs, funcionalidades, refatoração, análise de arquitetura e performance.
O pacote é autocontido em `skills/senior-software-engineer/`, com referências por
ecossistema e cenários de avaliação.

Em um host compatível com skills `SKILL.md`, copie essa pasta inteira para o
diretório de skills indicado pelo host e siga seu mecanismo de ativação. O nome
da skill é `senior-software-engineer`; caminhos de instalação e invocação variam
entre hosts. A instalação não foi executada neste repositório.

Exemplo de solicitação ao host com a skill carregada: “Use a skill
senior-software-engineer para corrigir este bug, respeitando as versões do projeto
e demonstrando a correção com testes relevantes.”

Consulte os [cenários de avaliação](skills/senior-software-engineer/evals/scenarios.md)
antes de declarar eficácia. A skill não instala compiladores, MCPs ou serviços,
não treina o modelo e não garante suporte universal.

## Base de conhecimento

A [base fundacional de engenharia](docs/base-fundacional.md) reúne princípios de
design, critérios para padrões de projeto, orientações por linguagem e um fluxo
de consulta e validação de APIs. Ela foi revisada a partir do texto fornecido
pelo proponente do projeto.

A [proposta de instruções operacionais](docs/instrucoes-operacionais.md) traduz
essa base em um roteiro usado para elaborar a primeira skill. Ambos são documentos de referência;
não ativam um agente, integrações externas ou atualização automática de memória.
A cobertura inicial inclui Python, JavaScript/TypeScript, Go, Rust, Java e C#/.NET,
sem representar suporte implementado ou eficácia comprovada nessas linguagens.

A [base complementar](docs/conhecimento-complementar.md) registra o novo material
fornecido pelo usuário, sua versão original e a síntese revisada usada pela skill.
As afirmações de versões e verificações do original não foram certificadas pelo projeto.

## Referências e contribuições

Este é um projeto de código aberto, e todas as pessoas são bem-vindas para
contribuir, independentemente do nível de experiência. Você pode propor ideias,
relatar problemas, melhorar a documentação e enviar melhorias por pull requests.
Consulte as [diretrizes de contribuição](CONTRIBUTING.md) para começar.

Referências externas serão estudadas para compreender conceitos e métodos e
orientar conteúdo original. Nesta etapa, nenhuma skill de terceiros será
instalada ou incorporada. Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para as
diretrizes e o registro da referência de arquitetura pendente de análise.

## Licença

O conteúdo original deste projeto que seus titulares puderem licenciar é
disponibilizado sob a [Apache License 2.0](LICENSE) (`Apache-2.0`). Essa licença
não altera os direitos ou as licenças de materiais externos citados.
