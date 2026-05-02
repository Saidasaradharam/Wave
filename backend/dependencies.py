"""
Authorization dependencies for project access control.

Security: Centralized permission verification for project-level operations.
Efficiency: Uses selectinload to eagerly load project members in a single query.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import User, Project, ProjectMember, VisibilityEnum
from auth import get_current_user


async def verify_project_access(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    Verify that the current user has read access to the specified project.

    Security: Enforces visibility-based access control:
    - Public projects: any authenticated user can access.
    - Private projects: only members and owners can access.

    Efficiency: Uses selectinload to eagerly load members in one query,
    preventing N+1 queries during permission checks.

    Args:
        project_id: The ID of the project to verify access for.
        current_user: The authenticated user requesting access.
        db: Async database session dependency.

    Returns:
        The project with loaded members.

    Raises:
        HTTPException 404: If project not found.
        HTTPException 403: If user lacks access to a private project.
    """
    # Efficiency: Eager load members with user data in a single query
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.members).selectinload(ProjectMember.user))
        .where(Project.id == project_id).execution_options(populate_existing=True)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Security: Public projects allow access to any authenticated user
    if project.visibility == VisibilityEnum.public:
        return project

    # Security: Private projects require membership or ownership
    member = next((m for m in project.members if m.user_id == current_user.id), None)

    if not member and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")

    return project


async def verify_project_member(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    Verify that the current user is an explicit member or owner of the project.

    Security: Required for write operations — modifying tasks, adding comments,
    inviting members. Stricter than verify_project_access.

    Efficiency: Uses selectinload to eagerly load members and their user data
    in a single query, preventing N+1 queries.

    Args:
        project_id: The ID of the project to verify membership for.
        current_user: The authenticated user requesting access.
        db: Async database session dependency.

    Returns:
        The project with loaded members.

    Raises:
        HTTPException 404: If project not found.
        HTTPException 403: If user is not a member or owner.
    """
    # Efficiency: Eager load members in one query
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.members).selectinload(ProjectMember.user))
        .where(Project.id == project_id).execution_options(populate_existing=True)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Security: Owner has full access
    if project.owner_id == current_user.id:
        return project

    # Security: Check explicit membership
    member = next((m for m in project.members if m.user_id == current_user.id), None)

    if not member:
        raise HTTPException(status_code=403, detail="Must be a project member to perform this action")

    return project
