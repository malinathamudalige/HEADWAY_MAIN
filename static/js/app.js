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

    // Initialize analytics if on analytics page
    if (window.location.pathname.includes('/analytics')) {
        initializeAnalyticsDashboard();
    }

    // Initialize additional features
    initializeLazyLoading();
    initializeSearch();
    initializeDragAndDrop();
    initializeAutoSave();

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
    // Only select elements we’ve explicitly marked as flash messages:
    const flashMessages = document.querySelectorAll('.flash-message');

    flashMessages.forEach(function(message, index) {
        // Add fade-in animation
        message.classList.add('fade-in');

        // Auto-hide after a short delay
        setTimeout(function() {
            hideFlashMessage(message);
        }, AppConfig.notificationDuration + (index * 200));

        // Add close button if not already present
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

    // Assume your flash-message markup has a <p> or similar as the container
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
        if (value.length < 6) {
            isValid = false;
            errorMessage = 'Password must be at least 6 characters long';
        }
    }

    // URL validation
    if (input.type === 'url' && value) {
        try {
            new URL(value);
        } catch (_) {
            isValid = false;
            errorMessage = 'Please enter a valid URL';
        }
    }

    // Custom rules
    rules.forEach(function(rule) {
        if (rule.startsWith('min:')) {
            const min = parseInt(rule.split(':')[1]);
            if (value.length < min) {
                isValid = false;
                errorMessage = `Minimum ${min} characters required`;
            }
        }

        if (rule.startsWith('max:')) {
            const max = parseInt(rule.split(':')[1]);
            if (value.length > max) {
                isValid = false;
                errorMessage = `Maximum ${max} characters allowed`;
            }
        }
    });

    if (!isValid) {
        showFieldError(input, errorMessage);
    } else {
        clearFieldError(input);
    }

    return isValid;
}

function showFieldError(input, message) {
    clearFieldError(input);

    input.classList.add('border-red-500');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-red-600 text-sm mt-1';
    errorDiv.textContent = message;

    input.parentNode.appendChild(errorDiv);
}

function clearFieldError(input) {
    input.classList.remove('border-red-500');
    const existingError = input.parentNode.querySelector('.field-error');
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

    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// =============================================================================
// MODAL HANDLERS
// =============================================================================

function initializeModalHandlers() {
    // Close modal when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-backdrop')) {
            closeModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    });
    document.body.style.overflow = '';
}

// =============================================================================
// CHARTS AND VISUALIZATIONS
// =============================================================================

function initializeCharts() {
    // Initialize Chart.js charts if present
    const chartElements = document.querySelectorAll('canvas[data-chart]');

    chartElements.forEach(function(canvas) {
        const chartType = canvas.dataset.chart;
        const chartData = JSON.parse(canvas.dataset.data || '{}');

        createChart(canvas, chartType, chartData);
    });
}

function createChart(canvas, type, data) {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded');
        return;
    }

    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// =============================================================================
// QUIZ FUNCTIONALITY
// =============================================================================

function initializeQuizFunctionality() {
    const quizContainers = document.querySelectorAll('.quiz-container');

    quizContainers.forEach(function(container) {
        setupQuizInteractions(container);
    });
}

function setupQuizInteractions(container) {
    const questions = container.querySelectorAll('.quiz-question');
    const submitButton = container.querySelector('.quiz-submit');

    questions.forEach(function(question, index) {
        const options = question.querySelectorAll('input[type="radio"]');

        options.forEach(function(option) {
            option.addEventListener('change', function() {
                updateQuizProgress(container);
            });
        });
    });

    if (submitButton) {
        submitButton.addEventListener('click', function(e) {
            e.preventDefault();
            submitQuiz(container);
        });
    }
}

function updateQuizProgress(container) {
    const questions = container.querySelectorAll('.quiz-question');
    const answered = container.querySelectorAll('.quiz-question input:checked').length;
    const progress = (answered / questions.length) * 100;

    const progressBar = container.querySelector('.quiz-progress-bar');
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }

    const submitButton = container.querySelector('.quiz-submit');
    if (submitButton) {
        submitButton.disabled = answered < questions.length;
    }
}

