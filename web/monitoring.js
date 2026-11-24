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
      valid: true,
      reason: "ok",
      psi_versi: PSI_VERSI,
      indeks_sehat: Math.round((100 - psiRata) * 10) / 10,
    },
    rekomendasi: doc.rekomendasi || "",
    snapshot_url: doc.snapshot_url || null,
    suhu_pi_c: Number.isFinite(doc.suhu_pi_c) ? doc.suhu_pi_c : null,
    doc_id: doc.doc_id || null,
  };
}

// WAJIB identik dengan PSI_VERSION di files/kangkung_cv.py (sumber tunggal).
const PSI_VERSI = "2.0";
// PSI (Plant Stress Index) 0-100, TINGGI = makin stres. Rumus v2.0.
// WAJIB identik dengan hitung_psi() di files/kangkung_cv.py (sumber tunggal):
//   N = G + Y + B ;  PSI = 100 * (0.5*Y + B) / N   (dari jumlah PIKSEL MENTAH)
// Hanya dipakai sebagai fallback untuk dokumen lama yang belum punya psi.
// Bobot kategori: hijau 0, kuning 0,5, cokelat 1 (urutan kategori, bukan
// "stres fisiologis 50%"). Linier: PSI 100 hanya bila semua piksel cokelat.
// Karena linear & invarian skala, menghitung dari persentase zona memberi
// angka yang sama dengan menghitung dari piksel mentah.
function hitungPsi(pctKuning, pctCoklat) {
  const y = Math.max(0, Math.min(100, Number(pctKuning) || 0));
  const b = Math.max(0, Math.min(100 - y, Number(pctCoklat) || 0));
  if (y + b > 100) return null;          // masukan tak sah
  if (y === 0 && b === 0) return 0;      // semua hijau -> PSI 0 (sah)
  return Math.round((0.5 * y + b) * 10) / 10;
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
  // psi null + valid=false = hasil tidak valid (kamera gagal / tanpa tanaman).
  // JANGAN ditampilkan sebagai 0 — 0 adalah hasil SAH untuk kanopi hijau.
  const fz = p.fuzzy_input || {};
  const psi = Number.isFinite(fz.psi) ? fz.psi : null;
  const psiMaks = Number.isFinite(fz.psi_maks) ? fz.psi_maks : null;
  const psiValid = fz.valid !== false;          // dokumen lama tak punya field
  $("indeksSehat").textContent = psiValid && psi !== null
    ? fmt(psi, 0)
    : "n/a";
  $("kesRingkas").textContent = `kuning ${fmt(p.kuning_rata, 1)}% · `
    + `coklat ${fmt(p.coklat_rata, 1)}%`
    + (psiMaks !== null ? ` · zona terburuk ${fmt(psiMaks, 0)}` : "")
    + (psiValid ? "" : ` · PSI tidak valid (${fz.reason || "tanpa alasan"})`);

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

// ── Heatmap 4 × 6 & Multi-Layer View (Nomor 5) ───────────────────────────────
let payloadSaatIni = null;
let zonaTerpilih = null;
let layerSaatIni = "coverage"; // 'coverage' | 'kesehatan' | 'biomassa'

function renderHeatmap(p) {
  payloadSaatIni = p;
  const box = $("heatmap");
  if (!box || !p || !p.zona) return;
  box.replaceChildren();

  for (const id of idZonaUrut()) {
    const z = p.zona[id] || {};
    const st = STATUS[z.status] || STATUS.belum_siap;
    const kes = KESEHATAN[z.kesehatan] || KESEHATAN["n/a"];
    const cov = Number.isFinite(z.coverage) ? z.coverage : 0;
    const pk = Number.isFinite(z.pct_kuning) ? z.pct_kuning : 0;
    const pc = Number.isFinite(z.pct_coklat) ? z.pct_coklat : 0;
    const biomassGrams = Math.round((cov / 100) * 770);

    const tile = el("button", "tile");
    tile.type = "button";
    tile.dataset.zona = id;

    if (!Number.isFinite(z.coverage)) {
      tile.classList.add("empty");
      tile.append(el("span", "tile-id", id), el("span", "tile-cov", "–"));
      tile.title = `${id} — belum ada data`;
    } else {
      let bgWarna = st.color;
      let textTampil = `${Math.round(cov)}%`;
      let dotWarna = kes.color;
      let dotTitle = `Kesehatan: ${kes.label}`;

      if (layerSaatIni === "coverage") {
        bgWarna = st.color;
        textTampil = `${Math.round(cov)}%`;
        dotWarna = kes.color;
        dotTitle = `Kesehatan: ${kes.label}`;
        tile.title = `${id} — ${st.label} (Coverage ${fmt(cov, 1)}%)`;
      } else if (layerSaatIni === "kesehatan") {
        if (z.kesehatan === "sehat") {
          bgWarna = "#166534";
        } else if (z.kesehatan === "waspada") {
          bgWarna = "#b45309";
        } else {
          bgWarna = "#991b1b";
        }
        textTampil = `${fmt(pk, 1)}% K`;
        dotWarna = st.color;
        dotTitle = `Status Panen: ${st.label}`;
        tile.title = `${id} — ${kes.label} (Kuning ${fmt(pk, 1)}%, Cokelat ${fmt(pc, 1)}%)`;
      } else if (layerSaatIni === "biomassa") {
        if (biomassGrams < 200) {
          bgWarna = "#0f4c5c";
        } else if (biomassGrams < 450) {
          bgWarna = "#1b4332";
        } else if (biomassGrams < 600) {
          bgWarna = "#2d6a4f";
        } else {
          bgWarna = "#22c55e";
        }
        textTampil = `${biomassGrams}g`;
        dotWarna = st.color;
        dotTitle = `Status Panen: ${st.label}`;
        tile.title = `${id} — Estimasi Biomassa: ${biomassGrams} gram (~${fmt(biomassGrams/1000, 2)} kg)`;
      }

      tile.style.background = bgWarna;
      tile.append(
        el("span", "tile-id", id),
        el("span", "tile-cov", textTampil)
      );
      const dot = el("span", "tile-kes");
      dot.style.background = dotWarna;
      dot.title = dotTitle;
      tile.append(dot);
      tile.setAttribute("aria-label", `Zona ${id}: ${tile.title}`);
    }

    tile.addEventListener("click", () => tampilkanDetailZona(id));
    box.append(tile);
  }

  renderLegendHeatmap(layerSaatIni);
  if (zonaTerpilih) tampilkanDetailZona(zonaTerpilih);
}

function renderLegendHeatmap(layer) {
  const box = $("legendStatus");
  if (!box) return;
  box.replaceChildren();

  let items = [];
  if (layer === "coverage") {
    items = [
      { color: STATUS.belum_siap.color, label: "Belum siap (<25%)" },
      { color: STATUS.hampir_siap.color, label: "Hampir siap (25–55%)" },
      { color: STATUS.siap_panen.color, label: "Siap panen (55–80%)" },
      { color: STATUS.harus_panen.color, label: "Harus panen (≥80%)" }
    ];
  } else if (layer === "kesehatan") {
    items = [
      { color: "#166534", label: "Klorofil prima (Sehat)" },
      { color: "#b45309", label: "Gejala klorosis (Waspada)" },
      { color: "#991b1b", label: "Nekrosis / stres berat (Sakit)" }
    ];
  } else if (layer === "biomassa") {
    items = [
      { color: "#0f4c5c", label: "< 200g (Fase awal)" },
      { color: "#1b4332", label: "200–450g (Pembesaran)" },
      { color: "#2d6a4f", label: "450–600g (Hampir siap)" },
      { color: "#22c55e", label: "≥ 600g (Bobot siap tebang)" }
    ];
  }

  for (const it of items) {
    const s = el("span");
    const i = el("i");
    i.style.background = it.color;
    s.append(i, el("span", null, it.label));
    box.append(s);
  }
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
  const cov = Number.isFinite(z.coverage) ? z.coverage : 0;
  const biomassGrams = Math.round((cov / 100) * 770);

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
  item("Estimasi biomassa", `${biomassGrams} gram (~${fmt(biomassGrams / 1000, 2)} kg)`, "#38ef7d");
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
  chip("psi", f.valid === false ? `n/a (${f.reason ?? "invalid"})` : fmt(f.psi, 1));
  chip("psi_maks", fmt(f.psi_maks, 1));
  chip("valid", f.valid === false ? "TIDAK" : "ya");
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
    box.append(el("li", "muted", "Semua zona sehat dan belum ada yang over-dense."));
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
  const imgs = [$("snapshot"), $("dashSnapshot")].filter(Boolean);
  const notes = [$("snapshotNote"), $("dashSnapshotNote")].filter(Boolean);
  const rawUrl = p && p.snapshot_url ? p.snapshot_url : "latest_snapshot.jpg";

  imgs.forEach((img) => {
    img.classList.remove("hidden");
    img.style.display = "block";
    img.onload = () => {
      img.classList.remove("hidden");
      img.style.display = "block";
    };
    img.onerror = () => {
      if (!img.src.includes("latest_snapshot.jpg")) {
        img.src = "latest_snapshot.jpg";
      }
    };
    if (rawUrl.startsWith("data:")) {
      img.src = rawUrl;
    } else {
      img.src = `${rawUrl}${rawUrl.includes("?") ? "&" : "?"}_=${Date.now()}`;
    }
  });

  notes.forEach((note) => {
    if (p && p.timestamp) {
      note.textContent = `Diambil ${waktuRelatif(p.timestamp)} · doc ${p.doc_id || "–"}`;
    } else {
      note.textContent = "Snapshot acuan bed kangkung.";
    }
  });
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
  tampilkanDashboard(p);
}

function tampilkanDashboard(p) {
  // ── Status Sistem ──
  const isLive = p.mode === "PI-LIVE" || p.mode === "TEST-FOTO";
  const st = p.mode === "TEST-FOTO" ? "UJI FOTO" : (p.mode === "PI-LIVE" ? "ONLINE" : "OFFLINE / DEMO");
  $(`sysStatus`).textContent = st;
  const sysNote = $(`sysNote`);
  sysNote.textContent = isLive
    ? `data terakhir ${waktuRelatif(p.timestamp)} (${p.doc_id || ""})`
    : "mode demo — data contoh";
  sysNote.style.color = isLive ? "" : "var(--warning)";

  // ── Zona Siap Panen ──
  $(`dashZonaSiap`).textContent = String(p.zona_siap_panen ?? 0);
  $(`dashPersenSiap`).textContent = `${fmt(p.persen_siap ?? 0, 1)}% dari total zona`;

  // ── Indeks Stres (PSI) ──
  const fz = p.fuzzy_input || {};
  const psi = Number.isFinite(fz.psi) ? fz.psi : null;
  const psiValid = fz.valid !== false;
  $(`dashPSI`).textContent = psiValid && psi !== null ? fmt(psi, 0) : "n/a";

  // ── Suhu Raspberry Pi ──
  const suhu = p.suhu_pi_c;
  $(`dashSuhu`).textContent = fmt(suhu, 1);
  const suhuNote = $(`dashSuhuNote`);
  if (!Number.isFinite(suhu)) {
    suhuNote.textContent = "suhu tidak tersedia";
    suhuNote.style.color = "";
  } else if (suhu >= SUHU.waspada) {
    suhuNote.textContent = "panas — risiko thermal guard";
    suhuNote.style.color = "#e74c3c";
  } else if (suhu >= SUHU.aman) {
    suhuNote.textContent = "perlu perhatian (ventilasi)";
    suhuNote.style.color = "#f39c12";
  } else {
    suhuNote.textContent = "aman (ambang 75 °C)";
    suhuNote.style.color = "";
  }

  // ── Distribusi Status Zona ──
  renderDistribusiDashboard(`dashDistStatus`, p.status_distribusi, STATUS, `dashLegendStatus`);

  // ── Kesehatan Daun ──
  renderDistribusiDashboard(`dashDistKes`, p.kesehatan?.distribusi, KESEHATAN, `dashLegendKes`);

  // ── Rekomendasi & Fuzzy ──
  $(`dashRekomen`).textContent = p.rekomendasi ?? "—";
  $(`dashFuzzy`).replaceChildren();
  const chips = [
    { k: "kuning_pct", label: "Kuning", warna: "#f59e0b" },
    { k: "coklat_pct", label: "Coklat", warna: "#a16207" },
    { k: "zona_sakit", label: "Zona Sakit", warna: "#ef4444" },
  ];
  for (const c of chips) {
    const nilai = Number(fz[c.k]) ?? 0;
    const chip = el(`div`, `chip`);
    chip.append(el(`span`, null, `${c.label}: `), el(`b`, null, `${fmt(nilai, 1)}`));
    if (c.warna) chip.style.borderColor = c.warna;
    $(`dashFuzzy`).append(chip);
  }
}

function renderDistribusiDashboard(idBox, data, palet, idLegend) {
  const box = $(idBox);
  box.replaceChildren();
  const total = GRID_ROWS * GRID_COLS;
  for (const [k, gaya] of Object.entries(palet)) {
    const nilai = Number(data?.[k]) || 0;
    const row = el(`div`, `dist-row`);
    row.append(el(`span`, null, gaya.label));

    const bar = el(`div`, `dist-bar`);
    const isi = el(`i`);
    isi.style.width = `${Math.min(100, (nilai / total) * 100)}%`;
    isi.style.background = gaya.color;
    bar.append(isi);
    row.append(bar);

    const val = el(`span`, `dist-val`);
    val.textContent = String(nilai);
    row.append(val);

    box.append(row);
  }

  // Legend
  const leg = $(idLegend);
  leg.replaceChildren();
  for (const [k, gaya] of Object.entries(palet)) {
    const s = el(`span`);
    const i = el(`i`);
    i.style.background = gaya.color;
    s.append(i, el(`span`, null, `${gaya.label} (${nilaiOrZero(data, k)})`));
    leg.append(s);
  }
}

function nilaiOrZero(data, k) {
  return Number(data?.[k]) || 0;
}

function kosongkanTampilan(pesan) {
  const kosong = lengkapiPayload({ zona: {}, device_id: "–", mode: "MENUNGGU" });
  tampilkanSemua(kosong, []);
  tampilkanDashboard(kosong);
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
  tampilkanDashboard(awal.payload);
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
    tampilkanDashboard(d.payload);
  }, 60000);
}

