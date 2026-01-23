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
   - Weekly digest generation using an LLM API (Mistral Large)
4. **Outputs**
   - Structured Markdown reports
   - Persisted, queryable data
5. **Execution**
   - Single-command execution
   - Fully containerized

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
LLM-based synthesis (Mistral API)
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
- Mistral API (LLM synthesis)
- SQLite
- Docker
- Shell scripting for orchestration

## Run locally (Docker)
```bash
./docker-run.sh
```

This will:
- build the image if needed
- run the full pipeline
- persist outputs and database locally

## Author
Arnaud Stadler
Python Developer – AI Automation & Production Systems

## License
MIT – free to use, adapt and integrate.