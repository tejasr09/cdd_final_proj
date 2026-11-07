import os
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import OrganizationMember


class Permission(StrEnum):
    ORGANIZATION_READ = "organization:read"
    MEMBER_MANAGE = "member:manage"
    ENTITY_READ = "entity:read"
    ENTITY_WRITE = "entity:write"
    DEPENDENCY_READ = "dependency:read"
    DEPENDENCY_WRITE = "dependency:write"
    EVENT_READ = "event:read"
    EVENT_WRITE = "event:write"
    ANALYSIS_RUN = "analysis:run"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "administrator": frozenset(Permission),
    "operations_coordinator": frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.ENTITY_READ,
            Permission.ENTITY_WRITE,
            Permission.DEPENDENCY_READ,
            Permission.DEPENDENCY_WRITE,
            Permission.EVENT_READ,
            Permission.EVENT_WRITE,
            Permission.ANALYSIS_RUN,
        }
    ),
    "department_coordinator": frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.ENTITY_READ,
            Permission.DEPENDENCY_READ,
            Permission.EVENT_READ,
        }
    ),
    "analyst": frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.ENTITY_READ,
            Permission.DEPENDENCY_READ,
            Permission.EVENT_READ,
            Permission.ANALYSIS_RUN,
        }
    ),
}


def local_auth_enabled() -> bool:
    return (
        os.environ.get("APP_ENV", "production").lower() in {"development", "test"}
        and os.environ.get("ENABLE_LOCAL_AUTH", "").lower() == "true"
    )


def resolve_active_membership(
    session: Session, user_id: UUID, organization_id: UUID
) -> OrganizationMember:
    membership = session.scalar(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.status == "active",
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization membership was not found.",
        )
    return membership


def authorize(membership: OrganizationMember, permission: Permission) -> None:
    allowed = ROLE_PERMISSIONS.get(membership.role, frozenset())
    if permission not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )


def parse_local_user_id(raw_user_id: str | None) -> UUID:
    if not local_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Local authentication is disabled.",
        )
    if raw_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A local user ID is required in development or test mode.",
        )
    try:
        return UUID(raw_user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The local user ID is invalid.",
        ) from error


def get_active_membership(
    session: Annotated[Session, Depends(get_session)],
    x_local_user_id: Annotated[str | None, Header()] = None,
    x_active_organization_id: Annotated[str | None, Header()] = None,
) -> OrganizationMember:
    user_id = parse_local_user_id(x_local_user_id)
    if x_active_organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active organization ID is required.",
        )
    try:
        organization_id = UUID(x_active_organization_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The active organization ID is invalid.",
        ) from error
    return resolve_active_membership(session, user_id, organization_id)
