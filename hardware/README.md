# Mounting Kamera Night-Vision (OpenSCAD)

Rancangan 3D untuk enclosure mesh-only yang menampung **Raspberry Pi 4 Model B**
dan **modul kamera OV5647 night-vision (OV5647 + 2x IR LED 850 nm)**, dipasang
di atas bed kangkung pada lengan yang dapat dimiringkan.

Semua dimensi ada di `params.scad`. File `.scad` lain hanya membacanya.

---

## Asal-usul desain (baca dulu)

Ada desain yang mirip di internet: "WIFI night vision camera (indoor) based on
an RPI Zero W" — 8 part STL + dokumentasi, lisensi **CC BY-NC-ND**.

Desain ini **bukan turunan** dari desain tersebut, dan tidak ada geometri yang
disalin darinya. Alasannya:

1. Desain asli untuk **Pi Zero W** (65 x 30 mm) dan **modul kamera berbeda**.
   Menyesuaikkannya ke Pi 4B (85 x 56 mm) berarti mengubah hampir semua
   dimensi, bukan sekadar scaling.
2. Lisensi **ND (No Derivatives)** melarang mengubah lalu mendistribusikan
   turunannya. Untuk proyek yang didesain ulang, mengedit STL-nya berisiko.

Semua di sini ditulis dari nol dengan sistem koordinat, parameter, dan
keputusan thermal yang berbeda.

---

## Part yang dihasilkan

| Part | Fungsi | STL | Volume |
|---|---|---|---|
| `fit_test.scad` | Pelat uji pola lubang + 3 pola aperture. **CETAK DULU.** | `stl/fit_test.stl` | 91 cm3 |
| `enclosure.scad` | Bodi box: muka kamera, dinding, rusuk, ventilasi, cable gland, paddle | `stl/enclosure.stl` | 56 cm3 |
| `enclosure_tutup.scad` | Tutup + jalur exhaust udara panas | `stl/enclosure_tutup.stl` | 17 cm3 |
| `camera_holder.scad` | Jepit PCB modul kamera (4x M2) | `stl/camera_holder.stl` | 3 cm3 |
| `mount_base.scad` | Antarmuka: **hollow persegi** / pipa / baut / dinding | `stl/mount_base.stl` | 44 cm3 |
| `arm.scad` | Lengan + pelat ujung kemiringan | `stl/arm.stl` | 28 cm3 |
| `assembly.scad` | Pratinjau rakitan (jangan dicetak) | - | - |
| `preview.scad` | **Rakitan lengkap + phantom** (Pi 4B, modul kamera, hollow) | - | - |
| `preview.ps1` | Render rakitan: mode `rakit` / `ledakan` / `xray` | - | - |

---

## `tutup_pi4b.scad` - tutup untuk box PASANGAN (produk terpisah)

> **Jangan dicampur dengan `enclosure_tupid.scad`.** Keduanya tutup, tapi untuk
> box yang berbeda dan tidak saling terkait.

| | Part | STL |
|---|---|---|
| Bodi (pasangan) | `files/pi4b_camera_enclosure_bottom.stl` | sudah final, dibuat oleh `files/build_pi4b_enclosure.py` |
| Tutup | `tutup_pi4b.scad` | `stl/tutup_pi4b.stl` |

Bodi pasangannya **93,0 x 99,5 x 40,0 mm** (cavitas 89 x 95,5). Spec tutup
sudah diverifikasi ke STL itu: semua angkanya cocok, tidak ada yang perlu
ditebak.

```
pelat   93,0 x 99,5 x 2,0 mm   R sudut 3,0   (flush dengan dinding luar box)
lip     88,6 x 95,1 x 4,0 mm   R sudut 0,8   dinding 1,6   z 36 .. 40
total   6,0 mm
```

- **Lip** = cavitas − 0,2 mm per sisi, jadi pas masuk tanpa dorongan.
- **Lip di z 36..40** dan slot ventilasi dinding box paling atas berakhir di
  z 35,5 → jarak 0,5 mm, jadi lip tidak menutupi ventilasi.
