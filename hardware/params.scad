// =============================================================================
// params.scad - SATU-SATUNYA sumber kebenaran dimensi untuk semua part mounting
// =============================================================================
//  Semua angka dalam mm. Ubah HANYA di file ini - part lain membacanya.
//
//  POLA OVERRIDE: setiap nilai memakai is_undef() dengan nama override
//  berakhiran _ov, sehingga bisa ditimpa dari command line tanpa mengedit
//  file. Contoh:
//      openscad -D 'panjang_lengan_ov=200' -o out.stl part.scad
//
//  ======================================================================
//  [UKUR] = DEFAULT YANG BELUM DIVERIFIKASI. Wajib diganti dengan hasil
//           pengukuran modul OV5647 night-vision yang Anda pakai. Lihat
//           hardware/README.md bagian "Fase 1 - Pengukuran". Cetak
//           fit_test.scad DULU untuk memverifikasi pola lubang - hanya
//           butuh 10 menit dan 3 gram filamen.
//  [TERKONFIRMASI] = angka standar pabrikan, relatif aman tanpa pengukuran.
//  ======================================================================
//
//  Referensi standar (Raspberry Pi Camera Module, form factor 25x24):
//    - PCB 25 x 24 mm, tebal ~1 mm                    [TERKONFIRMASI]
//    - 4 lubang sekrup M2                             [TERKONFIRMASI]
//    - backside PCB ke muka kamera = 6 mm              [TERKONFIRMASI]
//
//  Raspberry Pi 4 Model B:
//    - papan 85 x 56 mm, PCB 1,6 mm                    [TERKONFIRMASI]
//    - 4 lubang O2,7 mm (M2/M2.5), jarak 58 x 49 mm  [TERKONFIRMASI]
//    - komponen tertinggi (USB-A / RJ45) ~16 mm       [TERKONFIRMASI]
// =============================================================================

$fn = 48;

// --- Toleransi cetak ---
toleransi_cetak   = is_undef(toleransi_cetak_ov)   ? 0.25 : toleransi_cetak_ov;
tinggi_layer      = is_undef(tinggi_layer_ov)      ? 0.20 : tinggi_layer_ov;

// --- Raspberry Pi 4 Model B (seluruhnya TERKONFIRMASI) ---
pi_pcb_w          = is_undef(pi_pcb_w_ov)          ? 85.0 : pi_pcb_w_ov;
pi_pcb_h          = is_undef(pi_pcb_h_ov)          ? 56.0 : pi_pcb_h_ov;
pi_pcb_t          = is_undef(pi_pcb_t_ov)          ? 1.6  : pi_pcb_t_ov;
pi_lubang_x       = is_undef(pi_lubang_x_ov)       ? 58.0 : pi_lubang_x_ov;
pi_lubang_y       = is_undef(pi_lubang_y_ov)       ? 49.0 : pi_lubang_y_ov;
pi_lubang_d       = is_undef(pi_lubang_d_ov)       ? 2.7  : pi_lubang_d_ov;
pi_tinggi_port    = is_undef(pi_tinggi_port_ov)    ? 16.0 : pi_tinggi_port_ov;
pi_ruang_heatsink = is_undef(pi_ruang_heatsink_ov) ? 18.0 : pi_ruang_heatsink_ov;
pi_ruang_bawah    = is_undef(pi_ruang_bawah_ov)    ? 5.0  : pi_ruang_bawah_ov;
pi_post_d         = is_undef(pi_post_d_ov)         ? 8.0  : pi_post_d_ov;

// --- Modul kamera (PCB 25 x 24) ---
kamera_pcb_w      = is_undef(kamera_pcb_w_ov)      ? 25.0 : kamera_pcb_w_ov;
kamera_pcb_h      = is_undef(kamera_pcb_h_ov)      ? 24.0 : kamera_pcb_h_ov;
kamera_pcb_t      = is_undef(kamera_pcb_t_ov)      ? 1.0  : kamera_pcb_t_ov;

// Jarak antar lubang - INI YANG PALING KRITIKAL. [UKUR]
// Default 21 x 20 mengasumsikan lubang 2 mm dari tiap tepi PCB 25 x 24.
// Verifikasi dengan fit_test.scad SEBELUM mencetak part lain.
pola_lubang_x     = is_undef(pola_lubang_x_ov)     ? 21.0 : pola_lubang_x_ov;
pola_lubang_y     = is_undef(pola_lubang_y_ov)     ? 20.0 : pola_lubang_y_ov;
diameter_lubang_kamera = is_undef(diameter_lubang_kamera_ov) ? 2.0 : diameter_lubang_kamera_ov;
diameter_sekrup_m2 = is_undef(diameter_sekrup_m2_ov) ? 2.0 : diameter_sekrup_m2_ov;
diameter_tap_m2   = is_undef(diameter_tap_m2_ov)   ? 1.6  : diameter_tap_m2_ov;

