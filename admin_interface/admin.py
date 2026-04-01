from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import PaymentIssueReport
from Karkahan.utils import get_view_analytics_summary
from Home.models import PageSection


@admin.register(PaymentIssueReport)
class PaymentIssueReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'order', 'user', 'issue_type', 'status', 'priority', 
        'reported_at', 'is_resolved', 'time_since_reported'
    ]
    list_filter = [
        'status', 'priority', 'issue_type', 'reported_at', 
        'payment_status_at_report', 'email_status_at_report'
    ]
    search_fields = [
        'order__order_number', 'user__username', 'user__email', 
        'user_description', 'admin_notes', 'resolution_notes'
    ]
    readonly_fields = [
        'id', 'reported_at', 'updated_at', 'resolved_at', 'escalated_at',
        'order_details', 'payment_status_at_report', 'email_status_at_report',
        'transaction_id_at_report', 'time_since_reported'
    ]
    fieldsets = (
        ('Report Information', {
            'fields': ('id', 'order', 'user', 'issue_type', 'status', 'priority', 'user_description')
        }),
        ('System Information', {
            'fields': (
                'ip_address', 'user_agent', 'browser_info', 
                'payment_status_at_report', 'email_status_at_report', 'transaction_id_at_report'
            )
        }),
        ('Order Snapshot', {
            'fields': ('order_details',)
        }),
        ('Resolution', {
            'fields': ('admin_notes', 'resolution_notes', 'resolved_by', 'resolved_at', 'escalated_at')
        }),
        ('Timestamps', {
            'fields': ('reported_at', 'updated_at', 'time_since_reported')
        }),
    )
    
    actions = ['mark_as_resolved', 'escalate_issue', 'mark_as_under_review']
    
    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        qs = super().get_queryset(request)
        return qs.select_related('order', 'user', 'resolved_by')
    
    def time_since_reported(self, obj):
        """Display time elapsed since the issue was reported"""
        from django.utils import timezone
        time_diff = timezone.now() - obj.reported_at
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h ago"
        elif hours > 0:
            return f"{hours}h {minutes}m ago"
        else:
            return f"{minutes}m ago"
    time_since_reported.short_description = 'Time Since Reported'
    
    def is_resolved(self, obj):
        """Display if the issue is resolved"""
        if obj.status in ['resolved', 'closed']:
            return format_html('<span class="badge badge-success">Yes</span>')
        else:
            return format_html('<span class="badge badge-warning">No</span>')
    is_resolved.short_description = 'Resolved?'
    
    def mark_as_resolved(self, request, queryset):
        """Admin action to mark selected issues as resolved"""
        updated = 0
        for report in queryset:
            if report.status != 'resolved':
                report.mark_resolved(request.user, "Marked as resolved via admin action")
                updated += 1
        
        if updated > 0:
            messages.success(request, f'Successfully marked {updated} issue(s) as resolved.')
        else:
            messages.info(request, 'No issues were updated (already resolved).')
    
    mark_as_resolved.short_description = "Mark selected issues as resolved"
    
    def escalate_issue(self, request, queryset):
        """Admin action to escalate selected issues"""
        escalated = 0
        for report in queryset:
            if report.status != 'escalated':
                report.escalate(request.user, "Escalated via admin action")
                escalated += 1
        
        if escalated > 0:
            messages.success(request, f'Successfully escalated {escalated} issue(s).')
        else:
            messages.info(request, 'No issues were escalated (already escalated).')
    
    escalate_issue.short_description = "Escalate selected issues"
    
    def mark_as_under_review(self, request, queryset):
        """Admin action to mark selected issues as under review"""
        updated = 0
        for report in queryset:
            if report.status not in ['resolved', 'closed']:
                report.status = 'under_review'
                report.save()
                updated += 1
        
        if updated > 0:
            messages.success(request, f'Successfully marked {updated} issue(s) as under review.')
        else:
            messages.info(request, 'No issues were updated.')
    
    mark_as_under_review.short_description = "Mark selected issues as under review"
    
    def get_urls(self):
        """Add custom URLs for issue resolution"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/resolve/', self.admin_site.admin_view(self.resolve_issue), name='admin_interface_paymentissuereport_resolve'),
            path('<int:object_id>/escalate/', self.admin_site.admin_view(self.escalate_issue_view), name='admin_interface_paymentissuereport_escalate'),
        ]
        return custom_urls + urls
    
    def resolve_issue(self, request, object_id):
        """Custom view to resolve an issue with resolution notes"""
        report = get_object_or_404(PaymentIssueReport, id=object_id)
        
        if request.method == 'POST':
            resolution_notes = request.POST.get('resolution_notes', '')
            report.mark_resolved(request.user, resolution_notes)
            messages.success(request, f'Issue {report.id} has been resolved.')
            return redirect('admin:admin_interface_paymentissuereport_changelist')
        
        context = {
            **self.admin_site.each_context(request),
            'report': report,
            'title': f'Resolve Issue: {report.issue_type}'
        }
        return self.render_resolve_form(request, context)
    
    def escalate_issue_view(self, request, object_id):
        """Custom view to escalate an issue"""
        report = get_object_or_404(PaymentIssueReport, id=object_id)
        
        if request.method == 'POST':
            notes = request.POST.get('escalation_notes', '')
            report.escalate(request.user, notes)
            messages.success(request, f'Issue {report.id} has been escalated.')
            return redirect('admin:admin_interface_paymentissuereport_changelist')
        
        context = {
            **self.admin_site.each_context(request),
            'report': report,
            'title': f'Escalate Issue: {report.issue_type}'
        }
        return self.render_escalate_form(request, context)
    
    def render_resolve_form(self, request, context):
        """Render the resolve form template"""
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'admin/admin_interface/paymentissuereport/resolve.html', context)
    
    def render_escalate_form(self, request, context):
        """Render the escalate form template"""
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'admin/admin_interface/paymentissuereport/escalate.html', context)


