# Réparer likoo.html - supprime la fonction locale corrompue
$lines = Get-Content "likoo.html"

Write-Host "📝 Lecture du fichier: $($lines.Count) lignes"

# Remplacer les lignes 1549-1620 (index 1548-1619) par le code correct
$correctCode = @(
    "      viewUserProfileFromData(this);",
    "    });",
    "  });",  
    "}"
)

# Construire le nouveau fichier
$newLines = @()
$newLines += $lines[0..1547]  # Avant la corruption (jusqu'à ligne 1548 incluse)
$newLines += $correctCode      # Code correct
$newLines += $lines[1620..($lines.Count-1)]  # Après la corruption (depuis ligne 1621)

Write-Host "✅ Nouveau fichier: $($newLines.Count) lignes"

# Maintenant ajouter mkMemGroup avant renderMembers
# Trouver la ligne avec "function renderMembers()"
$renderMembersLine =  $newLines | Select-String -Pattern "^function renderMembers\(\)\{" | Select -First 1
if ($renderMembersLine) {
    $idx = $renderMembersLine.LineNumber - 1  # Index 0-based
    Write-Host "📍 renderMembers trouvé à la ligne $($idx+1)"
    
    # Insérer mkMemGroup avant
    $mkMemGroupCode = @(
        "function mkMemGroup(label, list) {",
        "  return ``<div class=`"mem-lbl`">`${label}</div>`${list.map((m, idx) => {",
        "    const userId = m.id || m.user_id || idx;",
        "    return ``<div class=`"mem-item`" data-user-id=`"`${userId}`" data-user-name=`"`${(m.name || '').replace(/`"/g, '&quot;')}`" style=`"cursor:pointer`">",
        "      <div class=`"mem-av`" style=`"background:`${m.color}18`">`${formatAvatar(m.av||m.avatar)}<div class=`"mem-dot `${m.status}`" style=`"border-color:var(--bg2)`"></div></div>",
        "      <div><div class=`"mem-name`">`${m.name}</div><div class=`"mem-role`">`${m.role||''}</div></div>",
        "    </div>``;",
        "  }).join('')}``;",
        "}",
        ""
    )
    
    $finalLines = @()
    $finalLines += $newLines[0..($idx-1)]
    $finalLines += $mkMemGroupCode
    $finalLines += $newLines[$idx..($newLines.Count-1)]
    
    Write-Host "✅ mkMemGroup ajouté"
} else {
    Write-Host "❌ renderMembers non trouvé!"
    $finalLines = $newLines
}

# Sauvegarder
$finalLines | Set-Content "likoo.html" -Encoding UTF8
Write-Host "🎉 Fichier réparé! Total: $($finalLines.Count) lignes"