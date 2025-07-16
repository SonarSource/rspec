$folders = @("S2631", "S5135", "S5144", "S5145", "S5146", "S5334", "S5883", "S6096", "S6173", "S6287", "S6399", "S6547", "S6641", "S6639", "S7044")

foreach ($folder in $folders) {
    $folderPath = "c:\Dev\repos\rspec\AI-generated\VBNetRspecExamples\$folder"
    
    # Check if DotnetCompliant.vb exists
    $compliantFile = "$folderPath\DotnetCompliant.vb"
    if (Test-Path $compliantFile) {
        $content = Get-Content $compliantFile -Raw
        
        # Replace class name and add namespace
        $newContent = $content -replace "Public Class S${folder}DotnetCompliant", "    Public Class Compliant"
        $newContent = $newContent -replace "Imports", "Imports"
        $newContent = "Imports Microsoft.AspNetCore.Mvc`r`n" + ($newContent -split "`r`n" | Where-Object { $_ -notmatch "^Imports Microsoft\.AspNetCore\.Mvc" } | ForEach-Object { if ($_ -match "^Imports") { $_ } else { if ($_ -match "^Public Class") { "`r`nNamespace $folder`r`n    $_" } else { if ($_ -eq "") { $_ } else { "    $_" } } } })
        $newContent += "`r`nEnd Namespace"
        
        # Write new file
        $newContent | Set-Content "$folderPath\Compliant.vb"
        
        # Delete old file
        Remove-Item $compliantFile
    }
}
