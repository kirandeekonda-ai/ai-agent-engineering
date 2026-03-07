/* ══════════════════════════════════════════════
   SolidWorks Change Impact Analyzer v2 — App Logic
   Visual annotations with side-by-side viewer
   ══════════════════════════════════════════════ */

const API_BASE = '';

// ── Theme Toggle ──
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const sun = document.getElementById('theme-icon-sun');
    const moon = document.getElementById('theme-icon-moon');
    if (sun && moon) {
        // Sun icon shows in dark mode (click to go light), moon shows in light mode (click to go dark)
        sun.style.display = theme === 'dark' ? 'block' : 'none';
        moon.style.display = theme === 'light' ? 'block' : 'none';
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('cia-theme', next);
}

// Apply saved theme immediately (before DOM content loaded)
applyTheme(localStorage.getItem('cia-theme') || 'light');

// Store report data globally for tab switching
let currentReport = null;

// Track zoom levels per file panel
const zoomLevels = {};
const ZOOM_MIN = 0.3;
const ZOOM_MAX = 3.0;
const ZOOM_STEP = 0.2;

// ── Page Load ──
document.addEventListener('DOMContentLoaded', () => {
    setupDragDrop();
    setupFileInput();
    loadDocuments();
});

// ── File Upload ──
function setupDragDrop() {
    const dropZone = document.getElementById('drop-zone');
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('drag-over'); });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
        if (files.length > 0) uploadFiles(files);
    });
    dropZone.addEventListener('click', () => document.getElementById('file-input').click());
}

function setupFileInput() {
    document.getElementById('file-input').addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) uploadFiles(files);
    });
}

async function uploadFiles(files) {
    const progressDiv = document.getElementById('upload-progress');
    progressDiv.classList.remove('hidden');
    progressDiv.innerHTML = files.map(f =>
        `<div class="progress-item"><span class="filename">${f.name}</span><span class="status status-loading">Processing...</span></div>`
    ).join('');

    showLoading('Uploading and analyzing PDFs with AI...');
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
        const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
        const data = await res.json();
        progressDiv.innerHTML = data.results.map(r =>
            `<div class="progress-item"><span class="filename">${r.file}</span>${r.error
                ? `<span class="status status-error">Error: ${r.error}</span>`
                : `<span class="status status-success">${r.dimensions_found} dims, ${r.tables_found} tables</span>`
            }</div>`
        ).join('');
        loadDocuments();
    } catch (err) {
        progressDiv.innerHTML = `<div class="progress-item"><span class="filename">Upload failed</span><span class="status status-error">${err.message}</span></div>`;
    }
    hideLoading();
}

// ── Documents ──
async function loadDocuments() {
    try {
        const res = await fetch(`${API_BASE}/documents`);
        const data = await res.json();
        document.getElementById('doc-count').textContent = `${data.total_documents} Documents`;

        const grid = document.getElementById('documents-list');
        if (data.documents.length === 0) {
            grid.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:32px;">No documents processed yet.</p>';
            return;
        }
        grid.innerHTML = data.documents.map(doc => `
            <div class="doc-card" id="doc-${doc.file.replace(/\./g, '-')}">
                <button class="doc-delete-btn" onclick="deleteDocument('${doc.file}')" title="Delete ${doc.file}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path>
                    </svg>
                </button>
                <div class="doc-name" title="${doc.file}">${doc.file}</div>
                <div class="doc-part">${doc.title_block?.part_name || 'N/A'} — ${doc.title_block?.part_number || ''} Rev ${doc.title_block?.revision || ''}</div>
                <div class="doc-stats">
                    <div class="doc-stat"><span class="num">${doc.dimensions_found}</span> dims</div>
                    <div class="doc-stat"><span class="num">${doc.tables_found}</span> tables</div>
                    <div class="doc-stat"><span class="num">${doc.notes_found}</span> notes</div>
                </div>
            </div>
        `).join('');
    } catch (err) { console.error('Failed to load documents:', err); }
}

