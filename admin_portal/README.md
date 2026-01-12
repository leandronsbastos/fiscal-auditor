# Portal Administrativo ETL

Portal web para gerenciamento de processos ETL (Extract, Transform, Load) com interface moderna e intuitiva.

## 🚀 Funcionalidades

### 📊 Dashboard
- **KPIs em tempo real**: Processos executados, taxa de sucesso, tempo médio
- **Gráficos interativos**: Processos por hora, status, performance
- **Monitoramento de recursos**: CPU, memória, disco
- **Processos recentes**: Visualização dos últimos processamentos
- **Jobs ativos**: Status dos agendamentos em execução

### 📁 Gerenciamento de Pastas
- **Configuração de diretórios**: Entrada, processamento, sucesso, erro
- **Teste de permissões**: Validação automática de leitura/escrita
- **Monitoramento de espaço**: Alertas de disco cheio
- **Fila de arquivos**: Visualização de arquivos aguardando processamento

### ⏰ Agendamento (Scheduler)
- **Múltiplos tipos de trigger**: Cron, intervalo, data específica
- **Configuração flexível**: Paralelismo, timeout, retry
- **Execução manual**: Trigger sob demanda
- **Histórico completo**: Sucessos, falhas, tempo de execução
- **Pausar/retomar jobs**: Controle granular

### 📝 Logs e Monitoramento
- **Filtros avançados**: Por nível, data, módulo, arquivo
- **Busca em tempo real**: WebSocket para atualizações live
- **Exportação**: CSV, JSON
- **Métricas detalhadas**: Performance, erros, throughput
- **Alertas automáticos**: Notificações de falhas

### ⚙️ Processos ETL
- **Visualização detalhada**: Status, duração, registros processados
- **Rastreamento de erros**: Stack traces, mensagens
- **Estatísticas por job**: Taxa de sucesso, tempo médio
- **Reprocessamento**: Executar novamente arquivos com erro

## 🏗️ Arquitetura

```
admin_portal/
├── app_admin.py           # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── models/                # Modelos de banco de dados
│   ├── __init__.py
│   └── admin_models.py    # FolderConfig, SchedulerJob, ETLProcess, SystemLog
├── routes/                # Endpoints da API
│   ├── __init__.py
│   ├── folder_routes.py   # Gerenciamento de pastas
│   ├── scheduler_routes.py # Jobs agendados
│   ├── etl_routes.py      # Processos ETL
│   └── log_routes.py      # Logs e monitoramento
├── services/              # Lógica de negócio
├── templates/             # Templates HTML
│   ├── base.html          # Layout base
│   ├── dashboard.html     # Dashboard principal
│   ├── folders.html       # Configuração de pastas
│   ├── scheduler.html     # Gerenciamento de jobs
│   ├── processes.html     # Visualização de processos
│   └── logs.html          # Logs e monitoramento
└── static/                # Assets estáticos
    ├── css/
    │   └── admin.css      # Estilos customizados
    └── js/
        └── admin.js       # JavaScript principal
```

## 🛠️ Tecnologias

- **Backend**: Flask 3.0
- **Database**: PostgreSQL + SQLAlchemy
- **Scheduler**: APScheduler
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js 4.4
- **Icons**: Font Awesome 6.4
- **Fonts**: Inter (Google Fonts)

## 📦 Instalação

1. **Instalar dependências**:
```bash
cd admin_portal
pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente**:
```bash
# Windows PowerShell
$env:ADMIN_DATABASE_URL = "postgresql://user:pass@localhost:5432/fiscal_datalake"
$env:SECRET_KEY = "your-secret-key-here"