function submitQuiz(container) {
    const formData = new FormData(container.querySelector('form'));
    const quizId = container.dataset.quizId;

    // Show loading state
    const submitButton = container.querySelector('.quiz-submit');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Submitting...';
    submitButton.disabled = true;

    fetch(`/student/quiz/${quizId}/submit`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showQuizResults(container, data.results);
        } else {
            showNotification('Error submitting quiz: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Quiz submission error:', error);
        showNotification('An error occurred while submitting the quiz', 'error');
    })
    .finally(() => {
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    });
}

function showQuizResults(container, results) {
    const resultsDiv = document.createElement('div');
    resultsDiv.className = 'quiz-results bg-blue-50 border border-blue-200 rounded-lg p-6 mt-6';
    resultsDiv.innerHTML = `
        <h3 class="text-lg font-semibold text-blue-800 mb-4">Quiz Results</h3>
        <div class="grid grid-cols-2 gap-4">
            <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">${results.score}%</div>
                <div class="text-sm text-blue-800">Your Score</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-green-600">${results.correct}/${results.total}</div>
                <div class="text-sm text-green-800">Correct Answers</div>
            </div>
        </div>
        <div class="mt-4 text-center">
            <button onclick="window.location.reload()" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                Try Again
            </button>
        </div>
    `;

    container.appendChild(resultsDiv);
}

// =============================================================================
// NOTIFICATION SYSTEM
// =============================================================================

function initializeNotificationSystem() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');

    const typeClasses = {
        'success': 'bg-green-100 border-green-400 text-green-700',
        'error': 'bg-red-100 border-red-400 text-red-700',
        'warning': 'bg-yellow-100 border-yellow-400 text-yellow-700',
        'info': 'bg-blue-100 border-blue-400 text-blue-700'
    };

    const typeIcons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-triangle',
        'warning': 'fa-exclamation-circle',
        'info': 'fa-info-circle'
    };

    notification.className = `${typeClasses[type]} px-4 py-3 rounded-lg shadow-lg border transform translate-x-full transition-transform duration-300`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${typeIcons[type]} mr-2"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 hover:opacity-70">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    container.appendChild(notification);

    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);

    // Auto-remove
    setTimeout(() => {
        notification.style.transform = 'translateX(full)';
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }, duration);
}

// =============================================================================
// KEYBOARD NAVIGATION
// =============================================================================

function initializeKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        // Global keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case '/':
                    e.preventDefault();
                    focusSearchBox();
                    break;
                case 'k':
                    e.preventDefault();
                    openCommandPalette();
                    break;
            }
        }

        // Tab navigation enhancement
        if (e.key === 'Tab') {
            enhanceTabNavigation(e);
        }
    });
}

function focusSearchBox() {
    const searchBox = document.querySelector('input[type="search"], input[placeholder*="search"]');
    if (searchBox) {
        searchBox.focus();
    }
}

function openCommandPalette() {
    // Command palette functionality (future enhancement)
    console.log('Command palette opened');
}

function enhanceTabNavigation(e) {
    // Add visual feedback for keyboard navigation
    document.body.classList.add('keyboard-navigation');

    setTimeout(() => {
        document.body.classList.remove('keyboard-navigation');
    }, 3000);
}

// =============================================================================
// THEME TOGGLE
// =============================================================================

function initializeThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }
}

function toggleTheme() {
    const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
}

// =============================================================================
// USER PREFERENCES
// =============================================================================

function loadUserPreferences() {
    // Load animation preferences
    const reduceMotion = localStorage.getItem('reduce-motion') === 'true';
    if (reduceMotion) {
        document.body.classList.add('reduce-motion');
    }

    // Load other preferences
    const preferences = JSON.parse(localStorage.getItem('user-preferences') || '{}');
    applyUserPreferences(preferences);
}

