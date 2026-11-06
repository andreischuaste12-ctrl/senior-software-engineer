# Processo de release

1. Atualizar `sse_agent/__init__.py` e `CHANGELOG.md` com o comportamento final.
2. Rodar unittest, Ruff e Mypy estrito conforme a configuração do CI.
3. Executar `python scripts/verify_wheel.py`: construir e instalar wheel num venv
   descartável, carregar os recursos fora do checkout, listar avaliações sem API.
4. Exigir CI aprovado em Windows, Ubuntu e macOS, incluindo o teste do wheel.
5. Revisar permissões, documentação, changelog e diff; verificar autoria dos
   commits antes da integração. Checks verdes não certificam privacidade integral.
6. Publicar tags, releases ou artefatos em registry somente quando solicitado.
   Um push para main não significa publicação de pacote no PyPI.

Métricas de cobertura devem registrar comando, versão da ferramenta, revisão,
plataforma, source/omit e se subprocessos foram incluídos. Não há limiar universal
que prove eficácia. Avaliações com modelo real exigem servidor/modelo configurado
e fixtures sintéticos; APIs externas exigem opt-in e podem gerar cobrança.
