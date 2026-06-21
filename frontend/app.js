// app.js — Career Copilot SPA

// ── State ──────────────────────────────────────────────────
const state = {
  file: null,
  jobDescription: "",
  loading: false,
  result: null,
};

// ── DOM refs ───────────────────────────────────────────────
const $ = id => document.getElementById(id);

const uploadZone   = $("upload-zone");
const fileInput    = $("resume-file");
const fileInfo     = $("file-info");
const fileName     = $("file-name");
const removeFile   = $("remove-file");
const jdTextarea   = $("job-description");
const jdCounter    = $("jd-counter");
const analyzeBtn   = $("analyze-btn");
const errorBox     = $("error-box");
const resultsPanel = $("results-panel");
const loadingState = $("loading-state");
const resultsContent = $("results-content");
const statusBadge  = $("status-badge");

// Pipeline step elements
const pipeSteps = {
  resume:   $("ps-resume"),
  job:      $("ps-job"),
  gap:      $("ps-gap"),
  strategy: $("ps-strategy"),
  interview:$("ps-interview"),
};

// ── File Upload ─────────────────────────────────────────────
fileInput.addEventListener("change", () => {
  if (fileInput.files && fileInput.files[0]) handleFile(fileInput.files[0]);
});

uploadZone.addEventListener("dragover", e => { e.preventDefault(); uploadZone.style.borderColor = "var(--primary)"; });
uploadZone.addEventListener("dragleave", () => { uploadZone.style.borderColor = ""; });
uploadZone.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.style.borderColor = "";
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  const allowed = [".pdf", ".docx", ".doc"];
  const ext = "." + file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) { showError("Only PDF and DOCX files are supported."); return; }
  if (file.size > 10 * 1024 * 1024) { showError("File is too large. Max 10 MB."); return; }
  state.file = file;
  fileName.textContent = file.name;
  fileInfo.classList.remove("hidden");
  uploadZone.classList.add("hidden");
  hideError();
  checkReady();
}

removeFile.addEventListener("click", () => {
  state.file = null;
  fileInput.value = "";
  fileInfo.classList.add("hidden");
  uploadZone.classList.remove("hidden");
  checkReady();
});

// ── Job Description ─────────────────────────────────────────
jdTextarea.addEventListener("input", () => {
  state.jobDescription = jdTextarea.value;
  jdCounter.textContent = state.jobDescription.length + " characters";
  checkReady();
});

// ── Enable/disable Analyze button ──────────────────────────
function checkReady() {
  analyzeBtn.disabled = !(state.file && state.jobDescription.trim().length > 30);
}

// ── Error helpers ───────────────────────────────────────────
function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove("hidden");
}
function hideError() {
  errorBox.classList.add("hidden");
}

// ── Pipeline step animation ─────────────────────────────────
let stepIndex = 0;
let stepTimer = null;
const stepKeys = ["resume", "job", "gap", "strategy", "interview"];

function startStepAnimation() {
  stepIndex = 0;
  stepKeys.forEach(k => { pipeSteps[k].classList.remove("active", "done"); });
  pipeSteps[stepKeys[0]].classList.add("active");
  // Advance every ~10s (rough timing for demo)
  stepTimer = setInterval(() => {
    pipeSteps[stepKeys[stepIndex]].classList.remove("active");
    pipeSteps[stepKeys[stepIndex]].classList.add("done");
    stepIndex++;
    if (stepIndex < stepKeys.length) {
      pipeSteps[stepKeys[stepIndex]].classList.add("active");
    } else {
      clearInterval(stepTimer);
    }
  }, 9000);
}

function stopStepAnimation() {
  clearInterval(stepTimer);
  stepKeys.forEach(k => { pipeSteps[k].classList.remove("active"); pipeSteps[k].classList.add("done"); });
}

// ── Analyze ─────────────────────────────────────────────────
analyzeBtn.addEventListener("click", runAnalysis);

