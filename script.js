const DATA_FILE = "./structured_real_scholarships.csv";
const REGISTERED_KEY = "scholarmatch_registered";

const state = {
  scholarships: [],
  recommendations: [],
  registered: loadRegistered(),
  tickerData: []
};

const profileForm = document.getElementById("profileForm");
const recommendationCards = document.getElementById("recommendationCards");
const registeredCards = document.getElementById("registeredCards");
const recommendationCount = document.getElementById("recommendationCount");
const liveTicker = document.getElementById("liveTicker");
const cardTemplate = document.getElementById("scholarshipCardTemplate");
const runMatchButton = profileForm?.querySelector("button[type='submit']");
const statusBox = document.getElementById("statusBox");
const matchList = document.getElementById("matchList");

init();

async function init() {
  // Always keep an in-memory dataset so the button gives output immediately.
  state.scholarships = getFallbackScholarships();
  setStatus("Using built-in dataset. Trying to load CSV...", "info");

  runSmartMatch();
  renderRegistered();

  const loaded = await loadScholarships();
  if (loaded.length) {
    state.scholarships = loaded;
    setStatus(`CSV loaded successfully (${loaded.length} scholarships).`, "ok");
  } else {
    setStatus("CSV not loaded. Using built-in dataset only.", "warn");
  }

  state.tickerData = state.scholarships.slice(0, 12).map((s, i) => ({
    name: s.scholarship_name,
    date: futureDate(5 + i * 2),
    viewers: 35 + (i * 11)
  }));

  renderTicker();
  setInterval(updateTickerLive, 4500);

  // start auto-scroll for the ticker
  startTickerAutoScroll();

  runSmartMatch();

  profileForm.addEventListener("submit", (e) => {
    e.preventDefault();
    (async () => {
      setStatus('Querying backend API...', 'info');
      const user = {
        marks: Number(document.getElementById("marks").value || 0),
        income: Number(document.getElementById("income").value || 0),
        category: (document.getElementById("category").value || "").toLowerCase(),
        gender: (document.getElementById("gender").value || "").toLowerCase(),
        education_level: (document.getElementById("education_level").value || "Any").toLowerCase(),
        disability: (document.getElementById("disability").value || "").toLowerCase()
      };

      const ok = await fetchFromApi(user);
      if (!ok) {
        setStatus('API not available; using local scoring.', 'warn');
        runSmartMatch();
      }
    })();
  });

  runMatchButton?.addEventListener("click", () => {
    // extra safety: if browser blocks form submit for any reason,
    // this still triggers a fresh calculation.
    setTimeout(runSmartMatch, 0);
  });
}

async function loadScholarships() {
  try {
    const res = await fetch(DATA_FILE);
    if (!res.ok) throw new Error("Unable to read CSV");

    const csv = await res.text();
    const rows = parseCsv(csv);

    return rows.map((r) => {
      const name = r.scholarship_name || "Scholarship";
      const maxIncome = Number(r.max_income || 0);
      const amount = Number(r.scholarship_amount || 0);
      const gender = (r.gender || "Any").trim();
      const level = (r.education_level || "Any").trim();

      return {
        scholarship_name: name,
        max_income: Number.isNaN(maxIncome) ? 0 : maxIncome,
        scholarship_amount: Number.isNaN(amount) ? 0 : amount,
        gender,
        education_level: level,
        category: "any",
        min_marks: inferMinMarks(level),
        disability: "no",
        link: `https://scholarships.gov.in/` +
          `?search=${encodeURIComponent(name)}`
      };
    });
  } catch (err) {
    console.warn("CSV load failed", err);
    return [];
  }
}

function getFallbackScholarships() {
  return [
    {
      scholarship_name: "National Merit Grant",
      max_income: 800000,
      scholarship_amount: 50000,
      gender: "Any",
      education_level: "UG",
      category: "any",
      min_marks: 70,
      disability: "no",
      link: "https://scholarships.gov.in/"
    },
    {
      scholarship_name: "STEM Future Fellowship",
      max_income: 600000,
      scholarship_amount: 75000,
      gender: "Any",
      education_level: "PG",
      category: "any",
      min_marks: 80,
      disability: "no",
      link: "https://scholarships.gov.in/"
    },
    {
      scholarship_name: "Ambedkar Support Scholarship",
      max_income: 400000,
      scholarship_amount: 30000,
      gender: "Any",
      education_level: "Diploma",
      category: "any",
      min_marks: 60,
      disability: "no",
      link: "https://scholarships.gov.in/"
    }
  ];
}

