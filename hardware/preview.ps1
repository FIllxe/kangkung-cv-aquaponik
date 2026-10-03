# =============================================================================
# preview.ps1 - Gabungkan semua part jadi 1 scene, render untuk review visual
# =============================================================================
#  Cara pakai:
#    .\preview.ps1                  # semua mode, semua sudut
#    .\preview.ps1 -Mode rakit      # hanya rakitan rapat
#    .\preview.ps1 -Mode ledakan    # exploded view
#    .\preview.ps1 -Mode xray       # dinding transparan
#    .\preview.ps1 -SudutKemiringan 30 -PanjangLengan 180
#    .\preview.ps1 -SkipStl         # hanya PNG, tanpa STL gabungan
#
#  Output:
#    renders\preview_<mode>_<sudut>.png   - 6 sudut per mode
#    stl\preview_rakit.stl                - semua part digabung 1 file
#
#  CATATAN: STL gabungan hanya untuk DILIHAT di viewer (Windows 3D Viewer,
#  Cura, OctoPrint). JANGAN di-slicer langsung - isinya beberapa part yang
#  harus dicetak terpisah dengan orientasi cetak masing-masing.
# =============================================================================

[CmdletBinding()]
param(
    [ValidateSet("rakit", "ledakan", "xray")]
    [string[]]$Mode = @("rakit", "ledakan", "xray"),
    [double]$PanjangLengan = 0,
    [double]$SudutKemiringan = -1,
    [ValidateSet("pipa", "hollow", "baut", "dinding")]
    [string]$TipeMount = "hollow",
    [double]$HollowA = 0,
    [double]$HollowB = 0,
    [switch]$SkipStl
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$stlDir = Join-Path $root "stl"
$renderDir = Join-Path $root "renders"

$candidates = @(
    (Join-Path ${env:ProgramFiles} "OpenSCAD\openscad.com"),
    (Join-Path ${env:ProgramFiles(x86)} "OpenSCAD\openscad.com"),
    (Join-Path $env:LOCALAPPDATA "Programs\OpenSCAD\openscad.com")
)
$scad = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $scad) { throw "OpenSCAD tidak ditemukan." }

foreach ($d in @($stlDir, $renderDir)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# --- Sudut view (gimbal 7 angka, jarak 0) ---
#  Catatan arah: kepala pada pose dasar sudah "kamera lurus ke bawah", jadi
#  kamera ada di sisi BAWAH box. rx = 0 = lihat dari atas (tutup),
#  rx = 180 = lihat dari bawah (muka kamera + barrel optik).
$views = @(
    @{ n = "iso";      rot = @(65, 0, 45) },
    @{ n = "iso_back"; rot = @(65, 0, 225) },
    @{ n = "iso_kiri"; rot = @(70, 0, 315) },
    @{ n = "muka";     rot = @(180, 0, 0) },   # muka kamera + barrel, dari bawah
    @{ n = "muka_miring"; rot = @(150, 0, 20) },
    @{ n = "samping";  rot = @(90, 0, 0) }
)

# --- Wrapper: OpenSCAD 2021.01 tidak meneruskan -D ke include ---
$wrap = Join-Path $root "_preview.scad"
$body = @()
$body += "mode_ov = `"$($Mode[0])`";"
if ($PanjangLengan -gt 0)  { $body += "panjang_lengan_ov = $PanjangLengan;" }
if ($SudutKemiringan -ge 0) { $body += "sudut_kemiringan_ov = $SudutKemiringan;" }
$body += "tipe_mount_ov = `"$TipeMount`";"
if ($HollowA -gt 0) { $body += "hollow_a_ov = $HollowA;" }
if ($HollowB -gt 0) { $body += "hollow_b_ov = $HollowB;" }
$body += "include <preview.scad>"
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($wrap, ($body -join "`n"), $utf8)

try {
    # --- STL gabungan (mode rakit) untuk dilihat di viewer ---
    if (-not $SkipStl) {
        Write-Host "==> STL gabungan (untuk viewer, jangan di-slicer)" -ForegroundColor Cyan
        [IO.File]::WriteAllText($wrap, (($body -replace 'mode_ov = "ledakan";', 'mode_ov = "rakit";') -replace 'mode_ov = "xray";', 'mode_ov = "rakit";' -join "`n"), $utf8)
        $dst = Join-Path $stlDir "preview_rakit.stl"
        Remove-Item $dst -ErrorAction SilentlyContinue
        $null = & $scad -o $dst $wrap 2>&1
        if (Test-Path $dst) {
            Write-Host ("  preview_rakit.stl  OK  {0:N0} B" -f (Get-Item $dst).Length) -ForegroundColor Green
        } else {
            Write-Host "  preview_rakit.stl  GAGAL" -ForegroundColor Red
        }
    }

    # --- Render PNG per mode ---
    foreach ($m in $Mode) {
        Write-Host "==> Render mode: $m" -ForegroundColor Cyan
        [IO.File]::WriteAllText($wrap, (($body -replace 'mode_ov = "[a-z]+";', "mode_ov = `"$m`";") -join "`n"), $utf8)
        # PENTING: mode xray memakai --preview (OpenCSG), BUKAN --render
        # (CGAL). Renderer CGALOutcome mengabaikan nilai alpha dari color(),
        # jadi dinding semi transparan akan keluar totally solid. OpenCSG
        # menghormati alpha, dan karena mode xray tidak butuh geometri final,
        # kualitasnya sudah lebih dari cukup untuk review.
        $usePreview = ($m -eq "xray")
        $eng = if ($usePreview) { "--preview=png" } else { "--render" }
        foreach ($v in $views) {
            $out = Join-Path $renderDir "preview_${m}_$($v.n).png"
            $camArgs = "0,0,0," + ($v.rot -join ",") + ",0"
            $a = @("--viewall", "--autocenter", "--projection=o",
                   "--camera=$camArgs", "--imgsize=1100,850", $eng,
                   "--colorscheme=Tomorrow", "-o", $out)
            $null = & $scad @a $wrap 2>&1
        }
        $n = (Get-ChildItem $renderDir -Filter "preview_${m}_*.png" -ErrorAction SilentlyContinue).Count
        Write-Host ("  {0,-10} {1} gambar" -f $m, $n) -ForegroundColor DarkCyan
    }
} finally {
    Remove-Item $wrap -Force -ErrorAction SilentlyContinue
}

Write-Host "`nSelesai." -ForegroundColor Green
Write-Host "PNG  : $renderDir\preview_*.png" -ForegroundColor Green
Write-Host "STL  : $stlDir\preview_rakit.stl (view only)" -ForegroundColor Green
