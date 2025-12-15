/**
 * Real-time Form Validation JavaScript for Flask POS Application
 * Provides instant validation feedback for form fields
 */

class FormValidator {
    constructor(options = {}) {
        this.options = {
            validationEndpoint: '/api/validation/validate-field',
            formValidationEndpoint: '/api/validation/validate-form',
            passwordStrengthEndpoint: '/api/validation/validate-password-strength',
            businessRuleEndpoint: '/api/validation/validate-business-rule',
            sanitizeEndpoint: '/api/validation/sanitize-input',
            debounceDelay: 300,
            showSuccessMessages: true,
            showErrorMessages: true,
            ...options
        };
        
        this.debounceTimers = {};
        this.csrfToken = this.getCSRFToken();
        this.init();
    }
    
    init() {
        // Initialize validation for all forms with data-validation attribute
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeForms();
        });
    }
    
    initializeForms() {
        const forms = document.querySelectorAll('form[data-validation="true"]');
        forms.forEach(form => {
            this.setupFormValidation(form);
        });
    }
    
    setupFormValidation(form) {
        const fields = form.querySelectorAll('input, textarea, select');
        
        fields.forEach(field => {
            this.setupFieldValidation(field);
        });
        
        // Setup form submission validation
        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
                this.showFormError(form, 'Please fix the validation errors before submitting');
            }
        });
    }
    
    setupFieldValidation(field) {
        const fieldType = this.getFieldType(field);
        const fieldName = field.name || field.id;
        
        if (!fieldName) return;
        
        // Real-time validation on input change
        field.addEventListener('input', (e) => {
            this.debounceValidation(fieldName, () => {
                this.validateField(fieldName, e.target.value, fieldType);
            });
        });
        
        // Validation on blur
        field.addEventListener('blur', (e) => {
            this.validateField(fieldName, e.target.value, fieldType);
        });
        
        // Clear validation on focus
        field.addEventListener('focus', (e) => {
            this.clearFieldValidation(fieldName);
        });
    }
    
    validateField(fieldName, value, fieldType = 'text') {
        this.clearFieldValidation(fieldName);
        
        const data = {
            field_name: fieldName,
            value: value,
            field_type: fieldType
        };
        
        this.makeRequest(this.options.validationEndpoint, data)
            .then(response => {
                if (response.success) {
                    this.showFieldValidation(fieldName, response.validation);
                }
            })
            .catch(error => {
                console.error('Validation error:', error);
                this.showFieldError(fieldName, 'Validation service unavailable');
            });
    }
    
    validateForm(form) {
        const formData = new FormData(form);
        const formConfig = this.getFormConfig(form);
        
        const data = {
            form_data: this.formDataToObject(formData),
            form_config: formConfig
        };
        
        return this.makeRequest(this.options.formValidationEndpoint, data)
            .then(response => {
                if (response.success) {
                    this.showFormValidation(form, response.validation);
                    return response.validation.valid;
                }
                return false;
            })
            .catch(error => {
                console.error('Form validation error:', error);
                this.showFormError(form, 'Validation service unavailable');
                return false;
            });
    }
    
    validatePasswordStrength(password) {
        return this.makeRequest(this.options.passwordStrengthEndpoint, { password })
            .then(response => {
                if (response.success) {
                    return {
                        isValid: response.is_valid,
                        errors: response.errors,
                        score: response.strength_score
                    };
                }
                return { isValid: false, errors: ['Validation failed'], score: 0 };
            });
    }
    
    validateBusinessRule(fieldName, value) {
        const data = {
            field_name: fieldName,
            value: value
        };
        
        return this.makeRequest(this.options.businessRuleEndpoint, data)
            .then(response => {
                if (response.success) {
                    return {
                        isValid: response.is_valid,
                        message: response.message
                    };
                }
                return { isValid: false, message: 'Validation failed' };
            });
    }
    
    sanitizeInput(value, fieldType = 'text') {
        const data = {
            value: value,
            field_type: fieldType
        };
        
        return this.makeRequest(this.options.sanitizeEndpoint, data)
            .then(response => {
                if (response.success) {
                    return response.sanitized_value;
                }
                return value;
            });
    }
    
    showFieldValidation(fieldName, validation) {
        const field = document.querySelector(`[name="${fieldName}"], #${fieldName}`);
        if (!field) return;
        
        const container = field.closest('.form-group') || field.parentElement;
        const existingFeedback = container.querySelector('.validation-feedback');
        
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        const feedback = document.createElement('div');
        feedback.className = 'validation-feedback';
        
        if (validation.valid) {
            feedback.classList.add('valid');
            if (this.options.showSuccessMessages) {
                feedback.innerHTML = '<i class="fas fa-check-circle text-success"></i> Valid';
            }
            
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            feedback.classList.add('invalid');
            const errors = validation.errors.map(error => `<div><i class="fas fa-exclamation-circle"></i> ${error}</div>`).join('');
            feedback.innerHTML = errors;
            
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
        
        if (validation.warnings && validation.warnings.length > 0) {
            const warnings = validation.warnings.map(warning => `<div class="text-warning"><i class="fas fa-exclamation-triangle"></i> ${warning}</div>`).join('');
            feedback.innerHTML += warnings;
        }
        
        container.appendChild(feedback);
    }
    
    showFieldError(fieldName, message) {
        const field = document.querySelector(`[name="${fieldName}"], #${fieldName}`);
        if (!field) return;
        
        const container = field.closest('.form-group') || field.parentElement;
        const existingFeedback = container.querySelector('.validation-feedback');
        
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        const feedback = document.createElement('div');
        feedback.className = 'validation-feedback invalid';
        feedback.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        
        container.appendChild(feedback);
        
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
    
    clearFieldValidation(fieldName) {
        const field = document.querySelector(`[name="${fieldName}"], #${fieldName}`);
        if (!field) return;
        
        const container = field.closest('.form-group') || field.parentElement;
        const feedback = container.querySelector('.validation-feedback');
        
        if (feedback) {
            feedback.remove();
        }
        
        field.classList.remove('is-valid', 'is-invalid');
    }
    
    showFormValidation(form, validation) {
        // Clear existing form errors
        this.clearFormValidation(form);
        
        if (validation.valid) {
            return true;
        }
        
        // Show field-specific errors
        Object.entries(validation.field_results).forEach(([fieldName, result]) => {
            this.showFieldValidation(fieldName, result);
        });
        
        // Show form-level errors
        if (validation.form_errors && validation.form_errors.length > 0) {
            this.showFormError(form, validation.form_errors.join(', '));
        }
        
        return false;
    }
    
    showFormError(form, message) {
        const existingError = form.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }
        
        const error = document.createElement('div');
        error.className = 'alert alert-danger form-error';
        error.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        
        form.insertBefore(error, form.firstChild);
    }
    
    clearFormValidation(form) {
        // Clear field validations
        const fields = form.querySelectorAll('input, textarea, select');
        fields.forEach(field => {
            const fieldName = field.name || field.id;
            if (fieldName) {
                this.clearFieldValidation(fieldName);
            }
        });
        
        // Clear form errors
        const formErrors = form.querySelectorAll('.form-error');
        formErrors.forEach(error => error.remove());
    }
    
    debounceValidation(fieldName, callback) {
        if (this.debounceTimers[fieldName]) {
            clearTimeout(this.debounceTimers[fieldName]);
        }
        
        this.debounceTimers[fieldName] = setTimeout(callback, this.options.debounceDelay);
    }
    
    makeRequest(url, data) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': this.csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
    }
    
    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Fallback to hidden input
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        return csrfInput ? csrfInput.value : '';
    }
    
    getFieldType(field) {
        if (field.type === 'email') return 'email';
        if (field.type === 'password') return 'password';
        if (field.type === 'tel') return 'phone';
        if (field.tagName === 'TEXTAREA') return 'textarea';
        if (field.tagName === 'SELECT') return 'select';
        return 'text';
    }
    
    getFormConfig(form) {
        const formType = form.getAttribute('data-form-type');
        if (formType && window.VALIDATION_CONFIGS && window.VALIDATION_CONFIGS[formType]) {
            return window.VALIDATION_CONFIGS[formType];
        }
        
        // Generate config from form fields
        const config = {};
        const fields = form.querySelectorAll('input, textarea, select');
        fields.forEach(field => {
            const fieldName = field.name || field.id;
            if (fieldName) {
                config[fieldName] = {
                    type: this.getFieldType(field)
                };
            }
        });
        
        return config;
    }
    
    formDataToObject(formData) {
        const object = {};
        formData.forEach((value, key) => {
            object[key] = value;
        });
        return object;
    }
}

