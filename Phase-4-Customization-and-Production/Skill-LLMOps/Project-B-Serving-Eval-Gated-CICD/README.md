# Project B — Serving + Eval-Gated CI/CD

**Phase:** 4 — Customization & Production · **Skill:** LLMOps · **Difficulty:** Intermediate

## Overview
Serve a model behind a REST API, containerize it, deploy to Kubernetes (minikube) via
GitHub Actions, and **block deploys when evals fail** (canary/rollback).

## Links to roadmap.sh/ai-engineer
- Deployment / Production Architecture
- Reuses the eval gate from the Evals skill

## Concepts covered
Model serving (FastAPI + vLLM/Ollama), containerization, Kubernetes, CI/CD,
evaluation gate, canary deploy + rollback.

## Prerequisites
- Evals Project B (eval gate) recommended first
- FastAPI, Docker, vLLM or Ollama, minikube, `kubectl`, GitHub Actions

## Learning objectives
- Serve a model behind a production-style API
- Deploy to Kubernetes via CI/CD
- Gate releases on evaluation results with rollback

## Suggested build steps
1. Wrap the model in a FastAPI service (`/generate`, `/health`).
2. Containerize with a multi-stage Dockerfile.
3. Add a GitHub Actions pipeline: lint + tests + **eval gate**.
4. Deploy to minikube; add readiness/liveness probes.
5. Implement a canary release with automatic rollback on failed eval/alarm.

## Reference material
- sarthxk20/llmops-platform: https://github.com/sarthxk20/llmops-platform
- Theepankumargandhi/Terraform-Based-LLMOps-Platform: https://github.com/Theepankumargandhi/Terraform-Based-LLMOps-Platform-for-Evaluation-Gated-Canary-Deployment

## Definition of done
- A failing eval blocks the deploy; a healthy build reaches the cluster.
- Canary + rollback works end-to-end.
