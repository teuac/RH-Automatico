import datetime
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.obra import Obra
from app.models.user import User
from app.models.upload import Upload
from app.models.pending_record import PendingRecord
from app.auth.rbac import get_active_user

class DashboardController:
    @staticmethod
    def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
        # Count Obras
        total_obras = db.query(Obra).filter(Obra.status == "ATIVO").count()
        
        # Uploads today
        today = datetime.datetime.utcnow().date()
        start_of_day = datetime.datetime.combine(today, datetime.time.min)
        uploads_today = db.query(Upload).filter(Upload.created_at >= start_of_day).count()
        
        # Pending count
        pending_count = db.query(PendingRecord).filter(PendingRecord.status == "PENDENTE").count()
        
        # Active users count
        active_users = db.query(User).filter(User.status == "ATIVO").count()
        
        # Last upload
        last_upload = db.query(Upload).order_by(Upload.created_at.desc()).first()
        last_processing_time = last_upload.processing_time_ms if last_upload else 0.0
        
        # Upload graph: daily uploads for last 7 days
        seven_days_ago = today - datetime.timedelta(days=7)
        daily_stats = (
            db.query(
                func.date(Upload.created_at).label("day"),
                func.count(Upload.id).label("count")
            )
            .filter(Upload.created_at >= datetime.datetime.combine(seven_days_ago, datetime.time.min))
            .group_by(func.date(Upload.created_at))
            .order_by(func.date(Upload.created_at))
            .all()
        )
        
        graph_data = [
            {"date": str(day), "uploads": count}
            for day, count in daily_stats
        ]

        return {
            "total_obras": total_obras,
            "uploads_today": uploads_today,
            "pending_count": pending_count,
            "active_users": active_users,
            "last_processing_time": last_processing_time,
            "upload_graph": graph_data
        }

dashboard_controller = DashboardController()
