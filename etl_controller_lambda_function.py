import os, boto3
from datetime import datetime, timedelta, timezone

CW = boto3.client("cloudwatch")
LAM = boto3.client("lambda")

FUNCTION_NAME = os.getenv("TARGET_FUNCTION", "ingest-transform")
P95_TARGET_MS = int(os.getenv("P95_TARGET_MS", "200"))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "50"))
MIN_CONCURRENCY = int(os.getenv("MIN_CONCURRENCY", "1"))
STEP = int(os.getenv("STEP", "2"))

def now_utc():
    return datetime.now(timezone.utc)

def get_p95_latency_ms(window_min=5):
    end = now_utc()
    start = end - timedelta(minutes=window_min)
    q = [{
        "Id": "p95",
        "MetricStat": {
            "Metric": {
                "Namespace": "AWS/Lambda",
                "MetricName": "Duration",
                "Dimensions": [{"Name": "FunctionName", "Value": FUNCTION_NAME}]
            },
            "Period": 60,
            "Stat": "p95"
        },
        "ReturnData": True
    }]
    resp = CW.get_metric_data(MetricDataQueries=q, StartTime=start, EndTime=end, ScanBy="TimestampAscending")
    vals = resp["MetricDataResults"][0]["Values"]
    return int(vals[-1]) if vals else None

def get_cold_starts_sum(window_min=5):
    end = now_utc()
    start = end - timedelta(minutes=window_min)
    q = [{
        "Id": "cs",
        "MetricStat": {
            "Metric": {
                "Namespace": "ServerlessETL",
                "MetricName": "ColdStart",
                "Dimensions": [{"Name": "Function", "Value": FUNCTION_NAME}]
            },
            "Period": 60,
            "Stat": "Sum"
        },
        "ReturnData": True
    }]
    resp = CW.get_metric_data(MetricDataQueries=q, StartTime=start, EndTime=end, ScanBy="TimestampAscending")
    vals = resp["MetricDataResults"][0]["Values"]
    return int(sum(vals)) if vals else 0

def get_reserved_concurrency():
    try:
        cfg = LAM.get_function_concurrency(FunctionName=FUNCTION_NAME)
        return cfg.get("ReservedConcurrentExecutions", 0)
    except LAM.exceptions.ResourceNotFoundException:
        return 0

def set_reserved_concurrency(n):
    n = max(MIN_CONCURRENCY, min(MAX_CONCURRENCY, n))
    LAM.put_function_concurrency(FunctionName=FUNCTION_NAME, ReservedConcurrentExecutions=n)
    return n

def lambda_handler(event, context):
    p95 = get_p95_latency_ms(5)
    cold = get_cold_starts_sum(5)
    cur = get_reserved_concurrency()

    action, new = "hold", cur
    if p95 is None:
        detail = {"reason": "no p95 data"}
    else:
        if p95 > int(P95_TARGET_MS * 1.10) or cold >= 1:
            new = cur + STEP; action = "scale_up"
        elif p95 < int(P95_TARGET_MS * 0.80) and cur > MIN_CONCURRENCY:
            new = cur - STEP; action = "scale_down"
        detail = {"p95_ms": p95, "cold_5m": cold}

    if new != cur:
        new = set_reserved_concurrency(new)

    CW.put_metric_data(
        Namespace="ServerlessETL",
        MetricData=[{
            "MetricName":"ControllerAction",
            "Value": 1 if action != "hold" else 0,
            "Unit":"Count",
            "Dimensions":[{"Name":"Function","Value":FUNCTION_NAME}]
        }]
    )

    result = {"action": action, "before": cur, "after": new, **detail}
    print(result)
    return result