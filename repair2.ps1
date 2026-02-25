# Réparer likoo.html
$lines = Get-Content "likoo.html"
Write-Host "Lecture: $($lines.Count) lignes"

# Code correct pour remplacer la section corrompue
$fix1 = "      viewUserProfileFromData(this);"
$fix2 = "    });"
$fix3 = "  });"
$fix4 = "}"

# Construire nouveau fichier
$new = New-Object System.Collections.ArrayList
for ($i = 0; $i -le 1547; $i++) { [void]$new.Add($lines[$i]) }
[void]$new.Add($fix1)
[void]$new.Add($fix2)
[void]$new.Add($fix3)
[void]$new.Add($fix4)
for ($i = 1620; $i -lt $lines.Count; $i++) { [void]$new.Add($lines[$i]) }

Write-Host "Apres suppression corruption: $($new.Count) lignes"

# Trouver renderMembers
$idx = -1
for ($i = 0; $i -lt $new.Count; $i++) {
    if ($new[$i] -match "^function renderMembers") {
        $idx = $i
        break
    }
}

if ($idx -gt 0) {
    Write-Host "renderMembers trouve ligne $($idx+1)"
    
    # Code mkMemGroup
    $mg = @()
    $mg += "function mkMemGroup(label, list) {"
    $mg += '  return `<div class="mem-lbl">${label}</div>${list.map((m, idx) => {'
    $mg += "    const userId = m.id || m.user_id || idx;"
    $mg += '    return `<div class="mem-item" data-user-id="${userId}" data-user-name="${(m.name || '"'').replace(/"'+'"/g, '"'"'&quot;'"'"')}" style="cursor:pointer">'
    $mg += '      <div class="mem-av" style="background:${m.color}18">${formatAvatar(m.av||m.avatar)}<div class="mem-dot ${m.status}" style="border-color:var(--bg2)"></div></div>'
    $mg += '      <div><div class="mem-name">${m.name}</div><div class="mem-role">${m.role||'"''"'}</div></div>'
    $mg += "    </div>`;"
    $mg += " }).join('"'"''"'"')}`;}"
    $mg += ""
    
    # Ins érer
    $final = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt $idx; $i++) { [void]$final.Add($new[$i]) }
    foreach ($line in $mg) { [void]$final.Add($line) }
    for ($i = $idx; $i -lt $new.Count; $i++) { [void]$final.Add($new[$i]) }
    
    Write-Host "mkMemGroup ajoute. Total: $($final.Count) lignes"
    $final | Set-Content "likoo.html" -Encoding UTF8
    Write-Host "Fichier repare!"
} else {
    Write-Host "ERREUR: renderMembers non trouve"
    $new | Set-Content "likoo.html" -Encoding UTF8
}