function parseCsv(csvText) {
  const lines = csvText.split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];

  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = splitCsvLine(line);
    return headers.reduce((acc, header, i) => {
      acc[header.trim()] = (values[i] || "").trim();
      return acc;
    }, {});
  });
}

function splitCsvLine(line) {
  const out = [];
  let cur = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];

    if (ch === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (ch === "," && !inQuotes) {
      out.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

function inferMinMarks(level) {
  const lv = (level || "").toLowerCase();
  // Map common labels to sensible minimum marks
  if (lv.includes("master") || lv.includes("pg")) return 75;
  if (lv.includes("degree") || lv === 'ug' || lv === 'degree') return 70;
  if (lv === 'pu' || lv.includes('pu')) return 60;
  if (lv.includes('1') || lv.includes('10') || lv.includes('class')) return 50;
  if (lv.includes("diploma")) return 60;
  return 65;
}

function runSmartMatch() {
  const user = {
    marks: Number(document.getElementById("marks").value || 0),
    income: Number(document.getElementById("income").value || 0),
    category: (document.getElementById("category").value || "").toLowerCase(),
    gender: (document.getElementById("gender").value || "").toLowerCase(),
    education_level: (document.getElementById("education_level").value || "Any").toLowerCase(),
    disability: (document.getElementById("disability").value || "").toLowerCase()
  };

  if (Number.isNaN(user.marks) || Number.isNaN(user.income)) {
    setStatus("Please enter valid marks and income values.", "warn");
    return;
  }

  if (!state.scholarships.length) {
    setStatus("No scholarships available yet. Please reload once.", "warn");
    renderRecommendations();
    return;
  }

  const rankedAll = state.scholarships
    .map((row) => scoreScholarship(user, row))
    .sort((a, b) => b.score - a.score);
  const eligibleOnly = rankedAll.filter((item) => item.eligible);

  // If no fully eligible scholarship exists, show top close matches instead.
  let candidates = eligibleOnly.length ? eligibleOnly : rankedAll;

  // Remove duplicates (keep first occurrence) and limit to top 10
  const seen = new Set();
  const unique = [];
  for (const c of candidates) {
    const key = (c.scholarship_name || c.name || '').trim();
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(c);
    }
    if (unique.length >= 10) break;
  }

  const ranked = unique;

  state.recommendations = ranked;
  setStatus("Smart match completed.", "ok");
  renderRecommendations();
}

// Try backend API first; fall back to local scoring if unavailable
async function fetchFromApi(user) {
  try {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });

    if (!res.ok) throw new Error('API error');
    const data = await res.json();
    if (!data || !Array.isArray(data.results)) throw new Error('Bad API response');

    // map API shape to internal shape
    state.recommendations = data.results.map((r) => ({
      scholarship_name: r.name,
      score: r.score,
      eligible: r.eligible,
      link: r.link,
      max_income: r.max_income,
      scholarship_amount: r.scholarship_amount,
      education_level: r.education_level
    })).slice(0, 12);

    renderRecommendations();
    setStatus('Loaded recommendations from API.', 'ok');
    return true;
  } catch (err) {
    console.warn('API fetch failed, falling back to local scoring', err);
    return false;
  }
}

