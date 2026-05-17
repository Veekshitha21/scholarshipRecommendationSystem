const REGISTERED_KEY = "scholarmatch_registered";

const state = {
  recommendations: [],
  registered: loadRegistered(),
  tickerData: [],
  apiMetrics: null
};

const filterForm = document.getElementById("filterForm");
const recommendationCards = document.getElementById("recommendationCards");
const registeredCards = document.getElementById("registeredCards");
const recommendationCount = document.getElementById("recommendationCount");
const registeredCount = document.getElementById("registeredCount");
const liveTicker = document.getElementById("liveTicker");
const cardTemplate = document.getElementById("scholarshipCardTemplate");
const statusBox = document.getElementById("statusBox");
const emptyState = document.getElementById("emptyState");
const emptyRegistered = document.getElementById("emptyRegistered");

init();

async function init() {
  renderRegistered();
  renderRecommendations();
  setStatus("Enter your profile and search — recommendations are powered by machine learning analysis.", "info");

  await loadTickerFromDataset();
  startTickerAutoScroll();

  filterForm.addEventListener("submit", (e) => {
    e.preventDefault();
    (async () => {
      setStatus("Analyzing your profile…", "info");
      if (statusBox) statusBox.style.display = "block";

      const user = {
        marks: Number(document.getElementById("marks").value || 0),
        income: Number(document.getElementById("income").value || 0),
        class_level: (document.getElementById("class_level")?.value || "any").toLowerCase(),
        category: (document.getElementById("category").value || "any").toLowerCase(),
        gender: (document.getElementById("gender").value || "any").toLowerCase(),
        disability: (document.getElementById("disability").value || "no").toLowerCase(),
        state: (document.getElementById("state")?.value || "").trim().toLowerCase(),
        education_level: (document.getElementById("education_level")?.value || "any").toLowerCase()
      };

      const ok = await fetchFromApi(user);
      if (!ok) {
        state.recommendations = [];
        renderRecommendations();
      }
    })();
  });
}

/** Ticker: real names from the same CSV the model uses (no client-side fake scholarships). */
async function loadTickerFromDataset() {
  try {
    const res = await fetch("/api/dataset-preview?limit=40");
    if (!res.ok) throw new Error("preview failed");
    const data = await res.json();
    const names = Array.isArray(data.scholarships) ? data.scholarships : [];
    state.tickerData = names.filter(Boolean).map((name) => ({ name: String(name) }));
  } catch {
    state.tickerData = [];
  }
  renderTicker();
}

async function fetchFromApi(user) {
  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(user)
    });

    if (!res.ok) throw new Error("API error");
    const data = await res.json();
    if (!data || !Array.isArray(data.results)) throw new Error("Bad API response");

    state.apiMetrics = data.metrics || null;

    state.recommendations = data.results
      .map((r) => ({
        scholarship_name: r.name,
        score: r.score,
        eligible: Boolean(r.eligible),
        link: r.link,
        success_probability: Number(r.success_probability ?? 0),
        chance_level: String(r.chance_level || "Unknown"),
        max_income: r.max_income,
        scholarship_amount: r.scholarship_amount,
        education_level: normalizeEducationLevel(r.education_level),
        gender: r.gender || "any",
        category: r.category || "any",
        disability: r.disability || "no",
        state: r.state || "any",
        ml_similarity: r.ml_similarity,
        ml_score: r.ml_score,
        rule_score: r.rule_score
      }))
      .sort((a, b) => {
        if (a.eligible !== b.eligible) return (b.eligible ? 1 : 0) - (a.eligible ? 1 : 0);
        return b.score - a.score;
      });

    state.tickerData = state.recommendations.slice(0, 16).map((item) => ({
      name: item.scholarship_name,
      score: item.score
    }));
    renderTicker();

    renderRecommendations();
    setStatus("Recommendations loaded successfully from the ML model.", "ok");
    return true;
  } catch (err) {
    console.warn("API fetch failed", err);
    setStatus(
      "Could not reach the recommendation API. Run the backend (e.g. run.bat) and open this app from the same server.",
      "warn"
    );
    return false;
  }
}

