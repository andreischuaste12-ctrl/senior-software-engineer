# Release process

The repository does not publish packages automatically. A release candidate must:

1. Use an intentional semantic version in `sse_agent.__version__` and update the changelog.
2. Run unit tests, Ruff, strict mypy, and `scripts/verify_wheel.py`.
3. Pass the GitHub Actions matrix on Windows, Ubuntu, and macOS for all configured
   Python versions.
4. Inspect wheel contents, metadata, bundled skill resources, LICENSE, and NOTICE.
5. Confirm that no credentials, local build artifacts, or unrelated changes are present.
6. Record real-model evaluation separately; scripted tests must not be presented as
   evidence of model effectiveness.

Publishing to PyPI, creating a GitHub release, signing artifacts, or changing
deployment systems requires explicit authorization and credentials supplied through
a secure mechanism.
