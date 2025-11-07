// Utility functions untuk aplikasi
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts setelah 5 detik
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Format dates
    const dates = document.querySelectorAll('.date-format');
    dates.forEach(element => {
        const date = new Date(element.textContent);
        element.textContent = date.toLocaleDateString('id-ID', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    });
});

// File upload preview
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const fileName = document.getElementById('fileName');
        if (fileName) {
            fileName.textContent = `Selected: ${file.name}`;
        }
    }
}

// API status checker
function checkAPIStatus() {
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'healthy') {
                console.log('✅ API is healthy');
            } else {
                console.warn('⚠️ API status:', data);
            }
        })
        .catch(error => {
            console.error('❌ API health check failed:', error);
        });
}

// Check API status every minute
setInterval(checkAPIStatus, 60000);

// Initial check
checkAPIStatus();
