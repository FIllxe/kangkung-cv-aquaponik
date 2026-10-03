// =============================================================================
//  preview.scad - GABUNGAN SEMUA PART jadi satu scene untuk di-review
// =============================================================================
//  File ini TIDAK untuk dicetak. Isinya:
//    1. seluruh part cetak (mount_base + arm + enclosure + tutup + jepit)
//    2. PHANTOM Raspberry Pi 4B  (PCB + port + heatsink)
//    3. PHANTOM modul kamera night-vision (PCB 25x24 + 3 barrel)
//    4. PHANTOM besi hollow persegi 40x40 yang dijepit klem
//    5. kabel ribbon CSI
//
//  Phantom dipakai supaya Anda bisa menilai RUANG: apakah PCB muat, apakah
//  port USB/RJ45 menabrak dinding, apakah modul kamera bertabrakan dengan Pi.
//  Semua angka phantom diambil dari params.scad, jadi mengubah dimensi di sana
//  juga mengubah phantom.
//
//  MODE (diset lewat wrapper, lihat preview.ps1):
//    rakit   : semua part terpasang (default)
//    ledakan : tiap part digeser ke atas = exploded view
//    xray    : dinding enclosure semi transparan supaya isi terlihat
// =============================================================================

// Guard: disable semua render mandiri dari file yang di-include, kalau tidak
// lengan / enclosure / jepit / tutup akan muncul dobel.
cetak_standalone_ov      = false;
tampilkan_standalone_ov  = false;

include <arm.scad>
include <mount_base.scad>
include <camera_holder.scad>
include <enclosure_tutup.scad>

// --- Mode ---
//  PENTING: override TIDAK boleh ditulis sebagai "x = is_undef(x) ? ... : x".
//  OpenSCAD memperlakukan itu sebagai self-reference, is_undef() selalu true,
//  jadi nilai dari wrapper preview.ps1 SELALU diabaikan dan mode stuck di
//  default. Ikuti konvensi params.scad: nama _ov dibaca apa adanya, lalu
//  diturunkan ke variabel dengan nama lain.
mode      = is_undef(mode_ov)    ? "rakit" : mode_ov;      // rakit|ledakan|xray
explode_n = is_undef(explode_ov) ? 55.0   : explode_ov;   // jarak exploded, mm
// Toggle phantom. Default nyala supaya review-nya bermakna.
ph_raspi   = is_undef(ph_raspi_ov)  ? true : ph_raspi_ov;
ph_kamera  = is_undef(ph_kamera_ov) ? true : ph_kamera_ov;
ph_hollow  = is_undef(ph_hollow_ov) ? true : ph_hollow_ov;


// =============================================================================
//  PHANTOM - Raspberry Pi 4 Model B
// =============================================================================
//  Sistem koordinat SAMA dengan enclosure.scad, yaitu asal = pusat muka
//  kamera dan kotak naik ke +Z. Jadi angka dari params.scad bisa dipakai
//  langsung tanpa konversi.
//
//  CATATAN PENTING - INI YANG HARUS ANDA PERHATIKAN:
//  Port Pi 4B bukan cuma USB. RJ45 menonjol jauh dari tepi PCB. Kalau
//  clearance di params.scad lebih kecil dari tonjolan port, port akan
//  MENABRAK dinding enclosure. Nilai di bawah memakai tonjolan realistis:
//     RJ45 ~13,5 mm | USB-A ~7,5 mm | micro-HDMI ~6 mm | USB-C ~7,5 mm
//  Phantom sengaja dibuat apa adanya supaya masalahnya TERLIHAT di render,
//  bukan baru ketahuan setelah enclosure dicetak dan dirakit.
ph_rj45_d = 13.5;
ph_usba_d = 7.5;
ph_hdmi_d = 6.0;
ph_usbc_d = 7.5;
ph_port_h = pi_tinggi_port;          // 16 mm
ph_heatsink = 10.0;

