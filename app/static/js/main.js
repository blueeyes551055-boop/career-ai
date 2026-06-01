// General UI behaviour shared across the dashboard.
document.addEventListener("DOMContentLoaded", function () {
  // Mobile sidebar toggle
  const btn = document.querySelector("[data-toggle-sidebar]");
  const sidebar = document.querySelector(".sidebar");
  const backdrop = document.querySelector(".sidebar-backdrop");

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("show");
  }
  if (btn && sidebar) {
    btn.addEventListener("click", function () {
      sidebar.classList.toggle("open");
      if (backdrop) backdrop.classList.toggle("show");
    });
  }
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  // Auto-dismiss flash alerts after 5s
  document.querySelectorAll(".alert-dismissible").forEach(function (el) {
    setTimeout(function () {
      try {
        bootstrap.Alert.getOrCreateInstance(el).close();
      } catch (e) { /* ignore */ }
    }, 5000);
  });
});


