/**
 * dashboard.js
 * ─────────────
 * Phase 4: Live Dashboard polling, room card rendering,
 * patient queue table, and room action controls.
 *
 * Polls:
 *   GET /api/rooms           → room status every 3s
 *   GET /api/rooms/queue     → patient queue every 5s
 *   GET /api/ris/notifications → new-order toasts every 6s
 */

'use strict';

// ── State ──────────────────────────────────────────────────────────────────────
const ROOMS_INTERVAL = 3000;
const QUEUE_INTERVAL = 5000;
const NOTIF_INTERVAL = 6000;

let _roomsTimer = null;
let _queueTimer = null;
let _notifTimer = null;
let _lastNotifIds = new Set();   // deduplicate toast notifications

// ── Colour / Label Helpers ─────────────────────────────────────────────────────

function getStatusMeta(status) {
    const STATUS_META = {
        IDLE: { label: t('dashboard.room_idle'), cls: 'status-idle', icon: 'fa-check-circle', bar: 0 },
        SCANNING: { label: t('queue.status_scanning'), cls: 'status-scanning', icon: 'fa-radiation', bar: null },
        CLEANING: { label: t('dashboard.room_cleaning'), cls: 'status-cleaning', icon: 'fa-broom', bar: 0 },
    };
    return STATUS_META[status] || STATUS_META.IDLE;
}

function urgencyLabel(score) {
    if (score >= 8) return { text: t('queue.urg_high'), cls: 'urg-high' };
    if (score >= 5) return { text: t('queue.urg_medium'), cls: 'urg-medium' };
    return { text: t('queue.urg_low'), cls: 'urg-low' };
}

function priorityBadge(score) {
    if (score >= 7) return `<span class="prio-badge prio-high">${score.toFixed(1)}</span>`;
    if (score >= 4) return `<span class="prio-badge prio-med">${score.toFixed(1)}</span>`;
    return `<span class="prio-badge prio-low">${score.toFixed(1)}</span>`;
}

/**
 * Compute progress % for a scanning room.
 * Uses predicted_end_time and assumes scan started some time ago.
 * We back-calculate start_time = end_time - predicted_duration.
 */
function computeProgress(room) {
    if (room.status !== 'SCANNING' || !room.predicted_end_time) return 0;
    const endMs = new Date(room.predicted_end_time).getTime();
    const durMs = (room.predicted_duration_min || 15) * 60 * 1000;
    const startMs = endMs - durMs;
    const nowMs = Date.now();
    const pct = Math.min(100, Math.max(0, ((nowMs - startMs) / durMs) * 100));
    return Math.round(pct);
}

function minutesLeft(predicted_end_time) {
    if (!predicted_end_time) return '--';
    const diffMs = new Date(predicted_end_time).getTime() - Date.now();
    if (diffMs <= 0) return '0 min';
    return Math.ceil(diffMs / 60000) + ' min';
}

// ── Stat Cards ─────────────────────────────────────────────────────────────────

function updateStatCards(rooms, queue) {
    const waitingCases = queue.filter(p => p.status === 'WAITING');
    const waiting = waitingCases.length;
    const critical = waitingCases.filter(p => p.is_urgent == 1 || p.urgency_score >= 8).length;

    const scanning = rooms.filter(r => r.status === 'SCANNING').length;
    const avgWait = queue.length
        ? Math.round(queue.reduce((s, p) => s + (p.wait_minutes || 0), 0) / queue.length)
        : 0;
    const sysLoad = Math.round((scanning / 4) * 100);

    setText('stat-waiting', waiting);

    const elCrit = document.getElementById('stat-critical');
    const elCritN = document.getElementById('stat-critical-count');
    if (elCrit && elCritN) {
        elCrit.style.display = 'inline-flex';
        elCritN.textContent = critical;
    }
    setText('stat-avg-wait', avgWait + ' min');
    setText('stat-active', scanning + '/4');
    setText('stat-load', sysLoad + '%');
}

// ── Room Cards ─────────────────────────────────────────────────────────────────

