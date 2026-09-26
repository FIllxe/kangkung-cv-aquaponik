/* Dashboard Monitor Kangkung Live — logika tampilan (vanilla JS, tanpa build).
 *
 * Sumber data: Firestore collection `bed_readings` yang di-push Raspberry Pi
 * tiap +-10 menit (skema: docs/SKEMA_FIREBASE_BED_READINGS.md). Dashboard ini
 * HANYA membaca — tidak ada aksi tulis/kontrol apa pun.
 *
 * Mode:
 *   - LIVE : `firebase-config.js` terisi -> onSnapshot realtime.
 *   - DEMO : `?demo=1`, atau config belum diisi / SDK gagal dimuat (offline).
 */

// ── Konstanta: disalin dari files/kangkung_cv.py agar tampilan = hasil backend ─
const GRID_ROWS = 4;
const GRID_COLS = 6;
const STATUS = {
  belum_siap:  { label: "Belum siap",  color: "#3498db", rentang: "0–25%" },
  hampir_siap: { label: "Hampir siap", color: "#f39c12", rentang: "25–55%" },
  siap_panen:  { label: "Siap panen",  color: "#2ecc71", rentang: "55–80%" },
  harus_panen: { label: "Harus panen", color: "#e74c3c", rentang: "≥ 80%" },
};
const KESEHATAN = {
  sehat:   { label: "Sehat",   color: "#2ecc71" },
  waspada: { label: "Waspada", color: "#f39c12" },
  sakit:   { label: "Sakit",   color: "#e74c3c" },
  "n/a":   { label: "n/a",     color: "#8c8c8c" },
};
const AMBANG = { kuning_waspada: 10, kuning_sakit: 25, coklat_waspada: 3, coklat_sakit: 8 };
const SUHU = { aman: 70, waspada: 75 };      // config.json: suhu_maks_c = 75
const MAKS_RIWAYAT = 144;                    // ±24 jam pada interval 10 menit
const SDK_URL = "https://www.gstatic.com/firebasejs/10.12.5";

// ── Helper singkat ───────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

function el(tag, cls, teks) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (teks !== undefined && teks !== null) n.textContent = teks;
  return n;
}

function fmt(n, d = 1) {
  return Number.isFinite(n) ? Number(n).toFixed(d) : "–";
}

