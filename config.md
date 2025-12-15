# Configuration Used (Final)

## AWS Region
- `us-east-1` (N. Virginia)

## API Gateway
- Base URL: `https://yliq855ne6.execute-api.us-east-1.amazonaws.com`
- Route: `POST /ingest`
- Full endpoint: `https://yliq855ne6.execute-api.us-east-1.amazonaws.com/ingest`

## Lambda Functions
- Ingest Lambda: `ingest-transform`
- Controller Lambda: `etl-controller-lambda`

## EventBridge (Controller Trigger)
- Rule name: `etl-controller-every-2m`
- Schedule: every 2 minutes
- Target: `etl-controller-lambda`

## Controller Lambda Environment Variables
(As configured in AWS Console → Lambda → `etl-controller-lambda` → Configuration → Environment variables)

- `TARGET_FUNCTION=ingest-transform`
- `MIN_CONCURRENCY=1`
- `MAX_CONCURRENCY=50`
- `STEP=2`
- `COOLDOWN_MIN=5`

### Latency Target
Project originally used `P95_TARGET_MS`, but experiments may use p99 on CloudWatch widgets depending on availability.

- `P95_TARGET_MS=30`

If you decide to align strictly with p99 in code/config, rename consistently:
- `P99_TARGET_MS=<value>` and update controller logic accordingly.

## CloudWatch
### Log Groups
- `/aws/lambda/ingest-transform`
- `/aws/lambda/etl-controller-lambda`

### Dashboard
- `serverless-controller-dashboard`
Widgets:
- Duration (p99)
- ColdStart count
- ConcurrentExecutions
- ControllerAction
- Log Insights widget showing `ingest_success` events