function renderRoomCards(rooms) {
    const grid = document.getElementById('rooms-grid');
    if (!grid) return;

    // Remove skeletons if they exist
    const skeletons = grid.querySelectorAll('.room-skeleton');
    skeletons.forEach(s => s.remove());

    rooms.forEach(room => {
        const meta = getStatusMeta(room.status);
        const cardId = `room-card-${room.id}`;
        let card = document.getElementById(cardId);

        if (!card) {
            card = document.createElement('div');
            card.id = cardId;
            card.className = 'room-card';
            grid.appendChild(card);
        }

        // Compute progress for SCANNING
        const pct = (room.status === 'SCANNING') ? computeProgress(room) : 0;

        // Patient info block
        const patientHtml = room.status === 'SCANNING' && room.patient_name
            ? `<div class="room-patient">
                  <div class="rp-name"><i class="fas fa-user-injured"></i> ${escHtml(room.patient_name)}</div>
                  <div class="rp-exam">${escHtml(room.patient_exam || '')}</div>
               </div>`
            : `<div class="room-patient room-patient--idle">
                  <i class="fas fa-bed"></i>
                  <span>${room.status === 'CLEANING' ? t('dashboard.room_cleaning') : t('dashboard.room_idle')}</span>
               </div>`;

        // Action button
        let actionHtml = '';
        if (room.status === 'SCANNING') {
            actionHtml = `<button class="room-action-btn btn-finish" onclick="markFinished(${room.id})">
                              <i class="fas fa-check"></i> ${t('dashboard.btn_finish')}
                          </button>`;
        } else if (room.status === 'CLEANING') {
            actionHtml = `<button class="room-action-btn btn-ready" onclick="markReady(${room.id})">
                              <i class="fas fa-check-double"></i> ${t('dashboard.btn_ready')}
                          </button>`;
        }

        if (room.status !== 'IDLE') {
            actionHtml += `<button class="room-action-btn btn-force" onclick="forceFree(${room.id})" 
                                   style="margin-top:4px; font-size:0.7rem; background:#475569; opacity:0.8;">
                                <i class="fas fa-undo"></i> ${t('dashboard.btn_force_free')}
                            </button>`;
        }

        card.className = `room-card room-card--${room.status.toLowerCase()}`;
        card.innerHTML = `
            <div class="room-card-header">
                <div class="room-icon"><i class="fas fa-x-ray"></i></div>
                <div class="room-info">
                    <div class="room-name">${escHtml(room.name)}</div>
                    <div class="room-modality">${room.modality_type}</div>
                </div>
                <div class="room-status-badge ${meta.cls}">
                    <i class="fas ${meta.icon}"></i> ${meta.label}
                </div>
            </div>

            <div class="room-progress-wrap">
                <div class="room-progress-bar">
                    <div class="room-progress-fill ${room.status === 'SCANNING' ? 'animated' : ''}"
                         style="width: ${pct}%"></div>
                </div>
                <span class="room-progress-pct">${room.status === 'SCANNING' ? pct + '%' : '--'}</span>
            </div>

            ${patientHtml}
            ${actionHtml ? `<div class="room-actions">${actionHtml}</div>` : ''}
        `;
    });
}

// ── Room Actions ───────────────────────────────────────────────────────────────

async function markFinished(roomId) {
    await patchRoomStatus(roomId, 'CLEANING');
}

async function markReady(roomId) {
    await patchRoomStatus(roomId, 'IDLE');
}

