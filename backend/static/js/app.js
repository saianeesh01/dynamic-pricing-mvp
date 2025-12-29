// Professional Dashboard JavaScript

let currentSection = 'dashboard';
let venues = [];
let recommendations = [];
let marketData = null;
let phase2Available = false;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Check system status
    await checkStatus();
    
    // Load venues
    await loadVenues();
    
    // Load market analysis
    await loadMarketAnalysis();
    
    // Setup navigation
    setupNavigation();
    
    // Setup forecast filters
    setupForecastFilters();
    
    // Load initial data
    updateDashboard();
}

// Check system status
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        phase2Available = status.phase2_available;
        
        // Update status badge
        const statusBadge = document.getElementById('statusBadge');
        if (statusBadge) {
            if (phase2Available) {
                statusBadge.innerHTML = '<span class="status-dot"></span><span>Phase 2 Active (AI)</span>';
                statusBadge.style.color = '#10b981';
            } else {
                statusBadge.innerHTML = '<span class="status-dot"></span><span>Phase 1 Active</span>';
                statusBadge.style.color = '#cbd5e1';
            }
        }
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            showSection(section);
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const section = document.getElementById(sectionName);
    if (section) {
        section.classList.add('active');
    }
    
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === sectionName) {
            item.classList.add('active');
        }
    });
    
    currentSection = sectionName;
    
    // Load section-specific data
    if (sectionName === 'market-analysis') {
        renderMarketCharts();
    } else if (sectionName === 'recommendations') {
        loadRecommendations();
    }
}

// Load venues
async function loadVenues() {
    try {
        const response = await fetch('/api/venues');
        venues = await response.json();
        
        // Populate venue filters
        const venueFilter = document.getElementById('venueFilter');
        const forecastVenue = document.getElementById('forecastVenue');
        
        venues.forEach(venue => {
            const option1 = new Option(venue, venue);
            const option2 = new Option(venue, venue);
            venueFilter.appendChild(option1);
            forecastVenue.appendChild(option2);
        });
    } catch (error) {
        console.error('Error loading venues:', error);
    }
}

// Load market analysis
async function loadMarketAnalysis() {
    try {
        const response = await fetch('/api/market-analysis');
        marketData = await response.json();
    } catch (error) {
        console.error('Error loading market analysis:', error);
    }
}

// Load recommendations
async function loadRecommendations() {
    const venueFilter = document.getElementById('venueFilter');
    const eventFilter = document.getElementById('eventFilter');
    const timeFilter = document.getElementById('timeFilter');
    
    const venue = venueFilter ? venueFilter.value : '';
    const eventType = eventFilter ? eventFilter.value : 'regular';
    const time = timeFilter ? timeFilter.value : '22:00';
    const [hours, minutes] = time.split(':');
    
    const isWeekend = new Date().getDay() >= 4;
    
    const data = {
        venue: venue || null,
        day_of_week: new Date().getDay(),
        hour: parseInt(hours) || 22,
        is_weekend: isWeekend,
        event_type: eventType,
        inventory_level: 1.0
    };
    
    const tbody = document.getElementById('recommendationsBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Loading recommendations...</td></tr>';
    }
    
    try {
        const response = await fetch('/api/bulk-recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({error: 'Unknown error'}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        recommendations = await response.json();
        
        if (!recommendations || recommendations.length === 0) {
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="9" class="loading">No recommendations found</td></tr>';
            }
            return;
        }
        
        renderRecommendations();
    } catch (error) {
        console.error('Error loading recommendations:', error);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9" class="loading">Error: ${error.message}</td></tr>`;
        }
    }
}

