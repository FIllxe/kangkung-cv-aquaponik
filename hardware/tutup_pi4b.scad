// =============================================================================
//  tutup_pi4b.scad - Tutup (lid) untuk pi4b_camera_enclosure_bottom.stl
// =============================================================================
//  PASANGAN: files\pi4b_camera_enclosure_bottom.stl
//  File itu dibuat oleh files\build_pi4b_enclosure.py. Lid ini terpisah karena
//  pasangan STL-nya sudah final dan tidak memakai params.scad parametric yang
//  lain. JANGAN disamakan dengan enclosure_tupid.scad - itu untuk box parametric
//  yang lebarnya 143,8 mm, jadi produk yang berbeda.
//
//  SUMBER UKURAN
//  Semua angka di bawah diverifikasi langsung ke STL pasangan dan ke script
//  pembuatnya:
//
//    Ukuran STL pasangan (diukur dari vertex) : 93,0 x 99,5 x 40,0 mm
//    INNER_X = PI_W + gap USB + gap SD       = 89,0 mm  (cavitas)
//    INNER_Y = CAM_ZONE + PI_D + BACK_GAP   = 95,5 mm  (cavitas)
//    OUT     = INNER + 2 x WALL              = 93,0 x 99,5 mm
//
//  Jadi "cavity 89 x 95,5" di spec bukan tebakan: itu persis isi script.
//
//  SISTEM KOORDINAT (sama dengan script dan STL pasangan)
//    Kotak berpusat di X/Y, Z = 0 adalah dasar luar box. Rim box ada di z = 40.
//
//  ORIENTASI CETAK
//    Pelat dibaring di meja (z = 0 .. 2), lip ke ATAS (z = 2 .. 6). Semua
//    dinding tegak lurus, jadi aman tanpa support dan tanpa bridge.
//    Untuk menyandingkan dengan STL pasangan di scene yang sama, pakai
//    lid_dalam_koordinat_box() di bawah.
// =============================================================================

$fn = 64;

// =============================================================================
//  PARAMETER (mm) - Spec lid
// =============================================================================
BOX_H            = 40.0;   // tinggi box pasangan, hasil ukur STL
WALL             = 2.0;    // ketebalan dinding box (dari script)

PLAT_LEBAR       = 93.0;   // ukuran pelat luar
PLAT_TINGGI      = 99.5;
PLAT_R           = 3.0;    // radius sudut luar, sebanding dengan dinding box
PLAT_TEBAL       = 2.0;

// Lip (bajul penahan) yang masuk ke cavitas, dikurangi clearance per sisi.
CAV_L            = 89.0;   // cavitas box arah X
CAV_T            = 95.5;   // cavitas box arah Y
LIP_CLR          = 0.2;    // clearance per sisi
LIP_L            = CAV_L - 2 * LIP_CLR;   // 88,6
LIP_T            = CAV_T - 2 * LIP_CLR;   // 95,1
LIP_R            = 0.8;    // radius sudut lip
LIP_DEDAL        = 1.6;    // ketebalan dinding lip
LIP_TINGGI       = 4.0;    // z = 36 .. 40

TOTAL_TINGGI     = PLAT_TEBAL + LIP_TINGGI;   // 6,0 mm

// Takik pembuka (pry notch) untuk ujung obeng, di tepi -X.
NOTIK_PANJANG    = 8.0;    // searah tepi (Y)
NOTIK_DALAM      = 1.5;    // masuk ke arah dalam (X)
NOTIK_Y          = 0.0;    // posisi di tepi -X

// Grid exhaust: busur konsentris seperti grid lantai, di atas SoC.
// Pusat memakai logika gx/gy yang SAMA dengan script (baris 91):
//     gx = bx2X(32.0) = 43,0 - 32,0 = 11,0
//     gy = by2Y(27.0) = 45,75 - 27,0 = 18,75
GRILE_X          = 11.0;
GRILE_Y          = 18.75;
GRILE_DIAMETER   = 26.0;   // diameter total grid (spec)
GRILE_CINCIN     = [[0, 5], [7, 9], [11, 13]];  // (r_dalam, r_luar)
GRILE_LENGAN     = 2.0;    // lebar palang silang yang memotong jadi kuadran