async function patchRoomStatus(roomId, newStatus) {
    try {
        const res = await Auth.fetch(`/api/rooms/${roomId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus }),
        });
        const data = await res.json();
        if (data.success) {
            showToast(t('dashboard.toast_update_success'), 'success');
            fetchRooms();   // immediate refresh
        } else {
            showToast(data.message || t('dashboard.toast_update_failed'), 'error');
        }
    } catch (e) {
        showToast(t('common.error'), 'error');
    }
}

// ── Patient Queue Table ─────────────────────────────────────────────────────────

function renderQueue(patients) {
    const tbody = document.getElementById('queue-tbody');
    if (!tbody) return;

    if (!patients.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="queue-empty">
            <i class="fas fa-inbox"></i><br>${t('queue.no_patients')}
        </td></tr>`;
        return;
    }

    tbody.innerHTML = patients.map(p => {
        const urg = urgencyLabel(p.urgency_score);
        const prio = priorityBadge(p.priority_score || 0);
        const statusCls = {
            WAITING: 'qs-waiting',
            ASSIGNED: 'qs-assigned',
            SCANNING: 'qs-scanning',
        }[p.status] || '';

        return `
        <tr class="queue-row">
            <td>
                <div class="qp-name">${escHtml(p.name)}</div>
                <div class="qp-id">P-${String(p.id).padStart(4, '0')}</div>
            </td>
            <td>${escHtml(p.exam_type)}</td>
            <td><span class="modality-badge mod-${p.modality_type.toLowerCase()}">${p.modality_type}</span></td>
            <td><span class="queue-status ${statusCls}">${t('queue.status_' + p.status.toLowerCase())}</span></td>
            <td><span class="urg-badge ${urg.cls}">${urg.text} (${p.urgency_score}/10)</span></td>
            <td>${prio}</td>
        </tr>`;
    }).join('');
}

// ── Notifications ──────────────────────────────────────────────────────────────

async function fetchNotifications() {
    try {
        const res = await Auth.fetch('/api/ris/notifications');
        const data = await res.json();
        if (!data.success) return;

        (data.notifications || []).forEach(n => {
            if (!_lastNotifIds.has(n.id)) {
                _lastNotifIds.add(n.id);

                // Show standard toast
                showToast(
                    `📋 New Order: ${n.patient} — ${n.exam} (${n.modality})`,
                    n.urgent ? 'urgent' : 'info'
                );
            }
        });

        // Update notification dot
        const dot = document.getElementById('notif-dot');
        if (dot) dot.style.display = data.count > 0 ? 'block' : 'none';
        const badge = document.getElementById('notif-count');
        if (badge) badge.textContent = data.count;

    } catch (_) { }
}
// ── API Fetchers ───────────────────────────────────────────────────────────────

let _latestQueue = [];

async function fetchRooms() {
    try {
        const res = await Auth.fetch('/api/rooms');
        const data = await res.json();
        if (!data.success) return;
        renderRoomCards(data.rooms || []);
        updateStatCards(data.rooms || [], _latestQueue);
    } catch (_) { }
}

async function fetchQueue() {
    try {
        const res = await Auth.fetch('/api/rooms/queue');
        const data = await res.json();
        if (!data.success) return;
        _latestQueue = data.queue || [];
        renderQueue(_latestQueue);
    } catch (_) { }
}

// ── Manual Dispatch Button ─────────────────────────────────────────────────────

async function triggerDispatch() {
    const btn = document.getElementById('dispatch-btn');
    if (btn) btn.disabled = true;
    try {
        const res = await Auth.fetch('/api/rooms/dispatch', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`Dispatch cycle: ${data.assignments_made} assignment(s) made`, 'success');
            fetchRooms();
            fetchQueue();
        } else {
            showToast('Dispatch failed: ' + (data.message || ''), 'error');
        }
    } catch (_) {
        showToast('Network error during dispatch', 'error');
    }
    if (btn) btn.disabled = false;
}

// ── Toast System ───────────────────────────────────────────────────────────────

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()">✕</button>`;
    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => toast.classList.add('toast-visible'));

    // Auto-dismiss after 5s
    setTimeout(() => {
        toast.classList.remove('toast-visible');
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

// ── Utilities ──────────────────────────────────────────────────────────────────

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
}

// ── Boot ───────────────────────────────────────────────────────────────────────

async function initDashboard() {
    // Initial fetches (don't wait to feel snappy)
    fetchRooms();
    fetchQueue();
    fetchNotifications();

    // Polling intervals
    _roomsTimer = setInterval(fetchRooms, ROOMS_INTERVAL);
    _queueTimer = setInterval(fetchQueue, QUEUE_INTERVAL);
    _notifTimer = setInterval(fetchNotifications, NOTIF_INTERVAL);
}

async function forceFree(roomId) {
    if (!confirm(`Are you sure you want to FORCE room ${roomId} to IDLE?`)) return;
    try {
        const res = await Auth.fetch(`/api/rooms/${roomId}/force-idle`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`Room ${roomId} forced to IDLE`, 'success');
            fetchRooms();
        } else {
            showToast(data.message || 'Action failed', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

// ── Export ─────────────────────────────────────────────────────────────────────

window.Dashboard = {
    fetchRooms,
    fetchQueue,
    triggerDispatch,
    showToast
};

document.addEventListener('DOMContentLoaded', initDashboard);