// Password strength meter
class PasswordStrengthMeter {
    constructor(inputElement, meterElement) {
        this.input = inputElement;
        this.meter = meterElement;
        this.init();
    }
    
    init() {
        if (!this.input || !this.meter) return;
        
        this.input.addEventListener('input', (e) => {
            this.updateStrength(e.target.value);
        });
        
        // Initialize meter
        this.updateStrength(this.input.value);
    }
    
    updateStrength(password) {
        const validator = new FormValidator();
        validator.validatePasswordStrength(password)
            .then(result => {
                this.updateMeter(result.score, result.errors);
            });
    }
    
    updateMeter(score, errors) {
        let strength = 'weak';
        let color = '#dc3545';
        let width = '25%';
        
        if (score >= 80) {
            strength = 'very-strong';
            color = '#28a745';
            width = '100%';
        } else if (score >= 60) {
            strength = 'strong';
            color = '#007bff';
            width = '75%';
        } else if (score >= 40) {
            strength = 'medium';
            color = '#ffc107';
            width = '50%';
        } else if (score >= 20) {
            strength = 'fair';
            color = '#fd7e14';
            width = '35%';
        }
        
        this.meter.style.width = width;
        this.meter.style.backgroundColor = color;
        this.meter.setAttribute('aria-valuenow', score);
        this.meter.setAttribute('aria-label', `Password strength: ${strength}`);
        
        // Update strength text
        const strengthText = this.meter.parentElement.querySelector('.password-strength-text');
        if (strengthText) {
            strengthText.textContent = strength.charAt(0).toUpperCase() + strength.slice(1).replace('-', ' ');
        }
        
        // Update error messages
        const errorContainer = this.meter.parentElement.querySelector('.password-errors');
        if (errorContainer) {
            errorContainer.innerHTML = errors.length > 0 
                ? errors.map(error => `<div><i class="fas fa-times text-danger"></i> ${error}</div>`).join('')
                : '';
        }
    }
}

// Initialize form validator
window.FormValidator = FormValidator;
window.PasswordStrengthMeter = PasswordStrengthMeter;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize global form validator
    window.formValidator = new FormValidator();
    
    // Initialize password strength meters
    const passwordInputs = document.querySelectorAll('input[type="password"][data-strength-meter="true"]');
    passwordInputs.forEach(input => {
        const meterId = input.getAttribute('data-strength-meter');
        const meter = document.getElementById(meterId);
        if (meter) {
            new PasswordStrengthMeter(input, meter);
        }
    });
    
    // Load validation configurations
    fetch('/api/validation/get-validation-config/registration')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.VALIDATION_CONFIGS = window.VALIDATION_CONFIGS || {};
                window.VALIDATION_CONFIGS.registration = data.config;
            }
        });
    
    fetch('/api/validation/get-validation-config/order')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.VALIDATION_CONFIGS = window.VALIDATION_CONFIGS || {};
                window.VALIDATION_CONFIGS.order = data.config;
            }
        });
    
    fetch('/api/validation/get-validation-config/settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.VALIDATION_CONFIGS = window.VALIDATION_CONFIGS || {};
                window.VALIDATION_CONFIGS.settings = data.config;
            }
        });
});