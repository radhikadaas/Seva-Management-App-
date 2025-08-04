document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const paath = document.getElementById("paath").value;
    const person = document.getElementById("person").value;
    const gotra = document.getElementById("gotra").value;
    const startRaw = document.getElementById("datepicker-range-start").value;
    const endRaw = document.getElementById("datepicker-range-end").value;

    // Convert MM/DD/YYYY ➜ YYYY-MM-DD
    const toISO = (dateStr) => {
      const [month, day, year] = dateStr.split("/");
      return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
    };

    const payload = {
      paath_name: paath,
      person_name: person,
      gotra_name: gotra,
      start_date: toISO(startRaw),
      end_date: toISO(endRaw),
    };

    console.log("Payload being sent:", payload);

    try {
      const res = await fetch("https://seva-management-app.onrender.com/data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to save");

      const toast = document.getElementById("toast-success");
      toast.classList.remove("hidden");
      toast.classList.add("flex");

      setTimeout(() => {
        toast.classList.add("hidden");
      }, 2000);

      form.reset();
    } catch (err) {
      alert("सेवा सेव करने में त्रुटि हुई 😢: " + err.message);
    }
  });
});