// =============================================================================
//  TURUNAN
// =============================================================================
GRILE_R_LUAR     = GRILE_DIAMETER / 2;        // 13,0
LIP_Z_BOTAS      = BOX_H - LIP_TINGGI;         // 36,0
LIP_Z_ATAS       = BOX_H;                     // 40,0

// Slot ventilasi dinding box paling atas ada di z = 32,5 .. 35,5 (script baris
// 145-147). Lip mulai z = 36, jadi jaraknya 0,5 mm.
VENT_ATAS_BOX    = 35.5;

// =============================================================================
//  MODUL BANTU
// =============================================================================

// Persegi panjang dengan sudut membulat, terpusat di titik asal.
//
// CATATAN: offset(r = +x) MEMBESARKAN benda, bukan hanya membulatkan sudut.
// Kalau ditulis offset(r=3) square([93, 99.5]), hasilnya jadi 99 x 105.5 mm -
// 3 mm lebih besar di tiap sisi. Jadi persegi di dalamnya harus dikecilkan
// 2 x r dulu, sama seperti fungsi rrect() di build_pi4b_enclosure.py.
module profil_rr(w, d, r) {
    offset(r = r)
        square([w - 2 * r, d - 2 * r], center = true);
}

// Grid busur konsentris, dipotong jadi 4 kuadran, seperti grid lantai.
module grid_busur() {
    for (ring = GRILE_CINCIN) {
        r0 = ring[0];
        r1 = ring[1];
        difference() {
            circle(r = r1);
            if (r0 > 0)
                circle(r = r0);
            // Dua palang silang: memotong tiap cincin jadi 4 kuadran.
            square([2 * r1 + 2, GRILE_LENGAN], center = true);
            square([GRILE_LENGAN, 2 * r1 + 2], center = true);
        }
    }
}

// __APPEND_MODULE__

// =============================================================================
//  PELAT
// =============================================================================
module pelat() {
    difference() {
        // Pelat luar, duduk di z = 0 .. PLAT_TEBAL.
        // JANGAN tambah translate z di sini: linear_extrude sudah mulai dari 0.
        linear_extrude(height = PLAT_TEBAL)
            profil_rr(PLAT_LEBAR, PLAT_TINGGI, PLAT_R);

        // Grid exhaust di atas SoC.
        translate([GRILE_X, GRILE_Y, -1])
            linear_extrude(height = PLAT_TEBAL + 2)
                grid_busur();

        // Takik pembuka di tepi -X, untuk ujung obeng. Dipotong penuh
        // setebal pelat supaya obeng bisa mencengkeram tepi dalam.
        translate([-(PLAT_LEBAR / 2) - 1, NOTIK_Y - NOTIK_PANJANG / 2, -1])
            cube([NOTIK_DALAM + 1, NOTIK_PANJANG, PLAT_TEBAL + 2]);
    }
}

// =============================================================================
//  LIP - bajul penahan yang masuk ke cavitas
// =============================================================================
module lip() {
    // z = PLAT_TEBAL .. TOTAL_TINGGI (2 .. 6 saat dicetak).
    translate([0, 0, PLAT_TEBAL])
        linear_extrude(height = LIP_TINGGI)
            difference() {
                profil_rr(LIP_L, LIP_T, LIP_R);
                // offset negatif membuat ketebalan dinding seragam.
                offset(r = -LIP_DEDAL)
                    profil_rr(LIP_L, LIP_T, LIP_R);
            }
}

// =============================================================================
//  RAKITAN
// =============================================================================
module tutup() {
    color("DimGray") pelat();
    color("DimGray") lip();
}

