// =============================================================================
// mount_base.scad - Antarmuka ke permukaan pemasangan
// =============================================================================
//  Empat tipe di params.scad -> tipe_mount:
//    "pipa"    : klem busur 300 derajat menjepit pipa bulat (diameter_pipa_luar)
//    "hollow"  : klem C untuk BESI HOLLOW PERSEGI / stal kotak (frame atap)
//    "baut"    : flange dengan lubang M5 untuk rangka logam
//    "dinding" : dasbor lebar + 2 lubang sekrup ke dinding
//
//  Semua tipe menyisakan bidang mating datar di ujung atas (sisi +Z) sebagai
//  tempat lengan kamera disambung, sehingga panjang lengan bebas diubah
//  tanpa mencetak ulang bagian klem.
//
//  KLEM HOLLOW - KENAPA BUKAN CINCIN PENUH
//    Klem C yang kaku (membungkus 270 derajat) hanya bisa dipasang dengan
//    DISELIPKAN DARI UJUNG hollow, karena dinding klem tidak bisa dilentarkan.
//    Kalau frame atap sudah terpasang, itu tidak mungkin. Solusinya: klem
//    dibuka di satu sisi, lalu dua lug diikat satu baut M5 -> dua bagian,
//    bisa dipasang di mana saja sepanjang hollow.
//
//  ARAH PASANG (klem hollow)
//    1. cetak klem_hollow
//    2. badan C masuk dari bawah hollow (sisi -Y), celah menghadap +Y
//    3. masukkan baut M5 ke dua lug, kencangkan sampai celah rapat
//    4. pasang lengan: baut M5 kedua lewat flange lengan ke lubang tengah
//       plat dasar (self-tap)
//
//  BEBAN: plat dasar (klem_hollow_pelat_t, 10 mm) menopang SELURUH berat box
//  dan sekaligus jadi dudukan self-tap M5 lengan, jadi sengaja lebih tebal
//  dari flange tipe lain yang cuma 6 mm.
// =============================================================================

include <params.scad>

flange_d = flange_d_efektif;   // ikut menyesuaikan ukuran klem mount
flange_t = antarmuka_flange_t;

clr_m5_rapat   = diameter_baut_antarmuka_d - 0.9;  // self-tap M5 (flange lengan)
clr_m5_longgar = diameter_baut_antarmuka_d + 0.5;  // clearance M5 (baut klem)

// Versi "_isi" dipakai assembly.scad (dibungkus union), versi polos
// untuk render/cetak mandiri.
module mount_base_isi() {
    if (tipe_mount == "pipa") {
        klem_pipa();
        flange_atas();
    } else if (tipe_mount == "hollow") {
        klem_hollow();
    } else if (tipe_mount == "baut") {
        flange_baut();
    } else if (tipe_mount == "dinding") {
        dasbor_dinding();
    } else {
        echo("tipe_mount tidak dikenal: ", tipe_mount);
    }
}

// Flange tipis di bagian atas klem, menjadi dudukan baut M5 untuk lengan
// CATATAN: tanpa translate z. Flange occupy z 0..flange_t supaya z = 0
// adalah bidang mating yang menempel ke lengan. Dulu ada
// translate([0,0,flange_t/2]) dengan maksud "memusatkan", padahal
// linear_extrude sudah mulai dari z 0 - hasilnya flange tergeser ke
// z 3..9 dan mating face meleset 3 mm ke atas.
module flange_atas() {
    linear_extrude(height = flange_t)
        difference() {
            circle(d = flange_d);
            circle(d = clr_m5_rapat);
        }
}

// --- Baut M5 pada flange: dipakai bersama semua tipe ---
// Sama seperti flange_atas(): occupy z 0..t, tanpa translate.
module baut_m5(t = flange_t) {
    linear_extrude(height = t)
        difference() {
            circle(d = flange_d);
            circle(d = clr_m5_rapat);
        }
}

