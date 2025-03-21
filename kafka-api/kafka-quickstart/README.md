# kafka samples

This folder contains Python code samples for common Kafka usecases:
- [consumer.py](./consumer.py): consuming JSON records from a topic
- [producer.py](./producer.py): producing JSON records to a topic
- [materialized_view.py](./materialized_view.py): creating a materialized view from JSON records from a topic

## Installing the samples

```
cd resources/kafka-samples
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the samples

First, start a local Kafka system if you don't have one already.

```zsh
docker compose up
```

Then, run the producer script in one shell:

```zsh
source venv/bin/activate
python3 producer.py
```

Then, run the consumer script in another shell:

```zsh
source venv/bin/activate
python3 consumer.py
```

Then, run the materializer script in another shell:

```zsh
source venv/bin/activate
python3 materialized_view.py
```