// Jarak tepi PCB ke dinding dalam enclosure (arah Y, sisi cable gland).
// params.scad sudah punya peringatan yang sama, tapi diulang di sini supaya
// preview menampilkan clearance per sumbu, bukan cuma satu angka.
ph_clear_port = int_h / 2 - pi_pcb_h / 2;
ph_clear_samping = int_w / 2 - pi_pcb_w / 2;   // arah X, tidak ada port
echo(str("[PHANTOM] clearance Y (sisi port) = ", ph_clear_port,
         " mm | tonjolan RJ45 = ", ph_rj45_d, " mm"));
echo(str("[PHANTOM] clearance X (samping, tanpa port) = ", ph_clear_samping, " mm"));
if (ph_clear_port < ph_rj45_d)
    echo(str("[PERINGATAN] Port RJ45 Pi 4B MENABRAK dinding: clearance ",
             ph_clear_port, " mm < ", ph_rj45_d,
             " mm. Solusi: naikkan encl_clearance_y menjadi >= ",
             ceil(ph_rj45_d), " mm (lebar box tidak berubah), ",
             "atau buat jendela port di dinding -Y."));

module phantom_port(x, w, d, h = ph_port_h) {
    color("DimGray")
        translate([x, -pi_pcb_h / 2 - d / 2, z_pi_pcb + pi_pcb_t + h / 2])
            cube([w, d, h], center = true);
}

module phantom_raspi() {
    if (ph_raspi) {
        // PCB
        color("Green", 0.75)
            translate([0, 0, z_pi_pcb + pi_pcb_t / 2])
                cube([pi_pcb_w, pi_pcb_h, pi_pcb_t], center = true);
        // 4 lubang PCB (penanda posisi standoff)
        color("Black")
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * pi_lubang_x / 2, sy * pi_lubang_y / 2,
                           z_pi_pcb - 0.5])
                    cylinder(d = pi_lubang_d, h = pi_pcb_t + 1);
        // Port pada tepi -Y (sisi cable gland).
        // USB-C DITARUH DI x = 0 karena cable gland juga di x = 0 - kalau tidak,
        // lubang kabel tidak akan pernah sejajar dengan colokan USB-C.
        // CATATAN: urutan kiri-ke-kanan di sini adalah ASUMSI. Ukur dengan
        // jangka dari modul Anda sebelum STL dicetak.
        phantom_port(-33, 16, ph_rj45_d);   // RJ45 ethernet (tonjolan terbesar)
        phantom_port(-14,  7, ph_hdmi_d);   // micro-HDMI
        phantom_port(  0,  9, ph_usbc_d);   // USB-C power -> arah cable gland
        phantom_port( 13, 13, ph_usba_d);   // USB-A
        phantom_port( 26, 13, ph_usba_d);   // USB-A
        // Heatsink di atas SoC
        color("Silver", 0.85)
            translate([0, 4, z_pi_pcb + pi_pcb_t + ph_heatsink / 2])
                cube([40, 40, ph_heatsink], center = true);
    }
}



// =============================================================================
//  PHANTOM - modul kamera OV5647 night-vision
// =============================================================================
//  PCB 25 x 24 ditekan ke 4 boss jepit, jadi z PCB =
//  encl_dinding + panjang_pilar_jepit. Barrel menembus dinding muka depan ke
//  arah -Z, menonjol led_ir_protrusi mm ke luar muka.
z_pc_kamera = encl_dinding + panjang_pilar_jepit;

