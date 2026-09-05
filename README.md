# Hierarchical Context Tree Engine

> **Domain:** Autonomous Agent Systems & Context State Architecture
> **Reference Guidelines & Standards:** `Distributed Systems RFC & State Machine Verification`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Hierarchical Context Tree Engine** is an advanced analytical and computational platform implementing Tree-structured recursive summarization & L1/L2/L3 memory pyramid engine (10M+ tokens).

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.
- **Tree Pruning Strategies**: Pluggable depth, relevance, age, and size-based pruning.
- **Subtree Caching**: LRU cache with TTL for resolved subtrees.
- **Tree Diff Visualization**: Structural diffs between tree snapshots with ASCII rendering.

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/hierarchical-context-tree-engine.git
cd hierarchical-context-tree-engine

# Install dependencies
pip install -e .

# Or install with web server support
pip install fastapi uvicorn pydantic pytest
```

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required: HMAC-SHA256 audit trail signing key (minimum 16 characters)
export AUDIT_SECRET_KEY="your-secure-random-key-here"

# Optional: LLM provider (mock, ollama, claude, openai)
export MODEL_PROVIDER=mock
```

See `.env.example` for all available options.

---

## 💻 CLI Quickstart & Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Interactive Chat
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task identifier (required, max 256 chars)
- `--target`: Target entity identifier (required, max 256 chars)
- `--primary`: Primary metric value (float, finite number)
- `--secondary`: Secondary metric value (float, finite number)
- `--critical`: Flag for critical priority (boolean)
- `--status`: Status descriptor (max 128 chars)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Parameter / observation metric | Required |
| `target_identifier` | Parameter / observation metric | Required |
| `primary_metric` | Parameter / observation metric | Required |
| `secondary_metric` | Parameter / observation metric | Optional |
| `is_critical_flag` | Parameter / observation metric | Optional |
| `status_descriptor` | Parameter / observation metric | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Input Validation:** Bounds checking, path traversal prevention, and NaN/Inf rejection on all metrics.
* **Secure Defaults:** Audit signing key must be provided via environment variable (no hardcoded secrets).
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

### Test Coverage

- **PHI Guard Enforcement:** Validates detection of SSNs, MRNs, phone numbers, emails
- **Audit Trail Integrity:** Verifies HMAC-SHA256 chain integrity
- **Input Validation:** Tests bounds checking, path traversal prevention
- **Tree Pruning:** Validates depth, relevance, age, and size pruning strategies
- **Subtree Cache:** Tests LRU eviction, TTL expiration, metrics
- **CLI Commands:** End-to-end CLI functionality

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t hierarchical-context-tree-engine .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" hierarchical-context-tree-engine

# Or use Docker Compose
cp .env.example .env
# Edit .env with your AUDIT_SECRET_KEY
docker-compose up -d
```

---

## 📁 Project Structure

```
hierarchical-context-tree-engine/
├── agents/                  # Core agent system
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Master orchestrator
│   ├── workers.py          # Specialized evaluation workers
│   ├── llm_factory.py      # LLM provider factory
│   ├── metrics.py          # Prometheus metrics
│   ├── learning.py         # Bayesian calibration engine
│   └── streamer.py         # WebSocket telemetry
├── context_tree/           # Tree engine modules
│   ├── engine.py           # Core algorithmic engine
│   ├── agents.py           # Tree coordination agents
│   ├── pruning.py          # Tree pruning strategies
│   ├── subtree_cache.py    # LRU subtree cache
│   ├── tree_diff.py        # Tree diff visualization
│   ├── server.py           # FastAPI server factory
│   └── cli.py              # Tree CLI interface
├── tests/                  # Test suite
├── web/                    # Web interface
├── cli.py                  # Main CLI entry point
├── simulator.py            # Batch simulation
├── enrichment.py           # Enrichment features
├── pyproject.toml          # Project configuration
├── Dockerfile              # Container build
└── docker-compose.yml      # Container orchestration
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