async function runAnalysis() {
  hideError();
  state.loading = true;
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing...";

  // Show loading
  resultsPanel.classList.remove("hidden");
  loadingState.classList.remove("hidden");
  resultsContent.classList.add("hidden");
  resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });

  startStepAnimation();

  const form = new FormData();
  form.append("resume_file", state.file);
  form.append("job_description", state.jobDescription);

  try {
    const res = await fetch("/api/analyze", { method: "POST", body: form });
    const json = await res.json();

    stopStepAnimation();

    if (!res.ok) {
      const msg = json.detail || "Analysis failed. Please try again.";
      showError(msg);
      if (res.status === 429) showError("API quota exhausted. Please wait and retry, or enable billing.");
      loadingState.classList.add("hidden");
      return;
    }

    state.result = json.data;
    renderResults(json.data);

  } catch (err) {
    stopStepAnimation();
    showError("Network error: " + err.message);
    loadingState.classList.add("hidden");
  } finally {
    state.loading = false;
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze";
  }
}

// ── Render helpers ──────────────────────────────────────────
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function listItems(ulId, items, emptyMsg) {
  const ul = $(ulId);
  ul.innerHTML = "";
  if (!items || !items.length) {
    ul.innerHTML = "<li>" + (emptyMsg || "None identified.") + "</li>";
    return;
  }
  items.forEach(item => {
    const li = el("li", null, item);
    ul.appendChild(li);
  });
}

// ── Main render ─────────────────────────────────────────────
function renderResults(data) {
  loadingState.classList.add("hidden");
  resultsContent.classList.remove("hidden");

  renderBanner(data);
  renderScore(data.match_score);
  renderResume(data.resume_review);
  renderGaps(data.skill_gaps);
  renderRoadmap(data.career_roadmap);
  renderInterview(data.interview_prep);

  resultsContent.scrollIntoView({ behavior: "smooth", block: "start" });
}

// 0. Banner
function renderBanner(data) {
  $("candidate-name").textContent  = data.candidate_name  || "Candidate";
  $("candidate-title").textContent = data.current_title   || "";
  const score = data.match_score.score;
  const color = data.match_score.color;
  const pill  = $("banner-score");
  pill.textContent  = score + "/100";
  pill.className    = "banner-score-pill pill-" + color;
}

// 1. Match Score
function renderScore(ms) {
  const score = ms.score || 0;
  const color = ms.color || "warning";
  $("score-number").textContent = score;
  $("score-number").className   = "score-big " + color;
  $("score-label").textContent  = ms.label || "";
  const fill = $("score-fill");
  fill.style.width  = score + "%";
  fill.className    = "score-fill fill-" + color;
  const track = $("score-track");
  track.setAttribute("aria-valuenow", score);
  track.setAttribute("aria-label", "Match score: " + score + " out of 100");
}

// 2. Resume Review
function renderResume(rr) {
  listItems("strengths-list",   rr.strengths,   "No strengths identified.");
  listItems("weaknesses-list",  rr.weaknesses,  "No significant weaknesses.");
  listItems("suggestions-list", rr.suggestions, "No suggestions at this time.");
}

// 3. Skill Gaps
function renderGaps(sg) {
  // Priority gaps
  const container = $("priority-gaps-list");
  container.innerHTML = "";
  const gaps = sg.priority_gaps || [];
  gaps.forEach(g => {
    const item = el("div", "gap-item");
    const header = el("div", "gap-header");
    const priority = (g.priority || "MEDIUM").toLowerCase();
    const badge = el("span", "badge badge-" + priority, g.priority || "");
    const name  = el("span", "gap-name", g.skill || "");
    header.appendChild(badge);
    header.appendChild(name);
    const reason = el("p", "gap-reason", g.reason || "");
    item.appendChild(header);
    item.appendChild(reason);
    container.appendChild(item);
  });

  // Missing skills tags
  const skillsCloud = $("missing-skills-tags");
  skillsCloud.innerHTML = "";
  (sg.missing_skills || []).forEach(s => { skillsCloud.appendChild(el("span", "tag", s)); });

  // Missing keywords
  const kwCloud = $("missing-keywords-tags");
  kwCloud.innerHTML = "";
  (sg.missing_keywords || []).slice(0, 16).forEach(k => { kwCloud.appendChild(el("span", "tag", k)); });
}

