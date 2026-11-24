# Dashboard Specification
## Kangkung Aquaponics Computer Vision Monitoring System

---

> **Version** 2.0  
> **Author** Felix Enrique  
> **Target** Static SPA (HTML / CSS / JS) -- no build toolchain  
> **Data Source** Firebase Firestore `bed_readings` collection, realtime listener  

---

## 1. Design Language

### 1.1 Visual Direction

Clean, data-dense, futuristic. Inspired by aerospace telemetry interfaces and scientific instrument panels. Every pixel communicates information; nothing is decorative.

### 1.2 Color System

| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#0a0e17` | Page background |
| `--bg-card` | `#111827` | Card / panel surfaces |
| `--bg-elevated` | `#1a2235` | Hover states, modals |
| `--border-subtle` | `#1e293b` | Card borders, dividers |
| `--border-accent` | `#334155` | Active borders, focus rings |
| `--text-primary` | `#f1f5f9` | Headings, primary data |
| `--text-secondary` | `#94a3b8` | Labels, captions |
| `--text-muted` | `#475569` | Disabled, timestamps |
| `--accent-cyan` | `#06b6d4` | Primary accent, links, active states |
| `--accent-green` | `#10b981` | Healthy, nominal, online |
| `--accent-yellow` | `#f59e0b` | Warning, chlorosis, waspada |
| `--accent-red` | `#ef4444` | Critical, necrosis, sakit |
| `--accent-blue` | `#3b82f6` | Informational, secondary accent |

### 1.3 Typography

| Element | Font | Weight | Size |
|---|---|---|---|
| Headings | Inter | 600 | 14-20px |
| Body / Labels | Inter | 400 | 12-14px |
| Data values | JetBrains Mono | 500 | 16-32px |
| Micro labels | Inter | 500 | 10-11px, uppercase, letter-spacing 0.05em |

### 1.4 Spacing and Radius

- Grid gap: 16px (cards), 12px (internal elements)
- Card padding: 20px
- Border radius: 8px (cards), 4px (badges, chips)
- No shadows. Depth conveyed through background tint and subtle 1px borders.

### 1.5 Motion

- Transitions: 200ms ease-out for hover/focus states
- Data update pulse: brief cyan glow on the card border (300ms) when a value changes
- Chart transitions: 400ms ease-in-out for new data points

---

## 2. Layout Architecture

### 2.1 Grid Structure

```
+---------------------------------------------------------------+
|  TOP BAR                                                       |
+---------------------------------------------------------------+
|  METRIC CARDS  (4 columns, auto-fit min 220px)                 |
|  [ Coverage ]  [ Harvest ]  [ PSI ]  [ System ]               |
+---------------------------------------------------------------+
|  PRIMARY PANELS  (2 columns, 1fr 1fr)                          |
|  [ Zone Heatmap 4x6 ]       [ Snapshot + Timeline Chart ]      |
+---------------------------------------------------------------+
|  SECONDARY PANELS  (2 columns, 1fr 1fr)                        |
|  [ Distribution Bars ]       [ Alerts + Fuzzy Input ]          |
+---------------------------------------------------------------+
|  FOOTER                                                        |
+---------------------------------------------------------------+
```

### 2.2 Responsive Breakpoints

| Breakpoint | Behavior |
|---|---|
| >= 1200px | Full 2-column layout as above |
| 768-1199px | Panels stack to single column; metric cards remain 2x2 |
| < 768px | Everything single column; heatmap tiles shrink to 36x36px |

---

## 3. Component Specifications

### 3.1 Top Bar

**Height:** 56px  
**Background:** `--bg-card` with bottom border `--border-subtle`

| Element | Position | Spec |
|---|---|---|
| Brand text | Left | "KANGKUNG CV MONITOR" -- uppercase, `--text-secondary`, 11px, letter-spacing 0.1em |
| Device ID | Left, after brand | `--text-muted`, monospace, 12px |
| Connection badge | Center | Pill shape. States: `LIVE` (cyan pulse dot + text), `OFFLINE` (red), `WAITING` (yellow blink), `DEMO` (blue) |
| Last update | Right | Relative timestamp ("3 min ago"), `--text-muted`, 12px. Absolute on hover tooltip. |
| Demo toggle | Right | Small outlined button, `--border-accent`, appears only when demo mode is available |

