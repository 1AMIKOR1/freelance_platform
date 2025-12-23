from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.users import UserModel
from app.repositories.base import BaseRepository
from app.schemas.user import SUserGet
from app.schemas.relations_users_roles import SUserGetWithRels


class UsersRepository(BaseRepository):
    model = UserModel
    schema = SUserGet

    async def get_one_or_none_with_role(self, **filter_by):
        query = (
            select(self.model)
            .filter_by(**filter_by)
            .options(selectinload(self.model.role))
        )

        result = await self.session.execute(query)

        model = result.scalars().one_or_none()
        if model is None:
            return None

        result = SUserGetWithRels.model_validate(model, from_attributes=True)
        return result
