// =============================================================================
// enclosure.scad - Bodi box kamera night-vision + Raspberry Pi 4 Model B
// =============================================================================
//  DESAIN ORISINAL (lihat hardware/README.md bagian "Asal-usul desain").
//  Tidak menurunkan geometri dari desain pihak ketiga mana pun.
//
//  SISTEM KOORDINAT
//    Titik asal  = pusat MUKA KAMERA (permukaan luar, Z = 0)
//    Sumbu optik = -Z  (kamera melihat ke bawah ke bed)
//    Kotak naik ke +Z, TUTUP di puncak (+Z)
//
//  ORIENTASI CETAK: muka kamera di meja (Z = 0 di bawah). Semua boss, post,
//  dan paddle tercetak vertikal -> tanpa support. Sun shield dibuat berbentuk
//  corong yang MELAR saat naik, jadi juga self-supporting.
//
//  TUMPUKAN Z (dihitung di params.scad, lihat z_* di sana)
//    0,0  -  2,4 ...... dinding muka depan
//    2,4  -  5,4 ...... 4 boss jepit kamera (self-tap M2)
//    5,4  -  6,4 ...... PCB modul kamera night-vision
//    6,4  -  8,8 ...... pelat jepit (camera_holder.scad)
//    8,8  - 18,8 ...... ruang tikungan kabel ribbon CSI
//   22,8  - 24,4 ...... PCB Raspberry Pi 4B (4 post standoff)
//   24,4  - 40,4 ...... komponen teratas (USB-A / RJ45)
//   40,4  - 58,4 ...... ruang bebas untuk heatsink
//   58,4  - 60,8 ...... tutup (enclosure_tutup.scad)
//
//  CATATAN THERMAL: 2x IR LED 3 W + Pi 4B ~ 12 W. Desain Pi Zero asli hanya
//  membuang ~1,3 W dengan 12 lubang kecil. Kebutuhan ventilasi di sini naik
//  sekitar 9x, itu sebabnya ukuran dan jumlah slot ventilasi sengaja besar.
// =============================================================================

include <params.scad>

tampilkan_standalone = is_undef(tampilkan_standalone_ov) ? true : tampilkan_standalone_ov;

// --- Turunan (dihitung di params.scad: int_w, int_h, rusuk_x, rusuk_y,
//     z_rusuk, rusuk_tinggi) ---
standoff_pi_h = z_pi_pcb - encl_dinding;
vent_z_atas = encl_d - 6;
vent_z_bawah = vent_z_atas - vent_jml_per_sisi * (vent_lebar + 2) + 2;

// Posisi slot ventilasi di dinding +/-Y. Dipilih di x = +/-20 supaya:
//   - jauh dari cable gland di -Y (x -8..8)
//   - jauh dari rusuk sudut di x 38..46
//   - dinding -Y juga bebas dari paddle (paddle ada di dinding +X)
vent_x = [-20, 20];


// Kulit luar: dari z = 0 (muka kamera) sampai puncak box.
module kulit_luar() {
    linear_extrude(height = encl_d)
        profil_chamfer(encl_w, encl_h, encl_chamfer);
}

// Rongga: terbuka di muka depan (z = 0) dan terbuka ke atas.
module rongga_dalam() {
    translate([0, 0, encl_dinding])
        linear_extrude(height = encl_d + 1)
            profil_chamfer(int_w, int_h, encl_chamfer);
}

// =============================================================================
//  1) MUKA KAMERA - dinding depan: 3 aperture + akses sensor
// =============================================================================
// Lubang yang harus tembus dinding muka depan. Dipakai dua kali: sekali untuk
// membuat muka_kamera() (tampak utuh), sekali sebagai pemotong di bodi.
module lubang_muka() {
    // -- aperture optik: 3 bukaan besar berjajar (lihat params.scad) --
    // Susunan dari kiri ke kanan: IR, Kamera, IR, lalu LDR di sisi kanan IR.
    if (led_ir_ada)
        translate([bukaan_ir1_dx, 0])
            circle(d = bukaan_ir_d);
    translate([bukaan_kamera_dx, 0])
        circle(d = bukaan_kamera_d);
    if (led_ir_ada)
        translate([bukaan_ir2_dx, 0])
            circle(d = bukaan_ir_d);

