// Zero-build frontend for the UP Police Data Analyst.
"use strict";

const $ = (id) => document.getElementById(id);

function setStatus(text) {
  const el = $("status");
  if (el) {
    el.textContent = text;
    el.hidden = false;
  }
}

function setDbStatus(text, ok = true) {
  const el = $("db-status");
  if (el) {
    el.textContent = text;
    el.hidden = false;
    el.classList.toggle("stub", !ok);
  }
}

function setRefreshStatus(text, ok = true) {
  const el = $("refresh-status");
  if (el) {
    el.textContent = text;
    el.hidden = false;
    el.classList.toggle("stub", !ok);
  }
}

async function loadHealth() {
  const badge = $("provider-badge");
  try {
    const res = await fetch("/health");
    const body = await res.json();
    const { provider, model, key_configured: keyed } = body.data;
    if (!keyed) {
      badge.textContent = "no API key — set one in .env";
      badge.classList.add("stub");
    } else {
      badge.textContent = `${provider} · ${model}`;
    }
  } catch {
    badge.textContent = "backend unreachable";
    badge.classList.add("stub");
  }
}

async function ingest() {
  const btn = $("ingest-btn");
  const status = $("ingest-status");
  const wrap = $("schema-wrap");
  const text = $("schema-text");
  const input = $("file-input");
  const files = input.files;

  if (!files || !files.length) {
    status.textContent = "Select at least one CSV file first.";
    status.hidden = false;
    return;
  }

  const form = new FormData();
  for (const f of files) form.append("files", f);

  btn.disabled = true;
  setStatus("Ingesting...");

  try {
    const res = await fetch("/api/v1/ingest", { method: "POST", body: form });
    const body = await res.json();
    if (!res.ok) throw new Error(body?.detail?.message || `HTTP ${res.status}`);
    const data = body.data;
    text.textContent = data.schema_markdown || "(no tables)";
    wrap.hidden = false;
    status.textContent = `Ingested ${data.tables.length} table(s). Session: ${data.session_id}`;
    renderUploadQueue(data.uploads || []);
    loadSessions();
    } catch (err) {
    status.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

function renderTable(columns, rows) {
  const table = $("result-table");
  if (!columns.length) { table.innerHTML = ""; return; }
  const thead = "<tr>" + columns.map((c) => `<th>${c}</th>`).join("") + "</tr>";
  const tbody = rows
    .map((r) => "<tr>" + r.map((v) => `<td>${v == null ? "" : v}</td>`).join("") + "</tr>")
    .join("");
  table.innerHTML = thead + tbody;
}

async function runQuestion() {
  const btn = $("run-btn");
  const status = $("status");
  const errBox = $("error");
  const wrap = $("result-wrap");
  const question = $("question").value.trim();

  errBox.hidden = true;
  wrap.hidden = true;

  if (!question) {
    errBox.textContent = "Type a question first.";
    errBox.hidden = false;
    return;
  }

  btn.disabled = true;
  setStatus("Running… Planning → executing → finalizing");

  const start = performance.now();
  try {
    const sid = ($("session-select")?.value || "sess1");
    const res = await fetch(`/api/v1/query?session_id=${encodeURIComponent(sid)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        session_id: sid,
        question,
        data_source: document.getElementById("data-source").value,
      }),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body?.detail?.message || `HTTP ${res.status}`);
    const queued = body.data;
    const elapsed = Math.max(0, Math.round((performance.now() - start) / 1000));
    setStatus(`Queued as ${queued.run_id} (${elapsed}s) — polling`);

    const run = await pollRun(queued.run_id, status);
    if (run.status === "failed") {
      errBox.textContent = run.error_message || "Run failed.";
      errBox.hidden = false;
      status.hidden = true;
      return;
    }

    let parsed = {};
    if (typeof run.output_text === "string") {
      try { parsed = JSON.parse(run.output_text); } catch { parsed = {}; }
    } else {
      parsed = run.output_text || {};
    }

    $("answer").innerHTML = `<p>${parsed.answer || "(no answer)"}</p>`;
    if (parsed.sql) $("sql").textContent = parsed.sql;

    if (Array.isArray(parsed.suggestions) && parsed.suggestions.length) {
      const chips = $("suggestions");
      chips.innerHTML = parsed.suggestions.map((s) => `<button class="chip">${s}</button>`).join("");
      chips.querySelectorAll(".chip").forEach((btn, i) => {
        btn.addEventListener("click", () => {
          $("question").value = parsed.suggestions[i];
          runQuestion();
        });
      });
    }

    const latencyMs = typeof parsed.latency_ms === "number" ? parsed.latency_ms : null;
    if (latencyMs != null) $("latency-badge").textContent = `${latencyMs} ms`;
    $("source-badge").textContent = parsed.source || "cache";

    const cols = Array.isArray(parsed.table?.columns) ? parsed.table.columns : [];
    const rows = Array.isArray(parsed.table?.rows) ? parsed.table.rows : [];
    if (cols.length) {
      $("table-wrap").hidden = false;
      renderTable(cols, rows);
    } else {
      $("table-wrap").hidden = true;
    }

    if (parsed.chart) {
      $("chart-wrap").hidden = false;
      Plotly.newPlot(
        "chart",
        parsed.chart.data || [],
        parsed.chart.layout || {},
        { displayModeBar: false, responsive: true }
      );
    } else {
      $("chart-wrap").hidden = true;
    }

    wrap.hidden = false;
    setStatus(`Completed in ${typeof latencyMs === "number" ? latencyMs + " ms" : "unknown time"}`);
  } catch (err) {
    errBox.textContent = err.message;
    errBox.hidden = false;
    status.hidden = true;
  } finally {
    btn.disabled = false;
  }
}

async function pollRun(runId, statusEl) {
  for (let i = 0; i < 40; i++) {
    await new Promise((r) => setTimeout(r, 500));
    const res = await fetch(`/runs/${runId}`);
    const body = await res.json();
    const run = body.data;
    if (run.status === "completed" || run.status === "failed") return run;
    if (statusEl) setStatus(`Polling... (${(i + 1) * 0.5}s)`);
  }
  throw new Error("Timed out waiting for run.");
}

async function connectDb() {
  const input = $("db-conn-input");
  const value = (input?.value || "").trim();
  if (!value) {
    setDbStatus("Paste a connection string first.", false);
    return;
  }
  setDbStatus("Connecting...", true);
  try {
    const res = await fetch("/api/v1/db/connect", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ connection_string: value }),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body?.detail?.message || `HTTP ${res.status}`);
    const info = body.data;
    setDbStatus(`Connected: ${info.server || "ok"}`, true);
  } catch (err) {
    setDbStatus(err.message, false);
  }
}

async function refreshCache() {
  const sid = ($("session-select")?.value || "sess1");
  setRefreshStatus(`Refreshing cache for ${sid}...`, true);
  try {
    const res = await fetch(`/api/v1/db/refresh-cache?session_id=${encodeURIComponent(sid)}`, { method: "POST" });
    const body = await res.json();
    if (!res.ok) throw new Error(body?.detail?.message || `HTTP ${res.status}`);
    const info = body.data;
    setRefreshStatus(`Synced ${info.tables_synced ?? "?"} tables · ${info.total_rows ?? 0} rows · ${info.elapsed_ms ?? 0} ms`, true);
  } catch (err) {
    setRefreshStatus(err.message, false);
  }
}

function renderUploadQueue(uploads) {
  const wrap = $("upload-queue");
  if (!wrap) return;
  if (!uploads.length) { wrap.innerHTML = ""; wrap.hidden = true; return; }
  wrap.hidden = false;
  wrap.innerHTML =
    '<div class="queue-head">Uploaded files</div>' +
    '<ul>' +
    uploads
      .map(
        (u) =>
          `<li><span class="queue-name">${(u.filename || "upload.csv")}</span> → <span class="queue-table">${u.table_name}</span> <span class="queue-meta">${u.row_count ?? 0} rows · ${u.bytes} bytes</span></li>`
      )
      .join("") +
    "</ul>";
}

async function loadSessions() {
  try {
    const res = await fetch("/api/v1/sessions");
    const body = await res.json();
    if (!res.ok) throw new Error(body?.detail?.message || `HTTP ${res.status}`);
    const list = body.data?.items || [];
    const sel = $("session-select");
    if (!sel) return;
    sel.innerHTML =
      list
        .map(
          (s) =>
            `<option value="${s.session_id}">${s.session_name || s.session_id}</option>`
        )
        .join("") || `<option value="sess1">sess1</option>`;
  } catch (err) {
    // Non-blocking: keep default session
  }
}

async function loadSchemaForSession(sessionId) {
  try {
    const res = await fetch(`/api/v1/ingest/schema?session_id=${encodeURIComponent(sessionId || "sess1")}`);
    const body = await res.json();
    if (!res.ok) throw new Error(body?.detail?.message || `HTTP ${res.status}`);
    const data = body.data || {};
    const text = $("schema-text");
    const wrap = $("schema-wrap");
    if (text) text.textContent = data.schema_markdown || "(no tables)";
    if (wrap) wrap.hidden = false;
  } catch (err) {
    const text = $("schema-text");
    if (text) text.textContent = `(schema unavailable: ${err.message})`;
  }
}

$("ingest-btn").addEventListener("click", async () => {
  await ingest();
  try {
    const sel = $("session-select");
    if (sel?.value) loadSchemaForSession(sel.value);
  } catch {}
});

$("run-btn").addEventListener("click", runQuestion);
if ($("db-connect-btn")) $("db-connect-btn").addEventListener("click", connectDb);
if ($("db-refresh-btn")) $("db-refresh-btn").addEventListener("click", refreshCache);
if ($("session-select")) $("session-select").addEventListener("change", (e) => loadSchemaForSession(e.target.value));
loadHealth();
loadSessions();
try { loadSchemaForSession("sess1"); } catch {}
