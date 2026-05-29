/**
 * Admin Form Helpers – Cascading Dropdown with Error Resilience
 * 
 * Fixes:
 * 1. Session timeout detection – catches HTML login redirect instead of JSON
 * 2. Server unresponsive detection – uses AbortController with timeout
 * 3. Dropdowns never get stuck in disabled state
 * 4. User-visible toast notifications for all errors
 * 5. Retry capability on failure
 */

(function() {
    'use strict';

    // ─── Toast Notification System ────────────────────────────────────────────
    function showToast(message, type) {
        // Remove existing toasts if too many
        const existing = document.querySelectorAll('.admin-toast');
        if (existing.length >= 3) {
            existing[0].remove();
        }

        const colors = {
            error: { bg: '#e74c3c', icon: 'fa-exclamation-circle' },
            warning: { bg: '#f39c12', icon: 'fa-exclamation-triangle' },
            info: { bg: '#3498db', icon: 'fa-info-circle' },
            success: { bg: '#27ae60', icon: 'fa-check-circle' }
        };
        const c = colors[type] || colors.info;

        const toast = document.createElement('div');
        toast.className = 'admin-toast';
        toast.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 99999;
            background: ${c.bg}; color: #fff; padding: 14px 20px;
            border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            font-size: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex; align-items: center; gap: 10px;
            max-width: 400px; min-width: 280px;
            animation: adminToastSlideIn 0.3s ease-out;
            pointer-events: auto;
        `;
        toast.innerHTML = `
            <i class="fas ${c.icon}" style="font-size: 18px;"></i>
            <span style="flex: 1;">${message}</span>
            <button onclick="this.parentElement.remove()" style="
                background: none; border: none; color: #fff; cursor: pointer;
                font-size: 18px; padding: 0; line-height: 1; opacity: 0.8;
            ">&times;</button>
        `;

        // Inject animation keyframes if not already present
        if (!document.getElementById('admin-toast-styles')) {
            const style = document.createElement('style');
            style.id = 'admin-toast-styles';
            style.textContent = `
                @keyframes adminToastSlideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(toast);

        // Auto-dismiss after 8 seconds (longer for users to notice)
        setTimeout(function() {
            if (toast.parentElement) {
                toast.style.transition = 'opacity 0.3s';
                toast.style.opacity = '0';
                setTimeout(function() { if (toast.parentElement) toast.remove(); }, 300);
            }
        }, 8000);
    }

    // ─── Session Check – Detect if response is login page ────────────────────
    function isHtmlResponse(text) {
        return text.trim().toLowerCase().startsWith('<!doctype') || 
               text.trim().toLowerCase().startsWith('<html') ||
               /<form.*login/i.test(text);
    }

    // ─── Improved loadData with timeout, session detection, retry ────────────
    window.loadCascadeData = function(url, targetElement, placeholderName, parentElement) {
        if (!targetElement) return;

        targetElement.innerHTML = '<option value="">⏳ Loading ' + placeholderName + '...</option>';
        targetElement.disabled = true;

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(function() {
            controller.abort();
        }, 15000); // 15 second timeout

        var retryCount = 0;
        var maxRetries = 2;

        function attemptLoad() {
            fetch(url, { signal: controller.signal })
                .then(function(response) {
                    clearTimeout(timeoutId);
                    
                    // Check content-type header
                    var contentType = response.headers.get('content-type') || '';
                    
                    if (!response.ok) {
                        throw new Error('Server returned ' + response.status + ' ' + response.statusText);
                    }
                    
                    return response.text().then(function(text) {
                        // Check if it's HTML (session redirect / login page)
                        if (isHtmlResponse(text)) {
                            throw new Error('SESSION_EXPIRED');
                        }
                        
                        // Try to parse as JSON
                        try {
                            return JSON.parse(text);
                        } catch(e) {
                            throw new Error('Invalid response format (not JSON)');
                        }
                    });
                })
                .then(function(data) {
                    targetElement.innerHTML = '<option value="">Select ' + placeholderName + '</option>';
                    if (Array.isArray(data)) {
                        data.forEach(function(item) {
                            var option = new Option(item.name, item.id);
                            targetElement.add(option);
                        });
                    }
                    targetElement.disabled = false;
                })
                .catch(function(error) {
                    clearTimeout(timeoutId);

                    if (error.message === 'SESSION_EXPIRED') {
                        // Session expired – show prominent warning
                        targetElement.innerHTML = '<option value="">⚠️ Session expired – please refresh</option>';
                        targetElement.disabled = false;
                        showToast(
                            'Your session has expired. Please <a href="javascript:location.reload()" style="color:#fff;font-weight:bold;text-decoration:underline;">refresh the page</a> to continue.',
                            'error'
                        );
                        return;
                    }

                    if (error.name === 'AbortError') {
                        // Timeout
                        if (retryCount < maxRetries) {
                            retryCount++;
                            targetElement.innerHTML = '<option value="">⏳ Retrying (' + retryCount + '/' + maxRetries + ')...</option>';
                            setTimeout(attemptLoad, 1500);
                            return;
                        }
                        targetElement.innerHTML = '<option value="">⚠️ Server not responding</option>';
                        targetElement.disabled = false;
                        showToast(
                            'Server is not responding for "' + placeholderName + '" dropdown. ' +
                            'Please <a href="javascript:location.reload()" style="color:#fff;font-weight:bold;text-decoration:underline;">refresh the page</a> or try again later.',
                            'error'
                        );
                    } else {
                        // Generic error
                        if (retryCount < maxRetries) {
                            retryCount++;
                            targetElement.innerHTML = '<option value="">⏳ Retrying (' + retryCount + '/' + maxRetries + ')...</option>';
                            setTimeout(attemptLoad, 1500);
                            return;
                        }
                        targetElement.innerHTML = '<option value="">⚠️ Error loading data</option>';
                        targetElement.disabled = false;
                        showToast(
                            'Error loading ' + placeholderName + '. The server may be unavailable. ' +
                            'Please <a href="javascript:location.reload()" style="color:#fff;font-weight:bold;text-decoration:underline;">refresh</a> and try again.',
                            'warning'
                        );
                    }
                });
        }

        attemptLoad();
    };

    // ─── Clear downstream selects ─────────────────────────────────────────────
    window.clearDownstreamSelects = function(selectors) {
        selectors.forEach(function(selector) {
            var el = document.querySelector(selector);
            if (el) {
                el.innerHTML = '<option value="">Select...</option>';
                el.disabled = true;
            }
        });
    };

    // ─── Auto-refresh guard ──────────────────────────────────────────────────
    // Periodically check if we can still communicate with the server
    // (only when page has been idle for a while)
    var lastActivity = Date.now();
    document.addEventListener('click', function() { lastActivity = Date.now(); });
    document.addEventListener('keydown', function() { lastActivity = Date.now(); });

    // After 25 minutes of inactivity, warn user about potential session expiry
    setTimeout(function() {
        var idleTime = Date.now() - lastActivity;
        if (idleTime > 25 * 60 * 1000) {
            showToast(
                'You have been inactive for a while. Your session may expire soon. ' +
                '<a href="javascript:location.reload()" style="color:#fff;font-weight:bold;text-decoration:underline;">Refresh now</a> to stay logged in.',
                'warning'
            );
        }
    }, 25 * 60 * 1000);

})();