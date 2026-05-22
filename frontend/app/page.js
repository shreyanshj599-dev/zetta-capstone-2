"use client";

import { useEffect, useMemo, useState } from "react";

const industries = ["all", "saas", "fintech", "healthcare", "ecommerce", "hardware", "consulting", "other"];

function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function statusClass(status) {
  if (status === "succeeded") return "status success";
  if (status === "failed") return "status danger";
  if (status === "running") return "status active";
  return "status";
}

function scoreLabel(score) {
  if (score === null || score === undefined) return "No score";
  if (score >= 80) return "Strong fit";
  if (score >= 55) return "Potential fit";
  return "Low fit";
}

function jobLabel(job) {
  if (!job) return "idle";
  if (job.status === "succeeded" && job.company && !job.started_at) return "cache hit";
  return job.status;
}

export default function Home() {
  const [url, setUrl] = useState("https://anthropic.com");
  const [batchUrls, setBatchUrls] = useState(
    "https://stripe.com\nhttps://vercel.com\nhttps://linear.app\nhttps://supabase.com"
  );
  const [job, setJob] = useState(null);
  const [batchJobs, setBatchJobs] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [industry, setIndustry] = useState("all");
  const [loading, setLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [error, setError] = useState("");

  const currentCompany = job?.company || null;
  const jobIsActive = job && (job.status === "queued" || job.status === "running");
  const currentJobLabel = jobLabel(job);

  const filteredCompanies = useMemo(() => companies, [companies]);

  async function requestJson(path, options) {
    const response = await fetch(path, options);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
        : data.detail || data.error || "Request failed";
      throw new Error(detail);
    }

    return data;
  }

  async function loadCompanies(nextIndustry = industry) {
    setListLoading(true);
    try {
      const query = nextIndustry === "all" ? "" : `?industry=${encodeURIComponent(nextIndustry)}`;
      const data = await requestJson(`/api/companies${query}`);
      setCompanies(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setListLoading(false);
    }
  }

  async function submitEnrichment(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const nextJob = await requestJson("/api/enrich", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url })
      });
      setJob(nextJob);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitBatch(event) {
    event.preventDefault();
    setError("");
    setBatchLoading(true);

    const urls = batchUrls
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);

    try {
      const jobs = await Promise.all(
        urls.map((item) =>
          requestJson("/api/enrich", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ url: item })
          })
        )
      );
      setBatchJobs(jobs);
    } catch (err) {
      setError(err.message);
    } finally {
      setBatchLoading(false);
    }
  }

  useEffect(() => {
    loadCompanies("all");
  }, []);

  useEffect(() => {
    if (!jobIsActive) {
      if (job?.status === "succeeded") loadCompanies(industry);
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const nextJob = await requestJson(`/api/enrich/${job.id}`);
        setJob(nextJob);
      } catch (err) {
        setError(err.message);
        window.clearInterval(timer);
      }
    }, 2500);

    return () => window.clearInterval(timer);
  }, [job?.id, job?.status, industry]);

  useEffect(() => {
    const activeJobs = batchJobs.filter((item) => item.status === "queued" || item.status === "running");
    if (!activeJobs.length) {
      if (batchJobs.some((item) => item.status === "succeeded")) loadCompanies(industry);
      return;
    }

    const timer = window.setInterval(async () => {
      const nextJobs = await Promise.all(
        batchJobs.map((item) => {
          if (item.status !== "queued" && item.status !== "running") return item;
          return requestJson(`/api/enrich/${item.id}`).catch((err) => ({
            ...item,
            status: "failed",
            error: err.message
          }));
        })
      );
      setBatchJobs(nextJobs);
    }, 2500);

    return () => window.clearInterval(timer);
  }, [batchJobs, industry]);

  return (
    <main className="shell">
      <section className="toolbar">
        <div>
          <p className="eyebrow">Zetta Capstone</p>
          <h1>Lead Enrichment</h1>
        </div>
        <div className="metrics">
          <div>
            <span>Cached companies</span>
            <strong>{companies.length}</strong>
          </div>
          <div>
            <span>Current job</span>
            <strong>{currentJobLabel}</strong>
          </div>
        </div>
      </section>

      <section className="workspace">
        <form className="enrich-form" onSubmit={submitEnrichment}>
          <label htmlFor="url">Company URL</label>
          <div className="submit-row">
            <input
              id="url"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://example.com"
              type="url"
              required
            />
            <button type="submit" disabled={loading || jobIsActive}>
              {jobIsActive ? "Processing" : "Enrich"}
            </button>
          </div>
          {error ? <p className="form-error">{error}</p> : null}
        </form>

        <div className="result-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Job</p>
              <h2>{job?.domain || "No active job"}</h2>
            </div>
            <span className={statusClass(job?.status)}>{currentJobLabel}</span>
          </div>

          {job ? (
            <div className="timeline">
              <div>
                <span>Created</span>
                <strong>{formatDate(job.created_at)}</strong>
              </div>
              <div>
                <span>Started</span>
                <strong>{formatDate(job.started_at)}</strong>
              </div>
              <div>
                <span>Finished</span>
                <strong>{formatDate(job.finished_at)}</strong>
              </div>
            </div>
          ) : (
            <p className="muted">Submit a domain to start the enrichment pipeline.</p>
          )}

          {job?.error ? <p className="form-error">{job.error}</p> : null}

          {currentCompany ? <CompanyDetail company={currentCompany} /> : null}
        </div>
      </section>

      <section className="parallel-section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Parallel Test</p>
            <h2>Submit Multiple URLs</h2>
          </div>
          <span className="status active">threads x 4</span>
        </div>

        <form className="batch-form" onSubmit={submitBatch}>
          <label htmlFor="batchUrls">URLs</label>
          <textarea
            id="batchUrls"
            value={batchUrls}
            onChange={(event) => setBatchUrls(event.target.value)}
            rows={4}
            spellCheck="false"
          />
          <div className="action-row">
            <button type="button" className="secondary" onClick={() => setBatchJobs([])}>
              Clear jobs
            </button>
            <button type="submit" disabled={batchLoading}>
              {batchLoading ? "Submitting" : "Run parallel test"}
            </button>
          </div>
        </form>

        <div className="job-grid">
          {batchJobs.map((item) => (
            <BatchJobCard key={item.id} job={item} />
          ))}
          {!batchJobs.length ? (
            <p className="muted empty">Submit multiple uncached URLs to see concurrent queued/running jobs.</p>
          ) : null}
        </div>
      </section>

      <section className="companies-section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Companies</p>
            <h2>Enriched Accounts</h2>
          </div>
          <div className="filter-row">
            <select
              value={industry}
              onChange={(event) => {
                setIndustry(event.target.value);
                loadCompanies(event.target.value);
              }}
            >
              {industries.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <button type="button" className="secondary" onClick={() => loadCompanies(industry)}>
              {listLoading ? "Refreshing" : "Refresh"}
            </button>
          </div>
        </div>

        <div className="company-grid">
          {filteredCompanies.map((company) => (
            <CompanyCard key={company.id} company={company} />
          ))}
          {!filteredCompanies.length && !listLoading ? (
            <p className="muted empty">No companies found.</p>
          ) : null}
        </div>
      </section>
    </main>
  );
}

