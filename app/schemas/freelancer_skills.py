from pydantic import BaseModel, ConfigDict, Field

class FreelancerSkillBase(BaseModel):
    freelancer_id: int = Field(..., ge=1)
    skill_id: int = Field(..., ge=1)

class FreelancerSkillCreate(FreelancerSkillBase):
    pass

class FreelancerSkill(FreelancerSkillBase):
    model_config = ConfigDict(from_attributes=True)