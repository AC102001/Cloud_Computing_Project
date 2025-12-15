# Experiments & Repro Steps

This document provides exact steps to reproduce:
1) Baseline run (controller OFF)
2) Controller-enabled run (controller ON)
3) Collecting metrics + logs for figures

---

## 0) Preconditions

- AWS region: `us-east-1`
- API endpoint exists and route `POST /ingest` is deployed.
- Lambda functions exist:
  - `ingest-transform`
  - `etl-controller-lambda`
- CloudWatch dashboard exists:
  - `serverless-controller-dashboard`

---

## 1) Verify Endpoint Works (single request)

```bash
URL="https://yliq855ne6.execute-api.us-east-1.amazonaws.com/ingest"
curl -s -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"sanity","action":"ping"}'
