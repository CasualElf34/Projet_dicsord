# Réparer likoo.html - version simple
$lines = Get-Content "likoo.html"
$mkMemCode = Get-Content "mkMemGroup.txt"

Write-Host "Original: $($lines.Count) lignes"

# Partie 1: avant corruption (lignes 0-1547)
$part1 = $lines[0..1547]

# Partie 2: code de remplacement pour la corruption
$part2 = @(
    "      viewUserProfileFromData(this);",
    "    });",
    "  });",
    "}"
)

# Partie 3: après corruption (lignes 1620+)
$part3 = $lines[1620..($lines.Count-1)]

# Fusionner
$fixed = $part1 + $part2 + $part3

Write-Host "Apres fix corruption: $($fixed.Count) lignes"

# Trouver renderMembers
$renderIdx = -1
for ($i = 0; $i -lt $fixed.Count; $i++) {
    if ($fixed[$i] -match "^function renderMembers") {
        $renderIdx = $i
        break
    }
}

if ($renderIdx -gt 0) {
    Write-Host "renderMembers ligne: $($renderIdx+1)"
    
    # Inserer mkMemGroup avant renderMembers
    $final = $fixed[0..($renderIdx-1)] + $mkMemCode + "" + $fixed[$renderIdx..($fixed.Count-1)]
    
    Write-Host "Final: $($final.Count) lignes"
    $final | Set-Content "likoo.html" -Encoding UTF8
    Write-Host 'Fichier repare!'
} else {
    Write-Host 'ERREUR: renderMembers non trouve'
}
