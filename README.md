# WHO ICD-11 Multilingual Auto Coder

**Status: Experimental threshold-audit demonstrator. Not a clinical ICD-11 coder.**

Despite its name, the current repository does **not** retrieve WHO ICD-11 concepts, perform multilingual terminology matching, assign ICD-11 MMS codes, or validate post-coordination. The numeric thresholds are generic software examples, not clinical criteria. Do not use this project for patient care, clinical classification, or billing.

## Features actually implemented

- Three Python rule workers: primary metric > 25, secondary metric > 12 or a critical flag, and selected anomaly terms in a status descriptor. Critical alerts take priority over elevated alerts.
- A CLI for individual synthetic tasks and CSV batch evaluation, with input/output paths limited to the working directory.
- A FastAPI service exposing /health, /metrics (JSON counters), /api/audit, /api/chat, and /api/audit/logs.
- An **in-memory** HMAC-SHA256 chained audit log. It is tamper-evident while running, but entries are lost after restart; supplying the same key does not persist records.
- A standalone static browser preview at **web/index.html**. It reproduces the simplified threshold rules in JavaScript, exports JSON, and makes no API calls. It does not issue audit signatures.

The older icd11_coder/ module has a separate, compatible rule-evaluation CLI but likewise does not contain WHO terminology mapping. The enrichment.py helpers are also generic threshold calculators.

## Install and test

Python 3.9 or later. Create and activate a virtual environment, then:

~~~bash
git clone https://github.com/abusuraihsakhri/who-icd11-multilingual-auto-coder.git
cd who-icd11-multilingual-auto-coder
python -m pip install ".[server,test]"
python -m pytest -q
~~~

## Use the CLI

~~~bash
python cli.py audit --task-id DEMO-01 --target SYNTHETIC --primary 29 --secondary 13
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
~~~

The installed **who-icd11-audit** command uses this principal CLI. The installed **who-icd11-multilingual-auto-coder** command uses the legacy CLI. These are different evaluation paths, not interchangeable ICD-11 coders.

The API documentation is at http://127.0.0.1:8000/docs after starting the server. For the static preview, open web/index.html or use:

~~~bash
python -m http.server --directory web 8080
~~~

The preview is plain HTML, CSS, and JavaScript. It does not require Python in the browser, Pyodide, or backend infrastructure.

## Docker

Supply a **new random secret** through the environment before starting Compose:

~~~bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
~~~

The Compose configuration binds port 8000 to localhost only. To expose this API on a network, set AUDIT_API_KEY as well; /api/audit, /api/chat and /api/audit/logs then require an X-API-Key request header. Configure transport security, authorization, and durable logs separately if deploying outside an isolated development environment. Do not commit actual secret values.

## Privacy and scientific limitations

The pattern-based guard detects some obvious email addresses, telephone numbers, MRNs, and similar structured identifiers, but it is not a comprehensive PHI detector and does **not** establish HIPAA Safe Harbor de-identification. Never submit identifiable patient information. The mock supervisory model does not call remote LLM services; all provider choices currently return a deterministic mock.

The server retains evaluation results and the audit chain in memory. Identifiers appear in returned responses, and the browser preview retains only its current result and counters in page memory. No clinical classification accuracy, cross-language performance, or coding validation has been demonstrated.

## Development and deployment

Run the tests with **python -m pytest -q** and compile checks with **python -m compileall -q agents icd11_coder cli.py enrichment.py simulator.py**. GitHub Actions runs the suite on Python 3.10–3.13.

The browser preview supports current mainstream browsers with JavaScript enabled. The repository includes a GitHub Pages deployment workflow, but a live application link will be added only after verified publication.

## License

MIT. See [LICENSE](LICENSE).
