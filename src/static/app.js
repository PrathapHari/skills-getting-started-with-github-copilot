document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Reset activity select (avoid duplicate options)
      activitySelect.innerHTML = '<option value="">Select an activity</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - (details.participants?.length || 0);

        // build participants section (bulleted list or empty state)
        let participantsHtml;
        if (details.participants && details.participants.length > 0) {
          const items = details.participants
            .map((p) => `<li><span class="participant-name">${escapeHtml(p)}</span><button class="delete-btn" data-activity="${escapeHtml(name)}" data-email="${escapeHtml(p)}" title="Unregister">✕</button></li>`)
            .join("");
          participantsHtml = `
            <div class="participants">
              <h5>Participants</h5>
              <ul>${items}</ul>
            </div>
          `;
        } else {
          participantsHtml = `<div class="participants empty">No participants yet</div>`;
        }

        activityCard.innerHTML = `
          <h4>${escapeHtml(name)}</h4>
          <p>${escapeHtml(details.description)}</p>
          <p><strong>Schedule:</strong> ${escapeHtml(details.schedule)}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHtml}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      activitiesList.addEventListener("click", async (event) => {
        if (event.target.classList.contains("delete-btn")) {
          const deleteBtn = event.target;
          const activity = deleteBtn.dataset.activity;
          const email = deleteBtn.dataset.email;

          if (!confirm(`Unregister ${email} from ${activity}?`)) {
            return;
          }

          try {
            const response = await fetch(
              `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
              {
                method: "POST",
              }
            );

            if (response.ok) {
              // Refresh the activities list
              fetchActivities();
            } else {
              const result = await response.json();
              alert(result.detail || "Failed to unregister participant");
            }
          } catch (error) {
            alert("Failed to unregister participant. Please try again.");
            console.error("Error unregistering:", error);
          }
        }
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // simple HTML escape to avoid injection when using innerHTML
  function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
