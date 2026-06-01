// Aptitude-test page: live progress, answer highlighting, client-side guard.
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("testForm");
  if (!form) return;

  const total = parseInt(form.dataset.total || "0", 10);
  const bar = document.getElementById("progressBar");
  const counter = document.getElementById("progressCounter");
  const submitBtn = document.getElementById("submitBtn");

  function answeredCount() {
    const names = new Set();
    form.querySelectorAll("input[type=radio]:checked").forEach((i) => names.add(i.name));
    return names.size;
  }

  function refresh() {
    const done = answeredCount();
    const pct = total ? Math.round((done / total) * 100) : 0;
    if (bar) {
      bar.style.width = pct + "%";
      bar.setAttribute("aria-valuenow", pct);
    }
    if (counter) counter.textContent = done + " / " + total + " answered";
    if (submitBtn) {
      submitBtn.disabled = done < total;
      submitBtn.textContent = done < total
        ? "Answer all questions to submit"
        : "Submit & See My Results";
    }
  }

  // Highlight selected options + update progress.
  form.querySelectorAll("input[type=radio]").forEach(function (input) {
    input.addEventListener("change", function () {
      // clear siblings sharing the same name
      form.querySelectorAll('input[name="' + input.name + '"]').forEach(function (sib) {
        const lbl = sib.closest("label");
        if (lbl) lbl.classList.remove("checked");
      });
      const lbl = input.closest("label");
      if (lbl) lbl.classList.add("checked");

      const card = input.closest(".q-card");
      if (card) card.classList.add("answered");
      refresh();
    });
  });

  // Final guard: block submit if anything is missing.
  form.addEventListener("submit", function (e) {
    if (answeredCount() < total) {
      e.preventDefault();
      alert("Please answer every question before submitting.");
      const firstUnanswered = findFirstUnanswered();
      if (firstUnanswered) firstUnanswered.scrollIntoView({ behavior: "smooth", block: "center" });
    } else {
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Analysing your answers…";
      }
    }
  });

  function findFirstUnanswered() {
    const cards = form.querySelectorAll(".q-card");
    for (const c of cards) {
      if (!c.querySelector("input[type=radio]:checked")) return c;
    }
    return null;
  }

  refresh();
});


