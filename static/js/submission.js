/**
 * Submission page logic & sample idea auto-fillers
 */
const SAMPLE_IDEAS = {
    legal: {
        title: "LexiDraft AI — Freelancer Contract Copilot",
        industry: "LegalTech / Productivity SaaS",
        raw_description: "An AI assistant built for freelance software developers and boutique agencies that analyzes client Master Service Agreements (MSAs), flags hidden indemnification clauses and payment terms, and drafts polite counter-proposal emails to protect payment terms without hiring an attorney.",
        target_audience: "Freelance developers, independent designers, boutique digital agencies, and solopreneurs",
        problem_statement: "Independent knowledge workers frequently sign disadvantageous contracts with vague scope and one-sided indemnification clauses because hiring a contract lawyer costs $400/hr.",
        proposed_solution: "An instant document redlining copilot that translates legalese into plain English risk scores, alerts on hidden liabilities, and auto-generates negotiated clause edits.",
        revenue_model: "Freemium + $29/mo Pro or $199/yr Unlimited"
    },
    climate: {
        title: "CarbonTrace — Automated Scope 3 Carbon Accounting",
        industry: "ClimateTech / Enterprise ESG",
        raw_description: "A lightweight B2B carbon accounting software for mid-market manufacturing suppliers that automatically ingests utility bills, ERP supplier receipts, and logistics manifests to generate certified ESG emissions reports for enterprise enterprise buyers.",
        target_audience: "Mid-market manufacturers, logistics fleets, Tier-1 supply chain contractors",
        problem_statement: "Mid-sized suppliers are being pressured by enterprise customers (Apple, Walmart) to disclose Scope 3 emissions under CSRD/SEC rules, but lack the resources for $50k consulting audits.",
        proposed_solution: "Plug-and-play carbon telemetry platform that connects directly to QuickBooks, SAP, and fleet fuel telemetry to produce audit-ready GHG Protocol carbon footprints within 48 hours.",
        revenue_model: "Tiered B2B SaaS ($299/mo Starter, $899/mo Growth)"
    },
    health: {
        title: "ScribePulse — Ambient Clinical AI Scribe",
        industry: "Digital Health / MedTech",
        raw_description: "An ambient AI scribe for independent outpatient clinics that listens to doctor-patient consultations and automatically writes structured SOAP clinical notes and accurate ICD-10 medical billing codes directly into electronic health records (EHR).",
        target_audience: "Private outpatient physicians, pediatric clinics, and wellness practitioners",
        problem_statement: "Physicians spend over 2 hours every evening completing repetitive EHR clinical documentation, contributing to burnout and delayed billing reimbursements.",
        proposed_solution: "Zero-click ambient voice scribe that structures compliant SOAP notes and billing codes in real-time, requiring only a 30-second final physician sign-off.",
        revenue_model: "Per-Provider Subscription ($149/physician/month)"
    }
};

function fillSampleIdea(type) {
    const sample = SAMPLE_IDEAS[type];
    if (!sample) return;

    document.getElementById("titleInput").value = sample.title;
    document.getElementById("industrySelect").value = sample.industry;
    document.getElementById("descInput").value = sample.raw_description;
    
    const targetAud = document.getElementById("targetAudienceInput");
    if (targetAud) targetAud.value = sample.target_audience;

    const probInput = document.getElementById("problemInput");
    if (probInput) probInput.value = sample.problem_statement;

    const solInput = document.getElementById("solutionInput");
    if (solInput) solInput.value = sample.proposed_solution;

    const revInput = document.getElementById("revenueInput");
    if (revInput) revInput.value = sample.revenue_model;

    // Trigger visual highlight
    const formCard = document.querySelector(".card-custom");
    if (formCard) {
        formCard.classList.add("border-primary");
        setTimeout(() => formCard.classList.remove("border-primary"), 800);
    }
}

