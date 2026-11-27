const API = "";           // same origin (Flask serves UI + API)

const $  = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

// ---------- Tab switching ----------
$$("nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$("nav button").forEach((b) => b.classList.remove("active"));
    $$(".tab").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    $("#tab-" + btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "list")         loadBookings();
    if (btn.dataset.tab === "reports")      loadReports();
    if (btn.dataset.tab === "mongo")        loadMongoReport();
  });
});

// ---------- Helpers ----------
async function api(path, opts) {
  const res = await fetch(API + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

function rowsToTable(tbody, rows, mapper) {
  tbody.innerHTML = "";
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:#999">(no rows)</td></tr>`;
    return;
  }
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = mapper(r);
    tbody.appendChild(tr);
  });
}

function localDT(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ---------- Bootstrap: load dropdowns ----------
async function loadRefs() {
  const [emps, desks] = await Promise.all([
    api("/api/employees"),
    api("/api/desks"),
  ]);
  const empSel  = $("#book-emp");
  const deskSel = $("#book-desk");
  empSel.innerHTML  = emps .map((e) => `<option value="${e.emp_id}">${e.emp_name} — ${e.role}</option>`).join("");
  deskSel.innerHTML = desks.map((d) => `<option value="${d.desk_id}">${d.desk_code} (${d.desk_type}, cap ${d.capacity}) — ${d.floor_name}/${d.zone_name}</option>`).join("");
}

// ---------- Book ----------
$("#book-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = $("#book-msg");
  msg.className = "msg";
  msg.textContent = "Reserving…";
  try {
    const body = {
      desk_id:    Number($("#book-desk").value),
      emp_id:     Number($("#book-emp").value),
      start_time: $("#book-start").value,
      end_time:   $("#book-end").value,
    };
    const r = await api("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    msg.className = "msg ok";
    msg.textContent = `✓ Booked successfully (booking #${r.booking_id}).`;
    $("#book-start").value = "";
    $("#book-end").value = "";
  } catch (err) {
    msg.className = "msg err";
    msg.textContent = `✗ ${err.error || "Booking failed"}${err.type === "conflict" ? " — overlapping reservation blocked." : ""}`;
  }
});

// ---------- Bookings list ----------
async function loadBookings() {
  const rows = await api("/api/bookings");
  rowsToTable($("#bookings-table tbody"), rows, (b) => `
    <td>${b.booking_id}</td>
    <td>${b.desk_code}</td>
    <td>${b.emp_name}</td>
    <td>${b.start_time}</td>
    <td>${b.end_time}</td>
    <td class="status-${b.status}">${b.status}</td>
    <td>
      ${b.status === "CONFIRMED" ? `
        <button onclick="act(${b.booking_id}, 'checkin')">Check-In</button>
        <button onclick="act(${b.booking_id}, 'checkout')">Check-Out</button>
        <button onclick="act(${b.booking_id}, 'cancel')">Cancel</button>
      ` : "—"}
    </td>
  `);
}
$("#reload-bookings").addEventListener("click", loadBookings);

window.act = async function (bid, action) {
  try {
    if (action === "cancel") {
      const reason = prompt("Cancellation reason?") || "";
      await api(`/api/bookings/${bid}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
    } else {
      await api(`/api/bookings/${bid}/${action}`, { method: "POST" });
    }
    loadBookings();
  } catch (e) {
    alert(e.error || "Action failed");
  }
};

// ---------- Availability ----------
$("#avail-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const cap   = $("#avail-cap").value;
  const start = $("#avail-start").value;
  const end   = $("#avail-end").value;
  try {
    const rows = await api(
      `/api/availability?capacity=${cap}&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
    );
    rowsToTable($("#avail-table tbody"), rows, (r) => `
      <td>${r.desk_code}</td><td>${r.capacity}</td>
    `);
  } catch (err) {
    alert(err.error || "Query failed");
  }
});

// ---------- Reports ----------
async function loadReports() {
  const [peak, zones, noshows, below, current] = await Promise.all([
    api("/api/reports/peak-hours"),
    api("/api/reports/zone-utilization"),
    api("/api/reports/no-shows"),
    api("/api/reports/below-average"),
    api("/api/reports/current-availability"),
  ]);
  rowsToTable($("#rep-peak   tbody"), peak,    (r) => `<td>${r.hour_of_day}:00</td><td>${r.bookings}</td>`);
  rowsToTable($("#rep-zone   tbody"), zones,   (r) => `<td>${r.zone_name}</td><td>${r.bookings}</td><td>${r.zone_rank}</td>`);
  rowsToTable($("#rep-noshow tbody"), noshows, (r) => `<td>${r.emp_name}</td><td>#${r.booking_id}</td><td>${r.start_time}</td>`);
  rowsToTable($("#rep-below  tbody"), below,   (r) => `<td>${r.desk_code}</td><td>${r.uses}</td>`);
  rowsToTable($("#rep-current tbody"), current, (r) => `<td>${r.desk_code}</td><td>${r.capacity}</td>`);
}

// ---------- MongoDB ----------
$("#mongo-search").addEventListener("click", async () => {
  const name = $("#mongo-amenity").value.trim();
  const rows = await api("/api/mongo/resources" + (name ? `?amenity=${encodeURIComponent(name)}` : ""));
  rowsToTable($("#mongo-table tbody"), rows, (r) => `
    <td>${r.desk_code}</td><td>${r.zone}</td><td>${r.resource_id}</td>
  `);
});

$("#mongo-add").addEventListener("click", async () => {
  const rid = $("#mongo-rid").value;
  const name = $("#mongo-name").value.trim();
  const count = Number($("#mongo-count").value) || 1;
  const msg = $("#mongo-msg");
  if (!rid || !name) { msg.textContent = "Resource ID and name are required."; msg.className = "msg err"; return; }
  try {
    await api(`/api/mongo/resource/${rid}/amenity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, count }),
    });
    msg.className = "msg ok";
    msg.textContent = "✓ Amenity added.";
    loadMongoReport();
  } catch (e) {
    msg.className = "msg err";
    msg.textContent = "✗ " + (e.error || "Failed");
  }
});

async function loadMongoReport() {
  const rows = await api("/api/mongo/amenity-report");
  rowsToTable($("#mongo-report tbody"), rows, (r) => `
    <td>${r.zone}</td><td>${r.total_units}</td><td>${r.distinct_count}</td>
  `);
}

// ---------- Init ----------
(async () => {
  try {
    await loadRefs();
    const now = new Date();
    const start = new Date(now); start.setMinutes(0, 0, 0);
    const end = new Date(start); end.setHours(end.getHours() + 1);
    $("#book-start").value = localDT(start);
    $("#book-end").value   = localDT(end);
    $("#avail-start").value = localDT(start);
    $("#avail-end").value   = localDT(end);
    loadBookings();
    loadReports();
    loadMongoReport();
  } catch (e) {
    console.error(e);
  }
})();