# Convert all files from CRLF to LF line endings
$rootPath = "c:\Dev\repos\rspec\AI-generated"

# Get all text files recursively
$files = Get-ChildItem -Path $rootPath -Recurse -File | Where-Object { 
    $_.Extension -in @('.vb', '.cs', '.txt', '.adoc', '.md', '.json', '.xml', '.sln', '.vbproj', '.csproj', '.ps1') 
}

Write-Host "Found $($files.Count) files to convert..."

foreach ($file in $files) {
    try {
        Write-Host "Converting: $($file.FullName)"
        
        # Read content as bytes to preserve encoding
        $content = Get-Content -Path $file.FullName -Raw
        
        if ($content) {
            # Replace CRLF with LF
            $lfContent = $content -replace "`r`n", "`n"
            
            # Write back with UTF8 encoding and LF line endings
            [System.IO.File]::WriteAllText($file.FullName, $lfContent, [System.Text.Encoding]::UTF8)
        }
    }
    catch {
        Write-Host "Error converting $($file.FullName): $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "Conversion completed!" -ForegroundColor Green