// Optik - modul Anda punya BARREL FOKUS ADJUSTABLE (ring knurled), jadi
// lensanya lebih besar dan lebih panjang dari modul standar. [UKUR]
// Estimasi dari FOTO modul: diameter ring knurled ~11-13 mm, barrel menonjol
// ~10-15 mm dari muka PCB. Verifikasi lewat fit_test bagian C.
optik_lensa_diameter  = is_undef(optik_lensa_diameter_ov)  ? 12.0 : optik_lensa_diameter_ov;
optik_lensa_panjang   = is_undef(optik_lensa_panjang_ov)   ? 12.0 : optik_lensa_panjang_ov;
// CATATAN: diameter_bukaan_lensa yang lama (10 mm) sudah DIHAPUS. Ukuran
// bukaan optik kini disatukan dengan bukaan_kamera_d di bawah, jadi tidak ada
// lagi dua angka yang bisa tidak sinkron.

// --- LED IR 850 nm + sensor onboard - SEMUA [UKUR] ---
// Modul night-vision punya 2 LED IR di kiri/kanan optik, plus LDR
// (fotoresistor) pengendali dan trimpot pengatur ambang. Keduanya WAJIB
// punya akses ke cahaya luar / obeng, kalau tidak:
//   - LDR tertutup  -> IR menyala terus 24 jam (boros + panas)
//   - trimpot mati   -> ambang tidak bisa disetel
//
// PENTING: pada modul di foto, LED IR memakai REFLEKTOR METAL 3 W (bukan dome
// LED 5 mm). Default lama 5,0 mm hampir pasti salah.
//
// Ukuran TIDAK diambil dari viewport desain asal. Rasio pada gambar itu
// (diameter LED 1,75x optik, jarak pusat optik ke LED 1,87x diameter optik)
// berarti jarak dua LED 3,74x diameter optik. Dengan optik 11 mm itu 41 mm,
// mustahil pada PCB modul 25 mm. Jadi lingkaran itu bukan barrel modul pada
// skala 1:1, dan tidak boleh dipakai sebagai acuan dimensi.
//
// Default memakai diameter ~11 mm karena pada foto modul ANDA ketiga barrel
// hampir sama besar dan memenuhi hampir seluruh lebar PCB 25 mm. Lubang yang
// kelewat besar hanya menyisakan celah, sedangkan yang kekecilan membuat modul
// tidak bisa masuk. Angka pastinya ditentukan oleh pola C di fit_test.
// Bukaan optik di dinding muka depan. INI yang menentukan lebar box, bukan
// lagi PCB Pi (lihat baris encl_w di bagian dimensi turunan).
//
// SUSUNAN BARIS (dari kiri ke kanan saat menghadap depan), mengikuti desain
// pada gambar:
//     [ IR 40 ] [ Kamera 30 ] [ IR 40 ] [ LDR 10 ]
// Lubang LDR menempel di sisi kanan lubang IR kanan, supaya LDR tetap melihat
// cahaya ambient. Kalau jendela LDR tertutup, IR menyala terus 24 jam
// (boros + panas) - itu alasan kenapa jaraknya tidak diperkecil.
//
// CATATAN PENTING - ukuran ini JAUH lebih besar dari modul kamera 25 x 24 mm.
// Lubang 30 dan 40 mm ini bukan lubang tembus modul, melainkan bukaan untuk
// HOUSING OPTIK: barrel kamera yang lebih besar dan array LED IR berbentuk
// ring. Modul PCB hanya dijepit di belakang sebagai penopang; yang mengisi
// lubang adalah tabung dan reflektor, bukan PCB. [UKUR housing fisik Anda]
bukaan_ir_d     = is_undef(bukaan_ir_d_ov)     ? 40.0 : bukaan_ir_d_ov;
bukaan_kamera_d = is_undef(bukaan_kamera_d_ov) ? 30.0 : bukaan_kamera_d_ov;
bukaan_ldr_d    = is_undef(bukaan_ldr_d_ov)    ? 10.0 : bukaan_ldr_d_ov;
// Jarak antara TEPI dua lubang, bukan antar pusat. 3 mm cukup supaya ada
// dinding tipis di antaranya dan keduanya tidak menggabung jadi satu lubang.
bukaan_gap      = is_undef(bukaan_gap_ov)      ? 3.0  : bukaan_gap_ov;
// Jarak dari tepi luar baris bukaan ke dinding dalam enclosure.
bukaan_margin   = is_undef(bukaan_margin_ov)   ? 5.0  : bukaan_margin_ov;

// Lebar total baris bukaan. Dihitung DI SINA (bukan di bagian turunan) karena
// panel_muka_lebar di bawah sudah memakainya, dan OpenSCAD membaca variabel
// sesuai urutan baris - dipakai sebelum didefinisikan hasilnya undefined.
bukaan_baris_lebar = bukaan_ir_d + bukaan_gap + bukaan_kamera_d + bukaan_gap
                   + bukaan_ir_d + bukaan_gap + bukaan_ldr_d;

led_ir_ada       = is_undef(led_ir_ada_ov)       ? true : led_ir_ada_ov;

