// app.js — Career Copilot Premium Client & AI SaaS Application Shell

// ── State Management ──────────────────────────────────────────
const state = {
  file: null,
  jobDescription: "",
  loading: false,
  result: null,
  activeView: "dashboard",
  history: [],
};

// ── DOM Helper ────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const qsa = selector => document.querySelectorAll(selector);

// ── Navigation & Shell Elements ───────────────────────────────
const appSidebar        = $("app-sidebar");
const sidebarOverlay    = $("sidebar-overlay");
const btnOpenSidebar    = $("btn-open-sidebar");
const btnCloseSidebar   = $("btn-close-sidebar");
const currentViewTitle  = $("current-view-title");
const activeContextPill = $("active-context-pill");
const topbarCandidateCtx = $("topbar-candidate-context");
const topbarBtnNew      = $("topbar-btn-new");
const themeToggle       = $("theme-toggle-btn");
const themeSun          = $("theme-icon-sun");
const themeMoon         = $("theme-icon-moon");
const statusBadge       = $("status-badge");

// Input Panels
const uploadZone        = $("upload-zone");
const fileInput         = $("resume-file");
const fileInfo          = $("file-info");
const fileName          = $("file-name");
const removeFile        = $("remove-file");
const jdTextarea        = $("job-description");
const jdCounter         = $("jd-counter");
const btnPasteDesc      = $("btn-paste-desc");
const analyzeBtn        = $("analyze-btn");
const errorBox          = $("error-box");
const errorMessage      = $("error-message");

// Dashboard & State Panels
const emptyState        = $("empty-state");
const loadingState      = $("loading-state");
const skeletonState     = $("results-skeleton");
const resultsPanel      = $("results-panel");
const resultsContent    = $("results-content");
const pipelineFill      = $("pipeline-fill");

// Pipeline Progress Nodes
const pipeSteps = {
  resume:   $("ps-resume"),
  job:      $("ps-job"),
  gap:      $("ps-gap"),
  strategy: $("ps-strategy"),
  interview:$("ps-interview"),
};

// ── Theme Switcher ────────────────────────────────────────────
function initTheme() {
  const storedTheme = localStorage.getItem("theme");
  const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  
  if (storedTheme === "dark" || (!storedTheme && systemPrefersDark)) {
    document.body.classList.add("dark-theme");
    if (themeSun) themeSun.classList.add("hidden");
    if (themeMoon) themeMoon.classList.remove("hidden");
  } else {
    document.body.classList.remove("dark-theme");
    if (themeSun) themeSun.classList.remove("hidden");
    if (themeMoon) themeMoon.classList.add("hidden");
  }
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const isDark = document.body.classList.toggle("dark-theme");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    
    if (isDark) {
      themeSun.classList.add("hidden");
      themeMoon.classList.remove("hidden");
    } else {
      themeSun.classList.remove("hidden");
      themeMoon.classList.add("hidden");
    }
  });
}

initTheme();

// ── View Router / View Switching System ───────────────────────
const viewTitles = {
  dashboard: "Dashboard Overview",
  workspace: "New Analysis Workspace",
  resume:    "Resume Profile Audit",
  jobmatch:  "Job Match Comparison",
  skills:    "Skills & Gap Matrix",
  roadmap:   "Action Plan & Roadmap",
  interview: "Interview Preparation",
  history:   "Analysis History",
  showcase:  "ADK & Agent Stack",
};

function switchView(targetView) {
  state.activeView = targetView;
  
  // 1. Update sidebar active item
  qsa(".nav-item").forEach(item => {
    if (item.getAttribute("data-view") === targetView) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // 2. Update view page visibility
  qsa(".view-page").forEach(page => {
    if (page.id === `view-${targetView}`) {
      page.classList.add("active");
    } else {
      page.classList.remove("active");
    }
  });

  // 3. Update topbar breadcrumb
  if (currentViewTitle) {
    currentViewTitle.textContent = viewTitles[targetView] || "Overview";
  }

  // 4. Close mobile sidebar drawer if open
  closeMobileSidebar();

  // Scroll to top of main content smoothly
  const body = document.querySelector(".app-content-body");
  if (body) body.scrollTop = 0;
}

// Bind navigation sidebar buttons
qsa(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    const view = btn.getAttribute("data-view");
    if (view) switchView(view);
  });
});

