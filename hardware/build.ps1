# =============================================================================
# build.ps1 - Compile .scad -> STL + render 8 sudut untuk review visual
# =============================================================================
#  Cara pakai:
#    .\build.ps1                          # semua part dengan setting default
#    .\build.ps1 -Part fit_test           # plat uji pola lubang (CETAK INI DULU)
#    .\build.ps1 -Part enclosure          # satu part saja
#    .\build.ps1 -TipeMount hollow -HollowA 30 -HollowB 30
#    .\build.ps1 -PanjangLengan 200
#    .\build.ps1 -OnlyRender              # hanya render PNG (tanpa STL)
#
#  Output:
#    stl\*.stl        - untuk slicer
#    renders\*.png    - 8 sudut + iso untuk inspeksi visual
#
#  URUTAN PENGERJAAN YANG DISARANKAN
#    1. .\build.ps1 -Part fit_test   -> cetak & cek pola lubang
#    2. perbarui params.scad dengan hasil pengukuran modul
#    3. .\build.ps1 -Part enclosure enclosure_tutup camera_holder
#    4. .\build.ps1                  # render semua untuk review
# =============================================================================

[CmdletBinding()]
param(
    [string[]]$Part = @(),
    [ValidateSet("pipa", "hollow", "baut", "dinding")]
    [string]$TipeMount = "hollow",
    [double]$HollowA = 0,
    [double]$HollowB = 0,
    [double]$PanjangLengan = 0,
    [double]$SudutKemiringan = -1,
    [switch]$OnlyRender,
    [switch]$SkipRender
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$stlDir = Join-Path $root "stl"
$renderDir = Join-Path $root "renders"

# OpenSCAD: pakai openscad.com (console) supaya stdout bisa ditangkap.
$candidates = @(
    (Join-Path ${env:ProgramFiles} "OpenSCAD\openscad.com"),
    (Join-Path ${env:ProgramFiles(x86)} "OpenSCAD\openscad.com"),
    (Join-Path $env:LOCALAPPDATA "Programs\OpenSCAD\openscad.com")
)
$scad = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $scad) { throw "OpenSCAD tidak ditemukan. Pasang dari: winget install OpenSCAD.OpenSCAD" }

foreach ($d in @($stlDir, $renderDir)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# --- Daftar part ---
$semuaPart = [ordered]@{
    "fit_test"        = "fit_test.scad"
    "enclosure"       = "enclosure.scad"
    "enclosure_tutup" = "enclosure_tutup.scad"
    "camera_holder"   = "camera_holder.scad"
    "mount_base"      = "mount_base.scad"
    "arm"             = "arm.scad"
}
if ($Part.Count -gt 0) {
    $parts = [ordered]@{}
    foreach ($p in $Part) {
        if (-not $semuaPart.Contains($p)) {
            throw "Part '$p' tidak dikenal. Pilihan: $($semuaPart.Keys -join ', ')"
        }
        $parts[$p] = $semuaPart[$p]
    }
} else {
    $parts = $semuaPart
}

# --- Override -D ---
# CATATAN PENTING (OpenSCAD 2021.01): variabel dari -D TIDAK terlihat oleh
# is_undef() di dalam file yang di-`include`. Solusinya: build.ps1 membuat
# file wrapper sementara yang menyetel override di lingkup terluar, baru
# meng-include part-nya. Ini sudah divalidasi.
function Get-OverrideBody {
    $lines = @()
    $lines += "tipe_mount_ov = `"$TipeMount`";"
    if ($HollowA -gt 0)        { $lines += "hollow_a_ov = $HollowA;" }
    if ($HollowB -gt 0)        { $lines += "hollow_b_ov = $HollowB;" }
    if ($PanjangLengan -gt 0)  { $lines += "panjang_lengan_ov = $PanjangLengan;" }
    if ($SudutKemiringan -ge 0) { $lines += "sudut_kemiringan_ov = $SudutKemiringan;" }
    return ($lines -join "`n")
}

function New-Wrapper {
    param([string]$PartFile)
    $wrap = Join-Path $root "_build_$([IO.Path]::GetFileNameWithoutExtension($PartFile)).scad"
    $body = Get-OverrideBody
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($wrap, "$body`ninclude <$([IO.Path]::GetFileNameWithoutExtension($PartFile)).scad>`n", $utf8)
    return $wrap
}
function Invoke-Scad {
    param([string]$Src, [string[]]$ExtraArgs, [string]$Label)
    $args = @()
    $args += $ExtraArgs
    $args += $Src
    $out = & $scad @args 2>&1
    $err = $out | Select-String -Pattern "^(ERROR|WARNING)"
    if ($err) {
        Write-Host "  [$Label] pesan:" -ForegroundColor Yellow
        $err | Select-Object -First 3 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkYellow }
    }
}

