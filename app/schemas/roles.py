from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)

class Role(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SRoleGet(Role):
    pass


class SRoleAdd(RoleBase):
    pass
