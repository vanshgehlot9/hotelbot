from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash
from app.domain.user.schemas import Token, UserCreate
from app.api.dependencies import get_firestore_db

router = APIRouter()

@router.post("/superadmin/login", response_model=Token)
async def superadmin_login(db=Depends(get_firestore_db), form_data: OAuth2PasswordRequestForm = Depends()):
    docs = db.collection("users").where("email", "==", form_data.username).where("role", "==", "superadmin").limit(1).stream()
    user = None
    for doc in docs:
        user = doc.to_dict()
        break
        
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Incorrect email or password for Super Admin")
        
    access_token = create_access_token(
        subject=user["email"],
        role="superadmin",
        tenant_id=user.get("tenant_id", "platform"),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/tenant/login", response_model=Token)
async def tenant_login(db=Depends(get_firestore_db), form_data: OAuth2PasswordRequestForm = Depends()):
    docs = db.collection("users").where("email", "==", form_data.username).where("role", "==", "tenant_admin").limit(1).stream()
    user = None
    for doc in docs:
        user = doc.to_dict()
        break
        
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Incorrect email or password for Tenant Admin")
        
    access_token = create_access_token(
        subject=user["email"],
        role="tenant_admin",
        tenant_id=user.get("tenant_id", ""),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/staff/login", response_model=Token)
async def staff_login(db=Depends(get_firestore_db), form_data: OAuth2PasswordRequestForm = Depends()):
    docs = db.collection("users").where("email", "==", form_data.username).where("role", "==", "agent").limit(1).stream()
    user = None
    for doc in docs:
        user = doc.to_dict()
        break
        
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Incorrect email or password for Staff")
        
    access_token = create_access_token(
        subject=user["email"],
        role="agent",
        tenant_id=user.get("tenant_id", ""),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}