# --- 1) Ekspor STL ---
if (-not $OnlyRender) {
    Write-Host "==> Ekspor STL" -ForegroundColor Cyan
    foreach ($name in $parts.Keys) {
        $src = New-Wrapper -PartFile $parts[$name]
        $dst = Join-Path $stlDir "$name.stl"
        Remove-Item $dst -ErrorAction SilentlyContinue
        Invoke-Scad -Src $src -ExtraArgs @("-o", $dst) -Label $name
        $ok = Test-Path $dst
        $sz = if ($ok) { "{0:N0} B" -f (Get-Item $dst).Length } else { "-" }
        "{0,-16} {1,-6} {2}" -f $name, $(if ($ok) { "OK" } else { "GAGAL" }), $sz |
            ForEach-Object { Write-Host $_ -ForegroundColor $(if ($ok) { "Green" } else { "Red" }) }
    }
}

# --- 2) Render 8 sudut untuk inspeksi ---
# OpenSCAD 2021.01: jarak eksplisit menggagalkan framing saat --viewall
# dipakai, jadi pakai --viewall --autocenter + rotasi gimbal (7 angka)
# dengan jarak 0. --render wajib agar CGAL selesai sebelum PNG ditulis.
$views = @(
    @{ n = "top";      rot = @(0, 0, 0) },
    @{ n = "bottom";   rot = @(180, 0, 0) },
    @{ n = "front";    rot = @(90, 0, 0) },
    @{ n = "back";     rot = @(90, 0, 180) },
    @{ n = "left";     rot = @(90, 0, 90) },
    @{ n = "right";    rot = @(90, 0, -90) },
    @{ n = "iso";      rot = @(65, 0, 45) },
    @{ n = "iso_back"; rot = @(65, 0, 225) }
)

Write-Host "==> Render 8 sudut" -ForegroundColor Cyan
if ($SkipRender) {
    Write-Host "  (dilewati karena -SkipRender)" -ForegroundColor DarkYellow
    foreach ($name in $parts.Keys) { Write-Host ("  {0,-16} 0 gambar" -f $name) -ForegroundColor DarkCyan }
    Get-ChildItem $root -Filter "_build_*.scad" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "`nSelesai. STL di: $stlDir" -ForegroundColor Green
    return
}
foreach ($name in $parts.Keys) {
    $src = New-Wrapper -PartFile $parts[$name]
    foreach ($v in $views) {
        $out = Join-Path $renderDir "$($name)_$($v.n).png"
        $camArgs = "0,0,0," + ($v.rot -join ",") + ",0"
        $a = @("--viewall", "--autocenter", "--projection=o",
               "--camera=$camArgs", "--imgsize=1000,750", "--render",
               "--colorscheme=Tomorrow", "-o", $out)
        $null = & $scad @a $src 2>&1
    }
    $n = (Get-ChildItem $renderDir -Filter "$name`_*.png" -ErrorAction SilentlyContinue).Count
    Write-Host ("  {0,-16} {1} gambar" -f $name, $n) -ForegroundColor DarkCyan
}

# Bersihkan file wrapper sementara
Get-ChildItem $root -Filter "_build_*.scad" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "`nSelesai. STL di: $stlDir" -ForegroundColor Green
Write-Host "Preview di : $renderDir" -ForegroundColor Green