// =============================================================================
//  KLEM HOLLOW PERSEGI (tipe_mount = "hollow")
// =============================================================================
//  Profile hollow memakai operasi "closing": offset(r) lalu offset(delta = -r).
//  Itu membulatkan HANYA sudut dalam dan menyisakan sudut luar tetap siku -
//  persis seperti penampang luar besi hollow sungguhan. Kalau cukup pakai
//  offset(r) saja, sudut dalam ikut melebar dan klem tidak akan menempel
//  ke hollow, hanya menyentuhnya di tengah sisi.
module profil_dalam_hollow() {
    a = hollow_a / 2 + klem_hollow_clr;
    b = hollow_b / 2 + klem_hollow_clr;
    r = hollow_r + klem_hollow_clr;
    offset(r = r) offset(delta = -r)
        square([2 * a, 2 * b], center = true);
}

// Permukaan luar klem = offset normal dari profil dalam setebal klem_tebal,
// sehingga ketebalan dinding klem seragam di semua sisi termasuk di sudut.
module profil_luar_hollow() {
    offset(delta = klem_tebal) profil_dalam_hollow();
}

// Badan klem: 3 sisi (-X, -Y, +X), terbuka di sisi +Y untuk installation
module klem_hollow_cshape() {
    a = hollow_a / 2 + klem_hollow_clr + klem_tebal;
    b = hollow_b / 2 + klem_hollow_clr + klem_tebal;
    difference() {
        difference() {
            profil_luar_hollow();
            profil_dalam_hollow();
        }
        // Buang dinding +Y. Lebar penuh 2*a, sehingga dinding -X dan +X ikut
        // hilang di baris paling +Y - inilah yang membuat bentuknya "C".
        translate([-a, b - klem_tebal - 1, -1])
            square([2 * a, klem_tebal + 2]);
    }
}

// Satu lug baut: web segitiga dari dinding sisi ke boss di ujungnya.
// Dibuat penuh setinggi klem, jadi aman tanpa support saat dicetak.
module klem_hollow_lug(sx) {
    a = hollow_a / 2 + klem_hollow_clr + klem_tebal;
    b = hollow_b / 2 + klem_hollow_clr + klem_tebal;
    y_boss = b + klem_hollow_lug_p;
    hull() {
        // pangkal menempel dinding sisi, setinggi penuh
        translate([sx * (a - klem_tebal / 2), 0])
            square([klem_tebal, 2 * b], center = true);
        // boss tempat baut M5 menyeberang
        translate([sx * (a - klem_tebal / 2), y_boss])
            circle(d = klem_hollow_lug_d);
    }
}

// Klem hollow: PLAT DI ATAS (z mount_pelat_t .. +mount_pelat_t), badan C dan
// lug DI BAWAHNYA (z 0 .. klem_panjang).
//
// Kenapa plat harus di atas:
//   - Plat itu yang jadi dudukan baut M5 lengan, jadi lengan harus bisa
//     duduk DI ATASNYA. Kalau plat di bawah, batang lengan akan menembus.
//   - Klem ini juga jadi tempat hollow "berjepit" antara plat atas dan C bawah,
//     persis cara klem C pada umumnya bekerja.
//   - Untuk mounting di frame atap, orientasi ini juga benar: plat menyentuh
//     sisi atas hollow, lengan menjulang ke atas dari situ.
module klem_hollow() {
    a = hollow_a / 2 + klem_hollow_clr + klem_tebal;
    y_boss = hollow_b / 2 + klem_hollow_clr + klem_tebal + klem_hollow_lug_p;
    difference() {
        union() {
            // --- badan C + 2 lug, z 0 .. klem_panjang ---
            union() {
                linear_extrude(height = klem_panjang) klem_hollow_cshape();
                for (sx = [-1, 1])
                    linear_extrude(height = klem_panjang) klem_hollow_lug(sx);
            }
            // --- plat ATAS: duduk di puncak badan C, z klem_panjang .. +pelat ---
            // Plat ini yang jadi dudukan baut M5 lengan, jadi lengan bisa
            // duduk DI ATASNYA. Kalau plat di bawah, batang lengan akan
            // menembus. Untuk mounting di frame atap orientasi ini juga
            // benar: plat menyentuh sisi atas hollow.
            translate([0, 0, klem_panjang])
                linear_extrude(height = mount_pelat_t)
                    difference() {
                        profil_luar_hollow();
                        circle(d = clr_m5_rapat);   // self-tap M5 untuk lengan
                    }
        }
        // lubang baut M5 melintang, setinggi tengah klem
        for (sx = [-1, 1])
            translate([sx * (a - klem_tebal / 2), y_boss, klem_panjang / 2])
                rotate([-90, 0, 0])
                    cylinder(d = klem_hollow_lug_t, h = klem_hollow_lug_d * 3,
                             center = true);
    }
}