// Versi yang sudah dipindahkan ke koordinat box, supaya bisa langsung
// disandingkan dengan STL pasangan.
//
// PERHATIKAN Z - nilai ini mudah salah, jadi dihitung eksplisit.
//   tutup() (orientasi cetak) occupy z 0..6: pelat z 0..2, lip z 2..6.
//   Spec minta lip di z 36..40 (4 mm masuk ke cavitas) dan pelat di z 40..42
//   (tepat di atas rim box yang ada di z = 40).
//   Karena lip di z 2..6, agar berakhir di 36..40, translate = 36 - 2 = 34.
//
// CATATAN: translate 34 BUKAN 40. Kalau dipakai 40, seluruh lid akan duduk di
// z 40..46, yaitu DI ATAS box, dan lip tidak masuk ke cavitas sama sekali.
module lid_dalam_koordinat_box() {
    translate([0, 0, LIP_Z_BOTAS - PLAT_TEBAL])
        tutup();
}

// =============================================================================
//  VALIDASI
//  Dipakai supaya kesalahan spesifikasi ketahuan saat build, bukan setelah
//  part dicetak.
// =============================================================================
if (abs(PLAT_LEBAR - (CAV_L + 2 * WALL)) > 0.01)
    echo(str("[PERINGATAN] Pelat lebar ", PLAT_LEBAR,
             " tidak sebanding dengan dinding box (", CAV_L, " + 2 x ", WALL,
             " = ", CAV_L + 2 * WALL, "). Pelat akan bolong atau melimpahi."));
if (abs(PLAT_TINGGI - (CAV_T + 2 * WALL)) > 0.01)
    echo(str("[PERINGATAN] Pelat tinggi ", PLAT_TINGGI,
             " tidak sebanding dengan dinding box (", CAV_T, " + 2 x ", WALL,
             " = ", CAV_T + 2 * WALL, ")."));
if (LIP_L > CAV_L || LIP_T > CAV_T)
    echo(str("[PERINGATAN] Lip lebih besar dari cavitas - tidak akan masuk!"));
if (LIP_Z_BOTAS < VENT_ATAS_BOX)
    echo(str("[PERINGATAN] Lip turun sampai z ", LIP_Z_BOTAS,
             " dan akan menutupi slot ventilasi box yang batas atasnya z ",
             VENT_ATAS_BOX, ". Kurangi LIP_TINGGI."));
if (LIP_DEDAL * 2 >= min(LIP_L, LIP_T))
    echo(str("[PERINGATAN] Dinding lip terlalu tebal untuk ukuran lip ini."));
if (GRILE_X - GRILE_R_LUAR < -PLAT_LEBAR / 2 + 1
    || GRILE_X + GRILE_R_LUAR > PLAT_LEBAR / 2 - 1)
    echo(str("[PERINGATAN] Grid keluar dari tepi pelat pada sumbu X."));
if (GRILE_Y - GRILE_R_LUAR < -PLAT_TINGGI / 2 + 1
    || GRILE_Y + GRILE_R_LUAR > PLAT_TINGGI / 2 - 1)
    echo(str("[PERINGATAN] Grid keluar dari tepi pelat pada sumbu Y."));

// Ringkasan dimensi turunan - titik awal saat debug.
echo(str("[LID] pelat ", PLAT_LEBAR, " x ", PLAT_TINGGI, " x ", PLAT_TEBAL,
         " mm | R sudut ", PLAT_R));
echo(str("[LID] lip ", LIP_L, " x ", LIP_T, " x ", LIP_TINGGI, " mm | R ",
         LIP_R, " | dinding ", LIP_DEDAL, " | z ", LIP_Z_BOTAS, " .. ", LIP_Z_ATAS,
         " (jarak dari slot ventilasi ",
         round(LIP_Z_BOTAS - VENT_ATAS_BOX), " mm)"));
echo(str("[LID] total tinggi ", TOTAL_TINGGI, " mm | grid d", GRILE_DIAMETER,
         " @ x=", GRILE_X, " y=", GRILE_Y));

tampilkan_standalone = is_undef(tampilkan_standalone_ov) ? true : tampilkan_standalone_ov;
if (tampilkan_standalone) {
    tutup();
}