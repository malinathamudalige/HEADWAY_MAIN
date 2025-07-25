/**
 * HEADWAY E-LEARNING PLATFORM - CUSTOM JAVASCRIPT
 * Enhanced functionality for interactive features
 * Author: Malintha Dinuranga
 * Course: IT5106 - Software Development
 */

// =============================================================================
// GLOBAL CONFIGURATION AND INITIALIZATION
// =============================================================================

const AppConfig = {
    animationSpeed: 300,
    notificationDuration: 5000,
    progressAnimationDuration: 1500,
    apiBaseUrl: '/api',
    debug: false
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Main application initialization
 */
function initializeApp() {
    console.log('🎓 Headway E-Learning Platform Initialized');
    
    // Initialize core features
    initializeFlashMessages();
    initializeProgressBars();
    initializeFormValidation();
    initializeTooltips();
    initializeModalHandlers();
    initializeCharts();
    initializeQuizFunctionality();
    initializeNotificationSystem();
    initializeKeyboardNavigation();
    initializeThemeToggle();
    
    // Load user preferences
    loadUserPreferences();
    
    // Initialize real-time features
    initializeRealTimeUpdates();
    
    console.log('✅ All features initialized successfully');
}

// =============================================================================
// FLASH MESSAGE SYSTEM
// =============================================================================

/**
 * Auto-hide flash messages with smooth animation
 */
function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('[class*="bg-red-50"], [class*="bg-green-50"], [class*="bg-yellow-50"], [class*="bg-blue-50"]');
    
    flashMessages.forEach(function(message, index) {
        // Add fade-in animation
        message.classList.add('fade-in');
        
        // Auto-hide after delay
        setTimeout(function() {
            hideFlashMessage(message);
        }, AppConfig.notificationDuration + (index * 200));
        
        // Add close button if not present
        if (!message.querySelector('.close-button')) {
            addCloseButton(message);
        }
    });
}

function hideFlashMessage(element) {
    element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    element.style.opacity = '0';
    element.style.transform = 'translateX(100%)';
    
    setTimeout(function() {
        if (element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }, 500);
}

function addCloseButton(message) {
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '<i class="fas fa-times"></i>';
    closeButton.className = 'close-button ml-4 text-current opacity-70 hover:opacity-100 transition-opacity';
    closeButton.onclick = function() {
        hideFlashMessage(message);
    };
    
    const messageContent = message.querySelector('p');
    if (messageContent) {
        messageContent.appendChild(closeButton);
    }
}

// =============================================================================
// PROGRESS BAR ANIMATIONS
// =============================================================================

/**
 * Animate progress bars on page load
 */
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('[data-progress]');
    
    progressBars.forEach(function(bar) {
        const targetProgress = parseInt(bar.dataset.progress);
        animateProgressBar(bar, targetProgress);
    });
}

function animateProgressBar(element, targetPercentage) {
    let currentPercentage = 0;
    const increment = targetPercentage / (AppConfig.progressAnimationDuration / 16);
    
    const timer = setInterval(function() {
        currentPercentage += increment;
        
        if (currentPercentage >= targetPercentage) {
            currentPercentage = targetPercentage;
            clearInterval(timer);
        }
        
        element.style.width = currentPercentage + '%';
        
        // Update text if present
        const progressText = element.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = Math.round(currentPercentage) + '%';
        }
    }, 16);
}

// =============================================================================
// FORM VALIDATION AND ENHANCEMENT
// =============================================================================

/**
 * Enhanced form validation with real-time feedback
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(function(input) {
            // Real-time validation
            input.addEventListener('blur', function() {
                validateField(input);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(input);
            });
        });
        
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                showNotification('Please fix the errors before submitting', 'error');
            }
        });
    });
}

function validateField(input) {
    const value = input.value.trim();
    const rules = input.dataset.rules ? input.dataset.rules.split('|') : [];
    let isValid = true;
    let errorMessage = '';
    
    // Required validation
    if (input.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Password validation
    if (input.type === 'password' && value) {
        if (value.length < 8) {
            isValid = false;
            errorMessage = 'Password must be at least 8 characters long';
        }
    }
    
    // Custom rules
    rules.forEach(function(rule) {
        if (rule.startsWith('min:')) {
            const minLength = parseInt(rule.split(':')[1]);
            if (value.length < minLength) {
                isValid = false;
                errorMessage = `Minimum ${minLength} characters required`;
            }
        }
        
        if (rule.startsWith('max:')) {
            const maxLength = parseInt(rule.split(':')[1]);
            if (value.length > maxLength) {
                isValid = false;
                errorMessage = `Maximum ${maxLength} characters allowed`;
            }
        }
    });
    
    if (isValid) {
        showFieldSuccess(input);
    } else {
        showFieldError(input, errorMessage);
    }
    
    return isValid;
}

function showFieldError(input, message) {
    input.classList.add('border-red-500', 'error');
    input.classList.remove('border-green-500', 'success');
    
    removeExistingError(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message text-red-500 text-sm mt-1';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

function showFieldSuccess(input) {
    input.classList.add('border-green-500', 'success');
    input.classList.remove('border-red-500', 'error');
    removeExistingError(input);
}

function clearFieldError(input) {
    input.classList.remove('border-red-500', 'border-green-500', 'error', 'success');
    removeExistingError(input);
}

function removeExistingError(input) {
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(function(input) {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// =============================================================================
// TOOLTIP SYSTEM
// =============================================================================

function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(function(element) {
        element.addEventListener('mouseenter', function() {
            showTooltip(element);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element) {
    const tooltipText = element.dataset.tooltip;
    const tooltip = document.createElement('div');

    tooltip.className = 'tooltip fixed bg-gray-900 text-white text-sm px-3 py-2 rounded-lg shadow-lg z-50 pointer-events-none';
    tooltip.textContent = tooltipText;
    tooltip.id = 'active-tooltip';

    document.body.appendChild(tooltip);
}