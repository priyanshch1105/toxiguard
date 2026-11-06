const views = {
  detect: { title: "Toxic content detector", subtitle: "Classify comments into six Jigsaw toxicity labels with calibrated confidence scores." },
  history: { title: "Moderation history", subtitle: "Every analyzed comment is stored with scores, timestamps, and a moderation decision." },
  analytics: { title: "Live analytics", subtitle: "Track volume, toxic rate, and label mix from comments submitted in this demo." },
  admin: { title: "Admin model lab", subtitle: "Compare trained models on the held-out Jigsaw test split. No dummy metrics." }
};

const samples = [
  "This article is well sourced and I appreciate the extra context in the talk page.",
  "You are an idiot and nobody wants you here. Go away.",
  "I will find you and hurt you if you keep posting this.",
  "That edit was stupid, you moron, and your whole community is trash."
];

const navButtons = document.querySelectorAll(".nav-btn");
const commentInput = document.getElementById("commentInput");
const charCount = document.getElementById("charCount");
const analyzeBtn = document.getElementById("analyzeBtn");
const sampleBtn = document.getElementById("sampleBtn");
const formError = document.getElementById("formError");
const resultEmpty = document.getElementById("resultEmpty");
const resultBody = document.getElementById("resultBody");
const verdictBox = document.getElementById("verdictBox");
const verdictTitle = document.getElementById("verdictTitle");
const verdictCopy = document.getElementById("verdictCopy");
const maxConfidence = document.getElementById("maxConfidence");
const labelGrid = document.getElementById("labelGrid");
const historyBody = document.querySelector("#historyTable tbody");
const historyEmpty = document.getElementById("historyEmpty");
const compareBody = document.querySelector("#compareTable tbody");
const metricsNote = document.getElementById("metricsNote");
const testMetrics = document.getElementById("testMetrics");
const kpiGrid = document.getElementById("kpiGrid");
const modelStatus = document.getElementById("modelStatus");
const bestModelChip = document.getElementById("bestModelChip");
const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");

let sampleIndex = 0;
let timelineChart;
let labelChart;
let labelMetricChart;

function showView(name) {
  document.querySelectorAll(".view").forEach((view) => {
    const active = view.id === `view-${name}`;
    view.classList.toggle("active", active);
    view.hidden = !active;
  });
  navButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.view === name));
  document.getElementById("pageTitle").textContent = views[name].title;
  document.getElementById("pageSubtitle").textContent = views[name].subtitle;
  sidebar.classList.remove("open");
  if (name === "history") loadHistory();
  if (name === "analytics") loadAnalytics();
  if (name === "admin") loadMetrics();
}

navButtons.forEach((btn) => btn.addEventListener("click", () => showView(btn.dataset.view)));
menuToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
commentInput.addEventListener("input", () => {
  charCount.textContent = `${commentInput.value.length} / 5000`;
});
sampleBtn.addEventListener("click", () => {
  commentInput.value = samples[sampleIndex % samples.length];
  sampleIndex += 1;
  commentInput.dispatchEvent(new Event("input"));
});
document.getElementById("refreshHistory").addEventListener("click", loadHistory);

analyzeBtn.addEventListener("click", async () => {
  formError.textContent = "";
  analyzeBtn.disabled = true;
  analyzeBtn.querySelector(".spinner").hidden = false;
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: commentInput.value, source: "web" })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Analysis failed");
    renderResult(data);
  } catch (error) {
    formError.textContent = error.message;
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.querySelector(".spinner").hidden = true;
  }
});

function renderResult(data) {
  resultEmpty.hidden = true;
  resultBody.hidden = false;
  verdictBox.className = `verdict ${data.moderation_result}`;
  verdictTitle.textContent = data.moderation_result;
  const labels = data.triggered_labels.length ? data.triggered_labels.join(", ") : "none";
  verdictCopy.textContent = data.is_toxic
    ? `Flagged labels: ${labels}.`
    : "No toxicity labels crossed the 0.50 threshold.";
  maxConfidence.textContent = `${Math.round(data.max_confidence * 100)}%`;
  labelGrid.innerHTML = Object.values(data.labels).map((item) => `
    <div class="label-row ${item.flagged ? "flagged" : ""}">
      <span>${item.label}</span>
      <div class="bar" aria-hidden="true"><span style="width:${Math.round(item.score * 100)}%"></span></div>
      <strong>${Math.round(item.score * 100)}%</strong>
    </div>
  `).join("");
}

