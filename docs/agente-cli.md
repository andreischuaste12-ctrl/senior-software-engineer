# Agente de IA no terminal — 0.3.0

Requer Python 3.11+ em Windows, Linux ou macOS, sem dependências de runtime externas.
A skill acompanha o wheel: tanto `pip install .` quanto `pip install -e .` são
suportados. O comando instalado é `sse-agent`; também funciona `python -m sse_agent`.
Não há pacote publicado no PyPI por esta alteração.

## Windows (PowerShell)

Na pasta do projeto, confirme Python e rode os testes sem modelo ou credenciais:

```powershell
py -3 --version
py -3 -m sse_agent --help
py -3 -m unittest discover -s tests -v
py -3 -m pip install .
sse-agent --version
```

Se `py` não existir, confira a instalação do Python Launcher ou use `python`
depois de verificar sua versão. Não precisa de WSL, Bash, venv ativado ou mudança
na ExecutionPolicy. Use aspas em caminhos com espaços.

## Modelo local por padrão

Inicie separadamente um servidor local compatível com Chat Completions e function
calling. O agente não baixa nem inicia um modelo. Confirme os requisitos de
hardware e se o servidor realmente funciona offline, sem telemetria ou forwarding.

- `SSE_BASE_URL`: padrão `http://127.0.0.1:1234/v1`.
- `SSE_MODEL`: ID exato do modelo disponível no servidor; obrigatório.
- `SSE_API_KEY`: opcional para servidores locais que exigem autenticação.

```powershell
$env:SSE_MODEL = "ID_DO_MODELO_LOCAL"
py -3 -m sse_agent --workspace "C:\Projetos\Meu Projeto" --deny "private/**" --allow-file "**/*.py" "Revise o código autorizado"
```

Chamadas de loopback ignoram proxies do ambiente e não seguem redirecionamentos.
Isso limita o cliente, não impõe isolamento de rede ao servidor local ou aos checks.
Para confidencialidade estrita, use isolamento do sistema operacional e servidor
local confiável. Não há garantia de risco zero.

## API externa exige autorização explícita

Uma URL externa é recusada antes de qualquer requisição, salvo com `--allow-remote`.
Quando optar por ela, configure `SSE_BASE_URL` com a base HTTPS do provedor,
`SSE_MODEL` e a credencial por variável de ambiente ou mecanismo seguro.
`OPENAI_API_KEY` é alternativa a `SSE_API_KEY`. O CLI não carrega arquivos `.env`.
Nunca grave a chave no Git, no histórico do shell ou em argumentos da CLI.

Com o opt-in, tarefa, instruções, arquivos lidos e resultados de checks podem ser
transmitidos ao provedor e gerar cobrança. Reveja seus dados e condições antes
de habilitar o envio. Filtros de arquivos não removem segredos de todo conteúdo.

## Acesso aos arquivos

- `--deny GLOB` é repetível e exclui arquivos ou diretórios de todas as ferramentas
  de arquivo, incluindo acesso direto, edição, listagem e busca.
- `--allow-file GLOB` é repetível. Quando presente, somente arquivos que casam com
  algum padrão são acessíveis; bloqueios embutidos e `--deny` continuam prevalecendo.