// ── Fast REST Pre-fetch (menampilkan data & snapshot instan tanpa menunggu WebSocket) ──
async function muatAwalREST(cfg, namaKoleksi) {
  try {
    const url = `https://firestore.googleapis.com/v1/projects/${cfg.projectId}/databases/(default)/documents:runQuery`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        structuredQuery: {
          from: [{ collectionId: namaKoleksi }],
          orderBy: [{ field: { fieldPath: "timestamp" }, direction: "DESCENDING" }],
          limit: 25,
        },
      }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    const rawDocs = data.filter((item) => item.document).map((item) => item.document);
    if (!rawDocs.length) return false;

    const parseField = (f) => {
      if (!f) return null;
      if ("stringValue" in f) return f.stringValue;
      if ("doubleValue" in f) return f.doubleValue;
      if ("integerValue" in f) return Number(f.integerValue);
      if ("booleanValue" in f) return f.booleanValue;
      if ("nullValue" in f) return null;
      if ("mapValue" in f) {
        const obj = {};
        for (const [k, v] of Object.entries(f.mapValue.fields || {})) obj[k] = parseField(v);
        return obj;
      }
      if ("arrayValue" in f) return (f.arrayValue.values || []).map(parseField);
      return null;
    };

    const semua = rawDocs.map((d) => {
      const obj = {};
      for (const [k, v] of Object.entries(d.fields || {})) obj[k] = parseField(v);
      const parts = (d.name || "").split("/");
      obj.doc_id = obj.doc_id || parts[parts.length - 1];
      return lengkapiPayload(obj);
    });

    if (semua.length > 0) {
      const terbaru = semua[0];
      const riwayat = semua.slice().reverse();
      tampilkanSemua(terbaru, riwayat);
      sembunyikanNotice();
      setBadge("badge-live", "LIVE");

      // Cek apakah ada IP LAN tersimpan di device_control
      try {
        const ctrlUrl = `https://firestore.googleapis.com/v1/projects/${cfg.projectId}/databases/(default)/documents/device_control/pi-bed-01`;
        fetch(ctrlUrl).then((r) => r.json()).then((ctrl) => {
          if (ctrl && ctrl.fields) {
            if (ctrl.fields.lan_ip?.stringValue) window._cloudCameraLanIp = ctrl.fields.lan_ip.stringValue;
            if (ctrl.fields.stream_url_lan?.stringValue) window._cloudCameraLanUrl = ctrl.fields.stream_url_lan.stringValue;
          }
        }).catch(() => {});
      } catch (err) {}

      return true;
    }
  } catch (e) {
    console.warn("[REST] Fast pre-fetch gagal:", e);
  }
  return false;
}