### 3.2 Metric Cards

Four cards in a single row. Each card:

**Structure:**
```
+---------------------------+
|  MICRO LABEL              |
|  PRIMARY VALUE    [UNIT]  |
|  Secondary detail line    |
|  Tertiary detail line     |
+---------------------------+
```

**Card 1: Coverage**
- Micro label: "RATA-RATA CAKUPAN"
- Primary value: `{coverage_rata}%` (2 decimal places, monospace, 28px)
- Detail 1: "Std dev: {coverage_std}%" in `--text-secondary`
- Detail 2: "{n}/24 zona terbaca" in `--text-muted`
- Left accent bar: 3px vertical, color mapped to coverage value (green > 55%, yellow 25-55%, red < 25%)

**Card 2: Harvest Readiness**
- Micro label: "ZONA SIAP PANEN"
- Primary value: `{zona_siap_panen}/24` (monospace, 28px)
- Detail 1: "{persen_siap}% dari total zona"
- Detail 2: Mini horizontal bar showing status distribution (4 segments, proportional width)
- Left accent bar: `--accent-green`

**Card 3: Plant Stress Index**
- Micro label: "INDEKS STRES PSI"
- Primary value: `{psi}` (0-100, monospace, 28px)
- Color: green 0-20, yellow 20-50, red 50-100
- Detail 1: "Kuning {kuning_rata}% | Coklat {coklat_rata}%"
- Detail 2: "Zona terburuk: {psi_maks}" in appropriate color
- Left accent bar: color mapped to PSI value

**Card 4: System Status**
- Micro label: "SUHU RASPBERRY PI"
- Primary value: `{suhu_pi_c} C` (monospace, 28px)
- Color: green < 65, yellow 65-75, red >= 75
- Detail 1: "Thermal guard: {status}"
- Detail 2: PSI version badge (`v2.0`) + data validity indicator
- Left accent bar: `--accent-cyan`

### 3.3 Zone Heatmap (4 x 6 Grid)

**Panel title:** "PETA ZONA BED" -- micro label style

**Grid layout:** 4 rows x 6 columns, gap 4px, contained within a panel with aspect ratio 6:4

**Each tile:**
- Size: flexible, minimum 48x48px
- Background color: mapped to harvest status
  - `belum_siap`: `#1e293b` (dark slate)
  - `hampir_siap`: `#854d0e` (muted amber)
  - `siap_panen`: `#166534` (forest green)
  - `harus_panen`: `#065f46` (deep teal-green, brighter border)
- Corner label: zone ID ("R1C1"), 9px, `--text-muted`
- Center value: coverage %, monospace, 13px
- Health indicator: 6px dot at bottom-right corner
  - `sehat`: `--accent-green`
  - `waspada`: `--accent-yellow`
  - `sakit`: `--accent-red`
- Hover: elevate background to `--bg-elevated`, show 1px `--accent-cyan` border
- Click: open Zone Detail Panel (see 3.7)

### 3.4 Snapshot Viewer

**Panel title:** "SNAPSHOT TERAKHIR"

- Image container: 100% width, maintain aspect ratio, rounded 4px, 1px border `--border-subtle`
- Source: `snapshot_url` from Firestore document
- Fallback: dark placeholder with text "Belum ada snapshot"
- Below image: capture timestamp, `--text-muted`, 11px

### 3.5 Coverage Timeline Chart

**Panel title:** "RIWAYAT CAKUPAN (24 JAM)"

**Renderer:** Canvas 2D (no external library)

**Specifications:**
- X-axis: time, last 144 readings (approximately 24 hours at 10-minute intervals)
- Y-axis: coverage % (0-100), gridlines at 25, 55, 80 (harvest thresholds)
- Threshold lines: dashed, 1px, labeled on right edge
  - 25%: `--accent-yellow` with label "Hampir Siap"
  - 55%: `--accent-green` with label "Siap Panen"
  - 80%: `--accent-cyan` with label "Harus Panen"
- Data line: solid 2px, `--accent-cyan`, with subtle fill gradient to transparent below
- Data points: 4px circles on hover only
- Tooltip on hover: timestamp + coverage value + PSI at that time
- Background: `--bg-card` with subtle horizontal gridlines at 0, 25, 50, 75, 100 using `--border-subtle`
- Axis labels: `--text-muted`, 10px

