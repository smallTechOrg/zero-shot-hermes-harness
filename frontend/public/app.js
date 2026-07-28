// Zero-build data analyst frontend. Single-origin: the page is served by the
// backend at /app, so API calls are same-origin relative paths.
"use strict";

const $ = (id) => document.getElementById(id);

async function loadHealth() {
 const badge = $("provider-badge");
 try {
 const res = await fetch("/health");
 const body = await res.json();
 const { provider, model, key_configured: keyed } = body.data;
 if (!keyed) {
 badge.textContent = "no API key -- set one in .env";
 badge.classList.add("stub");
 } else {
 badge.textContent = provider + " " + model;
 }
 } catch {
 badge.textContent = "backend unreachable";
 badge.classList.add("stub");
 }
}

async function uploadCsv() {
 const input = $("csv-input");
 const status = $("upload-status");
 status.hidden = true;
 if (!input.files || !input.files.length) {
 status.textContent = "Choose at least one CSV first.";
 status.hidden = false;
 return;
 }
 const form = new FormData();
 for (const file of input.files) {
 form.append("files", file);
 }
 status.textContent = "Uploading...";
 status.hidden = false;
 try {
 const res = await fetch("/ingest", { method: "POST", body: form });
 const body = await res.json();
 if (!res.ok) {
 throw new Error((body && body.detail && body.detail.message) || ("HTTP " + res.status));
 }
 status.textContent = "Uploaded " + (body.files || []).length + " file(s).";
 } catch (err) {
 status.textContent = err.message;
 }
}

async function runQuery() {
 const btn = $("run-btn");
 const status = $("status");
 const errBox = $("error");
 const question = $("question").value.trim();
 errBox.hidden = true;
 status.hidden = true;
 if (!question) {
 errBox.textContent = "Type a question first.";
 errBox.hidden = false;
 return;
 }
 btn.disabled = true;
 status.textContent = "Running...";
 status.hidden = false;
 try {
 const res = await fetch("/runs", {
 method: "POST",
 headers: { "content-type": "application/json" },
 body: JSON.stringify({ text: question }),
 });
 const body = await res.json();
 if (!res.ok) {
 throw new Error((body && body.detail && body.detail.message) || ("HTTP " + res.status));
 }
 const run = body.data;
 if (run.status === "failed") {
 throw new Error(run.error_message || "The agent run failed.");
 }
 renderRun(run);
 } catch (err) {
 errBox.textContent = err.message;
 errBox.hidden = false;
 } finally {
 btn.disabled = false;
 status.hidden = true;
 }
}

function renderRun(run) {
 const wrap = $("result-card");
 wrap.hidden = false;
 $("result-meta").textContent = "run " + run.run_id + " / " + run.provider + " / " + run.model;
 $("answer").textContent = run.output_text || "";
 renderTable(run.table);
 renderChart(run.chart);
 renderExports(run.export_links);
}

function renderTable(table) {
 const wrap = $("table-wrap");
 const tableEl = $("result-table");
 if (!table || !table.columns || !table.rows) {
 wrap.hidden = true;
 return;
 }
 wrap.hidden = false;
 const thead = tableEl.createTHead();
 const tr = thead.insertRow();
 table.columns.forEach((col) => {
 const th = document.createElement("th");
 th.textContent = col;
 tr.appendChild(th);
 });
 const tbody = tableEl.createTBody();
 table.rows.forEach((row) => {
 const tr = tbody.insertRow();
 table.columns.forEach((col, idx) => {
 const td = tr.insertCell();
 td.textContent = row[col] != null ? row[col] : "";
 });
 });
}

function renderChart(chart) {
 const wrap = $("chart-wrap");
 const img = $("chart-img");
 if (!chart || !chart.url) {
 wrap.hidden = true;
 return;
 }
 wrap.hidden = false;
 img.src = chart.url;
}

function renderExports(exportLinks) {
 const wrap = $("export-wrap");
 const container = $("export-links");
 container.innerHTML = "";
 if (!exportLinks) {
 wrap.hidden = true;
 return;
 }
 wrap.hidden = false;
 Object.entries(exportLinks).forEach(([fmt, url]) => {
 const a = document.createElement("a");
 a.href = url;
 a.textContent = "Download " + fmt.toUpperCase();
 a.target = "_blank";
 a.rel = "noopener";
 container.appendChild(a);
 });
}

$("upload-btn").addEventListener("click", uploadCsv);
$("run-btn").addEventListener("click", runQuery);
loadHealth();
