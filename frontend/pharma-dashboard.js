// Pharmaceutical Manufacturing Dashboard
// Real-time monitoring for FDA 21 CFR Part 11 compliant operations

// Configuration
const API_BASE = 'http://localhost:8002';  // Updated to correct Pharma API port
const UPDATE_INTERVAL = 2000; // 2 seconds

// Chart instances
let environmentChart = null;
let productionChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Pharma Manufacturing Dashboard...');
    
    initializeCharts();
    startRealtimeUpdates();
    simulateProductionData();
    
    // Show welcome notification
    showNotification('Dashboard connected to manufacturing systems', 'success');
});

// Initialize charts
function initializeCharts() {
    // Environmental Monitoring Chart
    const envCtx = document.getElementById('environmentChart').getContext('2d');
    environmentChart = new Chart(envCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Humidity (%)',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                },
                {
                    label: 'Pressure (Pa)',
                    data: [],
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    title: {
                        display: true,
                        text: 'Temperature (°C)',
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    title: {
                        display: true,
                        text: 'Humidity (%)',
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y2: {
                    type: 'linear',
                    display: false,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            }
        }
    });

    // Production Metrics Chart
    const prodCtx = document.getElementById('productionChart').getContext('2d');
    productionChart = new Chart(prodCtx, {
        type: 'bar',
        data: {
            labels: ['Line A', 'Line B', 'Line C', 'Line D'],
            datasets: [
                {
                    label: 'Target (units/hr)',
                    data: [15000, 10000, 8000, 12000],
                    backgroundColor: 'rgba(156, 163, 175, 0.5)',
                    borderColor: 'rgb(156, 163, 175)',
                    borderWidth: 1
                },
                {
                    label: 'Actual (units/hr)',
                    data: [12450, 8200, 0, 0],
                    backgroundColor: 'rgba(16, 185, 129, 0.5)',
                    borderColor: 'rgb(16, 185, 129)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    title: {
                        display: true,
                        text: 'Units per Hour',
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Start real-time updates
function startRealtimeUpdates() {
    setInterval(() => {
        updateEnvironmentalData();
        updateProductionMetrics();
        updateBatchProgress();
        checkForAlerts();
    }, UPDATE_INTERVAL);
}

// Update environmental data
function updateEnvironmentalData() {
    const timestamp = new Date().toLocaleTimeString();
    
    // Generate realistic environmental data
    const temp = 21 + (Math.random() - 0.5) * 0.5;
    const humidity = 45 + (Math.random() - 0.5) * 2;
    const pressure = 25 + (Math.random() - 0.5) * 1;
    
    // Update chart
    if (environmentChart.data.labels.length > 20) {
        environmentChart.data.labels.shift();
        environmentChart.data.datasets[0].data.shift();
        environmentChart.data.datasets[1].data.shift();
        environmentChart.data.datasets[2].data.shift();
    }
    
    environmentChart.data.labels.push(timestamp);
    environmentChart.data.datasets[0].data.push(temp.toFixed(1));
    environmentChart.data.datasets[1].data.push(humidity.toFixed(1));
    environmentChart.data.datasets[2].data.push(pressure.toFixed(1));
    environmentChart.update('none');
    
    // Update display values
    updateDisplayValue('temperature', temp, '°C');
    updateDisplayValue('humidity', humidity, '%');
    updateDisplayValue('pressure', pressure, ' Pa');
    
    // Check for deviations
    if (temp < 20 || temp > 22) {
        showAlert('Temperature deviation detected!');
    }
}

// Update production metrics
function updateProductionMetrics() {
    // Simulate production updates
    const lineAOutput = 12000 + Math.random() * 1000;
    const lineBOutput = 8000 + Math.random() * 500;
    
    productionChart.data.datasets[1].data[0] = lineAOutput;
    productionChart.data.datasets[1].data[1] = lineBOutput;
    productionChart.update('none');
    
    // Update batch progress
    const currentOutput = parseInt(document.querySelector('.text-green-400.font-bold').textContent.replace(/[^0-9]/g, ''));
    const newOutput = currentOutput + Math.floor(Math.random() * 50);
    if (newOutput < 50000) {
        updateBatchOutput(newOutput);
    }
}

// Update batch output
function updateBatchOutput(value) {
    const elements = document.querySelectorAll('.text-green-400.font-bold');
    if (elements[3]) {
        elements[3].textContent = value.toLocaleString() + ' units';
    }
    
    // Update yield
    const yield_val = (value / 50000 * 100).toFixed(1);
    if (elements[4]) {
        elements[4].textContent = yield_val + '%';
    }
}

// Update batch progress
function updateBatchProgress() {
    // Update progress bars
    const progressBars = document.querySelectorAll('.bg-green-500');
    progressBars.forEach((bar, index) => {
        if (index < 2) {
            const currentWidth = parseFloat(bar.style.width);
            const newWidth = Math.min(100, currentWidth + Math.random() * 0.5);
            bar.style.width = newWidth + '%';
        }
    });
}

// Check for alerts
function checkForAlerts() {
    // Random alert generation for demo
    if (Math.random() > 0.98) {
        const alerts = [
            'Clean Room 2: Particle count approaching limit',
            'Line A: Batch completion in 5 minutes',
            'QC Lab: Sample analysis complete',
            'Deviation DEV-2024-0012 requires review',
            'Maintenance scheduled for Line C at 15:00'
        ];
        const alert = alerts[Math.floor(Math.random() * alerts.length)];
        showAlert(alert);
    }
}

// Show alert
function showAlert(message) {
    const banner = document.getElementById('alertBanner');
    const text = document.getElementById('alertText');
    
    text.textContent = message;
    banner.classList.remove('hidden');
    
    setTimeout(() => {
        banner.classList.add('hidden');
    }, 5000);
}

// Update display value
function updateDisplayValue(id, value, unit) {
    // This would update the actual display elements
    // For now, just log the values
    console.log(`${id}: ${value}${unit}`);
}

// Simulate production data
function simulateProductionData() {
    // Simulate various production events
    setInterval(() => {
        // Update line statuses randomly
        if (Math.random() > 0.95) {
            const statuses = ['RUNNING', 'CLEANING', 'STANDBY', 'MAINTENANCE'];
            const colors = ['text-green-400', 'text-yellow-400', 'text-blue-400', 'text-red-400'];
            // Would update line status here
        }
        
        // Generate quality events
        if (Math.random() > 0.97) {
            showNotification('Quality check passed for Batch #2024-0847', 'success');
        }
        
        // Generate compliance events
        if (Math.random() > 0.98) {
            showNotification('Audit trail recorded: User JSmith approved batch release', 'info');
        }
    }, 10000);
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-20 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' :
        type === 'warning' ? 'bg-yellow-600' :
        'bg-blue-600'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${
                type === 'success' ? 'check-circle' :
                type === 'error' ? 'exclamation-circle' :
                type === 'warning' ? 'exclamation-triangle' :
                'info-circle'
            } mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after delay
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Initialize dashboard
console.log('Pharma Manufacturing Dashboard initialized');
showNotification('Connected to manufacturing control system', 'success');