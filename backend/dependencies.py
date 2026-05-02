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
    Ensures the user has read access to the project.
    Allows access if the project is public, or if the user is a member/owner.
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.members).selectinload(ProjectMember.user))
        .where(Project.id == project_id).execution_options(populate_existing=True)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.visibility == VisibilityEnum.public:
        return project
        
    # Check if user is a member
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
    Ensures the user is an explicit member or owner of the project.
    Required for modifying tasks, adding comments, etc.
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.members).selectinload(ProjectMember.user))
        .where(Project.id == project_id).execution_options(populate_existing=True)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.owner_id == current_user.id:
        return project
        
    member = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not member:
        raise HTTPException(status_code=403, detail="Must be a project member to perform this action")
        
    return project
