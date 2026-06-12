// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const navToggle = document.querySelector('.nav-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (navToggle && sidebar) {
        navToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !navToggle.contains(e.target) && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }
        });
    }

    // 2. Active Sidebar Link Highlight
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.sidebar-menu li');
    menuLinks.forEach(li => {
        const link = li.querySelector('a');
        if (link) {
            const href = link.getAttribute('href');
            if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
                li.classList.add('active');
            } else {
                li.classList.remove('active');
            }
        }
    });

    // 3. Modal Functionality
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');
    
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal');
            if (modal) modal.style.display = 'none';
        });
    });

    window.addEventListener('click', (e) => {
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // 4. Auto-dismiss Alert Messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                alert.remove();
            }, 800);
        }, 4500);
    });
});

// Helper functions to open modals programmatically
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Populate Traffic Update Modal values
function openUpdateTrafficModal(id, location, count, speed, congestion) {
    const modal = document.getElementById('updateTrafficModal');
    if (modal) {
        const form = modal.querySelector('form');
        form.action = `/traffic/update/${id}`;
        modal.querySelector('#edit_location').value = location;
        modal.querySelector('#edit_vehicle_count').value = count;
        modal.querySelector('#edit_avg_speed').value = speed;
        modal.querySelector('#edit_congestion_level').value = congestion;
        modal.style.display = 'flex';
    }
}

// Populate Pollution Update Modal values
function openUpdatePollutionModal(id, location, aqi, pm25, pm10, co2, noise) {
    const modal = document.getElementById('updatePollutionModal');
    if (modal) {
        const form = modal.querySelector('form');
        form.action = `/pollution/update/${id}`;
        modal.querySelector('#edit_location').value = location;
        modal.querySelector('#edit_aqi').value = aqi;
        modal.querySelector('#edit_pm25').value = pm25;
        modal.querySelector('#edit_pm10').value = pm10;
        modal.querySelector('#edit_co2').value = co2;
        modal.querySelector('#edit_noise_level').value = noise;
        modal.style.display = 'flex';
    }
}

// Populate Service Status Update Modal values
function openUpdateServiceModal(id, serviceName, location, status, responseTime, issuesCount) {
    const modal = document.getElementById('updateServiceModal');
    if (modal) {
        const form = modal.querySelector('form');
        form.action = `/services/update/${id}`;
        modal.querySelector('#edit_service_name').value = serviceName;
        modal.querySelector('#edit_location').value = location;
        modal.querySelector('#edit_status').value = status;
        modal.querySelector('#edit_response_time').value = responseTime;
        modal.querySelector('#edit_issue_count').value = issuesCount;
        modal.style.display = 'flex';
    }
}

// Update Citizen Report status via AJAX (officer action)
function updateReportStatus(reportId, statusValue) {
    if (!confirm(`Are you sure you want to change status to "${statusValue}"?`)) return;
    
    fetch(`/citizen-reports/update-status/${reportId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `status=${encodeURIComponent(statusValue)}`
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Failed to update status.');
        }
    })
    .catch(err => console.error('Error:', err));
}

// Delete Citizen Report via AJAX
function deleteReport(reportId) {
    if (!confirm('Are you sure you want to delete this report permanently?')) return;
    
    fetch(`/citizen-reports/delete/${reportId}`, {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Failed to delete report.');
        }
    })
    .catch(err => console.error('Error:', err));
}
