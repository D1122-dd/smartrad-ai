/**
 * history.js
 * ──────────
 * Fetches and renders the scan history log.
 */

'use strict';

function renderHistoryTable(records) {
    const tbody = document.getElementById('history-tbody');
    if (!tbody) return;

    if (!records.length) {
        tbody.innerHTML = `<tr><td colspan="10" class="queue-empty">
            <i class="fas fa-inbox"></i><br>No completed scans yet.
        </td></tr>`;
        return;
    }

    tbody.innerHTML = records.map(r => {
        const urgBadge = r.is_urgent
            ? `<span class="urg-badge urg-high">Urgent</span>`
            : `<span class="urg-badge urg-low">Normal</span>`;
        const ts = r.completed_at ? r.completed_at.replace('T', ' ').substring(0, 16) : '–';

        return `
        <tr class="queue-row">
            <td><div class="qp-name">${escHtml(r.patient_name)}</div></td>
            <td>${escHtml(r.exam_type)}</td>
            <td><span class="modality-badge mod-${r.modality_type.toLowerCase()}">${r.modality_type}</span></td>
            <td>${escHtml(r.room_name.split(' - ')[0])}</td>
            <td>${r.actual_duration} min</td>
            <td>${urgBadge}</td>
            <td style="color:#94a3b8;font-size:0.8rem;">${ts}</td>
            <td>
                <button class="action-btn delete-btn" onclick="deleteHistoryRecord(${r.id})" title="Delete record">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </td>
        </tr>`;
    }).join('');
}

async function deleteHistoryRecord(id) {
    if (!confirm('Delete this history record?')) return;
    try {
        const res = await Auth.fetch(`/api/analytics/history/${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (result.success) {
            loadHistory();
        }
    } catch (e) { console.error('Delete error:', e); }
}

async function clearAllHistory() {
    if (!confirm('Are you sure you want to CLEAR ALL scan history? This cannot be undone.')) return;
    try {
        const res = await Auth.fetch('/api/analytics/history/clear', { method: 'DELETE' });
        const result = await res.json();
        if (result.success) {
            loadHistory();
        }
    } catch (e) { console.error('Clear history error:', e); }
}

async function loadHistory() {
    try {
        const res = await Auth.fetch('/api/analytics/history');
        const data = await res.json();
        if (data.success) {
            renderHistoryTable(data.history || []);
        }
    } catch (e) {
        console.error('History load error:', e);
    }
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
}

document.addEventListener('DOMContentLoaded', loadHistory);