// Render recommendations table
function renderRecommendations() {
    const tbody = document.getElementById('recommendationsBody');
    
    if (recommendations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No recommendations found</td></tr>';
        return;
    }
    
    tbody.innerHTML = recommendations.map(rec => {
        const deltaClass = rec.delta_pct > 0 ? 'badge-success' : rec.delta_pct < 0 ? 'badge-danger' : 'badge-info';
        const methodBadge = rec.phase === 2 ? 'badge-success' : 'badge-info';
        const methodText = rec.phase === 2 ? 'Phase 2 (AI)' : 'Phase 1 (Market)';
        
        return `
            <tr>
                <td>${rec.venue}</td>
                <td><strong>${rec.bottle}</strong></td>
                <td>${rec.type}</td>
                <td>$${rec.current_price.toFixed(2)}</td>
                <td><strong>$${rec.recommended_price.toFixed(2)}</strong></td>
                <td><span class="badge ${deltaClass}">${rec.delta_pct > 0 ? '+' : ''}${rec.delta_pct.toFixed(1)}%</span></td>
                <td>${rec.revenue_improvement ? `$${rec.revenue_improvement.toFixed(2)}` : 'N/A'}</td>
                <td><span class="badge ${methodBadge}">${methodText}</span></td>
                <td>
                    <button class="btn-secondary" onclick="viewDetails('${rec.venue}', '${rec.bottle}')" style="padding: 0.25rem 0.75rem; font-size: 0.75rem;">Details</button>
                </td>
            </tr>
        `;
    }).join('');
}

