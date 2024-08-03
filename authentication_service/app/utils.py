from datetime import datetime, timedelta
from jose import jwt


ALGORITHM = "HS256"
SECRET_KEY = "Imtiaz Mart Project Authentication"



def create_access_token(subject: str, expiry_time: timedelta)->str:
    expire = datetime.utcnow() + expiry_time
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(access_token: str):
    decoded_jwt = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    return decoded_jwt
