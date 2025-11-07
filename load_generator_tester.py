import json, requests, threading, time, uuid, argparse

def hit(url):
    body = {"user_id": str(uuid.uuid4()), "action": "click"}
    requests.post(url, json=body, timeout=5)

def run(url, qps, duration):
    start = time.time()
    while time.time() - start < duration:
        threads = [threading.Thread(target=hit, args=(url,)) for _ in range(qps)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        time.sleep(1)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--qps", type=int, default=5)
    p.add_argument("--duration", type=int, default=60)
    args = p.parse_args()
    run(args.url, args.qps, args.duration)