### 3.6 Distribution Panels

**Panel title:** "DISTRIBUSI STATUS" and "KESEHATAN DAUN"

Two stacked horizontal bar charts within one panel.

**Status Distribution:**
- 4 horizontal bars (one per status category)
- Label on left (12px), count on right (monospace), bar proportional to count/24
- Colors match heatmap tile colors
- Order: `belum_siap`, `hampir_siap`, `siap_panen`, `harus_panen`

**Health Distribution:**
- 3 horizontal bars (sehat, waspada, sakit)
- Colors: green, yellow, red respectively
- Same layout as status bars

### 3.7 Zone Detail Panel (Overlay)

Triggered by clicking a heatmap tile. Slides in from the right as a 320px-wide panel overlay.

**Contents:**
```
+---------------------------+
|  ZONA R{r}C{c}     [X]   |
|  ─────────────────────    |
|  Cakupan        78.3%    |
|  Status       siap_panen  |
|  Kesehatan        sehat   |
|  ─────────────────────    |
|  Klorotik (kuning)  2.1% |
|  Nekrotik (coklat)  0.4% |
|  ─────────────────────    |
|  Piksel hijau      12840  |
|  Piksel kuning       271  |
|  Piksel coklat        51  |
+---------------------------+
```

- Background: `--bg-elevated`
- Close button: top-right, `--text-muted`
- Status/health values: colored according to their state
- Values right-aligned, monospace
- Dismiss: click X, click outside, or press Escape

### 3.8 Alerts and Recommendations Panel

**Panel title:** "REKOMENDASI DAN PERINGATAN"

**Recommendation block:**
- Background: `--bg-elevated` with left 3px accent bar `--accent-cyan`
- Text: `{rekomendasi}` from payload, 13px, `--text-primary`

**Fuzzy Input chips:**
- Row of inline chips below recommendation
- Each chip: `label: value` format
- Background: `--bg-card`, border `--border-subtle`, border-radius 4px, padding 4px 8px
- Label: `--text-muted`, 10px uppercase
- Value: `--text-primary`, monospace, 12px
- Chips: `psi`, `psi_maks`, `zona_sakit`, `kuning_pct`, `coklat_pct`, `valid`, `psi_versi`

**Priority alert list:**
- Title: "ZONA PERLU PERHATIAN" -- micro label
- Max 8 items shown
- Each item: single row with zone ID (monospace), health badge (colored dot + text), coverage %
- Sort order: sakit first, then waspada, then harus_panen with high PSI
- Minimal style: no card wrapping, just rows with subtle bottom border

---

## 4. Data Flow

### 4.1 Firebase Connection

```
onSnapshot(
  query(
    collection(db, "bed_readings"),
    orderBy("timestamp", "desc"),
    limit(144)
  ),
  (snapshot) => { ... }
)
```

- On first load: populate all panels with latest document
- On update: animate changed values (brief highlight), append to chart history
- On disconnect: switch badge to `OFFLINE`, freeze display, show last-known timestamp

### 4.2 Payload Processing

The dashboard receives raw `bed_readings` documents. Processing pipeline:

1. **Validate payload** -- check required fields exist
2. **Backward compatibility** -- call `lengkapiPayload()` to compute missing aggregates from zone data if absent
3. **PSI recalculation** -- mirror Python formula: `PSI = 100 * (0.5*Y + B) / N`
4. **Update UI** -- write values to DOM, redraw charts, update heatmap colors

### 4.3 Demo Mode

Activated when:
- Firebase config missing
- SDK initialization fails
- URL parameter `?demo=1`

Behavior:
- Generate synthetic zone data (randomized coverage 10-95%, realistic health distribution)
- Refresh every 60 seconds
- Badge shows `DEMO` in blue
- All panels functional with synthetic data

---

## 5. Interaction States

### 5.1 Connection Badge States

| State | Visual | Trigger |
|---|---|---|
| LIVE | Cyan dot (pulsing), cyan text | Active Firestore listener, data < 15 min old |
| WAITING | Yellow dot (blinking), yellow text | Listener active but no data received yet |
| OFFLINE | Red dot (static), red text | Listener error or data > 30 min stale |
| DEMO | Blue dot (static), blue text | Demo mode active |

