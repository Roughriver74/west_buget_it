"""
API endpoints for Revenue Analytics
Advanced analytics for revenue data: regional breakdown, product mix, trends, plan vs actual
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, extract
from datetime import datetime
from decimal import Decimal

from app.db import get_db
from app.db.models import (
    User,
    UserRoleEnum,
    RevenuePlan,
    RevenuePlanVersion,
    RevenuePlanDetail,
    RevenueActual,
    RevenueStream,
    RevenueCategory,
    RevenueVersionStatusEnum,
)
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/regional-breakdown")
def get_regional_breakdown(
    year: int = Query(..., description="Year for analysis"),
    department_id: Optional[int] = Query(None, description="Department ID (MANAGER/ADMIN only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get revenue breakdown by region (revenue streams)

    Returns:
    - Total planned revenue per region
    - Total actual revenue per region
    - Variance (actual - plan)
    - Variance percentage
    """
    # Determine department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    else:
        target_department_id = department_id if department_id is not None else current_user.department_id

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Get revenue streams (regions)
    streams = (
        db.query(RevenueStream)
        .filter(
            RevenueStream.department_id == target_department_id,
            RevenueStream.is_active == True
        )
        .all()
    )

    result = []
    for stream in streams:
        # Get approved plan details for this stream
        approved_versions = (
            db.query(RevenuePlanVersion)
            .join(RevenuePlan)
            .filter(
                RevenuePlan.year == year,
                RevenuePlan.department_id == target_department_id,
                RevenuePlanVersion.status == RevenueVersionStatusEnum.APPROVED
            )
            .all()
        )

        version_ids = [v.id for v in approved_versions]

        # Sum planned revenue for this stream
        planned_total = (
            db.query(func.coalesce(func.sum(
                RevenuePlanDetail.month_01 + RevenuePlanDetail.month_02 +
                RevenuePlanDetail.month_03 + RevenuePlanDetail.month_04 +
                RevenuePlanDetail.month_05 + RevenuePlanDetail.month_06 +
                RevenuePlanDetail.month_07 + RevenuePlanDetail.month_08 +
                RevenuePlanDetail.month_09 + RevenuePlanDetail.month_10 +
                RevenuePlanDetail.month_11 + RevenuePlanDetail.month_12
            ), 0))
            .filter(
                RevenuePlanDetail.version_id.in_(version_ids),
                RevenuePlanDetail.revenue_stream_id == stream.id
            )
            .scalar()
        ) if version_ids else 0

        # Sum actual revenue for this stream
        actual_total = (
            db.query(func.coalesce(func.sum(RevenueActual.actual_amount), 0))
            .filter(
                RevenueActual.year == year,
                RevenueActual.revenue_stream_id == stream.id,
                RevenueActual.department_id == target_department_id
            )
            .scalar()
        )

        planned = float(planned_total or 0)
        actual = float(actual_total or 0)
        variance = actual - planned
        variance_percent = (variance / planned * 100) if planned > 0 else 0

        result.append({
            "stream_id": stream.id,
            "stream_name": stream.name,
            "stream_type": stream.stream_type,
            "planned_revenue": planned,
            "actual_revenue": actual,
            "variance": variance,
            "variance_percent": round(variance_percent, 2),
        })

    log_info(
        f"Get regional breakdown - user_id: {current_user.id}, year: {year}, "
        f"department_id: {target_department_id}, regions: {len(result)}",
        "revenue_analytics"
    )

    return {
        "year": year,
        "department_id": target_department_id,
        "regions": result,
        "total_planned": sum(r["planned_revenue"] for r in result),
        "total_actual": sum(r["actual_revenue"] for r in result),
    }