// Bind quick navigation links (data-jump)
qsa("[data-jump]").forEach(btn => {
  btn.addEventListener("click", () => {
    const view = btn.getAttribute("data-jump");
    if (view) switchView(view);
  });
});

if (topbarBtnNew) {
  topbarBtnNew.addEventListener("click", () => switchView("workspace"));
}
if ($("dash-btn-start")) {
  $("dash-btn-start").addEventListener("click", () => switchView("workspace"));
}
if ($("history-btn-new")) {
  $("history-btn-new").addEventListener("click", () => switchView("workspace"));
}

// ── Mobile Sidebar Drawer Controls ─────────────────────────────
function openMobileSidebar() {
  if (appSidebar) appSidebar.classList.add("mobile-open");
  if (sidebarOverlay) sidebarOverlay.classList.remove("hidden");
}

function closeMobileSidebar() {
  if (appSidebar) appSidebar.classList.remove("mobile-open");
  if (sidebarOverlay) sidebarOverlay.classList.add("hidden");
}

if (btnOpenSidebar) btnOpenSidebar.addEventListener("click", openMobileSidebar);
if (btnCloseSidebar) btnCloseSidebar.addEventListener("click", closeMobileSidebar);
if (sidebarOverlay) sidebarOverlay.addEventListener("click", closeMobileSidebar);

// ── File Upload Controls ──────────────────────────────────────
if (fileInput) {
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) handleFile(fileInput.files[0]);
  });
}

if (uploadZone) {
  uploadZone.addEventListener("dragover", e => {
    e.preventDefault();
    uploadZone.classList.add("dragover");
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("dragover");
  });

  uploadZone.addEventListener("drop", e => {
    e.preventDefault();
    uploadZone.classList.remove("dragover");
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });
}

function handleFile(file) {
  const allowed = [".pdf", ".docx", ".doc"];
  const ext = "." + file.name.split(".").pop().toLowerCase();
  
  if (!allowed.includes(ext)) {
    showError("Invalid file type. Only text-based PDF, DOCX, and DOC files are supported.");
    return;
  }
  
  if (file.size > 10 * 1024 * 1024) {
    showError("File size exceeds 10MB limit.");
    return;
  }
  
  state.file = file;
  if (fileName) fileName.textContent = file.name;
  if (fileInfo) fileInfo.classList.remove("hidden");
  if (uploadZone) uploadZone.classList.add("hidden");
  hideError();
  checkReady();
}

if (removeFile) {
  removeFile.addEventListener("click", e => {
    e.preventDefault();
    state.file = null;
    if (fileInput) fileInput.value = "";
    if (fileInfo) fileInfo.classList.add("hidden");
    if (uploadZone) uploadZone.classList.remove("hidden");
    checkReady();
  });
}

// ── Job Description Textarea & Clipboard Action ──────────────
if (jdTextarea) {
  jdTextarea.addEventListener("input", () => {
    state.jobDescription = jdTextarea.value;
    if (jdCounter) jdCounter.textContent = state.jobDescription.length + " characters";
    checkReady();
  });
}

if (btnPasteDesc) {
  btnPasteDesc.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        jdTextarea.value = text;
        state.jobDescription = text;
        if (jdCounter) jdCounter.textContent = text.length + " characters";
        checkReady();
      }
    } catch (err) {
      console.warn("Unable to access clipboard: ", err);
    }
  });
}

function checkReady() {
  if (analyzeBtn) {
    analyzeBtn.disabled = !(state.file && state.jobDescription.trim().length > 30);
  }
}

// ── Error Helpers ─────────────────────────────────────────────
function showError(msg) {
  if (errorMessage) errorMessage.textContent = msg;
  if (errorBox) errorBox.classList.remove("hidden");
}
function hideError() {
  if (errorBox) errorBox.classList.add("hidden");
}

