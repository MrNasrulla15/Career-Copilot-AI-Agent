// app.js — Career Copilot Premium Client

// ── State Management ──────────────────────────────────────────
const state = {
  file: null,
  jobDescription: "",
  loading: false,
  result: null,
};

// ── DOM Reference Helpers ─────────────────────────────────────
const $ = id => document.getElementById(id);
const qsa = selector => document.querySelectorAll(selector);

// Navigation & Theme Elements
const tabWorkspace  = $("btn-tab-workspace");
const tabShowcase   = $("btn-tab-showcase");
const secWorkspace  = $("section-workspace");
const secShowcase   = $("section-showcase");
const themeToggle   = $("theme-toggle-btn");
const themeSun      = $("theme-icon-sun");
const themeMoon     = $("theme-icon-moon");

// Input Panels
const uploadZone    = $("upload-zone");
const fileInput     = $("resume-file");
const fileInfo      = $("file-info");
const fileName      = $("file-name");
const removeFile    = $("remove-file");
const jdTextarea    = $("job-description");
const jdCounter     = $("jd-counter");
const btnPasteDesc  = $("btn-paste-desc");
const analyzeBtn    = $("analyze-btn");
const errorBox      = $("error-box");
const errorMessage  = $("error-message");

// Dashboard States
const emptyState    = $("empty-state");
const loadingState  = $("loading-state");
const skeletonState = $("results-skeleton");
const resultsPanel  = $("results-panel");
const resultsContent = $("results-content");
const statusBadge   = $("status-badge");
const pipelineFill  = $("pipeline-fill");

// Pipeline Steps Map
const pipeSteps = {
  resume:   $("ps-resume"),
  job:      $("ps-job"),
  gap:      $("ps-gap"),
  strategy: $("ps-strategy"),
  interview:$("ps-interview"),
};

// ── Theme Switcher Logic ──────────────────────────────────────
function initTheme() {
  const storedTheme = localStorage.getItem("theme");
  const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  
  if (storedTheme === "dark" || (!storedTheme && systemPrefersDark)) {
    document.body.classList.add("dark-theme");
    themeSun.classList.add("hidden");
    themeMoon.classList.remove("hidden");
  } else {
    document.body.classList.remove("dark-theme");
    themeSun.classList.remove("hidden");
    themeMoon.classList.add("hidden");
  }
}

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

// Initialize theme on load
initTheme();

// ── Navigation Tab Logic ──────────────────────────────────────
function switchTab(target) {
  if (target === "workspace") {
    tabWorkspace.classList.add("active");
    tabWorkspace.setAttribute("aria-selected", "true");
    tabShowcase.classList.remove("active");
    tabShowcase.setAttribute("aria-selected", "false");
    
    secWorkspace.classList.remove("hidden");
    secShowcase.classList.add("hidden");
  } else if (target === "showcase") {
    tabShowcase.classList.add("active");
    tabShowcase.setAttribute("aria-selected", "true");
    tabWorkspace.classList.remove("active");
    tabWorkspace.setAttribute("aria-selected", "false");
    
    secShowcase.classList.remove("hidden");
    secWorkspace.classList.add("hidden");
  }
}

tabWorkspace.addEventListener("click", () => switchTab("workspace"));
tabShowcase.addEventListener("click", () => switchTab("showcase"));

// ── Drag & Drop File Upload ──────────────────────────────────
fileInput.addEventListener("change", () => {
  if (fileInput.files && fileInput.files[0]) handleFile(fileInput.files[0]);
});

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
  fileName.textContent = file.name;
  fileInfo.classList.remove("hidden");
  uploadZone.classList.add("hidden");
  hideError();
  checkReady();
}

removeFile.addEventListener("click", e => {
  e.preventDefault();
  state.file = null;
  fileInput.value = "";
  fileInfo.classList.add("hidden");
  uploadZone.classList.remove("hidden");
  checkReady();
});

// ── Job Description Input & Clipboard Action ──────────────────
jdTextarea.addEventListener("input", () => {
  state.jobDescription = jdTextarea.value;
  jdCounter.textContent = state.jobDescription.length + " characters";
  checkReady();
});

btnPasteDesc.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      jdTextarea.value = text;
      state.jobDescription = text;
      jdCounter.textContent = text.length + " characters";
      checkReady();
    }
  } catch (err) {
    console.warn("Unable to access clipboard: ", err);
  }
});

function checkReady() {
  analyzeBtn.disabled = !(state.file && state.jobDescription.trim().length > 30);
}

// ── Error Management ──────────────────────────────────────────
function showError(msg) {
  errorMessage.textContent = msg;
  errorBox.classList.remove("hidden");
}
function hideError() {
  errorBox.classList.add("hidden");
}