    // -- jendela fotoresistor (LDR): JANGAN ditutup. Kalau tertutup,
    //    LDR tidak melihat cahaya ambient dan IR menyala terus 24 jam.
    //    Ditaruh di sisi kanan lubang IR kanan, menempel tapi tidak menyatu
    //    (jarak bukaan_gap tetap ada di antaranya), sesuai desain pada gambar.
    translate([bukaan_ldr_dx, 0])
        circle(d = bukaan_ldr_d);

    // -- akses trimpot: untuk menyetel ambang nyala IR. Diletakkan di bawah
    //    baris bukaan supaya tidak mengambil lebar.
    translate([bukaan_kamera_dx, trimpot_dy])
        circle(d = trimpot_d + 2.0);

    // -- 2 jendela kecil LED indikator merah (kelihatan dari luar) --
    // supaya Anda bisa tahu IR sedang menyala tanpa membuka box
    if (led_indikator_ada)
        for (sx = [-1, 1])
            translate([bukaan_kamera_dx + sx * led_indikator_dx,
                       led_indikator_dy])
                circle(d = led_indikator_d);
}

// Cekungan dangkal yang membingkai kelima aperture. Efeknya: muka kamera
// terlihat "seperti plat kamera" yang ringkas di tengah bidang yang lebar,
// mendekati tampilan desain asli. Sengaja CEKUNG, bukan tonjol: kalau
// tonjol dan muka kamera di meja, dia jadi overhang yang butuh support.
// Dijadi modul 2D supaya bisa dipakai dua kali: di muka_kamera() (tampak
// utuh) dan sebagai pemotong di enclosure_bodi().
// Panel muka recessed: cekungan dangkal yang membingkai baris bukaan optik.
// Lebarnya mengikuti baris bukaan, bukan lagi angka tetap. TINGGI panel dibuat
// cukup untuk baris bukaan plus ruang untuk trimpot di bawahnya.
module panel_muka_2d() {
    offset(r = panel_muka_sudut)
        square([panel_muka_lebar, panel_muka_tinggi], center = true);
}

// Peringatan kalau baris bukaan keluar dari dinding muka (tidak akan terjadi
// selama encl_w mengikuti lebar_min_bukaan, tapi dijaga agar tidak bisa lolos
// kalau ada yang mengubah rumus lebar nanti).
if (bukaan_baris_lebar / 2 + bukaan_margin > int_w / 2)
    echo(str("[PERINGATAN] Baris bukaan terlalu lebar untuk dinding muka: butuh ",
             bukaan_baris_lebar + 2 * bukaan_margin, " mm, tersedia ",
             int_w, " mm. Perbesar bukaan_margin jadi lebih kecil atau turunkan ",
             "diameter bukaan."));

module muka_kamera(t = encl_dinding) {
    linear_extrude(height = t)
        difference() {
            profil_chamfer(encl_w, encl_h, encl_chamfer);
            panel_muka_2d();
            lubang_muka();
        }
}

// =============================================================================
//  2) SUN SHIELD - corong pelindung optik
//  Bentuk melebar ke atas (makin dekat kotak makin lebar) supaya aman tanpa
//  support saat dicetak dengan muka kamera di meja.
// =============================================================================
module sun_shield() {
    // Jari-jari luar corong DIBATASI oleh jarak ke bukaan tetangga, supaya
    // corong tidak mungkin menutupi bukaan IR atau LDR.
    // Semua bukaan sekarang berjajar di x, jadi batasnya dihitung dari tepi
    // bukaan kamera ke bukaan IR di sebelahnya.
    r_ir = led_ir_ada ? (bukaan_gap / 2 + bukaan_kamera_d / 2 - 1.0) : 1e9;
    r_luar = min(r_ir, bukaan_kamera_d / 2 + 12);