function BatchJobCard({ job }) {
  const label = jobLabel(job);
  return (
    <article className="job-card">
      <div className="card-top">
        <div>
          <h3>{job.domain}</h3>
          <p>{job.id}</p>
        </div>
        <span className={statusClass(job.status)}>{label}</span>
      </div>
      <div className="job-times">
        <span>Started: {formatDate(job.started_at)}</span>
        <span>Finished: {formatDate(job.finished_at)}</span>
      </div>
      {job.company ? (
        <p className="job-company">{job.company.name || job.company.domain}</p>
      ) : null}
      {job.error ? <p className="form-error">{job.error}</p> : null}
    </article>
  );
}

function CompanyDetail({ company }) {
  const hiring = company.hiring_signals || {};

  return (
    <div className="company-detail">
      <div className="score-band">
        <div>
          <span>ICP score</span>
          <strong>{company.icp_fit_score ?? "--"}</strong>
        </div>
        <p>{scoreLabel(company.icp_fit_score)}</p>
      </div>
      <dl>
        <div>
          <dt>Name</dt>
          <dd>{company.name || company.domain}</dd>
        </div>
        <div>
          <dt>Industry</dt>
          <dd>{company.industry || "Unknown"}</dd>
        </div>
        <div>
          <dt>Size</dt>
          <dd>{company.size_bucket || "Unknown"}</dd>
        </div>
        <div>
          <dt>HQ</dt>
          <dd>{company.hq_country || "Unknown"}</dd>
        </div>
      </dl>

      <div className="tags">
        {(company.tech_stack || []).map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>

      <div className="hiring">
        <strong>{hiring.is_hiring ? "Hiring" : "No hiring signal"}</strong>
        <span>{hiring.open_role_count ?? 0} open roles</span>
      </div>
    </div>
  );
}

function CompanyCard({ company }) {
  return (
    <article className="company-card">
      <div className="card-top">
        <div>
          <h3>{company.name || company.domain}</h3>
          <p>{company.domain}</p>
        </div>
        <strong>{company.icp_fit_score ?? "--"}</strong>
      </div>
      <div className="card-meta">
        <span>{company.industry || "unknown"}</span>
        <span>{company.size_bucket || "unknown"}</span>
        <span>{company.hq_country || "unknown"}</span>
      </div>
      <div className="tags compact">
        {(company.tech_stack || []).slice(0, 5).map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </article>
  );
}
