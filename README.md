# Hierarchical Context Tree Engine

Python context-tree utilities and a deterministic multi-worker task evaluator, with a separate static browser demonstration.

## What is included

- **`context_tree/`**: standalone depth, relevance, age, and size pruning strategies; a TTL/LRU subtree cache; tree snapshots, structural diffs, and ASCII rendering; a legacy coordinator and CLI.
- **`agents/`**: Pydantic-validated task payloads, three threshold-based evaluation workers, a supervisor, an in-memory HMAC-SHA256 audit chain, a restricted audit-log endpoint, and a mock chat adapter.
- **`web/`**: browser-local threshold evaluation and JSON download. The repository-root `index.html` redirects to this interface when the root is published using GitHub Pages.

The worker thresholds in `agents/workers.py` are application defaults: primary metric **>25**, secondary metric **>12**, and keyword-based status flags. They are **not externally validated clinical thresholds**. The browser reproduces these rules but does not execute Python, run backend workers, or sign audit logs.

## Browser interface

Open `web/index.html` in a current desktop or mobile browser, or use the repository's GitHub Pages publication when available. Enter a task identifier, target, primary and secondary metrics, status descriptor, and optional critical flag; select **Evaluate locally**. The result can be downloaded as JSON.

All browser calculations run locally, with no API request, remote font, or upload. The interface is **not** a PHI de-identification service. Do not enter patient information. The output is labeled `LOCAL_UNSIGNED` and contains no fabricated cryptographic signature.

## Python installation

Requires Python 3.9 or later.

```sh
python -m pip install -e .
# Optional backend and test dependencies
python -m pip install -e ".[server,test]"
```

A signing key of at least 16 characters is required for server/CLI operations that write an audit entry:

```sh
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python cli.py audit --task-id TASK-001 --target KEY-001 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py serve --host 127.0.0.1 --port 8000
```

The installed `hierarchical-context-tree-engine` command calls the alternative `context_tree.cli` implementation; its evaluation criteria and output fields differ from the top-level `cli.py`. This distinction is preserved for compatibility.

## Local API

Install the `server` extra and start the backend with `python cli.py serve`, then use:

- `GET /health`: runtime health.
- `POST /api/audit`: Pydantic-validated evaluation and signed in-memory audit record.
- `POST /api/chat`: deterministic mock response; no external model invocation.
- `GET /api/audit/logs`: disabled unless `AUDIT_LOG_READ_KEY` is set, and then requires `X-Audit-Read-Key`.
- `GET /metrics`: basic in-memory counts returned as JSON, not Prometheus exposition format.

See `.env.example` for environment variables. Audit records and evaluator state are in memory only and disappear on process restart. Their HMAC checks detect modifications to stored audit metadata while the signing key and process state are intact. This repository does not provide durable audit storage, comprehensive PHI identification, regulatory certification, or production authentication for task submission.

## Development and testing

```sh
python -m pip install -e ".[server,test]"
python -m compileall -q agents context_tree cli.py enrichment.py simulator.py
python -m pytest -q
python simulator.py 100
```

GitHub Actions tests Python 3.10, 3.11, and 3.12. The browser regression test checks JavaScript syntax and the main local-evaluation workflow when Node.js is available.

For container use, set `AUDIT_SECRET_KEY`, then run `docker compose up --build`. The included Dockerfile exposes the FastAPI service on port 8000.

## Privacy and limitations

Browser input stays in the browser until explicitly exported; downloaded JSON contains the entered identifiers. The Python service holds recent dossiers and audit metadata in process memory. The signature key must remain server-side and must never be embedded in a public static page. Supported LLM provider names currently map to a mock client and are not real provider integrations.

The repository's tree utilities are Python modules; the static demonstration implements only the documented threshold evaluator, not the full tree engine. The project does not require Pyodide for the delivered browser functionality.

## License

MIT — see [LICENSE](LICENSE).