function normalizeEducationLevel(level) {
  const v = String(level || "").trim().toLowerCase();
  if (!v || v === "any" || v === "all") return "any";
  if (["degree", "undergraduate", "bachelor", "bachelors", "ug"].includes(v)) return "ug";
  if (["masters", "master", "postgraduate", "pg"].includes(v)) return "pg";
  if (["diploma", "polytechnic"].includes(v)) return "diploma";
  if (["1-10th", "10th", "school", "secondary", "high school"].includes(v)) return "school";
  if (["pu", "puc", "pre-university", "pre university", "11th", "12th"].includes(v)) return "pu";
  return v;
}

function displayEducation(level) {
  const v = normalizeEducationLevel(level);
  if (v === "ug") return "UG";
  if (v === "pg") return "PG";
  if (v === "pu") return "PU";
  if (v === "school") return "1-10th";
  if (v === "diploma") return "Diploma";
  return "Any";
}

function renderRecommendations() {
  recommendationCards.innerHTML = "";

  if (!state.recommendations.length) {
    if (emptyState) emptyState.style.display = "flex";
    recommendationCount.textContent = "0 matches found";
    return;
  }

  if (emptyState) emptyState.style.display = "none";
  recommendationCount.textContent = `${state.recommendations.length} matches found`;

  state.recommendations.forEach((s) => {
    recommendationCards.appendChild(makeCard(s, "save"));
  });
}

function renderRegistered() {
  registeredCards.innerHTML = "";

  if (!state.registered.length) {
    if (emptyRegistered) emptyRegistered.style.display = "flex";
    registeredCount.textContent = "0 saved";
    return;
  }

  if (emptyRegistered) emptyRegistered.style.display = "none";
  registeredCount.textContent = `${state.registered.length} saved`;

  state.registered.forEach((s) => {
    const card = makeCard(s, "unsave");
    const registerBtn = card.querySelector(".register-btn");
    registerBtn.textContent = "Unsave";
    registerBtn.classList.add("registered", "unsave");
    registeredCards.appendChild(card);
  });
}