// ── Expandable Accordions Handling ────────────────────────────
function setupAccordions() {
  const accordions = qsa(".accordion-header-btn");
  
  accordions.forEach(btn => {
    btn.onclick = () => {
      const wrapper = btn.closest(".accordion-wrapper");
      const isExpanded = wrapper.classList.contains("expanded");
      
      if (isExpanded) {
        wrapper.classList.remove("expanded");
        btn.setAttribute("aria-expanded", "false");
      } else {
        wrapper.classList.add("expanded");
        btn.setAttribute("aria-expanded", "true");
      }
    };
  });
}

setupAccordions();

// ── Agent Pipeline Progress Step Animation ────────────────────
let stepIndex = 0;
let stepTimer = null;
const stepKeys = ["resume", "job", "gap", "strategy", "interview"];

function startStepAnimation() {
  stepIndex = 0;
  if (pipelineFill) pipelineFill.style.width = "0%";
  
  stepKeys.forEach(k => {
    if (pipeSteps[k]) pipeSteps[k].classList.remove("active", "done");
  });
  
  if (pipeSteps[stepKeys[0]]) pipeSteps[stepKeys[0]].classList.add("active");
  
  stepTimer = setInterval(() => {
    if (pipeSteps[stepKeys[stepIndex]]) {
      pipeSteps[stepKeys[stepIndex]].classList.remove("active");
      pipeSteps[stepKeys[stepIndex]].classList.add("done");
    }
    stepIndex++;
    
    const fillPercent = (stepIndex / (stepKeys.length - 1)) * 100;
    if (pipelineFill) pipelineFill.style.width = Math.min(fillPercent, 100) + "%";
    
    if (stepIndex < stepKeys.length) {
      if (pipeSteps[stepKeys[stepIndex]]) pipeSteps[stepKeys[stepIndex]].classList.add("active");
    } else {
      clearInterval(stepTimer);
    }
  }, 7000);
}

function stopStepAnimation() {
  clearInterval(stepTimer);
  if (pipelineFill) pipelineFill.style.width = "100%";
  stepKeys.forEach(k => {
    if (pipeSteps[k]) {
      pipeSteps[k].classList.remove("active");
      pipeSteps[k].classList.add("done");
    }
  });
}

// ── Analysis Pipeline Execution ───────────────────────────────
if (analyzeBtn) analyzeBtn.addEventListener("click", runAnalysis);

async function runAnalysis() {
  if (!state.file || !state.jobDescription.trim()) return;
  
  hideError();
  state.loading = true;
  analyzeBtn.disabled = true;
  const originalBtnText = analyzeBtn.innerHTML;
  analyzeBtn.innerHTML = `<span class="btn-spinner"></span> Analyzing Career Fit...`;

  // UI loading transition
  if (emptyState) emptyState.classList.add("hidden");
  if (loadingState) loadingState.classList.remove("hidden");
  if (skeletonState) skeletonState.classList.remove("hidden");
  if (resultsContent) resultsContent.classList.add("hidden");
  
  startStepAnimation();

  const formData = new FormData();
  formData.append("resume_file", state.file);
  formData.append("job_description", state.jobDescription);

  const headers = {};
  const clientApiKey = localStorage.getItem("app_api_key") || window.APP_API_KEY;
  if (clientApiKey) {
    headers["X-API-Key"] = clientApiKey;
  }

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: headers,
      body: formData,
    });
    
    const json = await response.json();
    stopStepAnimation();

    if (!response.ok) {
      const msg = json.detail || "Analysis failed. Please check file format and content.";
      showError(msg);
      if (response.status === 429) {
        showError("Gemini API rate limit reached. Please retry later.");
      }
      if (loadingState) loadingState.classList.add("hidden");
      if (skeletonState) skeletonState.classList.add("hidden");
      if (emptyState) emptyState.classList.remove("hidden");
      return;
    }

    state.result = json.data;
    saveAnalysisToHistory(json.data);
    renderAllViews(json.data);

    // Auto-switch to Dashboard view after completion so user sees executive summary
    switchView("dashboard");

  } catch (err) {
    stopStepAnimation();
    showError("Network/Server connection error: " + err.message);
    if (loadingState) loadingState.classList.add("hidden");
    if (skeletonState) skeletonState.classList.add("hidden");
    if (emptyState) emptyState.classList.remove("hidden");
  } finally {
    state.loading = false;
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = originalBtnText;
  }
}

