
document.addEventListener("DOMContentLoaded", () => {
  const badge = document.querySelector(".notification-badge");

  if (badge) {
    setInterval(() => {
      fetch("/admin/notifications/unread-count/")
        .then(res => res.json())
        .then(data => {
          if (data.unread_count > 0) {
            badge.textContent = data.unread_count;
            badge.style.display = "inline";
          } else {
            badge.style.display = "none";
          }
        })
        .catch(err => console.error("Notification fetch error:", err));
    }, 10000); // every 10 seconds
  }
});
