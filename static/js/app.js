/**
 * Global JavaScript helper utilities for Startup Idea Validator AI
 */
document.addEventListener("DOMContentLoaded", () => {
    // Initialize all Bootstrap tooltips if any
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));

    // Auto-dismiss alerts after 5 seconds
    const autoDismissAlerts = document.querySelectorAll(".alert-dismissible");
    autoDismissAlerts.forEach((alert) => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });

    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.querySelector(".sidebar");
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("show");
        });
    }
});
