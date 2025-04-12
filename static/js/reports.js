// Reports page functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize and render charts
    initializeReportCharts();
    
    // Initialize export functionality
    initializeExport();
});

// Initialize and render charts for reports page
function initializeReportCharts() {
    // Category chart 
    const categoryChartElement = document.getElementById('categoryChart');
    if (categoryChartElement && window.categoryChartData) {
        Plotly.newPlot('categoryChart', 
                       JSON.parse(window.categoryChartData).data, 
                       JSON.parse(window.categoryChartData).layout);
    }
    
    // Trend chart
    const trendChartElement = document.getElementById('trendChart');
    if (trendChartElement && window.trendChartData) {
        Plotly.newPlot('trendChart', 
                       JSON.parse(window.trendChartData).data, 
                       JSON.parse(window.trendChartData).layout);
    }
    
    // Resize charts when window size changes
    window.addEventListener('resize', function() {
        if (categoryChartElement && window.categoryChartData) {
            Plotly.relayout('categoryChart', {
                'width': categoryChartElement.offsetWidth,
                'height': categoryChartElement.offsetHeight
            });
        }
        
        if (trendChartElement && window.trendChartData) {
            Plotly.relayout('trendChart', {
                'width': trendChartElement.offsetWidth,
                'height': trendChartElement.offsetHeight
            });
        }
    });
}

// Initialize export functionality
function initializeExport() {
    const exportButtons = document.querySelectorAll('[data-export-format]');
    
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.getAttribute('data-export-format');
            const period = getCurrentPeriod();
            
            window.location.href = `/export?format=${format}&period=${period}`;
        });
    });
}

// Get current period from URL or default to 'month'
function getCurrentPeriod() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('period') || 'month';
}

// Switch between time periods
function switchPeriod(period) {
    window.location.href = `/reports?period=${period}`;
}
