import os
from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from models.user_models import UserCreate, UserInDB, UserLogin, Token
from models.schemas import RefreshRequest
from dependencies.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    get_current_user,
    create_access_token,
    get_password_hash,
    verify_password,
# Updated by Angelo for token management
    create_refresh_token,
    hash_refresh_token,
    save_refresh_token_to_db
)
from database.cloud_db_controller import CloudDBController
from dotenv import load_dotenv

load_dotenv("./.env.development")

router = APIRouter(
    prefix="/api",
    tags=["auth"],
    responses={404: {"description": "Not found"}, 422: {"description": "Validation Error"}, 401: {"description": "Unauthorized"}},
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
DB_CONNECTION = CloudDBController()

@router.post("/register/")
async def register(form: UserLogin):
    """ Register a new user account """
    try:
        DB_CONNECTION.connect()
        existing_user = DB_CONNECTION.find_document("JagCoaching", "users", {"email": form.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        hashed_password = get_password_hash(form.password)
        user_document = {
            "username": form.email,
            "email": form.email,
            "password": hashed_password,
            "is_active": True,
            "created_at": datetime.now()
        }

        result = DB_CONNECTION.add_document("JagCoaching", "users", user_document)
        if not result.acknowledged:
            raise HTTPException(status_code=500, detail="Failed to create user")

        return {"status": "success", "message": "Registration successful!"}

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        if DB_CONNECTION.client:
            DB_CONNECTION.client.close()


@router.post("/auth/token/", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    try:
        print(f"Login attempt for user: {form_data.username}")
        DB_CONNECTION.connect()
        user = DB_CONNECTION.find_document("JagCoaching", "users", {"email": form_data.username})

        if not user or not verify_password(form_data.password, user.get('password', '')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user["email"]}, expires_delta=access_token_expires)
# Updated by Angelo to include both access_token and refresh_token
        refresh_token = create_refresh_token()
        save_refresh_token_to_db(user_id=str(user["_id"]), refresh_token=refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        print(f"Login error: {str(e)}")
        raise
    finally:
        if DB_CONNECTION.client:
            DB_CONNECTION.client.close()

# Updated by Angelo to include a new login endpoint 
@router.post("/auth/token/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest = Body(...)):
    try:
        DB_CONNECTION.connect()
        token_hash = hash_refresh_token(request.refresh_token)
        stored = DB_CONNECTION.get_refresh_token("JagCoaching", token_hash)

        if not stored or stored.get("expires_at") < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user_id = stored["user_id"]

        DB_CONNECTION.delete_refresh_token("JagCoaching", token_hash)

        new_refresh_token = create_refresh_token()
        save_refresh_token_to_db(user_id=user_id, refresh_token=new_refresh_token)

        access_token = create_access_token(data={"sub": user_id})

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        print(f"Refresh token error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")
    finally:
        if DB_CONNECTION.client:
            DB_CONNECTION.client.close()


# TODO: Make Logout Function 
@router.post("/api/logout/")
async def logout(current_user: UserInDB = Depends(get_current_user)):
    print(current_user)
    return {"status": "success", "message": "Logout successful!"}
