/* =========================================================================
   ABC BANK ATM — client-side behaviour.
   MODULE 7 (JS validation) note honoured throughout: every check here is
   advisory/UX only. Django re-validates everything server-side.
   ========================================================================= */

document.addEventListener("DOMContentLoaded", () => {
  startClock();
  wireNumericInputs();
  wireQuickAmounts();
  wireLoginSubmit();
  wireProcessingSubmit();
  animateBalanceFigures();
  autoFadeAlerts();
});

/* -- Live clock in the screen header, like a real terminal -- */
function startClock() {
  const el = document.querySelector("[data-clock]");
  if (!el) return;
  const tick = () => {
    const now = new Date();
    el.textContent = now.toLocaleString(undefined, {
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  };
  tick();
  setInterval(tick, 1000);
}

/* -- Restrict PIN / card-number / amount fields to sane characters live -- */
function wireNumericInputs() {
  document.querySelectorAll('input[name="card_number"], input[data-card-number="true"], input[id*="card_number"]').forEach((input) => {
    const formatCard = () => {
      let raw = input.value.replace(/\D/g, "").slice(0, 16);
      let formatted = raw.replace(/(\d{4})(?=\d)/g, "$1 ");
      input.value = formatted;
      clearFieldError(input);
    };
    ["input", "keyup", "paste", "change"].forEach((evt) => input.addEventListener(evt, formatCard));
    if (input.value) formatCard();
  });

  document.querySelectorAll('input[data-numeric="digits"]').forEach((input) => {
    input.addEventListener("input", () => {
      input.value = input.value.replace(/\D/g, "");
      clearFieldError(input);
    });
  });

  document.querySelectorAll('input[data-numeric="amount"]').forEach((input) => {
    input.addEventListener("input", () => {
      input.value = input.value.replace(/[^\d.]/g, "");
      clearFieldError(input);
    });
  });
}

function clearFieldError(input) {
  input.classList.remove("is-invalid");
  const err = input.closest(".atm-field")?.querySelector(".field-error.js-error");
  if (err) err.remove();
}

function showFieldError(input, message) {
  input.classList.add("is-invalid");
  const field = input.closest(".atm-field");
  if (!field) return;
  let err = field.querySelector(".field-error.js-error");
  if (!err) {
    err = document.createElement("div");
    err.className = "field-error js-error";
    field.appendChild(err);
  }
  err.textContent = message;
}

/* -- Quick amount chips fill the amount field (withdraw / deposit) -- */
function wireQuickAmounts() {
  document.querySelectorAll(".chip[data-amount]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const target = document.querySelector("#id_amount");
      if (!target) return;
      target.value = chip.dataset.amount;
      target.focus();
      clearFieldError(target);
    });
  });
}

/* -- Login: play the "card insert" animation before the form posts -- */
function wireLoginSubmit() {
  const form = document.querySelector("#login-form");
  if (!form) return;
  const card = document.querySelector(".atm-card-graphic");

  form.addEventListener("submit", (event) => {
    const cardInput = form.querySelector('input[name="card_number"]');
    const pinInput = form.querySelector('input[name="pin"]');
    let valid = true;

    const rawCardDigits = cardInput.value.replace(/\s+/g, "");
    if (!/^\d{16}$/.test(rawCardDigits)) {
      showFieldError(cardInput, "Enter all 16 digits of the card number.");
      valid = false;
    }
    if (!/^\d{4}$/.test(pinInput.value)) {
      showFieldError(pinInput, "PIN must be exactly 4 digits.");
      valid = false;
    }
    if (!valid) {
      event.preventDefault();
      return;
    }

    if (card && !form.dataset.submitted) {
      event.preventDefault();
      form.dataset.submitted = "true";
      card.classList.add("inserting");
      showProcessing(form.closest(".screen"), "Reading card…");
      setTimeout(() => form.submit(), 850);
    }
  });
}

/* -- Every "action" form (withdraw/deposit/transfer/pin change) gets a
      brief, honest processing pause so the transaction feels real -- */
function wireProcessingSubmit() {
  document.querySelectorAll("form[data-processing]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (form.dataset.submitted) return;
      // Run native validation first; if invalid, let the browser show it.
      if (!form.checkValidity()) return;
      event.preventDefault();
      form.dataset.submitted = "true";
      const label = form.dataset.processing || "Processing…";
      showProcessing(form.closest(".screen"), label);
      setTimeout(() => form.submit(), 700);
    });
  });
}

function showProcessing(screenEl, label) {
  if (!screenEl) return;
  const overlay = document.createElement("div");
  overlay.className = "processing-overlay";
  overlay.innerHTML = `<div class="spinner"></div><span>${label}</span>`;
  screenEl.appendChild(overlay);
}

/* -- Count the balance up from 0 so it feels alive on load -- */
function animateBalanceFigures() {
  document.querySelectorAll("[data-count-to]").forEach((el) => {
    const target = parseFloat(el.dataset.countTo);
    if (Number.isNaN(target)) return;
    const duration = 700;
    const start = performance.now();

    function frame(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = target * eased;
      el.textContent = "₹" + value.toLocaleString("en-IN", { maximumFractionDigits: 0 });
      if (progress < 1) requestAnimationFrame(frame);
      else el.textContent = "₹" + target.toLocaleString("en-IN", { maximumFractionDigits: 2 });
    }
    requestAnimationFrame(frame);
  });
}

/* -- Success banners fade after a while; errors stay put -- */
function autoFadeAlerts() {
  document.querySelectorAll(".atm-alert.success").forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s ease";
      alert.style.opacity = "0";
    }, 4500);
  });
}
