# Interview Questions — LLMOps Project B: Serving + Eval-Gated CI/CD

Complete the project, then quiz yourself. Answers are detailed.

## Phase 4 — Customization & Production · LLMOps · Project B

**Q1. How do you serve a model in production?**
Wrap the model in a **FastAPI** service exposing endpoints like `POST /generate` and
`GET /health`. Behind it, run an inference engine (vLLM for throughput, or Ollama for
simplicity). vLLM adds continuous batching and paged attention for high concurrency.
The API should validate inputs, call the model, and return structured output — a
production-shaped interface, not a notebook.

**Q2. Why containerize, and what makes a good Dockerfile here?**
Containerization (multi-stage Dockerfile) packages the app + deps into a portable,
reproducible image that runs identically locally and in K8s. Multi-stage builds keep the
final image small (build deps excluded). You pin dependencies and the model artifact so
deployments are consistent and rollback-able.

**Q3. What are readiness and liveness probes, and why do they matter in Kubernetes?**
- **Liveness probe**: "is the container alive?" — if it fails, K8s restarts the pod
  (recovers from hangs).
- **Readiness probe**: "is it ready to serve traffic?" — gates whether the pod receives
  requests (e.g. wait until the model is loaded). Prevents routing traffic to a pod
  that's still warming up. They're how K8s keeps the service healthy automatically.

**Q4. What is a canary deploy and automatic rollback, and how do evals gate it?**
A **canary** ships a new version to a small subset of traffic first. You watch metrics/
**evals**; if a regression or alarm fires, **rollback** automatically reverts to the
last good version. The **eval gate** (reusing Phase 3 Evals B) blocks the deploy
entirely if evals fail *before* rollout, and the canary+rollback handles post-deploy
issues. This is safe, incremental shipping instead of big-bang releases.

**Q5. How does the CI/CD pipeline combine lint + tests + eval gate?**
GitHub Actions on push: (1) **lint** (catch style/syntax), (2) **tests** (unit/integration),
(3) **eval gate** (run the eval suite; fail if metrics drop). Only if all pass does the
pipeline build the image and deploy to minikube. This is the same "treat evals as tests"
principle from Evals B, extended to the full release path.

**Q6. Why minikube for this learning project, and what's the real-world equivalent?**
Minikube gives you a single-node local Kubernetes to practice real deploy/rollback,
probes, and CI integration without cloud cost or accounts. In production you'd use a
managed cluster (EKS/GKE/AKS) with the same manifests — the learning transfers directly.
The point is practicing the *production architecture*, not the cloud vendor specifics.
