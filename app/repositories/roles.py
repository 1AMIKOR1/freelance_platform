from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.roles import RoleModel
from app.repositories.base import BaseRepository
from app.schemas.roles import SRoleGet
from app.schemas.relations_users_roles import SRoleGetWithRels


class RolesRepository(BaseRepository):
    model = RoleModel
    schema = SRoleGet

    async def get_one_or_none_with_users(self, **filter_by):
        query = (
            select(self.model)
            .filter_by(**filter_by)
            .options(selectinload(self.model.users))
        )

        result = await self.session.execute(query)

        model = result.scalars().one_or_none()
        if model is None:
            return None

        result = SRoleGetWithRels.model_validate(model, from_attributes=True)
        return result
