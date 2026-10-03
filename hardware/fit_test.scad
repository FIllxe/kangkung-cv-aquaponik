// =============================================================================
// fit_test.scad - Pelat uji pola lubang. CETAK INI DULU.
// =============================================================================
//  Biaya: 3 g filamen, 10 menit cetak. Menghemat 5 jam + 80 g filamen kalau
//  pola lubang ternyata salah.
//
//  Isi plat (semua skala 1:1, cetak TANPA scaling):
//    A. POLA LUBANG KAMERA  - 4 lubang M2 + outline PCB 25 x 24
//    B. POLA LUBANG PI 4B   - 4 lubang pada jarak 58 x 49
//    C. TATA LETAK APERTURE - optik + 2 LED IR + LDR + trimpot
//    D. PENGGARIS BERENGKAH - 100 mm, tick 5 mm, untuk mengukur modul
//
//  CARA PAKAI
//    1. Cetak plat ini:  .\build.ps1 -Part fit_test
//    2. A: letakkan PCB modul kamera di atas pola A.
//         - 4 lubang TIDAK cocok -> ukur ulang pola_lubang_x/y di params.scad
//         - sudah cocok        -> pola A benar, lanjut ke B dan C
//    3. B: putar baut M2.5 x 8 sebanyak 2 kali untuk cek daya self-tap.
//    4. C: bandingkan jarak aperture dengan modul aslinya (pakai penggaris).
//    5. D: ukur modul langsung, lalu tulis angkanya ke params.scad.
//    6. Ulangi .\build.ps1 -Part fit_test sampai semuanya cocok.
//
//  SETELAH SEMUA LOLOS: hapus plat ini, baru cetak part sungguhan.
// =============================================================================

include <params.scad>

tebal = 3.0;
L = 210;   // lebar plat  (A + B di baris atas, 3x pola C di bawah)
W = 140;   // tinggi plat (3x pola C + penggaris D di baris bawah)
tebal_garis = 0.8;   // lebar garis penanda

// Empat tanda sudut PCB. Sengaja BUKAN persegi outline penuh: dengan pola
// lubang default yang cuma 2 mm dari tepi PCB, garis outline utuh akan
    // menyentuh lubang M2 dan menyebabkan plat terpotong menjadi beberapa
// (terverifikasi: hasil ekspor jadi 6 komponen). Bracket sudut yang pendek
// dan ditipkan 0,5 mm tidak pernah bersinggungan dengan lubang.
module sudut_pcb(w, h, t = 0.5, l = 4) {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * w / 2, sy * h / 2])
            difference() {
                square([l, l]);
                square([l - t, l - t]);
            }
}

// Semua cutter dibuat 3D eksplisit. Kalau cutter dibiarkan 2D, OpenSCAD
// tidak selalu mengekstrusinya setebal plat, sehingga lubangnya hilang.

// --- A. pola lubang kamera (kiri atas) ---
module uji_pola_kamera() {
    translate([-60, 45, 0])
        linear_extrude(height = tebal + 1) {
            // 4 tanda sudut PCB 25 x 24 supaya posisi lubang bisa dinilai
            // relatif terhadap tepi papan
            sudut_pcb(kamera_pcb_w, kamera_pcb_h);
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * pola_lubang_x / 2, sy * pola_lubang_y / 2])
                    circle(d = diameter_sekrup_m2 + 0.6);
        }
}

// --- B. pola lubang Raspberry Pi 4B (kanan atas) ---
module uji_pola_pi() {
    translate([45, 42, 0])
        linear_extrude(height = tebal + 1)
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * pi_lubang_x / 2, sy * pi_lubang_y / 2])
                    circle(d = pi_lubang_d - 0.3);  // sama dgn standoff di params
}