// ── Expandable Accordions Handling ────────────────────────────
function setupAccordions() {
  const accordions = qsa(".accordion-header-btn");
  
  accordions.forEach(btn => {
    // Remove existing event listener if re-initialized, but since it's a static bind, simple listener is fine
    btn.onclick = () => {
      const wrapper = btn.closest(".accordion-wrapper");
      const isExpanded = wrapper.classList.contains("expanded");
      
      // Toggle expanded state
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

// Initialize static accordions
setupAccordions();

// ── Agent Pipeline Steps Progress Logic ───────────────────────
let stepIndex = 0;
let stepTimer = null;
const stepKeys = ["resume", "job", "gap", "strategy", "interview"];

function startStepAnimation() {
  stepIndex = 0;
  pipelineFill.style.width = "0%";
  
  stepKeys.forEach(k => {
    pipeSteps[k].classList.remove("active", "done");
  });
  
  pipeSteps[stepKeys[0]].classList.add("active");
  
  // Advance steps over 35 seconds (approximate API response duration)
  stepTimer = setInterval(() => {
    pipeSteps[stepKeys[stepIndex]].classList.remove("active");
    pipeSteps[stepKeys[stepIndex]].classList.add("done");
    stepIndex++;
    
    // Update visual connecting line fill percentage
    const fillPercent = (stepIndex / (stepKeys.length - 1)) * 100;
    pipelineFill.style.width = Math.min(fillPercent, 100) + "%";
    
    if (stepIndex < stepKeys.length) {
      pipeSteps[stepKeys[stepIndex]].classList.add("active");
    } else {
      clearInterval(stepTimer);
    }
  }, 7000);
}

function stopStepAnimation() {
  clearInterval(stepTimer);
  pipelineFill.style.width = "100%";
  stepKeys.forEach(k => {
    pipeSteps[k].classList.remove("active");
    pipeSteps[k].classList.add("done");
  });
}

// ── Run Analysis Pipeline ─────────────────────────────────────
analyzeBtn.addEventListener("click", runAnalysis);

async function runAnalysis() {
  if (!state.file || !state.jobDescription.trim()) return;
  
  hideError();
  state.loading = true;
  analyzeBtn.disabled = true;
  const originalBtnText = analyzeBtn.textContent;
  analyzeBtn.innerHTML = `<span class="btn-spinner"></span> Analyzing Career Fit...`;

  // UI state transition
  emptyState.classList.add("hidden");
  loadingState.classList.remove("hidden");
  skeletonState.classList.remove("hidden");
  resultsContent.classList.add("hidden");
  
  resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  startStepAnimation();

  const formData = new FormData();
  formData.append("resume_file", state.file);
  formData.append("job_description", state.jobDescription);

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });
    
    const json = await response.json();
    stopStepAnimation();

    if (!response.ok) {
      const msg = json.detail || "Analysis failed. Please check file format and content.";
      showError(msg);
      if (response.status === 429) {
        showError("Gemini API daily quota limit reached (Free tier is limited to 20 requests per day). Please retry later.");
      }
      loadingState.classList.add("hidden");
      skeletonState.classList.add("hidden");
      emptyState.classList.remove("hidden");
      return;
    }

    state.result = json.data;
    renderResults(json.data);

  } catch (err) {
    stopStepAnimation();
    showError("Network/Server connection error: " + err.message);
    loadingState.classList.add("hidden");
    skeletonState.classList.add("hidden");
    emptyState.classList.remove("hidden");
  } finally {
    state.loading = false;
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = originalBtnText;
  }
}

// ── Rendering Engine & Helpers ────────────────────────────────
function createUIElement(tag, className, textContent) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  return element;
}

function renderResults(data) {
  // Hide loading/skeletons and reveal content
  loadingState.classList.add("hidden");
  skeletonState.classList.add("hidden");
  resultsContent.classList.remove("hidden");

  // Populate cards
  renderBanner(data);
  renderScore(data.match_score);
  renderResume(data.resume_review);
  renderGaps(data.skill_gaps);
  renderRoadmap(data.career_roadmap);
  renderInterview(data.interview_prep);

  // Scroll to results cleanly
  resultsContent.scrollIntoView({ behavior: "smooth", block: "start" });
}

// 1. Header banner info
function renderBanner(data) {
  $("candidate-name").textContent  = data.candidate_name || "Applicant Name";
  $("candidate-title").textContent = data.current_title || "Current Role Not Listed";
  
  const score = data.match_score.score || 0;
  const color = data.match_score.color || "warning";
  
  const bannerScore = $("banner-score");
  bannerScore.textContent = `${score}/100 Match`;
  bannerScore.className = `status-badge ${color}`;
}