// 2 LED indikator merah di muka PCB modul. Lubang kecil di dinding muka depan
// supaya Anda bisa melihat apakah IR menyala TANPA membuka box - penting saat
// debugging mode malam. [UKUR]
// POSISI: DI ATAS baris bukaan, bukan di samping. Bukaan IR sekarang Ø40 mm
// (radius 20), jadi indikator yang tadinya di dy = 10 mm akan jatuh DI DALAM
// lubang IR dan ikut hilang bersama optiknya. dy = 30 mm menyisakan 8,25 mm
// dari tepi atas bukaan.
led_indikator_d    = is_undef(led_indikator_d_ov)    ? 3.5  : led_indikator_d_ov;
led_indikator_dx   = is_undef(led_indikator_dx_ov)   ? 9.0  : led_indikator_dx_ov;
led_indikator_dy   = is_undef(led_indikator_dy_ov)   ? 30.0 : led_indikator_dy_ov;
led_indikator_ada  = is_undef(led_indikator_ada_ov)  ? true : led_indikator_ada_ov;

// LDR (fotoresistor) dan trimpot. Diameter LDR kini disatukan dengan
// bukaan_ldr_d di baris bukaan, jadi fotoresistor_d / _dx / _dy yang lama
// sudah dihapus - posisinya ikut dihitung di baris bukaan (bukaan_ldr_dx).
trimpot_d        = is_undef(trimpot_d_ov)        ? 6.0  : trimpot_d_ov;
// Trimpot diletakkan di bawah baris bukaan, jadi hanya tinggi (dy) yang perlu
// diatur. Nilai -30 mm memberi jarak dari tepi bawah bukaan IR (radius 20 mm).
trimpot_dy       = is_undef(trimpot_dy_ov)       ? -30.0: trimpot_dy_ov;

// --- Jepit kamera (dijepit dari dalam, terlihat lewat muka depan enclosure) ---
dinding_jepit    = is_undef(dinding_jepit_ov)    ? 2.4  : dinding_jepit_ov;
panjang_pilar_jepit = is_undef(panjang_pilar_jepit_ov) ? 3.0 : panjang_pilar_jepit_ov;
radius_sudut_dudukan = is_undef(radius_sudut_dudukan_ov) ? 2.0 : radius_sudut_dudukan_ov;

// --- Enclosure (muka kamera menghadap -Z, kotak naik ke +Z) ---
// MATERIAL: cetak PETG, BUKAN PLA. Lingkungan aquaponic 80-95% RH akan
// membuat PLA melengkung, menyerap air, dan berjamur dalam hitungan minggu.
encl_dinding     = is_undef(encl_dinding_ov)     ? 2.4  : encl_dinding_ov;  // 6 layer @ 0.4

// CLEARANCE Pi ke dinding dalam. Ini yang menentukan lebar/tinggi box.
//
// PENTING - clearance dipecah PER SUMBU, karena port Pi 4B hanya tonjol ke
// arah -Y (sisi port), sedangkan di arah X TIDAK ada port sama sekali: tepi
// kiri dan kanan PCB Pi 4B bersih, tidak ada konektor. Dulu clearance ini
// satu angka untuk X dan Y sekaligus, padahal geometri portnya asimetris.
// Itu sebabnya versi lama harus memakai 8 mm dan box jadi lebar 105,8 mm.
//
//  - X: cukup 3,5 mm. Tepi PCB di arah X bersih, jadi angka ini hanya untuk
//       toleransi cetak dan akurasi slicer.
//  - Y: harus >= tonjolan port terbesar. RJ45 ethernet menonjol ~13,5 mm dari
//       tepi PCB, jadi 3,5 mm akan membuat RJ45 MENABRAK dinding. Dipakai
//       15 mm (13,5 + 1,5 margin cetak).
//
// Catatan: box tetap 96,8 mm LEBAR (tidak membengkak), hanya TINGGI yang
// bertambah. Bandingkan dengan memakai 14 mm di kedua sumbu, yang akan
// menghasilkan 117,8 mm - lebar terbuang 21 mm tanpa alasan.
// Default per sumbu, dipisah supaya override lama (encl_clearance_ov) bisa
// dipasang di satu baris assignment tanpa self-reference.
encl_clearance_x_ov_default = 3.5;    // sumbu X: tepi PCB bersih, tanpa port
encl_clearance_y_ov_default = 15.0;   // sumbu Y: menampung RJ45 13,5 mm

// Jaga kompatibilitas: catatan dan skrip lama memakai encl_clearance_ov.
// Kalau override itu dipakai, nilainya diterapkan ke kedua sumbu. Ditulis
// sebagai satu assignment (bukan conditional terpisah) supaya tidak
// self-reference - pola conditional yang membaca variabel itselfnya akan
// menghasilkan undef di OpenSCAD.
encl_clearance_x = is_undef(encl_clearance_ov) ? encl_clearance_x_ov_default : encl_clearance_ov;
encl_clearance_y = is_undef(encl_clearance_ov) ? encl_clearance_y_ov_default : encl_clearance_ov;

