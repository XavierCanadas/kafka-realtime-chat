#
#  database.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 15/4/2025
#  Copyright (c) 2025. All rights reserved.

import os
from typing import Annotated
from sqlmodel import create_engine, Session, SQLModel

from fastapi import Depends

from .models import User

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://root:password@relational_database:5432/chatdb"
)
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)