// --- Tipe 1: klem pipa dua bagian ---
// Cangkang busur 300 derajat (bukan cincin penuh) agar bisa dipasang ke
// pipa tanpa harus membelah pipa.
// Busur dibuka di sisi +Y (arah depan), bukan di sisi atas, supaya klem
// tetap menggantung di Around pipa saat lengan kamera menekan ke bawah.
module busur(r, tebal, tinggi, sudut_buka = 60) {
    r_out = r + tebal;
    difference() {
        linear_extrude(height = tinggi)
            difference() {
                circle(r = r_out);
                circle(r = r);
            }
        // Potong sudut pembuka (60 derajat) menghadap +Y
        rotate([0, 0, 90 - sudut_buka / 2])
            translate([0, -r_out - 1, -1])
                linear_extrude(height = tinggi + 2)
                    square([2 * r_out + 2, r_out + 1]);
    }
}

module klem_pipa() {
    r_in = diameter_pipa_luar / 2 + 0.20;
    r_out = r_in + klem_tebal;
    tinggi_klem = klem_panjang;

    // Klem digantung, opening menghadap +Y
    translate([0, 0, flange_t]) rotate([0, 0, 180])
        busur(r_in, klem_tebal, tinggi_klem, 60);

    // Baut pengetat klem (sumbu X, memotong celah pembuka).
    // PENTING: cakram lug harus diberi web yang menyambungkannya ke busur.
    // Tanpa web, lug hanya menyentuh busur di satu titik dan diekspor STL
    // sebagai komponen terpisah yang akan jatuh sendiri saat dicetak.
    // Web diarahkan ke sisi +Y karena busur (setelah rotate 180) ada di +Y.
    for (sx = [-1, 1])
        translate([sx * r_out, 0, flange_t + tinggi_klem / 2])
            rotate([0, 90, 0])
                linear_extrude(height = klem_tebal, center = true)
                    difference() {
                        union() {
                            circle(d = 7);
                            translate([-7, 0])
                                square([14, r_out + 2]);
                        }
                        circle(d = diameter_baut_antarmuka_d - 0.9);
                    }
}

// --- Tipe 2: flange baut M5 ---
module flange_baut() {
    baut_m5();
    // Penguat ribs
    for (a = [0, 90, 180, 270])
        rotate([0, 0, a])
            translate([flange_d / 2 - 2, 0, 0])
                rotate([90, 0, 0])
                    linear_extrude(height = flange_t)
                        square([10, 6], center = true);
}

// Dudukan dinding: dasbor + boss di belakang, ketebalannya realistis.
module dasbor_dinding() {
    linear_extrude(height = dinding_dasbor_tebal)
        difference() {
            offset(r = 6)
                square([dinding_dasbor_lebar, dinding_dasbor_panjang], center = true);
            // Lubang sekrup dinding (2 buah, simetris)
            for (sy = [-1, 1])
                translate([0, sy * dinding_dasbor_panjang / 4])
                    circle(d = diameter_sekrup_dinding);
        }
    // Boss tengah untuk disambung lengan
    translate([0, 0, dinding_dasbor_tebal])
        linear_extrude(height = flange_t)
            difference() {
                circle(d = flange_d);
                circle(d = clr_m5_rapat);
            }
}

// --- Render mandiri (dilewati ketika di-include assembly) ---
if (is_undef(tampilkan_standalone_ov) || tampilkan_standalone_ov) {
    color("DimGray") mount_base_isi();
}