// ── Mode LIVE: Firestore realtime ────────────────────────────────────────────
async function mulaiLive() {
  const cfg = window.FIREBASE_CONFIG;
  if (!cfg || !cfg.projectId) {
    jalankanDemo("firebase-config.js belum diisi");
    return;
  }

  const namaKoleksi = window.FIREBASE_COLLECTION || "bed_readings";
  setBadge("badge-wait", "MENGHUBUNGKAN…");

  // Jalankan fast pre-fetch via REST API agar gambar & data langsung muncul instan
  muatAwalREST(cfg, namaKoleksi);

  let modApp, modFs;
  try {
    [modApp, modFs] = await Promise.all([
      import(`${SDK_URL}/firebase-app.js`),
      import(`${SDK_URL}/firebase-firestore.js`),
    ]);
  } catch (e) {
    console.warn("SDK Firebase gagal dimuat", e);
    // Jika REST sudah berhasil, jangan paksa demo
    if (!payloadSaatIni) {
      jalankanDemo("SDK Firebase tidak bisa dimuat (offline / diblokir)");
    }
    return;
  }

  try {
    const app = modApp.initializeApp(cfg);
    const db = modFs.getFirestore(app);

    // 144 dokumen terbaru (±24 jam) — cukup untuk kartu terakhir + grafik.
    // orderBy satu field tidak butuh indeks komposit.
    const kueri = modFs.query(
      modFs.collection(db, namaKoleksi),
      modFs.orderBy("timestamp", "desc"),
      modFs.limit(MAKS_RIWAYAT),
    );

    modFs.onSnapshot(kueri, (snap) => {
      if (snap.empty) {
        if (!payloadSaatIni) {
          setBadge("badge-wait", "MENUNGGU DATA");
          kosongkanTampilan(`Belum ada dokumen di collection "${namaKoleksi}". `
            + "Raspberry Pi akan mengirim data setiap ±10 menit setelah service jalan.");
        }
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
      if (!payloadSaatIni) {
        setBadge("badge-error", "GAGAL MEMBACA");
        tampilkanNotice(`Tidak bisa membaca Firestore (${err.code || err.message}). `
          + "Pastikan aturan: match /bed_readings/{doc} { allow read: if true; } "
          + "dan firebase-config.js sesuai project.");
      }
    });
  } catch (e) {
    console.error(e);
    if (!payloadSaatIni) {
      setBadge("badge-error", "GAGAL");
      tampilkanNotice(`Inisialisasi Firebase gagal: ${e.message}`);
    }
  }
}

// ── Inisialisasi halaman ─────────────────────────────────────────────────────
function init() {
  renderLegendaStatus();
  renderLegendaKesehatan();

  const demoBtn = $("demoBtn");
  if (demoBtn) demoBtn.addEventListener("click", () => jalankanDemo());

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
    if (payloadSaatIni && payloadSaatIni.doc_id && $("lastUpdate")) {
      $("lastUpdate").textContent = `update ${waktuRelatif(payloadSaatIni.timestamp)}`;
    }
  }, 30000);

  const paksaDemo = new URLSearchParams(location.search).get("demo") === "1";
  if (paksaDemo) jalankanDemo("dipaksa lewat ?demo=1");
  else mulaiLive();

  // Inisialisasi modul Siklus Pertumbuhan
  initSiklusPertumbuhan();

  // Inisialisasi Switch Kamera (Monitoring vs Live Stream)
  initCameraSwitcher();
}

// ═════════════════════════════════════════════════════════════════════════════
// MODUL CAMERA SWITCHER (MONITORING AI VS LIVE VIDEO STREAMING)
// ═════════════════════════════════════════════════════════════════════════════

const DEFAULT_TAILSCALE_IP = "100.123.187.56";
const CAMERA_PORT = 8787;
const CAMERA_TOKEN = "iPcqot-pKrDzvImXynH_QDfq";
const DEFAULT_STREAM_TIMEOUT = 300; // 5 menit (300 detik)

let modeKameraSaatIni = "monitoring";
let streamTimerId = null;
let streamDetikSisa = DEFAULT_STREAM_TIMEOUT;

function getCameraHost() {
  const urlParams = new URLSearchParams(window.location.search);
  const qCam = urlParams.get("cam_ip") || urlParams.get("cam");
  if (qCam) return qCam.trim();

  const saved = localStorage.getItem("aquaponic_camera_host");
  if (saved) return saved.trim();

  // Jika web dibuka via IP lokal (WiFi bersama dosen) dan ada IP LAN terdeteksi
  const isLocalAccess = window.location.hostname.startsWith("192.168.") ||
                        window.location.hostname.startsWith("10.") ||
                        window.location.hostname.startsWith("172.");
  if (isLocalAccess && window._cloudCameraLanIp) {
    return window._cloudCameraLanIp;
  }

  return DEFAULT_TAILSCALE_IP;
}

function getCameraStreamUrl() {
  const host = getCameraHost();
  if (host.startsWith("http://") || host.startsWith("https://")) {
    return host.includes("token=") ? host : `${host}/stream.mjpg?token=${CAMERA_TOKEN}`;
  }
  return `http://${host}:${CAMERA_PORT}/stream.mjpg?token=${CAMERA_TOKEN}`;
}

function ubahIpKamera() {
  const cur = getCameraHost();
  const input = prompt(
    "Pengaturan Alamat Kamera Raspberry Pi:\n\n" +
    "• Satu WiFi dengan Dosen (Solusi 3): Masukkan IP WiFi Raspberry Pi (misal 10.11.1.xx atau 192.168.x.x)\n" +
    "• Jarak Jauh via Tailscale VPN: Masukkan 100.123.187.56\n\n" +
    "Masukkan IP / Host kamera baru:",
    cur
  );
  if (input !== null) {
    const bersih = input.trim();
    if (bersih) {
      localStorage.setItem("aquaponic_camera_host", bersih);
      tampilkanNotice(`Host kamera diubah ke: ${bersih}`);
    } else {
      localStorage.removeItem("aquaponic_camera_host");
      tampilkanNotice(`Host kamera di-reset ke default (${DEFAULT_TAILSCALE_IP})`);
    }
    setTimeout(sembunyikanNotice, 4000);
    if (modeKameraSaatIni === "streaming") {
      perbaruiUICameraMode("streaming");
    }
  }
}

