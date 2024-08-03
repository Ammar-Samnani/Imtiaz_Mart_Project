from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Session, Field, create_engine
from typing import AsyncGenerator, Annotated
from contextlib import asynccontextmanager
from models.user_models import User
from app import settings
import requests


connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)


engine = create_engine(
    connection_string, connect_args={}, pool_recycle=300
)

def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables..")
    # loop.run_until_complete(consume_messages('todos', 'broker:19092'))
    # task = asyncio.create_task(consume_messages(settings.KAFKA_PRODUCT_TOPIC, 'broker:19092'))
    # asyncio.create_task(consume_messages("todos", "broker:19092"))
    # create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8006", # ADD NGROK URL Here Before Creating GPT Action
            "description": "Development Server"
        }
        ])


@app.get("/")
def read_root():
    return {"Hello": "PanaCloud"}

@app.post("/create_user")
def create_user(user: User, session: Annotated[Session, Depends(get_session)]):
    try:
        res = requests.get(url="http://172.25.176.1:8005/access_token", params={"user_name": user.full_name})
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    else:
        # user.update(res)
        response = res.json()
        print(response)
        # return {
        #     "user": {
        #         "id": user.id,
        #         "Full Name": user.full_name,
        #         "email": user.email,
        #         "number": user.number,
        #         "address": user.address
        #     },
        #     "access token": response["access token"]
        # }
    finally:
        session.add(user)
        session.commit()
        session.refresh(user)
