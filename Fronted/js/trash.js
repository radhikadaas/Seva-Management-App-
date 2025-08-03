// trash.js

const tableBody = document.querySelector("tbody");

function showToast(toastId, duration = 2000) {
  const toast = document.getElementById(toastId);
  if (!toast) return;

  toast.classList.remove("hidden");
  toast.classList.add("flex");

  setTimeout(() => {
    toast.classList.remove("flex");
    toast.classList.add("hidden");
  }, duration);
}

function renderTable(entries) {
  tableBody.innerHTML = "";

  if (entries.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="7" class="px-6 py-4 text-center text-white">कोई सेवा नहीं मिली</td></tr>`;
    return;
  }

  entries.forEach((entry) => {
    const row = document.createElement("tr");
    row.className =
      "odd:bg-white odd:dark:bg-gray-900 even:bg-gray-50 even:dark:bg-gray-800 border-b dark:border-gray-700 border-gray-200";

    row.innerHTML = `
      <td class="px-6 py-4 text-center">
        <input type="checkbox" class="restore-checkbox w-4 h-4" data-id="${entry.id}" />
      </td>
      <td class="px-6 py-4 text-center">
        <input type="checkbox" class="delete-checkbox w-4 h-4" data-id="${entry.id}" />
      </td>
      <td class="px-6 py-4">${entry.paath_name}</td>
      <td class="px-6 py-4">${entry.person_name}</td>
      <td class="px-6 py-4">${entry.gotra_name}</td>
      <td class="px-6 py-4">${entry.start_date}</td>
      <td class="px-6 py-4">${entry.end_date}</td>
    `;

    tableBody.appendChild(row);
  });

  attachCheckboxHandlers();
}

function attachCheckboxHandlers() {
  document.querySelectorAll(".restore-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", async function () {
      const id = this.dataset.id;
      try {
        const res = await fetch(`https://shriharivansh-backend.onrender.com/trash/${id}/restore`, {
          method: "PATCH",
        });
        if (!res.ok) throw new Error("Restore failed");
        this.closest("tr").remove();
        showToast("toast-success");
      } catch (err) {
        alert("पुनः जोड़ने में त्रुटि हुई 😢: " + err.message);
      }
    });
  });

  document.querySelectorAll(".delete-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", async function () {
      const id = this.dataset.id;
      try {
        const res = await fetch(`https://shriharivansh-backend.onrender.com/trash/${id}`, {
          method: "DELETE",
        });
        if (!res.ok) throw new Error("Permanent delete failed");
        this.closest("tr").remove();
        showToast("toast-danger");
      } catch (err) {
        alert("स्थाई रूप से हटाने में त्रुटि हुई 😢: " + err.message);
      }
    });
  });
}

async function fetchTrashEntries() {
  try {
    const res = await fetch("https://shriharivansh-backend.onrender.com/trash");
    if (!res.ok) throw new Error("Failed to fetch trash entries");
    const data = await res.json();
    renderTable(data);
  } catch (err) {
    console.error("❌ Error fetching trash entries:", err);
  }
}

document.addEventListener("DOMContentLoaded", fetchTrashEntries);
