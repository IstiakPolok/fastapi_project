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
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get daily revenue data for the previous month and current month to date"""
    current_date = datetime.utcnow()
    # Start of last month
    if current_date.month == 1:
        start_date = current_date.replace(year=current_date.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = current_date.replace(month=current_date.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get all subscription records from start_date
    subscriptions = db.query(
        func.date(UserSubscription.created_at).label("day"),
        func.sum(UserSubscription.payment_amount).label("revenue")
    ).filter(
        UserSubscription.created_at >= start_date,
        UserSubscription.payment_status == "completed"
    ).group_by(
        func.date(UserSubscription.created_at)
    ).all()
    
    # Map results to a dictionary for easy access
    revenue_map = {str(s.day): s.revenue for s in subscriptions}
    
    data = []
    total_revenue = 0
    
    # Iterate through each day from start_date to today
    delta = current_date - start_date
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        revenue = revenue_map.get(day_str, 0) or 0
        
        data.append(RevenueDataPoint(
            date=day_str,
            revenue=round(revenue, 2)
        ))
        total_revenue += revenue
        
    # Calculate current month start for filtering
    current_month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Filter into last month and this month
    last_month_data = [p for p in data if datetime.strptime(p.date, "%Y-%m-%d") < current_month_start]
    this_month_data = [p for p in data if datetime.strptime(p.date, "%Y-%m-%d") >= current_month_start]
    
    # Calculate growth percentage
    last_month_revenue = sum(p.revenue for p in last_month_data)
    current_month_revenue = sum(p.revenue for p in this_month_data)
    
    growth_percentage = 0
    if last_month_revenue > 0:
        growth_percentage = ((current_month_revenue / last_month_revenue) - 1) * 100
    elif current_month_revenue > 0:
        growth_percentage = 100
    
    return RevenueChartData(
        last_month_data=last_month_data,
        this_month_data=this_month_data,
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
