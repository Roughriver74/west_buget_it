"""
KPI Tasks API

REST API endpoints for managing KPI tasks linked to employee goals.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from fastapi import APIRouter, Depends, HTTPException, status, Query
from decimal import Decimal

from app.db.session import get_db
from app.db.models import (
    KPITask,
    EmployeeKPIGoal,
    Employee,
    User,
    UserRoleEnum,
    KPITaskStatusEnum,
    KPITaskPriorityEnum
)
from app.api.v1.auth import get_current_active_user
from app.schemas.kpi_task import (
    KPITaskCreate,
    KPITaskUpdate,
    KPITaskInDB,
    KPITaskResponse,
    KPITaskStatusUpdate,
    KPITaskComplexityUpdate,
    KPITaskBulkStatusUpdate,
    KPITaskStatistics
)

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.get("/", response_model=List[KPITaskResponse])
def get_kpi_tasks(
    employee_id: Optional[int] = Query(None, description="Фильтр по ID сотрудника"),
    employee_kpi_goal_id: Optional[int] = Query(None, description="Фильтр по ID цели"),
    status: Optional[KPITaskStatusEnum] = Query(None, description="Фильтр по статусу"),
    priority: Optional[KPITaskPriorityEnum] = Query(None, description="Фильтр по приоритету"),
    overdue_only: bool = Query(False, description="Показать только просроченные"),
    department_id: Optional[int] = Query(None, description="Фильтр по отделу"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of KPI tasks with filtering.

    **Permissions:**
    - USER: only their own tasks
    - MANAGER/ADMIN: can filter by department or see all
    """
    query = db.query(KPITask).options(
        joinedload(KPITask.employee),
        joinedload(KPITask.employee_kpi_goal),
        joinedload(KPITask.assigned_by)
    )

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        # USER sees only their own tasks
        query = query.filter(KPITask.employee_id == current_user.id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER/ADMIN can filter by department
        if department_id:
            query = query.filter(KPITask.department_id == department_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Apply filters
    if employee_id:
        query = query.filter(KPITask.employee_id == employee_id)

    if employee_kpi_goal_id:
        query = query.filter(KPITask.employee_kpi_goal_id == employee_kpi_goal_id)

    if status:
        query = query.filter(KPITask.status == status)

    if priority:
        query = query.filter(KPITask.priority == priority)

    if overdue_only:
        query = query.filter(
            and_(
                KPITask.due_date < datetime.utcnow(),
                KPITask.status.in_([KPITaskStatusEnum.TODO, KPITaskStatusEnum.IN_PROGRESS])
            )
        )

    # Order by priority (CRITICAL first) and due_date
    query = query.order_by(
        KPITask.priority.desc(),
        KPITask.due_date.asc().nullslast()
    )

    tasks = query.offset(skip).limit(limit).all()

    # Enrich with related data
    response_tasks = []
    for task in tasks:
        task_dict = KPITaskInDB.model_validate(task).model_dump()
        task_dict['employee_name'] = task.employee.full_name if task.employee else None
        task_dict['goal_name'] = task.employee_kpi_goal.goal.name if task.employee_kpi_goal and task.employee_kpi_goal.goal else None
        task_dict['assigned_by_name'] = task.assigned_by.full_name if task.assigned_by else None
        response_tasks.append(KPITaskResponse(**task_dict))

    return response_tasks


@router.get("/{task_id}", response_model=KPITaskResponse)
def get_kpi_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get single KPI task by ID"""
    task = db.query(KPITask).options(
        joinedload(KPITask.employee),
        joinedload(KPITask.employee_kpi_goal),
        joinedload(KPITask.assigned_by)
    ).filter(KPITask.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Permission check
    if current_user.role == UserRoleEnum.USER:
        if task.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own tasks"
            )
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if task.department_id != current_user.department_id and current_user.role != UserRoleEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view tasks in your department"
            )

    # Enrich response
    task_dict = KPITaskInDB.model_validate(task).model_dump()
    task_dict['employee_name'] = task.employee.full_name if task.employee else None
    task_dict['goal_name'] = task.employee_kpi_goal.goal.name if task.employee_kpi_goal and task.employee_kpi_goal.goal else None
    task_dict['assigned_by_name'] = task.assigned_by.full_name if task.assigned_by else None

    return KPITaskResponse(**task_dict)


@router.post("/", response_model=KPITaskResponse, status_code=status.HTTP_201_CREATED)
def create_kpi_task(
    task_data: KPITaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new KPI task.

    **Permissions:**
    - MANAGER/ADMIN: can create tasks for any employee in their department
    - USER: can create tasks for themselves
    """
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == task_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {task_data.employee_id} not found"
        )

    # Verify goal exists
    goal = db.query(EmployeeKPIGoal).filter(
        EmployeeKPIGoal.id == task_data.employee_kpi_goal_id
    ).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal {task_data.employee_kpi_goal_id} not found"
        )

    # Permission check
    if current_user.role == UserRoleEnum.USER:
        if task_data.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create tasks for yourself"
            )
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if employee.department_id != current_user.department_id and current_user.role != UserRoleEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create tasks for employees in your department"
            )

    # Create task
    task_dict = task_data.model_dump()
    task_dict['department_id'] = employee.department_id
    task_dict['assigned_by_id'] = current_user.id

    task = KPITask(**task_dict)
    db.add(task)
    db.commit()
    db.refresh(task)

    # Load relationships
    task = db.query(KPITask).options(
        joinedload(KPITask.employee),
        joinedload(KPITask.employee_kpi_goal),
        joinedload(KPITask.assigned_by)
    ).filter(KPITask.id == task.id).first()

    # Enrich response
    task_dict = KPITaskInDB.model_validate(task).model_dump()
    task_dict['employee_name'] = task.employee.full_name if task.employee else None
    task_dict['goal_name'] = task.employee_kpi_goal.goal.name if task.employee_kpi_goal and task.employee_kpi_goal.goal else None
    task_dict['assigned_by_name'] = task.assigned_by.full_name if task.assigned_by else None

    return KPITaskResponse(**task_dict)


