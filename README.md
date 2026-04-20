# 🤖 AI Automation Pipeline – LLM-powered Content Processing

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Dockerfile](https://img.shields.io/badge/Dockerfile-available-blue?logo=docker)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Dernier commit](https://img.shields.io/github/last-commit/arnaudstdr/resume_news)

## Overview
This project is a **production-ready AI automation pipeline** designed to process, normalize and summarize large volumes of content using LLMs.

Originally built for AI news monitoring, it is designed as a **reusable automation pattern** that can be adapted to many business use cases:
- content aggregation
- reporting
- monitoring
- internal knowledge digests
- automated analysis workflows

> **Goal:** turn unstructured inputs into structured, usable outputs with minimal manual intervention.

## Problem
Teams often deal with:
- large volumes of unstructured content
- repetitive analysis and summarization tasks
- manual reporting that does not scale

Most AI projects stop at the POC stage and fail to:
- integrate into real workflows
- run reliably
- produce consistent outputs

## Solution
This pipeline implements a **robust, end-to-end automation flow**:

1. **Ingestion**
   - RSS scraping (configurable sources)
2. **Normalization**
   - Local summarization using `sshleifer/distilbart-cnn-12-6`
   - Structured storage in SQLite
3. **High-level synthesis**
   - Weekly digest generation using Ollama (model `gemma4:31b-cloud`)
4. **Outputs**
   - Structured Markdown reports
   - HTML + PDF report sent by email
   - Persisted, queryable data
5. **Execution**
   - Single-command execution
   - Fully containerized
   - Scheduled weekly via cron (e.g. Raspberry Pi)

The result is a **reliable AI-driven workflow**, not an experiment.

## Architecture
```text
RSS feeds
   ↓
Scraper
   ↓
Local summarization (Transformers)
   ↓
SQLite storage
   ↓
LLM-based synthesis (Ollama / gemma4:31b-cloud)
   ↓
Structured outputs (Markdown)
```

Key design choices:
- Local models for high-frequency tasks
- API-based LLM only where high-level reasoning is needed
- Clear separation of steps
- Deterministic, repeatable execution

## Why this matters
This project demonstrates how to:
- integrate LLMs into real pipelines
- combine local models and external APIs efficiently
- build AI automation that can run unattended
- produce outputs that teams can actually use

It reflects a **production-oriented approach**:
- no UI-first design
- no over-engineering
- focus on reliability and maintainability

## Reusability & adaptation
This pipeline can be adapted for:
- business intelligence monitoring
- competitive analysis
- customer feedback analysis
- internal reporting
- document or knowledge processing

Only the input sources and summarization logic need to change.

## Tech stack
- Python
- Transformers (local models)
- Ollama (LLM synthesis, model `gemma4:31b-cloud`)
- SQLite
- Docker
- Shell scripting for orchestration

## Prerequisites

The pipeline calls a local Ollama daemon. Before running it:

```bash
ollama signin            # required for -cloud models
ollama pull gemma4:31b-cloud
ollama serve             # if not already running
```

Then copy `.env.example` to `.env` and adjust `OLLAMA_URL` / `OLLAMA_MODEL` if needed.

## Run locally (Docker)

```bash
./docker-run.sh
```

This will:

- build the image if needed
- run the full pipeline (container reaches Ollama via `host.docker.internal`)
- persist outputs and database locally

## Email delivery

The pipeline sends the weekly digest as HTML + PDF by email via `web_viewer/send_mail.py`.

First run creates `config/email_config.ini`. Edit it with your SMTP credentials:

```ini
[EMAIL]
smtp_server = smtp.gmail.com
smtp_port = 587
email_user = you@gmail.com
email_password = app_password       # Gmail : create an app password
recipient_email = you@gmail.com

[ADVANCED]
use_tls = true
timeout = 30
max_attachment_size_mb = 25
```

Gmail app password: <https://support.google.com/accounts/answer/185833>.

The `config/` directory is mounted into the container, so edits on the host persist across runs.

## Weekly schedule on Raspberry Pi

Tested on Raspberry Pi 5 (8 GB, ARM64).

1. **Install Ollama on the Pi**

    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ollama signin
    ollama pull gemma4:31b-cloud
    ```

2. **Make Ollama reachable from the Docker container**

    ```bash
    sudo systemctl edit ollama
    ```

    Add:

    ```ini
    [Service]
    Environment="OLLAMA_HOST=0.0.0.0:11434"
    ```

    Then:

    ```bash
    sudo systemctl restart ollama
    ```

3. **Clone the repo and prepare config**

    ```bash
    git clone https://github.com/arnaudstdr/resume_news.git ~/resume_news
    cd ~/resume_news
    cp .env.example .env
    # first run to generate config/email_config.ini, then edit it
    ./docker-run.sh
    ```

4. **Schedule with cron — every Monday at 06:00**

    ```bash
    crontab -e
    ```

    Add:

    ```cron
    0 6 * * 1 cd /home/pi/resume_news && ./docker-run.sh >> /home/pi/resume_news/pipeline.log 2>&1
    ```

    Inspect logs anytime via `tail -f ~/resume_news/pipeline.log`.

## Author

Arnaud Stadler
Python Developer – AI Automation & Production Systems

## License

MIT – free to use, adapt and integrate.