function scoreScholarship(user, row) {
  let score = 0;
  let eligible = true;
  const breakdown = [];

  // ML-style weighted scoring (mirrors your Python logic)
  if (user.marks >= row.min_marks) score += 30;
  if (user.marks >= row.min_marks) {
    breakdown.push(`Marks >= ${row.min_marks}: +30`);
  } else if (user.marks >= row.min_marks - 10) {
    score += 20;
    breakdown.push(`Marks within -10 of ${row.min_marks}: +20`);
  } else {
    eligible = false;
    breakdown.push(`Marks too low`);
  }

  if (!row.max_income || user.income <= row.max_income) {
    score += 30;
    breakdown.push(`Income ≤ ${row.max_income}: +30`);
  } else {
    score += (row.max_income / (user.income + 1)) * 30;
    eligible = false;
    breakdown.push(`Income > ${row.max_income}: partial`);
  }

  const schCat = String(row.category || "any").toLowerCase();
  if (schCat === "any" || schCat.includes(user.category)) {
    score += 15;
    breakdown.push(`Category match: +15`);
  } else {
    eligible = false;
    breakdown.push(`Category mismatch`);
  }

  // Education / Course match
  const rowLevel = String(row.education_level || "any").toLowerCase();
  if (rowLevel === "any" || rowLevel === user.education_level || user.education_level === "any") {
    score += 10;
    breakdown.push(`Course match: +10`);
  } else {
    // allow partial credit when nearby (diploma <-> ug)
    if ((rowLevel === 'ug' && user.education_level === 'diploma') || (rowLevel === 'diploma' && user.education_level === 'ug')) {
      score += 5;
      breakdown.push(`Course near-match: +5`);
    } else {
      breakdown.push(`Course mismatch`);
    }
  }

  const schGender = String(row.gender || "any").toLowerCase();
  if (schGender === "any" || schGender === user.gender) {
    score += 10;
    breakdown.push(`Gender match: +10`);
  }

  const schDis = String(row.disability || "no").toLowerCase();
  if (schDis === "no" || schDis === user.disability) {
    score += 5;
    breakdown.push(`Disability match/open: +5`);
  } else {
    eligible = false;
    breakdown.push(`Disability restriction`);
  }

  return {
    ...row,
    score: Math.round(score * 100) / 100,
    eligible,
    breakdown
  };
}

function renderMatchList() {
  if (!matchList) return;
  matchList.innerHTML = "";
  if (!state.recommendations.length) {
    matchList.innerHTML = `<p class="muted">No matches to display.</p>`;
    return;
  }

  const ol = document.createElement('ol');
  ol.style.margin = '0';
  ol.style.padding = '0 0 0 1.1rem';

  state.recommendations.forEach((s, idx) => {
    const li = document.createElement('li');
    li.className = 'match-item';

    const rank = document.createElement('div');
    rank.className = 'match-rank';
    rank.textContent = idx + 1;

    const left = document.createElement('div');
    left.style.display = 'flex';
    left.style.flexDirection = 'column';
    left.style.gap = '3px';

    const title = document.createElement('div');
    title.className = 'match-title';
    const a = document.createElement('a');
    const href = s.link || `https://scholarships.gov.in/?search=${encodeURIComponent(s.scholarship_name || s.name || '')}`;
    a.href = href;
    a.target = '_blank';
    a.rel = 'noopener';
    a.className = 'match-title-link';
    a.textContent = s.scholarship_name;
    a.addEventListener('click', (ev) => {
      ev.preventDefault();
      window.open(href, '_blank');
    });
    title.appendChild(a);

    const sub = document.createElement('div');
    sub.className = 'match-sub';
    const edu = s.education_level || 'Any';
    const gender = s.gender || 'Any';
    const incomeText = `Income ≤ ₹${formatNumber(s.max_income || 0)}`;
    sub.textContent = `${capitalize(edu)} • ${capitalize(gender)} • ${incomeText}`;

    left.appendChild(title);
    left.appendChild(sub);

    const badges = document.createElement('div');
    badges.className = 'match-badges';

    const scoreBadge = document.createElement('span');
    scoreBadge.className = 'badge-small';
    scoreBadge.textContent = `Score ${Math.round(s.score)}`;
    badges.appendChild(scoreBadge);

    if (s.eligible) {
      const e = document.createElement('span');
      e.className = 'badge-eligible';
      e.textContent = 'Eligible';
      badges.appendChild(e);
    }

    li.appendChild(rank);
    li.appendChild(left);
    li.appendChild(badges);

    if (s.breakdown && s.breakdown.length) {
      const br = document.createElement('div');
      br.className = 'breakdown';
      br.textContent = s.breakdown.join(' • ');
      li.appendChild(br);
    }

    ol.appendChild(li);
  });

  matchList.appendChild(ol);
}

function capitalize(s) {
  if (!s) return '';
  return String(s).charAt(0).toUpperCase() + String(s).slice(1);
}