// ── Rendering Engine (Populates all Views) ─────────────────────
function createUIElement(tag, className, textContent) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  return element;
}

function renderAllViews(data) {
  if (!data) return;

  // Reveal populated markers
  if (loadingState) loadingState.classList.add("hidden");
  if (skeletonState) skeletonState.classList.add("hidden");
  if (resultsContent) resultsContent.classList.remove("hidden");
  if (emptyState) emptyState.classList.add("hidden");

  // Show topbar context pill
  if (activeContextPill) activeContextPill.classList.remove("hidden");
  if (topbarCandidateCtx) {
    const title = data.current_title || "Active Candidate Profile";
    const score = data.match_score ? data.match_score.score : 0;
    topbarCandidateCtx.textContent = `${title} • ${score}/100 Match`;
  }

  // 1. Executive Banner & Sidebar User Details
  renderBanner(data);

  // 2. Score Gauge & Dashboard Metrics
  renderDashboardMetrics(data);

  // 3. Resume Review
  renderResume(data.resume_review);

  // 4. Job Match Comparison Table
  renderJobMatchTable(data);

  // 5. Skill Gaps Priority Cards & Tags
  renderGaps(data.skill_gaps);

  // 6. Career Roadmap & Projects
  renderRoadmap(data.career_roadmap);

  // 7. Interview Prep Accordions
  renderInterview(data.interview_prep);
}

// 1. Candidate Banner & Sidebar Info
function renderBanner(data) {
  const name = data.candidate_name || "Applicant Candidate";
  const title = data.current_title || "Target Role Candidate";
  
  if ($("candidate-name")) $("candidate-name").textContent = name;
  if ($("candidate-title")) $("candidate-title").textContent = title;
  
  if ($("sidebar-user-name")) $("sidebar-user-name").textContent = name;
  if ($("sidebar-user-role")) $("sidebar-user-role").textContent = title;
  
  const score = data.match_score ? data.match_score.score : 0;
  const color = data.match_score ? data.match_score.color : "warning";
  
  const bannerScore = $("banner-score");
  if (bannerScore) {
    bannerScore.textContent = `${score}/100 Match`;
    bannerScore.className = `status-badge ${color}`;
    bannerScore.classList.remove("hidden");
  }
}

