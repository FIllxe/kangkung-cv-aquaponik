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
    x1 = panjang_lengan + pelat_ujung_panjang / 2 - flange_t; // batang berhenti di muka dalam pelat ujung
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
//
// BUG LAMA (tidak pernah ketahuan karena preview hanya dilihat sekilas):
// versi sebelumnya membuat pelat sebagai plat HORIZONTAL (linear_extrude
// profil datar di XY, pelat normal +Z, z 0..flange_t) dengan lubang baut
// VERTIKAL di (x=panjang_lengan, y=+/-13). Padahal tap hole paddle ada di
// muka VERTIKAL box (normal +X) sejajar sumbu X pada y=+/-13 dan setinggi
// pusat paddle (z = flange_t + paddle_tinggi/2 = 18). Akibatnya:
//   - lubang pelat dan tap paddle tidak pernah sejajar (sumbu Z vs sumbu X)
//   - pelat (x 138..162) dan paddle (x 162..173) hanya bersinggungan di
//     satu garis tepi, baut tidak bisa menembus keduanya
//   - plat horizontal juga menutup jalur box yang turun ke bawah bidang lengan
// Versi ini: pelat VERTIKAL tebal flange_t di arah X, muka luar = poros pv
// (titik duduk muka paddle), tinggi menutup seluruh footprint paddle, dan
// 2 lubang clearance M4 sepanjang sumbu X tepat sejajar tap hole paddle.
module pelat_ujung() {
    z_poros  = flange_t + paddle_tinggi / 2;             // pusat paddle (18)
    xl_out   = panjang_lengan + pelat_ujung_panjang / 2; // muka luar = poros pv (162)
    lebar_p  = paddle_lebar + 4;                         // lebar paddle + fillet r2
    tinggi_p = z_poros + paddle_tinggi / 2 + 2;          // z 0..tinggi_p: tutup paddle penuh
    translate([xl_out, -lebar_p / 2, 0])
        rotate([0, -90, 0])                              // profil -> bidang YZ, ekstrusi ke -X
            // +1 mm: ekstrusi menembus 1 mm ke dalam batang lengan (yang
            // berhenti di xl_out - flange_t) supaya union punya volume
            // intersection nyata, bukan cuma bidang bersentuhan - kalau tidak,
            // CGAL memperingatkan "not a valid 2-manifold" saat ekspor STL.
            linear_extrude(height = flange_t + 1)
                difference() {
                    square([tinggi_p, lebar_p]);
                    // Lubang clearance M4, sumbu X, sejajar tap paddle
                    // (y = +/-paddle_jarak_baut, z = z_poros).
                    for (sy = [-1, 1])
                        translate([z_poros, lebar_p / 2 + sy * paddle_jarak_baut])
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
    // paddle, setinggi pusat paddle. pv dinyatakan dalam koordinat FRAME
    // LENGAN (z = 0 = bidang mating flange ke mount), jadi seluruh rangkaian
    // WAJIB diterjemahkan ke mount_z_mating karena di assembly.scad lengan
    // duduk di z = mount_z_mating.
    //
    // BUG LAMA: translate([0,0,mount_z_mating]) tidak ada, sehingga kepala
    // (box + paddle) terlalu rendah 30 mm pada klem hollow / 6 mm pada
    // tipe pipa. Geometri lama itu sumber tiga gejala sekaligus:
    //   - profil depan: paddle menggantung jauh di bawah pelat ujung lengan
    //   - lubang pelat dan tap paddle tidak sejajar vertikal
    //   - mode ledakan: batang lengan kelihatan menembus box
    pv = [panjang_lengan + pelat_ujung_panjang / 2, 0,
          flange_t + paddle_tinggi / 2];
    translate([0, 0, mount_z_mating])
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