// Render market charts
function renderMarketCharts() {
    if (!marketData) return;
    
    // VPI Chart
    const vpiCtx = document.getElementById('vpiChart');
    if (vpiCtx) {
        new Chart(vpiCtx, {
            type: 'bar',
            data: {
                labels: marketData.vpi.map(v => v.venue),
                datasets: [{
                    label: 'Venue Premium Index',
                    data: marketData.vpi.map(v => v.vpi),
                    backgroundColor: marketData.vpi.map(v => 
                        v.vpi > 1 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'
                    ),
                    borderColor: marketData.vpi.map(v => 
                        v.vpi > 1 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'
                    ),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const vpi = marketData.vpi[context.dataIndex];
                                return `VPI: ${vpi.vpi.toFixed(3)} (${vpi.premium_pct > 0 ? '+' : ''}${vpi.premium_pct.toFixed(1)}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#cbd5e1' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#cbd5e1' }
                    }
                }
            }
        });
    }
    
    // Price Distribution Chart
    const priceCtx = document.getElementById('priceDistributionChart');
    if (priceCtx) {
        new Chart(priceCtx, {
            type: 'bar',
            data: {
                labels: marketData.type_medians.map(t => t.type),
                datasets: [{
                    label: 'Median Price',
                    data: marketData.type_medians.map(t => t.median_price),
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: 'rgb(99, 102, 241)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `$${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { 
                            color: '#cbd5e1',
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#cbd5e1', maxRotation: 45 }
                    }
                }
            }
        });
    }
}

// Load demand forecast
async function loadDemandForecast() {
    const venue = document.getElementById('forecastVenue').value;
    const product = document.getElementById('forecastProduct').value;
    
    if (!venue || !product) {
        alert('Please select both venue and product');
        return;
    }
    
    // Get product details from API if not in recommendations
    let productData = recommendations.find(r => r.venue === venue && r.bottle === product);
    
    if (!productData) {
        // Try to get from API
        try {
            const productsResponse = await fetch(`/api/products?venue=${encodeURIComponent(venue)}`);
            const products = await productsResponse.json();
            productData = products.find(p => p.bottle === product);
        } catch (error) {
            console.error('Error fetching products:', error);
        }
    }
    
    if (!productData) {
        alert('Product not found. Please ensure recommendations are loaded first or select a different product.');
        return;
    }
    
    const data = {
        venue: venue,
        bottle: product,
        type: productData.type,
        price: productData.price || productData.current_price,
        day_of_week: new Date().getDay(),
        hour: 22,
        is_weekend: true,
        event_type: 'DJ',
        inventory_level: 1.0
    };
    
    try {
        const response = await fetch('/api/demand-prediction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to load demand forecast');
        }
        
        const predictions = await response.json();
        
        if (!predictions || predictions.length === 0) {
            alert('No predictions available. Make sure Phase 2 model is loaded.');
            return;
        }
        
        renderDemandChart(predictions);
    } catch (error) {
        console.error('Error loading demand forecast:', error);
        alert('Error loading demand forecast: ' + error.message);
    }
}

// Render demand chart
function renderDemandChart(predictions) {
    const ctx = document.getElementById('demandChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (window.demandChart) {
        window.demandChart.destroy();
    }
    
    window.demandChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: predictions.map(p => '$' + p.price.toFixed(0)),
            datasets: [
                {
                    label: 'Predicted Demand (bottles)',
                    data: predictions.map(p => p.predicted_demand),
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'Predicted Revenue',
                    data: predictions.map(p => p.revenue),
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: { color: '#cbd5e1' }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                return `Demand: ${context.parsed.y.toFixed(1)} bottles`;
                            } else {
                                return `Revenue: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#cbd5e1' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#cbd5e1' },
                    title: {
                        display: true,
                        text: 'Demand (bottles)',
                        color: '#cbd5e1'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { 
                        color: '#cbd5e1',
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    },
                    title: {
                        display: true,
                        text: 'Revenue ($)',
                        color: '#cbd5e1'
                    }
                }
            }
        }
    });
}

// Update dashboard stats
function updateDashboard() {
    // This would be populated with real data
    document.getElementById('totalProducts').textContent = '174';
    document.getElementById('avgRevenueImpact').textContent = '+4.2%';
    document.getElementById('optimizationRate').textContent = '87%';
    document.getElementById('activeVenues').textContent = venues.length || '3';
}

// Export recommendations
function exportRecommendations() {
    if (recommendations.length === 0) {
        alert('No recommendations to export');
        return;
    }
    
    const csv = [
        ['Venue', 'Bottle', 'Type', 'Current Price', 'Recommended Price', 'Change %', 'Revenue Impact', 'Method'].join(','),
        ...recommendations.map(r => [
            r.venue,
            r.bottle,
            r.type,
            r.current_price,
            r.recommended_price,
            r.delta_pct,
            r.revenue_improvement || 'N/A',
            r.phase === 2 ? 'Phase 2' : 'Phase 1'
        ].join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pricing_recommendations_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
}

// View details
function viewDetails(venue, bottle) {
    const rec = recommendations.find(r => r.venue === venue && r.bottle === bottle);
    if (rec) {
        alert(`Details for ${bottle} at ${venue}\n\nCurrent: $${rec.current_price}\nRecommended: $${rec.recommended_price}\nChange: ${rec.delta_pct}%\nReason: ${rec.reason}`);
    }
}

// Setup forecast filters (venue change handler)
function setupForecastFilters() {
    const forecastVenueSelect = document.getElementById('forecastVenue');
    if (forecastVenueSelect) {
        // Remove existing event listeners by cloning the element
        const newSelect = forecastVenueSelect.cloneNode(true);
        forecastVenueSelect.parentNode.replaceChild(newSelect, forecastVenueSelect);
        
        newSelect.addEventListener('change', async function() {
            const venue = this.value;
            if (!venue) {
                const productSelect = document.getElementById('forecastProduct');
                if (productSelect) {
                    productSelect.innerHTML = '<option value="">Select Product</option>';
                }
                return;
            }
            
            const productSelect = document.getElementById('forecastProduct');
            if (!productSelect) return;
            
            productSelect.innerHTML = '<option value="">Loading products...</option>';
            productSelect.disabled = true;
            
            try {
                const response = await fetch(`/api/products?venue=${encodeURIComponent(venue)}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const products = await response.json();
                
                if (!products || products.length === 0) {
                    productSelect.innerHTML = '<option value="">No products found</option>';
                    return;
                }
                
                productSelect.innerHTML = '<option value="">Select Product</option>';
                products.forEach(product => {
                    const option = new Option(product.bottle, product.bottle);
                    productSelect.appendChild(option);
                });
                productSelect.disabled = false;
            } catch (error) {
                console.error('Error loading products:', error);
                productSelect.innerHTML = '<option value="">Error loading products</option>';
                productSelect.disabled = false;
            }
        });
        
        // Trigger change event if a venue is already selected (e.g., from initial load)
        if (newSelect.value) {
            newSelect.dispatchEvent(new Event('change'));
        }
    }
}

