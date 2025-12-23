# app/schemas/__init__.py - ИСПРАВЛЕННЫЙ ВАРИАНТ
from .user import User, UserCreate, UserUpdate
# from .role import Role, RoleCreate, RoleUpdate
# from .freelancer import Freelancer, FreelancerCreate, FreelancerUpdate
# from .project import Project, ProjectCreate, ProjectUpdate
# from .proposal import Proposal, ProposalCreate, ProposalUpdate
# from .payment import Payment, PaymentCreate, PaymentUpdate
# from .review import Review, ReviewCreate, ReviewUpdate
# from .message import Message, MessageCreate, MessageUpdate
# from .skill import Skill, SkillCreate, SkillUpdate
# from .freelancer_skill import FreelancerSkill, FreelancerSkillCreate

__all__ = [
    # User
    "User", 
    "UserCreate", 
    "UserUpdate",
    
    # Role
    # "Role",
    # "RoleCreate", 
    # "RoleUpdate",
    
    # Freelancer
    # "Freelancer",
    # "FreelancerCreate", 
    # "FreelancerUpdate",
    
    # Project
    # "Project",
    # "ProjectCreate", 
    # "ProjectUpdate",
    
    # Proposal
    # "Proposal",
    # "ProposalCreate", 
    # "ProposalUpdate",
    
    # Payment
    # "Payment",
    # "PaymentCreate", 
    # "PaymentUpdate",
    
    # Review
    # "Review",
    # "ReviewCreate", 
    # "ReviewUpdate",
    
    # Message
    # "Message",
    # "MessageCreate", 
    # "MessageUpdate",
    
    # Skill
    # "Skill",
    # "SkillCreate", 
    # "SkillUpdate",
    
    # FreelancerSkill
    # "FreelancerSkill",
    # "FreelancerSkillCreate",
]