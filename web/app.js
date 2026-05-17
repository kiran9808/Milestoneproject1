(function () {
  const form = document.getElementById("prefs-form");
  const locationSelect = document.getElementById("location");
  const cuisineSelect = document.getElementById("cuisine");
  const minRatingInput = document.getElementById("min_rating");
  const minRatingOutput = document.getElementById("min_rating_value");
  const statusEl = document.getElementById("status");
  const errEl = document.getElementById("error");
  const outEl = document.getElementById("output");
  const disclaimerEl = document.getElementById("disclaimer");
  const summaryEl = document.getElementById("summary");
  const cardsEl = document.getElementById("cards");
  const selectionEl = document.getElementById("selection");

  async function loadLocationsIntoSelect() {
    locationSelect.innerHTML = '<option value="">Loading locations…</option>';
    locationSelect.disabled = true;
    try {
      const res = await fetch("/locations");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d.msg || JSON.stringify(d)).join("\n")
              : JSON.stringify(data);
        locationSelect.innerHTML = `<option value="">${escapeHtml(msg)}</option>`;
        locationSelect.disabled = false;
        showError(`HTTP ${res.status}: ${msg}`);
        return;
      }
      const locs = Array.isArray(data.locations) ? data.locations : [];
      locationSelect.innerHTML = "";
      const ph = document.createElement("option");
      ph.value = "";
      ph.textContent = locs.length ? "Choose a location…" : "No locations";
      locationSelect.appendChild(ph);
      for (const loc of locs) {
        const opt = document.createElement("option");
        opt.value = loc;
        opt.textContent = loc;
        locationSelect.appendChild(opt);
      }
      locationSelect.disabled = false;
    } catch (err) {
      locationSelect.innerHTML = '<option value="">Error</option>';
      locationSelect.disabled = false;
      throw err;
    }
  }

  async function loadCuisinesIntoSelect(forLocation) {
    var loc = (forLocation != null ? String(forLocation) : "").trim();
    if (!loc) {
      cuisineSelect.innerHTML = "";
      var ph0 = document.createElement("option");
      ph0.value = "";
      ph0.textContent = "Choose a location first";
      cuisineSelect.appendChild(ph0);
      cuisineSelect.disabled = true;
      return;
    }
    cuisineSelect.innerHTML = '<option value="">Loading cuisines…</option>';
    cuisineSelect.disabled = true;
    try {
      var q = new URLSearchParams({ location: loc });
      const res = await fetch("/cuisines?" + q.toString());
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d.msg || JSON.stringify(d)).join("\n")
              : JSON.stringify(data);
        cuisineSelect.innerHTML = `<option value="">${escapeHtml(msg)}</option>`;
        cuisineSelect.disabled = false;
        showError(`HTTP ${res.status}: ${msg}`);
        return;
      }
      const tags = Array.isArray(data.cuisines) ? data.cuisines : [];
      cuisineSelect.innerHTML = "";
      const any = document.createElement("option");
      any.value = "";
      any.textContent = tags.length ? "Any cuisine (optional)" : "No tags";
      cuisineSelect.appendChild(any);
      for (const tag of tags) {
        const opt = document.createElement("option");
        opt.value = tag;
        opt.textContent = tag;
        cuisineSelect.appendChild(opt);
      }
      cuisineSelect.disabled = false;
    } catch (err) {
      cuisineSelect.innerHTML = '<option value="">Error</option>';
      cuisineSelect.disabled = false;
      throw err;
    }
  }

  async function loadFormDropdowns() {
    hideError();
    try {
      await loadLocationsIntoSelect();
    } catch (e) {
      showError(e instanceof Error ? e.message : String(e));
    }
    try {
      await loadCuisinesIntoSelect("");
    } catch (e) {
      showError(e instanceof Error ? e.message : String(e));
    }
  }

  locationSelect.addEventListener("change", function () {
    loadCuisinesIntoSelect(locationSelect.value).catch(function (e) {
      showError(e instanceof Error ? e.message : String(e));
    });
  });

  function syncMinRatingDisplay() {
    const raw = parseFloat(minRatingInput.value);
    const v = Number.isFinite(raw) ? raw : 0;
    minRatingOutput.textContent = Number.isInteger(v) ? String(v) : v.toFixed(1);
    minRatingInput.setAttribute("aria-valuenow", minRatingOutput.textContent);
  }

  minRatingInput.addEventListener("input", syncMinRatingDisplay);
  syncMinRatingDisplay();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadFormDropdowns);
  } else {
    loadFormDropdowns();
  }

  function showError(msg) {
    errEl.textContent = msg;
    errEl.classList.remove("hidden");
    outEl.classList.add("hidden");
  }

  function hideError() {
    errEl.textContent = "";
    errEl.classList.add("hidden");
  }

  function fmtCost(n) {
    if (n == null || n === "") return "—";
    return `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  }

  function fmtRating(n) {
    if (n == null || n === "") return "—";
    return String(n);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();
    statusEl.textContent = "Calling API…";
    outEl.classList.add("hidden");
    form.querySelector('button[type="submit"]').disabled = true;

    const budgetRaw = parseFloat(form.budget_amount.value);
    const budgetAmount = Number.isFinite(budgetRaw) && budgetRaw >= 0 ? budgetRaw : 0;

    const body = {
      location: locationSelect.value.trim(),
      budget_amount: budgetAmount,
      min_rating: parseFloat(minRatingInput.value) || 0,
    };
    const cuisine = cuisineSelect.value.trim();
    if (cuisine) body.cuisine = cuisine;
    const prefs = form.additional_preferences.value.trim();
    if (prefs) body.additional_preferences = prefs;

    try {
      const res = await fetch("/recommendations/ranked", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const detail = data.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d.msg || JSON.stringify(d)).join("\n")
              : JSON.stringify(data);
        showError(`HTTP ${res.status}: ${msg}`);
        return;
      }

      disclaimerEl.textContent = data.disclaimer || "";
      if (data.summary) {
        summaryEl.textContent = data.summary;
        summaryEl.classList.remove("hidden");
      } else {
        summaryEl.classList.add("hidden");
      }

      document.getElementById("fallback-badge").classList.toggle("hidden", !data.used_llm_fallback);

      cardsEl.innerHTML = "";
      for (const it of data.items || []) {
        const div = document.createElement("div");
        div.className = "card";
        div.innerHTML = `
          <span class="rank">#${it.rank}</span>
          <h3>${escapeHtml(it.name)}</h3>
          <div class="meta">${it.location ? escapeHtml(it.location) + " · " : ""}${escapeHtml((it.cuisines || []).join(", ") || "—")}</div>
          <div class="meta">Rating: ${fmtRating(it.rating)} · Cost for two: ${fmtCost(it.cost)}</div>
          <p class="explanation">${escapeHtml(it.explanation || "")}</p>`;
        cardsEl.appendChild(div);
      }

      if (data.selection) {
        var s = data.selection;
        var parts = [
          "strict match = " + s.had_strict_match,
          "relaxations: " +
            ((s.relaxation_steps_applied || []).join(" → ") || "(none)"),
        ];
        if (s.cross_location_fallback) {
          parts.push(
            "expanded outside " +
              (s.expanded_from_location || locationSelect.value || "?") +
              " (other locations)",
          );
        }
        selectionEl.textContent = "Selection: " + parts.join("; ");
        selectionEl.classList.remove("hidden");
      } else {
        selectionEl.classList.add("hidden");
      }

      outEl.classList.remove("hidden");
    } catch (err) {
      showError(err instanceof Error ? err.message : String(err));
    } finally {
      statusEl.textContent = "";
      form.querySelector('button[type="submit"]').disabled = false;
    }
  });

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
})();