encl_lid_tebal   = is_undef(encl_lid_tebal_ov)   ? 2.4  : encl_lid_tebal_ov;
encl_kaidah_sisip= is_undef(encl_kaidah_sisip_ov)? 4.0  : encl_kaidah_sisip_ov;
encl_sisip_clr   = is_undef(encl_sisip_clr_ov)   ? 0.3  : encl_sisip_clr_ov;

// Chamfer 45 derajat pada 4 tepi vertikal. Applied ke profil luar DAN rongga
// dengan ukuran yang sama, jadi ketebalan dinding tetap seragam 2,4 mm.
encl_chamfer     = is_undef(encl_chamfer_ov)     ? 2.0  : encl_chamfer_ov;

// Panel muka recessed: cekungan dangkal di dinding depan yang membingkai
// kelima aperture. Efeknya: muka kamera jadi terlihat "seperti plat kamera"
// yang ringkas di tengah bidang lebar, mendekati tampilan desain asli.
// SENGaja CEKUNG bukan menonjol - kalau menonjol, saat dicetak dengan muka
// kamera di meja dia jadi overhang yang butuh support.
// Panel muka mengikuti baris bukaan, bukan angka tetap. Tambah margin supaya
// ada dinding di sekeliling setiap lubang, dan tinggi cukup untuk trimpot.
panel_muka_lebar     = is_undef(panel_muka_lebar_ov)
    ? bukaan_baris_lebar + 2 * bukaan_margin - 6 : panel_muka_lebar_ov;
panel_muka_tinggi    = is_undef(panel_muka_tinggi_ov)
    ? bukaan_ir_d + 16 : panel_muka_tinggi_ov;
panel_muka_kedalaman = is_undef(panel_muka_kedalaman_ov) ? 0.8  : panel_muka_kedalaman_ov;
panel_muka_sudut     = is_undef(panel_muka_sudut_ov)     ? 4.0  : panel_muka_sudut_ov;

encl_baut_d      = is_undef(encl_baut_d_ov)      ? 3.0  : encl_baut_d_ov;
encl_baut_clr    = is_undef(encl_baut_clr_ov)    ? 3.4  : encl_baut_clr_ov;
encl_tap_m3      = is_undef(encl_tap_m3_ov)      ? 2.5  : encl_tap_m3_ov;   // self-tap M3

// RUSUK SUDUT - pengganti boss tutup 48 mm. Duduknya DI ATAS komponen Pi
// (lihat z_rusuk di bagian turunan), menempel ke dua dinding rongga
// sekaligus, jadi kaku tanpa harus berdiri di lantai rongga. Inilah yang
// membolehkan clearance arah X turun ke 3,5 mm.
encl_rusuk_lebar = is_undef(encl_rusuk_lebar_ov) ? 8.0  : encl_rusuk_lebar_ov;  // sisi tiap dinding
encl_tap_tinggi  = is_undef(encl_tap_tinggi_ov)  ? 8.0  : encl_tap_tinggi_ov;   // panjang self-tap M3

// Ventilasi: 12 W (2x IR LED 3 W + Pi 4B) vs ~1,3 W pada desain Pi Zero asli,
// jadi kebutuhan ventilasi naik sekitar 9x. Intake di dinding -Y bagian bawah,
// exhaust di dinding +Y bagian atas -> arus konveksi alami.
vent_lebar       = is_undef(vent_lebar_ov)       ? 4.0  : vent_lebar_ov;
// Panjang 18 mm (bukan 22) supaya slot di x=+/-20 tidak menabrak paddle di
// dinding +X. Slot membentang di arah X, jadi tidak terpengaruh perubahan
// clearance Y.
vent_panjang     = is_undef(vent_panjang_ov)     ? 18.0 : vent_panjang_ov;
vent_jml_per_sisi= is_undef(vent_jml_per_sisi_ov)? 8    : vent_jml_per_sisi_ov;
vent_mulai_frac  = is_undef(vent_mulai_frac_ov)  ? 0.15 : vent_mulai_frac_ov; // fraksi tinggi dari dasar

// Cable gland M16 untuk kabel USB-C power (satu-satunya kabel keluar).
// Sekaligus jalur udara kedua.
//
// Posisi di x = 0 disengaja: di situ colokan USB-C pada phantom Pi, jadi
// kabel power keluar lurus dan tidak ditekuk tajam.
//
// CATATAN: parameter gland_dy pernah ada di sini tapi DIHAPUS karena tidak
// pernah dibaca cable_gland() - posisinya hard-code di translate([0, -int_h/2,
// zg]). Alasannya juga keliru: komentar lamanya mengklaim gland di x=0 akan
// memotong post standoff, padahal post standoff ada di x = +/-29 (tepi 25..33)
// sedangkan gland hanya selebar x = -8..8. Keduanya tidak mungkin bertabrakan
// di sumbu X, jadi offset Y tidak pernah dibutuhkan sama sekali.
gland_d          = is_undef(gland_d_ov)          ? 16.0 : gland_d_ov;