function waktuRelatif(iso) {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return "–";
  const s = Math.max(0, Math.round((Date.now() - t) / 1000));
  if (s < 60) return `${s} detik lalu`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m} menit lalu`;
  const j = Math.round(m / 60);
  return j < 24 ? `${j} jam lalu` : `${Math.round(j / 24)} hari lalu`;
}

function idZonaUrut() {
  const out = [];
  for (let r = 1; r <= GRID_ROWS; r++) {
    for (let c = 1; c <= GRID_COLS; c++) out.push(`R${r}C${c}`);
  }
  return out;
}

// ── Turunan status/kesehatan (cadangan bila dokumen hanya berisi agregat) ────
function statusDari(cov) {
  if (!Number.isFinite(cov) || cov < 25) return "belum_siap";
  if (cov < 55) return "hampir_siap";
  if (cov < 80) return "siap_panen";
  return "harus_panen";
}

function kesehatanDari(pk, pc) {
  if ((pc ?? 0) >= AMBANG.coklat_sakit || (pk ?? 0) >= AMBANG.kuning_sakit) return "sakit";
  if ((pc ?? 0) >= AMBANG.coklat_waspada || (pk ?? 0) >= AMBANG.kuning_waspada) return "waspada";
  return "sehat";
}

/* Lengkapi payload: hitung agregat yang hilang dari data zona.
 * Membuat dashboard tetap benar walau dokumen lama lebih ringkas. */
function lengkapiPayload(doc) {
  const zona = {};
  for (const id of idZonaUrut()) {
    const z = (doc.zona || {})[id] || {};
    const cov = Number(z.coverage);
    const pk = Number(z.pct_kuning) || 0;
    const pc = Number(z.pct_coklat) || 0;
    zona[id] = {
      coverage: Number.isFinite(cov) ? cov : null,
      status: z.status || statusDari(cov),
      pct_kuning: pk,
      pct_coklat: pc,
      kesehatan: z.kesehatan || kesehatanDari(pk, pc),
    };
  }
  const terisi = Object.values(zona).filter((z) => Number.isFinite(z.coverage));
  const covs = terisi.map((z) => z.coverage);
  const rata = covs.length ? covs.reduce((a, b) => a + b, 0) / covs.length : 0;
  const varian = covs.length
    ? covs.reduce((a, b) => a + (b - rata) ** 2, 0) / covs.length : 0;

  const dist = { belum_siap: 0, hampir_siap: 0, siap_panen: 0, harus_panen: 0 };
  const kes = { sehat: 0, waspada: 0, sakit: 0 };
  for (const z of terisi) {
    if (dist[z.status] !== undefined) dist[z.status] += 1;
    if (kes[z.kesehatan] !== undefined) kes[z.kesehatan] += 1;
  }
  const siap = dist.siap_panen + dist.harus_panen;
  const total = GRID_ROWS * GRID_COLS;
  const kuning = terisi.length ? terisi.reduce((a, z) => a + z.pct_kuning, 0) / terisi.length : 0;
  const coklat = terisi.length ? terisi.reduce((a, z) => a + z.pct_coklat, 0) / terisi.length : 0;
  const bulat = (x) => Math.round(x * 100) / 100;
  const psiRata = hitungPsi(kuning, coklat);
  const psiMaks = terisi.length
    ? Math.round(Math.max(...terisi.map((z) => hitungPsi(z.pct_kuning, z.pct_coklat))) * 10) / 10
    : 0;

  return {
    device_id: doc.device_id || "pi-bed-01",
    timestamp: doc.timestamp || new Date().toISOString(),
    mode: doc.mode || "PI-LIVE",
    zona,
    zona_terisi: terisi.length,
    coverage_rata: Number.isFinite(doc.coverage_rata) ? doc.coverage_rata : bulat(rata),
    coverage_std: Number.isFinite(doc.coverage_std) ? doc.coverage_std : bulat(Math.sqrt(varian)),
    status_distribusi: doc.status_distribusi || dist,
    zona_siap_panen: Number.isFinite(doc.zona_siap_panen) ? doc.zona_siap_panen : siap,
    persen_siap: Number.isFinite(doc.persen_siap) ? doc.persen_siap : Math.round(siap / total * 1000) / 10,
    kesehatan_distribusi: (doc.kesehatan && doc.kesehatan.distribusi) || kes,
    kuning_rata: doc.kesehatan && Number.isFinite(doc.kesehatan.kuning_rata)
      ? doc.kesehatan.kuning_rata : bulat(kuning),
    coklat_rata: doc.kesehatan && Number.isFinite(doc.kesehatan.coklat_rata)
      ? doc.kesehatan.coklat_rata : bulat(coklat),
    fuzzy_input: doc.fuzzy_input || {
      kuning_pct: bulat(kuning),
      coklat_pct: bulat(coklat),
      zona_sakit: kes.sakit,
      psi: psiRata,
      psi_maks: psiMaks,
      psi_versi: "1.0",
      indeks_sehat: Math.round((100 - psiRata) * 10) / 10,
    },
    rekomendasi: doc.rekomendasi || "",
    snapshot_url: doc.snapshot_url || null,
    suhu_pi_c: Number.isFinite(doc.suhu_pi_c) ? doc.suhu_pi_c : null,
    doc_id: doc.doc_id || null,
  };
}

// PSI (Plant Stress Index) 0-100, TINGGI = makin stres.
// WAJIB identik dengan hitung_psi() di files/kangkung_cv.py (sumber tunggal):
//   PSI = 100 * min(1, 0.4*min(kuning/25,1) + 0.6*min(coklat/8,1))
// Hanya dipakai sebagai fallback untuk dokumen lama yang belum punya psi.
const PSI_AMBANG = { kuning: 25, coklat: 8 };
const PSI_BOBOT = { kuning: 0.4, coklat: 0.6 };
function hitungPsi(pctKuning, pctCoklat) {
  const k = Math.min(1, Math.max(0, pctKuning) / PSI_AMBANG.kuning);
  const c = Math.min(1, Math.max(0, pctCoklat) / PSI_AMBANG.coklat);
  return Math.round(100 * Math.min(1, PSI_BOBOT.kuning * k + PSI_BOBOT.coklat * c) * 10) / 10;
}

// ── Data demo (agar halaman bisa dilihat tanpa Firebase) ─────────────────────
function acakBibit(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function buatZonaDemo(rand, maju) {
  const zona = {};
  for (let r = 1; r <= GRID_ROWS; r++) {
    for (let c = 1; c <= GRID_COLS; c++) {
      const fase = (c - 1) / (GRID_COLS - 1);        // bed "matang" dari kolom kiri
      const cov = Math.max(0, Math.min(100, 10 + fase * 80 + maju + (rand() - 0.5) * 16));
      const pk = rand() < 0.18 ? 11 + rand() * 20 : rand() * 7;
      const pc = rand() < 0.09 ? 4 + rand() * 8 : rand() * 2.5;
      zona[`R${r}C${c}`] = {
        coverage: Math.round(cov * 100) / 100,
        pct_kuning: Math.round(pk * 100) / 100,
        pct_coklat: Math.round(pc * 100) / 100,
        status: statusDari(cov),
        kesehatan: kesehatanDari(pk, pc),
      };
    }
  }
  return zona;
}

function buatDemo() {
  const rand = acakBibit(20260925);
  const riwayat = [];
  for (let i = MAKS_RIWAYAT - 1; i >= 0; i--) {
    const saat = new Date(Date.now() - i * 10 * 60 * 1000);
    const p = lengkapiPayload({
      device_id: "pi-bed-01",
      timestamp: saat.toISOString(),
      mode: "DEMO",
      zona: buatZonaDemo(rand, (MAKS_RIWAYAT - i) * 0.06),
      suhu_pi_c: Math.round((52 + rand() * 8) * 10) / 10,
      rekomendasi: "Data contoh — bed sisi kiri sudah masuk fase siap panen, "
        + "sisi kanan masih pertumbuhan awal.",
    });
    p.doc_id = `demo_${i}`;
    riwayat.push(p);
  }
  return { payload: riwayat[riwayat.length - 1], riwayat };
}

// ── Indikator koneksi & notifikasi ───────────────────────────────────────────
function setBadge(kelas, teks) {
  const b = $("connBadge");
  b.className = `badge ${kelas}`;
  b.textContent = teks;
}

function tampilkanNotice(pesan) {
  const n = $("notice");
  n.textContent = pesan;
  n.classList.remove("hidden");
}

function sembunyikanNotice() {
  $("notice").classList.add("hidden");
}

// ── Kartu ringkasan ──────────────────────────────────────────────────────────
function renderRingkasan(p) {
  $("covRata").textContent = fmt(p.coverage_rata, 1);
  $("covStd").textContent = `simpangan baku ${fmt(p.coverage_std, 1)}% `
    + `· ${p.zona_terisi}/24 zona terbaca`;

  $("zonaSiap").textContent = String(p.zona_siap_panen);
  $("persenSiap").textContent = `${fmt(p.persen_siap, 1)}% dari total zona`;

  // Kartu utama menampilkan PSI (Plant Stress Index): 0 = sehat, 100 = stres
  // berat. Arah READING: makin TINGGI = makin stres (bukan "makin sehat").
  const psi = p.fuzzy_input ? p.fuzzy_input.psi : null;
  const psiMaks = p.fuzzy_input ? p.fuzzy_input.psi_maks : null;
  $("indeksSehat").textContent = fmt(psi, 0);
  $("kesRingkas").textContent = `kuning ${fmt(p.kuning_rata, 1)}% · `
    + `coklat ${fmt(p.coklat_rata, 1)}%`
    + (Number.isFinite(psiMaks) ? ` · zona terburuk ${fmt(psiMaks, 0)}` : "");

  const suhu = p.suhu_pi_c;
  $("suhuPi").textContent = fmt(suhu, 1);
  const note = $("suhuNote");
  if (!Number.isFinite(suhu)) {
    note.textContent = "suhu tidak tersedia";
    note.style.color = "";
  } else if (suhu >= SUHU.waspada) {
    note.textContent = "panas — risiko thermal guard menunda capture";
    note.style.color = "#e74c3c";
  } else if (suhu >= SUHU.aman) {
    note.textContent = "perlu perhatian (ventilasi/heatsink)";
    note.style.color = "#f39c12";
  } else {
    note.textContent = "aman (ambang thermal guard 75 °C)";
    note.style.color = "";
  }
}

// ── Legenda ──────────────────────────────────────────────────────────────────
function renderLegendaStatus() {
  const box = $("legendStatus");
  box.replaceChildren();
  for (const [k, v] of Object.entries(STATUS)) {
    const s = el("span");
    const i = el("i");
    i.style.background = v.color;
    s.append(i, el("span", null, `${v.label} (${v.rentang})`));
    box.append(s);
  }
}

function renderLegendaKesehatan() {
  const box = $("legendKes");
  box.replaceChildren();
  for (const v of Object.values(KESEHATAN)) {
    const s = el("span");
    const i = el("i");
    i.style.background = v.color;
    i.style.borderRadius = "50%";
    s.append(i, el("span", null, v.label));
    box.append(s);
  }
}

// ── Heatmap 4 × 6 ────────────────────────────────────────────────────────────
let payloadSaatIni = null;
let zonaTerpilih = null;

function renderHeatmap(p) {
  payloadSaatIni = p;
  const box = $("heatmap");
  box.replaceChildren();

  for (const id of idZonaUrut()) {
    const z = p.zona[id] || {};
    const st = STATUS[z.status] || STATUS.belum_siap;
    const tile = el("button", "tile");
    tile.type = "button";
    tile.dataset.zona = id;
    tile.title = `${id} — ${st.label} (${fmt(z.coverage, 1)}%)`;

    if (!Number.isFinite(z.coverage)) {
      tile.classList.add("empty");
      tile.append(el("span", "tile-id", id), el("span", "tile-cov", "–"));
      tile.title = `${id} — belum ada data`;
    } else {
      tile.style.background = st.color;
      tile.append(
        el("span", "tile-id", id),
        el("span", "tile-cov", `${Math.round(z.coverage)}%`),
      );
      const kes = KESEHATAN[z.kesehatan] || KESEHATAN["n/a"];
      const dot = el("span", "tile-kes");
      dot.style.background = kes.color;
      dot.title = `Kesehatan: ${kes.label}`;
      tile.append(dot);
      tile.setAttribute("aria-label",
        `Zona ${id}: coverage ${fmt(z.coverage, 1)} persen, status ${st.label}, `
        + `kesehatan ${kes.label}`);
    }

    tile.addEventListener("click", () => tampilkanDetailZona(id));
    box.append(tile);
  }

  if (zonaTerpilih) tampilkanDetailZona(zonaTerpilih);
}

function tampilkanDetailZona(id) {
  const p = payloadSaatIni;
  const z = p && p.zona[id];
  const box = $("zoneDetail");
  if (!z) {
    box.textContent = `Zona ${id}: data belum tersedia.`;
    return;
  }
  zonaTerpilih = id;

  for (const t of document.querySelectorAll(".tile")) {
    t.classList.toggle("active", t.dataset.zona === id);
  }

  const st = STATUS[z.status] || STATUS.belum_siap;
  const kes = KESEHATAN[z.kesehatan] || KESEHATAN["n/a"];
  box.replaceChildren();

  const judul = el("div");
  judul.append(el("b", null, `Zona ${id}`), el("span", "muted",
    ` · coverage ${fmt(z.coverage, 1)}%`));
  box.append(judul);

  const kv = el("div", "kv");
  const item = (label, nilai, warna) => {
    const s = el("span");
    s.append(el("span", "muted", `${label}: `));
    const b = el("b", null, nilai);
    if (warna) b.style.color = warna;
    s.append(b);
    kv.append(s);
  };
  item("Status panen", `${st.label} (${st.rentang})`, st.color);
  item("Kesehatan", kes.label, kes.color);
  item("Kuning (klorosis)", `${fmt(z.pct_kuning, 1)}%`);
  item("Coklat (nekrosis)", `${fmt(z.pct_coklat, 1)}%`);
  box.append(kv);
}

// ── Distribusi status zona & kesehatan daun ──────────────────────────────────
function isiBar(box, data, palet) {
  const total = GRID_ROWS * GRID_COLS;
  box.replaceChildren();
  for (const [k, gaya] of Object.entries(palet)) {
    const nilai = Number(data[k]) || 0;
    const row = el("div", "dist-row");
    row.append(el("span", null, gaya.label));

    const bar = el("div", "dist-bar");
    const isi = el("i");
    isi.style.width = `${Math.min(100, (nilai / total) * 100)}%`;
    isi.style.background = gaya.color;
    bar.append(isi);

    row.append(bar, el("span", "dist-val", String(nilai)));
    box.append(row);
  }
}

function renderDistribusi(p) {
  isiBar($("distStatus"), p.status_distribusi || {}, STATUS);
  isiBar($("distKes"), p.kesehatan_distribusi || {}, KESEHATAN);
}

// ── Rekomendasi & input fuzzy pompa ──────────────────────────────────────────
function renderRekomendasi(p) {
  const teks = (p.rekomendasi || "").trim();
  $("rekomendasi").textContent = teks
    || (p.zona_siap_panen > 0
      ? `${p.zona_siap_panen} zona sudah masuk fase siap/harus panen.`
      : "Belum ada zona yang masuk fase siap panen.");

  const f = p.fuzzy_input || {};
  const box = $("fuzzy");
  box.replaceChildren();
  const chip = (label, nilai) => {
    const c = el("span", "chip");
    c.append(el("span", "muted", `${label}: `), el("b", null, nilai));
    box.append(c);
  };
  chip("kuning_pct", fmt(f.kuning_pct, 2));
  chip("coklat_pct", fmt(f.coklat_pct, 2));
  chip("zona_sakit", String(f.zona_sakit ?? "–"));
  chip("psi", fmt(f.psi, 1));
  chip("psi_maks", fmt(f.psi_maks, 1));
  chip("psi_versi", String(f.psi_versi ?? "–"));
  chip("indeks_sehat (legacy = 100 - psi)", fmt(f.indeks_sehat, 1));
  chip("mode", p.mode || "–");
}

// ── Zona perlu perhatian ─────────────────────────────────────────────────────
function renderAlert(p) {
  const box = $("alertList");
  box.replaceChildren();

  const penting = [];
  for (const [id, z] of Object.entries(p.zona)) {
    if (!Number.isFinite(z.coverage)) continue;
    if (z.kesehatan === "sakit") penting.push([0, id, z]);
    else if (z.kesehatan === "waspada") penting.push([1, id, z]);
    else if (z.status === "harus_panen") penting.push([2, id, z]);
  }
  penting.sort((a, b) => a[0] - b[0] || b[2].coverage - a[2].coverage);

  if (!penting.length) {
    box.append(el("li", "muted", "Semua zona sehat dan belum ada yang over-dense. 🎉"));
    return;
  }

  const warna = ["#e74c3c", "#f39c12", "#2ecc71"];
  for (const [prio, id, z] of penting.slice(0, 8)) {
    const li = el("li");
    li.style.borderLeftColor = warna[prio];
    const sebab = z.kesehatan === "sehat"
      ? "coverage tinggi (risiko over-dense)"
      : `kesehatan ${KESEHATAN[z.kesehatan].label}`;
    li.textContent = `${id} — ${sebab} · coverage ${fmt(z.coverage, 1)}% · `
      + `kuning ${fmt(z.pct_kuning, 1)}% · coklat ${fmt(z.pct_coklat, 1)}%`;
    box.append(li);
  }
  if (penting.length > 8) {
    box.append(el("li", "muted", `+ ${penting.length - 8} zona lain perlu diperiksa.`));
  }
}

// ── Snapshot terakhir ────────────────────────────────────────────────────────
function renderSnapshot(p) {
  const img = $("snapshot");
  const note = $("snapshotNote");
  const url = p.snapshot_url;

  if (!url) {
    img.classList.add("hidden");
    img.removeAttribute("src");
    note.textContent = p.mode === "DEMO"
      ? "Mode demo: snapshot tidak tersedia (di produksi diisi snapshot_url dari Firebase Storage)."
      : "Belum ada snapshot (pastikan upload Storage + snapshot_url terisi).";
    return;
  }
  img.onload = () => {
    img.classList.remove("hidden");
    note.textContent = `Diambil ${waktuRelatif(p.timestamp)} · doc ${p.doc_id || "–"}`;
  };
  img.onerror = () => {
    img.classList.add("hidden");
    note.textContent = "Snapshot gagal dimuat (URL kedaluwarsa / aturan Storage menolak akses).";
  };
  img.src = `${url}${url.includes("?") ? "&" : "?"}_=${Date.now()}`;
}

// ── Grafik riwayat coverage (canvas, tanpa library) ──────────────────────────
let titikGrafik = [];

function gambarGrafik(riwayat) {
  const cv = $("chart");
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || 480;
  const H = 160;
  cv.width = Math.round(W * dpr);
  cv.height = Math.round(H * dpr);
  const g = cv.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, W, H);

  const pad = { k: 32, t: 12, b: 22 };
  const plotW = Math.max(10, W - pad.k - 10);
  const plotH = H - pad.t - pad.b;
  const yDari = (v) => pad.t + (1 - Math.min(100, Math.max(0, v)) / 100) * plotH;

  g.font = "10px Segoe UI, sans-serif";
  g.textBaseline = "middle";
  for (const [nilai, warna] of [[25, "#3498db"], [55, "#2ecc71"], [80, "#e74c3c"]]) {
    const y = yDari(nilai);
    g.strokeStyle = "rgba(255,255,255,.10)";
    g.beginPath(); g.moveTo(pad.k, y); g.lineTo(pad.k + plotW, y); g.stroke();
    g.fillStyle = warna;
    g.fillText(`${nilai}%`, 6, y);
  }

  const data = riwayat.filter((p) => Number.isFinite(p.coverage_rata));
  if (data.length < 2) {
    g.fillStyle = "#9aa4cf";
    g.fillText("Belum cukup data untuk grafik.", pad.k + 8, pad.t + plotH / 2);
    titikGrafik = [];
    return;
  }

  const xDari = (i) => pad.k + (i / (data.length - 1)) * plotW;
  titikGrafik = data.map((p, i) => ({ x: xDari(i), y: yDari(p.coverage_rata), p }));

  const grad = g.createLinearGradient(0, pad.t, 0, pad.t + plotH);
  grad.addColorStop(0, "rgba(46,204,113,.45)");
  grad.addColorStop(1, "rgba(46,204,113,.02)");
  g.beginPath();
  g.moveTo(titikGrafik[0].x, pad.t + plotH);
  for (const t of titikGrafik) g.lineTo(t.x, t.y);
  g.lineTo(titikGrafik[titikGrafik.length - 1].x, pad.t + plotH);
  g.closePath();
  g.fillStyle = grad;
  g.fill();

  g.beginPath();
  titikGrafik.forEach((t, i) => (i ? g.lineTo(t.x, t.y) : g.moveTo(t.x, t.y)));
  g.strokeStyle = "#2ecc71";
  g.lineWidth = 2;
  g.stroke();

  g.fillStyle = "#9aa4cf";
  g.textBaseline = "top";
  g.fillText(new Date(data[0].timestamp).toLocaleString("id-ID",
    { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }),
  pad.k, pad.t + plotH + 4);
  const akhir = waktuRelatif(data[data.length - 1].timestamp);
  g.fillText(akhir, pad.k + plotW - g.measureText(akhir).width, pad.t + plotH + 4);
}

$("chart").addEventListener("mousemove", (ev) => {
  const tip = $("chartTip");
  if (!titikGrafik.length) return;
  const rect = $("chart").getBoundingClientRect();
  const x = ev.clientX - rect.left;
  let dekat = titikGrafik[0];
  for (const t of titikGrafik) {
    if (Math.abs(t.x - x) < Math.abs(dekat.x - x)) dekat = t;
  }
  tip.textContent = `${fmt(dekat.p.coverage_rata, 1)}% · `
    + new Date(dekat.p.timestamp).toLocaleString("id-ID");
  tip.style.left = `${dekat.x}px`;
  tip.style.top = `${dekat.y}px`;
  tip.classList.remove("hidden");
});

$("chart").addEventListener("mouseleave", () => $("chartTip").classList.add("hidden"));
window.addEventListener("resize", () => {
  if (window.riwayatSaatIni) gambarGrafik(window.riwayatSaatIni);
});

// ── Orkestrasi render ────────────────────────────────────────────────────────
function tampilkanSemua(payload, riwayat) {
  window.riwayatSaatIni = riwayat;
  const p = payload;

  $("deviceLine").textContent = `perangkat ${p.device_id} · mode ${p.mode}`
    + (p.doc_id ? ` · doc ${p.doc_id}` : "");
  $("lastUpdate").textContent = `update ${waktuRelatif(p.timestamp)}`;

  renderRingkasan(p);
  renderHeatmap(p);
  renderDistribusi(p);
  renderRekomendasi(p);
  renderAlert(p);
  renderSnapshot(p);
  gambarGrafik(riwayat);
}

function kosongkanTampilan(pesan) {
  const kosong = lengkapiPayload({ zona: {}, device_id: "–", mode: "MENUNGGU" });
  tampilkanSemua(kosong, []);
  tampilkanNotice(pesan);
}

// ── Mode DEMO (tanpa Firebase; juga dipakai saat offline) ────────────────────
let jamDemo = null;
let modeDemoAktif = false;

function jalankanDemo(alasan) {
  modeDemoAktif = true;
  if (jamDemo) clearInterval(jamDemo);
  const awal = buatDemo();
  tampilkanSemua(awal.payload, awal.riwayat);
  setBadge("badge-demo", "MODE DEMO");

  if (alasan) {
    tampilkanNotice(`Mode demo aktif — ${alasan}. Angka di layar adalah contoh, `
      + "bukan data Raspberry Pi. Isi firebase-config.js untuk mode live.");
  } else {
    sembunyikanNotice();
  }

  // Segarkan tiap 60 detik agar "update x detik lalu" ikut berjalan.
  jamDemo = setInterval(() => {
    const d = buatDemo();
    tampilkanSemua(d.payload, d.riwayat);
  }, 60000);
}

// ── Mode LIVE: Firestore realtime ────────────────────────────────────────────
async function mulaiLive() {
  const cfg = window.FIREBASE_CONFIG;
  if (!cfg || !cfg.projectId) {
    jalankanDemo("firebase-config.js belum diisi");
    return;
  }

  setBadge("badge-wait", "MENGHUBUNGKAN…");
  let modApp, modFs;
  try {
    [modApp, modFs] = await Promise.all([
      import(`${SDK_URL}/firebase-app.js`),
      import(`${SDK_URL}/firebase-firestore.js`),
    ]);
  } catch (e) {
    console.warn("SDK Firebase gagal dimuat", e);
    jalankanDemo("SDK Firebase tidak bisa dimuat (offline / diblokir)");
    return;
  }

  try {
    const app = modApp.initializeApp(cfg);
    const db = modFs.getFirestore(app);
    const namaKoleksi = window.FIREBASE_COLLECTION || "bed_readings";

    // 144 dokumen terbaru (±24 jam) — cukup untuk kartu terakhir + grafik.
    // orderBy satu field tidak butuh indeks komposit.
    const kueri = modFs.query(
      modFs.collection(db, namaKoleksi),
      modFs.orderBy("timestamp", "desc"),
      modFs.limit(MAKS_RIWAYAT),
    );

    modFs.onSnapshot(kueri, (snap) => {
      if (snap.empty) {
        setBadge("badge-wait", "MENUNGGU DATA");
        kosongkanTampilan(`Belum ada dokumen di collection "${namaKoleksi}". `
          + "Raspberry Pi akan mengirim data setiap ±10 menit setelah service jalan.");
        return;
      }
      const semua = snap.docs.map((d) => lengkapiPayload({ ...d.data(), doc_id: d.id }));
      const terbaru = semua[0];                       // desc -> indeks 0 = terbaru
      const riwayat = semua.slice().reverse();        // kronologis untuk grafik

      tampilkanSemua(terbaru, riwayat);
      sembunyikanNotice();
      setBadge(navigator.onLine ? "badge-live" : "badge-error",
        navigator.onLine ? "LIVE" : "TERPUTUS");
    }, (err) => {
      console.error(err);
      setBadge("badge-error", "GAGAL MEMBACA");
      tampilkanNotice(`Tidak bisa membaca Firestore (${err.code || err.message}). `
        + "Pastikan aturan: match /bed_readings/{doc} { allow read: if true; } "
        + "dan firebase-config.js sesuai project.");
    });
  } catch (e) {
    console.error(e);
    setBadge("badge-error", "GAGAL");
    tampilkanNotice(`Inisialisasi Firebase gagal: ${e.message}`);
  }
}

// ── Inisialisasi halaman ─────────────────────────────────────────────────────
function init() {
  renderLegendaStatus();
  renderLegendaKesehatan();

  $("demoBtn").addEventListener("click", () => jalankanDemo());

  window.addEventListener("online", () => {
    if (modeDemoAktif) return;
    setBadge("badge-live", "LIVE");
  });
  window.addEventListener("offline", () => {
    if (modeDemoAktif) return;
    setBadge("badge-error", "TERPUTUS");
  });

  // Perbarui label "update x menit lalu" tanpa menunggu snapshot baru.
  setInterval(() => {
    if (payloadSaatIni && payloadSaatIni.doc_id) {
      $("lastUpdate").textContent = `update ${waktuRelatif(payloadSaatIni.timestamp)}`;
    }
  }, 30000);

  const paksaDemo = new URLSearchParams(location.search).get("demo") === "1";
  if (paksaDemo) jalankanDemo("dipaksa lewat ?demo=1");
  else mulaiLive();
}

init();