# Linux/Mac
export ADMIN_DATABASE_URL="postgresql://user:pass@localhost:5432/fiscal_datalake"
export SECRET_KEY="your-secret-key-here"
```

3. **Inicializar banco de dados**:
O banco de dados é criado automaticamente na primeira execução.

4. **Executar aplicação**:
```bash
python app_admin.py
```

5. **Acessar portal**:
```
http://localhost:5001
```

## 🔧 Configuração

### Banco de Dados
O portal utiliza o mesmo banco PostgreSQL do sistema fiscal-auditor. As tabelas são criadas automaticamente:

- `folder_config`: Configuração de pastas
- `scheduler_jobs`: Jobs agendados
- `etl_processes`: Histórico de processos
- `system_logs`: Logs do sistema
- `system_metrics`: Métricas de performance

### Scheduler
Jobs são configurados via interface web e executam automaticamente:

```python
# Exemplo de job cron (todo dia às 2h)
{
    "name": "ETL Diário",
    "job_type": "cron",
    "cron_expression": "0 2 * * *",
    "max_instances": 1,
    "timeout_seconds": 3600
}

# Exemplo de job intervalo (a cada 30 minutos)
{
    "name": "ETL Frequente",
    "job_type": "interval",
    "interval_seconds": 1800,
    "max_instances": 3
}
```

## 📡 API Endpoints

### Sistema
- `GET /api/system/health` - Health check
- `GET /api/system/metrics?hours=24` - Métricas do sistema

### Pastas
- `GET /api/folders/config` - Buscar configuração
- `POST /api/folders/config` - Salvar configuração
- `POST /api/folders/test-permissions` - Testar permissões

### Scheduler
- `GET /api/scheduler/jobs` - Listar jobs
- `POST /api/scheduler/jobs` - Criar job
- `PUT /api/scheduler/jobs/<id>` - Atualizar job
- `DELETE /api/scheduler/jobs/<id>` - Deletar job
- `POST /api/scheduler/jobs/<id>/run` - Executar manualmente

### Processos ETL
- `GET /api/etl/processes` - Listar processos
- `GET /api/etl/processes/<id>` - Detalhes do processo
- `DELETE /api/etl/processes/<id>` - Deletar processo

### Logs
- `GET /api/logs?level=ERROR&hours=24` - Buscar logs
- `GET /api/logs/export` - Exportar logs
- `GET /api/logs/stream` - Stream em tempo real (WebSocket)

## 🎨 Customização

### Temas
O portal suporta customização de cores via CSS variables em `static/css/admin.css`:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #43e97b;
    --danger-color: #f5576c;
    /* ... */
}
```

### Gráficos
Personalize gráficos Chart.js em cada template:

```javascript
// Exemplo em dashboard.html
new Chart(ctx, {
    type: 'line',
    data: { /* ... */ },
    options: { /* Customize aqui */ }
});
```

## 🔒 Segurança

- **JWT Authentication**: Em desenvolvimento
- **RBAC**: Role-Based Access Control em desenvolvimento
- **Audit Log**: Todas alterações são registradas
- **Path Validation**: Validação de caminhos de arquivo
- **Input Sanitization**: Proteção contra XSS e SQL Injection

## 📊 Monitoramento

O portal monitora automaticamente:
- **CPU**: Uso de processador
- **Memória**: RAM disponível/utilizada
- **Disco**: Espaço livre em todas as partições
- **Processos ETL**: Status, duração, sucesso/falha
- **Jobs**: Execuções, próxima execução, histórico

## 🐛 Troubleshooting

### Porta já em uso
```bash
# Alterar porta no app_admin.py, linha final:
app.run(port=5002)  # Trocar 5001 por outra porta
```

### Erro de conexão com banco
Verifique a string de conexão e se o PostgreSQL está rodando:
```bash
psql -U postgres -d fiscal_datalake -c "SELECT 1"
```

### Jobs não executam
Verifique logs em `admin_portal/logs/etl_admin.log`:
```bash
tail -f admin_portal/logs/etl_admin.log
```

## 🚀 Próximas Funcionalidades

- [ ] Autenticação JWT completa
- [ ] Notificações por email
- [ ] Dashboard em tempo real com WebSocket
- [ ] Backup automático de configurações
- [ ] Dark/Light theme toggle
- [ ] Internacionalização (PT/EN/ES)
- [ ] API GraphQL
- [ ] Mobile app

## 📝 Licença

Este projeto é parte do sistema Fiscal Auditor.

## 👥 Suporte

Para suporte e dúvidas, consulte a documentação principal do projeto.

---

**Desenvolvido com ❤️ para simplificar a gestão de processos ETL**