async function loadHistory() {
  const response = await fetch("/api/history");
  const rows = await response.json();
  historyBody.innerHTML = rows.map((row) => `
    <tr>
      <td>${formatTime(row.created_at)}</td>
      <td class="comment-cell">${escapeHtml(row.text)}</td>
      <td><span class="badge ${row.moderation_result}">${row.moderation_result}</span></td>
      <td>${row.triggered_labels.join(", ") || "Safe"}</td>
      <td>${Math.round(row.max_confidence * 100)}%</td>
    </tr>
  `).join("");
  historyEmpty.hidden = rows.length > 0;
}

async function loadAnalytics() {
  const response = await fetch("/api/analytics");
  const data = await response.json();
  const kpis = [
    ["Analyzed comments", data.totals.analyzed],
    ["Toxic comments", data.totals.toxic],
    ["Safe comments", data.totals.safe],
    ["Toxic rate", `${Math.round(data.totals.toxic_rate * 100)}%`]
  ];
  kpiGrid.innerHTML = kpis.map(([label, value]) => `
    <article class="kpi"><span>${label}</span><strong>${value}</strong></article>
  `).join("");

  const dates = data.timeline.map((item) => item.date.slice(5));
  timelineChart = upsertChart(timelineChart, document.getElementById("timelineChart"), {
    type: "line",
    data: {
      labels: dates,
      datasets: [
        { label: "Total", data: data.timeline.map((item) => item.total), borderColor: "#3b82f6", tension: 0.3 },
        { label: "Toxic", data: data.timeline.map((item) => item.toxic), borderColor: "#ef4444", tension: 0.3 }
      ]
    },
    options: chartDefaults()
  });

  const labelNames = Object.keys(data.label_distribution);
  labelChart = upsertChart(labelChart, document.getElementById("labelChart"), {
    type: "bar",
    data: {
      labels: labelNames,
      datasets: [{
        label: "Flagged comments",
        data: labelNames.map((name) => data.label_distribution[name]),
        backgroundColor: ["#ef4444", "#b91c1c", "#f97316", "#eab308", "#fb7185", "#a855f7"]
      }]
    },
    options: chartDefaults()
  });
}

async function loadMetrics() {
  const response = await fetch("/api/metrics");
  if (!response.ok) {
    metricsNote.textContent = "Train the model first with python -m ml.train";
    return;
  }
  const data = await response.json();
  bestModelChip.textContent = `Best model: ${data.best_model}`;
  modelStatus.textContent = `Ready · ${data.best_model}`;
  metricsNote.textContent = data.notes;
  compareBody.innerHTML = Object.entries(data.comparison).map(([name, item]) => `
    <tr>
      <td>${name}${name === data.best_model ? " (selected)" : ""}</td>
      <td>${pct(item.validation.macro_f1)}</td>
      <td>${pct(item.validation.any_toxic_f1)}</td>
      <td>${pct(item.validation.macro_roc_auc)}</td>
      <td>${item.train_seconds}s</td>
    </tr>
  `).join("");
  const overall = data.test.overall;
  const cards = [
    ["Subset accuracy", overall.subset_accuracy],
    ["Hamming accuracy", overall.hamming_accuracy],
    ["Macro F1", overall.macro_f1],
    ["Micro F1", overall.micro_f1],
    ["Any-toxic F1", overall.any_toxic_f1],
    ["Macro ROC-AUC", overall.macro_roc_auc]
  ];
  testMetrics.innerHTML = cards.map(([label, value]) => `
    <div class="metric-item"><span>${label}</span><strong>${pct(value)}</strong></div>
  `).join("");
  const labels = Object.keys(data.test.per_label);
  labelMetricChart = upsertChart(labelMetricChart, document.getElementById("labelMetricChart"), {
    type: "bar",
    data: {
      labels: labels.map((name) => name.replace("_", " ")),
      datasets: [
        { label: "F1", data: labels.map((name) => data.test.per_label[name].f1), backgroundColor: "#3b82f6" },
        { label: "ROC-AUC", data: labels.map((name) => data.test.per_label[name].roc_auc), backgroundColor: "#22c55e" }
      ]
    },
    options: chartDefaults()
  });
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    modelStatus.textContent = data.status === "ok" ? "Model ready" : "Model training";
    if (data.status === "ok") loadMetrics();
  } catch (error) {
    modelStatus.textContent = "API offline";
  }
}

function upsertChart(existing, canvas, config) {
  if (existing) existing.destroy();
  return new Chart(canvas, config);
}

function chartDefaults() {
  return {
    responsive: true,
    plugins: { legend: { labels: { color: "#93a0bf" } } },
    scales: {
      x: { ticks: { color: "#93a0bf" }, grid: { color: "rgba(147,160,191,0.08)" } },
      y: { ticks: { color: "#93a0bf" }, grid: { color: "rgba(147,160,191,0.08)" }, beginAtZero: true }
    }
  };
}

function pct(value) {
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function formatTime(value) {
  if (!value) return "";
  return new Date(value).toLocaleString();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
}

checkHealth();
