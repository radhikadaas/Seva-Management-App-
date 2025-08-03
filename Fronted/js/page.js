let allEntries = [];
let currentSort = "desc";
let currentSearchField = "paath_name"; // Default to name-based search

const tableBody = document.querySelector("tbody");
const selectedCategory = document.getElementById("selected-category");
const searchInput = document.getElementById("search-input");
const searchForm = document.getElementById("search-form");

function renderTable(entries) {
  tableBody.innerHTML = "";
  if (entries.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 text-center text-white">कोई सेवा नहीं मिली</td></tr>`;
    return;
  }

  entries.forEach((entry) => {
    const row = document.createElement("tr");
    row.className =
      "odd:bg-white odd:dark:bg-gray-900 even:bg-gray-50 even:dark:bg-gray-800 border-b dark:border-gray-700 border-gray-200";
    row.innerHTML = `
      <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
        ${entry.paath_name}
      </th>
      <td class="px-6 py-4">${entry.person_name}</td>
      <td class="px-6 py-4">${entry.gotra_name}</td>
      <td class="px-6 py-4">${entry.start_date}</td>
      <td class="px-6 py-4">${entry.end_date}</td>
      <td class="px-6 py-4">
        <div class="flex items-center justify-between">
          <input type="checkbox" class="delete-checkbox w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded-sm focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600" data-id="${entry.id}" />
        </div>
      </td>
    `;
    tableBody.appendChild(row);
  });

  attachDeleteHandlers();
}

function fetchAndRender() {
  fetch("https://shriharivansh-backend.onrender.com/data")
    .then((res) => res.json())
    .then((data) => {
      allEntries = data;
      sortAndRender();
    })
    .catch((err) => console.error("❌ Failed to fetch entries:", err));
}

function sortAndRender(entries = allEntries) {
  const sorted = [...entries];
  sorted.sort((a, b) => {
    const dateA = new Date(a.start_date);
    const dateB = new Date(b.start_date);
    return currentSort === "asc" ? dateA - dateB : dateB - dateA;
  });
  renderTable(sorted);
}

function showToast(id = "toast-danger", duration = 2000) {
  const toast = document.getElementById(id);
  if (!toast) return;

  toast.classList.remove("hidden");
  toast.classList.add("flex");

  setTimeout(() => {
    toast.classList.remove("flex");
    toast.classList.add("hidden");
  }, duration);
}

function attachDeleteHandlers() {
  const checkboxes = document.querySelectorAll(".delete-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", async function () {
      const id = this.dataset.id;
      try {
        const res = await fetch(`https://shriharivansh-backend.onrender.com/data/${id}`, {
          method: "DELETE",
        });
        if (!res.ok) throw new Error("Failed to delete");

        this.closest("tr")?.remove();
        showToast();
      } catch (err) {
        alert("सेवा हटाने में त्रुटि हुई 😢: " + err.message);
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fetchAndRender();

  document.querySelectorAll("input[name='search-radio']").forEach((radio) => {
    radio.addEventListener("change", () => {
      currentSearchField = radio.value;
      selectedCategory.textContent = radio.dataset.label;
    });
  });

  document.querySelectorAll("input[name='sort-radio']").forEach((radio) => {
    radio.addEventListener("change", () => {
      currentSort = radio.value;
      sortAndRender();
    });
  });
});

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = searchInput.value.trim();
  if (!query) return fetchAndRender();

  try {
    const res = await fetch(
      `https://shriharivansh-backend.onrender.com/search?field=${encodeURIComponent(
        currentSearchField
      )}&query=${encodeURIComponent(query)}`
    );
    const data = await res.json();
    sortAndRender(data);
  } catch (err) {
    console.error("❌ Failed to fetch search results:", err);
  }
});