- **Pry notch** 8 x 1,5 mm di tepi −X untuk ujung obeng.
- **Grid exhaust** busur konsentris Ø26 mm di x = 11, y = 18,75, tepat di atas
  SoC. Pusatnya dihitung dengan logika `gx`/`gy` yang sama persis dengan
  `build_pi4b_enclosure.py` baris 91 (`gx = 43,0 − 32,0 = 11,0`,
  `gy = 45,75 − 27,0 = 18,75`).

### Cara memverifikasi pas-fit-nya

Ruang lingkup, bisa diulang kapan saja, dan hasilnya terukur:

```powershell
# 1. build tutup
openscad.com -o stl\tutup_pi4b.stl tutup_pi4b.scad

# 2. cek mesh
.\cek_mesh.ps1 -File (Resolve-Path .\stl\tutup_pi4b.stl)

# 3. uji interferensi nyata terhadap STL pasangan (hasil harus 0,0 mm3)
#    irisan lip z36..40 dengan box
```

Hasil saat ini: `bb = 93,0 x 99,5 x 6,0` (flush, tidak melimpahi) dan
**irisan lip x box = 0,0 mm3** → tidak ada tabrakan.

### Dua jebakan yang sudah ditangani di file ini

1. **`offset(r=+x)` tidak cuma membulatkan, tapi MEMBESARKAN benda.**
   `offset(r=3) square([93, 99.5])` menghasilkan **99 x 105,5 mm**, bukan
   93 x 99,5. Jadi `profil_rr()` mengecilkan persegi di dalamnya menjadi
   `w − 2r` dulu, sama seperti `rrect()` di script Python.

2. **Offset Z untuk penempatan di koordinat box = 34, bukan 40.** `tutup()` occupy
   z 0..6 (pelat 0..2, lip 2..6). Supaya lip berakhir di z 36..40, translate
   harus `36 − 2 = 34`. Kalau dipakai 40, lid duduk **di atas** box (z 40..46)
   dan lip tidak masuk ke cavitas sama sekali. Gunakan modul
   `lid_dalam_koordinat_box()` daripada menebak sendiri.
| `cek_mesh.ps1` | Validator STL (bukan part) | - | - |

Semua STL diverifikasi dengan `cek_mesh.ps1`: **watertight, 0 edge bocor,
0 edge non-manifold, 1 komponen terhubung, volume positif**.

---

## Dimensi hasil desain

```
enclosure      153,8 x 90,8 x 56,8 mm   (badan; +10 mm paddle di sisi -X)
tutup         150,8 x 94,8 x  6,4 mm   (overhang 2 mm per sisi = drip shield)
lengan        193,3 x 56,6 x  6,0 mm
klem hollow    54,6 x 65,6 x 30,0 mm   (untuk hollow 40 x 40 mm)
```

Dimensi enclosure berubah beberapa kali:

- **105,8 x 76,8 → 96,8 x 67,8 mm.** Penyebabnya: boss tutup yang dulu berdiri
  setinggi 48 mm di lantai rongga memaksa clearance 8 mm. Sekarang boss itu
  diganti **rusuk sudut** yang melayang di atas komponen Pi, sehingga clearance
  arah X cukup 3,5 mm.
- **96,8 x 67,8 → 96,8 x 90,8 mm** (tinggi +23 mm, lebar tetap). Ini untuk
  memberi ruang port Pi 4B. Clearance dipecah per sumbu: X tetap 3,5 mm, Y
  jadi 15 mm karena RJ45 menonjol 13,5 mm. Penjelasan lengkap ada di bagian
  "Review visual" di bawah.
- **96,8 → 143,8 mm lebar** (lebar +47 mm, tinggi tetap). Ini untuk baris
  bukaan optik yang lebih besar, dijelaskan tepat di bawah ini.

### Baris bukaan optik (muka depan)

Bukaan bukan lagi 3 lubang kecil di tengah, tapi **baris 4 bukaan besar** sesuai
gambar:

```
[ IR Ø40 ]  [ Kamera Ø30 ]  [ IR Ø40 ]  [ LDR Ø10 ]
  x=-44,5       x=-6,5         x=31,5       x=59,5
```

Lebar baris bukaan = **129 mm**, plus margin 5 mm per sisi dan dinding 2,4 mm,
jadi box harus lebar **143,8 mm**. Titu baliknya: `encl_w` sekarang dihitung
dari lebar baris bukaan (`lebar_min_bukaan`), bukan lagi dari PCB Pi. Kalau
lebar box masih mengikuti Pi yang cuma 85 mm, bukaan optik akan keluar dari
dinding.