@router.get("/product-mix")
def get_product_mix(
    year: int = Query(..., description="Year for analysis"),
    department_id: Optional[int] = Query(None, description="Department ID (MANAGER/ADMIN only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get revenue breakdown by product category

    Returns:
    - Total planned revenue per category
    - Total actual revenue per category
    - Share of total revenue (%)
    """
    # Determine department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    else:
        target_department_id = department_id if department_id is not None else current_user.department_id

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Get revenue categories
    categories = (
        db.query(RevenueCategory)
        .filter(
            RevenueCategory.department_id == target_department_id,
            RevenueCategory.is_active == True
        )
        .all()
    )

    result = []
    total_planned = 0
    total_actual = 0

    for category in categories:
        # Get approved plan details for this category
        approved_versions = (
            db.query(RevenuePlanVersion)
            .join(RevenuePlan)
            .filter(
                RevenuePlan.year == year,
                RevenuePlan.department_id == target_department_id,
                RevenuePlanVersion.status == RevenueVersionStatusEnum.APPROVED
            )
            .all()
        )

        version_ids = [v.id for v in approved_versions]

        # Sum planned revenue for this category
        planned_total = (
            db.query(func.coalesce(func.sum(
                RevenuePlanDetail.month_01 + RevenuePlanDetail.month_02 +
                RevenuePlanDetail.month_03 + RevenuePlanDetail.month_04 +
                RevenuePlanDetail.month_05 + RevenuePlanDetail.month_06 +
                RevenuePlanDetail.month_07 + RevenuePlanDetail.month_08 +
                RevenuePlanDetail.month_09 + RevenuePlanDetail.month_10 +
                RevenuePlanDetail.month_11 + RevenuePlanDetail.month_12
            ), 0))
            .filter(
                RevenuePlanDetail.version_id.in_(version_ids),
                RevenuePlanDetail.revenue_category_id == category.id
            )
            .scalar()
        ) if version_ids else 0

        # Sum actual revenue for this category
        actual_total = (
            db.query(func.coalesce(func.sum(RevenueActual.actual_amount), 0))
            .filter(
                RevenueActual.year == year,
                RevenueActual.revenue_category_id == category.id,
                RevenueActual.department_id == target_department_id
            )
            .scalar()
        )

        planned = float(planned_total or 0)
        actual = float(actual_total or 0)
        total_planned += planned
        total_actual += actual

        result.append({
            "category_id": category.id,
            "category_name": category.name,
            "category_type": category.category_type,
            "planned_revenue": planned,
            "actual_revenue": actual,
        })

    # Calculate shares
    for item in result:
        item["planned_share"] = round(
            (item["planned_revenue"] / total_planned * 100) if total_planned > 0 else 0, 2
        )
        item["actual_share"] = round(
            (item["actual_revenue"] / total_actual * 100) if total_actual > 0 else 0, 2
        )

    # Sort by planned revenue descending
    result.sort(key=lambda x: x["planned_revenue"], reverse=True)

    log_info(
        f"Get product mix - user_id: {current_user.id}, year: {year}, "
        f"department_id: {target_department_id}, categories: {len(result)}",
        "revenue_analytics"
    )

    return {
        "year": year,
        "department_id": target_department_id,
        "categories": result,
        "total_planned": total_planned,
        "total_actual": total_actual,
    }


@router.get("/monthly-trends")
def get_monthly_trends(
    year: int = Query(..., description="Year for analysis"),
    department_id: Optional[int] = Query(None, description="Department ID (MANAGER/ADMIN only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get monthly revenue trends (plan vs actual)

    Returns 12 months with planned and actual revenue
    """
    # Determine department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    else:
        target_department_id = department_id if department_id is not None else current_user.department_id

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Get approved versions
    approved_versions = (
        db.query(RevenuePlanVersion)
        .join(RevenuePlan)
        .filter(
            RevenuePlan.year == year,
            RevenuePlan.department_id == target_department_id,
            RevenuePlanVersion.status == RevenueVersionStatusEnum.APPROVED
        )
        .all()
    )

    version_ids = [v.id for v in approved_versions]

    monthly_data = []
    for month in range(1, 13):
        month_field = f"month_{str(month).zfill(2)}"

        # Sum planned revenue for this month
        planned = (
            db.query(func.coalesce(func.sum(getattr(RevenuePlanDetail, month_field)), 0))
            .filter(RevenuePlanDetail.version_id.in_(version_ids))
            .scalar()
        ) if version_ids else 0

        # Sum actual revenue for this month
        actual = (
            db.query(func.coalesce(func.sum(RevenueActual.actual_amount), 0))
            .filter(
                RevenueActual.year == year,
                RevenueActual.month == month,
                RevenueActual.department_id == target_department_id
            )
            .scalar()
        )

        monthly_data.append({
            "month": month,
            "month_name": [
                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
            ][month - 1],
            "planned": float(planned or 0),
            "actual": float(actual or 0),
            "variance": float((actual or 0) - (planned or 0)),
        })

    log_info(
        f"Get monthly trends - user_id: {current_user.id}, year: {year}, "
        f"department_id: {target_department_id}",
        "revenue_analytics"
    )

    return {
        "year": year,
        "department_id": target_department_id,
        "monthly_data": monthly_data,
    }


@router.get("/top-performers")
def get_top_performers(
    year: int = Query(..., description="Year for analysis"),
    limit: int = Query(5, description="Number of top items to return", ge=1, le=20),
    department_id: Optional[int] = Query(None, description="Department ID (MANAGER/ADMIN only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get top performing regions and categories by actual revenue
    """
    # Determine department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    else:
        target_department_id = department_id if department_id is not None else current_user.department_id

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Top regions (revenue streams)
    top_regions = (
        db.query(
            RevenueStream.id,
            RevenueStream.name,
            func.sum(RevenueActual.actual_amount).label("total_revenue")
        )
        .join(RevenueActual, RevenueActual.revenue_stream_id == RevenueStream.id)
        .filter(
            RevenueActual.year == year,
            RevenueActual.department_id == target_department_id,
            RevenueStream.department_id == target_department_id
        )
        .group_by(RevenueStream.id, RevenueStream.name)
        .order_by(func.sum(RevenueActual.actual_amount).desc())
        .limit(limit)
        .all()
    )

    # Top categories
    top_categories = (
        db.query(
            RevenueCategory.id,
            RevenueCategory.name,
            func.sum(RevenueActual.actual_amount).label("total_revenue")
        )
        .join(RevenueActual, RevenueActual.revenue_category_id == RevenueCategory.id)
        .filter(
            RevenueActual.year == year,
            RevenueActual.department_id == target_department_id,
            RevenueCategory.department_id == target_department_id
        )
        .group_by(RevenueCategory.id, RevenueCategory.name)
        .order_by(func.sum(RevenueActual.actual_amount).desc())
        .limit(limit)
        .all()
    )

    log_info(
        f"Get top performers - user_id: {current_user.id}, year: {year}, "
        f"department_id: {target_department_id}, limit: {limit}",
        "revenue_analytics"
    )

    return {
        "year": year,
        "department_id": target_department_id,
        "top_regions": [
            {
                "id": r.id,
                "name": r.name,
                "total_revenue": float(r.total_revenue or 0),
            }
            for r in top_regions
        ],
        "top_categories": [
            {
                "id": c.id,
                "name": c.name,
                "total_revenue": float(c.total_revenue or 0),
            }
            for c in top_categories
        ],
    }