// Paddle antarmuka lengan, pada dinding +X.
// Disambung ke pelat ujung arm.scad dengan 2x baut M4 x 25, dikencangkan
// gesekan (friction clamp). Kekuatan gesekan PETG-ke-PETG (mu ~0,3) pada
// lebar 26 mm dan preload M4 jauh melebihi beban lengan, sehingga tidak
// perlu pin pivot. TAPI kencangkan ulang berkala karena siklus panas dan
// getaran bisa melonggarkan sambungan ini.
paddle_tebal     = is_undef(paddle_tebal_ov)     ? 10.0 : paddle_tebal_ov;
paddle_lebar     = is_undef(paddle_lebar_ov)     ? 22.0 : paddle_lebar_ov;
paddle_tinggi    = is_undef(paddle_tinggi_ov)    ? 24.0 : paddle_tinggi_ov;
paddle_jarak_baut= is_undef(paddle_jarak_baut_ov)? 13.0 : paddle_jarak_baut_ov;
paddle_tap_d     = is_undef(paddle_tap_d_ov)     ? 3.4  : paddle_tap_d_ov;  // self-tap M4
paddle_clr_d     = is_undef(paddle_clr_d_ov)     ? 4.5  : paddle_clr_d_ov;  // lubang M4

// --- Permukaan pemasangan ---
// tipe_mount: "pipa" | "hollow" | "baut" | "dinding"
// DEFAULT "hollow": instalasi sebenarnya adalah besi hollow persegi (stal
// kotak) di frame atap. Ubah tanpa edit file:
//     .\build.ps1 -TipeMount hollow -HollowA 30 -HollowB 30
tipe_mount         = is_undef(tipe_mount_ov)         ? "hollow" : tipe_mount_ov;

diameter_pipa_luar = is_undef(diameter_pipa_luar_ov) ? 25.4 : diameter_pipa_luar_ov;
klem_tebal         = is_undef(klem_tebal_ov)         ? 4.0  : klem_tebal_ov;
klem_lebar         = is_undef(klem_lebar_ov)         ? 14.0 : klem_lebar_ov;
klem_panjang       = is_undef(klem_panjang_ov)       ? 20.0 : klem_panjang_ov;

// Besi hollow persegi. hollow_a x hollow_b = DIMENSI LUAR, yang diukur dengan
// jangka sorong. hollow_r = radius sudut luar (tipikal 1,5-2 x tebal dinding;
// untuk hollow 40x40 bertebal 1,6 mm biasanya sekitar 3 mm).
// [UKUR] default 40 x 40 chosen karena ukuran(common) - WAJIB cek Physical.
hollow_a          = is_undef(hollow_a_ov)          ? 40.0 : hollow_a_ov;
hollow_b          = is_undef(hollow_b_ov)          ? 40.0 : hollow_b_ov;
hollow_r          = is_undef(hollow_r_ov)          ? 3.0  : hollow_r_ov;
klem_hollow_clr   = is_undef(klem_hollow_clr_ov)   ? 0.30 : klem_hollow_clr_ov;  // rongga longgar
klem_hollow_lug_p = is_undef(klem_hollow_lug_p_ov) ? 12.0 : klem_hollow_lug_p_ov; // jangkauan lug dari batang
klem_hollow_lug_d = is_undef(klem_hollow_lug_d_ov) ? 10.0 : klem_hollow_lug_d_ov; // diameter boss lug
klem_hollow_lug_t = is_undef(klem_hollow_lug_t_ov) ? 5.5  : klem_hollow_lug_t_ov; // clearance M5
// Plat dasar lebih tebal dari flange biasa (10 vs 6 mm) karena dua alasan:
//   1. jadi dudukan self-tap M5 untuk sambungan lengan (butuh engagement cukup)
//   2. plat ini menopang SELURUH berat box, jadi harus tidak lentur
klem_hollow_pelat_t = is_undef(klem_hollow_pelat_t_ov) ? 10.0 : klem_hollow_pelat_t_ov;

// Antarmuka flange lengan <-> mount (dipakai bersama semua tipe mount).
antarmuka_flange_d = is_undef(antarmuka_flange_d_ov) ? 34.0 : antarmuka_flange_d_ov;
antarmuka_flange_t = is_undef(antarmuka_flange_t_ov) ? 6.0  : antarmuka_flange_t_ov;
diameter_baut_antarmuka_d = is_undef(diameter_baut_antarmuka_d_ov) ? 5.0 : diameter_baut_antarmuka_d_ov;

dinding_dasbor_lebar    = is_undef(dinding_dasbor_lebar_ov)    ? 40.0 : dinding_dasbor_lebar_ov;
dinding_dasbor_panjang  = is_undef(dinding_dasbor_panjang_ov)  ? 60.0 : dinding_dasbor_panjang_ov;
dinding_dasbor_tebal    = is_undef(dinding_dasbor_tebal_ov)    ? 4.0  : dinding_dasbor_tebal_ov;
diameter_sekrup_dinding  = is_undef(diameter_sekrup_dinding_ov)  ? 4.5  : diameter_sekrup_dinding_ov;

