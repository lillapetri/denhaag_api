from datetime import datetime
from uuid import uuid4

from API.v1 import app_v1
from Models.user import UserIn
from Utils.db_functions import db_insert_user
from Utils.security import authenticate, check_jwt_token, create_jwt_token, get_hashed_password
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

app = FastAPI(title="What to do in the Hague?", description="Freetime activities collected in and around the Hague",
              version='1.0.0')
app.include_router(app_v1, prefix='/v1', dependencies=[Depends(check_jwt_token)])


# Test API route
@app.get('/test', tags=['Test connection'])
async def test_connection():
    return {'Connection established.'}


# Create admin
@app.post('/user', tags=['Create admin(s) who can manage database'], status_code=HTTP_201_CREATED)
async def new_user(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    user_in_db = {'username': username, 'hashed_password': get_hashed_password(password), 'is_active': True,
                  'created_at': datetime.utcnow(), 'id': uuid4(), 'role': 'admin'}
    try:
        result = await db_insert_user(user_in_db)
        if result is not None:
            return HTTP_201_CREATED
    except Exception as e:
        detail = 'Something went wrong. Please try again.'
        if hasattr(e, 'detail'):
            detail = e.detail
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=detail)


# Get token
@app.post('/login', description='Returns JWT token.', tags=['Get access token'])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    user = {'username': username, 'password': password}
    user_dict = UserIn(**user)
    result = await authenticate(user_dict)
    if result is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)
    else:
        token = create_jwt_token(result)
        return token


@app.middleware('http')
async def middleware(request: Request, call_next):
    start_time = datetime.utcnow()
    print(request.method)
    if request.method != 'GET' and not str(request.url).__contains__('login'):
        try:
            jwt_token = request.headers['Authorization'].split('Bearer ')[1]
            is_valid = check_jwt_token(jwt_token)
        except Exception as e:
            is_valid = False
        if not is_valid:
            return Response('Unauthorized', status_code=HTTP_401_UNAUTHORIZED)
    response = await call_next(request)
    execution_time = (datetime.utcnow() - start_time).microseconds
    response.headers['x-execution-time'] = str(execution_time)
    return response