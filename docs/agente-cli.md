# Agente de IA no terminal

Implementação em Python 3.11+ para Windows, Linux e macOS, usando apenas a biblioteca
padrão. O CLI carrega a skill e suas referências revisadas, conversa com uma API
Chat Completions com function calling e executa um loop limitado de ferramentas.
Use o checkout completo; ainda não há distribuição via pip ou executável global.

## Configuração

No diretório raiz do projeto, execute `py -3 -m sse_agent --help` no Windows
ou `python -m sse_agent --help` em Linux/macOS.
Configure no ambiente do processo, sem registrar valores no Git:

- `SSE_API_KEY`: credencial do provedor; `OPENAI_API_KEY` é alternativa.
- `SSE_MODEL`: ID de um modelo que suporte Chat Completions e function calling.
- `SSE_BASE_URL`: base da API, padrão `https://api.openai.com/v1`. Um provedor
  compatível pode ter requisitos diferentes; confira sua documentação.

O CLI não carrega `.env`. Não passe a credencial por argumento de terminal.
HTTPS é obrigatório para provedores externos; HTTP é aceito somente para loopback
no desenvolvimento. Redirecionamentos são recusados para não encaminhar credenciais.
O uso da API pode gerar cobrança conforme o provedor. O código e os resultados de
ferramentas lidos durante a tarefa serão enviados ao endpoint configurado.

## Uso

### Windows (PowerShell)

Instale Python 3.11 ou superior pelo instalador oficial com o Python Launcher
(`py`). Abra o PowerShell na pasta do checkout completo e confira:

```powershell
py -3 --version
py -3 -m sse_agent --help
py -3 -m unittest discover -s tests -v
```

Esses comandos não exigem chave nem acesso ao provedor. Se `py` não existir,
use `python` depois de confirmar `python --version`; verifique a instalação e os
aliases de execução do Windows caso o comando abra a Microsoft Store.
Não é necessário WSL, Bash, ativar venv ou alterar a ExecutionPolicy do PowerShell.

Configure a chave nas variáveis de ambiente do processo por um mecanismo seguro
e defina `SSE_MODEL` com o ID do provedor. Isso não instala um modelo local.
Então execute:

```powershell
py -3 -m sse_agent --workspace "C:\Projetos\Meu Projeto" "Analise a arquitetura"
py -3 -m sse_agent --workspace "C:\Projetos\Meu Projeto" --allow-write --check "tests=py -3 -m unittest discover -s tests -v" "Corrija o bug e valide com tests"
```

Use aspas em caminhos com espaços. `--check` usa interpretação nativa de
argumentos no Windows, sem shell Unix. Prefira executáveis como `py.exe`,
`python.exe` e `dotnet.exe` aos wrappers `.cmd`/`.bat` para controlar a interpretação.

### Linux/macOS

Somente leitura por padrão:

```bash
python -m sse_agent --workspace /caminho/do/projeto "Analise a arquitetura e priorize problemas concretos"
```

Autorizar escrita e disponibilizar um check específico:

```bash
python -m sse_agent --workspace /caminho/do/projeto --allow-write \
  --check 'tests=python -m unittest discover -s tests -v' \
  "Corrija o bug descrito, preserve os contratos e valide com tests"
```

Adapte o check ao projeto; ele será executado no workspace. Cada `--check`
registra um nome único e um comando dividido em argumentos sem shell. Pipes,
redirecionamento e expansão de variáveis não são interpretados. O modelo escolhe
apenas um nome registrado, sem acrescentar argumentos. Checks podem executar código
do projeto e escrever arquivos mesmo sem `--allow-write`; só autorize comandos e
repositórios em que confia. As duas variáveis de chave da API acima são removidas
do ambiente dos checks; outras variáveis do processo continuam disponíveis.

Em todas as plataformas, `--check-json` também aceita `NOME=ARRAY_JSON`, onde o
array contém executável e argumentos como strings, sem reinterpretar seus caminhos.
É útil para invocações programáticas; a passagem de aspas pelo terminal varia
entre versões do PowerShell, portanto prefira `--check` nos exemplos simples.

