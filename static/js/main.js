// Main JavaScript for FTA Origin Determination Tool

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // File upload preview functionality
    initFileUpload();
    
    // Analysis progress tracking
    initAnalysisProgress();
    
    // Initialize tooltips
    initTooltips();
});

function initFileUpload() {
    const fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) return;
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            validateFile(file);
            showFilePreview(file);
        }
    });
}

function validateFile(file) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel', // .xls
        'text/csv' // .csv
    ];
    
    if (file.size > maxSize) {
        showAlert('File size exceeds 16MB limit. Please choose a smaller file.', 'warning');
        return false;
    }
    
    if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().match(/\.(xlsx|xls|csv)$/)) {
        showAlert('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'warning');
        return false;
    }
    
    return true;
}

function showFilePreview(file) {
    const preview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    
    if (preview && fileName && fileSize) {
        fileName.textContent = file.name;
        fileSize.textContent = `Size: ${(file.size / 1024 / 1024).toFixed(2)} MB`;
        preview.style.display = 'block';
    }
}

function initAnalysisProgress() {
    // Auto-refresh for incomplete analyses
    const progressIndicator = document.querySelector('.spinner-border');
    const analysisStatus = document.querySelector('[data-analysis-status]');
    
    if (progressIndicator && analysisStatus) {
        // Set up periodic status checking
        const sessionId = analysisStatus.dataset.sessionId;
        if (sessionId) {
            checkAnalysisStatus(sessionId);
        }
    }
}

function checkAnalysisStatus(sessionId) {
    fetch(`/api/analysis/${sessionId}/status`)
        .then(response => response.json())
        .then(data => {
            if (data.completed) {
                // Refresh page to show results
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                // Check again in 3 seconds
                setTimeout(() => {
                    checkAnalysisStatus(sessionId);
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Error checking analysis status:', error);
        });
}

function initTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i data-feather="${type === 'error' ? 'alert-triangle' : 'info'}" class="me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        const alertDiv = document.createElement('div');
        alertDiv.innerHTML = alertHtml;
        container.insertBefore(alertDiv.firstElementChild, container.firstElementChild);
        
        // Re-initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatPercentage(value, decimals = 2) {
    return (value).toFixed(decimals) + '%';
}

// Export functions for global use
window.FTAOriginTool = {
    showAlert,
    formatFileSize,
    formatCurrency,
    formatPercentage,
    validateFile
};
