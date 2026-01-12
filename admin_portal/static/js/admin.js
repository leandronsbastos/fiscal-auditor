// Admin Portal JavaScript
// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    }[type] || 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove após 5 segundos
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Formatação de data
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

// Formatação de duração
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

// Formatação de tamanho de arquivo
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB';
    else return (bytes / 1073741824).toFixed(2) + ' GB';
}

// Confirmação de ação
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Copiar para clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copiado para a área de transferência', 'success');
    }).catch(err => {
        showToast('Erro ao copiar', 'error');
    });
}

// Exportar dados como CSV
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const rows = data.map(row => 
        headers.map(header => {
            const value = row[header];
            return typeof value === 'string' && value.includes(',') 
                ? `"${value}"` 
                : value;
        }).join(',')
    );
    
    return [headers.join(','), ...rows].join('\n');
}

// Debounce para busca
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Loading overlay
function showLoading() {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    `;
    overlay.innerHTML = '<div style="color: white; font-size: 24px;"><i class="fas fa-spinner fa-spin"></i> Carregando...</div>';
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Refresh chart
function refreshChart(chartId) {
    showToast('Atualizando gráfico...', 'info');
    // Recarregar dados do gráfico específico
    window.location.reload();
}

// View process details
function viewProcess(id) {
    window.location.href = `/processes/${id}`;
}

// Delete process
function deleteProcess(id) {
    confirmAction('Tem certeza que deseja excluir este processo?', async () => {
        try {
            const response = await fetch(`/api/etl/processes/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showToast('Processo excluído com sucesso', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                throw new Error('Erro ao excluir processo');
            }
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

// Run job manually
async function runJobManually(jobId) {
    try {
        showLoading();
        const response = await fetch(`/api/scheduler/jobs/${jobId}/run`, {
            method: 'POST'
        });
        
        hideLoading();
        
        if (response.ok) {
            showToast('Job executado com sucesso', 'success');
            setTimeout(() => window.location.reload(), 2000);
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Erro ao executar job');
        }
    } catch (error) {
        hideLoading();
        showToast(error.message, 'error');
    }
}

// Toggle job status
async function toggleJobStatus(jobId, currentStatus) {
    try {
        const response = await fetch(`/api/scheduler/jobs/${jobId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_active: !currentStatus
            })
        });
        
        if (response.ok) {
            showToast(`Job ${!currentStatus ? 'ativado' : 'desativado'} com sucesso`, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error('Erro ao atualizar status do job');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Initialize tooltips (se usar biblioteca de tooltips)
document.addEventListener('DOMContentLoaded', () => {
    // Adicionar listeners globais aqui
    console.log('Admin Portal carregado');
});