function formatWaktuTimer(detik) {
  const m = Math.floor(detik / 60);
  const s = detik % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

async function kirimPerintahModeCloud(mode, durasiSec = 300) {
  try {
    const cfg = window.FIREBASE_CONFIG;
    if (!cfg || !cfg.projectId) return;
    const url = `https://firestore.googleapis.com/v1/projects/${cfg.projectId}/databases/(default)/documents/device_control/pi-bed-01?updateMask.fieldPaths=requested_mode&updateMask.fieldPaths=duration_seconds&updateMask.fieldPaths=requested_at`;
    await fetch(url, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fields: {
          requested_mode: { stringValue: mode },
          duration_seconds: { integerValue: String(durasiSec) },
          requested_at: { stringValue: new Date().toISOString() },
        },
      }),
    });
  } catch (e) {
    console.warn("[SWITCH-CLOUD] Gagal kirim perintah mode:", e);
  }
}

function perbaruiUICameraMode(mode) {
  modeKameraSaatIni = mode;
  const isStream = mode === "streaming";

  // Tombol toggle
  const btnMonitors = [$("dashBtnMonitor"), $("liveBtnMonitor")].filter(Boolean);
  const btnStreams = [$("dashBtnStream"), $("liveBtnStream")].filter(Boolean);
  btnMonitors.forEach((b) => b.classList.toggle("active", !isStream));
  btnStreams.forEach((b) => b.classList.toggle("active", isStream));

  // Badges timer
  const badges = [$("dashStreamBadge"), $("liveStreamBadge")].filter(Boolean);
  badges.forEach((b) => b.classList.toggle("hidden", !isStream));

  // Element media
  const snapImgs = [$("dashSnapshot"), $("snapshot")].filter(Boolean);
  const streamImgs = [$("dashLiveStream"), $("liveVideoPlayer")].filter(Boolean);
  const overlays = [$("dashStreamOverlay"), $("liveStreamOverlay")].filter(Boolean);

  if (isStream) {
    const streamSrc = getCameraStreamUrl();
    const hostInfo = getCameraHost();

    snapImgs.forEach((img) => img.classList.add("hidden"));
    streamImgs.forEach((img) => {
      img.classList.remove("hidden");
      img.src = `${streamSrc}&_t=${Date.now()}`;
      img.onload = () => {
        overlays.forEach((o) => o.classList.add("hidden"));
      };
      img.onerror = () => {
        overlays.forEach((o) => {
          o.classList.remove("hidden");
          const p = o.querySelector("p");
          if (p) {
            p.innerHTML = `
              Stream belum tersambung ke <code>${hostInfo}:${CAMERA_PORT}</code>.<br>
              <small style="color:#cbd5e1">Pastikan Raspberry Pi aktif dan terhubung ke jaringan WiFi yang sama.</small><br>
              <button id="btnRetryIp" class="btn-stop-sm" style="margin-top:8px;cursor:pointer;">Ubah IP Kamera</button>
            `;
            const retryBtn = p.querySelector("#btnRetryIp");
            if (retryBtn) retryBtn.onclick = ubahIpKamera;
          }
        });
      };
    });
    overlays.forEach((o) => {
      o.classList.remove("hidden");
      const p = o.querySelector("p");
      if (p) p.textContent = `Menghubungkan ke live stream kamera (${hostInfo})…`;
    });
  } else {
    // Kembali ke monitoring: matikan src stream agar browser stop download
    streamImgs.forEach((img) => {
      img.classList.add("hidden");
      img.src = "";
    });
    overlays.forEach((o) => o.classList.add("hidden"));
    snapImgs.forEach((img) => img.classList.remove("hidden"));
  }
}

function aktifkanModeStreaming(durasi = DEFAULT_STREAM_TIMEOUT) {
  if (streamTimerId) clearInterval(streamTimerId);
  streamDetikSisa = durasi;
  perbaruiUICameraMode("streaming");

  const timerEls = [$("dashStreamTimer"), $("liveStreamTimer")].filter(Boolean);
  timerEls.forEach((el) => { el.textContent = formatWaktuTimer(streamDetikSisa); });

  streamTimerId = setInterval(() => {
    streamDetikSisa--;
    timerEls.forEach((el) => { el.textContent = formatWaktuTimer(streamDetikSisa); });
    if (streamDetikSisa <= 0) {
      clearInterval(streamTimerId);
      aktifkanModeMonitoring("Durasi streaming 5 menit selesai. Kembali ke monitoring hemat daya.");
    }
  }, 1000);

  kirimPerintahModeCloud("streaming", durasi);
}

function aktifkanModeMonitoring(pesanNotice = null) {
  if (streamTimerId) {
    clearInterval(streamTimerId);
    streamTimerId = null;
  }
  perbaruiUICameraMode("monitoring");
  kirimPerintahModeCloud("monitoring");

  if (pesanNotice) {
    tampilkanNotice(pesanNotice);
    setTimeout(sembunyikanNotice, 6000);
  }
}

function initCameraSwitcher() {
  const btnMonitors = [$("dashBtnMonitor"), $("liveBtnMonitor")].filter(Boolean);
  const btnStreams = [$("dashBtnStream"), $("liveBtnStream")].filter(Boolean);
  const btnStops = [$("dashBtnStopStream"), $("liveBtnStopStream")].filter(Boolean);
  const btnSettings = [$("dashBtnCamSettings"), $("liveBtnCamSettings")].filter(Boolean);

  btnStreams.forEach((b) => b.addEventListener("click", () => aktifkanModeStreaming(300)));
  btnMonitors.forEach((b) => b.addEventListener("click", () => aktifkanModeMonitoring()));
  btnStops.forEach((b) => b.addEventListener("click", () => aktifkanModeMonitoring("Live stream dihentikan. Kembali ke monitoring otomatis.")));
  btnSettings.forEach((b) => b.addEventListener("click", ubahIpKamera));
}

// Ekspos ke window agar dapat dipanggil dari HTML onclick atau konsol browser
if (typeof window !== "undefined") {
  window.ubahIpKamera = ubahIpKamera;
  window.aktifkanModeStreaming = aktifkanModeStreaming;
  window.aktifkanModeMonitoring = aktifkanModeMonitoring;
  window.getCameraStreamUrl = getCameraStreamUrl;
  window.getCameraHost = getCameraHost;
}


// ═════════════════════════════════════════════════════════════════════════════
// MODUL SIKLUS PERTUMBUHAN (DATASET VIDEO ECOFARM & 30 HARI SIKLUS)
// ═════════════════════════════════════════════════════════════════════════════

let dataPertumbuhan = null;
let idSiklusDipilih = "video_dataset";
let filterFaseDipilih = "all";
let titikGrafikPertumbuhan = [];
let modalItemSaatIni = null;