function applyUserPreferences(preferences) {
    // Apply notification preferences
    if (preferences.notificationDuration) {
        AppConfig.notificationDuration = preferences.notificationDuration;
    }

    // Apply animation preferences
    if (preferences.animationSpeed) {
        AppConfig.animationSpeed = preferences.animationSpeed;
    }
}

// =============================================================================
// REAL-TIME UPDATES
// =============================================================================

function initializeRealTimeUpdates() {
    // Check for updates every 30 seconds
    setInterval(function() {
        checkForUpdates();
    }, 30000);
}

function checkForUpdates() {
    // Check for new notifications, messages, etc.
    fetch('/api/check-updates')
        .then(response => response.json())
        .then(data => {
            if (data.hasUpdates) {
                handleRealTimeUpdates(data);
            }
        })
        .catch(error => {
            if (AppConfig.debug) {
                console.error('Update check failed:', error);
            }
        });
}

function handleRealTimeUpdates(data) {
    // Handle different types of updates
    if (data.notifications) {
        data.notifications.forEach(notification => {
            showNotification(notification.message, notification.type);
        });
    }

    if (data.badgeUpdate) {
        updateBadgeCount(data.badgeUpdate);
    }
}

function updateBadgeCount(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
}

// =============================================================================
// ANALYTICS FUNCTIONALITY
// =============================================================================

/**
 * Initialize analytics dashboard functionality
 */
function initializeAnalyticsDashboard() {
    // Initialize chart animations
    initializeAnalyticsCharts();

    // Initialize export functionality
    initializeExportButtons();

    // Initialize filter functionality
    initializeAnalyticsFilters();

    // Initialize tooltips for metrics
    initializeAnalyticsTooltips();

    console.log('📊 Analytics dashboard initialized');
}

/**
 * Initialize analytics charts with animations
 */
function initializeAnalyticsCharts() {
    // Animate progress bars
    const progressBars = document.querySelectorAll('.bg-green-600[style*="width"]');
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        bar.style.transition = 'width 1.5s ease-in-out';

        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 300);
    });

    // Animate metric cards
    const metricCards = document.querySelectorAll('.text-2xl.font-bold');
    metricCards.forEach((card, index) => {
        const targetValue = parseInt(card.textContent) || parseFloat(card.textContent) || 0;
        card.textContent = '0';

        setTimeout(() => {
            animateCounter(card, targetValue, 1500);
        }, 200 * index);
    });
}

/**
 * Animate counter from 0 to target value
 */
function animateCounter(element, target, duration) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }

        // Handle different number formats
        if (element.textContent.includes('%')) {
            element.textContent = Math.round(current) + '%';
        } else if (target % 1 !== 0) {
            element.textContent = current.toFixed(1);
        } else {
            element.textContent = Math.round(current);
        }
    }, 16);
}

/**
 * Initialize export button functionality
 */
function initializeExportButtons() {
    // Main export button
    const exportButton = document.querySelector('button[onclick*="exportAnalyticsReport"]');
    if (exportButton) {
        exportButton.removeAttribute('onclick');
        exportButton.addEventListener('click', function(e) {
            e.preventDefault();
            handleAnalyticsExport();
        });
    }

    // Individual course export buttons
    const courseExportButtons = document.querySelectorAll('button[onclick*="exportCourseAnalytics"]');
    courseExportButtons.forEach(button => {
        const onclickAttr = button.getAttribute('onclick');
        if (onclickAttr) {
            const courseId = onclickAttr.match(/'([^']+)'/)[1];

            button.removeAttribute('onclick');
            button.addEventListener('click', function(e) {
                e.preventDefault();
                handleCourseAnalyticsExport(courseId);
            });
        }
    });
}

/**
 * Handle main analytics export
 */
