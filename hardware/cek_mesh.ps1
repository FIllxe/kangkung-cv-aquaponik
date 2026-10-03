# =============================================================================
# cek_mesh.ps1 - Validasi geometri STL (watertight / manifold / 1 komponen)
# =============================================================================
#  .\cek_mesh.ps1              -> cek semua STL di .\stl
#  .\cek_mesh.ps1 -File a.stl  -> cek satu file
#
#  Yang diperiksa:
#    1. COMPONENT  : jumlah benda terpisah. Harus 1. Kalau > 1 ada bagian
#                    yang cuma "nyentuh" dan akan jatuh sendiri saat dicetak.
#    2. MANIFOLD   : setiap edge harus dipakai tepat 2 kali dengan arah berlawanan
#                    (orientasi permukaan harus konsisten). Edge yang dipakai
#                    1x = lubang bocor, >2x = non-manifold.
#    3. VOLUME     : volume bertanda harus > 0. Negatif berarti orientasi
#                    terbalik dan slicer bisa salah baca.
#    4. BOUNDING   : ukuranoverall, untuk dibandingkan dengan ekspektasi.
# =============================================================================

param([string[]]$File)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $File) { $File = @(Get-ChildItem (Join-Path $root "stl") -Filter *.stl | ForEach-Object { $_.FullName }) }

function Get-Key([double]$x, [double]$y, [double]$z) {
    # kunci vertex dengan presisi 1e-4 mm supaya segitiga yang berbagi titik
    # tepat dianggap satu simpul
    "{0:F4},{1:F4},{2:F4}" -f $x, $y, $z
}

# Baca STL (binary maupun ASCII) -> List[double[]] berisi 9 float per segitiga
# (v0 = idx 0..2, v1 = 3..5, v2 = 6..8)
function Get-Triangles([string]$path) {
    $tris = New-Object 'System.Collections.Generic.List[double[]]'

    $head = New-Object byte[] 84
    $fs = [IO.File]::OpenRead($path)
    $null = $fs.Read($head, 0, 84)
    $fs.Close()
    $nBin = [BitConverter]::ToInt32($head, 80)
    # STL ASCII selalu diawali kata "solid"; file binary bisa kebetulan
    # diawali "solid" juga, jadi dicek lewat ukuran file terhadap nBin.
    $teks = [Text.Encoding]::ASCII.GetString($head, 0, 20)
    $isAscii = ($teks -match '^\s*solid') -and
                (([IO.FileInfo]$path).Length -lt (84 + $nBin * 50))

    if ($isAscii) {
        $txt = [IO.File]::ReadAllText($path)
        $rx = 'vertex\s+(-?[\d.]+(?:[eE][-+]?\d+)?)\s+(-?[\d.]+(?:[eE][-+]?\d+)?)\s+(-?[\d.]+(?:[eE][-+]?\d+)?)'
        $ms = [regex]::Matches($txt, $rx)
        $inv = [Globalization.CultureInfo]::InvariantCulture
        for ($i = 0; $i + 2 -lt $ms.Count; $i += 3) {
            $t = New-Object double[] 9
            for ($v = 0; $v -lt 3; $v++) {
                $t[$v * 3 + 0] = [double]::Parse($ms[$i + $v].Groups[1].Value, $inv)
                $t[$v * 3 + 1] = [double]::Parse($ms[$i + $v].Groups[2].Value, $inv)
                $t[$v * 3 + 2] = [double]::Parse($ms[$i + $v].Groups[3].Value, $inv)
            }
            $tris.Add($t)
        }
    } else {
        $bytes = [IO.File]::ReadAllBytes($path)
        for ($i = 0; $i -lt $nBin; $i++) {
            $o = 84 + $i * 50
            $t = New-Object double[] 9
            for ($k = 0; $k -lt 9; $k++) {
                $t[$k] = [BitConverter]::ToSingle($bytes, $o + 12 + ($k + 3) * 4)
            }
            $tris.Add($t)
        }
    }
    return ,$tris
}

