const API_BASE = ""; // same-origin: FastAPI serves this file and the /api/* routes together

const state = { page: 1, pageSize: 20 };

const els = {
  keyword: document.getElementById("keyword"),
  jobType: document.getElementById("jobType"),
  sortBy: document.getElementById("sortBy"),
  remoteOnly: document.getElementById("remoteOnly"),
  searchBtn: document.getElementById("searchBtn"),
  results: document.getElementById("results"),
  meta: document.getElementById("meta"),
  pagination: document.getElementById("pagination"),
  signInForm: document.getElementById("signInForm"),
  signInEmail: document.getElementById("signInEmail"),
  signedOutView: document.getElementById("signedOutView"),
  signedInView: document.getElementById("signedInView"),
  signedInEmail: document.getElementById("signedInEmail"),
  logoutBtn: document.getElementById("logoutBtn"),
  authStatus: document.getElementById("authStatus"),
};

function fmtDate(iso) {
  if (!iso) return "Date unknown";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Date unknown";
  const days = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "1 day ago";
  if (days < 30) return `${days} days ago`;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function jobCard(job) {
  const badgeClass = ["full-time", "part-time", "contract", "internship"].includes(job.job_type)
    ? job.job_type
    : "unknown";
  const sponsoredClass = job.sponsored ? " sponsored" : "";
  const snippet = job.description_snippet
    ? `<p class="job-snippet">${escapeHtml(job.description_snippet)}</p>`
    : "";
  const salary = job.salary ? `<span>💰 ${escapeHtml(job.salary)}</span>` : "";

  return `
    <article class="job-card${sponsoredClass}">
      <div class="job-top">
        <div>
          <h3 class="job-title"><a href="${escapeAttr(job.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(job.title)}</a></h3>
          <p class="job-company">${escapeHtml(job.company)}</p>
        </div>
        <div class="badges">
          ${job.sponsored ? '<span class="badge sponsored-tag">Sponsored</span>' : ""}
          <span class="badge ${badgeClass}">${badgeClass.replace("-", " ")}</span>
        </div>
      </div>
      <div class="job-meta">
        <span>📍 ${escapeHtml(job.location || (job.remote ? "Remote" : "Not specified"))}</span>
        <span>🕒 ${fmtDate(job.posted_at)}</span>
        <span>🔗 ${escapeHtml(job.source)}</span>
        ${salary}
      </div>
      ${snippet}
    </article>
  `;
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function escapeAttr(str) {
  return escapeHtml(str);
}

async function search(page = 1) {
  state.page = page;
  els.results.innerHTML = '<p class="empty">Loading jobs…</p>';
  els.pagination.innerHTML = "";

  const params = new URLSearchParams({
    page: String(page),
    page_size: String(state.pageSize),
    sort: els.sortBy.value,
  });
  if (els.keyword.value.trim()) params.set("keyword", els.keyword.value.trim());
  if (els.jobType.value !== "all") params.set("job_type", els.jobType.value);
  if (els.remoteOnly.checked) params.set("remote_only", "true");

  try {
    const res = await fetch(`${API_BASE}/api/jobs?${params.toString()}`);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    const data = await res.json();
    render(data);
  } catch (err) {
    els.results.innerHTML = `<p class="error">Couldn't load jobs right now (${escapeHtml(err.message)}). Please try again shortly.</p>`;
    els.meta.textContent = "";
  }
}

function render(data) {
  if (!data.jobs.length) {
    els.results.innerHTML = '<p class="empty">No jobs match those filters yet. Try a broader keyword.</p>';
  } else {
    els.results.innerHTML = data.jobs.map(jobCard).join("");
  }

  els.meta.textContent = `${data.total} job${data.total === 1 ? "" : "s"} found · cache refreshed ${Math.round(data.cache_age_seconds)}s ago`;

  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
  els.pagination.innerHTML = `
    <button id="prevPage" ${data.page <= 1 ? "disabled" : ""}>← Prev</button>
    <span>Page ${data.page} of ${totalPages}</span>
    <button id="nextPage" ${data.page >= totalPages ? "disabled" : ""}>Next →</button>
  `;
  document.getElementById("prevPage")?.addEventListener("click", () => search(state.page - 1));
  document.getElementById("nextPage")?.addEventListener("click", () => search(state.page + 1));
}

els.searchBtn.addEventListener("click", () => search(1));
els.keyword.addEventListener("keydown", (e) => {
  if (e.key === "Enter") search(1);
});
els.jobType.addEventListener("change", () => search(1));
els.sortBy.addEventListener("change", () => search(1));
els.remoteOnly.addEventListener("change", () => search(1));

function showSignedIn(email) {
  els.signedInEmail.textContent = email;
  els.signedInView.hidden = false;
  els.signedOutView.hidden = true;
}

function showSignedOut() {
  els.signedInView.hidden = true;
  els.signedOutView.hidden = false;
}

async function refreshAuthState() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`);
    if (res.ok) {
      const data = await res.json();
      showSignedIn(data.email);
      return;
    }
  } catch {
    // network error — leave as signed-out rather than guessing
  }
  showSignedOut();
}

els.signInForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  els.authStatus.textContent = "Sending…";
  try {
    const res = await fetch(`${API_BASE}/api/auth/request-link`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: els.signInEmail.value }),
    });
    if (!res.ok) throw new Error("failed");
    els.authStatus.textContent = "Check your email for a sign-in link.";
    els.signInForm.reset();
  } catch {
    els.authStatus.textContent = "Something went wrong, please try again.";
  }
});

els.logoutBtn.addEventListener("click", async () => {
  try {
    await fetch(`${API_BASE}/api/auth/logout`, { method: "POST" });
  } catch {
    // best-effort — show signed-out either way
  }
  els.authStatus.textContent = "";
  showSignedOut();
});

function handleAuthRedirect() {
  const params = new URLSearchParams(window.location.search);
  const authResult = params.get("auth");
  if (!authResult) return;
  els.authStatus.textContent =
    authResult === "success" ? "Signed in!" : "That sign-in link is invalid or expired — request a new one.";
  params.delete("auth");
  const newUrl = window.location.pathname + (params.toString() ? `?${params}` : "");
  window.history.replaceState({}, "", newUrl);
}

handleAuthRedirect();
refreshAuthState();
search(1);