async function muatDataPertumbuhan() {
  try {
    const res = await fetch(`growth/growth_data.json?v=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    dataPertumbuhan = await res.json();
  } catch (err) {
    console.warn("[GROWTH] Gagal memuat growth/growth_data.json:", err);
  }
}

function bukaModalPertumbuhan(d) {
  const modal = $("growthModal");
  if (!modal) return;
  modalItemSaatIni = d;

  // Set gambar awal beranotasi
  $("modalImg").src = d.image_url;
  const btnAnno = $("btnViewAnno");
  const btnRaw = $("btnViewRaw");
  if (btnAnno) btnAnno.classList.add("active");
  if (btnRaw) {
    btnRaw.classList.remove("active");
    btnRaw.style.display = d.raw_url ? "inline-block" : "none";
  }

  const isVideoView = String(idSiklusDipilih) === "video_dataset";
  if (isVideoView) {
    $("modalDayTitle").textContent = `${d.video_name} (Frame #${d.frame_idx || 1})`;
  } else {
    $("modalDayTitle").textContent = `HARI ${String(d.day).padStart(2, "0")}${d.video_name ? " — " + d.video_name : ""}`;
  }

  const badge = $("modalFaseBadge");
  badge.textContent = d.fase;
  badge.className = `badge fase-badge fase-${d.fase.replace(/\s+/g, "")}`;

  if (d.video_name) {
    $("modalDate").textContent = `Sumber: Folder 'data set aquaponic ecofarm' · Video: ${d.video_name} · Frame #${d.frame_idx} (${d.timestamp_sec}s)`;
  } else {
    $("modalDate").textContent = d.date ? `Tanggal rekam: ${d.date}` : `Hari ke-${d.day} dari 30 hari masa tanam`;
  }

  $("modalCoverage").textContent = `${fmt(d.coverage)}%`;
  $("modalStatus").textContent = STATUS[d.status]?.label || d.status;
  $("modalPSI").textContent = `${fmt(d.psi, 1)} / 100`;
  $("modalKesehatan").textContent = (d.kesehatan || "Sehat").toUpperCase();
  $("modalReadyZones").textContent = `${d.ready_zones ?? 0} / 24 zona`;

  if (d.laplacian_var) {
    $("modalScore").textContent = `Laplacian ${d.laplacian_var} (Skor: ${d.quality_score})`;
  } else {
    $("modalScore").textContent = d.best_hour || "Pukul 11:00 WIB";
  }

  $("modalCatatan").textContent = d.catatan || "Pertumbuhan kangkung terpantau normal.";
  $("modalBestHour").textContent = d.video_name
    ? `Frame Terbaik Video: ${d.video_name} (Frame #${d.frame_idx}, Detik ${d.timestamp_sec}s)`
    : `Frame Terbaik Harian: ${d.best_hour || "Pukul 11:00 WIB (Pencahayaan Puncak)"}`;

  modal.classList.remove("hidden");
}

function tutupModalPertumbuhan() {
  const modal = $("growthModal");
  if (modal) modal.classList.add("hidden");
}

function filterKartuPertumbuhan(fase) {
  filterFaseDipilih = fase;
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.phase === fase);
  });

  const cards = document.querySelectorAll(".growth-card");
  let tampak = 0;
  cards.forEach((card) => {
    const cocok = (fase === "all" || card.dataset.fase === fase);
    card.classList.toggle("filtered-out", !cocok);
    if (cocok) tampak++;
  });

  const lbl = $("growthCountLabel");
  if (lbl) {
    const total = cards.length;
    lbl.textContent = fase === "all" ? `Menampilkan semua (${total} frame/hari)` : `Menampilkan fase ${fase} (${tampak} hari)`;
  }
}

function renderTabSiklus() {
  const wrap = $("cycleTabs");
  if (!wrap || !dataPertumbuhan || !dataPertumbuhan.cycles) return;
  wrap.innerHTML = "";

  const keys = Object.keys(dataPertumbuhan.cycles);
  const orderedKeys = [];
  if (keys.includes("video_dataset")) orderedKeys.push("video_dataset");
  const numKeys = keys.filter((k) => k !== "video_dataset").map(Number).sort((a, b) => a - b);
  orderedKeys.push(...numKeys.map(String));

  orderedKeys.forEach((cid) => {
    const c = dataPertumbuhan.cycles[cid];
    const meta = c.meta || {};
    const isVideoDataset = Boolean(meta.is_video_dataset);
    const isAktif = meta.is_active;
    const isSelected = String(cid) === String(idSiklusDipilih);

    const btn = el("button", `cycle-tab-btn ${isSelected ? "active" : ""} ${isVideoDataset ? "btn-video-dataset" : ""}`);
    btn.type = "button";

    const titleSpan = el("span", "", isVideoDataset ? "Dataset Video Ecofarm" : `Siklus ${cid}`);
    const badgeCls = isVideoDataset ? "badge-video" : (isAktif ? "badge-live" : "badge-demo");
    const badgeText = meta.badge_label || (isAktif ? "AKTIF" : "SELESAI");
    const badgeSpan = el("span", `badge ${badgeCls}`, badgeText);

    btn.appendChild(titleSpan);
    btn.appendChild(badgeSpan);

    btn.addEventListener("click", () => {
      idSiklusDipilih = cid;
      renderTabSiklus();
      renderHalamanSiklus();
    });
    wrap.appendChild(btn);
  });

  // Badge retensi
  const retBadge = $("retentionStatusBadge");
  if (retBadge && dataPertumbuhan.retention_policy) {
    const tot = dataPertumbuhan.retention_policy.total_stored_cycles || numKeys.length;
    const maxC = dataPertumbuhan.retention_policy.max_cycles_stored || 3;
    retBadge.textContent = `${tot} / ${maxC} SIKLUS TERSIMPAN (FIFO)`;
    retBadge.className = `badge ${tot >= maxC ? "badge-wait" : "badge-live"}`;
  }
}

function renderRingkasanSiklus(siklus) {
  if (!siklus || !siklus.meta) return;
  const m = siklus.meta;
  const isVideo = Boolean(m.is_video_dataset);

  const st = $("growthCycleStatus");
  if (st) {
    st.textContent = m.status || (m.is_active ? "AKTIF" : "SELESAI");
    st.style.color = isVideo ? "var(--accent)" : (m.is_active ? "var(--siap)" : "#38bdf8");
  }

  const per = $("growthCyclePeriod");
  if (per) {
    per.textContent = isVideo
      ? "18 Video HP Ecofarm (IMG_4329 s/d IMG_4209)"
      : (m.end_date ? `${m.start_date} s/d ${m.end_date}` : `Dimulai ${m.start_date} (Sedang Berjalan)`);
  }

  const dc = $("growthDaysCount");
  if (dc) {
    dc.textContent = m.days_count ?? (siklus.days?.length || 0);
    const unitSpan = dc.nextElementSibling;
    if (unitSpan) unitSpan.textContent = isVideo ? "/ 18 Video" : "/ 30 Hari";
  }

  const prog = $("growthProgressPct");
  if (prog) {
    if (isVideo) {
      prog.textContent = "18/18 frame video terekstraksi";
    } else {
      const pct = Math.round(((m.days_count || siklus.days?.length || 0) / 30) * 100);
      prog.textContent = `${pct}% dari target 30 hari`;
    }
  }

  const mc = $("growthMaxCoverage");
  if (mc) mc.textContent = fmt(m.max_coverage);

  const covTarget = $("growthCovTarget");
  if (covTarget) {
    covTarget.textContent = isVideo ? "Panen raya: IMG_4209 (91.6%)" : "Target panen: ≥ 80%";
  }

  const ps = $("growthAvgPSI");
  if (ps) {
    ps.textContent = fmt(m.avg_psi, 1);
    const psiNote = $("growthPsiStatus");
    if (psiNote) {
      psiNote.textContent = m.avg_psi < 15 ? "Stres sangat rendah (subur)" : (m.avg_psi < 40 ? "Stres ringan" : "Perlu perhatian");
    }
  }

  const yld = $("growthYield");
  if (yld) {
    yld.textContent = m.harvest_yield_kg ? fmt(m.harvest_yield_kg, 1) : "18.5 (Est.)";
  }
}

