# Mở báo cáo bằng Word (ẩn), cập nhật mục lục / danh mục bảng, hình và mọi trường, lưu lại, rồi xuất PDF.
# Chạy: powershell -ExecutionPolicy Bypass -File reports\update_fields.ps1 [-Pdf <đường dẫn pdf>]
param([string]$Doc = "reports\Bao_cao_do_an_Dinh_Quoc_Bao.docx", [string]$Pdf = "")
$path = (Resolve-Path $Doc).Path
$lock = Join-Path (Split-Path $path) ("~$" + (Split-Path $path -Leaf).Substring(2))
if (Test-Path $lock) { Write-Output "File đang mở trong Word: $path"; exit 1 }
$w = New-Object -ComObject Word.Application
try {
    $w.Visible = $false
    $d = $w.Documents.Open($path, $false, $false)
    for ($k = 0; $k -lt 2; $k++) {          # hai lượt: lượt sau có số trang đúng sau khi mục lục đã chiếm chỗ
        foreach ($t in $d.TablesOfContents) { $t.Update() }
        $d.Fields.Update() | Out-Null
        $d.Repaginate()
    }
    $d.Save()
    if ($Pdf) { $d.ExportAsFixedFormat($Pdf, 17) }
    Write-Output ("trang: " + $d.ComputeStatistics(2) + " | mục lục: " + $d.TablesOfContents.Count)
}
finally {
    foreach ($x in @($w.Documents)) { $x.Close([ref]0) }
    $w.Quit([ref]0)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($w)
}
