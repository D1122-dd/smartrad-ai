/**
 * performance.js
 * ──────────────
 * Fetches analytics data from the API and renders all Chart.js charts
 * on the Performance page.
 */

'use strict';

// Chart.js default font
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#64748b';

const PALETTE = {
    blue: '#2563eb',
    lightBlue: '#93c5fd',
    green: '#22c55e',
    amber: '#f59e0b',
    purple: '#7c3aed',
    red: '#ef4444',
    gray: '#e2e8f0',
};

// ── Chart instances (kept for potential re-render) ─────────────────────────────
let _chartDuration = null;
let _chartModality = null;
let _chartRooms = null;
let _chartAccuracy = null;


// ── KPI Tiles ──────────────────────────────────────────────────────────────────



// ── Line Chart: Avg Duration Trend ─────────────────────────────────────────────

function renderDurationChart(dailyTrend) {
    const rows = [...(dailyTrend || [])].reverse();   // oldest → newest
    const labels = rows.map(r => r.scan_date);
    const actual = rows.map(r => r.avg_actual);

    const ctx = document.getElementById('chart-duration');
    if (!ctx) return;
    if (_chartDuration) _chartDuration.destroy();

    _chartDuration = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Scan Duration',
                    data: actual,
                    borderColor: PALETTE.green,
                    backgroundColor: 'rgba(34,197,94,0.08)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: PALETTE.green,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { usePointStyle: true, padding: 16 } },
                tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y} min` } },
            },
            scales: {
                x: { grid: { color: PALETTE.gray } },
                y: {
                    grid: { color: PALETTE.gray }, beginAtZero: true,
                    ticks: { callback: v => v + ' min' }
                },
            },
        },
    });
}


// ── Donut Chart: Modality Split ─────────────────────────────────────────────────

function renderModalityChart(modalitySplit) {
    const labels = (modalitySplit || []).map(m => m.modality_type);
    const values = (modalitySplit || []).map(m => m.scans);

    const ctx = document.getElementById('chart-modality');
    if (!ctx) return;
    if (_chartModality) _chartModality.destroy();

    _chartModality = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: [PALETTE.blue, PALETTE.purple],
                borderWidth: 0,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } },
                tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} scans` } },
            },
        },
    });
}


// ── Bar Chart: Room Utilization ────────────────────────────────────────────────

function renderRoomsChart(roomUtilization) {
    const labels = (roomUtilization || []).map(r => r.room_name.split(' - ')[0]);
    const values = (roomUtilization || []).map(r => r.scans);

    const ctx = document.getElementById('chart-rooms');
    if (!ctx) return;
    if (_chartRooms) _chartRooms.destroy();

    _chartRooms = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Scans Completed',
                data: values,
                backgroundColor: [PALETTE.blue, PALETTE.purple, PALETTE.green, PALETTE.amber],
                borderRadius: 8,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} scans` } },
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    grid: { color: PALETTE.gray }, beginAtZero: true,
                    ticks: { stepSize: 1 }
                },
            },
        },
    });
}


// ── Accuracy Ring ──────────────────────────────────────────────────────────────



// ── History Table ──────────────────────────────────────────────────────────────



// ── Boot ───────────────────────────────────────────────────────────────────────

async function loadAnalytics() {
    try {
        const res = await Auth.fetch('/api/analytics/summary');
        const sumData = await res.json();

        if (sumData.success) {
            const d = sumData.data;
            renderDurationChart(d.daily_trend || []);
            renderModalityChart(d.modality_split || []);
            renderRoomsChart(d.room_utilization || []);
        }

    } catch (e) {
        console.error('Analytics load error:', e);
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
}

document.addEventListener('DOMContentLoaded', loadAnalytics);