| Parameter | Nilai | Arti |
|---|---|---|
| `bukaan_ir_d` | 40 mm | Diameter lubang IR kiri dan kanan |
| `bukaan_kamera_d` | 30 mm | Diameter lubang kamera |
| `bukaan_ldr_d` | 10 mm | Diameter jendela LDR |
| `bukaan_gap` | 3 mm | Jarak antar **tepi** lubang (bukan antar pusat) |
| `bukaan_margin` | 5 mm | Jarak dari tepi luar baris ke dinding dalam |

LDR sengaja diletakkan **di sisi kanan lubang IR kanan**, menempel tapi tetap
pisah 3 mm, supaya fotoresistor tetap melihat cahaya ambient. Kalau jendela LDR
tertutup, IR menyala terus 24 jam (boros + panas).

**Ukuran ini lebih besar dari modul kamera (25 x 24 mm).** Lubang Ø30 dan Ø40
itu bukan lubang tembus modul, melainkan bukaan untuk **housing optik**: barrel
kamera yang lebih besar dan array LED IR berbentuk ring. Modul PCB hanya dijepit
di belakang sebagai penopang. [UKUR housing fisik Anda sebelum mencetak]

Semua yang ikut bergeser otomatis karena membaca angka turunan yang sama:

- **Boss jepit** di `enclosure.scad` dan **pelat jepit + post** di
  `camera_holder.scad` memakai `bukaan_kamera_dx`, jadi modul kamera selalu
  tepat di belakang barrel optik.
- **Panel muka** lebar dan tingginya dihitung dari baris bukaan, bukan angka
  tetap.
- **Sun shield** ikut bergeser ke `bukaan_kamera_dx` (default masih mati).
- **Trimpot** dipindah ke bawah baris (`trimpot_dy = -30`), **LED indikator** ke
  atas (`led_indikator_dy = 30`). Keduanya tadinya di `dy = ±10-12` yang sekarang
  jatuh DI DALAM bukaan IR Ø40. Ada validasi otomatis yang memperingatkan kalau
  ini terulang.

Parameter lama yang sekarang mati dan **sudah dihapus** (supaya tidak ada dua
angka yang bisa tidak sinkron): `diameter_bukaan_lensa`, `led_ir_protrusi`,
`fotoresistor_d/dx/dy`, `trimpot_dx`, `led_ir_jarak_x`, `led_ir_diameter`,
`led_ir_dy`.

Rincian visual untuk mendekati tampilan desain asal:

- **Chamfer 2 mm** pada 4 tepi vertikal. Profil yang sama dipakai untuk kulit
  luar dan rongga dalam, jadi ketebalan dinding tetap seragam 2,4 mm.
- **Panel muka recessed** 0,8 mm, 48 x 42 mm, membingkai kelima aperture —
  memberi kesan "plat kamera" ringkas di tengah muka yang lebar.
- **Paddle dipadatkan** tanpa gusset segitiga yang menonjol.

Tumpukan Z di dalam enclosure (dihitung otomatis di `params.scad`):

```
 0,0 -  2,4  dinding muka depan (panel muka cekung 0,8 mm di dalamnya)
 2,4 -  5,4  4 boss jepit kamera (self-tap M2)
 5,4 -  6,4  PCB modul kamera night-vision (1 mm)
 6,4 -  8,8  pelat jepit (camera_holder.scad)
 8,8 - 14,8  ruang tikungan kabel ribbon CSI
14,8 - 19,8  4 post standoff (5 mm) + PCB Raspberry Pi 4B (1,6 mm)
19,8 - 35,8  komponen teratas (USB-A / RJ45)
35,8 - 54,4  ruang bebas untuk heatsink (18,6 mm)
39,0 - 54,4  4 rusuk sudut (self-tap M3) - melayang di atas komponen Pi
54,4 - 56,8  tutup (skirt masuk 4 mm ke rongga)
```

---

## Thermal: ini masalah utama desain ini

Desain Pi Zero asli membuang ~1,3 W. Versi ini harus membuang:

- 2x LED IR 3 W (saat menyala, hanya pada mode malam)
- Raspberry Pi 4B ~5 W (load CV kontinu)
- **Total sampai ~11 W**, sekitar **8x** beban desain asli

Konsekuensinya:

- Ventilasi jauh lebih besar: 16 slot di dinding ±Y (2 kolom x 8 baris per
  sisi, slot 18 x 4 mm) plus 8 slot di tutup.
- **Intake di separuh bawah dinding -Y, exhaust di separuh atas dinding +Y.**
  Pemisahan inilah yang menghasilkan arus konveksi alami. Kalau semua slot
  setinggi sama, hampir tidak ada aliran.
- Ventilasi sengaja **dipindah ke dinding ±Y**, bukan ±X. Alasannya: dinding ±X
  dipakai penuh oleh rusuk sudut (4 boss tutup) dan paddle lengan, sehingga
  slot di sana tertutup sebagian. Dinding -Y juga dipakai cable gland, jadi
  slot intake digeser ke x = ±20 — cukup jauh dari gland (x -8..8).
- Slot ventilasi terlindung hujan: tutup selalu di **ATAS**, bukan di samping.
- Ruang heatsink 18,6 mm di atas Pi, cukup untuk heat sink aluminium ~45x45 mm.
  Kalau heat sink yang dipakai lebih rendah, kurangi `pi_ruang_heatsink` untuk
  memperpendek box — tapi perhatikan bahwa ruang itu juga menentukan tinggi
  rusuk sudut (lihat peringatan di `params.scad`).

Kalau setelah dipasang temperaturunya masih naik, langkah berikutnya adalah
**memisahkan Pi 4B ke enclosure kedua** (perbesar `encl_clearance_ov`), bukan
hanya menambah ventilasi.

---

## Review visual: `preview.scad` + `preview.ps1`

`preview.scad` menggabungkan **semua part jadi satu scene** untuk review,
ditambah *phantom* (adon Raspberry Pi 4B, modul kamera, kabel ribbon, dan besi
hollow yang dijepit klem) supaya Anda bisa menilai clearance tanpa perlu
mencetak dulu.

```powershell
.\preview.ps1                  # 3 mode x 6 sudut
.\preview.ps1 -Mode ledakan    # exploded view (tiap part digeser)
.\preview.ps1 -Mode xray       # dinding transparan, isi kelihatan
.\preview.ps1 -SudutKemiringan 30 -PanjangLengan 180
```

Output: `renders\preview_<mode>_<sudut>.png` dan `stl\preview_rakit.stl`.

> STL gabungan **hanya untuk dilihat** di Windows 3D Viewer / Cura / OctoPrint.
> Jangan di-slicer langsung, karena isinya beberapa part yang harus dicetak
> terpisah dengan orientasi cetak masing-masing.

Catatan teknis: mode `xray` sengaja dirender dengan `--preview` (OpenCSG),
bukan `--render` (CGAL). Renderer CGAL mengabaikan nilai alpha dari `color()`,
jadi dinding semi transparan akan keluar sepenuhnya pekat kalau pakai
`--render`. OpenCSG juga jauh lebih cepat, jadi `.\preview.ps1 -Mode xray`
hanya besoin hitungan detik.

### Dua masalah nyata yang ditemukan lewat phantom

Phantom bukan hiasan. Saat pertama kali dirender, langsung terlihat dua hal
yang mustahil kelihatan dari STL part terpisah. **Keduanya sudah diperbaiki.**

**1. Port Pi 4B menabrak dinding - SUDAH DIPERBAIKI**

Awalnya muncul peringatan ini:

```
[PERINGATAN] Port RJ45 Pi 4B MENABRAK dinding: clearance 3,5 mm < 13,5 mm
```

Clearance lama 3,5 mm, padahal konektor Pi 4B menonjol jauh dari tepi PCB:

| Port | Tonjolan dari tepi PCB |
|---|---|
| RJ45 ethernet | ~13,5 mm |
| USB-A | ~7,5 mm |
| USB-C (power) | ~7,5 mm |
| micro-HDMI | ~6 mm |

RJ45 butuh 13,5 mm, jadi **PCB Pi 4B tidak akan bisa masuk ke box sama sekali**.