// ── Custom Confirm Modal ──
function showConfirmModal(message) {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirm-modal');
        const msgEl = document.getElementById('confirm-message');
        const cancelBtn = document.getElementById('confirm-cancel-btn');
        const deleteBtn = document.getElementById('confirm-delete-btn');

        msgEl.textContent = message;
        modal.classList.remove('hidden');

        const cleanup = () => {
            modal.classList.add('hidden');
            cancelBtn.removeEventListener('click', onCancel);
            deleteBtn.removeEventListener('click', onDelete);
        };

        const onCancel = () => { cleanup(); resolve(false); };
        const onDelete = () => { cleanup(); resolve(true); };

        cancelBtn.addEventListener('click', onCancel);
        deleteBtn.addEventListener('click', onDelete);
    });
}

async function deleteAllDocuments() {
    const confirmed = await showConfirmModal('Are you sure you want to delete all processed documents? This action cannot be undone.');
    if (!confirmed) return;

    showLoading('Deleting documents...');
    try {
        const res = await fetch(`${API_BASE}/documents`, { method: 'DELETE' });
        const data = await res.json();

        // Hide the report section if it's currently showing
        document.getElementById('report-section').classList.add('hidden');
        currentReport = null;

        // Reload the empty documents list
        loadDocuments();
    } catch (err) {
        alert('Failed to delete documents: ' + err.message);
    }
    hideLoading();
}

async function deleteDocument(filename) {
    const confirmed = await showConfirmModal(`Are you sure you want to delete ${filename}?`);
    if (!confirmed) return;

    try {
        const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });

        if (!res.ok) {
            throw new Error(`Server returned ${res.status}`);
        }

        // Remove the card from UI immediately for snappy feel
        const cardId = `doc-${filename.replace(/\./g, '-')}`;
        const cardElem = document.getElementById(cardId);
        if (cardElem) {
            cardElem.style.display = 'none';
        }

        // If report is showing data from this file, it might become stale. 
        // For simplicity, we just reload the document list in the background
        // and ideally update the total count label.
        loadDocuments();

    } catch (err) {
        console.error('Failed to delete document:', err);
        // Fallback or custom toast could go here instead of alert
        loadDocuments(); // reload to ensure UI is in sync
    }
}

// ── Change Request ──
async function submitChange(event) {
    event.preventDefault();
    const paramName = document.getElementById('param-name').value;
    const oldValue = document.getElementById('old-value').value;
    const newValue = document.getElementById('new-value').value;

    showLoading(`Analyzing impact: ${paramName} ${oldValue} → ${newValue} (generating annotated views)...`);

    const formData = new FormData();
    formData.append('parameter_name', paramName);
    formData.append('old_value', oldValue);
    formData.append('new_value', newValue);

    try {
        const res = await fetch(`${API_BASE}/change-request`, { method: 'POST', body: formData });
        const report = await res.json();
        currentReport = report;
        displayReport(report, oldValue, newValue);
    } catch (err) {
        alert('Error: ' + err.message);
    }
    hideLoading();
}

// ── Color scheme for relevance ──
const RELEVANCE_COLORS = {
    related: { dot: '#22c55e', label: 'Needs Update' },
    maybe: { dot: '#f59e0b', label: 'Review' },
    unrelated: { dot: '#6b7280', label: 'Unrelated' },
};

function confColor(relevance) {
    return (RELEVANCE_COLORS[relevance] || RELEVANCE_COLORS.maybe).dot;
}

