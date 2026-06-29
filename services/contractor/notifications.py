import redis, json

r = redis.Redis(host="localhost", port=6379, db=0)

def enqueue_notification(payload: dict):
    r.lpush("notifications:queue", json.dumps(payload))
    return True

def pop_notification():
    item = r.rpop("notifications:queue")
    if not item:
        return None
    return json.loads(item)
