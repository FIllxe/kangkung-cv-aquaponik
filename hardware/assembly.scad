// =============================================================================
// assembly.scad - Pratinjau rakitan lengkap
//  (mount_base + arm + enclosure + tutup + jepit kamera)
// =============================================================================
//  File ini hanya untuk REVIEW VISUAL, bukan untuk dicetak.
//  Pilih tipe mount di params.scad -> tipe_mount, lalu jalankan build.ps1
//  atau render manual:
//      openscad -o out.png --viewall --autocenter --projection=o \
//               --camera=0,0,0,65,0,45,0 --imgsize=1200,900 --render assembly.scad
//  build.ps1 sengaja tidak build file ini ke STL karena outputnya menyatukan
//  5 part sekaligus. Untuk slicing, cetak tiap part terpisah.
// =============================================================================

// Guard render mandiri. WAJIB disables dua-duanya: arm.scad dipanggil manual
// di bawah supaya posisinya benar (di atas mount), dan enclosure/jepit/tutup
// juga ditampilkan manual. Kalau tidak, include akan merender semuanya sendiri
// dan muncul lengan dobel di z = 0.
cetak_standalone_ov = false;
tampilkan_standalone_ov = false;
include <arm.scad>
include <mount_base.scad>
include <camera_holder.scad>
include <enclosure_tutup.scad>

// Rakitan: klem di bawah, bidang mating di atasnya, lengan ke samping,
// enclosure di ujung, dan tutup menutupi atas enclosure.
// CATATAN: arm.scad TIDAK lagi menyertakan kepala, supaya STL-nya tetap satu
// benda. Kepala dan jepit kamera dirender di sini untuk pratinjau saja.
// Posisi lengan memakai mount_z_mating (30 mm untuk klem hollow, 6 mm untuk
// tipe pipa/baut), bukan angka tetap, supaya lengan selalu menempel tepat di
// permukaan mount apa pun tipenya.
color("DimGray") mount_base_isi();
translate([0, 0, mount_z_mating]) color("DimGray") arm();
kepala_enclosure();

// Jepit kamera + tutup. Keduanya memakai modul kepala_transform() yang SAMA
// dengan enclosure, jadi posisinya pasti menempel - tidak ada lagi translate
//manual yang bisa meleset.
kepala_jepit_dan_tutup();