// --- Lengan & kemiringan ---
// sudut_kemiringan diukur dari POSE DASAR, dan pose dasar itu sudah berarti
// "kamera lurus ke bawah" (lihat blok KEPALA di arm.scad untuk alasannya).
// Jadi:
//     sudut_kemiringan = 0   -> optik LURUS KE BAWAH (lookdown ke bed)
//     sudut_kemiringan = 20  -> optik miring 20 derajat dari tegak
//     sudut_kemiringan = 90  -> optik mendatar
// DEFAULT 0 sesuai instalasi: box digantung di frame atap, kamera lookdown ke
// bed tanaman. Paddle ada di dinding +X enclosure yang setelah rotasi menjadi
// arah horizontal menuju lengan, sehingga lengan TIDAK masuk field of view.
pelat_ujung_panjang = is_undef(pelat_ujung_panjang_ov) ? 24.0 : pelat_ujung_panjang_ov;
sudut_kemiringan  = is_undef(sudut_kemiringan_ov)  ? 0    : sudut_kemiringan_ov;
panjang_lengan    = is_undef(panjang_lengan_ov)    ? 150.0 : panjang_lengan_ov;
lebar_lengan      = is_undef(lebar_lengan_ov)      ? 16.0 : lebar_lengan_ov;
tebal_lengan      = is_undef(tebal_lengan_ov)      ? 6.0  : tebal_lengan_ov;
diameter_pivot    = is_undef(diameter_pivot_ov)    ? 5.0  : diameter_pivot_ov;

// --- Kabel ribbon CSI ---
lebar_ribbon      = is_undef(lebar_ribbon_ov)      ? 15.0 : lebar_ribbon_ov;
diameter_ribbon   = is_undef(diameter_ribbon_ov)   ? 3.0  : diameter_ribbon_ov;
ruang_ribbon      = is_undef(ruang_ribbon_ov)      ? 6.0  : ruang_ribbon_ov;

// --- Sun hood (tabung pelindung optik, opsional) ---
// PENTING untuk IR: dinding dalam matte hitam. Cahaya IR 850 nm memantul
// kuat dari permukaan putih/plastik bening dan bisa membuat \"flare\" di
// sudut gambar, yang merusak deteksi bed.
panjang_sunshield = is_undef(panjang_sunshield_ov) ? 12.0 : panjang_sunshield_ov;
bukan_sunshield   = is_undef(bukan_sunshield_ov)   ? 2.0  : bukan_sunshield_ov;
// DEFAULT MATI. Sun shield adalah corong di sekitar optik, sedangkan pada
// modul night-vision LETAK LED IR, LDR, dan trimpot sangat dekat dengan optik.
// Corong yang terlalu lebar akan:
//   (a) MENUTUPI aperture LED IR -> cahaya IR terhalang, kamera buta malam hari
//   (b) menutupi jendela LDR     -> IR menyala terus 24 jam
// Ukuran hood dihitung otomatis di enclosure.scad dari jarak LED IR sehingga
// tidak mungkin menutupi secara tidak sengaja. Nyalakan hanya setelah mengukur
// modul (Fase 1) dan pastikan ruang di sekitar optik cukup longgar.
pakai_sunshield   = is_undef(pakai_sunshield_ov)   ? false : pakai_sunshield_ov;

// =============================================================================
//  DIMENSI TURUNAN - JANGAN DIEDIT. Dihitung otomatis dari nilai di atas.
//  Kalau salah satu berubah, semua part mengikuti otomatis.
// =============================================================================

// Lebar & tinggi enclosures.
//
// LEBAR sekarang ditentukan oleh BARIS BUKAAN di muka depan, bukan lagi oleh
// PCB Pi. Alasannya: 3 bukaan besar (40 + 30 + 40 + 10 mm) plus jarak antar
// tepi dan margin butuh ~138 mm, jauh lebih lebar dari PCB Pi yang cuma 85 mm.
// Kalau lebar box tetap mengikuti Pi, bukaan optik akan keluar dari dinding.
// (bukaan_baris_lebar sendiri sudah dihitung di atas, dekat parameternya.)
lebar_min_bukaan   = bukaan_baris_lebar + 2 * bukaan_margin + 2 * encl_dinding;
lebar_min_pi       = pi_pcb_w + 2 * encl_clearance_x + 2 * encl_dinding;
encl_w = max(lebar_min_bukaan, lebar_min_pi);

// Posisi pusat tiap bukaan, dihitung dari titik tengah baris. Baris dibuat
// simetris terhadap dinding meskipun LDR hanya ada di sisi kanan.
bukaan_ir1_dx = -(bukaan_baris_lebar - bukaan_ir_d) / 2;              // IR kiri
bukaan_kamera_dx = bukaan_ir1_dx + bukaan_ir_d / 2 + bukaan_gap
                 + bukaan_kamera_d / 2;                                 // tengah
bukaan_ir2_dx = bukaan_kamera_dx + bukaan_kamera_d / 2 + bukaan_gap
              + bukaan_ir_d / 2;                                       // IR kanan
