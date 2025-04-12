// Dashboard functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize expense deletion functionality
    initializeDeleteExpense();
});

// Handle expense deletion
function initializeDeleteExpense() {
    const deleteButtons = document.querySelectorAll('.delete-expense');
    const confirmDeleteButton = document.getElementById('confirmDelete');
    const deleteExpenseModal = document.getElementById('deleteExpenseModal');
    
    if (!deleteButtons.length || !confirmDeleteButton || !deleteExpenseModal) {
        return; // Elements not found, possibly on another page
    }
    
    const modal = new bootstrap.Modal(deleteExpenseModal);
    let expenseIdToDelete = null;
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            expenseIdToDelete = this.getAttribute('data-expense-id');
            modal.show();
        });
    });
    
    confirmDeleteButton.addEventListener('click', function() {
        if (expenseIdToDelete) {
            deleteExpense(expenseIdToDelete, modal);
        }
    });
}

// Send delete request to server
function deleteExpense(expenseId, modal) {
    fetch(`/delete-expense/${expenseId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            modal.hide();
            window.location.reload();
        } else {
            alert('Error deleting expense: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting the expense.');
    });
}

// Initialize and render charts if present
function initializeCharts() {
    // Category chart 
    const categoryChartElement = document.getElementById('categoryChart');
    if (categoryChartElement && window.categoryChartData) {
        Plotly.newPlot('categoryChart', 
                       JSON.parse(window.categoryChartData).data, 
                       JSON.parse(window.categoryChartData).layout);
    }
    
    // Resize charts when window size changes
    window.addEventListener('resize', function() {
        if (categoryChartElement && window.categoryChartData) {
            Plotly.relayout('categoryChart', {
                'width': categoryChartElement.offsetWidth,
                'height': categoryChartElement.offsetHeight
            });
        }
    });
}