// =========================================================================
// Real-time 8-Agent Pipeline Orchestration Tracking
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ideaSubmissionForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        const asyncChecked = document.getElementById("asyncCheck")?.checked;
        if (!asyncChecked) {
            // Normal full page post
            return;
        }

        e.preventDefault();

        const title = document.getElementById("titleInput")?.value.trim();
        const desc = document.getElementById("descInput")?.value.trim();
        if (!title || !desc) {
            alert("Please provide both an Idea Title and Description.");
            return;
        }

        // Show Bootstrap progress modal
        const modalEl = document.getElementById("validationProgressModal");
        const modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: false });
        modal.show();

        const submitBtn = document.getElementById("submitBtn");
        if (submitBtn) submitBtn.disabled = true;

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const resData = await response.json();
            const ideaId = resData.idea_id;
            const redirectUrl = resData.redirect_url || `/idea/${ideaId}/report`;

            if (ideaId) {
                trackAgentExecution(ideaId, redirectUrl);
            } else {
                window.location.href = redirectUrl;
            }
        } catch (err) {
            console.error("Submission failed, submitting normally:", err);
            form.submit();
        }
    });
});

function trackAgentExecution(ideaId, redirectUrl) {
    const overallBar = document.getElementById("overallProgressBar");
    const overallPct = document.getElementById("overallPercentText");
    const overallStatus = document.getElementById("overallStatusText");
    const completionBanner = document.getElementById("completionBanner");
    const viewReportBtn = document.getElementById("viewReportBtn");
    const headerSpinner = document.getElementById("headerSpinner");

    const agentKeys = [
        "extractor",
        "market",
        "competitors",
        "swot_risk",
        "mvp",
        "gtm",
        "advisor",
        "report"
    ];

    let pollInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/idea/${ideaId}/status`);
            if (!res.ok) return;

            const data = await res.json();
            const prog = data.progress || {};
            const percent = prog.percent || 10;
            const agentsData = prog.agents || {};

            // Update overall bar
            if (overallBar) overallBar.style.width = `${percent}%`;
            if (overallPct) overallPct.textContent = `${percent}%`;
            if (overallStatus && prog.message) overallStatus.textContent = prog.message;

            // Update individual agent badges based on genuine execution state
            agentKeys.forEach(k => {
                const badge = document.getElementById(`agent-badge-${k}`);
                const row = document.getElementById(`agent-row-${k}`);
                const agentInfo = agentsData[k] || {};
                const st = agentInfo.status || "pending";

                if (badge) {
                    if (st === "completed") {
                        badge.className = "badge bg-success-subtle text-success border border-success-subtle";
                        badge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Completed';
                        if (row) row.classList.remove("bg-light");
                    } else if (st === "processing") {
                        badge.className = "badge bg-primary text-white";
                        badge.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processing...';
                        if (row) row.classList.add("bg-primary-subtle", "bg-opacity-25");
                    } else if (st === "failed") {
                        badge.className = "badge bg-danger-subtle text-danger border border-danger-subtle";
                        badge.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i> Failed';
                    } else {
                        badge.className = "badge bg-secondary-subtle text-muted";
                        badge.textContent = "Pending";
                    }
                }
            });

            // Pipeline finished
            if (data.status === "completed" || prog.status === "completed") {
                clearInterval(pollInterval);
                if (overallBar) {
                    overallBar.style.width = "100%";
                    overallBar.classList.remove("progress-bar-animated");
                    overallBar.classList.add("bg-success");
                }
                if (overallPct) overallPct.textContent = "100%";
                if (overallStatus) overallStatus.textContent = "Multi-Agent Validation Finalized!";
                if (headerSpinner) headerSpinner.classList.add("d-none");

                // Ensure all badges marked completed
                agentKeys.forEach(k => {
                    const badge = document.getElementById(`agent-badge-${k}`);
                    if (badge && !badge.innerHTML.includes("Failed")) {
                        badge.className = "badge bg-success-subtle text-success border border-success-subtle";
                        badge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Completed';
                    }
                });

                if (completionBanner) completionBanner.classList.remove("d-none");
                if (viewReportBtn) viewReportBtn.href = redirectUrl;

                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1600);
            } else if (data.status === "failed" || prog.status === "failed") {
                clearInterval(pollInterval);
                if (overallBar) overallBar.classList.add("bg-danger");
                if (overallStatus) overallStatus.textContent = "Validation halted with an error.";
                if (headerSpinner) headerSpinner.classList.add("d-none");
            }
        } catch (e) {
            console.error("Agent progress tracker error:", e);
        }
    }, 1200);
}