// ── Report Display ──
function displayReport(report, oldValue, newValue) {
    const section = document.getElementById('report-section');
    section.classList.remove('hidden');

    document.getElementById('report-subtitle').textContent =
        `${report.change_request.parameter}: ${oldValue} → ${newValue}`;

    // Summary cards — show relevance-based counts
    const annotatedFiles = report.annotated_files || [];
    const totalRelated = annotatedFiles.reduce((s, f) => s + (f.pages || []).reduce((p, pg) => p + (pg.related_count || 0), 0), 0);
    const totalMaybe = annotatedFiles.reduce((s, f) => s + (f.pages || []).reduce((p, pg) => p + (pg.maybe_count || 0), 0), 0);
    const totalUnrelated = annotatedFiles.reduce((s, f) => s + (f.pages || []).reduce((p, pg) => p + (pg.unrelated_count || 0), 0), 0);
    const totalAll = totalRelated + totalMaybe + totalUnrelated;

    const s = report.summary || {};
    document.getElementById('summary-cards').innerHTML = `
        <div class="summary-card files"><div class="big-number">${s.total_files_scanned || 0}</div><div class="label">Files Scanned</div></div>
        <div class="summary-card affected"><div class="big-number">${s.total_files_affected || 0}</div><div class="label">Files Affected</div></div>
        <div class="summary-card confident"><div class="big-number">${totalRelated}</div><div class="label">Need Updating</div></div>
        <div class="summary-card matches"><div class="big-number">${totalMaybe + totalUnrelated}</div><div class="label">Review / Skip</div></div>
    `;

    // Build file tabs — show related count
    const tabsDiv = document.getElementById('file-tabs');
    tabsDiv.innerHTML = annotatedFiles.map((af, idx) => {
        const relCount = af.pages?.reduce((sum, p) => sum + (p.related_count || 0), 0) || 0;
        const totalCount = af.pages?.reduce((sum, p) => sum + (p.total_matches || 0), 0) || 0;
        return `<button class="file-tab ${idx === 0 ? 'active' : ''}" onclick="switchTab(${idx})" data-idx="${idx}">
            ${af.file}
            ${relCount > 0 ? `<span class="tab-count" style="background:rgba(34,197,94,0.15);color:#22c55e">${relCount}</span>` : ''}
        </button>`;
    }).join('');

    // Build viewer panels
    const viewerDiv = document.getElementById('visual-viewer');
    viewerDiv.innerHTML = annotatedFiles.map((af, idx) => {
        return buildViewerPanel(af, idx, oldValue);
    }).join('');

    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function buildViewerPanel(annotatedFile, idx, searchValue) {
    const page = annotatedFile.pages?.[0]; // First page (our test PDFs are single-page)

    // Initialize zoom
    zoomLevels[idx] = 1.0;

    if (!page || page.total_matches === 0) {
        return `<div class="viewer-panel ${idx === 0 ? 'active' : ''}" data-panel="${idx}">
            <div class="pdf-panel"><div class="no-matches">No matches found in this document</div></div>
            <div class="match-panel">
                <div class="match-panel-header"><h3>${annotatedFile.file}</h3><div class="match-count">0 matches</div></div>
                <div class="match-list"></div>
            </div>
        </div>`;
    }

    const matches = page.matches || [];

    // Sort: related first, then maybe, then unrelated
    const sortOrder = { related: 0, maybe: 1, unrelated: 2 };
    const sortedMatches = [...matches].sort((a, b) =>
        (sortOrder[a.relevance] || 1) - (sortOrder[b.relevance] || 1)
    );

    const relCount = matches.filter(m => m.relevance === 'related').length;
    const maybeCount = matches.filter(m => m.relevance === 'maybe').length;
    const unrelCount = matches.filter(m => m.relevance === 'unrelated').length;

    // Build match list items
    const matchItems = sortedMatches.map((m, mi) => {
        const relevance = m.relevance || 'maybe';
        const colors = RELEVANCE_COLORS[relevance] || RELEVANCE_COLORS.maybe;
        const contextHl = highlightValue(m.display_context || m.context || '', searchValue);
        const reason = m.reason || '';
        return `
            <div class="match-item ${relevance === 'unrelated' ? 'match-dimmed' : ''}" data-match="${mi}"
                 onmouseenter="highlightMatch(${idx}, ${mi})"
                 onmouseleave="unhighlightMatch(${idx}, ${mi})">
                <div class="match-dot" style="background:${colors.dot}"></div>
                <div class="match-info">
                    <div class="match-type" style="color:${colors.dot}">${colors.label}</div>
                    <div class="match-line">${contextHl}</div>
                    <div class="match-reason">${reason}</div>
                </div>
            </div>
        `;
    }).join('');

    return `<div class="viewer-panel ${idx === 0 ? 'active' : ''}" data-panel="${idx}">
        <div class="pdf-panel" id="pdf-panel-${idx}">
            <div class="zoom-toolbar">
                <button class="zoom-btn" onclick="zoomOut(${idx})" title="Zoom Out">−</button>
                <span class="zoom-level" id="zoom-level-${idx}">100%</span>
                <button class="zoom-btn" onclick="zoomIn(${idx})" title="Zoom In">+</button>
                <button class="zoom-btn zoom-btn-fit" onclick="zoomFit(${idx})" title="Fit to Width">Fit</button>
            </div>
            <div class="pdf-image-container" id="pdf-container-${idx}" onwheel="handleWheel(event, ${idx})">
                <img id="pdf-img-${idx}" src="data:image/jpeg;base64,${page.image_base64}" alt="Annotated ${annotatedFile.file}" />
            </div>
        </div>
        <div class="match-panel">
            <div class="match-panel-header">
                <h3>${annotatedFile.file}</h3>
                <div class="match-count">
                    <span style="color:#22c55e;font-weight:700">${relCount} need updating</span>
                    ${maybeCount > 0 ? ` · <span style="color:#f59e0b">${maybeCount} review</span>` : ''}
                    ${unrelCount > 0 ? ` · <span style="color:#6b7280">${unrelCount} skipped</span>` : ''}
                </div>
            </div>
            <div class="match-list">${matchItems}</div>
        </div>
    </div>`;
}

function switchTab(idx) {
    // Update tab active state
    document.querySelectorAll('.file-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.file-tab[data-idx="${idx}"]`).classList.add('active');

    // Show corresponding panel
    document.querySelectorAll('.viewer-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`.viewer-panel[data-panel="${idx}"]`).classList.add('active');
}

function highlightMatch(panelIdx, matchIdx) {
    const items = document.querySelectorAll(`.viewer-panel[data-panel="${panelIdx}"] .match-item`);
    items[matchIdx]?.classList.add('highlighted');
}

function unhighlightMatch(panelIdx, matchIdx) {
    const items = document.querySelectorAll(`.viewer-panel[data-panel="${panelIdx}"] .match-item`);
    items[matchIdx]?.classList.remove('highlighted');
}

function highlightValue(text, value) {
    if (!text || !value) return text;
    const escaped = value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return text.replace(new RegExp(`(${escaped})`, 'gi'), '<span class="hl">$1</span>');
}

// ── Zoom Controls ──

function applyZoom(panelIdx) {
    const img = document.getElementById(`pdf-img-${panelIdx}`);
    const label = document.getElementById(`zoom-level-${panelIdx}`);
    const level = zoomLevels[panelIdx] || 1.0;

    if (level === 1.0) {
        img.style.transform = 'none';
        img.style.width = '100%';
    } else {
        img.style.width = `${level * 100}%`;
        img.style.transform = 'none';
    }
    label.textContent = `${Math.round(level * 100)}%`;
}

function zoomIn(panelIdx) {
    zoomLevels[panelIdx] = Math.min(ZOOM_MAX, (zoomLevels[panelIdx] || 1.0) + ZOOM_STEP);
    applyZoom(panelIdx);
}

function zoomOut(panelIdx) {
    zoomLevels[panelIdx] = Math.max(ZOOM_MIN, (zoomLevels[panelIdx] || 1.0) - ZOOM_STEP);
    applyZoom(panelIdx);
}

function zoomFit(panelIdx) {
    zoomLevels[panelIdx] = 1.0;
    applyZoom(panelIdx);
    // Also scroll to top
    const container = document.getElementById(`pdf-container-${panelIdx}`);
    if (container) { container.scrollTop = 0; container.scrollLeft = 0; }
}

function handleWheel(event, panelIdx) {
    if (event.ctrlKey) {
        event.preventDefault();
        if (event.deltaY < 0) zoomIn(panelIdx);
        else zoomOut(panelIdx);
    }
}

// ── Loading ──
function showLoading(text) {
    document.getElementById('loading-text').textContent = text || 'Processing...';
    document.getElementById('loading-overlay').classList.remove('hidden');
}
function hideLoading() { document.getElementById('loading-overlay').classList.add('hidden'); }