@router.put("/{task_id}", response_model=KPITaskResponse)
def update_kpi_task(
    task_id: int,
    task_update: KPITaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update KPI task.

    **Permissions:**
    - Task owner (employee): can update their own tasks
    - MANAGER/ADMIN: can update tasks in their department
    """
    task = db.query(KPITask).filter(KPITask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Permission check
    if current_user.role == UserRoleEnum.USER:
        if task.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own tasks"
            )
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if task.department_id != current_user.department_id and current_user.role != UserRoleEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tasks in your department"
            )

    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)

    # Auto-set completed_at when status changes to DONE
    if 'status' in update_data and update_data['status'] == KPITaskStatusEnum.DONE:
        if task.status != KPITaskStatusEnum.DONE:
            update_data['completed_at'] = datetime.utcnow()
            # Auto-set completion to 100%
            if 'completion_percentage' not in update_data:
                update_data['completion_percentage'] = Decimal("100")

    # Clear completed_at if status changes from DONE to something else
    if 'status' in update_data and update_data['status'] != KPITaskStatusEnum.DONE:
        if task.status == KPITaskStatusEnum.DONE:
            update_data['completed_at'] = None

    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    # Load relationships
    task = db.query(KPITask).options(
        joinedload(KPITask.employee),
        joinedload(KPITask.employee_kpi_goal),
        joinedload(KPITask.assigned_by)
    ).filter(KPITask.id == task.id).first()

    # Enrich response
    task_dict = KPITaskInDB.model_validate(task).model_dump()
    task_dict['employee_name'] = task.employee.full_name if task.employee else None
    task_dict['goal_name'] = task.employee_kpi_goal.goal.name if task.employee_kpi_goal and task.employee_kpi_goal.goal else None
    task_dict['assigned_by_name'] = task.assigned_by.full_name if task.assigned_by else None

    return KPITaskResponse(**task_dict)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kpi_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete KPI task.

    **Permissions:**
    - MANAGER/ADMIN only
    """
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER or ADMIN can delete tasks"
        )

    task = db.query(KPITask).filter(KPITask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Permission check for MANAGER
    if current_user.role == UserRoleEnum.MANAGER:
        if task.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete tasks in your department"
            )

    db.delete(task)
    db.commit()


