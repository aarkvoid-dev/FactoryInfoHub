/**
 * Payment Error Handling System
 * Provides comprehensive frontend error handling for payment operations
 */

class PaymentErrorHandler {
    constructor() {
        this.init();
    }

    init() {
        this.setupGlobalErrorHandling();
        this.setupPaymentFormValidation();
        this.setupNetworkMonitoring();
    }

    /**
     * Setup global error handling for uncaught errors
     */
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            this.logError('Global Error', event.error);
            this.showUserFriendlyError('An unexpected error occurred. Please try again.');
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Unhandled Promise Rejection', event.reason);
            this.showUserFriendlyError('A network error occurred. Please check your connection and try again.');
        });
    }

    /**
     * Setup payment form validation
     */
    setupPaymentFormValidation() {
        const paymentForms = document.querySelectorAll('.payment-form');
        paymentForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validatePaymentForm(form)) {
                    e.preventDefault();
                    this.showUserFriendlyError('Please check your payment information and try again.');
                }
            });
        });
    }

    /**
     * Setup network monitoring
     */
    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            this.showSuccessMessage('Connection restored. You can now proceed with payment.');
        });

        window.addEventListener('offline', () => {
            this.showUserFriendlyError('You are offline. Please check your internet connection.');
        });
    }

    /**
     * Validate payment form fields
     */
    validatePaymentForm(form) {
        const errors = [];
        
        // Check required fields
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                errors.push(`${field.name} is required`);
            }
        });

        // Validate email format
        const emailField = form.querySelector('input[type="email"]');
        if (emailField && !this.isValidEmail(emailField.value)) {
            errors.push('Please enter a valid email address');
        }

        // Validate card number (basic Luhn check)
        const cardNumberField = form.querySelector('input[name="card_number"]');
        if (cardNumberField && !this.isValidCardNumber(cardNumberField.value)) {
            errors.push('Please enter a valid card number');
        }

        // Validate expiry date
        const expiryField = form.querySelector('input[name="expiry_date"]');
        if (expiryField && !this.isValidExpiryDate(expiryField.value)) {
            errors.push('Please enter a valid expiry date');
        }

        // Validate CVV
        const cvvField = form.querySelector('input[name="cvv"]');
        if (cvvField && !this.isValidCVV(cvvField.value)) {
            errors.push('Please enter a valid CVV');
        }

        if (errors.length > 0) {
            this.showFormErrors(errors);
            return false;
        }

        return true;
    }

    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate card number using Luhn algorithm
     */
    isValidCardNumber(cardNumber) {
        const cleaned = cardNumber.replace(/\D/g, '');
        if (cleaned.length < 13 || cleaned.length > 19) {
            return false;
        }

        let sum = 0;
        let isEven = false;

        for (let i = cleaned.length - 1; i >= 0; i--) {
            let digit = parseInt(cleaned.charAt(i));

            if (isEven) {
                digit *= 2;
                if (digit > 9) {
                    digit -= 9;
                }
            }

            sum += digit;
            isEven = !isEven;
        }

        return sum % 10 === 0;
    }

    /**
     * Validate expiry date
     */
    isValidExpiryDate(expiryDate) {
        const [month, year] = expiryDate.split('/').map(s => s.trim());
        
        if (!month || !year) {
            return false;
        }

        const monthNum = parseInt(month);
        const yearNum = parseInt(year);
        
        if (monthNum < 1 || monthNum > 12) {
            return false;
        }

        const currentDate = new Date();
        const currentYear = currentDate.getFullYear();
        const currentMonth = currentDate.getMonth() + 1;

        const fullYear = yearNum + (yearNum < 100 ? 2000 : 0);

        if (fullYear < currentYear) {
            return false;
        }

        if (fullYear === currentYear && monthNum < currentMonth) {
            return false;
        }

        return true;
    }

    /**
     * Validate CVV
     */
    isValidCVV(cvv) {
        const cvvRegex = /^\d{3,4}$/;
        return cvvRegex.test(cvv);
    }

    /**
     * Show form validation errors
     */
    showFormErrors(errors) {
        const errorContainer = document.querySelector('.form-errors') || 
                              document.querySelector('.error-messages');
        
        if (errorContainer) {
            errorContainer.innerHTML = errors.map(error => 
                `<div class="error-item">${error}</div>`
            ).join('');
            errorContainer.style.display = 'block';
        }
    }

    /**
     * Show user-friendly error message
     */
    showUserFriendlyError(message) {
        const errorContainer = document.querySelector('.payment-errors') || 
                              document.querySelector('.error-container');
        
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Payment Error:</strong> ${message}
                    <button type="button" class="close" data-dismiss="alert">
                        <span>&times;</span>
                    </button>
                </div>
            `;
            errorContainer.style.display = 'block';
        }

        // Auto-hide error after 10 seconds
        setTimeout(() => {
            if (errorContainer) {
                errorContainer.style.display = 'none';
            }
        }, 10000);
    }

    /**
     * Show success message
     */
    showSuccessMessage(message) {
        const successContainer = document.querySelector('.payment-success') || 
                                document.querySelector('.success-container');
        
        if (successContainer) {
            successContainer.innerHTML = `
                <div class="alert alert-success" role="alert">
                    <i class="fas fa-check-circle"></i>
                    ${message}
                    <button type="button" class="close" data-dismiss="alert">
                        <span>&times;</span>
                    </button>
                </div>
            `;
            successContainer.style.display = 'block';
        }

        // Auto-hide success after 5 seconds
        setTimeout(() => {
            if (successContainer) {
                successContainer.style.display = 'none';
            }
        }, 5000);
    }

    /**
     * Handle AJAX payment errors
     */
    handlePaymentError(response) {
        let errorMessage = 'Payment processing failed. Please try again.';
        
        if (response && response.error) {
            errorMessage = response.error;
        } else if (response && response.message) {
            errorMessage = response.message;
        }

        this.showUserFriendlyError(errorMessage);
        this.logError('Payment Error', errorMessage);
    }

    /**
     * Handle network errors
     */
    handleNetworkError(error) {
        let message = 'Network error. Please check your internet connection.';
        
        if (error.name === 'TimeoutError') {
            message = 'Request timed out. Please try again.';
        } else if (error.name === 'AbortError') {
            message = 'Request was cancelled.';
        }

        this.showUserFriendlyError(message);
        this.logError('Network Error', error);
    }

    /**
     * Log errors to console and server
     */
    logError(errorType, errorDetails) {
        console.error(`${errorType}:`, errorDetails);
        
        // Send error to server for monitoring
        if (typeof errorDetails === 'object') {
            errorDetails = JSON.stringify(errorDetails);
        }

        fetch('/api/log-error/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                error_type: errorType,
                error_details: errorDetails,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
                url: window.location.href
            })
        }).catch(() => {
            // Ignore errors when logging errors
        });
    }

    /**
     * Get CSRF token from meta tag
     */
    getCSRFToken() {
        const tokenElement = document.querySelector('meta[name="csrf-token"]');
        return tokenElement ? tokenElement.getAttribute('content') : '';
    }

    /**
     * Setup retry mechanism for failed payments
     */
    setupRetryMechanism() {
        const retryButtons = document.querySelectorAll('.retry-payment-btn');
        retryButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Retrying...';
                
                // Retry logic would go here
                setTimeout(() => {
                    button.disabled = false;
                    button.innerHTML = 'Retry Payment';
                }, 3000);
            });
        });
    }

    /**
     * Show loading state during payment processing
     */
    showPaymentProcessing() {
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
    }

    /**
     * Hide loading state
     */
    hidePaymentProcessing() {
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Complete Payment';
        }
    }
}

// Initialize payment error handling when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const paymentErrorHandler = new PaymentErrorHandler();
    
    // Setup retry mechanism
    paymentErrorHandler.setupRetryMechanism();
    
    // Handle checkout form submission
    const checkoutForm = document.querySelector('#checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', (e) => {
            paymentErrorHandler.showPaymentProcessing();
        });
    }
});

// Export for use in other modules
window.PaymentErrorHandler = PaymentErrorHandler;