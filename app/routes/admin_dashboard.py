from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.models.activity import ActivityLog
from app.schemas.admin import DashboardStats, RevenueChartData, RevenueDataPoint, RecentActivityResponse, ActivityItem
from app.core.admin_dependencies import get_current_admin

router = APIRouter(prefix="/api/admin/dashboard", tags=["Admin Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get dashboard statistics: total users, engagement rate, revenue"""
    # Total users
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = total_users - active_users
    
    # Engagement rate (active users / total users * 100)
    engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
    
    # Subscription stats
    total_subscriptions = db.query(UserSubscription).count()
    active_subscriptions = db.query(UserSubscription).filter(
        UserSubscription.status == "active",
        UserSubscription.end_date >= datetime.utcnow()
    ).count()
    
    # Monthly revenue (current month)
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = db.query(func.sum(UserSubscription.payment_amount)).filter(
        UserSubscription.created_at >= current_month_start
    ).scalar() or 0
    
    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        engagement_rate=round(engagement_rate, 2),
        monthly_revenue=round(monthly_revenue, 2),
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions
    )


@router.get("/revenue-chart", response_model=RevenueChartData)
async def get_revenue_chart(
    months: int = Query(default=12, ge=1, le=24),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get revenue data for chart visualization"""
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    data = []
    total_revenue = 0
    current_date = datetime.utcnow()
    
    for i in range(months - 1, -1, -1):
        # Calculate month start and end
        target_date = current_date - timedelta(days=30 * i)
        month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if target_date.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        # Get revenue for this month
        revenue = db.query(func.sum(UserSubscription.payment_amount)).filter(
            UserSubscription.created_at >= month_start,
            UserSubscription.created_at < month_end
        ).scalar() or 0
        
        data.append(RevenueDataPoint(
            month=month_names[month_start.month - 1],
            revenue=round(revenue, 2)
        ))
        total_revenue += revenue
    
    # Calculate growth percentage (compare last two months)
    growth_percentage = 0
    if len(data) >= 2 and data[-2].revenue > 0:
        growth_percentage = ((data[-1].revenue - data[-2].revenue) / data[-2].revenue) * 100
    
    return RevenueChartData(
        data=data,
        total_revenue=round(total_revenue, 2),
        growth_percentage=round(growth_percentage, 2)
    )


@router.get("/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get recent user activities"""
    # Get recent activities with user info
    activities = db.query(ActivityLog).order_by(
        ActivityLog.created_at.desc()
    ).limit(limit).all()
    
    total_count = db.query(ActivityLog).count()
    
    activity_items = []
    for activity in activities:
        user_email = None
        if activity.user_id:
            user = db.query(User).filter(User.id == activity.user_id).first()
            user_email = user.email if user else None
        
        activity_items.append(ActivityItem(
            id=activity.id,
            action=activity.action,
            description=activity.description,
            user_email=user_email,
            created_at=activity.created_at
        ))
    
    return RecentActivityResponse(
        activities=activity_items,
        total_count=total_count
    )
