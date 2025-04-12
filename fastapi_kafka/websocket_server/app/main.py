from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from confluent_kafka import Producer, Consumer, KafkaError
import json
import logging

# set up the loggin in docker
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)