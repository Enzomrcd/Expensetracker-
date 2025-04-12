// Auth related functionality

// Helper to show errors
function showError(message) {
    const toastMessage = document.getElementById('toastMessage');
    const errorToast = document.getElementById('errorToast');
    
    if (toastMessage && errorToast) {
        toastMessage.textContent = message;
        const toast = new bootstrap.Toast(errorToast);
        toast.show();
    } else {
        console.error('Error:', message);
        alert(message);
    }
}

// Login with email and password
function signInWithEmail(email, password) {
    // Call the server directly
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            showError(data.error || 'Login failed');
        }
    })
    .catch(error => {
        showError('Login error: ' + error.message);
    });
}

// Register with email and password
function registerWithEmail(email, password) {
    // Call the server directly for registration
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            email, 
            password,
            isRegistration: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            showError(data.error || 'Registration failed');
        }
    })
    .catch(error => {
        showError('Registration error: ' + error.message);
    });
}

// Sign out the user
function signOut() {
    fetch('/logout')
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                return response.json();
            }
        })
        .then(data => {
            if (data && !data.success) {
                showError(data.error || 'Logout failed');
            }
        })
        .catch(error => {
            console.error('Logout error:', error);
        });
}

// Initialize auth when DOM content is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up email login form
    const loginForm = document.getElementById('email-login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            signInWithEmail(email, password);
        });
    }
    
    // Set up email registration form
    const registerForm = document.getElementById('email-register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            // Validate passwords match
            if (password !== confirmPassword) {
                showError('Passwords do not match');
                return;
            }
            
            registerWithEmail(email, password);
        });
    }
    
    // Set up UI elements for login/register toggling
    const emailSignInBtn = document.getElementById('emailSignIn');
    const registerLink = document.getElementById('registerLink');
    const loginLink = document.getElementById('loginLink');
    const emailSignInForm = document.getElementById('emailSignInForm');
    const registerFormDisplay = document.getElementById('registerForm');
    
    if (emailSignInBtn) {
        emailSignInBtn.addEventListener('click', function() {
            emailSignInForm.classList.remove('d-none');
            if (registerFormDisplay) registerFormDisplay.classList.add('d-none');
        });
    }
    
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            emailSignInForm.classList.add('d-none');
            registerFormDisplay.classList.remove('d-none');
        });
    }
    
    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            registerFormDisplay.classList.add('d-none');
            emailSignInForm.classList.remove('d-none');
        });
    }
    
    // Set up logout button
    const signOutBtn = document.getElementById('sign-out-btn');
    if (signOutBtn) {
        signOutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            signOut();
        });
    }
});
// Add forgot password functionality
const forgotPasswordLink = document.getElementById('forgotPasswordLink');
if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener('click', function(e) {
        e.preventDefault();
        const email = document.getElementById('email').value;
        if (!email) {
            alert('Please enter your email address first');
            return;
        }
        
        fetch('/reset-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Password reset instructions have been sent to your email');
            } else {
                alert(data.error || 'Failed to send reset instructions');
            }
        });
    });
}