**Bugnya: clearance hanya satu angka untuk kedua sumbu.** Padahal geometri port
Pi 4B asimetris - semua port menempel di tepi **-Y**, sedangkan tepi kiri dan
kanan PCB (arah **X**) bersih total, tidak ada konektor sama sekali. Clearance
masih dikali 2 di `encl_w` dan `encl_h`, jadi menaikkan clearance demi RJ45
justru ikut membengkakkan *lebar* box tanpa ada gunanya.

Karena itu `encl_clearance` dipecah jadi dua:

| Parameter | Nilai | Alasan |
|---|---|---|
| `encl_clearance_x` | 3,5 mm | Tepi PCB arah X tidak ada port. Cukup untuk toleransi cetak. |
| `encl_clearance_y` | 15,0 mm | RJ45 13,5 mm + 1,5 mm margin cetak. |

Hasilnya box jadi **96,8 x 90,8 mm** (dari 96,8 x 67,8 mm). Bandingkan dengan
cara lama yang menaikkan clearance di kedua sumbu:

| Cara | Box | Lebar |
|---|---|---|
| `encl_clearance` di kedua sumbu (14 mm) | 117,8 x 88,8 mm | **21 mm terbuang** |
| Clearance per sumbu (dipakai) | 96,8 x 90,8 mm | 96,8 mm |

Jadi port Pi sekarang muat dengan lega, sementara lebar box tetap 96,8 mm.
`encl_clearance_ov` masih honoured sebagai override untuk kedua sumbu, jadi
catatan atau skrip lama tidak langsung rusak.

Validasi `[PERINGATAN] clearance Y hanya ... mm` dipindah ke `params.scad`,
bukan hanya di `preview.scad`. Alasannya: preview bukan bagian dari jalur build
part. Kalau clearance Y dikecilkan lagi, semua part **tetap berhasil dicetak
tanpa error**, lalu baru disesali waktu rakit. Jadi harus gagal lebih awal.

Opsi jendela port di dinding -Y (yang akan membuat box tetap 67,8 mm tinggi)
tidak diambil, karena butuh koordinat port yang harus diukur dengan jangka dari
modul fisik Anda, dan intake ventilasi di dinding -Y ikut harus dipindah.

**2. `gland_dy` mati - SUDAH DIHAPUS**

`params.scad` mendefinisikan `gland_dy = 10` dengan komentar panjang tentang
kenapa posisinya tidak boleh 0, tapi `cable_gland()` di `enclosure.scad` tidak
pernah membacanya - posisinya hard-code di `translate([0, -int_h/2, zg])`.
Variabel mati, jadi **dihapus** (bukan dipoles), termasuk alasannya yang ternyata
salah: komentar lama mengklaim gland di `x = 0` akan memotong post standoff,
padahal post standoff ada di `x = +/-29` (tepi 25..33 mm) sedangkan gland hanya
selebar `x = -8..8` mm. Keduanya tidak mungkin bertabrakan di sumbu X, jadi
offset Y tidak pernah dibutuhkan sama sekali.

---

## Mounting di frame atap (klem hollow persegi)

Konfigurasi default: box digantung dari **besi hollow persegi (stal kotak)** di
frame atap, dengan **kamera lurus ke bawah** menatap bed tanaman.

### Klem hollow

`mount_base.scad` punya empat tipe mount: `"hollow"` (default), `"pipa"`,
`"baut"`, `"dinding"`.

Klem hollow berbentuk **C yang dibuka di satu sisi** dan diikat satu baut M5
melalui dua lug. Kenapa bukan cincin penuh: klem C yang kaku hanya bisa
dipasang dengan **diselipkan dari ujung hollow**. Kalau frame atap sudah
terpasang, itu tidak mungkin. Dengan dua bagian, klem bisa dipasang di titik
mana saja sepanjang hollow.

Arah pasang: badan C mengapit hollow dari bawah, plat atas menekan sisi atas
hollow, lalu baut M5 diencangkan sampai celah rapat. Satu baut M5 kedua
menyambungkan lengan ke plat atas.

Ukuran hollow diatur lewat `hollow_a` / `hollow_b` (dimension luar) dan
`hollow_r` (radius sudut). **Default 40 x 40 mm belum diukur** — setelah
dijangka sorong, build ulang tanpa mengedit file:

