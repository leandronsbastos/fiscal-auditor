"""
Modelos de banco de dados para o Portal Administrativo - usando importação do db
"""
# Este arquivo será renomeado para substituir admin_models.py
# Agora os modelos receberão o db como parâmetro

def create_models(db):
    """
    Cria os modelos usando a instância db do Flask-SQLAlchemy
    """
    from datetime import datetime
    import json
    
    class FolderConfig(db.Model):
        """Configuração de pastas do sistema ETL"""
        __tablename__ = 'folder_config'
        
        id = db.Column(db.Integer, primary_key=True)
        input_path = db.Column(db.String(500), nullable=False)
        processing_path = db.Column(db.String(500), nullable=False)
        success_path = db.Column(db.String(500), nullable=False)
        error_path = db.Column(db.String(500), nullable=False)
        rejected_path = db.Column(db.String(500), nullable=True)
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.now)
        updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
        
        def to_dict(self):
            return {
                'id': self.id,
                'input_path': self.input_path,
                'processing_path': self.processing_path,
                'success_path': self.success_path,
                'error_path': self.error_path,
                'rejected_path': self.rejected_path,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }

    class SchedulerJob(db.Model):
        """Configuração de jobs agendados"""
        __tablename__ = 'scheduler_jobs'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(200), nullable=False, unique=True)
        job_type = db.Column(db.String(50), nullable=False)
        cron_expression = db.Column(db.String(100), nullable=True)
        interval_seconds = db.Column(db.Integer, nullable=True)
        scheduled_time = db.Column(db.DateTime, nullable=True)
        is_active = db.Column(db.Boolean, default=True)
        max_instances = db.Column(db.Integer, default=1)
        timeout_seconds = db.Column(db.Integer, default=3600)
        retry_count = db.Column(db.Integer, default=3)
        retry_delay_seconds = db.Column(db.Integer, default=60)
        last_run = db.Column(db.DateTime, nullable=True)
        next_run = db.Column(db.DateTime, nullable=True)
        run_count = db.Column(db.Integer, default=0)
        success_count = db.Column(db.Integer, default=0)
        failure_count = db.Column(db.Integer, default=0)
        config_json = db.Column(db.Text, nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.now)
        updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
        
        def to_dict(self):
            return {
                'id': self.id,
                'name': self.name,
                'job_type': self.job_type,
                'cron_expression': self.cron_expression,
                'interval_seconds': self.interval_seconds,
                'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
                'is_active': self.is_active,
                'max_instances': self.max_instances,
                'timeout_seconds': self.timeout_seconds,
                'retry_count': self.retry_count,
                'retry_delay_seconds': self.retry_delay_seconds,
                'last_run': self.last_run.isoformat() if self.last_run else None,
                'next_run': self.next_run.isoformat() if self.next_run else None,
                'run_count': self.run_count,
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'config': json.loads(self.config_json) if self.config_json else {},
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }

    class ETLProcess(db.Model):
        """Registro de processos ETL executados"""
        __tablename__ = 'etl_processes'
        
        id = db.Column(db.Integer, primary_key=True)
        job_id = db.Column(db.Integer, nullable=True)
        filename = db.Column(db.String(500), nullable=False)
        filepath = db.Column(db.String(1000), nullable=True)
        status = db.Column(db.String(50), nullable=False)
        start_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
        end_time = db.Column(db.DateTime, nullable=True)
        duration_seconds = db.Column(db.Float, nullable=True)
        records_processed = db.Column(db.Integer, default=0)
        records_inserted = db.Column(db.Integer, default=0)
        records_updated = db.Column(db.Integer, default=0)
        records_skipped = db.Column(db.Integer, default=0)
        records_error = db.Column(db.Integer, default=0)
        error_message = db.Column(db.Text, nullable=True)
        error_traceback = db.Column(db.Text, nullable=True)
        metadata_json = db.Column(db.Text, nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.now)
        
        def to_dict(self):
            return {
                'id': self.id,
                'job_id': self.job_id,
                'filename': self.filename,
                'filepath': self.filepath,
                'status': self.status,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_seconds': self.duration_seconds,
                'records_processed': self.records_processed,
                'records_inserted': self.records_inserted,
                'records_updated': self.records_updated,
                'records_skipped': self.records_skipped,
                'records_error': self.records_error,
                'error_message': self.error_message,
                'metadata': json.loads(self.metadata_json) if self.metadata_json else {},
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

    class SystemLog(db.Model):
        """Logs do sistema"""
        __tablename__ = 'system_logs'
        
        id = db.Column(db.Integer, primary_key=True)
        timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
        level = db.Column(db.String(20), nullable=False, index=True)
        module = db.Column(db.String(100), nullable=False, index=True)
        function_name = db.Column(db.String(100), nullable=True)
        message = db.Column(db.Text, nullable=False)
        details_json = db.Column(db.Text, nullable=True)
        user_id = db.Column(db.Integer, nullable=True)
        ip_address = db.Column(db.String(50), nullable=True)
        process_id = db.Column(db.Integer, nullable=True)
        
        def to_dict(self):
            return {
                'id': self.id,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'level': self.level,
                'module': self.module,
                'function_name': self.function_name,
                'message': self.message,
                'details': json.loads(self.details_json) if self.details_json else {},
                'user_id': self.user_id,
                'ip_address': self.ip_address,
                'process_id': self.process_id
            }

    class SystemMetrics(db.Model):
        """Métricas do sistema"""
        __tablename__ = 'system_metrics'
        
        id = db.Column(db.Integer, primary_key=True)
        timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
        metric_type = db.Column(db.String(50), nullable=False, index=True)
        metric_name = db.Column(db.String(100), nullable=False)
        metric_value = db.Column(db.Float, nullable=False)
        unit = db.Column(db.String(20), nullable=True)
        tags_json = db.Column(db.Text, nullable=True)
        
        def to_dict(self):
            return {
                'id': self.id,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'metric_type': self.metric_type,
                'metric_name': self.metric_name,
                'metric_value': self.metric_value,
                'unit': self.unit,
                'tags': json.loads(self.tags_json) if self.tags_json else {}
            }
    
    return {
        'FolderConfig': FolderConfig,
        'SchedulerJob': SchedulerJob,
        'ETLProcess': ETLProcess,
        'SystemLog': SystemLog,
        'SystemMetrics': SystemMetrics
    }
