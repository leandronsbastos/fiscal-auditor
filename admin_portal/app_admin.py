"""
Portal Administrativo ETL - Aplicação Principal
Sistema de gerenciamento de processos ETL com interface web
"""
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from threading import Thread
import logging
import os
import sys
import psutil
import json

# Adicionar path do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Criar diretório de logs se não existir
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'etl_admin.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicialização do Flask
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'ADMIN_DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/fiscal_datalake'
)
app.config['SQLALCHEMY_BINDS'] = {
    'fiscal_auditor': os.environ.get(
        'FISCAL_AUDITOR_DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/fiscal_auditor'
    )
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# Extensões
CORS(app)
db = SQLAlchemy(app)

# Criar modelos
from admin_portal.models.models import create_models
from admin_portal.models.fiscal_auditor_models import create_models as create_fiscal_models

models = create_models(db)
FolderConfig = models['FolderConfig']
SchedulerJob = models['SchedulerJob']
ETLProcess = models['ETLProcess']
SystemLog = models['SystemLog']
SystemMetrics = models['SystemMetrics']

# Modelos do fiscal_auditor
fiscal_models = create_fiscal_models(db)
Empresa = fiscal_models['Empresa']
Usuario = fiscal_models['Usuario']
UsuarioEmpresa = fiscal_models['UsuarioEmpresa']

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Importar rotas
from admin_portal.routes import folder_routes, scheduler_routes, etl_routes, log_routes
from admin_portal.routes.empresa_routes import init_empresa_routes
from admin_portal.routes.empresas import empresas_bp, init_models

# Inicializar modelos nas rotas
init_models(db, Empresa, Usuario, UsuarioEmpresa)

# Registrar blueprint de empresas
app.register_blueprint(empresas_bp)


# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
def index():
    """Página principal - Dashboard"""
    return render_template('dashboard.html')


@app.route('/folders')
def folders_page():
    """Página de configuração de pastas"""
    return render_template('folders.html')


@app.route('/scheduler')
def scheduler_page():
    """Página de agendamentos"""
    return render_template('scheduler.html')


@app.route('/processes')
def processes_page():
    """Página de processos ETL"""
    return render_template('processes.html')


@app.route('/logs')
def logs_page():
    """Página de visualização de logs"""
    return render_template('logs.html')


@app.route('/settings')
def settings_page():
    """Página de configurações do sistema"""
    return render_template('settings.html')


# ==================== API SISTEMA ====================

@app.route('/api/system/health', methods=['GET'])
def system_health():
    """Health check do sistema"""
    try:
        # CPU e Memória
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Contadores do banco
        total_processes = db.session.query(ETLProcess).count()
        active_jobs = db.session.query(SchedulerJob).filter_by(is_active=True).count()
        recent_errors = db.session.query(SystemLog).filter(
            SystemLog.level == 'ERROR',
            SystemLog.timestamp >= datetime.now() - timedelta(hours=24)
        ).count()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            },
            'etl': {
                'total_processes': total_processes,
                'active_jobs': active_jobs,
                'recent_errors': recent_errors
            }
        })
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/api/system/metrics', methods=['GET'])
def system_metrics():
    """Métricas do sistema"""
    try:
        # Parâmetros de filtro
        hours = request.args.get('hours', default=24, type=int)
        since = datetime.now() - timedelta(hours=hours)
        
        # Processos por hora
        processes_by_hour = db.session.query(
            db.func.date_trunc('hour', ETLProcess.start_time).label('hour'),
            db.func.count(ETLProcess.id).label('count'),
            db.func.sum(db.case((ETLProcess.status == 'success', 1), else_=0)).label('success'),
            db.func.sum(db.case((ETLProcess.status == 'error', 1), else_=0)).label('errors')
        ).filter(
            ETLProcess.start_time >= since
        ).group_by('hour').order_by('hour').all()
        
        # Tempo médio de processamento
        avg_duration = db.session.query(
            db.func.avg(ETLProcess.duration_seconds)
        ).filter(
            ETLProcess.start_time >= since,
            ETLProcess.status == 'success'
        ).scalar() or 0
        
        # Top erros
        top_errors = db.session.query(
            ETLProcess.error_message,
            db.func.count(ETLProcess.id).label('count')
        ).filter(
            ETLProcess.start_time >= since,
            ETLProcess.status == 'error'
        ).group_by(ETLProcess.error_message).order_by(db.desc('count')).limit(5).all()
        
        return jsonify({
            'period_hours': hours,
            'processes_by_hour': [
                {
                    'hour': p.hour.isoformat(),
                    'total': p.count,
                    'success': p.success,
                    'errors': p.errors
                } for p in processes_by_hour
            ],
            'avg_duration_seconds': round(avg_duration, 2),
            'top_errors': [
                {
                    'message': e.error_message[:100] if e.error_message else 'Unknown',
                    'count': e.count
                } for e in top_errors
            ]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== API FOLDERS ====================

@app.route('/api/folders/config', methods=['GET'])
def get_folder_config():
    """Retorna configuração atual de pastas"""
    try:
        config = db.session.query(FolderConfig).filter_by(is_active=True).first()
        if config:
            return jsonify(config.to_dict())
        return jsonify({'message': 'Nenhuma configuração encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar configuração de pastas: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/folders/config', methods=['POST'])
def save_folder_config():
    """Salva configuração de pastas"""
    try:
        data = request.json
        
        # Desativar configurações antigas
        db.session.query(FolderConfig).update({'is_active': False})
        
        # Criar nova configuração
        config = FolderConfig(
            input_path=data.get('input_path'),
            processing_path=data.get('processing_path'),
            success_path=data.get('success_path'),
            error_path=data.get('error_path'),
            rejected_path=data.get('rejected_path'),
            is_active=True
        )
        
        db.session.add(config)
        db.session.commit()
        
        # Log
        log = SystemLog(
            level='INFO',
            module='folder_config',
            message=f'Configuração de pastas atualizada',
            details_json=json.dumps(data)
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(config.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar configuração: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/folders/test-permissions', methods=['POST'])
def test_folder_permissions():
    """Testa permissões de acesso às pastas"""
    try:
        data = request.json
        results = {}
        
        for key in ['input_path', 'processing_path', 'success_path', 'error_path']:
            path = data.get(key)
            if path:
                results[key] = {
                    'exists': os.path.exists(path),
                    'readable': os.access(path, os.R_OK) if os.path.exists(path) else False,
                    'writable': os.access(path, os.W_OK) if os.path.exists(path) else False
                }
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Erro ao testar permissões: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/folders/browse', methods=['POST'])
def browse_folders():
    """Lista diretórios para navegação"""
    try:
        data = request.json
        current_path = data.get('path', '')
        
        # Se path vazio, listar drives (Windows)
        if not current_path:
            if os.name == 'nt':  # Windows
                import string
                drives = []
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        drives.append({
                            'name': drive,
                            'path': drive,
                            'type': 'drive',
                            'icon': 'hdd'
                        })
                return jsonify({
                    'current': '',
                    'parent': None,
                    'items': drives
                })
            else:  # Linux/Mac
                current_path = '/'
        
        # Verificar se o caminho existe
        if not os.path.exists(current_path):
            return jsonify({'error': 'Caminho não encontrado'}), 404
        
        # Listar itens do diretório
        items = []
        try:
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    try:
                        # Verificar se tem permissão de leitura
                        os.listdir(item_path)
                        has_permission = True
                    except PermissionError:
                        has_permission = False
                    
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': 'folder',
                        'icon': 'folder',
                        'accessible': has_permission
                    })
        except PermissionError:
            return jsonify({'error': 'Sem permissão para acessar este diretório'}), 403
        
        # Ordenar pastas alfabeticamente
        items.sort(key=lambda x: x['name'].lower())
        
        # Caminho pai
        parent_path = os.path.dirname(current_path) if current_path else None
        
        return jsonify({
            'current': current_path,
            'parent': parent_path,
            'items': items
        })
    except Exception as e:
        logger.error(f"Erro ao navegar pastas: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/folders/create', methods=['POST'])
def create_folder():
    """Cria um novo diretório"""
    try:
        data = request.json
        folder_path = data.get('path')
        
        if not folder_path:
            return jsonify({'error': 'Caminho não fornecido'}), 400
        
        os.makedirs(folder_path, exist_ok=True)
        
        return jsonify({
            'message': 'Pasta criada com sucesso',
            'path': folder_path
        })
    except Exception as e:
        logger.error(f"Erro ao criar pasta: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== API SCHEDULER ====================

@app.route('/api/scheduler/jobs', methods=['GET'])
def get_scheduler_jobs():
    """Lista todos os jobs agendados"""
    try:
        active_only = request.args.get('active') == 'true'
        
        query = db.session.query(SchedulerJob)
        if active_only:
            query = query.filter_by(is_active=True)
        
        jobs = query.order_by(SchedulerJob.name).all()
        return jsonify([job.to_dict() for job in jobs])
    except Exception as e:
        logger.error(f"Erro ao listar jobs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scheduler/jobs', methods=['POST'])
def create_scheduler_job():
    """Cria um novo job agendado"""
    try:
        data = request.json
        logger.info(f"Dados recebidos para criar job: {data}")
        
        # Validar campos obrigatórios
        if not data.get('name'):
            return jsonify({'error': 'Nome do job é obrigatório'}), 400
        
        # Validar tipo de job
        job_type = data.get('job_type')
        if job_type not in ['cron', 'interval']:
            return jsonify({'error': 'Tipo de job inválido. Use "cron" ou "interval"'}), 400
        
        # Validar parâmetros específicos
        if job_type == 'interval':
            interval_seconds = data.get('interval_seconds')
            if not interval_seconds or int(interval_seconds) < 60:
                return jsonify({'error': 'Intervalo mínimo é 60 segundos'}), 400
        elif job_type == 'cron':
            if not data.get('cron_expression'):
                return jsonify({'error': 'Expressão cron é obrigatória'}), 400
        
        # Criar job
        job = SchedulerJob(
            name=data.get('name'),
            job_type=job_type,
            cron_expression=data.get('cron_expression') if job_type == 'cron' else None,
            interval_seconds=data.get('interval_seconds') if job_type == 'interval' else None,
            is_active=data.get('is_active', True),
            max_instances=data.get('max_instances', 1),
            timeout_seconds=data.get('timeout_seconds', 3600),
            retry_count=data.get('retry_count', 3),
            retry_delay_seconds=data.get('retry_delay_seconds', 60),
            config_json=json.dumps(data.get('config', {}))
        )
        
        db.session.add(job)
        db.session.commit()
        
        logger.info(f"Job '{job.name}' criado no banco com ID {job.id}")
        
        # Adicionar ao scheduler se estiver ativo
        if job.is_active:
            try:
                add_scheduler_job(job)
                logger.info(f"Job '{job.name}' adicionado ao scheduler")
            except Exception as e:
                logger.error(f"Erro ao adicionar job ao scheduler: {str(e)}")
                # Não falha a criação do job, apenas loga o erro
        
        logger.info(f"Job '{job.name}' criado com sucesso")
        return jsonify(job.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar job: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/scheduler/jobs/<int:job_id>', methods=['PUT'])
def update_scheduler_job(job_id):
    """Atualiza um job existente"""
    try:
        job = db.session.query(SchedulerJob).get(job_id)
        if not job:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        data = request.json
        
        # Atualizar campos
        if 'name' in data:
            job.name = data['name']
        if 'job_type' in data:
            job.job_type = data['job_type']
        if 'cron_expression' in data:
            job.cron_expression = data['cron_expression']
        if 'interval_seconds' in data:
            job.interval_seconds = data['interval_seconds']
        if 'is_active' in data:
            job.is_active = data['is_active']
        if 'max_instances' in data:
            job.max_instances = data['max_instances']
        if 'timeout_seconds' in data:
            job.timeout_seconds = data['timeout_seconds']
        if 'retry_count' in data:
            job.retry_count = data['retry_count']
        if 'retry_delay_seconds' in data:
            job.retry_delay_seconds = data['retry_delay_seconds']
        if 'config' in data:
            job.config_json = json.dumps(data['config'])
        
        job.updated_at = datetime.now()
        db.session.commit()
        
        # Remover do scheduler
        try:
            scheduler.remove_job(f'job_{job_id}')
        except:
            pass
        
        # Adicionar novamente se estiver ativo
        if job.is_active:
            add_scheduler_job(job)
        
        logger.info(f"Job '{job.name}' atualizado com sucesso")
        return jsonify(job.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar job: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scheduler/jobs/<int:job_id>', methods=['DELETE'])
def delete_scheduler_job(job_id):
    """Exclui um job"""
    try:
        job = db.session.query(SchedulerJob).get(job_id)
        if not job:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        job_name = job.name
        
        # Remover do scheduler
        try:
            scheduler.remove_job(f'job_{job_id}')
        except:
            pass
        
        # Remover do banco
        db.session.delete(job)
        db.session.commit()
        
        logger.info(f"Job '{job_name}' excluído com sucesso")
        return jsonify({'message': 'Job excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir job: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scheduler/jobs/<int:job_id>/run', methods=['POST'])
def run_scheduler_job_manually(job_id):
    """Executa um job manualmente"""
    try:
        job = db.session.get(SchedulerJob, job_id)
        if not job:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        # Executar em background
        from threading import Thread
        thread = Thread(target=run_etl_job, args=(job_id,))
        thread.start()
        
        logger.info(f"Job '{job.name}' iniciado manualmente")
        return jsonify({'message': 'Job iniciado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao executar job: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scheduler/jobs/<int:job_id>/toggle', methods=['POST'])
def toggle_scheduler_job(job_id):
    """Ativa/desativa um job"""
    try:
        job = db.session.query(SchedulerJob).get(job_id)
        if not job:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        job.is_active = not job.is_active
        job.updated_at = datetime.now()
        db.session.commit()
        
        # Gerenciar no scheduler
        try:
            scheduler.remove_job(f'job_{job_id}')
        except:
            pass
        
        if job.is_active:
            add_scheduler_job(job)
        
        status = 'ativado' if job.is_active else 'desativado'
        logger.info(f"Job '{job.name}' {status}")
        return jsonify(job.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao alternar job: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== API LOGS ====================

@app.route('/api/logs', methods=['GET'])
def get_system_logs():
    """Retorna logs do sistema"""
    try:
        level = request.args.get('level')
        limit = int(request.args.get('limit', 100))
        
        query = db.session.query(SystemLog).order_by(SystemLog.timestamp.desc())
        
        if level:
            query = query.filter_by(level=level)
        
        logs = query.limit(limit).all()
        return jsonify([log.to_dict() for log in logs])
    except Exception as e:
        logger.error(f"Erro ao buscar logs: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== API PROCESSOS ETL ====================

@app.route('/api/etl/processes', methods=['GET'])
def get_etl_processes():
    """Lista processos ETL"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        query = db.session.query(ETLProcess).order_by(ETLProcess.start_time.desc())
        
        if status:
            query = query.filter_by(status=status)
        
        processes = query.limit(limit).all()
        return jsonify([proc.to_dict() for proc in processes])
    except Exception as e:
        logger.error(f"Erro ao buscar processos: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/etl/processes/<int:process_id>', methods=['GET'])
def get_etl_process_detail(process_id):
    """Detalhes de um processo ETL"""
    try:
        process = db.session.query(ETLProcess).get(process_id)
        if not process:
            return jsonify({'error': 'Processo não encontrado'}), 404
        
        return jsonify(process.to_dict())
    except Exception as e:
        logger.error(f"Erro ao buscar processo: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== INICIALIZAÇÃO ====================

def init_database():
    """Inicializa o banco de dados"""
    with app.app_context():
        try:
            # Criar tabelas
            db.create_all()
            logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {str(e)}")


def load_scheduled_jobs():
    """Carrega jobs agendados do banco de dados"""
    with app.app_context():
        try:
            jobs = db.session.query(SchedulerJob).filter_by(is_active=True).all()
            for job in jobs:
                add_scheduler_job(job)
            logger.info(f"{len(jobs)} jobs carregados no scheduler")
        except Exception as e:
            logger.error(f"Erro ao carregar jobs: {str(e)}")


def add_scheduler_job(job: SchedulerJob):
    """Adiciona um job no scheduler"""
    try:
        if job.job_type == 'cron':
            trigger = CronTrigger.from_crontab(job.cron_expression)
        elif job.job_type == 'interval':
            trigger = IntervalTrigger(seconds=job.interval_seconds)
        else:
            logger.warning(f"Tipo de job desconhecido: {job.job_type}")
            return
        
        scheduler.add_job(
            func=run_etl_job,
            trigger=trigger,
            id=f'job_{job.id}',
            name=job.name,
            args=[job.id],
            max_instances=job.max_instances,
            replace_existing=True
        )
        logger.info(f"Job '{job.name}' adicionado ao scheduler")
    except Exception as e:
        logger.error(f"Erro ao adicionar job {job.name}: {str(e)}")


def run_etl_job(job_id: int):
    """Executa um job ETL"""
    with app.app_context():
        try:
            # Buscar job
            job = db.session.get(SchedulerJob, job_id)
            if not job:
                logger.error(f"Job {job_id} não encontrado")
                return
            
            logger.info(f"Iniciando execução do job: {job.name}")
            
            # Atualizar contadores
            job.last_run = datetime.now()
            job.run_count += 1
            db.session.commit()
            
            # Importar e executar ETL
            from etl_service.pipeline import ETLPipeline
            
            # Buscar configuração de pastas
            config = db.session.query(FolderConfig).filter_by(is_active=True).first()
            if not config:
                raise Exception("Nenhuma configuração de pastas ativa")
            
            # Executar pipeline
            pipeline = ETLPipeline()
            
            start_time = datetime.now()
            result = pipeline.processar_diretorio(
                diretorio=config.input_path,
                tipo_processamento='completo',
                recursivo=False
            )
            end_time = datetime.now()
            
            # Registrar processo
            process = ETLProcess(
                job_id=job_id,
                filename=f"job_{job.name}_{start_time.strftime('%Y%m%d_%H%M%S')}",
                status='success' if result.get('erros', 0) == 0 else 'error',
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                records_processed=result.get('processados', 0) + result.get('duplicados', 0),
                records_inserted=result.get('processados', 0),
                error_message=f"Erros: {result.get('erros', 0)}" if result.get('erros', 0) > 0 else None
            )
            db.session.add(process)
            
            # Atualizar job
            if result.get('erros', 0) == 0:
                job.success_count += 1
            else:
                job.failure_count += 1
            
            db.session.commit()
            logger.info(f"Job {job.name} concluído: {result.get('processados', 0)} processados, {result.get('erros', 0)} erros")
            
        except Exception as e:
            logger.error(f"Erro ao executar job {job_id}: {str(e)}", exc_info=True)
            
            # Registrar erro
            try:
                if 'job' in locals() and job:
                    job.failure_count += 1
                    db.session.commit()
                
                # Log de erro
                log = SystemLog(
                    level='ERROR',
                    module='scheduler',
                    function_name='run_etl_job',
                    message=f'Erro ao executar job {job_id}: {str(e)}',
                    details_json=json.dumps({'error': str(e), 'job_id': job_id})
                )
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                logger.error(f"Erro ao registrar erro do job: {str(log_error)}")


if __name__ == '__main__':
    # Criar diretório de logs
    os.makedirs('admin_portal/logs', exist_ok=True)
    
    # Inicializar banco de dados
    init_database()
    
    # Inicializar rotas de empresa
    init_empresa_routes(app, app.config['SQLALCHEMY_BINDS']['fiscal_auditor'])
    
    # Carregar jobs agendados
    load_scheduled_jobs()
    
    # Iniciar aplicação
    logger.info("Iniciando Portal Administrativo ETL")
    logger.info("Acesse: http://localhost:5001")
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5001,
            use_reloader=False  # Desabilitar reloader para não duplicar o scheduler
        )
    except KeyboardInterrupt:
        logger.info("Encerrando Portal Administrativo ETL")
        scheduler.shutdown()
