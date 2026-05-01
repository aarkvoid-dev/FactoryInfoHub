from django.db import models
from django.conf import settings
from django.utils import timezone

class PaymentIssueReport(models.Model):
    """Model to track user-reported payment issues"""
    
    ISSUE_TYPE_CHOICES = [
        ('payment_failed', 'Payment Failed'),
        ('payment_pending', 'Payment Pending Too Long'),
        ('email_not_received', 'Order Email Not Received'),
        ('duplicate_charge', 'Duplicate Charge'),
        ('payment_verification', 'Payment Verification Issue'),
        ('other', 'Other Issue'),
    ]
    
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Link to existing Karkahan Order model
    order = models.ForeignKey('Karkahan.Order', on_delete=models.CASCADE, related_name='issue_reports')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_issue_reports')
    
    # Issue details
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # User description
    user_description = models.TextField(blank=True, help_text="User's description of the issue")
    
    # System information (auto-collected)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    browser_info = models.CharField(max_length=200, blank=True)
    
    # Issue details snapshot (auto-generated from order)
    order_details = models.JSONField(default=dict, help_text="Snapshot of order details at time of report")
    payment_status_at_report = models.CharField(max_length=20, blank=True)
    email_status_at_report = models.CharField(max_length=20, blank=True)
    transaction_id_at_report = models.CharField(max_length=255, blank=True)
    
    # Admin notes and resolution
    admin_notes = models.TextField(blank=True, help_text="Internal notes for support team")
    resolution_notes = models.TextField(blank=True, help_text="Resolution details")
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_issues')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    escalated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-reported_at']
        verbose_name = "Payment Issue Report"
        verbose_name_plural = "Payment Issue Reports"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['issue_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['reported_at']),
            models.Index(fields=['user']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"Issue {self.id} - Order {self.order.order_number} - {self.get_issue_type_display()}"

    def save(self, *args, **kwargs):
        # Auto-generate order details snapshot if not provided
        if not self.order_details:
            self.order_details = {
                'order_id': self.order.id,
                'order_number': self.order.order_number,
                'total_amount': str(self.order.total_amount),
                'payment_status': self.order.payment_status,
                'payment_completed': self.order.payment_completed,
                'email_status': self.order.email_status,
                'transaction_id': self.order.transaction_id,
                'gateway_used': self.order.gateway_used.name if self.order.gateway_used else None,
                'created_at': self.order.created_at.isoformat(),
            }
        
        # Update status fields from order
        self.payment_status_at_report = self.order.payment_status
        self.email_status_at_report = self.order.email_status
        self.transaction_id_at_report = self.order.transaction_id
        
        super().save(*args, **kwargs)

    def mark_resolved(self, resolved_by_user, resolution_notes=""):
        """Mark the issue as resolved"""
        self.status = 'resolved'
        self.resolved_by = resolved_by_user
        self.resolved_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.save()

    def escalate(self, escalated_by_user, notes=""):
        """Escalate the issue to higher support level"""
        self.status = 'escalated'
        self.escalated_at = timezone.now()
        self.admin_notes = f"{self.admin_notes}\n\nEscalated by {escalated_by_user.username} on {timezone.now()}: {notes}"
        self.save()

    @property
    def is_resolved(self):
        return self.status in ['resolved', 'closed']

    @property
    def time_since_reported(self):
        """Get time elapsed since the issue was reported"""
        return timezone.now() - self.reported_at

    def get_priority_color(self):
        """Get Bootstrap color class for priority level"""
        color_map = {
            'low': 'success',
            'medium': 'warning', 
            'high': 'danger',
            'urgent': 'dark'
        }
        return color_map.get(self.priority, 'secondary')