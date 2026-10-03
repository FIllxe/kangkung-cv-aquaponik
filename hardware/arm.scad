// =============================================================================
// arm.scad - Lengan kamera + engsel kemiringan
// =============================================================================
//  Menghubungkan flange mount_base.scad ke enclosure.scad (kamera + Pi 4B).
//
//  Orientasi: flange mount di titik asal, lengan memanjang ke +X, lalu
//  kepala dimiringkan sebesar sudut_kemiringan.
//     sudut_kemiringan = 0   -> optik mendatar (sepanjang lengan)
//     sudut_kemiringan = 90  -> optik lurus ke bawah (top-down ke bed)
//
//  RANGKAIAN UJUNG LENGAN
//    rotate([0,-90,0]) Needed untuk memutar enclosure supaya paddle di
//    dinding +X menjadi normal +Z, yaitu menghadap pelat ujung lengan.
//    Optik jadi mendatar sepanjang lengan, sehingga bisa dimiringkan oleh
//    engsel berporos Y.
//    Geser X sebesar encl_d/2 karena pusat simetri enclosure ada di
//    tengah-tebalnya, sedangkan paddle ada di sisi +X.
// =============================================================================

tampilkan_standalone_ov = false;
include <enclosure.scad>
include <params.scad>

eps       = toleransi_cetak;
flange_d  = flange_d_efektif;   // ikut menyesuaikan ukuran klem mount
flange_t  = antarmuka_flange_t;

// --- Baut M5: kepala + batang, untuk sambungan flange ---
module baut_m5(kepala = 8, batang = 20, t = flange_t) {
    translate([0, 0, t]) {
        cylinder(d = kepala, h = 4);
        translate([0, 0, 4])
            cylinder(d = 5, h = batang);
    }
}

// --- Flange bawah (disambung ke mount_base) ---
// CATATAN: JANGAN pakai translate([0,0,flange_t/2]) di sini. Flange harus
// menempati z = 0 .. flange_t karena z = 0 adalah bidang mating yang
// menempel ke permukaan mount. Versi lama memakai translate tersebut
// dengan maksud "memusatkan", padahal linear_extrude sudah mulai dari 0,
// jadi flange tergeser ke z 3..9 - bidang mating meleset 3 mm ke atas.
module flange_bawah() {
    linear_extrude(height = flange_t)
        difference() {
            circle(d = flange_d);
            circle(d = diameter_baut_antarmuka_d - 0.9);
        }
}

// --- Bodi lengan ---
// x0 HARUS lebih besar dari mount_out_r (radius luar klem mount), bukan
// flange_d/2 - 6. Versi lama memakai x0 = 11, sementara klem pipa punya
// r_out 18,4 mm dan klem hollow 40x40 punya 24,3 mm - artinya batang lengan
// menembus dinding klem. Bug itu tidak terlihat di STL terpisah (lengan dan
// mount adalah dua part berbeda), baru ketahuan saat rakitan dirakit.
// Sisa 1 mm jadi celah, jadi tidak ada gesekan PETG-ke-PETG yang membuat
// lengan "nyangkut" dan susah dilepas.
module lengan() {
    x0 = mount_out_r + 1;
    x1 = panjang_lengan - pelat_ujung_panjang / 2;   // batang berhenti di awal pelat
    panjang = x1 - x0;
    tengah = (x0 + x1) / 2;
    // Baris batang DISETELARASKAN dengan flange (z 0..flange_t), bukan
    // bergeser di z -3..+3 seperti versi lama. Alasannya: batang sekarang
    // duduk DI ATAS plat mount, jadi seluruh profil lengan harus mulai dari
    // z = 0. Kalau batang melayang di bawah flange, batang akan menembus
    // plat mount.
    zt = flange_t / 2;
    difference() {
        translate([tengah, 0, zt])
            cube([panjang, lebar_lengan, tebal_lengan], center = true);
        // Lubang kabel sepanjang lengan
        translate([tengah, 0, zt - tebal_lengan / 2 + diameter_ribbon / 2 + 0.8])
            cube([panjang - 20, diameter_ribbon, 6], center = true);
    }
}

// --- Pelat ujung: menyambung lengan ke paddle enclosure ---
// 2x baut M4 x 25 mengunci sudut kemiringan lewat gesekan. Kencangkan ulang
// berkala: siklus panas dan getaran bisa melonggarkan sambungan ini.
// CATATAN z: pelat occupy z 0..flange_t, sama seperti flange dan batang, agar
// muka plates-nya persis di z = flange_t tempat muka luar paddle bertumpu.
// Versi lama memakai translate([...,flange_t/2]) sehingga pelat ikut bergeser
// ke z 3..9 dan paddle menusuk 3 mm ke dalam pelat.
module pelat_ujung() {
    translate([panjang_lengan, 0, 0])
        linear_extrude(height = flange_t)
            difference() {
                offset(r = 3)
                    square([24, lebar_lengan], center = true);
                // Lubang baut harus OBJEK 2D (circle), bukan cylinder:
                // seluruh blok ini berada di dalam linear_extrude, dan
                // OpenSCAD tidak mendukung campuran 2D + 3D di satu operasi.
                for (sy = [-1, 1])
                    translate([0, sy * paddle_jarak_baut])
                        circle(d = paddle_clr_d);
            }
}

