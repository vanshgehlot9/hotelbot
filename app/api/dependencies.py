from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings
from app.domain.user.schemas import TokenData
from app.db.firebase import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_firestore_db():
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_firestore_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=payload.get("role"), tenant_id=payload.get("tenant_id"))
    except JWTError:
        raise credentials_exception
        
    # Verify user exists in Firestore
    docs = db.collection("users").where("email", "==", token_data.email).limit(1).stream()
    user_doc = None
    for doc in docs:
        user_doc = doc.to_dict()
        user_doc["id"] = doc.id
        break
        
    if user_doc is None:
        raise credentials_exception
        
    return user_doc

def get_current_active_user(current_user: dict = Depends(get_current_user)):
    return current_user

def require_role(roles: list[str]):
    def role_checker(current_user: dict = Depends(get_current_active_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return current_user
    return role_checker

require_superadmin = require_role(["superadmin"])
require_tenant_admin = require_role(["superadmin", "tenant_admin"])
