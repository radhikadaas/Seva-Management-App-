document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("tbody");
  const dateInput = document.getElementById("datepicker-custom");

  function renderTable(entries) {
    tableBody.innerHTML = "";

    if (!Array.isArray(entries) || entries.length === 0) {
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

  function fetchAll() {
    fetch("https://shriharivansh-backend.onrender.com/data")
      .then((res) => res.json())
      .then((data) => renderTable(data))
      .catch(() => {
        tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 text-center text-white">सेवा लोड करने में त्रुटि</td></tr>`;
      });
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
    document.querySelectorAll(".delete-checkbox").forEach((checkbox) => {
      checkbox.addEventListener("change", async function () {
        const id = this.dataset.id;
        try {
          const res = await fetch(`https://shriharivansh-backend.onrender.com/data/${id}`, {
            method: "DELETE",
          });
          if (!res.ok) throw new Error();
          this.closest("tr")?.remove();
          showToast();
        } catch {
          alert("सेवा हटाने में त्रुटि हुई 😢");
        }
      });
    });
  }

  async function searchByDate(input) {
    if (!input) return fetchAll();

    try {
      let formattedDate = input;

      if (input.includes("/")) {
        const [mm, dd, yyyy] = input.split("/");
        formattedDate = `${yyyy}-${mm.padStart(2, "0")}-${dd.padStart(2, "0")}`;
      }

      const res = await fetch(
        `https://shriharivansh-backend.onrender.com/search-by-date?date=${encodeURIComponent(
          formattedDate
        )}`
      );
      if (!res.ok) throw new Error();

      const data = await res.json();
      renderTable(data);
    } catch {
      tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 text-center text-white">तिथि से सेवा लोड नहीं हुई</td></tr>`;
    }
  }

  fetchAll();

  const handleDateChange = () => searchByDate(dateInput.value.trim());
  dateInput.addEventListener("change", handleDateChange);
  dateInput.addEventListener("changeDate", handleDateChange);
  dateInput.addEventListener("datepicker:changeDate", handleDateChange);
});