// =============================================================================
//  KEPALA - kunci kerangka koordinat untuk kemiringan
// =============================================================================
//  Dua bug besar yang TIDAK pernah ketahuan dari STL terpisah:
//
//  1) KERANGKA KEMIRINGAN. Versi lama memakai
//     rotate([0,sudut,0]) rotate([0,-90,0]) + translate(...paddle_x_luar).
//     Translate itu hanya benar untuk sudut 0. Pada sudut 90, dua rotasi itu
//     saling meniadakan (komposisinya identitas) sehingga kepala tidak ikut
//     miring sama sekali - kamera tetap mendatar.
//
//  2) ARAH PASANG PADDLE. Paddle ada di dinding SAMPING box (+X) sementara
//     optik ada di muka -Z. Keduanya tegak lurus. Kalau kamera diarahkan lurus
//     ke bawah, sisi paddle otomatis ikut menjadi mendatar - dan karena box
//     tumbuh ke arah berlawanan dengan paddle, box akan MENYERANG batang
//     lengan. Jadi "kamera tegak ke bawah" dan "box menggantung di luar
//     lengan" tidak bisa dicapai dengan rotasi pada sumbu Y.
//
//  SOLUSI: sumbu engsel dipindah ke sumbu Y, dan pose dasar didefinisikan
//  sebagai "kamera sudah lurus ke bawah". rotate([0,0,180]) dipakai supaya sisi
//  paddle menghadap ke lengan sementara box tumbuh menjauh - persis seperti
//  lampu gantung di ujung lengan. Kemiringan diukur dari pose itu, sehingga
//  sudut_kemiringan = 0 sudah berarti KAMERA LURUS KE BAWAH, persis yang
//  dibutuhkan untuk lookdown ke bed dari frame atap.
// =============================================================================
//
//  kepala_dasar(): asal di PUSAT MUKA PADDLE, sumbu +X = arah keluar paddle,
//                  sumbu +Z = arah tutup. Box tumbuh ke -X, optik ke -Z.
module kepala_dasar() {
    translate([-paddle_x_luar, 0, -encl_d / 2])
        children();
}

module kepala_transform() {
    // Titik poros = muka luar pelat ujung yang jadi bidang mating dengan
    // paddle, setinggi pusat paddle.
    pv = [panjang_lengan + pelat_ujung_panjang / 2, 0,
          flange_t + paddle_tinggi / 2];
    translate(pv)
        rotate([0, sudut_kemiringan, 0])        // kemiringan terhadap pose dasar
            translate([-pv[0], 0, -pv[2]])     // geser poros ke titik asal
                translate(pv)                   // LETAKKAN kepala di ujung lengan
                    // Balik 180 derajat terhadap sumbu Z: sisi paddle menghadap
                    // lengan, box tumbuh menjauhi lengan. Tanpa ini box akan
                    // menutupi batang lengan.
                    rotate([0, 0, 180])
                        children();
}

// --- Kepala: enclosure (kamera + Pi 4B) di ujung lengan ---
// WAJIB memanggil kepala_dasar(): tanpa itu asal kerangkanya masih di pusat
// box, bukan di muka paddle, dan seluruh kepala bergeser.
module kepala_enclosure() {
    kepala_transform() kepala_dasar() enclosure_kepala();
}

// --- Jepit kamera + tutup, memakai kerangka yang sama persis ---
// Tutup dicetak dengan pelat di meja dan skirt ke ATAS, sedangkan saat
// dipasang skirt harus masuk ke BAWAH. Karena itu tutup dibalik 180 derajat.
module kepala_jepit_dan_tutup() {
    kepala_transform() kepala_dasar() {
        color("SteelBlue") camera_holder_isi();
        translate([0, 0, encl_d])
            rotate([180, 0, 0])
                color("SlateGray") enclosure_tutup();
    }
}

// Catatan PENTING untuk build: file ini mengekspor HANYA lengan. Kepala
// (enclosure) adalah part terpisah yang disambung dengan baut, jadi kalau
// ikut diekspor ke STL yang sama, slicer akan memperlakukannya sebagai satu
// benda dan salah orientasi cetak. Kepala dirender terpisah lewat
// enclosure.scad, dan digabung hanya di assembly.scad untuk pratinjau.
module arm() {
    color("DimGray") flange_bawah();
    color("DimGray") lengan();
    color("DimGray") pelat_ujung();
}

// Render mandiri. Guard-nya PENTING: karena arm.scad di-`include` oleh
// assembly.scad, panggilan arm() di baris terakhir akan ikut dieksekusi dan
// muncul lengan kedua di z = 0 (belum digeser ke mount). Variabel guard-nya
// sengaja berbeda dari tampilkan_standalone_ov, karena arm.scad sudah
// menyetel variabel itu menjadi false untuk dipakai enclosure.scad.
cetak_standalone = is_undef(cetak_standalone_ov) ? true : cetak_standalone_ov;
if (cetak_standalone) arm();
