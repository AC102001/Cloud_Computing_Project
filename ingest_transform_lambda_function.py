import json, os, time, datetime, gzip, uuid, boto3

s3 = boto3.client("s3")
BUCKET = os.environ["RAW_BUCKET"]

# Global cold-start flag and CW client
COLD = True
CWM = boto3.client("cloudwatch")

def lambda_handler(event, context):
    global COLD
    t0 = time.time()
    try:
        body = event.get("body") if isinstance(event, dict) else None
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8")
        payload = json.loads(body or "{}")

        if "user_id" not in payload or "action" not in payload:
            raise ValueError("Required fields: user_id, action")

        now = datetime.datetime.utcnow()
        payload["_ingest_ts"] = now.isoformat() + "Z"
        payload["_request_id"] = str(uuid.uuid4())

        key = f"raw/year={now:%Y}/month={now:%m}/day={now:%d}/{payload['_request_id']}.json.gz"
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=gzip.compress(json.dumps(payload).encode("utf-8"))
        )

        latency_ms = int((time.time() - t0) * 1000)

        print(json.dumps({
            "metric": "ingest_success",
            "latency_ms": latency_ms,
            "cold_start": COLD,
            "request_id": payload["_request_id"],
            "container": context.log_stream_name
        }))

        if COLD:
            try:
                CWM.put_metric_data(
                    Namespace="ServerlessETL",
                    MetricData=[{
                        "MetricName": "ColdStart",
                        "Value": 1,
                        "Unit": "Count",
                        "Dimensions": [{"Name": "Function", "Value": context.function_name}]
                    }]
                )
            finally:
                COLD = False

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "latency_ms": latency_ms})
        }

    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        print(json.dumps({
            "metric": "ingest_error",
            "error": str(e),
            "latency_ms": latency_ms,
            "cold_start": COLD,
            "container": getattr(context, "log_stream_name", "unknown")
        }))
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": str(e)})
        }