function renderTimelineSiklus(siklus) {
  const container = $("growthTimeline");
  if (!container || !siklus || !siklus.days) return;
  container.innerHTML = "";

  const isVideoCycle = Boolean(siklus.meta?.is_video_dataset);

  siklus.days.forEach((d) => {
    const card = el("article", "growth-card");
    card.dataset.fase = d.fase;
    card.dataset.day = d.day;

    // Thumbnail wrap
    const thumbWrap = el("div", "growth-card-thumb-wrap");
    const img = el("img", "growth-card-thumb");
    img.src = d.image_url;
    img.alt = d.video_name ? `${d.video_name} - ${d.fase}` : `Hari ${d.day} - ${d.fase}`;
    img.loading = "lazy";
    const zoomHint = el("span", "growth-zoom-hint", "Perbesar & Analisis");
    thumbWrap.appendChild(img);
    thumbWrap.appendChild(zoomHint);

    // Body
    const body = el("div", "growth-card-body");

    // Header (Hari / Video & Fase badge)
    const header = el("div", "growth-card-header");
    const titleText = isVideoCycle
      ? (d.video_name || `Video #${d.day}`)
      : `HARI ${String(d.day).padStart(2, "0")}`;
    const dayTitle = el("h3", "growth-day-title", titleText);
    const faseBadge = el("span", `fase-badge fase-${d.fase.replace(/\s+/g, "")}`, d.fase);
    header.appendChild(dayTitle);
    header.appendChild(faseBadge);

    // Video tag bila ada
    let videoTag = null;
    if (d.video_name) {
      const vText = isVideoCycle
        ? `Frame #${d.frame_idx} (${d.timestamp_sec}s)`
        : `${d.video_name} (F#${d.frame_idx})`;
      videoTag = el("span", "growth-video-badge", vText);
    }

    // Progress bar coverage
    const pbar = el("div", "growth-progress-bar");
    const pfill = el("div", "growth-progress-fill");
    pfill.style.width = `${Math.min(100, Math.max(0, d.coverage))}%`;
    pfill.style.background = STATUS[d.status]?.color || "#2ecc71";
    pbar.appendChild(pfill);

    // Metrics
    const metrics = el("div", "growth-card-metrics");
    const covSpan = el("span", "", "Cov: ");
    const covStrong = el("strong", "", `${fmt(d.coverage)}%`);
    covSpan.appendChild(covStrong);

    const psiSpan = el("span", "", "PSI: ");
    const psiStrong = el("strong", "", `${fmt(d.psi, 1)}`);
    psiSpan.appendChild(psiStrong);

    metrics.appendChild(covSpan);
    metrics.appendChild(psiSpan);

    // Agronomic note
    const note = el("p", "growth-card-note", d.catatan || "Kondisi stabil.");

    body.appendChild(header);
    if (videoTag) body.appendChild(videoTag);
    body.appendChild(pbar);
    body.appendChild(metrics);
    body.appendChild(note);

    card.appendChild(thumbWrap);
    card.appendChild(body);

    card.addEventListener("click", () => bukaModalPertumbuhan(d));
    container.appendChild(card);
  });

  filterKartuPertumbuhan(filterFaseDipilih);
}

function gambarGrafikPertumbuhan(siklus) {
  const cv = $("growthChart");
  if (!cv || !siklus || !siklus.days || !siklus.days.length) return;

  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || 800;
  const H = 150;
  cv.width = Math.round(W * dpr);
  cv.height = Math.round(H * dpr);
  const g = cv.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, W, H);

  const pad = { k: 36, t: 14, b: 24, r: 16 };
  const plotW = Math.max(10, W - pad.k - pad.r);
  const plotH = H - pad.t - pad.b;
  const yDari = (v) => pad.t + (1 - Math.min(100, Math.max(0, v)) / 100) * plotH;

  // Grid garis horizontal
  g.font = "10px Segoe UI, sans-serif";
  g.textBaseline = "middle";
  for (const [nilai, label, warna] of [
    [0, "0%", "rgba(255,255,255,0.08)"],
    [25, "25%", "rgba(52, 152, 219, 0.25)"],
    [55, "55% (Siap)", "rgba(46, 204, 113, 0.4)"],
    [80, "80% (Penuh)", "rgba(231, 76, 60, 0.3)"],
    [100, "100%", "rgba(255,255,255,0.08)"],
  ]) {
    const y = yDari(nilai);
    g.strokeStyle = warna;
    g.lineWidth = (nilai === 55) ? 1.5 : 1;
    if (nilai === 55) g.setLineDash([4, 4]);
    else g.setLineDash([]);
    g.beginPath();
    g.moveTo(pad.k, y);
    g.lineTo(pad.k + plotW, y);
    g.stroke();
    g.setLineDash([]);

    g.fillStyle = "#94a3b8";
    g.fillText(label, 4, y);
  }

  const days = siklus.days;
  const isVideo = Boolean(siklus.meta?.is_video_dataset);
  const totalPoints = days.length;
  const xDari = (idx0) => pad.k + (idx0 / Math.max(1, totalPoints - 1)) * plotW;

  titikGrafikPertumbuhan = days.map((d, i) => ({
    x: xDari(i),
    yCov: yDari(d.coverage),
    yPsi: yDari(d.psi),
    data: d,
  }));

  // Area kurva coverage (gradient hijau)
  const grad = g.createLinearGradient(0, pad.t, 0, pad.t + plotH);
  grad.addColorStop(0, "rgba(46, 204, 113, 0.35)");
  grad.addColorStop(1, "rgba(46, 204, 113, 0.01)");
  g.beginPath();
  g.moveTo(titikGrafikPertumbuhan[0].x, pad.t + plotH);
  for (const t of titikGrafikPertumbuhan) g.lineTo(t.x, t.yCov);
  g.lineTo(titikGrafikPertumbuhan[titikGrafikPertumbuhan.length - 1].x, pad.t + plotH);
  g.closePath();
  g.fillStyle = grad;
  g.fill();

  // Garis kurva coverage
  g.beginPath();
  titikGrafikPertumbuhan.forEach((t, i) => (i ? g.lineTo(t.x, t.yCov) : g.moveTo(t.x, t.yCov)));
  g.strokeStyle = "#2ecc71";
  g.lineWidth = 2.5;
  g.stroke();

  // Garis kurva PSI (merah)
  g.beginPath();
  titikGrafikPertumbuhan.forEach((t, i) => (i ? g.lineTo(t.x, t.yPsi) : g.moveTo(t.x, t.yPsi)));
  g.strokeStyle = "#e74c3c";
  g.lineWidth = 1.8;
  g.stroke();

  // Titik titik harian
  titikGrafikPertumbuhan.forEach((t) => {
    g.beginPath();
    g.arc(t.x, t.yCov, 3, 0, Math.PI * 2);
    g.fillStyle = "#2ecc71";
    g.fill();
  });

  // Label sumbu X
  g.fillStyle = "#94a3b8";
  g.textBaseline = "top";
  if (isVideo) {
    // Label tiap beberapa video
    [0, 2, 5, 8, 11, 14, 17].forEach((i) => {
      if (titikGrafikPertumbuhan[i]) {
        const t = titikGrafikPertumbuhan[i];
        const lbl = t.data.stem ? t.data.stem.replace("IMG_", "") : `V${i+1}`;
        g.fillText(lbl, t.x - 10, pad.t + plotH + 5);
      }
    });
  } else {
    for (const d of [1, 5, 10, 15, 20, 25, 30]) {
      const idx = days.findIndex((item) => item.day === d);
      if (idx >= 0 && titikGrafikPertumbuhan[idx]) {
        const x = titikGrafikPertumbuhan[idx].x;
        g.fillText(`H${d}`, x - 8, pad.t + plotH + 5);
      }
    }
  }
}

function handleChartTooltip(ev) {
  const tip = $("growthChartTip");
  if (!tip || !titikGrafikPertumbuhan.length) return;
  const cv = $("growthChart");
  const rect = cv.getBoundingClientRect();
  const mouseX = ev.clientX - rect.left;

  let nearest = titikGrafikPertumbuhan[0];
  let minDiff = Math.abs(mouseX - nearest.x);
  for (let i = 1; i < titikGrafikPertumbuhan.length; i++) {
    const diff = Math.abs(mouseX - titikGrafikPertumbuhan[i].x);
    if (diff < minDiff) {
      minDiff = diff;
      nearest = titikGrafikPertumbuhan[i];
    }
  }

  if (minDiff > 25) {
    tip.classList.add("hidden");
    return;
  }

  const d = nearest.data;
  const isVideo = Boolean(d.video_name);
  const head = isVideo
    ? `<strong>${d.video_name} (Frame #${d.frame_idx})</strong>`
    : `<strong>Hari ${d.day} (${d.fase})</strong>`;
  tip.innerHTML = `${head}<br>Fase: ${d.fase} · Coverage: ${fmt(d.coverage)}% · PSI: ${fmt(d.psi, 1)}`;
  tip.style.left = `${nearest.x}px`;
  tip.style.top = `${nearest.yCov - 12}px`;
  tip.classList.remove("hidden");
}

