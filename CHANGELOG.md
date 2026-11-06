# Changelog

## 0.3.0

- Endpoint local por padrão e APIs externas bloqueadas sem `--allow-remote`.
- Filtros `--deny` e `--allow-file`, bloqueios adicionais de configurações sensíveis.
- Busca/listagem por `directory`, globstar com zero ou mais diretórios e exclusão
  de vendor, .next e coverage.
- Resposta pareada para ferramentas excedentes sem executar mais de oito na rodada.
- Normalização dos caminhos equivalentes no avaliador E05.
- Recursos da skill incluídos no wheel, com smoke test fora do checkout.
- Teste HTTP sem DNS reverso, validadores compartilhados e tipagem estrita.
- Actions atualizadas sobre o histórico atual, sem mesclar branches antigas.

Mudança de compatibilidade: quem usa provedor externo precisa configurar
`SSE_BASE_URL`, `SSE_MODEL`, a chave e passar `--allow-remote` explicitamente.

## 0.2.0

- Busca textual, leitura por linhas, edição pontual e preservação de CRLF.
- Harness de avaliações, compactação de contexto e instalação editável.
- Limite antecipado de expansão UTF-8 e retentativas opt-in.