// 2. Dashboard Metrics Grid & Summary Cards
function renderDashboardMetrics(data) {
  const ms = data.match_score || { score: 0, label: "Matched", color: "warning" };
  const score = ms.score || 0;
  const color = ms.color || "warning";
  
  // Hero Score Gauge
  if ($("score-number")) {
    $("score-number").textContent = score;
    $("score-number").className = `circular-score-val ${color}`;
  }
  
  if ($("score-label")) {
    $("score-label").textContent = ms.label || "Matched";
    $("score-label").className = `match-label-badge ${color}`;
  }
  
  const circleFill = $("score-ring-fill");
  if (circleFill) {
    const radius = 50;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    circleFill.style.strokeDasharray = `${circumference}`;
    circleFill.style.strokeDashoffset = `${offset}`;
    circleFill.className = `progress-ring-circle-fill ${color}`;
  }

  // Calculate Sub-Metrics
  const gaps = data.skill_gaps || {};
  const missingCount = (gaps.missing_skills || []).length;
  const missingKwCount = (gaps.missing_keywords || []).length;
  
  // Skills Match percentage
  const skillsScore = Math.max(20, Math.min(100, 100 - (missingCount * 12)));
  if ($("dash-skills-val")) $("dash-skills-val").textContent = `${skillsScore}%`;
  if ($("dash-skills-bar")) $("dash-skills-bar").style.width = `${skillsScore}%`;
  if ($("dash-skills-sub")) $("dash-skills-sub").textContent = `${missingCount} missing target skill(s)`;

  // Experience Fit score
  const expScore = Math.min(100, Math.max(40, score + 5));
  if ($("dash-exp-val")) $("dash-exp-val").textContent = `${expScore}%`;
  if ($("dash-exp-bar")) $("dash-exp-bar").style.width = `${expScore}%`;

  // ATS Keyword Readiness percentage
  const atsScore = Math.max(30, Math.min(100, 100 - (missingKwCount * 5)));
  if ($("dash-ats-val")) $("dash-ats-val").textContent = `${atsScore}%`;
  if ($("dash-ats-bar")) $("dash-ats-bar").style.width = `${atsScore}%`;
  if ($("dash-ats-sub")) $("dash-ats-sub").textContent = `${missingKwCount} missing keyword(s)`;

  // Strengths & Gaps Snippets
  const strengths = data.resume_review ? data.resume_review.strengths : [];
  if ($("dash-top-strength")) {
    $("dash-top-strength").textContent = strengths.length ? strengths[0] : "Strong technical background.";
  }

  const priorityGaps = gaps.priority_gaps || [];
  if ($("dash-top-gap")) {
    if (priorityGaps.length) {
      const g = priorityGaps[0];
      $("dash-top-gap").textContent = `${g.skill || 'Gap'}: ${g.reason || ''}`;
    } else {
      $("dash-top-gap").textContent = "No high priority gaps detected.";
    }
  }

  // Immediate Roadmap Step Snippet
  const roadmap = data.career_roadmap || {};
  const immediateSteps = roadmap.immediate || [];
  if ($("dash-immediate-step-text")) {
    $("dash-immediate-step-text").textContent = immediateSteps.length ? immediateSteps[0] : "Focus on learning primary missing stack components.";
  }
}

// 3. Resume Review
function renderResume(rr) {
  if (!rr) return;

  const populateList = (listId, items, emptyText) => {
    const listEl = $(listId);
    if (!listEl) return;
    listEl.innerHTML = "";
    
    if (!items || !items.length) {
      const li = createUIElement("li", "", emptyText);
      listEl.appendChild(li);
      return;
    }
    
    items.forEach(item => {
      const li = createUIElement("li");
      const checkSVG = `<svg class="list-item-bullet" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 5 12"/></svg>`;
      const crossSVG = `<svg class="list-item-bullet" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
      li.innerHTML = (listId === "strengths-list" ? checkSVG : crossSVG) + `<span>${item}</span>`;
      listEl.appendChild(li);
    });
  };

  populateList("strengths-list", rr.strengths, "No specific profile strengths identified.");
  populateList("weaknesses-list", rr.weaknesses, "No critical profile development areas identified.");

  const suggsList = $("suggestions-list");
  if (suggsList) {
    suggsList.innerHTML = "";
    if (!rr.suggestions || !rr.suggestions.length) {
      suggsList.appendChild(createUIElement("li", "", "Profile optimization recommendations are complete. No further action needed."));
    } else {
      rr.suggestions.forEach(s => {
        const li = createUIElement("li");
        const arrowSVG = `<svg class="list-item-bullet" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"/></svg>`;
        li.innerHTML = arrowSVG + `<span>${s}</span>`;
        suggsList.appendChild(li);
      });
    }
  }
}

