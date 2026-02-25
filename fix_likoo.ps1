# Script pour réparer likoo.html
$content = Get-Content "likoo.html" -Raw

# Pattern corrompu à remplacer (la partie avec viewUserProfileFromData définie localement)
$badPattern = @'
  // Attacher les événements click aux éléments membres
  el.querySelectorAll('.mem-item').forEach(item => {
    item.addEventListener('click', function(e) {
      e.stopPropagation();
      function viewUserProfileFromData\(el\) \{[\s\S]*?\}
      \$\{isMe\?
'@

# Code correct à insérer
$goodCode = @'
  //Attacher les événements click aux éléments membres
  el.querySelectorAll('.mem-item').forEach(item => {
    item.addEventListener('click', function(e) {
      e.stopPropagation();
      viewUserProfileFromData(this);
    });
  });
}
function toggleMembers(){
  S.membersVisible=!S.membersVisible;
  const z=q('#zoneRight');
  z.style.display=S.membersVisible?'flex':'none';
}

// ═══════════════════════════════════════════════
// RENDER CHAT
// ═══════════════════════════════════════════════
function renderChat(){
  const key=activeKey();
  const msgs=key?(S.messages[key]||[]):[];
  const el=q('#messages'); if(!el)return;
  if(!key||msgs.length===0){
    const ch=S.activeSrv?.channels.find(c=>c.id===S.activeCh);
    el.innerHTML=`<div class="empty-chat">
      <div class="big">${S.view==='dm'?'💬':'#'}</div>
      <h3>${S.view==='dm'?'Début de la conversation':'#'+(ch?.name||'salon')}</h3>
      <p style="font-size:13px">${key?'Soyez le premier à écrire ici !':'Sélectionnez un salon.'}</p>
    </div>`;
    return;
  }
  const compact=S.compact;
  el.innerHTML=msgs.map((m,i)=>{
    if(m.system)return`<div class="sys-line">${m.content}</div>`;
    const prev=msgs[i-1];
    const same=prev&&!prev.system&&prev.author?.name===m.author?.name;
    const auth=m.author||S.me;
    const isMe=auth.name===S.me.name;
    const reacts=(m.reactions||[]).map(r=>`<span class="react-chip ${r.mine?'mine':''}" onclick="toggleReact('${key}',${m.id},'${r.e}')">${r.e} ${r.c}</span>`).join('');
    const body=m.file
      ?(m.file.type.startsWith('image/')
        ?`<img src="${m.file.data}" class="img-msg">`
        :`<div class="file-chip">📄 <span>${m.file.name}</span><span style="color:var(--text4);font-size:11px">${m.file.size}</span></div>`)
      :`<div class="msg-content">${String(m.content).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>`;
    const acts=`<div class="msg-acts">
      <button class="msg-act-btn" onclick="quickReact('${key}',${m.id})">😊</button>
      <button class="msg-act-btn" onclick="quickReact('${key}',${m.id})">👍</button>
      <button class="msg-act-btn" onclick="quickReact('${key}',${m.id})">😂</button>
      ${isMe?`<button class="msg-act-btn" onclick="editMsg('${key}',${m.id})">✏️</button>`:''}
      ${isMe?`<button class="msg-act-btn" style="color:var(--red)" onclick="delMsg('${key}',${m.id})">🗑</button>`:''}
'@

Write-Host "Recherche de la section corrompue..."

# Trouver l'index de début de la section corrompue
$startIdx = $content.IndexOf("  // Attacher les événements click")
if ($startIdx -eq -1) {
    Write-Host "❌ Section non trouvée!"
    exit 1
}

# Trouver où commence vraiment renderChat (ou la prochaine fonction majeure)
# Chercher "${isMe?" qui est une partie du code mis au mauvais endroit
$corruptIdx = $content.IndexOf('${isMe?`<button class="msg-act-btn"', $startIdx)
if ($corruptIdx -eq -1) {
    Write-Host "❌ Corruption non trouvée!"
    exit 1
}

Write-Host "✅ Section corrompue trouvée entre $startIdx et $corruptIdx"
Write-Host "Remplacement en cours..."

# Extraire les parties
$before = $content.Substring(0, $startIdx)
$after = $content.Substring($corruptIdx)

# Reconstituer
$fixed = $before + $goodCode + $after

# Sauvegarder
$fixed | Set-Content "likoo_fixed.html" -Encoding UTF8
Write-Host "✅ Fichier réparé: likoo_fixed.html"
Write-Host "Vérification: $((Get-Content 'likoo_fixed.html').Length) lignes"