# ============================================================================
# Status & Workflow Operations
# ============================================================================

@router.post("/{task_id}/status", response_model=KPITaskResponse)
def update_task_status(
    task_id: int,
    status_update: KPITaskStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update task status with optional completion percentage"""
    task = db.query(KPITask).filter(KPITask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Permission check
    if current_user.role == UserRoleEnum.USER:
        if task.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own tasks"
            )

    # Update status
    task.status = status_update.status
    if status_update.completion_percentage is not None:
        task.completion_percentage = status_update.completion_percentage
    if status_update.notes:
        task.notes = (task.notes or "") + f"\n[{datetime.utcnow().isoformat()}] {status_update.notes}"

    # Auto-set timestamps
    if status_update.status == KPITaskStatusEnum.IN_PROGRESS and task.start_date is None:
        task.start_date = datetime.utcnow()
    if status_update.status == KPITaskStatusEnum.DONE:
        task.completed_at = datetime.utcnow()
        if task.completion_percentage is None or task.completion_percentage < 100:
            task.completion_percentage = Decimal("100")

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    # Load relationships
    task = db.query(KPITask).options(
        joinedload(KPITask.employee),
        joinedload(KPITask.employee_kpi_goal),
        joinedload(KPITask.assigned_by)
    ).filter(KPITask.id == task.id).first()

    # Enrich response
    task_dict = KPITaskInDB.model_validate(task).model_dump()
    task_dict['employee_name'] = task.employee.full_name if task.employee else None
    task_dict['goal_name'] = task.employee_kpi_goal.goal.name if task.employee_kpi_goal and task.employee_kpi_goal.goal else None
    task_dict['assigned_by_name'] = task.assigned_by.full_name if task.assigned_by else None

    return KPITaskResponse(**task_dict)


@router.post("/bulk/status")
def bulk_update_task_status(
    bulk_update: KPITaskBulkStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk status update for multiple tasks.

    **Permissions:**
    - MANAGER/ADMIN only
    """
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER or ADMIN can perform bulk operations"
        )

    tasks = db.query(KPITask).filter(KPITask.id.in_(bulk_update.task_ids)).all()
    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tasks found"
        )

    # Permission check for MANAGER
    if current_user.role == UserRoleEnum.MANAGER:
        for task in tasks:
            if task.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Task {task.id} is not in your department"
                )

    # Update all tasks
    updated_count = 0
    for task in tasks:
        task.status = bulk_update.status
        if bulk_update.notes:
            task.notes = (task.notes or "") + f"\n[{datetime.utcnow().isoformat()}] {bulk_update.notes}"

        # Auto-set timestamps
        if bulk_update.status == KPITaskStatusEnum.DONE:
            task.completed_at = datetime.utcnow()
            task.completion_percentage = Decimal("100")

        task.updated_at = datetime.utcnow()
        updated_count += 1

    db.commit()

    return {
        "success": True,
        "message": f"Updated {updated_count} tasks to {bulk_update.status.value}",
        "updated_count": updated_count,
        "task_ids": bulk_update.task_ids
    }


# ============================================================================
# Complexity & Estimation Operations
# ============================================================================