function handleAnalyticsExport() {
    const button = event.target.closest('button');
    const originalContent = button.innerHTML;

    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Preparing Export...';
    button.disabled = true;

    // Get current filter values
    const timeFilter = document.getElementById('timeFilter')?.value || 'all_time';

    // Create export URL
    const exportUrl = `/educator/analytics/export?time_filter=${timeFilter}`;

    // Simulate processing time for better UX
    setTimeout(() => {
        // Create download link
        const link = document.createElement('a');
        link.href = exportUrl;
        link.download = `educator_analytics_${timeFilter}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Show success message
        showNotification('Analytics report exported successfully!', 'success');

        // Reset button
        button.innerHTML = originalContent;
        button.disabled = false;
    }, 1500);
}

/**
 * Handle individual course analytics export
 */
function handleCourseAnalyticsExport(courseId) {
    const button = event.target.closest('button');
    const originalContent = button.innerHTML;

    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Exporting...';
    button.disabled = true;

    // Create export URL
    const exportUrl = `/educator/course/${courseId}/analytics/export`;

    setTimeout(() => {
        // Create download link
        const link = document.createElement('a');
        link.href = exportUrl;
        link.download = `course_analytics_${courseId}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Show success message
        showNotification('Course analytics exported successfully!', 'success');

        // Reset button
        button.innerHTML = originalContent;
        button.disabled = false;
    }, 1000);
}

/**
 * Initialize analytics filters
 */
function initializeAnalyticsFilters() {
    const timeFilter = document.getElementById('timeFilter');
    const sortFilter = document.getElementById('sortBy');

    if (timeFilter) {
        timeFilter.removeAttribute('onchange');
        timeFilter.addEventListener('change', function() {
            applyAnalyticsFilters();
        });
    }

    if (sortFilter) {
        sortFilter.removeAttribute('onchange');
        sortFilter.addEventListener('change', function() {
            applyAnalyticsFilters();
        });
    }
}

/**
 * Apply analytics filters with smooth transition
 */
function applyAnalyticsFilters() {
    const timeFilter = document.getElementById('timeFilter').value;
    const sortBy = document.getElementById('sortBy').value;

    // Show loading state
    const contentArea = document.getElementById('analyticsContent');
    const loadingIndicator = document.getElementById('loadingIndicator');

    if (contentArea && loadingIndicator) {
        contentArea.style.opacity = '0.5';
        loadingIndicator.classList.remove('hidden');
    }

    // Update filter display
    updateFilterDisplay(timeFilter);

    // Apply filters with animation
    setTimeout(() => {
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.set('time_filter', timeFilter);
        currentUrl.searchParams.set('sort_by', sortBy);

        // Smooth page transition
        document.body.style.opacity = '0.8';

        setTimeout(() => {
            window.location.href = currentUrl.toString();
        }, 300);
    }, 500);
}

/**
 * Update filter display text
 */
function updateFilterDisplay(timeFilter) {
    const filterTexts = {
        'all_time': 'All Time',
        'last_30_days': 'Last 30 Days',
        'last_3_months': 'Last 3 Months',
        'last_6_months': 'Last 6 Months'
    };

    const displayElement = document.getElementById('currentFilterText');
    if (displayElement) {
        displayElement.textContent = filterTexts[timeFilter] || 'All Time';
    }
}

/**
 * Initialize analytics tooltips
 */
function initializeAnalyticsTooltips() {
    // Add tooltips to metric cards
    const metricCards = document.querySelectorAll('.text-center.p-3');
    metricCards.forEach(card => {
        const metricElement = card.querySelector('.text-sm');
        if (metricElement) {
            const metric = metricElement.textContent.toLowerCase();
            let tooltipText = '';

            switch(true) {
                case metric.includes('students'):
                    tooltipText = 'Total number of enrolled students in this course';
                    break;
                case metric.includes('completion'):
                    tooltipText = 'Percentage of students who completed all modules';
                    break;
                case metric.includes('score'):
                    tooltipText = 'Average quiz and assessment scores';
                    break;
                case metric.includes('progress'):
                    tooltipText = 'Average course progress across all students';
                    break;
                case metric.includes('modules'):
                    tooltipText = 'Total number of learning modules';
                    break;
            }

            if (tooltipText) {
                card.title = tooltipText;
                card.style.cursor = 'help';
            }
        }
    });
}

/**
 * Analytics utility functions
 */
