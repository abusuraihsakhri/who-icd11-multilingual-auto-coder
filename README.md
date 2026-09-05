# WHO ICD-11 Multilingual Auto Coder

> **Domain:** Clinical & Biomedical AI / Medical Informatics
> **Standards:** WHO ICD-11 MMS Specification, CAP Synoptic Protocols

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

WHO ICD-11 Multilingual Auto Coder is an enterprise-grade distributed component platform for clinical and biomedical AI. It evaluates task payloads through a multi-worker consensus engine, classifies urgency, and maintains a tamper-evident HMAC-SHA256 audit trail. The system enforces zero-PHI outbound interception to comply with HIPAA Safe Harbor de-identification requirements.

---

## Key Capabilities

- **Multi-Worker Consensus Engine:** Three specialized workers (Invariant QC, Safety Escalation, Protocol Conformance) evaluate each task independently and aggregate into a consensus dossier.
- **Zero-PHI Outbound Guard:** Regex and pattern-based inspection blocks SSNs, MRNs, phone numbers, emails, and patient identifiers from leaving the system.
- **HMAC-SHA256 Tamper-Evident Audit Trail:** Cryptographically chained audit log with signature verification for every evaluation and state transition.
- **FastAPI REST API:** OpenAPI 3.1 endpoints for audit, chat, and metrics.
- **Prometheus Metrics:** Operational telemetry export.
- **CLI & Batch Processing:** Command-line interface supporting single evaluations and bulk CSV processing.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/who-icd11-multilingual-auto-coder.git
cd who-icd11-multilingual-auto-coder

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Optional: Set audit secret key for persistent audit integrity
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

---

## Usage

### CLI Commands

#### 1. Single Task Evaluation (Audit)
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

#### 2. Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

#### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

#### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health check and system metadata |
| GET | `/metrics` | Prometheus operational metrics |
| POST | `/api/audit` | Submit task payload for evaluation |
| POST | `/api/chat` | Air-gapped supervisory chat query |
| GET | `/api/audit/logs` | Retrieve and verify HMAC audit trail |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-2026-8801",
    "target_identifier": "TARGET-PQC-BIO-01",
    "primary_metric": 32.4,
    "secondary_metric": 18.2,
    "status_descriptor": "DISCORDANT_ANOMALY",
    "is_critical_flag": true
  }'
```

### Input Data Schema

| Field | Type | Description | Requirement |
|:------|:-----|:------------|:------------|
| `task_id` | string (max 128 chars) | Unique task/case identifier | Required |
| `target_identifier` | string (max 128 chars) | Entity or target key | Required |
| `primary_metric` | float | Primary measurement or score | Required |
| `secondary_metric` | float | Secondary score (default 0.0) | Optional |
| `status_descriptor` | string (max 64 chars) | Status code (default "NOMINAL") | Optional |
| `is_critical_flag` | boolean | Emergency escalation flag (default false) | Optional |

---

## Testing

```bash
# Run the full test suite
pytest -v

# Run with simulation benchmark
python simulator.py 1000
```

---

## Security Features

- **Zero-PHI Outbound Interceptor:** Blocks MRNs, SSNs, phone numbers, emails, DOBs, and patient names.
- **HMAC-SHA256 Audit Trail:** Every state transition is cryptographically signed and chained. Use `verify-audit` command or `/api/audit/logs` endpoint to verify integrity.
- **Path Traversal Protection:** Batch file I/O is restricted to the working directory.
- **Input Validation:** String fields are bounded to prevent abuse.
- **Audit Secret Key:** Configure via `AUDIT_SECRET_KEY` environment variable. If not set, an ephemeral key is generated (with a warning) for the session.

---

## Docker Deployment

```bash
docker build -t who-icd11-multilingual-auto-coder .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key who-icd11-multilingual-auto-coder
```

Or using docker-compose:

```bash
docker-compose up -d
```

---

## Project Structure

```
who-icd11-multilingual-auto-coder/
├── agents/                  # Core distributed component engine
│   ├── __init__.py
│   ├── api.py               # FastAPI REST server
│   ├── base.py              # Security, PHI guard, HMAC audit
│   ├── models.py            # Pydantic data models
│   ├── supervisor.py        # Master orchestrator
│   ├── workers.py           # Specialized evaluation workers
│   ├── llm_factory.py       # LLM provider adapter
│   ├── metrics.py           # Prometheus metrics collector
│   ├── learning.py          # Bayesian calibration engine
│   └── streamer.py          # WebSocket telemetry broadcaster
├── icd11_coder/             # Legacy ICD-11 coder module
├── tests/                   # Pytest test suite
├── cli.py                   # Primary CLI entry point
├── simulator.py             # Load testing simulator
├── enrichment.py            # Threshold-based enrichment engines
├── pyproject.toml           # Project metadata
├── Dockerfile               # Container build spec
└── docker-compose.yml       # Container orchestration
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