    r_min_boleh = bukaan_kamera_d / 2 + bukan_sunshield;  // dinding min
    if (r_luar < r_min_boleh)
        echo(str("[PERINGATAN] sun shield dilewati: ruang hanya ", r_luar,
                 " mm, minimal ", r_min_boleh, " mm. Cetak pakai_sunshield=false ",
                 "atau perbesar jarak antar bukaan."));

    z0 = -panjang_sunshield;
    h  = panjang_sunshield + 0.5;          // 0,5 mm tumpang tindih ke badan
    difference() {
        // Corong ikut bergeser ke posisi bukaan kamera.
        translate([bukaan_kamera_dx, 0, z0])
            cylinder(d1 = 2 * r_luar, d2 = 2 * r_luar + 6, h = h, $fn = 64);
        translate([bukaan_kamera_dx, 0, z0 - 1])
            cylinder(d = bukaan_kamera_d + 4, h = h + 2, $fn = 64);
    }
}

// =============================================================================
//  3) RUSUK SUDUT - 4 buah, self-tap M3. PENGGANTI boss tutup 48 mm.
// =============================================================================
//  Versi lama memakai 4 post yang berdiri di LANTAI rongga setinggi 48 mm.
//  Karena berdiri di samping papan, post itu memaksa clearance ke 8 mm
//  dan membuat box 105,8 x 76,8 mm - jauh lebih gemuk dari yang diperlukan.
//
//  Sekarang post diganti rusuk sudut setinggi ~15 mm yang MELAYANG di atas
//  komponen Pi (z_rusuk dihitung di params.scad dari z_ktop + 2,6 mm).
//  Karena tidak lagi ada yang berdiri di lantai rongga, clearance X bisa
//  turun ke 3,5 mm. Sisi Y tetap 15 mm karena di situ port Pi 4B tonjol.
//
//  Rusuk menyentuh DUA dinding (x = int_w/2 dan y = int_h/2) sepanjang
//  tingginya, jadi kaku tanpa perlu gusset tambahan.
//
//  AMAN TANPA SUPPORT: saat muka kamera di meja, rusuk tumbuh ke atas sebagai
//  dinding vertikal. Satu-satunya overhang cuma tapak horizontal 8 mm (sisi
//  rusuk) - jauh di bawah batas FDM tanpa support.
module rusuk_sudut() {
    // z_rusuk adalah dasar rusuk, z_dasar_rongga adalah atapnya. Karena cube()
    // memakai center = true, titik TENGAH rusuk harus di tengah-tengah keduanya,
    // BUKAN di z_rusuk. Versi lama memakai z_rusuk sebagai pusat, sehingga
    // rusuk melayang 7,7 mm di bawah atap rongga (terjadi 4 komponen terpisah)
    // sekaligus menabrak port USB-A / RJ45 yang tingginya sampai z_ktop.
    z_tengah = (z_rusuk + z_dasar_rongga) / 2;
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * rusuk_x, sy * rusuk_y, z_tengah])
            difference() {
                cube([encl_rusuk_lebar, encl_rusuk_lebar, rusuk_tinggi], center = true);
                // Lubang self-tap M3, dibuka ke ATAP (z_dasar_rongga) supaya
                // baut M3 dari tutup masuk ke bawah, persis seperti versi lama.
                translate([0, 0, rusuk_tinggi / 2 - encl_tap_tinggi / 2])
                    cylinder(d = encl_tap_m3, h = encl_tap_tinggi);
            }
}

// CATATAN: modul gusset_boss() SUDAH DIHAPUS bersama boss_tutup().
// Gusset itu menempelkan post ke dinding dari lantai rongga, dan justru itu
// yang membuat post harus berdiri di samping papan Pi (clearance 8 mm).
// Rusuk sudut yang sekarang tidak butuh gusset: dia langsung menyentuh dua
// dinding sepanjang seluruh tingginya.

