# Cloud Computing Project: Adaptive Concurrency Controller on AWS Lambda

This project implements a simple serverless “data plane + control plane” system:
- **Data plane:** `ingest-transform` Lambda behind API Gateway that ingests JSON events and emits structured logs/metrics.
- **Control plane:** `etl-controller-lambda` Lambda (triggered by EventBridge on a schedule) that reads recent latency/cold start signals and (attempts to) adjust reserved concurrency for `ingest-transform`.

> Note: In our AWS account, attempts to increase reserved concurrency may hit AWS quota/constraints. This is expected and documented in Results.

---

## Architecture (High-Level)

Traffic Generator (curl loop)  
→ API Gateway `POST /ingest`  
→ Lambda `ingest-transform`  
→ CloudWatch Metrics + Structured Logs  
→ EventBridge (every 2 min)  
→ Lambda `etl-controller-lambda`  
→ (attempt) Update Reserved Concurrency of `ingest-transform`  
→ observed via Dashboard Widgets

---

## Repo Files

- `ingest_transform_lambda_function.py`  
  Lambda code for the ingest endpoint. Writes structured logs like:
  - `metric=ingest_success`
  - `latency_ms`
  - `cold_start`
- `etl_controller_lambda_function.py`  
  Controller Lambda code. Periodically evaluates recent performance and decides: `scale_up`, `scale_down`, or `hold`.
- `load_generator_tester.py`  
  Helper / local test script (optional use depending on workflow).
- `requirements.txt`  
  Minimal Python dependencies.
- `config.md`  
  Configuration used (environment variables and key AWS resources).
- `experiments.md`  
  Exact steps to reproduce baseline vs controller runs and capture figures.

---

## AWS Resources Used

**Region:** us-east-1 (N. Virginia)

### Lambda Functions
- `ingest-transform`
- `etl-controller-lambda`

### API Gateway
- API base URL: `https://yliq855ne6.execute-api.us-east-1.amazonaws.com`
- Ingest route: `POST /ingest`

Full endpoint:
https://yliq855ne6.execute-api.us-east-1.amazonaws.com/ingest