const AnalyticsUtils = {
    /**
     * Format numbers for display
     */
    formatNumber: function(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    /**
     * Calculate percentage change
     */
    calculatePercentageChange: function(current, previous) {
        if (previous === 0) return current > 0 ? 100 : 0;
        return ((current - previous) / previous) * 100;
    },

    /**
     * Get performance status based on metrics
     */
    getPerformanceStatus: function(value, metric) {
        const thresholds = {
            'completion_rate': { excellent: 80, good: 60 },
            'avg_score': { excellent: 85, good: 70 },
            'engagement_rate': { excellent: 75, good: 50 }
        };

        const threshold = thresholds[metric];
        if (!threshold) return 'unknown';

        if (value >= threshold.excellent) return 'excellent';
        if (value >= threshold.good) return 'good';
        return 'needs_improvement';
    }
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Debounce function to limit function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function to limit function calls
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Smooth scroll to element
 */
function smoothScrollTo(element, duration = 800) {
    const targetPosition = element.offsetTop;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;

    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }

    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }

    requestAnimationFrame(animation);
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success', 2000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            showNotification('Failed to copy to clipboard', 'error');
        }

        textArea.remove();
    }
}

/**
 * Format date for display
 */
function formatDate(date, format = 'default') {
    const d = new Date(date);

    switch(format) {
        case 'short':
            return d.toLocaleDateString();
        case 'long':
            return d.toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        case 'time':
            return d.toLocaleTimeString();
        case 'datetime':
            return d.toLocaleString();
        default:
            return d.toLocaleDateString();
    }
}

/**
 * Generate random ID
 */
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// =============================================================================
// ENHANCED FEATURES
// =============================================================================

/**
 * Initialize lazy loading for images
 */
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"]');

    searchInputs.forEach(input => {
        const debouncedSearch = debounce(performSearch, 300);
        input.addEventListener('input', debouncedSearch);
    });
}

function performSearch(event) {
    const query = event.target.value.trim();
    const searchType = event.target.dataset.searchType || 'general';

    if (query.length >= 2) {
        // Perform search based on type
        switch(searchType) {
            case 'courses':
                searchCourses(query);
                break;
            case 'students':
                searchStudents(query);
                break;
            default:
                generalSearch(query);
        }
    } else {
        clearSearchResults(event.target);
    }
}

function searchCourses(query) {
    // Implementation for course search
    console.log('Searching courses:', query);
}

function searchStudents(query) {
    // Implementation for student search
    console.log('Searching students:', query);
}

function generalSearch(query) {
    // Implementation for general search
    console.log('General search:', query);
}

function clearSearchResults(input) {
    const resultsContainer = input.parentNode.querySelector('.search-results');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
        resultsContainer.style.display = 'none';
    }
}

/**
 * Initialize drag and drop functionality
 */
function initializeDragAndDrop() {
    const dropZones = document.querySelectorAll('.drop-zone');

    dropZones.forEach(zone => {
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('drop', handleDrop);
        zone.addEventListener('dragenter', handleDragEnter);
        zone.addEventListener('dragleave', handleDragLeave);
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
}

function handleDragEnter(e) {
    e.preventDefault();
    e.target.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.target.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.target.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files);
    const dropType = e.target.dataset.dropType || 'file';

    files.forEach(file => {
        handleFileUpload(file, dropType);
    });
}

function handleFileUpload(file, type) {
    // Validate file type and size
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (file.size > maxSize) {
        showNotification('File size too large. Maximum 10MB allowed.', 'error');
        return;
    }

    // Create FormData and upload
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    uploadFile(formData);
}

function uploadFile(formData) {
    const uploadUrl = '/api/upload';

    fetch(uploadUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('File uploaded successfully!', 'success');
            // Handle successful upload
        } else {
            showNotification('Upload failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showNotification('Upload failed. Please try again.', 'error');
    });
}

/**
 * Initialize auto-save functionality
 */
function initializeAutoSave() {
    const autoSaveForms = document.querySelectorAll('form[data-autosave]');

    autoSaveForms.forEach(form => {
        const debouncedSave = debounce(() => autoSaveForm(form), 2000);

        form.addEventListener('input', debouncedSave);
        form.addEventListener('change', debouncedSave);
    });
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const saveUrl = form.dataset.autosaveUrl || form.action;

    // Show auto-save indicator
    showAutoSaveIndicator('Saving...');

    fetch(saveUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Auto-Save': 'true'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAutoSaveIndicator('Saved', 'success');
        } else {
            showAutoSaveIndicator('Save failed', 'error');
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
        showAutoSaveIndicator('Save failed', 'error');
    });
}

