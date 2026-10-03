// =============================================================================
// camera_holder.scad - Jepit modul kamera night-vision (OV5647 + 2x IR LED)
// =============================================================================
//  PERUBAHAN PERAN: dulu part ini adalah dudukan kamera yang TERANG di ujung
//  lengan. Sekarang kamera sudah DI DALAM enclosure.scad, jadi part ini
//  hanya menjepit PCB kamera dari belakang ke boss di dinding muka depan.
//
//  TUMPUKAN Z (lokal; z = 0 = muka DALAM dinding muka depan enclosure)
//    0    ....  panjang_pilar_jepit ....  boss self-tap M2 di enclosure
//    3,0  ....  4,0  .....................  PCB modul kamera night-vision (1 mm)
//    4,0  ....  6,4  .....................  PELAT JEPIIT (part ini, 2,4 mm)
//
//  Pemasangan: 4x sekrup M2 x 12 dari pelat jepit, menembus PCB kamera lalu
//  masuk ke boss self-tap di dinding muka depan enclosure.
//
//  Modul bisa dilepas (buka 4 sekrup M2) tanpa membongkar lengan.
//
//  URUTAN PEMASANGAN YANG BENAR:
//    1. masukkan modul kamera, Optic menghadap -Z (ke arah bed)
//    2. sambungkan ribbon CSI ke konektor di belakang modul
//    3. kencangkan 4 sekrup M2 secara SILANG, bukan berurutan, supaya PCB
//       rata dan tidak mendeformasi sudut PCB
//    4. pasang kunci barrel (kalau dipakai) lalu fokuskan
// =============================================================================

include <params.scad>

tampilkan_standalone = is_undef(tampilkan_standalone_ov) ? true : tampilkan_standalone_ov;

// --- Geometri turunan ---
z_pcb_depan    = panjang_pilar_jepit;                 // muka depan PCB
z_pcb_belakang = z_pcb_depan + kamera_pcb_t;           // muka belakang PCB
lebar_pelat    = kamera_pcb_w + 10;
tinggi_pelat   = kamera_pcb_h + 10;
pos_x          = pola_lubang_x / 2 + 5;                // posisi post penahan
pos_y          = pola_lubang_y / 2 + 5;

// =============================================================================
//  PELAT JEPIIT - menekan PCB kamera dari belakang
//  Berada di z = z_pcb_belakang .. + dinding_jepit, yaitu DI BELAKANG PCB.
//
//  POSISI: seluruh part ini digeser ke bukaan_kamera_dx, supaya modul kamera
//  berada tepat di belakang barrel optik yang menembus dinding muka depan.
//  Boss di enclosure.scad memakai angka yang sama, jadi keduanya selalu senada.
//  Kalau bukaan digeser, jepit ini ikut bergeser otomatis.
// =============================================================================
module pelat_jepit() {
    translate([bukaan_kamera_dx, 0, z_pcb_belakang])
        linear_extrude(height = dinding_jepit)
            difference() {
                offset(r = 3)
                    square([lebar_pelat, tinggi_pelat], center = true);

                // 4 lubang sekrup M2 yang menembus PCB ke boss enclosure
                for (sx = [-1, 1], sy = [-1, 1])
                    translate([sx * pola_lubang_x / 2, sy * pola_lubang_y / 2])
                        circle(d = diameter_sekrup_m2 + 0.5);

                // Jendela tengah: memberi jalan ke konektor ribbon CSI di
                // belakang PCB, mengurangi bahan cetak, serta membantu aliran udara
                offset(r = 2)
                    square([kamera_pcb_w - 6, kamera_pcb_h - 6], center = true);
            }
}

// 4 post penahan: duduk di dinding muka depan enclosure, DI LUAR PCB.
// Tingginya dibuat sampai masuk separuh ke pelat jepit, supaya keduanya
// menjadi SATU komponen padat (bukan dua benda yang hanya bersentuhan).
module post_penahan() {
    h = z_pcb_belakang + dinding_jepit / 2;
    for (sx = [-1, 1], sy = [-1, 1])
        translate([bukaan_kamera_dx + sx * pos_x, sy * pos_y, 0])
            cylinder(d = 4.0, h = h);
}

// =============================================================================
//  KUNCI BARREL - SUDAH DIHAPUS, dan ini alasannya.
// =============================================================================
//  Versi pertama memakai cincin setengah atas dengan 2 post ke pelat jepit.
//  Post-nya diletakkan pada x = +/- rt (telinga cincin), dan hal itu
//  jatuh tepat di DALAM jendela tengah pelat, sehingga
//  post tidak pernah menyentuh pelat. Hasil ekspor STL terverifikasi menjadi
//  3 komponen terpisah, bukan satu benda utuh.
//
//  Menggantinya dengan geometri yang lebih rapi justru berisiko: tidak ada
//  yang bisa menguji gesekan barrel tanpa modul fisik di tangan, dan salah
//  desain akan membuat cetakan pertama gagal.
//
//  CARA MENAHAN FOKUS YANG DIPAKAI SEKARANG
//    1. Fokuskan SETELAH modul terpasang menjepit (barrel berupa gesekan
//       pas di lubang optik dinding muka depan enclosure).
//    2. Tandai posisi barrel dengan spidol pada ring knurled.
//    3. Cek ulang fokus setiap kali box dibuka atau setelah dipindah.
//    4. Opsional: sekencang O-ring karet / lakban pada barrel, atau lem
//       polypropylene cyanoacrylate dosis kecil. Ini jauh lebih andal
//       daripada dongolan plastik.
// =============================================================================

// =============================================================================
//  RAKITAN
// =============================================================================
module camera_holder_isi() {
    color("SteelBlue") post_penahan();
    color("SteelBlue") pelat_jepit();
}

if (tampilkan_standalone) {
    camera_holder_isi();
}
