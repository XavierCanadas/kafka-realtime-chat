from typing import Union
import json
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from confluent_kafka import Producer, Consumer, KafkaException
from threading import Thread
import logging


class CreateRuleRequest(BaseModel):
    """Additional attributes documentation.

    Attributes:
        operator: AD2Q7 - must be > or <
        cooldown_seconds: AD2Q8 - Do not trigger the alarm until cooldown_seconds
            passes since the last trigger
        window_duration_seconds: AD2Q9 - trigger the alarm only if the average of
            metrics in the window time is above/below the threshold.
            There's no need of a type attribute. If the window is 0, is
            instantaneous if not we compute the average
        tags: AD2Q6 - is dict with key the tag name and value a list of
            the tags values that allow the rule.
    """

    metric_name: str
    threshold: int
    operator: str = ">"
    cooldown_seconds: int = 0
    window_duration_seconds: int = 0
    tags: dict = {}
    discord_webhook_url: str


# uuid.uuid4() to make the id
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOPIC = "rules"

PRODUCER_CONFIG = {
    "bootstrap.servers": "kafka-1:9092",
    "client.id": "kafka-producer-rules",
}

CONSUMER_CONFIG = {
    "bootstrap.servers": "kafka-1:9092",
    "group.id": str(uuid.uuid4()),
    "auto.offset.reset": "earliest",  # rules are read all
}