```powershell
.\build.ps1 -TipeMount hollow -HollowA 30 -HollowB 30
```

### Kemiringan dan arah pandang

`sudut_kemiringan` diukur dari pose dasar, dan **pose dasar sudah berarti kamera
lurus ke bawah**:

| Nilai | Arah optik |
|---|---|
| `0` (default) | lurus ke bawah — lookdown ke bed |
| `20` | miring 20 derajat dari tegak |
| `90` | mendatar |

Lengan memakai panjang 150 mm; ubah dengan `-PanjangLengan`.

### Batasan yang perlu diketahui

Paddle ada di dinding **samping** box, sedangkan optik ada di muka — keduanya
tegak lurus. Konsekuensinya, saat kamera diarahkan mendatar, box tetap menggantung
horizontal di ujung lengan, bukan berayun ke bawah seperti lampu gantung. Ini
sifat geometri, bukan cacat. Selama sudut dipakai kecil (0-30 derajat) box
tetap menggantung rapi di ujung lengan.

---

## Optik night-vision

Muka depan punya **5 lubang**, semuanya wajib terbuka:

| Lubang | Fungsi | Kenapa tidak boleh ditutup |
|---|---|---|
| Optik | jalur pandang | — |
| 2x diameter LED IR | Cahaya inframerah | Ditutup = kamera buta di malam hari |
| Jendela fotoresistor (LDR) | Deteksi siang/malam | Ditutup = IR menyala terus 24 jam |
| Akses trimpot | Setel ambang nyala IR | Ditutup = tidak bisa disetel |

### Sun shield: default MATI

`pakai_sunshield = false`. Alasannya bukan sekadar "ribet":

Sun shield adalah corong di sekitar optik. Pada modul night-vision, **LED IR,
LDR, dan trimpot letaknya sangat dekat dengan optik**. Corong yang lebar wajar
justru akan menutupi lubang-lubang itu — kamera jadi buta malam hari atau IR
menyala terus.

Jari-jari corong dihitung otomatis di `enclosure.scad` dari jarak ke fitur
terdekat, sehingga secara matematis tidak mungkin menutupi. Kalau ruangnya
memang cukup setelah modul diukur, ubah `pakai_sunshield = true`.

### Menahan fokus

Modul Anda punya barrel fokus ber-ring knurled. Ada fitur "kunci barrel" yang
pernah dirancang, tapi **dihapus** — alasannya tercatat di `camera_holder.scad`.
Ganti dengan:

1. Fokuskan setelah modul terpasang menjepit.
2. Tandai posisi barrel dengan spidol.
3. Cek ulang fokus setiap box dibuka.
4. Opsional: sekencang O-ring / lakban pada barrel, atau lem cyanoacrylate
   dosis kecil. Jauh lebih andal daripada dongolan plastik.

---

## Prasyarat

```powershell
winget install OpenSCAD.OpenSCAD
```

OpenSCAD 2021.01. Tidak perlu Docker.

---

## Build

```powershell
cd hardware
.\build.ps1                                  # semua part
.\build.ps1 -Part fit_test                   # plat uji (langkah pertama)
.\build.ps1 -Part enclosure,enclosure_tutup  # beberapa part sekaligus
.\build.ps1 -TipeMount hollow                # hollow (default) | pipa | baut | dinding
.\build.ps1 -HollowA 30 -HollowB 30          # ukuran hollow persegi (mm)
.\build.ps1 -PanjangLengan 200               # panjang lengan (mm)
.\build.ps1 -SudutKemiringan 20              # kemiringan dari tegak (derajat)
.\build.ps1 -SkipRender                     # hanya STL, tanpa render (cepat)
.\build.ps1 -OnlyRender                      # hanya render PNG
.\cek_mesh.ps1                               # validasi semua STL di .\stl
```

Output: `stl/*.stl` (untuk slicer) dan `renders/*.png` (8 sudut per part).

> **Catatan teknis**: OpenSCAD 2021.01 tidak meneruskan variabel `-D` ke dalam
> file yang di-`include`, sehingga `build.ps1` membuat file wrapper sementara
> untuk menyetel override di lingkup terluar. Jangan dihapus logika itu.


---

## FASE 1 - Pengukuran (WAJIB, SEBELUM CETAK PART NYATA)

