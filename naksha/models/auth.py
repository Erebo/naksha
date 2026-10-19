"""Authentication and Authorization Domain Models."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OfficerRole(str, Enum):
    """Statutory revenue administration officer roles."""
    UNION_LAND_OFFICER = "union_land_officer"
    AC_LAND = "ac_land"
    KANUNGO = "kanungo"
    SURVEYOR = "surveyor"
    SYSTEM_ADMIN = "system_admin"


class OfficerContext(BaseModel):
    """Authenticated officer security context parsed from Bearer JWT session."""
    officer_id: str = Field(description="Unique officer identifier (e.g. UL-2024-KSH).")
    name: str = Field(description="Officer official display name.")
    role: OfficerRole = Field(description="Authorized administrative role.")
    designation: str = Field(description="Official job title.")
    office: str = Field(description="Jurisdiction or office location.")
    jurisdiction: str = Field(description="Statutory geographical scope (e.g. কাশিমপুর or গাজীপুর সদর).")