// =============================================================================
//  4) POST STANDOFF RASPBERRY PI 4B - 4 buah, jarak 58 x 49 mm
//  Dipakai self-tap (tanpa heat-set insert): lubang dikecilkan 0,3 mm.
// =============================================================================
module standoff_pi() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * pi_lubang_x / 2, sy * pi_lubang_y / 2, encl_dinding])
            difference() {
                cylinder(d = pi_post_d, h = standoff_pi_h);
                cylinder(d = pi_lubang_d - 0.3, h = standoff_pi_h);
            }
}

// =============================================================================
//  5) BOSS JEPIIT KAMERA - 4 buah di muka dalam dinding depan, self-tap M2
//  Pelat jepit dari camera_holder.scad menekan PCB kamera ke post ini.
// =============================================================================
module boss_jepit_kamera() {
    // Boss mengikuti posisi bukaan kamera, supaya jepit camera_holder.scad
    // menekan modul tepat di belakang barrel optik.
    for (sx = [-1, 1], sy = [-1, 1])
        translate([bukaan_kamera_dx + sx * pola_lubang_x / 2,
                   sy * pola_lubang_y / 2, encl_dinding])
            difference() {
                cylinder(d = 5.0, h = panjang_pilar_jepit);
                cylinder(d = diameter_tap_m2, h = panjang_pilar_jepit);
            }
}

// =============================================================================
//  6) VENTILASI - slot di dinding +/-X
//  Intake di sisi -X bagian bawah, exhaust di sisi +X bagian atas, sehingga
//  udara dingin masuk rendah dan udara panas keluar tinggi (konveksi alami).
//  Terlindung hujan karena tutup selalu di ATAS, bukan di samping.
// =============================================================================
// Ventilasi dipindah ke dinding +/-Y. Alasannya: rusuk sudut memakai sudut
// dinding +/-X, dan slot di dinding itu akan tertutup sebagian oleh rusuk
// (slot y 12,5..30,5 beririsan dengan rusuk y 23,5..31,5 pada z 39..54,4).
// Dinding -Y juga dipakai cable gland di x = 0, jadi slot intake digeser ke
// x = +/-20 - cukup jauh dari gland (x -8..8) dan dari rusuk (x 38..46).
module potong_vent(sy, x, zk) {
    // Cutter DIPUSATKAN di tengah dinding, bukan di muka dalamnya, supaya
    // tidak menusuk ke dalam rongga dan mengikis tepi PCB Pi 4B.
    translate([x, sy * (int_h / 2 + encl_dinding / 2), zk])
        rotate([90, 0, 0])
            linear_extrude(height = encl_dinding * 2, center = true)
                offset(r = 1.5)
                    // CATATAN sumbu: setelah rotate([90,0,0]) sumbu X lokal tetap
                    // +X dan sumbu Y lokal menjadi +Z. Jadi slot horizontal
                    // (panjang di X) ditulis [panjang, lebar].
                    square([vent_panjang, vent_lebar], center = true);
}

module ventilasi() {
    n = vent_jml_per_sisi;
    n_bawah = floor(n / 2);
    for (x = vent_x)
        for (i = [0 : n - 1]) {
            // intake (-Y) = separuh BAWAH, exhaust (+Y) = separuh ATAS.
            // Pemisahan inilah yang menghasilkan arus konveksi alami: udara
            // dingin masuk rendah, udara panas keluar tinggi. Kalau semua slot
            // berada di ketinggian sama, hampir tidak ada aliran melalui box.
            if (i < n_bawah) {
                potong_vent(-1, x, vent_z_bawah + i * (vent_lebar + 2) + vent_lebar / 2);
            } else {
                potong_vent(1, x, vent_z_bawah + i * (vent_lebar + 2) + vent_lebar / 2);
            }
        }
}

// =============================================================================
//  7) CABLE GLAND - lubang M16 di dinding -Y untuk kabel USB-C power
//  Ini satu-satunya kabel yang keluar dari box. Sekaligus jalur udara kedua.
//  CATATAN: Raspberry Pi 4B harus dipasang dengan port USB-C menghadap ke
//  dinding -Y supaya kabelnya lurus dan tidak ditekuk tajam.
// =============================================================================
module cable_gland() {
    zg = z_pi_pcb + pi_pcb_t / 2;         // setinggi PCB Pi, di tengah port
    translate([0, -int_h / 2, zg])
        rotate([-90, 0, 0])
            cylinder(d = gland_d, h = encl_dinding * 4, center = true);
}