@router.post("/{task_id}/complexity", response_model=KPITaskResponse)
def update_task_complexity(
    task_id: int,
    complexity_update: KPITaskComplexityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update task complexity and estimation.

    **Permissions:**
    - MANAGER/ADMIN: can update any task in their department
    """
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER or ADMIN can update task complexity"
        )

    task = db.query(KPITask).filter(KPITask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Permission check for MANAGER
    if current_user.role == UserRoleEnum.MANAGER:
        if task.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tasks in your department"
            )

    # Update complexity
    task.complexity = complexity_update.complexity
    if complexity_update.estimated_hours is not None:
        task.estimated_hours = complexity_update.estimated_hours
    if complexity_update.notes:
        task.notes = (task.notes or "") + f"\n[{datetime.utcnow().isoformat()}] Complexity updated: {complexity_update.notes}"

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    # Load relationships
    task = db.query(KPITask).options(
        joinedload(KPITask.employee),
        joinedload(KPITask.employee_kpi_goal),
        joinedload(KPITask.assigned_by)
    ).filter(KPITask.id == task.id).first()

    # Enrich response
    task_dict = KPITaskInDB.model_validate(task).model_dump()
    task_dict['employee_name'] = task.employee.full_name if task.employee else None
    task_dict['goal_name'] = task.employee_kpi_goal.goal.name if task.employee_kpi_goal and task.employee_kpi_goal.goal else None
    task_dict['assigned_by_name'] = task.assigned_by.full_name if task.assigned_by else None

    return KPITaskResponse(**task_dict)


# ============================================================================
# Analytics & Statistics
# ============================================================================

@router.get("/analytics/statistics", response_model=KPITaskStatistics)
def get_task_statistics(
    employee_id: Optional[int] = Query(None, description="Фильтр по сотруднику"),
    department_id: Optional[int] = Query(None, description="Фильтр по отделу"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get task statistics.

    **Permissions:**
    - USER: only their own statistics
    - MANAGER/ADMIN: can filter by department or see all
    """
    query = db.query(KPITask)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(KPITask.employee_id == current_user.id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            query = query.filter(KPITask.department_id == department_id)
        if employee_id:
            query = query.filter(KPITask.employee_id == employee_id)

    # Total tasks
    total_tasks = query.count()

    # By status
    by_status = {}
    for status_enum in KPITaskStatusEnum:
        count = query.filter(KPITask.status == status_enum).count()
        by_status[status_enum.value] = count

    # By priority
    by_priority = {}
    for priority_enum in KPITaskPriorityEnum:
        count = query.filter(KPITask.priority == priority_enum).count()
        by_priority[priority_enum.value] = count

    # Average complexity
    avg_complexity = db.query(func.avg(KPITask.complexity)).filter(
        KPITask.complexity.isnot(None)
    ).scalar()
    if avg_complexity and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            avg_complexity = db.query(func.avg(KPITask.complexity)).filter(
                KPITask.department_id == department_id,
                KPITask.complexity.isnot(None)
            ).scalar()
        elif employee_id:
            avg_complexity = db.query(func.avg(KPITask.complexity)).filter(
                KPITask.employee_id == employee_id,
                KPITask.complexity.isnot(None)
            ).scalar()

    # Total estimated/actual hours
    total_estimated = query.filter(KPITask.estimated_hours.isnot(None)).with_entities(
        func.sum(KPITask.estimated_hours)
    ).scalar() or Decimal("0")

    total_actual = query.filter(KPITask.actual_hours.isnot(None)).with_entities(
        func.sum(KPITask.actual_hours)
    ).scalar() or Decimal("0")

    # Completion rate
    done_count = query.filter(KPITask.status == KPITaskStatusEnum.DONE).count()
    completion_rate = Decimal(done_count / total_tasks * 100) if total_tasks > 0 else Decimal("0")

    # Overdue tasks
    overdue_count = query.filter(
        and_(
            KPITask.due_date < datetime.utcnow(),
            KPITask.status.in_([KPITaskStatusEnum.TODO, KPITaskStatusEnum.IN_PROGRESS])
        )
    ).count()

    return KPITaskStatistics(
        total_tasks=total_tasks,
        by_status=by_status,
        by_priority=by_priority,
        avg_complexity=Decimal(str(avg_complexity)) if avg_complexity else None,
        total_estimated_hours=total_estimated,
        total_actual_hours=total_actual,
        completion_rate=completion_rate,
        overdue_tasks=overdue_count
    )