// 2. Matching score circular gauge
function renderScore(ms) {
  const score = ms.score || 0;
  const color = ms.color || "warning";
  
  const scoreNum = $("score-number");
  scoreNum.textContent = score;
  scoreNum.className = `circular-score-val ${color}`;
  
  const label = $("score-label");
  label.textContent = ms.label || "Matched";
  label.className = `match-label-badge ${color}`;
  
  // Animate circular SVG fill
  const circleFill = $("score-ring-fill");
  const radius = 50;
  const circumference = 2 * Math.PI * radius; // ~314.16
  const offset = circumference - (score / 100) * circumference;
  
  circleFill.style.strokeDasharray = `${circumference}`;
  circleFill.style.strokeDashoffset = `${offset}`;
  circleFill.className = `progress-ring-circle-fill ${color}`;
}

// 3. Resume strength, development areas, suggestions
function renderResume(rr) {
  const populateList = (listId, items, emptyText) => {
    const listEl = $(listId);
    listEl.innerHTML = "";
    
    if (!items || !items.length) {
      const li = createUIElement("li", "", emptyText);
      listEl.appendChild(li);
      return;
    }
    
    items.forEach(item => {
      const li = createUIElement("li");
      
      // Inline SVGs for checkmark/x icon bullets
      const checkSVG = `<svg class="list-item-bullet" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 5 12"/></svg>`;
      const crossSVG = `<svg class="list-item-bullet" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
      
      li.innerHTML = (listId === "strengths-list" ? checkSVG : crossSVG) + `<span>${item}</span>`;
      listEl.appendChild(li);
    });
  };

  populateList("strengths-list", rr.strengths, "No specific profile strengths identified.");
  populateList("weaknesses-list", rr.weaknesses, "No critical profile development areas identified.");

  // Improvements suggestions
  const suggsList = $("suggestions-list");
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

// 4. Skill Gaps priority cards & tags
function renderGaps(sg) {
  // Priority Gaps list
  const priorityList = $("priority-gaps-list");
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

  // Missing Skills Tags
  const skillsCloud = $("missing-skills-tags");
  skillsCloud.innerHTML = "";
  if (!sg.missing_skills || !sg.missing_skills.length) {
    skillsCloud.appendChild(createUIElement("span", "tag-badge", "None"));
  } else {
    sg.missing_skills.forEach(s => {
      const tag = createUIElement("span", "tag-badge danger", s);
      skillsCloud.appendChild(tag);
    });
  }

  // Missing Keywords Tags
  const kwCloud = $("missing-keywords-tags");
  kwCloud.innerHTML = "";
  if (!sg.missing_keywords || !sg.missing_keywords.length) {
    kwCloud.appendChild(createUIElement("span", "tag-badge", "None"));
  } else {
    sg.missing_keywords.slice(0, 15).forEach(k => {
      const tag = createUIElement("span", "tag-badge", k);
      kwCloud.appendChild(tag);
    });
  }
}

// 5. Timeline Action Plan & Projects
function renderRoadmap(cr) {
  const populateTimeline = (listId, items) => {
    const listEl = $(listId);
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

  // Suggested Projects Grid
  const projGrid = $("projects-grid");
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

// 6. Accordion Questions, revision cards, Suggested Answers
function renderInterview(ip) {
  const populateQuestions = (listId, questions) => {
    const listEl = $(listId);
    listEl.innerHTML = "";
    if (!questions || !questions.length) {
      listEl.appendChild(createUIElement("p", "empty-state-desc", "No expected questions curated for this domain."));
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

  // System Design Accordion Visibility
  const sdAccordion = $("sysdesign-section");
  const sdQuestions = $("sysdesign-questions");
  sdQuestions.innerHTML = "";
  
  if (ip.system_design_questions && ip.system_design_questions.length) {
    sdAccordion.classList.remove("hidden");
    populateQuestions("sysdesign-questions", ip.system_design_questions);
  } else {
    sdAccordion.classList.add("hidden");
  }

  // Revision Topics
  const prepAreas = $("prep-areas");
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

  // Suggested Answer Frameworks
  const ansContainer = $("answer-cards");
  ansContainer.innerHTML = "";
  if (!ip.suggested_answers || !ip.suggested_answers.length) {
    ansContainer.appendChild(createUIElement("p", "empty-state-desc", "No specific frameworks curated. Use standard STAR/CAR method."));
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

// ── Startup API Handshake Connection ──────────────────────────
(async () => {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      statusBadge.textContent = data.api_key_configured ? "API Connected" : "API Unconfigured";
      statusBadge.className = "status-badge " + (data.api_key_configured ? "ok" : "error");
    } else {
      statusBadge.textContent = "API Service Check Failed";
      statusBadge.className = "status-badge error";
    }
  } catch (err) {
    console.error("Health handshake failed: ", err);
    statusBadge.textContent = "Server Offline";
    statusBadge.className = "status-badge error";
  }
})();