bukaan_ldr_dx = bukaan_ir2_dx + bukaan_ir_d / 2 + bukaan_gap
              + bukaan_ldr_d / 2;                                       // LDR

// Tinggi tetap mengikuti clearance Y (ruang Pi) + dinding, karena baris bukaan
// hanya setinggi bukaan_ir_d yang jauh lebih kecil dari tinggi box.
encl_h = pi_pcb_h + 2 * encl_clearance_y + 2 * encl_dinding;

// Kedalaman = tumpukan: dinding muka + jepit kamera + tikungan ribbon +
// standoff Pi + PCB + komponen teratas + ruang heatsink + tutup.
encl_d = encl_dinding
       + (dinding_jepit + panjang_pilar_jepit)   // jepit kamera
       + ruang_ribbon                            // tikungan kabel CSI
       + pi_ruang_bawah
       + pi_pcb_t
       + pi_tinggi_port
       + pi_ruang_heatsink
       + encl_lid_tebal;

// Rongga dalam (dipakai bersama oleh enclosure.scad dan enclosure_tutup.scad)
int_w = encl_w - 2 * encl_dinding;
int_h = encl_h - 2 * encl_dinding;

// Posisi pusat rusuk sudut = titik tengah footprint rusuk. enclosure_tutup
// memakai angka yang sama untuk posisi lubang baut M3, jadi keduanya selalu
// senada. Rusuk menempel ke dinding di x=int_w/2 dan y=int_h/2, lebarnya
// encl_rusuk_lebar ke arah dalam.
rusuk_x = int_w / 2 - encl_rusuk_lebar / 2;
rusuk_y = int_h / 2 - encl_rusuk_lebar / 2;

// DIAMETER LUAR klem mount, dipakai arm.scad untuk menentukan titik mulai
// batang lengan. Tanpa ini, batang lengan mulai di x=11 (flange_d/2-6)
// sementara klem pipa punya r_out 18,4 mm -> keduanya saling menembus.
// Bug ini tidak terlihat di STL terpisah, baru saat rakitan dirakit.
mount_out_r = tipe_mount == "hollow"
            ? max(hollow_a, hollow_b) / 2 + klem_hollow_clr + klem_tebal
            : tipe_mount == "pipa"
            ? diameter_pipa_luar / 2 + 0.20 + klem_tebal
            : antarmuka_flange_d / 2;

// Ketinggian BIDANG MATING paling atas pada mount, yaitu z tempat permukaan
// datar tempat flange lengan harus duduk. assembly.scad memakai angka ini
// untuk menaruh lengan, jadi semua tipe mount otomatis pas tanpa angka
// hard-coded.
//   hollow : plat atas berakhir di klem_panjang + klem_hollow_pelat_t
//   pipa   : flange_atas occupy z 0..antarmuka_flange_t
//   baut   : baut_m5 occupy z 0..antarmuka_flange_t
//   dinding: dasbor (tebal) + boss flange
mount_z_mating = tipe_mount == "hollow"
              ? (klem_panjang + klem_hollow_pelat_t)
              : tipe_mount == "dinding"
              ? (dinding_dasbor_tebal + antarmuka_flange_t)
              : antarmuka_flange_t;

// Ketebalan plat atas klem hollow (dipakai mount_base.scad)
mount_pelat_t = tipe_mount == "hollow" ? klem_hollow_pelat_t : antarmuka_flange_t;

// Diameter flange yang DIPAKAI. Harus cukup besar untuk menutupi klem mount,
// karena batang lengan baru boleh mulai di x = mount_out_r + 1 (supaya tidak
// menembus dinding klem). Kalau flangenya cuma 34 mm, meanwhile batang mulai
// di 25,3 mm untuk hollow 40x40 - keduanya TIDAK bersentuhan dan lengan
// terpecah jadi 2 komponen di STL.
flange_d_efektif = max(antarmuka_flange_d, 2 * (mount_out_r + 4));

// Muka luar paddle (bidang mating dengan pelat ujung lengan). arm.scad
// menjadikannya acuan, jadi harus dalam koordinat enclosure yang tidak ambigu.
paddle_x_luar = encl_w / 2 + paddle_tebal;

// Ketinggian titik-titik penting terhadap dasar (muka kamera luar = Z 0).
z_jepit_kamera = encl_dinding;                              // muka dalam dinding depan
z_pi_pcb       = z_jepit_kamera + dinding_jepit + panjang_pilar_jepit + ruang_ribbon
                + pi_ruang_bawah;                           // permukaan bawah PCB Pi
z_dasar_rongga = encl_d - encl_lid_tebal;                   // atap rongga

// Puncak komponen Pi (USB-A / RJ45) dan dasar rusuk sudut. Dipisah 2,6 mm
// dari puncak komponen supaya rusuk tidak pernah menabrak Pi, dan aman juga
// kalau ada heatsink yang lebih tinggi dari asumsi pi_tinggi_port.
z_ktop         = z_pi_pcb + pi_pcb_t + pi_tinggi_port;
z_rusuk        = z_ktop + 2.6;
rusuk_tinggi   = z_dasar_rongga - z_rusuk;