## Ferramentas e limites

| Ferramenta | Capacidade |
| --- | --- |
| list_files | Lista até 1000 arquivos e sinaliza truncamento; exclui diretórios comuns de dependências, Git, links simbólicos e nomes sensíveis conhecidos. |
| read_file | Lê UTF-8 até 64000 bytes e retorna SHA-256. |
| write_file | Disponível com --allow-write; cria texto em diretório existente ou substitui arquivo previamente lido usando seu hash. Não exclui arquivos. |
| run_check | Disponível apenas quando o operador registra checks; devolve exit code, timeout e até 16000 bytes de saída. |

O padrão é 12 rodadas (`--max-steps`) e 60 segundos por chamada/check (`--timeout`).
Há limites de 8 chamadas de ferramenta por rodada, 250000 bytes no payload e
2000000 bytes na resposta HTTP. São limites locais, não estimativas de tokens ou
controle de gastos. Não há retry automático de chamadas pagas. A saída final vai
para stdout e o progresso para stderr. Falha operacional retorna código 1;
interrupção pelo usuário retorna 130. Uma resposta final do modelo não comprova
que os testes passaram: confira as evidências apresentadas e o diff.

Operações já realizadas não são desfeitas se ocorrer falha posterior. Revise o
estado do Git antes e depois de cada execução. Trabalhe em um checkout sem
modificações concorrentes: a conferência de hash reduz sobrescritas obsoletas,
mas não fornece transações nem isolamento contra corridas no filesystem.

No Windows, ferramentas de arquivo rejeitam junctions/reparse points, caminhos
de drive/UNC, streams alternativos NTFS e nomes de dispositivos reservados.
Pastas redirecionadas por esses recursos precisam ser selecionadas diretamente
como workspace ou substituídas por um checkout comum. Caminhos relativos com
barras normais ou invertidas são aceitos.

Checks Python recebem saída UTF-8; outros executáveis precisam emitir UTF-8
para preservar acentos no relatório. Timeout/interrupção encerra o grupo em POSIX
e usa `taskkill /T /F` no Windows, com fallback para o processo principal.
Isso não isola processos maliciosos que tentem escapar ou se desanexar.
Aplicativos que bloqueiem arquivos abertos podem impedir substituições no Windows;
nesse caso a ferramenta retorna o erro.

## Fronteiras desta versão

Não há sandbox de sistema operacional: checks executam processos com as permissões
do usuário. Para projetos não confiáveis, use container/VM isolado sem credenciais
e com limites externos de rede, CPU, disco e memória. O filtro de nomes de arquivos
é preventivo e não detecta todos os segredos; não aponte o agente para conteúdo
confidencial que não possa ser enviado ao provedor. A proteção contra instruções
maliciosas também depende do modelo; não foi demonstrada por testes de eficácia.

Não há shell livre, criação de diretórios por ferramenta, exclusão, Git push,
deploy, pesquisa web, MCP, cache, RAG, agendamento ou memória persistente. A skill
não foi treinada em um modelo próprio: orienta um modelo acessado por API.

## Validação local

```bash
python -m unittest discover -s tests -v
```

Os testes exercitam leitura/escrita, limites de caminho e conteúdo, hash obsoleto,
check com falha/timeout, erros da API e uma execução real do CLI contra um servidor
HTTP simulado local, com chamadas de ferramentas e alteração de arquivo temporário.
Esse teste confirma integração e protocolo; não avalia raciocínio de um LLM.
Para eficácia, execute os cenários comportamentais da skill com um modelo real.

O GitHub Actions executa a suíte em Windows, Ubuntu e macOS com Python 3.11 e
3.14 após push/PR ou acionamento manual. O teste de junction roda somente no
Windows. O teste de symlink pode ser ignorado se o Windows não conceder o
privilégio necessário; isso será indicado no resultado da suíte.
Sem execução nativa de Windows, a validação nessa plataforma permanece pendente.