function showAutoSaveIndicator(message, type = 'info') {
    let indicator = document.getElementById('autosave-indicator');

    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'autosave-indicator';
        indicator.className = 'fixed bottom-4 right-4 px-3 py-2 rounded-lg text-sm z-40';
        document.body.appendChild(indicator);
    }

    // Set styles based on type
    const typeClasses = {
        'info': 'bg-blue-100 text-blue-800 border border-blue-200',
        'success': 'bg-green-100 text-green-800 border border-green-200',
        'error': 'bg-red-100 text-red-800 border border-red-200'
    };

    indicator.className = `fixed bottom-4 right-4 px-3 py-2 rounded-lg text-sm z-40 ${typeClasses[type]}`;
    indicator.textContent = message;
    indicator.style.display = 'block';

    // Hide after 2 seconds
    setTimeout(() => {
        indicator.style.display = 'none';
    }, 2000);
}

// =============================================================================
// GLOBAL FUNCTIONS (for backward compatibility)
// =============================================================================

// Analytics functions for template usage
window.filterAnalytics = applyAnalyticsFilters;
window.exportAnalyticsReport = handleAnalyticsExport;
window.exportCourseAnalytics = handleCourseAnalyticsExport;

// Utility functions
window.showNotification = showNotification;
window.openModal = openModal;
window.closeModal = closeModal;
window.copyToClipboard = copyToClipboard;
window.smoothScrollTo = smoothScrollTo;

// =============================================================================
// ERROR HANDLING AND DEBUGGING
// =============================================================================

/**
 * Global error handler
 */
window.addEventListener('error', function(e) {
    if (AppConfig.debug) {
        console.error('Global error:', e.error);
    }

    // Don't show error notifications for minor script errors
    if (!e.error.message.includes('Script error')) {
        showNotification('An unexpected error occurred', 'error');
    }
});

/**
 * Unhandled promise rejection handler
 */
window.addEventListener('unhandledrejection', function(e) {
    if (AppConfig.debug) {
        console.error('Unhandled promise rejection:', e.reason);
    }

    showNotification('An error occurred while processing your request', 'error');
});

/**
 * Performance monitoring
 */
function monitorPerformance() {
    if ('performance' in window) {
        window.addEventListener('load', function() {
            setTimeout(function() {
                const perfData = performance.timing;
                const loadTime = perfData.loadEventEnd - perfData.navigationStart;

                if (AppConfig.debug) {
                    console.log(`Page load time: ${loadTime}ms`);
                }

                // Send performance data to analytics if needed
                if (loadTime > 3000) {
                    console.warn('Slow page load detected:', loadTime + 'ms');
                }
            }, 0);
        });
    }
}

// Initialize performance monitoring
monitorPerformance();

// =============================================================================
// EXPORT FOR MODULE SYSTEMS
// =============================================================================

// CommonJS
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AppConfig,
        AnalyticsUtils,
        initializeApp,
        initializeAnalyticsDashboard,
        showNotification,
        formatDate,
        copyToClipboard
    };
}

// AMD
if (typeof define === 'function' && define.amd) {
    define(function() {
        return {
            AppConfig,
            AnalyticsUtils,
            initializeApp,
            initializeAnalyticsDashboard,
            showNotification,
            formatDate,
            copyToClipboard
        };
    });
}

console.log('🎓 Headway E-Learning Platform JavaScript Loaded Successfully');