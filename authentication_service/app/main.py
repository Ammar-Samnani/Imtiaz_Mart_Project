# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from app import settings
from sqlmodel import Field, Session, SQLModel, create_engine, select, Sequence
from fastapi import FastAPI, Depends
from typing import AsyncGenerator
# from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from datetime import timedelta
from app.utils import create_access_token, decode_access_token
from jose import JWTError
from fastapi.security import OAuth2PasswordRequestForm

# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
# connection_string = str(settings.DATABASE_URL).replace(
#     "postgresql", "postgresql+psycopg"
# )


# recycle connections after 5 minutes
# to correspond with the compute scale down
# engine = create_engine(
#     connection_string, connect_args={}, pool_recycle=300
# )


# async def consume_messages(topic, bootstrap_servers):
#     # Create a consumer instance.
#     consumer = AIOKafkaConsumer(
#         topic,
#         bootstrap_servers=bootstrap_servers,
#         group_id="product-service-messages"
#         # auto_offset_reset="earliest",
#     )

#     # Start the consumer.
#     await consumer.start()
#     try:
#         # Continuously listen for messages.
#         async for message in consumer:
#             print("RAW")
#             print(f"Received message on topic {message.topic}")

#             product_data = json.loads(message.value.decode())
#             print("TYPE", (type(product_data)))
#             print(f"Product Data {product_data}")

#     finally:
#         # Ensure to close the consumer when done.
#         await consumer.stop()


# def create_db_and_tables()->None:
#     SQLModel.metadata.create_all(engine)



# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
# loop = asyncio.get_event_loop()
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables..")
    # loop.run_until_complete(consume_messages('todos', 'broker:19092'))
    # task = asyncio.create_task(consume_messages('product-events', 'broker:19092'))
    # create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8005", # ADD NGROK URL Here Before Creating GPT Action
            "description": "Development Server"
        }
        ])


# def get_session():
#     with Session(engine) as session:
#         yield session



# # Kafka Producer as a dependency
# async def get_kafka_producer():
#     producer = AIOKafkaProducer(bootstrap_servers='broker:19092')
#     await producer.start()
#     try:
#         yield producer
#     finally:
#         await producer.stop()


# @app.post("/login")
# def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)]):
#     """UNCOMPETED"""

@app.get("/access_token")
def get_access_token(user_name: str):
    access_token_expire = timedelta(days=1)
    access_token = create_access_token(user_name, access_token_expire)

    return {"access token": access_token}


@app.get("/decode_token")
def decoding_token(access_token: str):
    try:
        decoded_token_data = decode_access_token(access_token)
        return {"decoded_token": decoded_token_data}
    except JWTError as e:
        return {"error": str(e)}