$adaGagal = $false
foreach ($f in $File) {
    $tris = Get-Triangles $f

    # --- map vertex + daftar edge (dengan orientasi) ---
    $vmap = @{}
    $edges = @{}
    $vx = New-Object 'System.Collections.Generic.List[double]'
    $vy = New-Object 'System.Collections.Generic.List[double]'
    $vz = New-Object 'System.Collections.Generic.List[double]'

    foreach ($t in $tris) {
        $ids = New-Object int[] 3
        for ($e = 0; $e -lt 3; $e++) {
            $k = 3 * $e
            $key = Get-Key $t[$k] $t[$k + 1] $t[$k + 2]
            if (-not $vmap.ContainsKey($key)) {
                $vmap[$key] = $vmap.Count
                $vx.Add($t[$k]); $vy.Add($t[$k + 1]); $vz.Add($t[$k + 2])
            }
            $ids[$e] = $vmap[$key]
        }
        for ($e = 0; $e -lt 3; $e++) {
            $a = $ids[$e]; $b = $ids[($e + 1) % 3]
            $key = if ($a -lt $b) { "$a-$b" } else { "$b-$a" }
            $dir = if ($a -lt $b) { 1 } else { -1 }
            if (-not $edges.ContainsKey($key)) { $edges[$key] = 0 }
            $edges[$key] += $dir
        }
    }

    # --- 1 & 2) cek edge bocor / non-manifold ---
    $bocor = 0; $nonManifold = 0
    foreach ($k in $edges.Keys) {
        $s = [Math]::Abs($edges[$k])
        if ($s -eq 1) { $bocor++ } elseif ($s -gt 2) { $nonManifold++ }
    }

    # --- 3) volume bertanda: V = a . (b x c) / 6 ---
    $vol = 0.0
    foreach ($t in $tris) {
        $nx = $t[4] * $t[8] - $t[5] * $t[7]
        $ny = $t[5] * $t[6] - $t[3] * $t[8]
        $nz = $t[3] * $t[7] - $t[4] * $t[6]
        $vol += ($t[0] * $nx + $t[1] * $ny + $t[2] * $nz) / 6.0
    }

    # --- 4) komponen terhubung: union-find inline ---
    $nV = $vmap.Count
    $parent = New-Object int[] $nV
    for ($i = 0; $i -lt $nV; $i++) { $parent[$i] = $i }
    foreach ($t in $tris) {
        $ids = @()
        for ($e = 0; $e -lt 3; $e++) {
            $k = 3 * $e
            $ids += $vmap[(Get-Key $t[$k] $t[$k + 1] $t[$k + 2])]
        }
        for ($e = 0; $e -lt 3; $e++) {
            $ra = $ids[$e]
            while ($parent[$ra] -ne $ra) { $ra = $parent[$ra] }
            for ($g = 0; $g -lt 3; $g++) {
                if ($g -eq $e) { continue }
                $rb = $ids[$g]
                while ($parent[$rb] -ne $rb) { $rb = $parent[$rb] }
                if ($ra -ne $rb) { $parent[$rb] = $ra }
            }
        }
    }
    $roots = @{}
    for ($i = 0; $i -lt $nV; $i++) {
        $r = $i
        while ($parent[$r] -ne $r) { $r = $parent[$r] }
        $roots[$r] = $true
    }
    $nComp = $roots.Count

    # --- 4b) daftar komponen: peta simpul -> label, lalu bbox tiap label ---
    $label = New-Object int[] $nV
    $next = 0
    for ($i = 0; $i -lt $nV; $i++) {
        $r = $i
        while ($parent[$r] -ne $r) { $r = $parent[$r] }
        $parent[$i] = $r
    }
    $lab = @{}
    for ($i = 0; $i -lt $nV; $i++) {
        $r = $parent[$i]
        if (-not $lab.ContainsKey($r)) { $lab[$r] = $next; $next++ }
        $label[$i] = $lab[$r]
    }

    # --- 5) bounding box keseluruhan + daftar per komponen ---
    $dx = ($vx | Measure-Object -Max).Maximum - ($vx | Measure-Object -Min).Minimum
    $dy = ($vy | Measure-Object -Max).Maximum - ($vy | Measure-Object -Min).Minimum
    $dz = ($vz | Measure-Object -Max).Maximum - ($vz | Measure-Object -Min).Minimum

    $ok = ($bocor -eq 0 -and $nonManifold -eq 0 -and $nComp -eq 1 -and $vol -gt 0)
    if (-not $ok) { $adaGagal = $true }
    $nama = Split-Path -Leaf $f
    $baris = "{0,-18} tri={1,-7} bocor={2,-3} nonman={3,-3} komponen={4,-3} vol={5,10:F1} mm3  bb={6:F1} x {7:F1} x {8:F1}" -f $nama, $tris.Count, $bocor, $nonManifold, $nComp, $vol, $dx, $dy, $dz
    Write-Host $baris -ForegroundColor $(if ($ok) { "Green" } else { "Red" })

    # Kalau pecah jadi beberapa komponen, tampilkan posisi masing-masing.
    # Ini yang langsung-memberi tahu bagian mana yang lepas.
    if ($nComp -gt 1) {
        $mnx = @{}; $mxx = @{}; $mny = @{}; $mxy = @{}; $mnz = @{}; $mxz = @{}
        for ($i = 0; $i -lt $nV; $i++) {
            $L = $label[$i]
            if (-not $mnx.ContainsKey($L)) {
                $mnx[$L] = $vx[$i]; $mxx[$L] = $vx[$i]
                $mny[$L] = $vy[$i]; $mxy[$L] = $vy[$i]
                $mnz[$L] = $vz[$i]; $mxz[$L] = $vz[$i]
            } else {
                if ($vx[$i] -lt $mnx[$L]) { $mnx[$L] = $vx[$i] }
                if ($vx[$i] -gt $mxx[$L]) { $mxx[$L] = $vx[$i] }
                if ($vy[$i] -lt $mny[$L]) { $mny[$L] = $vy[$i] }
                if ($vy[$i] -gt $mxy[$L]) { $mxy[$L] = $vy[$i] }
                if ($vz[$i] -lt $mnz[$L]) { $mnz[$L] = $vz[$i] }
                if ($vz[$i] -gt $mxz[$L]) { $mxz[$L] = $vz[$i] }
            }
        }
        foreach ($L in ($mnx.Keys | Sort-Object)) {
            Write-Host ("    komponen {0}: x {1,7:F1}..{2,7:F1}  y {3,7:F1}..{4,7:F1}  z {5,7:F1}..{6,7:F1}" -f $L, $mnx[$L], $mxx[$L], $mny[$L], $mxy[$L], $mnz[$L], $mxz[$L]) -ForegroundColor Yellow
        }
    }
}
if ($adaGagal) { Write-Host "`nADA PART YANG GAGAL VALIDASI" -ForegroundColor Red }
else { Write-Host "`nSemua STL OK" -ForegroundColor Green }