// 4. Career Roadmap
function renderRoadmap(cr) {
  const fillPhase = (listId, items) => {
    const ol = $(listId);
    ol.innerHTML = "";
    (items || []).forEach(item => { ol.appendChild(el("li", null, item)); });
  };
  fillPhase("road-immediate", cr.immediate);
  fillPhase("road-midterm",   cr.mid_term);
  fillPhase("road-longterm",  cr.long_term);

  // Projects
  const grid = $("projects-grid");
  grid.innerHTML = "";
  (cr.projects || []).forEach(p => {
    const card = el("div", "project-card");
    const header = el("div", "project-header");
    header.appendChild(el("span", "project-title", p.title || ""));
    header.appendChild(el("span", "project-dur", p.duration ? "~" + p.duration : ""));
    const desc = el("p", "project-desc", p.desc || "");
    const skills = el("div", "project-skills");
    (p.skills || []).forEach(s => { skills.appendChild(el("span", "skill-tag", s)); });
    card.appendChild(header);
    card.appendChild(desc);
    card.appendChild(skills);
    grid.appendChild(card);
  });
}

// 5. Interview Prep
function renderInterview(ip) {
  // Technical questions
  const techOl = $("tech-questions");
  techOl.innerHTML = "";
  (ip.technical_questions || []).forEach(q => { techOl.appendChild(el("li", null, q)); });

  // Behavioral questions
  const behavOl = $("behavioral-questions");
  behavOl.innerHTML = "";
  (ip.behavioral_questions || []).forEach(q => { behavOl.appendChild(el("li", null, q)); });

  // System design (show if present)
  const sdSection = $("sysdesign-section");
  const sdOl = $("sysdesign-questions");
  sdOl.innerHTML = "";
  if (ip.system_design_questions && ip.system_design_questions.length) {
    sdSection.classList.remove("hidden");
    ip.system_design_questions.forEach(q => { sdOl.appendChild(el("li", null, q)); });
  }

  // Prep areas
  const prepContainer = $("prep-areas");
  prepContainer.innerHTML = "";
  (ip.preparation_areas || []).forEach(area => {
    const div = el("div", "prep-area");
    div.appendChild(el("div", "prep-area-name", area.area || ""));
    div.appendChild(el("div", "prep-area-why", area.why || ""));
    const ul = el("ul", "prep-actions");
    (area.actions || []).forEach(a => { ul.appendChild(el("li", null, a)); });
    div.appendChild(ul);
    prepContainer.appendChild(div);
  });

  // Answer frameworks
  const answerContainer = $("answer-cards");
  answerContainer.innerHTML = "";
  (ip.suggested_answers || []).forEach(sa => {
    const card = el("div", "answer-card");
    card.appendChild(el("div", "answer-question", "Q: " + (sa.question || "")));
    card.appendChild(el("div", "answer-framework", sa.framework || ""));
    const ul = el("ul", "answer-points");
    (sa.key_points || []).forEach(kp => { ul.appendChild(el("li", null, kp)); });
    card.appendChild(ul);
    answerContainer.appendChild(card);
  });
}

// ── Health check on load ────────────────────────────────────
(async () => {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      statusBadge.textContent = data.api_key_configured ? "API Connected" : "No API Key";
      statusBadge.className   = "status-badge " + (data.api_key_configured ? "ok" : "error");
    }
  } catch {
    statusBadge.textContent = "Server Offline";
    statusBadge.className   = "status-badge error";
  }
})();
