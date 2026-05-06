from fastapi import APIRouter, Depends, HTTPException
import uuid
from app.core.security import get_password_hash
from app.api.dependencies import get_firestore_db, require_superadmin, require_tenant_admin
from pydantic import BaseModel, EmailStr

router = APIRouter()

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

@router.get("/tenants")
async def list_tenants(
    db=Depends(get_firestore_db),
    current_user: dict = Depends(require_superadmin)
):
    """List all tenant admins."""
    docs = db.collection("users").where("role", "==", "tenant_admin").stream()
    users = []
    for doc in docs:
        u = doc.to_dict()
        u.pop("hashed_password", None)  # never expose password hash
        users.append(u)
    return {"tenants": users}

@router.put("/change-password")
async def change_tenant_password(
    payload: ChangePasswordRequest,
    db=Depends(get_firestore_db),
    current_user: dict = Depends(require_superadmin)
):
    """Super Admin changes a tenant admin's password."""
    docs = list(db.collection("users").where("email", "==", payload.email).limit(1).stream())
    if not docs:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_ref = db.collection("users").document(docs[0].id)
    user_ref.update({"hashed_password": get_password_hash(payload.new_password)})
    return {"msg": f"Password updated successfully for {payload.email}"}

@router.post("/tenant")
async def create_tenant_admin(
    payload: CreateUserRequest,
    db = Depends(get_firestore_db),
    current_user: dict = Depends(require_superadmin)
):
    """Super Admin creates a Tenant Admin with a newly generated tenant_id"""
    docs = db.collection("users").where("email", "==", payload.email).limit(1).stream()
    if any(docs):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
    hashed_password = get_password_hash(payload.password)
    
    new_user = {
        "email": payload.email,
        "hashed_password": hashed_password,
        "role": "tenant_admin",
        "tenant_id": tenant_id
    }
    
    db.collection("users").document(payload.email).set(new_user)
    
    # Also create a blank tenant record
    db.collection("tenants").document(tenant_id).set({
        "name": f"Hotel for {payload.email}",
        "subscription_tier": "free",
        "created_by": current_user["email"]
    })
    
    return {"msg": "Tenant admin created successfully", "tenant_id": tenant_id, "email": payload.email}

@router.post("/agent")
async def create_agent(
    payload: CreateUserRequest,
    db = Depends(get_firestore_db),
    current_user: dict = Depends(require_tenant_admin)
):
    """Tenant Admin creates an Agent assigned to their own tenant_id"""
    docs = db.collection("users").where("email", "==", payload.email).limit(1).stream()
    if any(docs):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    tenant_id = current_user.get("tenant_id")
    if not tenant_id or tenant_id == "platform":
        raise HTTPException(status_code=400, detail="Invalid tenant context for creating an agent")
        
    hashed_password = get_password_hash(payload.password)
    
    new_user = {
        "email": payload.email,
        "hashed_password": hashed_password,
        "role": "agent",
        "tenant_id": tenant_id
    }
    
    db.collection("users").document(payload.email).set(new_user)
    return {"msg": "Agent created successfully", "email": payload.email}
