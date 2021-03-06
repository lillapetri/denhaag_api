from datetime import datetime, timedelta
from time import time

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from Models.user import UserOut
from Utils.constants import JWT_ALGORITHM, JWT_EXPIRATION_TIME_MINUTES, JWT_SECRET_KEY
from Utils.db_functions import check_user, check_username

pwd_context = CryptContext(schemes=['bcrypt'])
oauth_schema = OAuth2PasswordBearer(tokenUrl='/token')


def get_hashed_password(password):
    return pwd_context.hash(password)


# Authenticate and give JWT token
async def authenticate(user):
    is_valid = await check_user(user)
    if is_valid:
        return user
    return None


# Create access JWT token
def create_jwt_token(user: UserOut):
    expiration = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_TIME_MINUTES)
    jwt_payload = {"sub": user.username, "exp": expiration, "role": user.role}
    jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM).decode('utf-8')
    return {"access_token": "Bearer " + jwt_token}


# Check whether JWT token is correct
async def check_jwt_token(token: str = Depends(oauth_schema)):
    try:
        jwt_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
        username = jwt_payload.get('sub')
        expiration = jwt_payload.get('exp')
        role = jwt_payload.get('role')
        if time() < expiration:
            is_valid = await check_username(username)
            if is_valid:
                return final_checks(role)
    except Exception as e:
        return False
    return False


# Last authorization checking and returning the final result
def final_checks(role: str):
    try:
        if role.lower() == 'admin':
            return True
    except Exception as e:
        return False
    return False