// =============================================================================
//  8) PADDLE - antarmuka ke lengan kamera, pada dinding +X
//  Muka luar paddle ada PERSIS di x = paddle_x_luar (= encl_w/2 + paddle_tebal).
//  arm.scad memakai angka itu sebagai bidang mating dengan pelat ujung lengan,
//  jadi kalau geometri paddle diubah, kedua file otomatis tetap cocok.
//  Disambung 2x baut M4 x 25 (gesekan mengunci sudut kemiringan).
// =============================================================================
module paddle() {
    x0 = encl_w / 2 - 1;                  // sedikit masuk ke dinding
    difference() {
        // Pelat padat dengan tepi membulat. Versi lama memakai hull() dengan
        // gusset segitiga di atas & bawah; sekarang cukup pelat polos supaya
        // sisinya bersih sehingga bentuk box tetap terbaca utuh.
        // Sumbu: rotate([0,90,0]) memetakan X lokal -> -Z dan Y lokal -> +Y.
        translate([x0, 0, encl_d / 2])
            rotate([0, 90, 0])
                linear_extrude(height = paddle_tebal + 1)
                    offset(r = 2)
                        square([paddle_tinggi, paddle_lebar], center = true);
        // 2 lubang self-tap M4, sumbu X
        for (sy = [-1, 1])
            translate([paddle_x_luar - 3, sy * paddle_jarak_baut, encl_d / 2])
                rotate([0, 90, 0])
                    cylinder(d = paddle_tap_d, h = 8, center = true);
    }
}

// =============================================================================
//  RAKITAN BODI
// =============================================================================
module enclosure_bodi() {
    union() {
        difference() {
            union() {
                // Kulit luar (dinding muka depan setebal encl_dinding sudah
                // termasuk di dalamnya, karena rongga_dalam() mulai di z itu)
                kulit_luar();
                standoff_pi();
                boss_jepit_kamera();
                paddle();
                if (pakai_sunshield) sun_shield();
            }

            // --- potongan ---

            // Rongga dalam: terbuka di muka depan (Z=0) dan terbuka ke atas
            rongga_dalam();

            // Tembus dinding muka depan: cekungan panel + kelima aperture.
            // Keduanya HARUS jadi pemotong TERPISAH, dan PANEL cutter hanya
            // boleh setebal panel_muka_kedalaman. Kalau diekstrusi setebal
            // dinding penuh, seluruh area panel jadi lubang tembus dan muka
            // kamera kehilangan bidik - bukan lagi cekungan dangkal.
            //
            // Pemotong lubang diekstrusi 0,01 mm lebih tinggi dari dinding
            // supaya tidak menyisakan skin setipis 0 di bidang potong.
            linear_extrude(height = panel_muka_kedalaman) panel_muka_2d();
            linear_extrude(height = encl_dinding + 0.01) lubang_muka();

            ventilasi();
            cable_gland();
        }

        // PENTING: rusuk sudut ditambahkan DI LUAR difference, sesudah semua
        // potongan selesai. Rusuk hidup DI DALAM rongga, jadi kalau masuk ke
        // union yang sama dengan kulit luar, rongga_dalam() akan menghapusnya
        // seluruhnya dan tutup kehilangan tempat bautnya. Sebaliknya kalau
        // diletakkan di daftar potongan, rusuk jadi TERBUANG. Dua-duanya
        // salah, dan bug versi boss_tutup() yang lama adalah kasus pertama -
        // tidak pernah ketahuan karena validasi mesh hanya menghitung
        // konektivitas, bukan mengecek FUNGSI bautnya.
        rusuk_sudut();
    }
}

// Modul untuk dipanggil arm.scad / assembly.scad
module enclosure_kepala() {
    color("DimGray") enclosure_bodi();
}

// Render mandiri (dilewati ketika di-include oleh arm/assembly)
if (tampilkan_standalone) {
    enclosure_kepala();
}