producer = Producer(PRODUCER_CONFIG)
consumer = Consumer(CONSUMER_CONFIG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    # The documentation recomends calling producer.flush() before shutdown
    global running
    running = False
    producer.flush()


app = FastAPI()

# consumer rules
rules_materialized_view = {}
running = True


def rule_consume(consumer):
    try:
        consumer.subscribe(["rules"])
        logger.info("Consumer subscribed to 'rules' topic")

        while running:
            msg = consumer.poll(timeout=1.0)

            if msg == None:
                continue

            # the documentation says that a consume function should hadle msg.error()
            if msg.error():
                raise KafkaException(msg.error())

            rule_id = msg.key().decode("utf-8")  # bytes to string

            logger.info(f"Received rule: {rule_id}")

            # process the rule
            if msg.value() == None:
                logger.info(f"Deleting rule: {rule_id}")
                del rules_materialized_view[rule_id]

            else:
                new_rule = json.loads(msg.value())
                logger.info(
                    f"Adding or updating rule new rule: rule_id = {rule_id}, value = {new_rule}"
                )
                rules_materialized_view[rule_id] = new_rule

            logger.info(f"Current rules count: {len(rules_materialized_view)}")

    except Exception as e:
        logger.error(f"Error in consumer: {str(e)}")

    finally:
        consumer.close()
        logger.info("Consumer closed")


thread = Thread(target=rule_consume, args=(consumer,), daemon=True)
thread.start()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/rules")
def create_rule(request: CreateRuleRequest):
    rule_id = uuid.uuid4()

    if request.operator not in [">", "<"]:
        raise HTTPException(
            status_code=400, detail="Operator must be either '>' or '<'"
        )

    if request.cooldown_seconds < 0:
        raise HTTPException(status_code=400, detail="Cooldown seconds must be positive")

    if request.window_duration_seconds < 0:
        raise HTTPException(status_code=400, detail="window duration must be positive")
    
    if "general" in request.tags:
        raise HTTPException(status_code=400, detail="'General' cound not be used as a tag.")

    value = {
        "id": str(rule_id),
        "metric_name": request.metric_name,
        "threshold": request.threshold,
        "operator": request.operator,
        "cooldown_seconds": request.cooldown_seconds,
        "window_duration_seconds": request.window_duration_seconds,
        "tags": request.tags,
        "discord_webhook_url": request.discord_webhook_url,
    }

    producer.produce(TOPIC, key=str(rule_id), value=json.dumps(value))

    producer.poll(1)

    return value


@app.put("/rules/{rule_id}")
def update_rule(rule_id: str, request: CreateRuleRequest):
    # the consumer in alarm manage the update of the rule

    if request.operator not in [">", "<"]:
        raise HTTPException(
            status_code=400, detail="Operator must be either '>' or '<'"
        )

    if request.cooldown_seconds < 0:
        raise HTTPException(status_code=400, detail="Cooldown seconds must be positive")

    if request.window_duration_seconds < 0:
        raise HTTPException(status_code=400, detail="window duration must be positive")

    value = {
        "id": rule_id,
        "metric_name": request.metric_name,
        "threshold": request.threshold,
        "operator": request.operator,
        "cooldown_seconds": request.cooldown_seconds,
        "window_duration_seconds": request.window_duration_seconds,
        "tags": request.tags,
        "discord_webhook_url": request.discord_webhook_url,
    }

    producer.produce(TOPIC, key=rule_id, value=json.dumps(value))

    producer.poll(1)

    return value


@app.get("/rules/{rule_id}")
def get_rule(rule_id: str):
    if rule_id not in rules_materialized_view:
        raise HTTPException(
            status_code=404, detail=f"Rule with id = {rule_id} not found"
        )
    return rules_materialized_view.get(rule_id)


@app.get("/rules/")
def get_all_rule():
    return list(rules_materialized_view.values())


@app.delete("/rules/{rule_id}")
def delete_rule(rule_id: str):
    producer.produce(TOPIC, key=rule_id, value=None)
    producer.poll(1)


"""
Test command:

------------------------------------------------------------------

- Original command:
curl -X POST http://localhost:5001/rules -H 'Content-Type: application/json' -d '{
    "metric_name": "packages-received-original",
    "threshold": 500,
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq

curl -X DELETE http://localhost:5001/rules/86c77e3e-c160-4ac5-86e3-6c8c29ec4c59 | jq

------------------------------------------------------------------

- AD2Q1 - update a rule
curl -X PUT http://localhost:5001/rules/5a9bc1cb-2a48-463a-9ce7-40d66ae33074 -H 'Content-Type: application/json' -d '{
    "metric_name": "packages-received",
    "threshold": 600,
    "operator": ">",
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq

------------------------------------------------------------------

- AD2Q2 - get the rules
curl -X GET http://localhost:5001/rules/5a9bc1cb-2a48-463a-9ce7-40d66ae33074 | jq
curl -X GET http://localhost:5001/rules/ | jq

------------------------------------------------------------------

- AD2Q7 - rule operator:
curl -X POST http://localhost:5001/rules -H 'Content-Type: application/json' -d '{
    "metric_name": "packages-received-2",
    "threshold": 490,
    "operator": "<",
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq


------------------------------------------------------------------

- AD2Q8 - cooldown support:
curl -X POST http://localhost:5001/rules -H 'Content-Type: application/json' -d '{
    "metric_name": "packages-received-3",
    "threshold": 490,
    "operator": ">",
    "cooldown_seconds": 10,
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq

------------------------------------------------------------------

- AD2Q9 - window average:
curl -X POST http://localhost:5001/rules -H 'Content-Type: application/json' -d '{
    "metric_name": "packages-received-4",
    "threshold": 495,
    "operator": ">",
    "cooldown_seconds": 0,
    "window_duration_seconds": 3,
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq

------------------------------------------------------------------

- AD2Q6 - tagging support:
General rule
curl -X PUT http://localhost:5001/rules/abd74af3-fe58-4e29-bc38-4040682712c1 -H 'Content-Type: application/json' -d '{
    "metric_name": "conveyorbelt",
    "threshold": 495,
    "operator": ">",
    "cooldown_seconds": 0,
    "window_duration_seconds": 0,
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq

Specific 1
curl -X POST http://localhost:5001/rules -H 'Content-Type: application/json' -d '{
    "metric_name": "conveyorbelt",
    "threshold": 494,
    "operator": ">",
    "cooldown_seconds": 0,
    "window_duration_seconds": 3,
    "tags": {"machine_id": [12354, 12355]},
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq

Specific 2
curl -X POST http://localhost:5001/rules -H 'Content-Type: application/json' -d '{
    "metric_name": "conveyorbelt",
    "threshold": 495,
    "operator": ">",
    "cooldown_seconds": 0,
    "window_duration_seconds": 3,
    "tags": {"machine_id": [12356]},
    "discord_webhook_url": "https://discord.com/api/webhooks/1345043184140685465/5zB-RWlAarIhMiqF_-S4kF2pt4e8b2-InJonoGHlzAv4qBhpuZXpf6eAYwe-DvVyOOlJ"
}' | jq

"""