function renderRecommendations() {
  recommendationCards.innerHTML = "";
  const eligibleCount = state.recommendations.filter((x) => x.eligible).length;
  recommendationCount.textContent = `${state.recommendations.length} found`;

  if (!state.recommendations.length) {
    recommendationCards.innerHTML = `<p class="muted">No scholarships matched this profile.</p>`;
    return;
  }

  if (!eligibleCount) {
    recommendationCards.insertAdjacentHTML(
      "beforeend",
      `<p class="muted">No fully eligible scholarships found. Showing best near matches.</p>`
    );
  }

  state.recommendations.forEach((s) => {
    const card = makeCard(s, true);
    recommendationCards.appendChild(card);
  });
  // also render compact ordered match summary
  renderMatchList();
}

function renderRegistered() {
  registeredCards.innerHTML = "";

  if (!state.registered.length) {
    registeredCards.innerHTML = `<p class="muted">No registered scholarships yet.</p>`;
    return;
  }

  state.registered.forEach((s) => {
    const card = makeCard(s, false);
    const registerBtn = card.querySelector(".register-btn");
    registerBtn.textContent = "Registered";
    registerBtn.disabled = true;
    registerBtn.classList.add("disabled");
    registeredCards.appendChild(card);
  });
}

function makeCard(scholarship, allowRegister) {
  const node = cardTemplate.content.cloneNode(true);

  node.querySelector(".title").textContent = scholarship.scholarship_name;
  node.querySelector(".score-chip").textContent = scholarship.eligible
    ? `Score ${scholarship.score ?? "-"} • Eligible`
    : `Score ${scholarship.score ?? "-"} • Near match`;
  node.querySelector(".meta").textContent = `Income ≤ ₹${formatNumber(scholarship.max_income || 0)} | ${scholarship.gender} | ${scholarship.education_level}`;
  node.querySelector(".amount").textContent = scholarship.scholarship_amount
    ? `Amount: ₹${formatNumber(scholarship.scholarship_amount)}`
    : "Amount: Not specified";

  const link = node.querySelector(".apply-link");
  // build a safe unique link and open via window.open to avoid reuse issues
  const safeLink = scholarship.link || `https://scholarships.gov.in/?search=${encodeURIComponent(scholarship.scholarship_name || scholarship.name || '')}`;
  link.href = safeLink;
  link.addEventListener('click', (ev) => {
    ev.preventDefault();
    window.open(safeLink, '_blank');
  });

  const btn = node.querySelector(".register-btn");
  btn.addEventListener("click", () => {
    if (!allowRegister) return;

    const exists = state.registered.find((x) => x.scholarship_name === scholarship.scholarship_name);
    if (!exists) {
      state.registered.push({ ...scholarship });
      saveRegistered(state.registered);
      renderRegistered();
    }

    btn.textContent = "Registered";
    btn.disabled = true;
  });

  if (!allowRegister) {
    btn.disabled = true;
  }

  return node;
}

function renderTicker() {
  const items = state.tickerData
    .map((item) => `<div class="ticker-item">🔵 ${escapeHtml(item.name)} | Deadline: ${item.date} | ${item.viewers} students tracking</div>`)
    .join("");

  // single-column vertical track (no horizontal duplication)
  liveTicker.innerHTML = `<div class="ticker-track">${items}</div>`;

  // reset auto-scroll position when content updates
  const track = document.querySelector('.ticker-track');
  if (track) track.scrollTop = 0;
}

let _tickerInterval = null;
function startTickerAutoScroll() {
  stopTickerAutoScroll();
  const track = document.querySelector('.ticker-track');
  if (!track) return;

  // small incremental auto-scroll
  _tickerInterval = setInterval(() => {
    if (!track) return;
    // scroll by 1 pixel; if reached bottom, reset to top
    if (track.scrollTop + track.clientHeight >= track.scrollHeight) {
      track.scrollTop = 0;
    } else {
      track.scrollTop += 1;
    }
  }, 50);

  // pause on hover
  track.addEventListener('mouseenter', stopTickerAutoScroll);
  track.addEventListener('mouseleave', startTickerAutoScroll);
}

function stopTickerAutoScroll() {
  if (_tickerInterval) {
    clearInterval(_tickerInterval);
    _tickerInterval = null;
  }
}

function updateTickerLive() {
  state.tickerData = state.tickerData.map((item) => ({
    ...item,
    viewers: Math.max(10, item.viewers + randomInt(-4, 9))
  }));
  renderTicker();
}

function futureDate(daysAhead) {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
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