Nilai di `params.scad` yang ditandai `[UKUR]` **belum diverifikasi** untuk
modul Anda. Modul night-vision adalah clone, dan dimensinya bisa berbeda dari
modul Raspberry Pi standar.

**Langkah 1 - cetak `fit_test` saja.** 3 g filamen, 10 menit. Plat ini punya:

- **A** - pola lubang kamera: 4 lubang M2 + 4 tanda sudut PCB 25x24
- **B** - pola lubang Pi 4B: 4 lubang jarak 58x49
- **C** - **3 pola aperture berdampingan**: diameter LED IR 12/14/16 mm dengan
  jarak pusat optik 18/20/22 mm. Tempelkan modul nyata ke tiap pola, dan Anda
  langsung tahu mana yang cocok - cukup SATU kali cetak, bukan tiga.
- **D** - penggaris berengkah 100 mm untuk mengukur langsung

Letakkan PCB modul di atas pola A. Kalau 4 lubang tidak cocok, pola salah.

**Langkah 2 - ukur dengan penggaris, lalu tulis ke `params.scad`:**

| Parameter | Cara mengukur | Estimasi dari foto |
|---|---|---|
| `pola_lubang_x` | jarak center lubang kiri ke kanan | 21 |
| `pola_lubang_y` | jarak center lubang atas ke bawah | 20 |
| `kamera_pcb_w` / `kamera_pcb_h` | sisi PCB terpanjang / terpendek | 25 / 24 |
| `kamera_pcb_t` | tebal PCB | 1 |
| `optik_lensa_diameter` | diameter ring knurled | 9-12 |
| `diameter_bukaan_lensa` | +0,5 mm longgar dari barrel | 10 |
| `optik_lensa_panjang` | menonjolnya barrel dari muka PCB | 10-15 |
| `led_ir_diameter` | **diameter TERLEBAR reflektor**, bukan LED | 9-12 |
| `led_ir_jarak_x` | jarak antara dua pusat LED IR | 18-24 |
| `led_indikator_dx` / `_dy` | posisi 2 LED merah kecil | 9 / 10 |
| `fotoresistor_d` / `_dx` / `_dy` | LDR | - |
| `trimpot_d` / `_dx` / `_dy` | trimpot | - |

> **Penting**: pada modul di foto, LED IR memakai **reflektor logam 3 W**, bukan
> dome LED 5 mm. Default lama `led_ir_diameter = 5.0` hampir pasti salah.
> Pola C di `fit_test` sengaja mencakup rentang 12-16 mm untuk mengujinya.

Default sekarang: `pola_lubang_x = 21.0`, `pola_lubang_y = 20.0`
(asumsi lubang 2 mm dari tiap tepi PCB 25x24). **Asumsi ini belum diuji.**

Juga perlu diukur: **ukuran luar hollow persegi** untuk `-HollowA` / `-HollowB`.

**Langkah 3** - ulang `.\build.ps1 -Part fit_test` sampai cocok.

---

## Pemasangan

### Di dalam box

1. Pasang **tutup** dulu (4x baut M3x10 ke 4 rusuk sudut) - lebih mudah
   dikerjakan di luar.
2. Masukkan **modul kamera**: optik menghadap -Z (ke arah bed), PCB duduk di
   4 boss jepit.
3. Sambungkan **ribbon CSI** ke konektor di belakang modul.
4. Pasang **pelat jepit** + 4x sekrup **M2x12**, dikencangkan **secara silang**
   (bukan berurutan) supaya PCB rata.
5. Pasang **Pi 4B** di 4 post standoff. **PENTING: port USB-C harus
   menghadap ke dinding -Y** (ada lubang cable gland M16 di sana).
6. Pasang heatsink, isi sekitar 15 g thermal paste.
7. Tutup box, kencangkan 4x M3.

### Antara box dan lengan

- **2x baut M4x25** menembus pelat ujung lengan, masuk self-tap di paddle.
- Gesekan mengunci sudut kemiringan. **Kencangkan ulang berkala**: siklus
  panas dan getaran bisa melonggarkan sambungan ini. Kalau lengan terasa
  menggantung, itu tanda awalnya.

### Lubang cable gland

