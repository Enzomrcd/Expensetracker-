// Expense form handling

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation
    initializeFormValidation();
    
    // Pre-fill current date on expense forms
    setDefaultDate();
});

// Set default date for expense forms
function setDefaultDate() {
    const dateField = document.getElementById('date');
    if (dateField && !dateField.value) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        
        dateField.value = `${year}-${month}-${day}`;
    }
}

// Client-side form validation
function initializeFormValidation() {
    const expenseForm = document.querySelector('form');
    if (!expenseForm) return;
    
    expenseForm.addEventListener('submit', function(event) {
        let isValid = true;
        
        // Validate amount
        const amountField = document.getElementById('amount');
        if (amountField) {
            const amount = parseFloat(amountField.value);
            if (isNaN(amount) || amount <= 0) {
                isValid = false;
                showFieldError(amountField, 'Please enter a valid amount greater than 0.');
            } else {
                clearFieldError(amountField);
            }
        }
        
        // Validate category
        const categoryField = document.getElementById('category');
        if (categoryField && categoryField.value === '') {
            isValid = false;
            showFieldError(categoryField, 'Please select a category.');
        } else {
            clearFieldError(categoryField);
        }
        
        // Validate date
        const dateField = document.getElementById('date');
        if (dateField && !dateField.value) {
            isValid = false;
            showFieldError(dateField, 'Please select a date.');
        } else {
            clearFieldError(dateField);
        }
        
        if (!isValid) {
            event.preventDefault();
        }
    });
}

// Show form field error
function showFieldError(field, message) {
    // Clear any existing error
    clearFieldError(field);
    
    // Add error class to field
    field.classList.add('is-invalid');
    
    // Create and add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

// Clear form field error
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    // Remove any existing error message
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Format currency for display
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}
