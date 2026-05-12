const REGISTERED_KEY = "scholarmatch_registered";

const state = {
  recommendations: [],
  registered: loadRegistered(),
  tickerData: []
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
  setStatus("Enter your profile and submit — rankings come from the API / ML model.", "info");

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

    state.recommendations = data.results
      .map((r) => ({
        scholarship_name: r.name,
        score: r.score,
        eligible: Boolean(r.eligible),
        link: r.link,
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
    setStatus("Recommendations loaded from your trained model.", "ok");
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
    recommendationCards.appendChild(makeCard(s, true));
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
    const card = makeCard(s, false);
    const registerBtn = card.querySelector(".register-btn");
    registerBtn.textContent = "✓ Saved";
    registerBtn.disabled = true;
    registerBtn.classList.add("registered");
    registeredCards.appendChild(card);
  });
}

function makeCard(scholarship, allowRegister) {
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
  btn.addEventListener("click", () => {
    if (!allowRegister) return;

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

  if (!allowRegister) {
    btn.disabled = true;
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
