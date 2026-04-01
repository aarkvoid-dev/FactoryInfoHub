"""
Comprehensive logging configuration for the Factory InfoHub payment system.
This module provides structured logging for payment processing, webhooks, and error handling.
"""

import logging
import logging.handlers
import os
from django.conf import settings


class PaymentLogger:
    """Centralized logging class for payment-related operations"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for payment system"""
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.handlers.RotatingFileHandler(
                    os.path.join(log_dir, 'payment_system.log'),
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                ),
                logging.StreamHandler()  # Console output
            ]
        )
        
        # Payment-specific logger
        self.payment_logger = logging.getLogger('payment_system')
        self.payment_logger.setLevel(logging.DEBUG)
        
        # Webhook logger
        self.webhook_logger = logging.getLogger('payment_webhooks')
        self.webhook_logger.setLevel(logging.INFO)
        
        # Error logger
        self.error_logger = logging.getLogger('payment_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Security logger
        self.security_logger = logging.getLogger('payment_security')
        self.security_logger.setLevel(logging.WARNING)
        
        # Performance logger
        self.performance_logger = logging.getLogger('payment_performance')
        self.performance_logger.setLevel(logging.INFO)
    
    def log_payment_attempt(self, user_id, amount, gateway, order_id):
        """Log payment attempt"""
        self.payment_logger.info(
            f"Payment attempt - User: {user_id}, Amount: {amount}, "
            f"Gateway: {gateway}, Order: {order_id}"
        )
    
    def log_payment_success(self, user_id, amount, gateway, order_id, transaction_id):
        """Log successful payment"""
        self.payment_logger.info(
            f"Payment success - User: {user_id}, Amount: {amount}, "
            f"Gateway: {gateway}, Order: {order_id}, Transaction: {transaction_id}"
        )
    
    def log_payment_failure(self, user_id, amount, gateway, order_id, error_message):
        """Log payment failure"""
        self.error_logger.error(
            f"Payment failure - User: {user_id}, Amount: {amount}, "
            f"Gateway: {gateway}, Order: {order_id}, Error: {error_message}"
        )
    
    def log_webhook_received(self, gateway, event_type, order_id):
        """Log webhook receipt"""
        self.webhook_logger.info(
            f"Webhook received - Gateway: {gateway}, Event: {event_type}, Order: {order_id}"
        )
    
    def log_webhook_processed(self, gateway, event_type, order_id, status):
        """Log webhook processing result"""
        self.webhook_logger.info(
            f"Webhook processed - Gateway: {gateway}, Event: {event_type}, "
            f"Order: {order_id}, Status: {status}"
        )
    
    def log_webhook_error(self, gateway, event_type, order_id, error_message):
        """Log webhook processing error"""
        self.error_logger.error(
            f"Webhook error - Gateway: {gateway}, Event: {event_type}, "
            f"Order: {order_id}, Error: {error_message}"
        )
    
    def log_email_sent(self, user_email, order_id, email_type):
        """Log email sending"""
        self.payment_logger.info(
            f"Email sent - User: {user_email}, Order: {order_id}, Type: {email_type}"
        )
    
    def log_email_failed(self, user_email, order_id, email_type, error_message):
        """Log email sending failure"""
        self.error_logger.error(
            f"Email failed - User: {user_email}, Order: {order_id}, "
            f"Type: {email_type}, Error: {error_message}"
        )
    
    def log_security_event(self, event_type, details, user_id=None):
        """Log security-related events"""
        self.security_logger.warning(
            f"Security event - Type: {event_type}, User: {user_id}, Details: {details}"
        )
    
    def log_performance_metric(self, operation, duration, details=None):
        """Log performance metrics"""
        self.performance_logger.info(
            f"Performance - Operation: {operation}, Duration: {duration}ms, Details: {details}"
        )


# Initialize the logging system
payment_logger = PaymentLogger()


def get_payment_logger():
    """Get the payment logger instance"""
    return payment_logger


def log_payment_attempt(user_id, amount, gateway, order_id):
    """Convenience function to log payment attempt"""
    payment_logger.log_payment_attempt(user_id, amount, gateway, order_id)


def log_payment_success(user_id, amount, gateway, order_id, transaction_id):
    """Convenience function to log payment success"""
    payment_logger.log_payment_success(user_id, amount, gateway, order_id, transaction_id)


def log_payment_failure(user_id, amount, gateway, order_id, error_message):
    """Convenience function to log payment failure"""
    payment_logger.log_payment_failure(user_id, amount, gateway, order_id, error_message)


def log_webhook_received(gateway, event_type, order_id):
    """Convenience function to log webhook receipt"""
    payment_logger.log_webhook_received(gateway, event_type, order_id)


def log_webhook_processed(gateway, event_type, order_id, status):
    """Convenience function to log webhook processing"""
    payment_logger.log_webhook_processed(gateway, event_type, order_id, status)


def log_webhook_error(gateway, event_type, order_id, error_message):
    """Convenience function to log webhook error"""
    payment_logger.log_webhook_error(gateway, event_type, order_id, error_message)


def log_email_sent(user_email, order_id, email_type):
    """Convenience function to log email sending"""
    payment_logger.log_email_sent(user_email, order_id, email_type)


def log_email_failed(user_email, order_id, email_type, error_message):
    """Convenience function to log email failure"""
    payment_logger.log_email_failed(user_email, order_id, email_type, error_message)


def log_security_event(event_type, details, user_id=None):
    """Convenience function to log security events"""
    payment_logger.log_security_event(event_type, details, user_id)


def log_performance_metric(operation, duration, details=None):
    """Convenience function to log performance metrics"""
    payment_logger.log_performance_metric(operation, duration, details)