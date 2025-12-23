from app.schemas.user import SUserGet
from app.schemas.roles import SRoleGet


class SRoleGetWithRels(SRoleGet):
    users: list[SUserGet] | None = None


class SUserGetWithRels(SUserGet):
    role: SRoleGet
