from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class SignInActivity(BaseModel):
    lastSignInDateTime: datetime | None = None


class User(BaseModel):
    id: str
    displayName: str
    userPrincipalName: str
    accountEnabled: bool = True
    assignedLicenses: list[dict] = Field(default_factory=list)
    signInActivity: SignInActivity | None = None


class PrepaidUnits(BaseModel):
    enabled: int
    suspended: int
    warning: int


class SubscribedSku(BaseModel):
    skuId: str
    skuPartNumber: str
    consumedUnits: int
    prepaidUnits: PrepaidUnits


class CredentialRegistration(BaseModel):
    userId: str
    userPrincipalName: str
    isMfaRegistered: bool