### 5.2 Data Freshness

- < 15 minutes: normal display
- 15-30 minutes: timestamp turns `--accent-yellow`, append "(stale)" label
- \> 30 minutes: timestamp turns `--accent-red`, badge switches to OFFLINE

### 5.3 Thermal Guard Warning

When `suhu_pi_c >= 75`:
- System card left accent bar turns red
- Value text turns `--accent-red`
- Optional: subtle red pulse on card border

---

## 6. File Structure

```
web/
  index.html          -- single HTML entry point, all structure
  css/
    variables.css     -- design tokens (colors, spacing, typography)
    layout.css        -- grid, responsive breakpoints
    components.css    -- cards, heatmap, charts, panels, badges
  js/
    config.js         -- Firebase config, thresholds, constants
    firebase.js       -- Firestore connection, onSnapshot handler
    state.js          -- application state store, history buffer
    render.js         -- DOM update functions per component
    chart.js          -- canvas chart drawing logic
    heatmap.js        -- zone grid rendering and interaction
    demo.js           -- synthetic data generator
    utils.js          -- formatters, PSI calc, relative time
  assets/
    favicon.svg       -- minimal geometric icon
```

---

## 7. Performance Targets

| Metric | Target |
|---|---|
| First Contentful Paint | < 1.5s |
| Time to Interactive | < 2.0s |
| Bundle size (total) | < 50 KB (no framework, no external libs) |
| Chart redraw | < 16ms (60fps capable) |
| Memory (144 readings) | < 5 MB |
| Firestore reads per session | ~1 initial + 1 per update (realtime listener) |

---

## 8. Accessibility

- All interactive elements keyboard-navigable (Tab, Enter, Escape)
- Color is never the sole indicator; always paired with text labels
- Minimum contrast ratio 4.5:1 for text, 3:1 for large text and UI components
- Screen reader: ARIA labels on heatmap tiles, chart summary text, badge status
- Reduced motion: respect `prefers-reduced-motion` media query (disable pulse animations)

---

## 9. Future Extension Points

### 9.1 Fuzzy Controller Integration

When the partner team's ESP32 fuzzy controller goes live, the dashboard will add:

- New panel: "KEPUTUSAN FUZZY" displaying the latest decision from `keputusan_fuzzy` collection
- Decision states: `ganti_air`, `tambah_nutrisi`, `cek_pH`, `panen_selektif`, `tidak_ada_tindakan`
- Approval workflow: status badge (`menunggu_acc` / `disetujui` / `dieksekusi`)
- Read-only display; approval happens outside this dashboard

### 9.2 Sensor Data Panel

If the partner team exposes pH, turbidity, and temperature sensor readings to Firestore:

- New metric cards or a dedicated panel for water quality parameters
- pH trend chart (similar to coverage timeline)
- Turbidity gauge visualization

### 9.3 Multi-Camera Support

- Device selector dropdown in top bar
- Each device maintains independent state and history
- Side-by-side comparison mode for two beds

---

## 10. Reference: Harvest Status Thresholds

| Status | Coverage Range | Heatmap Color | Action |
|---|---|---|---|
| `belum_siap` | 0 -- 25% | Dark slate | No action |
| `hampir_siap` | 25 -- 55% | Muted amber | Monitor growth |
| `siap_panen` | 55 -- 80% | Forest green | Schedule harvest |
| `harus_panen` | > 80% | Deep teal, bright border | Harvest immediately |

## 11. Reference: Health Classification Thresholds

| Condition | Waspada Threshold | Sakit Threshold | Indicator Color |
|---|---|---|---|
| Chlorosis (yellow) | >= 10% | >= 25% | Yellow |
| Necrosis (brown) | >= 3% | >= 8% | Red |

Brown is prioritized over yellow when both thresholds are exceeded.

## 12. Reference: PSI Scale

| PSI Range | Interpretation | Color |
|---|---|---|
| 0 -- 20 | Nominal, predominantly green canopy | Green |
| 20 -- 50 | Moderate stress, significant chlorosis | Yellow |
| 50 -- 100 | Severe stress, extensive necrosis | Red |

Formula: `PSI = 100 * (0.5 * yellow_pixels + brown_pixels) / total_plant_pixels`