// --- C. tata letak aperture (3 pola lengkap, kiri bawah) ---
// TIGA POLA LENGKAP berdampingan. Yang divariasikan adalah TIGA dimensi
// sekaligus - diameter optik, diameter LED IR, dan jarak antar dua LED - karena
// ketiganya tidak bisa ditebak secara terpisah.
//
// Kenapa rentangnya lebar: ada dua sumber informasi yang saling bertentangan.
//
//   H1 - foto modul Anda sendiri: ketiga barrel tampak hampir sama besar dan
//        memenuhi hampir seluruh lebar PCB 25 mm.
//   H2 - viewport desain asal: lubang LED IR terlihat sekitar 1,75 kali lebih
//        besar dari lubang optik, dengan celah jelas di antaranya.
//
// H2 TIDAK bisa dipakai untuk menentukan ukuran mm, dan alasannya aritmetis:
// pada H2 jarak pusat optik ke pusat LED adalah sekitar 1,87 kali diameter
// optik, jadi jarak dua LED adalah 3,74 kali diameter optik. Dengan optik
// 13 mm berarti 49 mm - mustahil pada PCB 25 mm. Jadi lingkaran pada viewport
// itu hampir pasti bukan barrel modul 25 mm pada skala 1:1, dan tidak boleh
// dipakai sebagai acuan dimensi.
//
// Karena itu H1 yang dipakai, dan rentang pola dibuat cukup lebar untuk
// menutup H1 maupun bila ternyata modul Anda lebih besar dari dugaan.
pola_apertur = [
    [ 9.0,  9.0, 18.0],   // barrel kecil
    [11.0, 11.0, 21.0],   // sedang
    [13.0, 14.0, 24.0]    // besar
];

module satu_pola_apertur(d_lensa, d_led, jarak_x) {
    linear_extrude(height = tebal + 1) {
        // Baris bukaan utama, mengikuti params.scad supaya hasil uji sama
        // persis dengan lubang di enclosure.scad.
        if (led_ir_ada) {
            translate([bukaan_ir1_dx, 0]) circle(d = bukaan_ir_d);
            translate([bukaan_ir2_dx, 0]) circle(d = bukaan_ir_d);
        }
        translate([bukaan_kamera_dx, 0]) circle(d = bukaan_kamera_d);
        translate([bukaan_ldr_dx, 0]) circle(d = bukaan_ldr_d);

        // Akses kecil: trimpot di bawah baris, 2 LED indikator di atasnya.
        translate([bukaan_kamera_dx, trimpot_dy])
            circle(d = trimpot_d + 2.0);
        if (led_indikator_ada)
            for (sx = [-1, 1])
                translate([bukaan_kamera_dx + sx * led_indikator_dx,
                           led_indikator_dy])
                    circle(d = led_indikator_d);
    }
}

// Label nama pola. Dibuat SEBAGAI HURUF EMBOSS (dinaikkan dari permukaan
// plat), BUKAN diukir. Kalau diukir, huruf yang punya rongga dalam - seperti
// 0, 8, 6, 9, 4 - meninggalkan pulau material setebal 3 mm yang menggantung
// di tengah lubang huruf, dan STL jadi terbaca 9 komponen terpisah.
module label_pola() {
    for (i = [0 : len(pola_apertur) - 1])
        translate([-55 + i * 55, -20 - 34, tebal])
            linear_extrude(height = 0.8)
                text(str("L", pola_apertur[i][0], " R", pola_apertur[i][1], " x", pola_apertur[i][2]),
                     size = 5, halign = "center", valign = "center");
}

module uji_apertur() {
    for (i = [0 : len(pola_apertur) - 1])
        translate([-55 + i * 55, -20, 0])
            satu_pola_apertur(pola_apertur[i][0], pola_apertur[i][1], pola_apertur[i][2]);
}

// --- D. penggaris berengkah 100 mm (kanan bawah) ---
module uji_penggaris() {
    x0 = 0;
    y0 = -W / 2 + 4;
    linear_extrude(height = tebal + 1) {
        translate([x0, y0, 0]) square([100, tebal_garis]);
        for (i = [0 : 20])
            translate([x0 + i * 5, y0, 0])
                square([tebal_garis, (i % 2 == 0) ? 6 : 3]);
    }
}

module fit_test() {
    union() {
        difference() {
            linear_extrude(height = tebal)
                offset(r = 4)
                    square([L, W], center = true);
            uji_pola_kamera();
            uji_pola_pi();
            uji_apertur();
            uji_penggaris();
        }
        // Label ditambahkan SESUDAH potongan, jadi jadi huruf emboss yang
        // menempel ke plat dan tidak pernah jadi pulau material.
        label_pola();
    }
}

fit_test();
