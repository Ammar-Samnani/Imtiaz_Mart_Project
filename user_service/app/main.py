from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Session, Field, create_engine, select
from typing import AsyncGenerator, Annotated
from contextlib import asynccontextmanager
from models.user_models import User, User_Update
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
    create_db_and_tables()
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


@app.get("/users/")
def read_all_users(session: Annotated[Session, Depends(get_session)]):
        users = session.exec(select(User)).all()
        return users


@app.post("/create_user")
def create_user(user: User, session: Annotated[Session, Depends(get_session)]):
    try:
        res = requests.get(url="http://172.22.208.1:8005/access_token", params={"user_name": user.full_name}) ##Update IP if run on different system
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    else:
        # user.update(res)
        response = res.json()
        session.add(user)
        session.commit()
        session.refresh(user)
        return {
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "number": user.number,
                "address": user.address
            },
            "access token": response["access token"]
        }
    # finally:
    #     session.add(user)
    #     session.commit()
    #     session.refresh(user)
    #     return {
    #         "user": {
    #             "id": user.id,
    #             "Full Name": user.full_name,
    #             "email": user.email,
    #             "number": user.number,
    #             "address": user.address
    #         }
    #     }

@app.patch("/user_update/{user_id}")
def update_user_by_id(user_id: int, to_update_user_data: User_Update, session: Annotated[Session, Depends(get_session)]):
    # Step 1: Get the user by ID
    user = session.exec(select(User).where(User.id == user_id)).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Step 2: Update the user
    hero_data = to_update_user_data.model_dump(exclude_unset=True)
    user.sqlmodel_update(hero_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.delete("/delete_user_by_name/{user_name}")
def Delete_User_by_Name(user_name: str, session: Annotated[Session, Depends(get_session)]):
    # Step 1: Get the Product by ID
    user = session.exec(select(User).where(User.full_name == user_name)).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"message": "User Deleted Successfully"}


@app.delete("/delete_user_by_id/{user_id}")
def delete_user_by_id(user_id: int, session: Annotated[Session, Depends(get_session)]):

    # Step 1: Get the User by ID
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Step 2: Delete the User
    session.delete(user)
    session.commit()
    
    # Step 3: Return a success message
    return {"message": "User Deleted Successfully"}