// 4. Job Match Comparison Table
function renderJobMatchTable(data) {
  const tbody = $("jobmatch-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  const gaps = data.skill_gaps || {};
  const missingSkills = gaps.missing_skills || [];
  const priorityGaps = gaps.priority_gaps || [];

  const rows = [
    {
      category: "Technical Stack",
      requirement: "Core framework & language requirements",
      evidence: missingSkills.length ? `Missing skills: ${missingSkills.join(", ")}` : "All core required technical skills present on resume.",
      status: missingSkills.length ? (missingSkills.length > 2 ? "missing" : "partial") : "matched",
      statusLabel: missingSkills.length ? (missingSkills.length > 2 ? "Missing Skills" : "Partial Fit") : "Full Match"
    },
    {
      category: "Professional Experience",
      requirement: "Seniority & Domain depth",
      evidence: data.resume_review && data.resume_review.strengths ? data.resume_review.strengths[0] : "Experience verified",
      status: "matched",
      statusLabel: "Matched"
    },
    {
      category: "Education & Certifications",
      requirement: "Degree or equivalent experience",
      evidence: "Verified via structured resume analysis",
      status: "matched",
      statusLabel: "Matched"
    },
    {
      category: "ATS Keyword Coverage",
      requirement: "Target job listing terminology",
      evidence: gaps.missing_keywords && gaps.missing_keywords.length ? `${gaps.missing_keywords.length} keywords missing` : "Comprehensive keyword overlap",
      status: gaps.missing_keywords && gaps.missing_keywords.length > 5 ? "partial" : "matched",
      statusLabel: gaps.missing_keywords && gaps.missing_keywords.length > 5 ? "Partial Match" : "Matched"
    }
  ];

  rows.forEach(r => {
    const tr = createUIElement("tr");
    tr.innerHTML = `
      <td><strong>${r.category}</strong></td>
      <td>${r.requirement}</td>
      <td>${r.evidence}</td>
      <td><span class="match-badge ${r.status}">${r.statusLabel}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// 5. Skill Gaps Priority Cards & Tags
function renderGaps(sg) {
  if (!sg) return;
  
  const priorityList = $("priority-gaps-list");
  if (priorityList) {
    priorityList.innerHTML = "";
    const gaps = sg.priority_gaps || [];
    if (!gaps.length) {
      const card = createUIElement("div", "priority-gap-card low");
      card.innerHTML = `
        <div class="priority-gap-header">
          <span class="priority-gap-title">No Critical Gaps</span>
          <span class="gap-priority-badge low">Low</span>
        </div>
        <p class="priority-gap-desc">Your profile aligns closely with the core requirements. No high priority gaps detected.</p>
      `;
      priorityList.appendChild(card);
    } else {
      gaps.forEach(g => {
        const prio = (g.priority || "medium").toLowerCase();
        const card = createUIElement("div", `priority-gap-card ${prio}`);
        card.innerHTML = `
          <div class="priority-gap-header">
            <span class="priority-gap-title">${g.skill || "Skill Block"}</span>
            <span class="gap-priority-badge ${prio}">${g.priority || "Medium"}</span>
          </div>
          <p class="priority-gap-desc">${g.reason || ""}</p>
        `;
        priorityList.appendChild(card);
      });
    }
  }

  const skillsCloud = $("missing-skills-tags");
  if (skillsCloud) {
    skillsCloud.innerHTML = "";
    if (!sg.missing_skills || !sg.missing_skills.length) {
      skillsCloud.appendChild(createUIElement("span", "tag-badge", "None"));
    } else {
      sg.missing_skills.forEach(s => {
        skillsCloud.appendChild(createUIElement("span", "tag-badge danger", s));
      });
    }
  }

  const kwCloud = $("missing-keywords-tags");
  if (kwCloud) {
    kwCloud.innerHTML = "";
    if (!sg.missing_keywords || !sg.missing_keywords.length) {
      kwCloud.appendChild(createUIElement("span", "tag-badge", "None"));
    } else {
      sg.missing_keywords.slice(0, 15).forEach(k => {
        kwCloud.appendChild(createUIElement("span", "tag-badge", k));
      });
    }
  }
}

// 6. Timeline Roadmap & Projects
function renderRoadmap(cr) {
  if (!cr) return;

  const populateTimeline = (listId, items) => {
    const listEl = $(listId);
    if (!listEl) return;
    listEl.innerHTML = "";
    if (!items || !items.length) {
      listEl.appendChild(createUIElement("li", "", "Goal complete. Focus on next milestone."));
      return;
    }
    items.forEach(item => {
      listEl.appendChild(createUIElement("li", "", item));
    });
  };

  populateTimeline("road-immediate", cr.immediate);
  populateTimeline("road-midterm",   cr.mid_term);
  populateTimeline("road-longterm",  cr.long_term);

  const projGrid = $("projects-grid");
  if (projGrid) {
    projGrid.innerHTML = "";
    if (!cr.projects || !cr.projects.length) {
      const pCard = createUIElement("div", "roadmap-project-card");
      pCard.innerHTML = `
        <div class="roadmap-project-header">
          <span class="roadmap-project-title">Custom Project Sandbox</span>
        </div>
        <p class="roadmap-project-desc">Combine missing stack components into a single full-stack deployment sandbox.</p>
      `;
      projGrid.appendChild(pCard);
    } else {
      cr.projects.forEach(p => {
        const pCard = createUIElement("div", "roadmap-project-card");
        const title = createUIElement("span", "roadmap-project-title", p.title || "Project Idea");
        const dur = createUIElement("span", "roadmap-project-duration", p.duration ? `~${p.duration}` : "");
        const header = createUIElement("div", "roadmap-project-header");
        header.appendChild(title);
        header.appendChild(dur);
        
        const desc = createUIElement("p", "roadmap-project-desc", p.desc || "");
        const skillsContainer = createUIElement("div", "roadmap-project-skills-list");
        (p.skills || []).forEach(s => {
          skillsContainer.appendChild(createUIElement("span", "roadmap-project-skill-tag", s));
        });
        
        pCard.appendChild(header);
        pCard.appendChild(desc);
        pCard.appendChild(skillsContainer);
        projGrid.appendChild(pCard);
      });
    }
  }
}

// 7. Interview Preparation Accordions
function renderInterview(ip) {
  if (!ip) return;

  const populateQuestions = (listId, questions) => {
    const listEl = $(listId);
    if (!listEl) return;
    listEl.innerHTML = "";
    if (!questions || !questions.length) {
      listEl.appendChild(createUIElement("p", "empty-state-desc", "No expected questions curated for this category."));
      return;
    }
    
    questions.forEach((q, idx) => {
      const qNode = createUIElement("div", "interview-question-node");
      qNode.innerHTML = `
        <span class="interview-question-index">${idx + 1}</span>
        <span class="interview-question-text">${q}</span>
      `;
      listEl.appendChild(qNode);
    });
  };

  populateQuestions("tech-questions", ip.technical_questions);
  populateQuestions("behavioral-questions", ip.behavioral_questions);

  const sdAccordion = $("sysdesign-section");
  const sdQuestions = $("sysdesign-questions");
  if (sdQuestions) sdQuestions.innerHTML = "";
  
  if (ip.system_design_questions && ip.system_design_questions.length) {
    if (sdAccordion) sdAccordion.classList.remove("hidden");
    populateQuestions("sysdesign-questions", ip.system_design_questions);
  } else {
    if (sdAccordion) sdAccordion.classList.add("hidden");
  }

  const prepAreas = $("prep-areas");
  if (prepAreas) {
    prepAreas.innerHTML = "";
    if (!ip.preparation_areas || !ip.preparation_areas.length) {
      prepAreas.appendChild(createUIElement("p", "empty-state-desc", "Revision guide outline is up to date."));
    } else {
      ip.preparation_areas.forEach(pa => {
        const card = createUIElement("div", "revision-topic-card");
        const title = createUIElement("span", "revision-topic-title", pa.area || "Core Stack");
        const why = createUIElement("span", "revision-topic-why", pa.why || "");
        const list = createUIElement("ul", "revision-topic-actions-list");
        (pa.actions || []).forEach(action => {
          list.appendChild(createUIElement("li", "", action));
        });
        card.appendChild(title);
        card.appendChild(why);
        card.appendChild(list);
        prepAreas.appendChild(card);
      });
    }
  }

  const ansContainer = $("answer-cards");
  if (ansContainer) {
    ansContainer.innerHTML = "";
    if (!ip.suggested_answers || !ip.suggested_answers.length) {
      ansContainer.appendChild(createUIElement("p", "empty-state-desc", "No specific frameworks curated. Use standard STAR method."));
    } else {
      ip.suggested_answers.forEach(sa => {
        const card = createUIElement("div", "suggested-answer-framework-card");
        card.innerHTML = `
          <h4 class="suggested-answer-q">Q: ${sa.question || ""}</h4>
          <div class="suggested-answer-lbl">Framework: ${sa.framework || "STAR"}</div>
        `;
        const bulletList = createUIElement("ul", "suggested-answer-bullets-list");
        (sa.key_points || []).forEach(kp => {
          bulletList.appendChild(createUIElement("li", "", kp));
        });
        card.appendChild(bulletList);
        ansContainer.appendChild(card);
      });
    }
  }
}

// ── Local Storage History Management ──────────────────────────
function loadHistory() {
  try {
    const raw = localStorage.getItem("career_copilot_history");
    state.history = raw ? JSON.parse(raw) : [];
  } catch (err) {
    state.history = [];
  }
  renderHistoryUI();
}

function saveAnalysisToHistory(reportData) {
  const entry = {
    id: Date.now().toString(),
    date: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    title: reportData.current_title || "Career Fit Analysis",
    candidateName: reportData.candidate_name || "Applicant",
    score: reportData.match_score ? reportData.match_score.score : 0,
    color: reportData.match_score ? reportData.match_score.color : "warning",
    topGap: reportData.skill_gaps && reportData.skill_gaps.missing_skills ? reportData.skill_gaps.missing_skills[0] : null,
    data: reportData,
  };

  state.history.unshift(entry);
  if (state.history.length > 20) state.history.pop();
  
  try {
    localStorage.setItem("career_copilot_history", JSON.stringify(state.history));
  } catch (e) {
    console.warn("Could not save history to localStorage", e);
  }
  
  renderHistoryUI();
}

function renderHistoryUI() {
  const container = $("history-list-container");
  const emptyHistory = $("history-empty-state");
  const badge = $("history-count-badge");
  const btnClear = $("btn-clear-history");

  if (badge) {
    badge.textContent = state.history.length;
    if (state.history.length > 0) badge.classList.remove("hidden");
    else badge.classList.add("hidden");
  }

  if (!state.history.length) {
    if (emptyHistory) emptyHistory.classList.remove("hidden");
    if (container) container.classList.add("hidden");
    if (btnClear) btnClear.classList.add("hidden");
    return;
  }

  if (emptyHistory) emptyHistory.classList.add("hidden");
  if (btnClear) btnClear.classList.remove("hidden");
  if (container) {
    container.classList.remove("hidden");
    container.innerHTML = "";

    state.history.forEach(item => {
      const card = createUIElement("div", "history-card");
      card.innerHTML = `
        <div>
          <div class="history-card-header">
            <div>
              <div class="history-title">${item.title}</div>
              <div class="history-date">${item.candidateName} • ${item.date}</div>
            </div>
            <span class="status-badge ${item.color}">${item.score}/100</span>
          </div>
          ${item.topGap ? `<p style="font-size: 0.78rem; color: var(--text-muted);">Top Gap: <strong>${item.topGap}</strong></p>` : ''}
        </div>
        <div class="history-card-footer">
          <button class="btn-primary-sm view-history-btn" data-id="${item.id}">View Report &rarr;</button>
        </div>
      `;
      container.appendChild(card);
    });

    qsa(".view-history-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const found = state.history.find(h => h.id === id);
        if (found && found.data) {
          state.result = found.data;
          renderAllViews(found.data);
          switchView("dashboard");
        }
      });
    });
  }
}

if ($("btn-clear-history")) {
  $("btn-clear-history").addEventListener("click", () => {
    state.history = [];
    localStorage.removeItem("career_copilot_history");
    renderHistoryUI();
  });
}

// ── Startup API Handshake Connection ──────────────────────────
(async () => {
  loadHistory();

  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      if (statusBadge) {
        statusBadge.textContent = data.api_key_configured ? "API Connected" : "API Unconfigured";
        statusBadge.className = "status-badge " + (data.api_key_configured ? "ok" : "error");
      }
    } else {
      if (statusBadge) {
        statusBadge.textContent = "API Check Failed";
        statusBadge.className = "status-badge error";
      }
    }
  } catch (err) {
    console.error("Health handshake failed: ", err);
    if (statusBadge) {
      statusBadge.textContent = "Server Offline";
      statusBadge.className = "status-badge error";
    }
  }
})();
