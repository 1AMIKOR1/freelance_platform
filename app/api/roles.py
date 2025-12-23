from fastapi import APIRouter

from app.api.dependencies import DBDep
from app.exceptions.roles import (
    RoleAlreadyExistsError,
    RoleAlreadyExistsHTTPError,
    RoleNotFoundError,
    RoleNotFoundHTTPError,
)
from app.schemas.roles import SRoleAdd, SRoleGet
from app.schemas.relations_users_roles import SRoleGetWithRels
from app.services.roles import RoleService

router = APIRouter(prefix="/auth", tags=["Управление ролями"])


@router.post("/roles", summary="Создание новой роли")
async def create_new_role(
    role_data: SRoleAdd,
    db: DBDep,
) -> dict[str, str]:
    try:
        await RoleService(db).create_role(role_data)
    except RoleAlreadyExistsError:
        raise RoleAlreadyExistsHTTPError
    return {"status": "OK"}


@router.get("/roles", summary="Получение списка ролей")
async def get_all_roles(
    db: DBDep,
) -> list[SRoleGet]:
    return await RoleService(db).get_roles()


@router.get("/roles/{id}", summary="Получение конкретной роли")
async def get_role(
    db: DBDep,
    id: int,
) -> SRoleGetWithRels:
    return await RoleService(db).get_role(role_id=id)


@router.put("/roles/{id}", summary="Изменение конкретной роли")
async def get_role(
    db: DBDep,
    role_data: SRoleAdd,
    id: int,
) -> dict[str, str]:
    try:
        await RoleService(db).edit_role(role_id=id, role_data=role_data)
    except RoleNotFoundError:
        raise RoleNotFoundHTTPError

    return {"status": "OK"}


@router.delete("/roles/{id}", summary="Удаление конкретной роли")
async def delete_role(
    db: DBDep,
    id: int,
) -> dict[str, str]:
    try:
        await RoleService(db).delete_role(role_id=id)
    except RoleNotFoundError:
        raise RoleNotFoundHTTPError

    return {"status": "OK"}