module phantom_kamera() {
    if (ph_kamera) {
        // Modul kamera ikut bergeser ke bukaan_kamera_dx, sama seperti
        // camera_holder.scad, supaya phantom dan STL part selalu senada.
        color("Green", 0.8)
            translate([bukaan_kamera_dx, 0, z_pc_kamera + kamera_pcb_t / 2])
                cube([kamera_pcb_w, kamera_pcb_h, kamera_pcb_t], center = true);
        // Barrel optik, mengisi bukaan kamera
        color("Black")
            translate([bukaan_kamera_dx, 0, (z_pc_kamera - optik_lensa_panjang) / 2])
                cylinder(d = optik_lensa_diameter,
                         h = z_pc_kamera + optik_lensa_panjang);
        // 2 array LED IR, mengisi bukaan IR kiri dan kanan
        color("Black")
            for (dx = [bukaan_ir1_dx, bukaan_ir2_dx])
                translate([dx, 0, (z_pc_kamera - optik_lensa_panjang) / 2])
                    cylinder(d = bukaan_ir_d - 1.5,
                             h = z_pc_kamera + optik_lensa_panjang);
    }
}

// =============================================================================
//  PHANTOM - kabel ribbon CSI, kamera -> konektor di Pi
// =============================================================================
module phantom_ribbon() {
    if (ph_kamera && ph_raspi) {
        z1 = z_pc_kamera + kamera_pcb_t;      // keluar dari PCB kamera
        z2 = z_pi_pcb + pi_pcb_t / 2;        // masuk ke Pi
        color("Ivory", 0.9)
            hull() {
                translate([0, 0, z1])
                    cube([kamera_pcb_w * 0.6, lebar_ribbon, 0.4], center = true);
                translate([0, -8, (z1 + z2) / 2])
                    cube([lebar_ribbon, 0.4, z2 - z1], center = true);
                translate([0, -pi_pcb_h / 2 + 8, z2])
                    cube([lebar_ribbon, 14, 0.4], center = true);
            }
    }
}

// =============================================================================
//  PHANTOM - besi hollow persegi yang dijepit klem
// =============================================================================
module phantom_hollow() {
    if (ph_hollow && tipe_mount == "hollow") {
        t = 3;                                  // tebal dinding besi hollow
        color("SlateGray", 0.9)
            translate([0, 0, -klem_panjang])
                difference() {
                    cube([hollow_a, hollow_b, klem_panjang * 2.2], center = true);
                    cube([hollow_a - 2 * t, hollow_b - 2 * t,
                          klem_panjang * 2.2 + 2], center = true);
                }
    }
}


// =============================================================================
//  RAKITAN
// =============================================================================
//  ex = jarak exploded. 0 = rapat.
ex = (mode == "ledakan") ? explode_n : 0;

// Alpha dinding: 0,22 saat mode xray, 1 saat rapat.
al = (mode == "xray") ? 0.22 : 1;

phantom_hollow();

// Klem + lengan. Pada mode ledakan klem turun dan lengan naik supaya bidang
// mating terlihat lepas.
translate([0, 0, -ex])                 color("DimGray", al) mount_base_isi();
translate([0, 0, mount_z_mating + ex]) color("DimGray", al) arm();

// Kepala: box + phantom + jepit + tutup, semuanya di dalam kerangka transform
// yang SAMA (kepala_transform + kepala_dasar), jadi tidak mungkin salah tempat.
translate([0, 0, 2 * ex])
kepala_transform() kepala_dasar() {
    // Bodi enclosure (transparan saat mode xray)
    color("DimGray", al) enclosure_bodi();

    // Isi box
    phantom_kamera();
    phantom_ribbon();
    phantom_raspi();

    // Jepit kamera: naik sebesar ex pada mode ledakan
    translate([0, 0, ex])   color("SteelBlue") camera_holder_isi();

    // Tutup: duduk di puncak box, dibalik 180 derajat supaya skirt masuk ke
    // bawah. Pada mode ledakan naik 2x ex supaya terpisah dari jepit.
    translate([0, 0, encl_d + 2 * ex])
        rotate([180, 0, 0]) color("SlateGray") enclosure_tutup();
}

echo(str("[PREVIEW] mode=", mode, " | mount=", tipe_mount,
         " | lengan=", panjang_lengan, " mm | sudut=", sudut_kemiringan,
         " | eksplode=", ex));