- Padrões usam `/` ou `\`; `**` casa zero ou mais diretórios. Um padrão sem `/`
  casa nomes de arquivo em qualquer nível. Os filtros de acesso ignoram caixa
  para manter proteção consistente entre Windows e POSIX.
- Configurações conhecidas como wp-config.php, .npmrc, .netrc, .git-credentials,
  .pypirc, .htpasswd, secrets.yaml/yml, *.env, *.tfstate, *.tfvars, *.jks e chaves
  conhecidas são bloqueadas, assim como .git/.aws/.ssh/.kube/.gnupg/.docker.
- Templates .env.example/.sample/.template podem ser lidos; confirme que não contêm
  credenciais. Nomes desconhecidos e segredos embutidos em código não são detectados
  universalmente. Prefira uma lista pequena de arquivos explicitamente autorizados.
- Dependências/caches vendor, node_modules, .next, coverage, venv e similares são
  omitidos e bloqueados. build/dist/target são omitidos na raiz, mas código aninhado
  com esses nomes continua acessível.
- Links simbólicos, junctions/reparse points, caminhos fora da raiz, streams NTFS
  e nomes reservados de dispositivos são recusados. Um diretório redirecionado deve
  ser selecionado diretamente como raiz ou substituído por um checkout comum.

Essas regras não controlam o código executado por checks nem detectam hardlinks ou
corridas maliciosas no filesystem. Trabalhe sem modificações concorrentes.

## Ferramentas

| Ferramenta | Contrato |
| --- | --- |
| list_files | `pattern` e `directory` opcionais; até 1000 resultados e 10000 arquivos varridos por busca, com truncamento explícito. Caminhos são relativos à raiz do workspace. |
| search_text | Busca literal por `query`, `pattern`, `directory`, `ignore_case`; até 200 resultados, com trechos próximos da ocorrência. |
| read_file | UTF-8 até 64000 bytes por resposta; arquivos de até 2 MB com `start_line`/`end_line`; SHA-256 do arquivo inteiro. |
| replace_in_file | `--allow-write`; trecho único ou `replace_all`, hash obrigatório, preservação de CRLF e verificação de tamanho antes de expandir. |
| write_file | `--allow-write`; cria em diretório existente ou substitui com hash válido; não exclui arquivos. |
| run_check | Executa apenas um comando nomeado pelo operador; retorna exit code, timeout e começo/final da saída. |

`directory` inicia a enumeração nessa subpasta, evitando gastar o teto em outras
árvores. Padrões são relativos ao workspace, mesmo com uma raiz de busca menor.
Não há descoberta garantida de todo um monorepo em uma única chamada.

Uma rodada pode executar até oito ferramentas. Chamadas excedentes recebem erro
pareado com seu ID e podem ser solicitadas depois. Toda a rodada é validada antes
de executar efeitos. Há teto absoluto de 128 chamadas na resposta para impedir
rodadas abusivas. Ferramentas executam sequencialmente; não há paralelismo real.

## Checks e limites

```powershell
py -3 -m sse_agent --workspace "C:\Projetos\Meu Projeto" --allow-write --check "tests=py -3 -m unittest discover -s tests -v" "Corrija o bug e valide"
```

Linux/macOS: substitua `py -3` por `python` e use o caminho local do projeto.
`--check` segue parsing nativo do Windows ou shlex no POSIX, sem shell livre.
`--check-json` recebe `NOME=ARRAY_JSON` para invocações programáticas. Prefira
executáveis, não wrappers .cmd/.bat, para controlar interpretação de argumentos.

Checks executam código com suas permissões e podem escrever arquivos mesmo sem
`--allow-write`. Não são sandbox. Recebem ambiente mínimo; `--check-env NOME`
autoriza variáveis adicionais, mas as duas chaves de API nunca são repassadas.
Isso não impede que um processo leia credenciais do disco ou acesse a rede.
Use container/VM e limites externos para executar projetos não confiáveis.

Timeout usa grupo POSIX ou taskkill /T /F no Windows. O teste não garante contenção
de processos hostis que se desanexem. A saída retornada tem até cerca de 16000 bytes,
mas não há cota de disco imposta ao log temporário. Checks Python recebem UTF-8.

Padrões: 12 rodadas, 120 s por chamada de API, 60 s por check, payload de 250000
bytes e resposta HTTP de até 2000000 bytes. Resultados antigos podem ser compactados;
o pedido, instruções e rodada mais recente são preservados. Falta de contexto
interrompe a tarefa com erro. Não há limite monetário implementado.

Retries ficam desligados. `--api-retries N` (0–3) autoriza tentativas extras para
429/5xx, com backoff ou Retry-After numérico limitado a 30 s. Nenhuma dessas
respostas garante ausência de processamento/cobrança anterior. Conexão e timeout
não são repetidos automaticamente. O CLI de avaliações segue a mesma regra.

Saída final vai para stdout; progresso/erro para stderr. Erros retornam 1;
interrupção retorna 130. Alterações anteriores não são desfeitas se a tarefa falhar.
Revise o diff e a evidência de checks; texto final do modelo não comprova sucesso.

## Validação e releases

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m pip install ruff==0.17.4 mypy==2.4.1
py -3 -m ruff check .
py -3 -m mypy --strict
py -3 scripts/verify_wheel.py
```

O CI executa Windows, Ubuntu e macOS com Python 3.11 e 3.14, inclusive instalação
não editável fora do checkout. Junction só roda no Windows; symlink pode exigir
privilégios locais. O teste HTTP usa loopback numérico sem DNS reverso.
Aprovação de testes não garante ausência de vulnerabilidades ou eficácia geral.
Consulte [releases](releases.md) e [changelog](../CHANGELOG.md).

```powershell
py -3 -m sse_agent.evals list
py -3 -m sse_agent.evals run E05 --json
```

Evals usa o servidor/modelo configurado; também exige `--allow-remote` para APIs
externas. São fixtures sintéticos de E01/E03/E05/E10 e critérios determinísticos.
Os testes do harness usam clientes roteirizados e não medem eficácia de um modelo
real. Sem servidor/modelo configurado, essa avaliação permanece não executada.
Não há RAG, pesquisa web, memória persistente, download de modelos ou deploy.