function makeCard(scholarship, actionMode = "save") {
  const node = cardTemplate.content.cloneNode(true);

  node.querySelector(".title").textContent = scholarship.scholarship_name;

  const scoreChip = node.querySelector(".score-chip");
  const displayScore = Math.round(Number(scholarship.score) || 0);
  scoreChip.textContent = scholarship.eligible
    ? `Match ${displayScore}`
    : `Match ${displayScore} (near)`;

  if (scholarship.score >= 80) {
    scoreChip.style.background = "linear-gradient(135deg, #FF8A5B, #FF6B35)";
    scoreChip.style.color = "white";
  } else if (scholarship.score >= 60) {
    scoreChip.style.background = "linear-gradient(135deg, #00B4A6, #008B7F)";
    scoreChip.style.color = "white";
  } else {
    scoreChip.style.background = "rgba(255, 138, 91, 0.2)";
    scoreChip.style.color = "#FF6B35";
  }

  // Add Applicability Percentage (based on match score)
  const applicablePercentage = Math.min(Math.round(displayScore), 100);
  const applicableEl = node.querySelector(".applicable-percentage");
  applicableEl.textContent = `${applicablePercentage}%`;
  
  // Set color based on applicability
  if (applicablePercentage >= 80) {
    applicableEl.style.color = "#FF6B35";
    applicableEl.style.fontWeight = "700";
  } else if (applicablePercentage >= 60) {
    applicableEl.style.color = "#00B4A6";
    applicableEl.style.fontWeight = "700";
  } else {
    applicableEl.style.color = "#FF8A5B";
    applicableEl.style.fontWeight = "600";
  }
  
  const successProbabilityEl = node.querySelector(".success-probability-value");
  successProbabilityEl.textContent = `${Math.round(Number(scholarship.success_probability) || 0)}%`;
  successProbabilityEl.style.color = scholarship.success_probability >= 75 ? "#00B4A6" : scholarship.success_probability >= 40 ? "#FF8A5B" : "#666";
  successProbabilityEl.style.fontWeight = "700";

  const chanceLevelEl = node.querySelector(".chance-level-value");
  chanceLevelEl.textContent = scholarship.chance_level || "Unknown";
  chanceLevelEl.style.fontWeight = "700";
  chanceLevelEl.style.color = scholarship.chance_level === "High Chance" ? "#00B4A6" : scholarship.chance_level === "Medium Chance" ? "#FF8A5B" : "#666";

  // Backend metrics returned by the recommendation API
  const accuracyEl = node.querySelector(".accuracy-value");
  const apiAccuracy = state.apiMetrics?.accuracy_percent;
  accuracyEl.textContent = apiAccuracy == null ? "N/A" : `${Number(apiAccuracy).toFixed(2)}%`;
  accuracyEl.style.color = "#00B4A6";
  accuracyEl.style.fontWeight = "700";

  const responseTimeEl = node.querySelector(".response-time-value");
  const responseTime = state.apiMetrics?.last_response_time_ms;
  responseTimeEl.textContent = responseTime == null ? "N/A" : `${Number(responseTime).toFixed(2)} ms`;
  responseTimeEl.style.color = "#666";
  responseTimeEl.style.fontWeight = "600";
  
  const errorRateEl = node.querySelector(".error-rate-value");
  const errorRate = state.apiMetrics?.error_rate_percent;
  errorRateEl.textContent = errorRate == null ? "N/A" : `${Number(errorRate).toFixed(2)}%`;
  errorRateEl.style.color = "#666";
  errorRateEl.style.fontWeight = "600";

  const stateLabel = scholarship.state && scholarship.state !== "any" ? scholarship.state : "All states";
  node.querySelector(".meta").textContent = `${displayEducation(scholarship.education_level)} • ${scholarship.gender || "any"} • ${stateLabel}`;
  node.querySelector(".amount").textContent = scholarship.scholarship_amount
    ? `₹${formatNumber(scholarship.scholarship_amount)}`
    : "Amount not specified";

  const link = node.querySelector(".apply-link");
  const safeLink =
    scholarship.link ||
    `https://scholarships.gov.in/?search=${encodeURIComponent(scholarship.scholarship_name || "")}`;
  link.href = safeLink;
  link.addEventListener("click", (ev) => {
    ev.preventDefault();
    window.open(safeLink, "_blank");
  });

  const btn = node.querySelector(".register-btn");
  if (actionMode === "unsave") {
    btn.textContent = "Unsave";
    btn.addEventListener("click", () => {
      state.registered = state.registered.filter(
        (x) => x.scholarship_name !== scholarship.scholarship_name
      );
      saveRegistered(state.registered);
      renderRegistered();
      renderRecommendations();
    });
  } else {
    btn.addEventListener("click", () => {
      const exists = state.registered.find((x) => x.scholarship_name === scholarship.scholarship_name);
      if (!exists) {
        state.registered.push({ ...scholarship });
        saveRegistered(state.registered);
        renderRegistered();
        renderRecommendations();
      }

      btn.textContent = "✓ Saved";
      btn.disabled = true;
      btn.classList.add("registered");
    });
  }

  return node;
}

function renderTicker() {
  const items = state.tickerData.length
    ? state.tickerData
        .map((item) => {
          const name = escapeHtml(item.name || "");
          const extra =
            item.score != null && item.score !== ""
              ? ` <span class="ticker-meta">· score ${Math.round(Number(item.score))}</span>`
              : "";
          return `<div class="ticker-item">${name}${extra}</div>`;
        })
        .join("")
    : `<div class="ticker-item">Start the backend and refresh — scholarship names load from your dataset.</div>`;

  liveTicker.innerHTML = `<div class="ticker-track">${items}</div>`;

  const track = document.querySelector(".ticker-track");
  if (track) track.scrollTop = 0;
}

let _tickerInterval = null;

function startTickerAutoScroll() {
  stopTickerAutoScroll();
  const track = document.querySelector(".ticker-track");
  if (!track) return;

  _tickerInterval = setInterval(() => {
    if (!track) return;
    if (track.scrollTop + track.clientHeight >= track.scrollHeight - 1) {
      track.scrollTop = 0;
    } else {
      track.scrollTop += 1;
    }
  }, 50);

  track.addEventListener("mouseenter", stopTickerAutoScroll);
  track.addEventListener("mouseleave", startTickerAutoScroll);
}

function stopTickerAutoScroll() {
  if (_tickerInterval) {
    clearInterval(_tickerInterval);
    _tickerInterval = null;
  }
}

function formatNumber(n) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);
}

function loadRegistered() {
  try {
    return JSON.parse(localStorage.getItem(REGISTERED_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveRegistered(data) {
  localStorage.setItem(REGISTERED_KEY, JSON.stringify(data));
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setStatus(message, type = "info") {
  if (!statusBox) return;
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}
