# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from app import settings
from sqlmodel import Field, Session, SQLModel, create_engine, select, Sequence
from fastapi import FastAPI, Depends, Body, HTTPException, Query
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json
from app.models.product_models import Product, Product_Update
from app import settings
import requests

# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)


# recycle connections after 5 minutes
# to correspond with the compute scale down
engine = create_engine(
    connection_string, connect_args={}, pool_recycle=300
)


def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)

async def consume_messages(topic, bootstrap_servers):
    # Create a consumer instance.
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="todos-messages"
        # auto_offset_reset='earliest'
    )

    # Start the consumer.
    await consumer.start()
    try:
        # Continuously listen for messages.
        async for message in consumer:
            print(f"Received message: {message.value.decode()} on topic {message.topic} in todos-messages group")
            # Here you can add code to process each message.
            # Example: parse the message, store it in a database, etc.
    finally:
        # Ensure to close the consumer when done.
        await consumer.stop()


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
# loop = asyncio.get_event_loop()
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables..")
    # loop.run_until_complete(consume_messages('todos', 'broker:19092'))
    task = asyncio.create_task(consume_messages(settings.KAFKA_PRODUCT_TOPIC, 'broker:19092'))
    asyncio.create_task(consume_messages("todos", "broker:19092"))
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8003", # ADD NGROK URL Here Before Creating GPT Action
            "description": "Development Server"
        }
        ])

def get_session():
    with Session(engine) as session:
        yield session


@app.get("/get_token")
def generate_token(user_name: str):
    try:
        res = requests.get(url="http://172.25.176.1:8005/access_token", params={"user_name": user_name})
        print(res.raise_for_status())
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return res.json()


@app.get("/")
def read_root():
    return {"Hello": "PanaCloud"}

# Kafka Producer as a dependency
async def get_kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers='broker:19092')
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()


@app.get("/products_by_name/", response_model=Product)
def read_products_by_name(session: Annotated[Session, Depends(get_session)], product_name: Annotated[str, Query(title="Product Name", description="Note: Case Sensitive.")]):
        products = session.exec(select(Product)).all()
        products_len = (len(products))-1
        while products_len >= 0:
            if products[products_len].name == product_name:
                return products[products_len]
            else:
                products_len -= 1
        else:
            raise HTTPException(status_code=404, detail="Product not found")


@app.get("/products_by_id/", response_model=Product)
def read_products_by_id(session: Annotated[Session, Depends(get_session)], id: int):
        products = session.exec(select(Product)).all()
        products_len = len(products)
        if id > products_len:
            return {"Error": "Out of range"}
        else:
            return products[id]


@app.get("/products/", response_model=list[Product])
def read_all_products(session: Annotated[Session, Depends(get_session)]):
        products = session.exec(select(Product)).all()
        return products


@app.post("/products/", response_model=Product)
async def create_product(product: Product, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)])->Product:
        product_dict = {field: getattr(product, field) for field in product.dict()}
        product_json = json.dumps(product_dict).encode("utf-8")
        print("productJSON:", product_json)
        # Produce message
        await producer.send_and_wait(settings.KAFKA_PRODUCT_TOPIC, product_json)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

@app.delete("/products/{product_id}", response_model=dict)
def delete_product_by_id(product_id: int, session: Annotated[Session, Depends(get_session)]):
    # Step 1: Get the Product by ID
    product = session.exec(select(Product).where(Product.id == product_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    # Step 2: Delete the Product
    session.delete(product)
    session.commit()
    return {"message": "Product Deleted Successfully"}
