"""
app.py — MobileMart Order Management System
Works both locally (SQLite) and on Render (PostgreSQL) automatically.
"""

from flask import Flask, request, jsonify, send_from_directory
import os

from database import (setup_database, seed_orders, fetch_all_orders,
                      fetch_order_by_id, fetch_all_invoices,
                      update_order_status, POSTGRES)
from pdf_invoice import generate_invoice_bytes
from email_handler import (create_and_send_invoice, process_acceptance,
                            process_rejection, send_to_supplier)

app        = Flask(__name__)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BOSS_EMAIL     = os.environ.get("BOSS_EMAIL",     "ammarkhan172006@gmail.com")
YOUR_EMAIL     = os.environ.get("YOUR_EMAIL",     "ammarwaqar439@gmail.com")
SUPPLIER_EMAIL = os.environ.get("SUPPLIER_EMAIL", "k230878@nu.edu.pk")


# ── Debug route ───────────────────────────────────────────────────────────────
@app.route("/debug")
def debug():
    try:
        orders = fetch_all_orders()
        return jsonify({
            "status":      "ok",
            "db_type":     "PostgreSQL" if POSTGRES else "SQLite",
            "order_count": len(orders),
            "sample":      orders[:2]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MobileMart — Order System</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
* { box-sizing:border-box; margin:0; padding:0; }

body {
  font-family:'Inter',sans-serif;
  background:#060B18;
  color:#F1F5F9;
  min-height:100vh;
}

body::before {
  content:'';
  position:fixed; inset:0;
  background:
    radial-gradient(ellipse 80% 50% at 20% 0%, rgba(99,102,241,0.15) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 100%, rgba(139,92,246,0.1) 0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 50% 50%, rgba(6,182,212,0.05) 0%, transparent 60%);
  pointer-events:none; z-index:0;
}

/* SIDEBAR */
.sidebar {
  position:fixed; left:0; top:0; bottom:0; width:240px;
  background:rgba(15,23,42,0.97);
  border-right:1px solid rgba(99,102,241,0.2);
  display:flex; flex-direction:column;
  z-index:100;
  backdrop-filter:blur(20px);
}
.sidebar-logo { padding:28px 22px 22px; border-bottom:1px solid rgba(255,255,255,0.06); }
.logo-icon {
  width:48px; height:48px; border-radius:14px;
  background:linear-gradient(135deg,#6366F1,#8B5CF6);
  display:flex; align-items:center; justify-content:center;
  font-size:24px; margin-bottom:12px;
  box-shadow:0 8px 24px rgba(99,102,241,0.4);
}
.logo-name { font-size:16px; font-weight:800; color:#F1F5F9; }
.logo-sub  { font-size:10px; color:#475569; margin-top:3px; letter-spacing:0.5px; text-transform:uppercase; }
.sidebar-nav { padding:18px 12px; flex:1; overflow-y:auto; }
.nav-section {
  font-size:9px; font-weight:700; color:#334155;
  text-transform:uppercase; letter-spacing:1.5px;
  padding:0 10px; margin:14px 0 5px;
}
.nav-item {
  display:flex; align-items:center; gap:10px;
  padding:9px 12px; border-radius:10px;
  font-size:13px; font-weight:500; color:#64748B;
  cursor:pointer; margin-bottom:2px; transition:all .15s;
}
.nav-item:hover { background:rgba(99,102,241,0.1); color:#A5B4FC; }
.nav-item.active {
  background:linear-gradient(135deg,rgba(99,102,241,0.2),rgba(139,92,246,0.15));
  color:#A5B4FC; border:1px solid rgba(99,102,241,0.25);
}
.status-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.count-badge { margin-left:auto; font-size:11px; font-weight:800; min-width:20px; text-align:center; }
.sidebar-stats {
  margin:6px 12px 12px;
  background:rgba(99,102,241,0.07);
  border:1px solid rgba(99,102,241,0.15);
  border-radius:12px; padding:14px 16px;
}
.ss-label { font-size:9px; color:#334155; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; font-weight:700; }
.ss-row { display:flex; justify-content:space-between; padding:4px 0; }
.ss-key { font-size:12px; color:#475569; }
.ss-val { font-size:12px; font-weight:800; }
.sidebar-footer {
  padding:12px 20px;
  border-top:1px solid rgba(255,255,255,0.05);
  font-size:11px; color:#334155;
}

/* MAIN */
.main { margin-left:240px; padding:30px 34px; position:relative; z-index:1; }

/* PAGE HEADER */
.page-header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:28px; }
.ph-title {
  font-size:26px; font-weight:900; letter-spacing:-0.5px;
  background:linear-gradient(135deg,#F1F5F9 40%,#A5B4FC);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.ph-sub { font-size:13px; color:#475569; margin-top:4px; }
.ph-right { display:flex; gap:10px; align-items:center; }
.badge-demo {
  background:linear-gradient(135deg,#6366F1,#8B5CF6);
  color:white; font-size:10px; font-weight:800;
  padding:6px 14px; border-radius:20px; letter-spacing:1px;
  box-shadow:0 4px 14px rgba(99,102,241,0.4);
}
.refresh-btn {
  background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
  color:#94A3B8; padding:7px 16px; border-radius:20px;
  font-size:12px; font-weight:600; cursor:pointer;
  font-family:'Inter',sans-serif; transition:all .2s;
}
.refresh-btn:hover { background:rgba(255,255,255,0.1); color:#F1F5F9; }

/* FLOW BAR */
.flow-bar {
  display:flex; align-items:center;
  background:rgba(15,23,42,0.7);
  border:1px solid rgba(255,255,255,0.07);
  border-radius:14px; padding:16px 24px;
  margin-bottom:26px; overflow-x:auto;
  backdrop-filter:blur(10px); gap:0;
}
.flow-step { display:flex; align-items:center; gap:10px; flex-shrink:0; }
.flow-num {
  width:32px; height:32px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-size:13px; font-weight:800; flex-shrink:0;
}
.fn1 { background:rgba(99,102,241,0.2); color:#A5B4FC; border:1px solid rgba(99,102,241,0.4); }
.fn2 { background:rgba(245,158,11,0.2); color:#FCD34D; border:1px solid rgba(245,158,11,0.4); }
.fn3 { background:rgba(16,185,129,0.2); color:#6EE7B7; border:1px solid rgba(16,185,129,0.4); }
.fn4 { background:rgba(6,182,212,0.2);  color:#67E8F9; border:1px solid rgba(6,182,212,0.4); }
.flow-title { font-size:12px; font-weight:700; color:#E2E8F0; }
.flow-desc  { font-size:10px; color:#475569; margin-top:2px; }
.flow-arrow { margin:0 14px; color:#1E293B; font-size:20px; flex-shrink:0; }

/* KPI GRID */
.kpi-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:28px; }
.kpi-card {
  background:rgba(15,23,42,0.8);
  border:1px solid rgba(255,255,255,0.07);
  border-radius:16px; padding:20px 18px;
  position:relative; overflow:hidden;
  transition:all .2s; cursor:default; backdrop-filter:blur(10px);
}
.kpi-card:hover { transform:translateY(-3px); border-color:rgba(255,255,255,0.13); box-shadow:0 16px 40px rgba(0,0,0,0.5); }
.kpi-card::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; border-radius:16px 16px 0 0; }
.kc1::after { background:linear-gradient(90deg,#6366F1,#8B5CF6); }
.kc2::after { background:linear-gradient(90deg,#06B6D4,#6366F1); }
.kc3::after { background:linear-gradient(90deg,#F59E0B,#EC4899); }
.kc4::after { background:linear-gradient(90deg,#10B981,#06B6D4); }
.kc5::after { background:linear-gradient(90deg,#EF4444,#EC4899); }
.kpi-glow { position:absolute; top:-20px; right:-20px; width:80px; height:80px; border-radius:50%; opacity:0.12; filter:blur(24px); }
.kc1 .kpi-glow { background:#6366F1; } .kc2 .kpi-glow { background:#06B6D4; }
.kc3 .kpi-glow { background:#F59E0B; } .kc4 .kpi-glow { background:#10B981; }
.kc5 .kpi-glow { background:#EF4444; }
.kpi-icon { width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:17px; margin-bottom:14px; }
.kc1 .kpi-icon { background:rgba(99,102,241,0.15); }  .kc2 .kpi-icon { background:rgba(6,182,212,0.15); }
.kc3 .kpi-icon { background:rgba(245,158,11,0.15); }  .kc4 .kpi-icon { background:rgba(16,185,129,0.15); }
.kc5 .kpi-icon { background:rgba(239,68,68,0.15); }
.kpi-val { font-size:28px; font-weight:900; line-height:1; letter-spacing:-1px; }
.kc1 .kpi-val{color:#A5B4FC;} .kc2 .kpi-val{color:#67E8F9;} .kc3 .kpi-val{color:#FCD34D;}
.kc4 .kpi-val{color:#6EE7B7;} .kc5 .kpi-val{color:#FCA5A5;}
.kpi-lbl { font-size:11px; color:#475569; margin-top:6px; font-weight:500; }

/* PANEL */
.panel {
  background:rgba(15,23,42,0.8);
  border:1px solid rgba(255,255,255,0.07);
  border-radius:18px; margin-bottom:26px; overflow:hidden; backdrop-filter:blur(10px);
}
.panel-head {
  padding:16px 22px; border-bottom:1px solid rgba(255,255,255,0.06);
  display:flex; align-items:center; justify-content:space-between;
  background:rgba(99,102,241,0.04);
}
.ph-l { display:flex; align-items:center; gap:10px; }
.ph-l h2 { font-size:14px; font-weight:700; color:#E2E8F0; }
.p-count { background:rgba(99,102,241,0.15); color:#A5B4FC; font-size:10px; font-weight:800; padding:2px 9px; border-radius:20px; border:1px solid rgba(99,102,241,0.25); }
.ph-hint { font-size:11px; color:#334155; }
.tbl-wrap { overflow-x:auto; }

/* TABLE */
table { width:100%; border-collapse:collapse; }
thead th { background:rgba(6,11,24,0.9); padding:11px 16px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#334155; text-align:left; white-space:nowrap; }
tbody td { padding:13px 16px; border-bottom:1px solid rgba(255,255,255,0.04); font-size:13px; vertical-align:middle; }
tbody tr:last-child td { border-bottom:none; }
tbody tr:hover td { background:rgba(99,102,241,0.04); }

/* BADGES */
.badge { display:inline-flex; align-items:center; gap:6px; padding:4px 12px; border-radius:20px; font-size:11px; font-weight:700; white-space:nowrap; }
.bd { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
.b-pending  { background:rgba(245,158,11,0.1);  color:#FCD34D; border:1px solid rgba(245,158,11,0.2); }
.b-pending .bd  { background:#F59E0B; }
.b-waiting  { background:rgba(99,102,241,0.1);  color:#A5B4FC; border:1px solid rgba(99,102,241,0.25); }
.b-waiting .bd  { background:#6366F1; box-shadow:0 0 8px #6366F1; animation:gpulse 1.5s infinite; }
.b-approved { background:rgba(16,185,129,0.1);  color:#6EE7B7; border:1px solid rgba(16,185,129,0.2); }
.b-approved .bd { background:#10B981; }
.b-dispatch { background:rgba(6,182,212,0.1);   color:#67E8F9; border:1px solid rgba(6,182,212,0.2); }
.b-dispatch .bd { background:#06B6D4; }
.b-rejected { background:rgba(239,68,68,0.1);   color:#FCA5A5; border:1px solid rgba(239,68,68,0.2); }
.b-rejected .bd { background:#EF4444; }
@keyframes gpulse { 0%,100%{opacity:1;box-shadow:0 0 8px #6366F1;} 50%{opacity:.2;box-shadow:none;} }

/* BUTTONS */
.btn { display:inline-flex; align-items:center; gap:6px; padding:8px 15px; border-radius:9px; font-size:12px; font-weight:700; font-family:'Inter',sans-serif; cursor:pointer; border:none; white-space:nowrap; transition:all .2s; }
.btn-gen { background:linear-gradient(135deg,#6366F1,#8B5CF6); color:white; box-shadow:0 4px 14px rgba(99,102,241,0.35); }
.btn-gen:hover { transform:translateY(-2px); box-shadow:0 8px 20px rgba(99,102,241,0.5); }
.btn-fwd { background:linear-gradient(135deg,#D97706,#F59E0B); color:white; box-shadow:0 4px 14px rgba(245,158,11,0.35); }
.btn-fwd:hover { transform:translateY(-2px); box-shadow:0 8px 20px rgba(245,158,11,0.5); }
.btn:disabled { background:rgba(255,255,255,0.05); color:#334155; cursor:not-allowed; transform:none; box-shadow:none; border:1px solid rgba(255,255,255,0.07); }

/* CELLS */
.order-id  { font-weight:700; color:#A5B4FC; font-family:monospace; font-size:13px; }
.cust-name { font-weight:600; color:#E2E8F0; }
.cust-phone{ font-size:11px; color:#475569; margin-top:2px; }
.prod-name { font-weight:600; color:#E2E8F0; font-size:13px; }
.prod-sub  { font-size:11px; color:#475569; margin-top:2px; }
.amt { font-weight:800; color:#34D399; }

/* TOAST */
#toast {
  position:fixed; bottom:30px; left:50%;
  transform:translateX(-50%) translateY(120px);
  padding:13px 22px; border-radius:12px; font-size:13px; font-weight:600;
  box-shadow:0 12px 40px rgba(0,0,0,0.7);
  transition:transform .4s cubic-bezier(.34,1.56,.64,1);
  z-index:9999; pointer-events:none;
  display:flex; align-items:center; gap:10px;
  border:1px solid rgba(255,255,255,0.1);
  backdrop-filter:blur(20px); max-width:440px;
}
#toast.show { transform:translateX(-50%) translateY(0); }

/* EMPTY */
.empty { text-align:center; padding:50px 20px; color:#334155; }
.empty-icon { font-size:38px; margin-bottom:12px; opacity:0.35; }
.empty-text { font-size:13px; }

::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-thumb { background:rgba(99,102,241,0.3); border-radius:2px; }
</style>
</head>
<body>

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-icon">📱</div>
    <div class="logo-name">MobileMart PK</div>
    <div class="logo-sub">Order Management System</div>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-section">Navigation</div>
    <div class="nav-item active"><span>📋</span> All Orders</div>
    <div class="nav-item" onclick="document.getElementById('inv-panel').scrollIntoView({behavior:'smooth'})">
      <span>📬</span> Invoice History
    </div>
    <div class="nav-section">Live Status</div>
    <div class="nav-item">
      <div class="status-dot" style="background:#F59E0B;box-shadow:0 0 6px #F59E0B55"></div>
      <span style="flex:1">Pending</span>
      <span class="count-badge" id="sb-p" style="color:#FCD34D">—</span>
    </div>
    <div class="nav-item">
      <div class="status-dot" style="background:#6366F1"></div>
      <span style="flex:1">Awaiting Boss</span>
      <span class="count-badge" id="sb-w" style="color:#A5B4FC">—</span>
    </div>
    <div class="nav-item">
      <div class="status-dot" style="background:#10B981"></div>
      <span style="flex:1">Approved</span>
      <span class="count-badge" id="sb-a" style="color:#6EE7B7">—</span>
    </div>
    <div class="nav-item">
      <div class="status-dot" style="background:#06B6D4"></div>
      <span style="flex:1">Dispatched</span>
      <span class="count-badge" id="sb-d" style="color:#67E8F9">—</span>
    </div>
    <div class="nav-item">
      <div class="status-dot" style="background:#EF4444"></div>
      <span style="flex:1">Rejected</span>
      <span class="count-badge" id="sb-r" style="color:#FCA5A5">—</span>
    </div>
  </nav>
  <div class="sidebar-stats">
    <div class="ss-label">Revenue Summary</div>
    <div class="ss-row"><span class="ss-key">Total Value</span><span class="ss-val" id="ss-rev" style="color:#A5B4FC">—</span></div>
    <div class="ss-row"><span class="ss-key">Invoices Sent</span><span class="ss-val" id="ss-inv" style="color:#6EE7B7">—</span></div>
  </div>
  <div class="sidebar-footer">
    🔄 Auto-refresh every 15s<br>
    <span id="last-refresh" style="color:#1E293B;font-size:10px">—</span>
  </div>
</aside>

<!-- MAIN -->
<main class="main">
  <div class="page-header">
    <div>
      <div class="ph-title">📱 Order Dashboard</div>
      <div class="ph-sub">Generate invoices · Send for approval · Dispatch to supplier</div>
    </div>
    <div class="ph-right">
      <button class="refresh-btn" onclick="loadData()">↺ Refresh Now</button>
      <div class="badge-demo">LIVE</div>
    </div>
  </div>

  <div class="flow-bar">
    <div class="flow-step">
      <div class="flow-num fn1">1</div>
      <div><div class="flow-title">Generate Invoice</div><div class="flow-desc">PDF created instantly</div></div>
    </div>
    <div class="flow-arrow">→</div>
    <div class="flow-step">
      <div class="flow-num fn2">2</div>
      <div><div class="flow-title">Boss Reviews</div><div class="flow-desc">Email + PDF sent · Pending decision</div></div>
    </div>
    <div class="flow-arrow">→</div>
    <div class="flow-step">
      <div class="flow-num fn3">3</div>
      <div><div class="flow-title">You're Notified</div><div class="flow-desc">Confirmation email → your inbox</div></div>
    </div>
    <div class="flow-arrow">→</div>
    <div class="flow-step">
      <div class="flow-num fn4">4</div>
      <div><div class="flow-title">Forward to Supplier</div><div class="flow-desc">Click → supplier gets the order</div></div>
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card kc1"><div class="kpi-glow"></div><div class="kpi-icon">🗂️</div><div class="kpi-val" id="k-total">—</div><div class="kpi-lbl">Total Orders</div></div>
    <div class="kpi-card kc2"><div class="kpi-glow"></div><div class="kpi-icon">💰</div><div class="kpi-val" id="k-rev" style="font-size:15px;letter-spacing:0">—</div><div class="kpi-lbl">Total Revenue</div></div>
    <div class="kpi-card kc3"><div class="kpi-glow"></div><div class="kpi-icon">⏳</div><div class="kpi-val" id="k-pending">—</div><div class="kpi-lbl">Pending</div></div>
    <div class="kpi-card kc4"><div class="kpi-glow"></div><div class="kpi-icon">✅</div><div class="kpi-val" id="k-approved">—</div><div class="kpi-lbl">Approved</div></div>
    <div class="kpi-card kc5"><div class="kpi-glow"></div><div class="kpi-icon">🚚</div><div class="kpi-val" id="k-dispatch">—</div><div class="kpi-lbl">Dispatched</div></div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <div class="ph-l">
        <h2>📋 All Orders</h2>
        <span class="p-count" id="ord-cnt">loading...</span>
      </div>
      <span class="ph-hint">Click ⚡ Generate Invoice to start the workflow</span>
    </div>
    <div class="tbl-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>Order ID</th><th>Customer</th><th>Product</th>
          <th>Qty</th><th>Amount</th><th>Date</th><th>Status</th><th>Action</th>
        </tr></thead>
        <tbody id="orders-body">
          <tr><td colspan="9"><div class="empty"><div class="empty-icon">⏳</div><div class="empty-text">Loading orders...</div></div></td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="panel" id="inv-panel">
    <div class="panel-head">
      <div class="ph-l">
        <h2>📬 Invoice History</h2>
        <span class="p-count" id="inv-cnt">loading...</span>
      </div>
      <span class="ph-hint">Updates automatically every 15s</span>
    </div>
    <div class="tbl-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>Invoice ID</th><th>Order ID</th>
          <th>Sent To Boss</th><th>Sent At</th><th>Status</th><th>PDF</th>
        </tr></thead>
        <tbody id="inv-body">
          <tr><td colspan="7"><div class="empty"><div class="empty-icon">📭</div><div class="empty-text">No invoices yet.</div></div></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</main>

<div id="toast"></div>

<script>
function toast(msg, type) {
  var t = document.getElementById('toast');
  var cfg = {
    info:    {bg:'rgba(30,58,95,0.97)',  bd:'#3B82F6', ic:'ℹ️'},
    success: {bg:'rgba(6,78,59,0.97)',   bd:'#10B981', ic:'✅'},
    error:   {bg:'rgba(76,5,25,0.97)',   bd:'#EF4444', ic:'❌'},
    warn:    {bg:'rgba(69,26,3,0.97)',   bd:'#F59E0B', ic:'⚠️'}
  };
  var c = cfg[type] || cfg.info;
  t.innerHTML = '<span>' + c.ic + '</span><span>' + msg + '</span>';
  t.style.background  = c.bg;
  t.style.borderColor = c.bd;
  t.style.color = '#F1F5F9';
  t.classList.add('show');
  setTimeout(function(){ t.classList.remove('show'); }, 5000);
}

function badge(status) {
  var map = {
    'PENDING':                ['b-pending',  'Pending'],
    'AWAITING APPROVAL':      ['b-waiting',  'Awaiting Approval'],
    'APPROVED':               ['b-approved', 'Approved'],
    'REJECTED':               ['b-rejected', 'Rejected'],
    'DISPATCHED TO SUPPLIER': ['b-dispatch', 'Dispatched'],
    'FORWARDED TO SUPPLIER':  ['b-dispatch', 'Forwarded']
  };
  var info = map[status] || ['b-pending', status];
  return '<span class="badge ' + info[0] + '"><span class="bd"></span>' + info[1] + '</span>';
}

function btn_html(o, inv) {
  if (o.status === 'PENDING') {
    return '<button class="btn btn-gen" onclick="genInvoice(\'' + o.order_id + '\', this)">⚡ Generate Invoice</button>';
  } else if (o.status === 'AWAITING APPROVAL') {
    return '<button class="btn" disabled>⏳ Awaiting Boss</button>';
  } else if (o.status === 'APPROVED') {
    var iid = inv ? inv.invoice_id : '';
    return '<button class="btn btn-fwd" onclick="fwdSupplier(\'' + o.order_id + '\', \'' + iid + '\', this)">🚚 Forward to Supplier</button>';
  } else if (o.status === 'DISPATCHED TO SUPPLIER' || o.status === 'FORWARDED TO SUPPLIER') {
    return '<button class="btn" disabled>✓ Dispatched</button>';
  } else if (o.status === 'REJECTED') {
    return '<button class="btn" disabled style="color:#EF4444;border-color:rgba(239,68,68,0.2)">✗ Rejected</button>';
  }
  return '';
}

async function loadData() {
  try {
    var res = await fetch('/api/data');
    if (!res.ok) { toast('Server error: ' + res.status, 'error'); return; }
    var data     = await res.json();
    var orders   = data.orders   || [];
    var invoices = data.invoices || [];

    var revenue  = orders.reduce(function(s,o){ return s+(o.total_price||0); }, 0);
    var pending  = orders.filter(function(o){ return o.status==='PENDING'; }).length;
    var waiting  = orders.filter(function(o){ return o.status==='AWAITING APPROVAL'; }).length;
    var approved = orders.filter(function(o){ return o.status==='APPROVED'; }).length;
    var dispatch = orders.filter(function(o){ return o.status==='DISPATCHED TO SUPPLIER'||o.status==='FORWARDED TO SUPPLIER'; }).length;
    var rejected = orders.filter(function(o){ return o.status==='REJECTED'; }).length;

    document.getElementById('k-total').textContent    = orders.length;
    document.getElementById('k-rev').textContent      = 'PKR ' + revenue.toLocaleString();
    document.getElementById('k-pending').textContent  = pending;
    document.getElementById('k-approved').textContent = approved;
    document.getElementById('k-dispatch').textContent = dispatch;
    document.getElementById('sb-p').textContent = pending;
    document.getElementById('sb-w').textContent = waiting;
    document.getElementById('sb-a').textContent = approved;
    document.getElementById('sb-d').textContent = dispatch;
    document.getElementById('sb-r').textContent = rejected;
    document.getElementById('ss-rev').textContent = 'PKR ' + revenue.toLocaleString();
    document.getElementById('ss-inv').textContent = invoices.length;
    document.getElementById('ord-cnt').textContent = orders.length + ' orders';
    document.getElementById('inv-cnt').textContent = invoices.length + ' invoices';
    document.getElementById('last-refresh').textContent = 'Updated ' + new Date().toLocaleTimeString();

    var invMap = {};
    invoices.forEach(function(inv) {
      if (!invMap[inv.order_id] || new Date(inv.generated_at) > new Date(invMap[inv.order_id].generated_at))
        invMap[inv.order_id] = inv;
    });

    var ob = document.getElementById('orders-body');
    if (orders.length === 0) {
      ob.innerHTML = '<tr><td colspan="9"><div class="empty"><div class="empty-icon">📦</div><div class="empty-text">No orders found. Check /debug for DB status.</div></div></td></tr>';
    } else {
      var html = '';
      orders.forEach(function(o, i) {
        var inv = invMap[o.order_id];
        html += '<tr>' +
          '<td style="color:#334155;font-size:11px">' + (i+1) + '</td>' +
          '<td><span class="order-id">' + o.order_id + '</span></td>' +
          '<td><div class="cust-name">' + o.customer_name + '</div><div class="cust-phone">' + o.customer_phone + '</div></td>' +
          '<td><div class="prod-name">' + o.product_name + '</div><div class="prod-sub">' + o.brand + ' · ' + o.category + '</div></td>' +
          '<td style="text-align:center;font-weight:700;color:#E2E8F0">' + o.quantity + '</td>' +
          '<td><span class="amt">PKR ' + Number(o.total_price).toLocaleString() + '</span></td>' +
          '<td style="color:#475569;font-size:12px">' + (o.order_date||'').slice(0,10) + '</td>' +
          '<td>' + badge(o.status) + '</td>' +
          '<td>' + btn_html(o, inv) + '</td>' +
          '</tr>';
      });
      ob.innerHTML = html;
    }

    var ib = document.getElementById('inv-body');
    if (invoices.length === 0) {
      ib.innerHTML = '<tr><td colspan="7"><div class="empty"><div class="empty-icon">📭</div><div class="empty-text">No invoices yet. Click Generate Invoice above.</div></div></td></tr>';
    } else {
      var html2 = '';
      invoices.forEach(function(inv, i) {
        html2 += '<tr>' +
          '<td style="color:#334155;font-size:11px">' + (i+1) + '</td>' +
          '<td style="font-family:monospace;font-size:12px;color:#C4B5FD;font-weight:700">' + inv.invoice_id + '</td>' +
          '<td style="font-weight:700;color:#A5B4FC">' + inv.order_id + '</td>' +
          '<td style="font-size:12px;color:#475569">' + (inv.boss_email||'—') + '</td>' +
          '<td style="font-size:12px;color:#475569">' + (inv.sent_at||'').slice(0,16).replace('T',' ') + '</td>' +
          '<td>' + badge(inv.status) + '</td>' +
          '<td><span style="color:#475569;font-size:12px">PDF emailed</span></td>' +
          '</tr>';
      });
      ib.innerHTML = html2;
    }
  } catch(e) {
    console.error(e);
    toast('Failed to load: ' + e.message, 'error');
  }
}

function genInvoice(orderId, btn) {
  btn.disabled = true;
  btn.innerHTML = '⏳ Sending...';
  toast('Generating PDF and emailing boss...', 'info');
  fetch('/generate', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({order_id: orderId})
  })
  .then(function(r){ return r.json(); })
  .then(function(data) {
    if (data.success) {
      toast('Invoice ' + data.invoice_id + ' sent to boss!', 'success');
      setTimeout(loadData, 1200);
    } else {
      btn.disabled = false;
      btn.innerHTML = '⚡ Generate Invoice';
      toast('Error: ' + data.error, 'error');
    }
  })
  .catch(function(e) {
    btn.disabled = false;
    btn.innerHTML = '⚡ Generate Invoice';
    toast('Network error: ' + e.message, 'error');
  });
}

function fwdSupplier(orderId, invoiceId, btn) {
  btn.disabled = true;
  btn.innerHTML = '⏳ Forwarding...';
  toast('Sending order to supplier...', 'info');
  fetch('/forward', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({order_id: orderId, invoice_id: invoiceId})
  })
  .then(function(r){ return r.json(); })
  .then(function(data) {
    if (data.success) {
      toast('Order forwarded to supplier!', 'success');
      setTimeout(loadData, 1200);
    } else {
      btn.disabled = false;
      btn.innerHTML = '🚚 Forward to Supplier';
      toast('Error: ' + data.error, 'error');
    }
  })
  .catch(function(e) {
    btn.disabled = false;
    btn.innerHTML = '🚚 Forward to Supplier';
    toast('Network error: ' + e.message, 'error');
  });
}

loadData();
setInterval(loadData, 15000);
</script>
</body>
</html>"""


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/api/data")
def api_data():
    try:
        orders   = fetch_all_orders()
        invoices = fetch_all_invoices()
        return jsonify({"orders": orders, "invoices": invoices})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"orders": [], "invoices": [], "error": str(e)})


@app.route("/generate", methods=["POST"])
def generate():
    try:
        order_id = request.get_json().get("order_id")
        order    = fetch_order_by_id(order_id)
        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        # Generate PDF in memory — works on Render and locally
        pdf_bytes, invoice_id = generate_invoice_bytes(order)

        # Save to DB and send approval email to boss with PDF attached
        create_and_send_invoice(order, pdf_bytes, invoice_id,
                                BOSS_EMAIL, YOUR_EMAIL)

        update_order_status(order_id, "AWAITING APPROVAL")
        return jsonify({"success": True, "invoice_id": invoice_id})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/forward", methods=["POST"])
def forward():
    try:
        body       = request.get_json()
        order_id   = body.get("order_id")
        invoice_id = body.get("invoice_id")
        order      = fetch_order_by_id(order_id)
        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        send_to_supplier(order, invoice_id, SUPPLIER_EMAIL, YOUR_EMAIL)
        return jsonify({"success": True})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/accept")
def accept():
    token = request.args.get("token", "")
    ok, invoice_id, order_id = process_acceptance(token)
    if ok:
        return ("""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Inter',sans-serif;background:#060B18;display:flex;align-items:center;justify-content:center;min-height:100vh;}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 60% 50% at 50% 0%,rgba(16,185,129,0.18) 0%,transparent 70%);pointer-events:none;}
.card{background:rgba(15,23,42,0.92);border:1px solid rgba(16,185,129,0.3);border-radius:20px;padding:52px 44px;text-align:center;max-width:420px;width:90%;box-shadow:0 0 60px rgba(16,185,129,0.12);position:relative;z-index:1;}
.ring{width:80px;height:80px;border-radius:50%;background:rgba(16,185,129,0.12);border:2px solid rgba(16,185,129,0.4);display:flex;align-items:center;justify-content:center;font-size:36px;margin:0 auto 24px;}
h1{color:#34D399;font-size:24px;font-weight:800;margin-bottom:20px;}
.row{background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.15);border-radius:10px;padding:12px 18px;margin:10px 0;text-align:left;}
.rl{font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;}
.rv{font-size:14px;font-weight:700;color:#E2E8F0;margin-top:3px;}
p{color:#475569;font-size:13px;line-height:1.7;margin:18px 0;}
a{display:inline-block;margin-top:16px;background:rgba(99,102,241,0.15);color:#A5B4FC;border:1px solid rgba(99,102,241,0.3);padding:10px 22px;border-radius:10px;font-weight:600;font-size:13px;text-decoration:none;}
</style></head><body><div class="card">
<div class="ring">✅</div>
<h1>Order Accepted!</h1>
<div class="row"><div class="rl">Invoice ID</div><div class="rv">""" + invoice_id + """</div></div>
<div class="row"><div class="rl">Order ID</div><div class="rv">""" + order_id + """</div></div>
<p>This order is <strong style="color:#34D399">APPROVED</strong>. A confirmation email has been sent to the team.</p>
<a href="/">← Back to Dashboard</a>
</div></body></html>""")
    return ('<html><body style="font-family:Inter,Arial;background:#060B18;color:white;text-align:center;padding:60px;">'
            '<h2 style="color:#EF4444;">⚠️ ' + str(invoice_id) + '</h2>'
            '<a href="/" style="color:#818CF8;">← Back</a></body></html>')


@app.route("/reject")
def reject():
    token = request.args.get("token", "")
    ok, result = process_rejection(token)
    if ok:
        return ("""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Inter',sans-serif;background:#060B18;display:flex;align-items:center;justify-content:center;min-height:100vh;}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 60% 50% at 50% 0%,rgba(239,68,68,0.15) 0%,transparent 70%);pointer-events:none;}
.card{background:rgba(15,23,42,0.92);border:1px solid rgba(239,68,68,0.3);border-radius:20px;padding:52px 44px;text-align:center;max-width:420px;width:90%;box-shadow:0 0 60px rgba(239,68,68,0.1);position:relative;z-index:1;}
.ring{width:80px;height:80px;border-radius:50%;background:rgba(239,68,68,0.1);border:2px solid rgba(239,68,68,0.35);display:flex;align-items:center;justify-content:center;font-size:36px;margin:0 auto 24px;}
h1{color:#FCA5A5;font-size:24px;font-weight:800;margin-bottom:20px;}
.row{background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.15);border-radius:10px;padding:12px 18px;margin:10px 0;text-align:left;}
.rl{font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;}
.rv{font-size:14px;font-weight:700;color:#E2E8F0;margin-top:3px;}
p{color:#475569;font-size:13px;line-height:1.7;margin:18px 0;}
a{display:inline-block;margin-top:16px;background:rgba(99,102,241,0.15);color:#A5B4FC;border:1px solid rgba(99,102,241,0.3);padding:10px 22px;border-radius:10px;font-weight:600;font-size:13px;text-decoration:none;}
</style></head><body><div class="card">
<div class="ring">❌</div>
<h1>Order Rejected</h1>
<div class="row"><div class="rl">Invoice ID</div><div class="rv">""" + result + """</div></div>
<p>This order has been <strong style="color:#FCA5A5">REJECTED</strong> and cancelled.</p>
<a href="/">← Back to Dashboard</a>
</div></body></html>""")
    return ('<html><body style="font-family:Inter,Arial;background:#060B18;color:white;text-align:center;padding:60px;">'
            '<h2 style="color:#EF4444;">⚠️ ' + str(result) + '</h2>'
            '<a href="/" style="color:#818CF8;">← Back</a></body></html>')


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    setup_database()
    seed_orders()
    print("\n" + "="*52)
    print("  MobileMart is running!")
    print("  Dashboard : http://localhost:5000")
    print("  Debug     : http://localhost:5000/debug")
    print("="*52 + "\n")
    app.run(debug=True, port=5000)