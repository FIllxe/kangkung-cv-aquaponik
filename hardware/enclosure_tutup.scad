// =============================================================================
// enclosure_tutup.scad - Tutup box + jalur exhaust udara panas
// =============================================================================
//  Bentuk "baki": pelat atas lebar + skirtsisi yang masuk ke rongga box.
//
//  FUNGSI GANDA:
//    1. Menutup box (4x baut M3 x 10 ke boss sudut)
//    2. Jalur exhaust untuk udara panas, melengkapi intake di dinding -X
//
//  ORIENTASI CETAK: pelat dibaring di meja (Z 0), skirtsisi ke ATAS. Semua
//  dinding skirtsisi tegak lurus -> aman tanpa support, tanpa bridge.
//
//  SELOVERLAP: pelat lebih lebar dari rongga (menutup penuh diameter luar)
//  sekaligus menjadi drip shield: air hujan dialihkan ke luar sebelum
            // mencapai slot ventilasi di dinding.
//
//  CATATAN DESAIN: slot di tutup ini adalah exhaust SECONDARY. Intake
//  utamanya ada di dinding -X (enclosure.scad). Jangan diperbesar berlebihan,
//  karena draft yang terlalu besar akan melewati Pi 4B tanpa sempat tukar
//  panas ke dinding.
// =============================================================================

include <params.scad>

tampilkan_standalone = is_undef(tampilkan_standalone_ov) ? true : tampilkan_standalone_ov;

lebar_sisip  = int_w  - 2 * encl_sisip_clr;
tinggi_sisip = int_h  - 2 * encl_sisip_clr;
tebal_sisip  = 2.0;
z_sisip      = encl_lid_tebal;

// Grid exhaust: 2 baris x 4 kolom, tersebar di tengah pelat agar udara panas
// keluar jauh dari intake (dinding -X) dan dari badan heatsink.
vent_tutup_panjang = 18.0;
vent_tutup_lebar   = 4.0;
vent_tutup_jml_x   = 4;
vent_tutup_jml_y   = 2;

module ventilasi_tutup() {
    for (ix = [0 : vent_tutup_jml_x - 1])
        for (iy = [0 : vent_tutup_jml_y - 1]) {
            x = (ix - (vent_tutup_jml_x - 1) / 2) * (vent_tutup_panjang + 5);
            y = (iy - (vent_tutup_jml_y - 1) / 2) * (vent_tutup_lebar + 6);
            translate([x, y, 0])
                linear_extrude(height = encl_lid_tebal + 0.01)
                    offset(r = 1.5)
                        square([vent_tutup_panjang, vent_tutup_lebar], center = true);
        }
}

module pelat_tutup() {
    difference() {
        // Pelat lebar penuh, duduk di z = 0 .. encl_lid_tebal.
        // JANGAN tambah translate z di sini: linear_extrude sudah mulai dari 0,
        // sehingga translate z akan membuat pelat melayang di atas rim box.
        // offset r memberi overhang 2 mm ke segala sisi dari profil berchamfer.
        // Ini disengaja: overhang itu juga berfungsi sebagai drip shield, air
        // dialihkan keluar sebelum mencapai slot ventilasi di dinding.
        linear_extrude(height = encl_lid_tebal)
            offset(r = 2)
                profil_chamfer(encl_w, encl_h, encl_chamfer);
        ventilasi_tutup();
        // 4 lubang baut M3 ke rusuk sudut (posisi dihitung di params.scad)
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * rusuk_x, sy * rusuk_y, 0])
                cylinder(d = encl_baut_clr, h = encl_lid_tebal + 0.01);
    }
}

module skirtsisi() {
    // Cangkang tipis tanpa atas & bawah, masuk ke rongga box.
    // Mengikuti profil_chamfer yang sama persis dengan rongga, karena kalau
    // tetap persegi, sudut skir skirt akan menabrak dinding rongga yang
    // sekarang sudah dipangkas 45 derajat.
    translate([0, 0, z_sisip])
        linear_extrude(height = encl_kaidah_sisip)
            difference() {
                profil_chamfer(lebar_sisip, tinggi_sisip, encl_chamfer);
                profil_chamfer(lebar_sisip - 2 * tebal_sisip,
                               tinggi_sisip - 2 * tebal_sisip, encl_chamfer);
            }
}

module enclosure_tutup() {
    color("DimGray") pelat_tutup();
    color("DimGray") skirtsisi();
}

if (tampilkan_standalone) {
    enclosure_tutup();
}
