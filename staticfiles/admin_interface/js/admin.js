// Admin Interface JavaScript
document.addEventListener('DOMContentLoaded', function() {
  // Toggle sidebar
  const toggleSidebar = document.querySelectorAll('.js-toggle-db-sidebar');
  const sidebar = document.querySelector('.dashboard__sidebar');

  toggleSidebar.forEach(button => {
    button.addEventListener('click', function() {
      sidebar.classList.toggle('-hidden');
    });
  });

  // Tabs functionality
  const tabs = document.querySelectorAll('.js-tabs');
  tabs.forEach(tab => {
    const buttons = tab.querySelectorAll('.js-tabs-button');
    const content = tab.querySelector('.js-tabs-content');

    buttons.forEach(button => {
      button.addEventListener('click', function() {
        const target = this.getAttribute('data-tab-target');

        // Remove active class from all buttons
        buttons.forEach(btn => btn.classList.remove('is-tab-el-active'));

        // Add active class to clicked button
        this.classList.add('is-tab-el-active');

        // Hide all tab panes
        const panes = content.querySelectorAll('.tabs__pane');
        panes.forEach(pane => pane.classList.remove('is-tab-el-active'));

        // Show target tab pane
        const targetPane = content.querySelector(target);
        if (targetPane) {
          targetPane.classList.add('is-tab-el-active');
        }
      });
    });
  });

  // Dropdown functionality
  const dropdowns = document.querySelectorAll('.dropdown');
  dropdowns.forEach(dropdown => {
    const button = dropdown.querySelector('.dropdown-toggle');
    const menu = dropdown.querySelector('.dropdown-menu');

    if (button) {
      button.addEventListener('click', function(e) {
        e.stopPropagation();
        menu.classList.toggle('show');
      });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
      if (!dropdown.contains(e.target)) {
        menu.classList.remove('show');
      }
    });
  });

  // Form validation
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      let isValid = true;

      // Validate required fields
      const requiredFields = form.querySelectorAll('[required]');
      requiredFields.forEach(field => {
        if (!field.value.trim()) {
          isValid = false;
          field.classList.add('error');
        } else {
          field.classList.remove('error');
        }
      });

      if (!isValid) {
        e.preventDefault();
        showNotification('Please fill in all required fields', 'error');
      }
    });
  });

  // Show notification
  function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  // Chart initialization (placeholder)
  function initCharts() {
    // This would be replaced with actual chart initialization code
    console.log('Charts initialized');
  }

  // Initialize everything
  initCharts();
});