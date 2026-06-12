"""
Users API
用户管理模块
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_db, get_admin_user
from app.core.security import get_security_manager
from app.models.user import User
from app.schemas.auth import UserCreateRequest, UserUpdateRequest
from app.schemas.common import BaseResponse
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=BaseResponse)
async def get_users(
    search: str | None = Query(None),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取用户列表"""
    query = select(User)

    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    if role:
        query = query.where(User.role == role)

    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return BaseResponse(
        data={
            "items": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "avatar": user.avatar,
                    "status": user.status,
                    "createdAt": user.created_at.isoformat() if user.created_at else None,
                }
                for user in users
            ],
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
    )


@router.post("", response_model=BaseResponse)
async def create_user(
    data: UserCreateRequest,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建用户"""
    security = get_security_manager()
    password_hash = security.hash_password(data.password)

    user = User(
        username=data.username,
        email=data.email,
        password_hash=password_hash,
        role=data.role,
        status="active",
    )
    db.add(user)
    await db.commit()

    return BaseResponse(data={"id": user.id})


@router.put("/{user_id}", response_model=BaseResponse)
async def update_user(
    user_id: str,
    data: UserUpdateRequest,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新用户"""
    update_data = {}
    raw = data.model_dump(exclude_unset=True)

    if "role" in raw:
        existing_result = await db.execute(select(User).where(User.id == user_id))
        existing_user = existing_result.scalar_one_or_none()
        if existing_user and existing_user.role == "admin" and raw["role"] == "operator":
            raise HTTPException(status_code=400, detail="不允许将管理员降级为操作员")

    if "username" in raw:
        update_data["username"] = raw["username"]
    if "email" in raw:
        update_data["email"] = raw["email"]
    if "role" in raw:
        update_data["role"] = raw["role"]
    if "password" in raw:
        security = get_security_manager()
        update_data["password_hash"] = security.hash_password(raw["password"])

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(**update_data)
    )
    await db.commit()

    return BaseResponse(message="更新成功")


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    await db.execute(
        delete(User).where(User.id == user_id)
    )
    await db.commit()

    return BaseResponse(message="删除成功")


@router.patch("/{user_id}/toggle", response_model=BaseResponse)
async def toggle_user(
    user_id: str,
    status: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(status=status)
    )
    await db.commit()

    return BaseResponse(message="操作成功")