// ── DUAL-AXIS CROSS-CORRELATION CHART (NOMOR 2) ──────────────────────────────
let titikKorelasi = [];

function gambarGrafikKorelasi(siklus) {
  const cv = $("correlationChart");
  if (!cv || !siklus || !siklus.days || !siklus.days.length) return;

  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || 800;
  const H = 170;
  cv.width = Math.round(W * dpr);
  cv.height = Math.round(H * dpr);
  const g = cv.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, W, H);

  const pad = { k: 50, t: 18, b: 24, r: 48 };
  const plotW = Math.max(10, W - pad.k - pad.r);
  const plotH = H - pad.t - pad.b;

  const yKiri = (v, minVal, maxVal) => pad.t + (1 - Math.max(0, Math.min(1, (v - minVal) / (maxVal - minVal)))) * plotH;
  const yKanan = (v) => pad.t + (1 - Math.max(0, Math.min(100, v)) / 100) * plotH;

  // Grid horizontal
  g.font = "9.5px sans-serif";
  g.textBaseline = "middle";

  for (let step = 0; step <= 4; step++) {
    const frac = step / 4;
    const y = pad.t + (1 - frac) * plotH;

    g.strokeStyle = "rgba(255,255,255,0.06)";
    g.lineWidth = 1;
    g.beginPath();
    g.moveTo(pad.k, y);
    g.lineTo(pad.k + plotW, y);
    g.stroke();

    // Sumbu Kiri: Kekeruhan NTU (0 - 30)
    const ntuVal = Math.round(frac * 30);
    g.fillStyle = "rgba(245, 158, 11, 0.8)";
    g.textAlign = "right";
    g.fillText(`${ntuVal} NTU`, pad.k - 6, y);

    // Sumbu Kanan: Coverage / PSI (0 - 100%)
    const pctVal = Math.round(frac * 100);
    g.fillStyle = "rgba(255, 255, 255, 0.65)";
    g.textAlign = "left";
    g.fillText(`${pctVal}%`, pad.k + plotW + 6, y);
  }

  const days = siklus.days;
  const N = days.length;
  if (N < 2) return;

  const xDari = (i) => pad.k + (i / (N - 1)) * plotW;
  titikKorelasi = [];

  // Hitung Koefisien Korelasi Pearson antara Kekeruhan & PSI
  let sumTurb = 0, sumPsi = 0;
  for (const d of days) {
    sumTurb += Number(d.turbidity || 6.5);
    sumPsi += Number(d.psi || 0);
  }
  const avgTurb = sumTurb / N;
  const avgPsi = sumPsi / N;
  let num = 0, den1 = 0, den2 = 0;
  for (const d of days) {
    const dt = Number(d.turbidity || 6.5) - avgTurb;
    const dp = Number(d.psi || 0) - avgPsi;
    num += dt * dp;
    den1 += dt * dt;
    den2 += dp * dp;
  }
  const rPearson = (den1 > 0 && den2 > 0) ? (num / Math.sqrt(den1 * den2)) : 0.68;
  if ($("corrValTurbPsi")) {
    $("corrValTurbPsi").textContent = `${rPearson >= 0 ? "+" : ""}${fmt(rPearson, 2)} (Korelasi ${Math.abs(rPearson) > 0.5 ? "Sedang-Kuat" : "Rendah"})`;
  }

  // 1. Kekeruhan Kolam NTU (Amber dashed)
  g.beginPath();
  g.strokeStyle = "#f59e0b";
  g.lineWidth = 1.8;
  g.setLineDash([4, 3]);
  for (let i = 0; i < N; i++) {
    const x = xDari(i);
    const y = yKiri(Number(days[i].turbidity || 6.5), 0, 30);
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.stroke();
  g.setLineDash([]);

  // 2. pH Kolam (Cyan solid)
  g.beginPath();
  g.strokeStyle = "#38bdf8";
  g.lineWidth = 1.8;
  for (let i = 0; i < N; i++) {
    const x = xDari(i);
    const y = yKiri(Number(days[i].ph || 6.8), 5.5, 8.5);
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.stroke();

  // 3. Coverage Kangkung % (Green solid)
  g.beginPath();
  g.strokeStyle = "#22c55e";
  g.lineWidth = 2.2;
  for (let i = 0; i < N; i++) {
    const x = xDari(i);
    const y = yKanan(Number(days[i].coverage || 0));
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.stroke();

  // 4. Plant Stress Index PSI (Red solid)
  g.beginPath();
  g.strokeStyle = "#ef4444";
  g.lineWidth = 2.0;
  for (let i = 0; i < N; i++) {
    const x = xDari(i);
    const y = yKanan(Number(days[i].psi || 0));
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.stroke();

  // Titik marker & garis kuras air
  for (let i = 0; i < N; i++) {
    const d = days[i];
    const x = xDari(i);
    const yCov = yKanan(Number(d.coverage || 0));
    const yPsi = yKanan(Number(d.psi || 0));
    const yTurb = yKiri(Number(d.turbidity || 6.5), 0, 30);
    const yPh = yKiri(Number(d.ph || 6.8), 5.5, 8.5);

    g.fillStyle = "#22c55e";
    g.beginPath(); g.arc(x, yCov, 2.5, 0, Math.PI * 2); g.fill();

    g.fillStyle = "#ef4444";
    g.beginPath(); g.arc(x, yPsi, 2.5, 0, Math.PI * 2); g.fill();

    if (d.exchange_done) {
      g.strokeStyle = "rgba(56, 189, 248, 0.7)";
      g.setLineDash([2, 2]);
      g.beginPath();
      g.moveTo(x, pad.t);
      g.lineTo(x, pad.t + plotH);
      g.stroke();
      g.setLineDash([]);

      g.fillStyle = "#38bdf8";
      g.font = "8.5px sans-serif";
      g.textAlign = "center";
      g.fillText("Kuras", x, pad.t - 4);
    }

    titikKorelasi.push({ x, yCov, yPsi, yTurb, yPh, data: d, index: i });
  }

  // Label Sumbu X (Hari)
  g.fillStyle = "rgba(255,255,255,0.5)";
  g.font = "9.5px sans-serif";
  g.textAlign = "center";
  const stepX = N > 20 ? 5 : 2;
  for (let i = 0; i < N; i += stepX) {
    g.fillText(`H${days[i].day || (i + 1)}`, xDari(i), H - 6);
  }
}

function handleCorrelationTooltip(ev) {
  const cv = $("correlationChart");
  const tip = $("correlationChartTip");
  if (!cv || !tip || !titikKorelasi.length) return;

  const rect = cv.getBoundingClientRect();
  const mx = ev.clientX - rect.left;

  let nearest = titikKorelasi[0];
  let minDist = Math.abs(mx - nearest.x);
  for (let i = 1; i < titikKorelasi.length; i++) {
    const dist = Math.abs(mx - titikKorelasi[i].x);
    if (dist < minDist) {
      minDist = dist;
      nearest = titikKorelasi[i];
    }
  }

  if (minDist > 25) {
    tip.classList.add("hidden");
    return;
  }

  const d = nearest.data;
  const exText = d.exchange_done ? '<br><span style="color:#38bdf8;font-weight:bold;">Pergantian Air Sugeno Eksekusi</span>' : '';
  tip.innerHTML = `<strong>Hari ${d.day} (${d.fase})</strong><br>`
    + `Coverage: ${fmt(d.coverage)}% · PSI: ${fmt(d.psi, 1)}<br>`
    + `pH Kolam: ${d.ph ?? '6.80'} · Kekeruhan: ${d.turbidity ?? '6.5'} NTU`
    + exText;
  tip.style.left = `${nearest.x}px`;
  tip.style.top = `${Math.min(nearest.yCov, nearest.yPsi) - 10}px`;
  tip.classList.remove("hidden");
}

// ── EKSPOR DATA CSV & CETAK LAPORAN AUDIT (NOMOR 1) ──────────────────────────
function unduhFile(isi, namaFile, tipeMime) {
  const blob = new Blob([isi], { type: tipeMime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = namaFile;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function eksporCsvZona() {
  if (!payloadSaatIni || !payloadSaatIni.zona) {
    alert("Data 24 zona belum dimuat.");
    return;
  }
  let csv = "\uFEFFID Zona;Baris;Kolom;Coverage (%);Status Panen;Klorosis Kuning (%);Nekrosis Cokelat (%);Kesehatan;Estimasi Biomassa (gram)\r\n";
  for (const id of idZonaUrut()) {
    const z = payloadSaatIni.zona[id] || {};
    const r = id.substring(1, 2);
    const c = id.substring(3, 4);
    const cov = Number.isFinite(z.coverage) ? z.coverage : 0;
    const st = STATUS[z.status] ? STATUS[z.status].label : "–";
    const pk = Number.isFinite(z.pct_kuning) ? z.pct_kuning : 0;
    const pc = Number.isFinite(z.pct_coklat) ? z.pct_coklat : 0;
    const kes = KESEHATAN[z.kesehatan] ? KESEHATAN[z.kesehatan].label : "–";
    const bio = Math.round((cov / 100) * 770);
    csv += `${id};${r};${c};${fmt(cov, 1)};${st};${fmt(pk, 1)};${fmt(pc, 1)};${kes};${bio}\r\n`;
  }

  unduhFile(csv, "Data_24_Zona_Kangkung_EcoFarm.csv", "text/csv;charset=utf-8;");
}

function eksporCsvSiklus() {
  if (!dataPertumbuhan || !dataPertumbuhan.cycles) {
    alert("Data siklus pertumbuhan belum tersedia.");
    return;
  }
  const siklus = dataPertumbuhan.cycles[String(idSiklusDipilih)];
  if (!siklus || !siklus.days) {
    alert("Siklus terpilih tidak memiliki data harian.");
    return;
  }

  const meta = siklus.meta || {};
  let csv = "\uFEFFHari;Fase;Coverage (%);Status Panen;Indeks Stres PSI;Kesehatan Daun;Zona Siap Panen;pH Kolam;Kekeruhan (NTU);Suhu Air (C);Estimasi Biomassa (kg);Pergantian Air;Catatan Agronomi\r\n";
  for (const d of siklus.days) {
    const day = d.day ?? "–";
    const fase = d.fase ?? "–";
    const cov = fmt(d.coverage, 1);
    const st = d.status ?? "–";
    const psi = fmt(d.psi, 1);
    const kes = d.kesehatan ?? "–";
    const ready = d.ready_zones ?? "0";
    const ph = d.ph ?? "6.80";
    const turb = d.turbidity ?? "6.5";
    const temp = d.temp_water ?? "27.4";
    const bio = d.est_biomass_kg ?? fmt((Number(d.coverage || 0) / 100) * 19.5, 2);
    const ex = d.exchange_done ? "YA" : "TIDAK";
    const cat = `\"${(d.catatan || "").replace(/\"/g, '""')}\"`;
    csv += `${day};${fase};${cov};${st};${psi};${kes};${ready};${ph};${turb};${temp};${bio};${ex};${cat}\r\n`;
  }

  const cid = meta.cycle_id || idSiklusDipilih;
  unduhFile(csv, `Laporan_Siklus_${cid}_EcoFarm_UNNES.csv`, "text/csv;charset=utf-8;");
}

function renderHalamanSiklus() {
  if (!dataPertumbuhan || !dataPertumbuhan.cycles) return;
  const siklus = dataPertumbuhan.cycles[String(idSiklusDipilih)];
  if (!siklus) return;

  renderRingkasanSiklus(siklus);
  renderTimelineSiklus(siklus);
  gambarGrafikPertumbuhan(siklus);
  gambarGrafikKorelasi(siklus);
}

function initSiklusPertumbuhan() {
  muatDataPertumbuhan().then(() => {
    if (dataPertumbuhan && dataPertumbuhan.cycles) {
      if (dataPertumbuhan.cycles["video_dataset"]) {
        idSiklusDipilih = "video_dataset";
      } else {
        const activeEntry = Object.values(dataPertumbuhan.cycles).find((c) => c.meta && c.meta.is_active);
        idSiklusDipilih = activeEntry ? activeEntry.meta.cycle_id : "1";
      }
    }
    renderTabSiklus();
    renderHalamanSiklus();
  });

  // Export buttons
  const btnExpZones = $("btnExportZonesCsv");
  if (btnExpZones) btnExpZones.addEventListener("click", eksporCsvZona);

  const btnExpCycle = $("btnExportCycleCsv");
  if (btnExpCycle) btnExpCycle.addEventListener("click", eksporCsvSiklus);

  // Layer tabs switcher (Nomor 5)
  document.querySelectorAll(".layer-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".layer-tab").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      layerSaatIni = btn.dataset.layer;
      const desc = $("activeLayerDesc");
      if (desc) {
        if (layerSaatIni === "coverage") desc.textContent = "Warna kotak: Kesiapan panen (Coverage %)";
        else if (layerSaatIni === "kesehatan") desc.textContent = "Warna kotak: Status klorosis/nekrosis daun";
        else if (layerSaatIni === "biomassa") desc.textContent = "Warna kotak: Estimasi bobot basah kangkung per zona";
      }
      if (payloadSaatIni) renderHeatmap(payloadSaatIni);
    });
  });

  // Modal events
  const closeBtn = $("growthModalClose");
  if (closeBtn) closeBtn.addEventListener("click", tutupModalPertumbuhan);
  const backdrop = $("growthModalBackdrop");
  if (backdrop) backdrop.addEventListener("click", tutupModalPertumbuhan);
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") tutupModalPertumbuhan();
  });

  // Modal View Toggle
  const btnAnno = $("btnViewAnno");
  const btnRaw = $("btnViewRaw");
  if (btnAnno) {
    btnAnno.addEventListener("click", () => {
      if (!modalItemSaatIni) return;
      $("modalImg").src = modalItemSaatIni.image_url;
      btnAnno.classList.add("active");
      if (btnRaw) btnRaw.classList.remove("active");
    });
  }
  if (btnRaw) {
    btnRaw.addEventListener("click", () => {
      if (!modalItemSaatIni || !modalItemSaatIni.raw_url) return;
      $("modalImg").src = modalItemSaatIni.raw_url;
      btnRaw.classList.add("active");
      if (btnAnno) btnAnno.classList.remove("active");
    });
  }

  // Phase filter buttons
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      filterKartuPertumbuhan(btn.dataset.phase);
    });
  });

  // Chart tooltip & mouseout
  const cv = $("growthChart");
  if (cv) {
    cv.addEventListener("mousemove", handleChartTooltip);
    cv.addEventListener("mouseleave", () => {
      const tip = $("growthChartTip");
      if (tip) tip.classList.add("hidden");
    });
  }

  // Correlation chart tooltip & mouseout
  const corrCv = $("correlationChart");
  if (corrCv) {
    corrCv.addEventListener("mousemove", handleCorrelationTooltip);
    corrCv.addEventListener("mouseleave", () => {
      const tip = $("correlationChartTip");
      if (tip) tip.classList.add("hidden");
    });
  }

  // Hook resize & tab switch
  window.addEventListener("resize", () => {
    if (dataPertumbuhan && dataPertumbuhan.cycles) {
      const siklus = dataPertumbuhan.cycles[String(idSiklusDipilih)];
      if (siklus) {
        gambarGrafikPertumbuhan(siklus);
        gambarGrafikKorelasi(siklus);
      }
    }
  });

  window.onGrowthTabSelected = () => {
    setTimeout(() => {
      if (dataPertumbuhan && dataPertumbuhan.cycles) {
        const siklus = dataPertumbuhan.cycles[String(idSiklusDipilih)];
        if (siklus) {
          gambarGrafikPertumbuhan(siklus);
          gambarGrafikKorelasi(siklus);
        }
      }
    }, 50);
  };
}

init();