Pakai **cable gland M16** (bukan lubang kosong) - tanpa seal, air dan debu
aquaponic akan masuk. Isi juga dengan **silicone sealant** di sekeliling
kabel, dan taruh **silica gel** di dalam box.

---

## Tips cetak

| Item | Rekomendasi |
|---|---|
| Material | **PETG.** PLA melengkung, menyerap air, dan berjamur dalam hitungan minggu di lingkungan aquaponic 80-95% RH. |
| Layer | 0,2 mm |
| Infill | minimal 25% untuk lengan, 40% untuk bodi box |
| Support | **tidak perlu** untuk semua part. Semua rusuk, boss, dan post tercetak vertikal; overhang terbesar cuma tapak horizontal 8 mm pada rusuk sudut. |
| Lubang self-tap | M2 `diameter_tap_m2 = 1.6`; M3 `encl_tap_m3 = 2.5`; M4 `paddle_tap_d = 3.4` |
| Orientasi | Semua STL sudah di orientasi cetak: muka kamera di meja, tutup pelat di meja. |
| Skala | **100%**, jangan skalakan - semua toleransi sudah dihitung |

---

## Keterkaitan dengan pipeline CV

Mounting menentukan apakah deteksi bed berhasil. Dari `files/adaptive_bed.py`:

| Kode | Persyaratan | Implikasi mounting |
|---|---|---|
| `min_area_ratio = 0.12` | Bed minimal 12% luas frame | Jangan pasang kamera terlalu jauh |
| `v_hi <= 110` | Bed harus area gelap | Hindari pantulan langsung ke modul |
| `MORPH_CLOSE (25,25)` | Bed harus satu blob utuh | Jangan sampai pipa/daun menutupi bed |
| `approxPolyDP` 4 titik | 4 tepi bed harus terlihat | Beri margin, jangan pas di tepi frame |
| `CornerSmoother` | Kamera harus kokoh | Kencangkan semua baut |

### Peringatan: IR membatalkan kalibrasi HSV

Kalibrasi warna dilakukan pada cahaya siang. Pada mode malam, cahaya IR 850 nm
**tidak terlihat mata tetapi kuat dideteksi sensor**, dan mengubah nilai HSV
secara total. Konsekuensinya:

- Ambang `v_hi <= 110` **tidak bisa sama** untuk siang dan malam.
- Pipeline perlu **dua mode pemrosesan**: siang (HSV) dan malam (grayscale +
  intensity, dengan ambang terpisah).
- Deteksi malam jauh lebih mudah dan tidak butuh pemisahan warna.

Setel trimpot onboard **sebelum** membungkus modul, di ruang terang, supaya
ambang switching-nya benar.

---

## Kalibrasi setelah terpasang

```bash
systemctl --user stop kangkung-camera     # lepas kamera dari preview
~/kangkung_pi/venv/bin/python kangkung_pi.py --test
```

Target kelulusan: `coverage_rata` **bukan 0** di payload (`outbox/*.json`).
Kalau masih 0, bed belum terdeteksi - atur ulang sudut atau tinggi kamera.

Untuk mengunci posisi bed permanen:

```bash
python kalibrasi_kamera.py <sumber> --manual
```

Kriteria: kontur bed hasil warp menutupi 4 sudut dan `coverage` masuk akal
(tidak 0% padahal bed penuh tanaman).

---

## Struktur

```text
hardware/
  params.scad           semua dimensi (SATU-SATUNYA sumber kebenaran)
  fit_test.scad         plat uji pola lubang (CETAK DULU)
  enclosure.scad        bodi box
  enclosure_tutup.scad  tutup + exhaust
  camera_holder.scad    jepit modul kamera
  mount_base.scad       klem hollow persegi / pipa / flange / dasbor dinding
  arm.scad              lengan + pelat ujung
  assembly.scad         pratinjau rakitan (jangan dicetak)
  build.ps1             compile STL + render 8 sudut
  cek_mesh.ps1          validator STL (watertight / manifold / komponen)
  stl/                  output STL
  renders/              output PNG
```

## Catatan lisensi

Geometri dan kode desain ini ditulis dari nol dan tidak diturunkan dari desain
pihak ketiga mana pun. Lisensi yang Anda pilih bebas dipakai sesuai kebutuhan
proyek Anda.

