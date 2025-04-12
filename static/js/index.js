// Index page scripts

document.addEventListener('DOMContentLoaded', function() {
  // Toggle between login and register forms
  const emailSignInBtn = document.getElementById('emailSignIn');
  const registerLink = document.getElementById('registerLink');
  const loginLink = document.getElementById('loginLink');
  const authError = document.getElementById('auth-error');
  
  if (emailSignInBtn) {
    emailSignInBtn.addEventListener('click', function() {
      document.getElementById('emailSignInForm').classList.remove('d-none');
      document.getElementById('registerForm').classList.add('d-none');
      // Hide any previous errors
      if (authError) authError.classList.add('d-none');
    });
  }
  
  if (registerLink) {
    registerLink.addEventListener('click', function(e) {
      e.preventDefault();
      document.getElementById('emailSignInForm').classList.add('d-none');
      document.getElementById('registerForm').classList.remove('d-none');
      // Hide any previous errors
      if (authError) authError.classList.add('d-none');
    });
  }
  
  if (loginLink) {
    loginLink.addEventListener('click', function(e) {
      e.preventDefault();
      document.getElementById('registerForm').classList.add('d-none');
      document.getElementById('emailSignInForm').classList.remove('d-none');
      // Hide any previous errors
      if (authError) authError.classList.add('d-none');
    });
  }
  
  // Note: We've moved the form handling to auth.js for better organization
  // This file now only handles the UI elements for the index page
  
  // Helper to show errors
  function showError(message) {
    const errorElement = document.getElementById('auth-error');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.remove('d-none');
    } else {
      console.error('Error:', message);
      alert(message);
    }
  }
});