// Peringatan kalau rusuk jadi terlalu pendek untuk self-tap M3.
if (rusuk_tinggi < encl_tap_tinggi + 2)
    echo(str("[PERINGATAN] rusuk sudut hanya ", rusuk_tinggi,
             " mm, kurang dari ", encl_tap_tinggi + 2,
             " mm untuk self-tap M3 + dinding bawah. Kurangi pi_ruang_heatsink."));

// Validasi clearance per sumbu. Dijaga di sini (bukan hanya di preview) karena
// preview bukan bagian dari jalur build part: kalau clearance Y dikecilkan lagi,
// semua part TETAP berhasil dicetak tanpa error, lalu baru menyesal setelah
// dirakit. Jadi harus diperingatkan lebih awal, di sini.
if (encl_clearance_y < 13.5)
    echo(str("[PERINGATAN] clearance Y hanya ", encl_clearance_y,
             " mm. RJ45 Pi 4B menonjol 13,5 mm dari tepi PCB, jadi port akan ",
             "MENABRAK dinding -Y. Naikkan encl_clearance_y ke >= 14 mm."));

// Validasi feature kecil (trimpot, LED indikator) terhadap baris bukaan.
// Lubang kecil yang jatuh di dalam bukaan besar akan hilang tanpa error:
// OpenSCAD tetap menampilkan keduanya sebagai lubang di bidang 2D, jadi
// tidak ada yang gagal saat render - lubang kecilnya просто ikut hilang.
if (led_indikator_ada
    && abs(led_indikator_dy) < bukaan_ir_d / 2 + led_indikator_d / 2)
    echo(str("[PERINGATAN] LED indikator (dy = ", led_indikator_dy,
             " mm) jatuh DI DALAM bukaan IR (radius ", bukaan_ir_d / 2,
             " mm) dan tidak akan terlihat. Naikkan led_indikator_dy."));
if (abs(trimpot_dy) < bukaan_ir_d / 2 + trimpot_d / 2)
    echo(str("[PERINGATAN] Trimpot (dy = ", trimpot_dy,
             " mm) jatuh DI DALAM bukaan IR (radius ", bukaan_ir_d / 2,
             " mm) dan tidak bisa dijangkau obeng. Naikkan atau turunkan trimpot_dy."));

// Ringkasan dimensi turunan - sangat berguna saat debug, karena semua angka
// di bawah dihitung berantai. Kalau ada yang salah, ini titik mulainya.
echo(str("[DIMENSI] encl = ", encl_w, " x ", encl_h, " x ", encl_d,
         " | int = ", int_w, " x ", int_h));
echo(str("[CLEARANCE] x = ", encl_clearance_x, " mm | y = ", encl_clearance_y, " mm"));
echo(str("[BUKAAN] baris = ", bukaan_baris_lebar, " mm | IR d=", bukaan_ir_d,
         " @ x=", bukaan_ir1_dx, " dan x=", bukaan_ir2_dx,
         " | kamera d=", bukaan_kamera_d, " @ x=", bukaan_kamera_dx,
         " | LDR d=", bukaan_ldr_d, " @ x=", bukaan_ldr_dx));
echo(str("[RUSUK]  x=", rusuk_x, " y=", rusuk_y,
         " z_dasar=", z_rusuk, " atap=", z_dasar_rongga, " tinggi=", rusuk_tinggi));


// =============================================================================
//  HELPER GEOMETRI BERSAMA
// =============================================================================
//  Chamfer 45 derajat pada 4 tepi vertikal. Ada di params.scad (bukan
//  enclosure.scad) karena dipakai juga oleh enclosure_tutup.scad, sehingga
//  kulit box danutupnya selalu memakai profil yang sama persis.
// =============================================================================
//  Cara kerjanya: profile awal dipotong dengan persegi yang DIPUTAR 45 derajat.
//  Jarak potongan tegak lurus ke setiap sudut sama dengan "c", jadi keempat
//  chamfer sama panjang walaupun mukanya bukan persegi sempurna.
//  Offset r di dalam dipakai supaya sudut tetap sedikit membulat dan tidak
//  runcing tajam.
module profil_chamfer(lebar, tinggi, c) {
    s = ((lebar + tinggi) / 2 - c * sqrt(2)) / sqrt(2);   // setengah sisi kotak 45
    r = radius_sudut_dudukan;
    intersection() {
        // PENTING: harus pakai operasi "closing" = offset(r) lalu offset(delta=-r).
        // Kalau hanya offset(r),persegi ikut MEMBESAR 2*r di semua sisi, jadi
        // box jadi 100,8 x 71,8 padahal enclosurenya 96,8 x 67,8 - dan rongga
        // dalam ikut melebar sehingga dinding hilang dan rusuk sudut lepas.
        offset(r = r) offset(delta = -r)
            square([lebar, tinggi], center = true);
        if (c > 0)
            rotate([0, 0, 45])
                square([2 * s, 2 * s], center = true);
    }
}
