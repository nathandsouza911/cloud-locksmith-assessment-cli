from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class SignInActivity(BaseModel):
    lastSignInDateTime: datetime | None = None


class User(BaseModel):
    id: str
    displayName: str | None = None
    userPrincipalName: str | None = None
    accountEnabled: bool = True
    userType: str | None = None
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
    id: str
    userPrincipalName: str | None = None
    isMfaRegistered: bool = False


class SecurityDefaults(BaseModel):
    """policies/identitySecurityDefaultsEnforcementPolicy"""
    isEnabled: bool = False


class ConditionalAccessPolicy(BaseModel):
    """identity/conditionalAccess/policies — inventory only, no rule internals."""
    id: str
    displayName: str | None = None
    # "enabled" | "disabled" | "enabledForReportingButNotEnforced"
    state: str | None = None


class DefaultUserRolePermissions(BaseModel):
    # Which app-consent policies are granted to the default (non-admin) user role.
    permissionGrantPoliciesAssigned: list[str] = Field(default_factory=list)


class AuthorizationPolicy(BaseModel):
    """policies/authorizationPolicy — tenant-wide user/consent/guest defaults."""
    defaultUserRolePermissions: DefaultUserRolePermissions = Field(
        default_factory=DefaultUserRolePermissions
    )
    # "everyone" | "adminsAndGuestInviters" | "adminsGuestInvitersAndAllMembers" | "none"
    allowInvitesFrom: str | None = None
