/* ═══════════════════════════════════════════════════
   LIKOO — app.js
   Draggable modules, chat, servers, mobile/desktop
   ═══════════════════════════════════════════════════ */

// ─────────────────────────────────────────────
// GLOBAL STATE
// ─────────────────────────────────────────────
const APP = {
  me: null,
  servers: [],
  activeSrv: null,
  activeCh: null,
  dmChannel: null,
  view: 'home',       // 'home' | 'server' | 'dm' | 'servers-list'
  messages: {},
  panelTab: 'channels',
  inVoice: null,
  isMobile: false,
  mobTab: 'servers',  // 'servers' | 'channels' | 'chat' | 'members'
};

const COLORS = ['#8b5cf6','#ec4899','#14b8a6','#f59e0b','#3b82f6','#22c55e','#ef4444','#a855f7'];
const AVATARS = ['🦊','👾','🐉','🌟','🦁','🐺','🦋','🐙','🎭','🦄','🐻','🐸','🦅','🐬','🦋'];
const EMOJIS  = ['😀','😂','❤️','👍','🎉','🔥','✨','😎','🤔','😅','👀','💯','🚀','🎮','💜','😍','🤣','👋','💪','🦄','⚡','🌟','😭','🥺','🤯','😏','🤙','💀','🍕','🎵'];

// helper to render avatar string (emoji or image URL)
function formatAvatar(av){
  if(!av) return '';
  if(typeof av==='string' && (
       av.startsWith('http') || av.startsWith('/') || av.startsWith('data:')
     )){
    return `<img src="${av}" class="avatar-img" alt="avatar">`;
  }
  return `<span style="font-size:15px">${av}</span>`;
}

// upload a new avatar file to the backend
function uploadAvatar(input){
  const file = input.files[0];
  if(!file) return;
  // temporary blob url for instant feedback
  const blobUrl = URL.createObjectURL(file);
  if(APP.me){
    APP.me.av = blobUrl;
    save();
    updateNavAv();
    renderUserDock();
    renderServers();
    renderChannels();
    renderMembers();
  }
  const reader = new FileReader();
  reader.onload = e => {
    const dataUrl = e.target.result;
    document.getElementById('avatarPreview').innerHTML = `<img src="${dataUrl}" alt="avatar">`;
    // immediately update app state so it survives navigation
    if(APP.me){
      APP.me.av = dataUrl;
      save();
      updateNavAv();
      renderUserDock();
      renderServers();
      renderChannels();
      renderMembers();
      const mem = q('#members-list .mem-item:first-child img');
      if(mem) mem.src = APP.me.av;
    }
    URL.revokeObjectURL(blobUrl);
  };
  reader.readAsDataURL(file);

  // send to server if we have a token
  if(APP.me && APP.me.token){
    const form = new FormData();
    form.append('avatar', file);
    fetch('/api/auth/avatar', {
      method:'POST',
      body: form,
      headers:{ 'Authorization': 'Bearer ' + APP.me.token }
    }).then(r=>r.json()).then(data=>{
      if(data.avatar){
        APP.me.av = data.avatar;
        save();
        updateNavAv();
        renderUserDock();
        renderServers();
        renderChannels();
        renderMembers();
        const mem = q('#members-list .mem-item:first-child img');
        if(mem) mem.src = APP.me.av;
      } else if(data.error){
        alert('Erreur : '+data.error);
      }
    }).catch(err=>console.error('upload error',err));
  }
}

const DEMO_MEMBERS = [
  { name:'Zara',  tag:'4521', av:'🦊', color:'#ec4899', status:'online',  role:'Admin' },
  { name:'Nino',  tag:'7788', av:'👾', color:'#3b82f6', status:'online',  role:'Membre' },
  { name:'Léa',   tag:'3310', av:'🦋', color:'#22c55e', status:'away',    role:'Membre' },
  { name:'Max',   tag:'9001', av:'🐉', color:'#f59e0b', status:'dnd',     role:'Modérateur' },
  { name:'Sofia', tag:'1111', av:'🌟', color:'#a855f7', status:'offline', role:'Membre' },
  { name:'Kev',   tag:'2222', av:'🦁', color:'#14b8a6', status:'offline', role:'Membre' },
];
const DEMO_DMS = [
  { id:'dm_zara', ...DEMO_MEMBERS[0] },
  { id:'dm_nino', ...DEMO_MEMBERS[1] },
  { id:'dm_lea',  ...DEMO_MEMBERS[2] },
];

// ─────────────────────────────────────────────
// BOOT
// ─────────────────────────────────────────────
function boot() {
  detectLayout();
  const saved = localStorage.getItem('likoo_state');
  if (saved) {
    try { APP.me = JSON.parse(saved); } catch(e) {}
  }
  if (APP.me) {
    startApp();
  } else {
    openModal('modal-setup');
  }
  buildEmojiPicker();
  window.addEventListener('resize', detectLayout);
}

function detectLayout() {
  APP.isMobile = window.innerWidth < 700;
  if (APP.isMobile) {
    document.body.classList.remove('desktop-mode');
  } else {
    document.body.classList.add('desktop-mode');
  }
}

function startApp() {
  buildDemoData();
  renderUserDock();
  renderServers();
  if (!APP.isMobile) {
    renderChannels();
    renderMembers();
    renderChat();
  }
  renderMobileServers();
}

// ─────────────────────────────────────────────
// DEMO DATA
// ─────────────────────────────────────────────
function buildDemoData() {
  const t = now();
  const srv = {
    id: 'demo', name: 'Mon Serveur', emoji: '🏠',
    channels: [
      { id:'gen',    name:'général',       type:'text',    desc:'Espace principal', notif:2 },
      { id:'intro',  name:'introductions', type:'text',    desc:'Présentez-vous !' },
      { id:'ann',    name:'annonces',      type:'announce',desc:'' },
      { id:'gaming', name:'gaming',        type:'text',    desc:'🎮 Jeux vidéo' },
      { id:'music',  name:'musique',       type:'text',    desc:'🎵 Vos playlists' },
      { id:'vc1',    name:'Vocal lounge',  type:'voice' },
      { id:'vc2',    name:'Gaming VC',     type:'voice' },
    ],
    members: DEMO_MEMBERS,
  };
  APP.servers = [srv];

  APP.messages['gen'] = [
    { id:1, author:DEMO_MEMBERS[0], content:'Bienvenue sur Likoo ! 🎉 Enfin notre propre espace.', time:t, reactions:[{e:'🎉',c:3},{e:'❤️',c:2}] },
    { id:2, author:DEMO_MEMBERS[1], content:'Trop bien les couleurs violet pastel, j\'adore 💜', time:t, reactions:[] },
    { id:3, author:DEMO_MEMBERS[2], content:'Et les modules qu\'on peut déplacer c\'est trop cool 👀', time:t, reactions:[{e:'👀',c:1}] },
    { id:4, author:DEMO_MEMBERS[3], content:'J\'ai invité tout le monde, on est chauds 🔥', time:t, reactions:[{e:'🔥',c:4}] },
  ];
  APP.messages['intro'] = [
    { id:5, author:DEMO_MEMBERS[1], content:'Salut ! Je suis Nino 🎮', time:t, reactions:[] },
    { id:6, author:DEMO_MEMBERS[2], content:'Moi c\'est Léa, dev front 💻', time:t, reactions:[{e:'💙',c:1}] },
  ];
  ['gaming','music','ann','vc1','vc2'].forEach(k => APP.messages[k] = []);
  APP.messages['dm_zara'] = [{ id:7, author:DEMO_MEMBERS[0], content:'Yo ! Tu as vu Likoo ? 😎', time:t, reactions:[] }];
  APP.messages['dm_nino'] = [];
  APP.messages['dm_lea']  = [];
}

// ─────────────────────────────────────────────
// USER
// ─────────────────────────────────────────────
function setupAccount() {
  const name = q('#setupName').value.trim() || 'Utilisateur';
  const tag  = q('#setupTag').value.replace(/\D/g,'').slice(0,4).padStart(4,'0') || rndInt(1000,9999).toString();
  APP.me = { name, tag, av: AVATARS[rndInt(0,AVATARS.length-1)], color: COLORS[rndInt(0,COLORS.length-1)], status:'online' };
  save();
  closeModal('modal-setup');
  startApp();
}

function renderUserDock() {
  // Desktop
  const dock = q('#user-dock');
  if (!dock) return;
  const avHtml = formatAvatar(APP.me.av);
  dock.innerHTML = `
    <div class="user-dock-av" onclick="openModal('modal-settings')" style="background:${APP.me.color}22">
      ${avHtml}
      <div class="status-dot ${APP.me.status}" id="status-dot-main"></div>
    </div>
    <div class="user-dock-info">
      <div class="uname" id="my-display-name">${APP.me.name}</div>
      <div class="utag">#${APP.me.tag}</div>
    </div>
    <div class="dock-btns">
      <button class="dock-btn" onclick="toggleMute(this)" title="Micro">🎙</button>
      <button class="dock-btn" onclick="toggleDeaf(this)" title="Casque">🎧</button>
      <button class="dock-btn" onclick="openModal('modal-settings')">⚙</button>
    </div>
  `;
}

// ─────────────────────────────────────────────
// SERVERS RENDER
// ─────────────────────────────────────────────
function renderServers() {
  const el = q('#servers-scroll');
  if (!el) return;
  let html = `
    <div class="srv-icon tooltip-srv ${APP.view==='dm'?'active':''}" data-tip="Messages Privés" onclick="showDM()">💬</div>
    <div class="srv-sep"></div>
    ${APP.servers.map(s => `
      <div class="srv-icon ${APP.activeSrv?.id===s.id&&APP.view==='server'?'active':''}"
           data-tip="${s.name}" onclick="selectServer('${s.id}')">
        ${s.emoji}
        ${s.channels.some(c=>c.notif)?`<div class="notif-badge">${s.channels.reduce((a,c)=>a+(c.notif||0),0)}</div>`:''}
      </div>
    `).join('')}
    <div class="srv-sep"></div>
    <div class="srv-add" onclick="openModal('modal-create-server')" title="Créer un serveur">+</div>
  `;
  el.innerHTML = html;
}

// ─────────────────────────────────────────────
// CHANNELS RENDER
// ─────────────────────────────────────────────
function renderChannels() {
  const srv = APP.activeSrv;
  const heading = q('#server-heading-name');
  const list = q('#channels-list');
  if (!list) return;

  if (!srv) {
    if (heading) heading.textContent = 'Messages Privés';
    list.innerHTML = `
      <div class="ch-section-lbl">Conversations</div>
      ${DEMO_DMS.map(u => `
        <div class="ch-item ${APP.dmChannel===u.id?'active':''}" onclick="selectDM('${u.id}')">
          <span class="ch-ico">${formatAvatar(u.av)}</span> ${u.name}
        </div>
      `).join('')}
      <div style="padding:8px 10px;margin-top:6px">
        <button class="btn btn-primary" style="width:100%;font-size:12px;padding:7px" onclick="alert('Ajoutez un ami par son tag Likoo !')">+ Ajouter un ami</button>
      </div>
    `;
    return;
  }

  if (heading) heading.textContent = srv.name;
  const texts  = srv.channels.filter(c => c.type !== 'voice');
  const voices = srv.channels.filter(c => c.type === 'voice');

  list.innerHTML = `
    <div class="search-box"><span class="s-ico">🔍</span><input type="text" placeholder="Rechercher…"></div>
    <div class="ch-section-lbl">Salons <span class="ch-add" onclick="openModal('modal-create-channel')">+</span></div>
    ${texts.map(c => `
      <div class="ch-item ${APP.activeCh===c.id?'active':''}" onclick="selectChannel('${c.id}')">
        <span class="ch-ico">${c.type==='announce'?'📢':'#'}</span> ${c.name}
        ${c.notif?`<span class="ch-notif">${c.notif}</span>`:''}
      </div>
    `).join('')}
    <div class="ch-section-lbl" style="margin-top:6px">Vocaux <span class="ch-add" onclick="openModal('modal-create-channel')">+</span></div>
    ${voices.map(c => `
      <div class="ch-item ${APP.activeCh===c.id?'active':''}" onclick="selectChannel('${c.id}')">
        <span class="ch-ico">🔊</span> ${c.name}
      </div>
    `).join('')}
    ${APP.inVoice ? `<div class="voice-strip">🔊 ${APP.inVoice} <span class="v-leave" onclick="leaveVoice()">✕ Quitter</span></div>` : ''}
  `;
}

// ─────────────────────────────────────────────
// MEMBERS RENDER
// ─────────────────────────────────────────────
function renderMembers() {
  const el = q('#members-list');
  if (!el) return;
  const srv = APP.activeSrv;
  if (!srv) { el.innerHTML = ''; return; }

  const groups = [
    { label:'Admin',       list: srv.members.filter(m=>m.role==='Admin'&&m.status!=='offline') },
    { label:'Modérateur',  list: srv.members.filter(m=>m.role==='Modérateur'&&m.status!=='offline') },
    { label:'En ligne',    list: srv.members.filter(m=>m.role==='Membre'&&m.status==='online') },
    { label:'Absent',      list: srv.members.filter(m=>m.role==='Membre'&&m.status==='away') },
    { label:'Hors ligne',  list: srv.members.filter(m=>m.status==='offline') },
  ].filter(g=>g.list.length);

  const self = [{ name:APP.me.name, av:APP.me.av, color:APP.me.color, status:APP.me.status, role:'Membre' }];
  let html = renderMemberGroup('Toi', self);
  groups.forEach(g => html += renderMemberGroup(`${g.label} — ${g.list.length}`, g.list));
  el.innerHTML = html;
}

function renderMemberGroup(label, list) {
  return `<div class="mem-section-lbl">${label}</div>
  ${list.map(m=>`<div class="mem-item">
    <div class="mem-av" style="background:${m.color}22">
      ${formatAvatar(m.av||m.avatar)}
      <div class="mem-dot ${m.status}"></div>
    </div>
    <div><div class="mem-name">${m.name}</div><div class="mem-role">${m.role||''}</div></div>
  </div>`).join('')}`;
}

// ─────────────────────────────────────────────
// CHAT RENDER
// ─────────────────────────────────────────────
function renderChat() {
  const key = activeKey();
  const msgs = key ? (APP.messages[key] || []) : [];
  const el = q('#messages-area');
  if (!el) return;

  // Chat bar
  const barIcon = q('#chat-icon');
  const barName = q('#chat-name');
  const barDesc = q('#chat-desc');

  if (APP.view === 'dm' && APP.dmChannel) {
    const u = DEMO_DMS.find(d=>d.id===APP.dmChannel);
    if (barIcon) barIcon.textContent = u?.av || '💬';
    if (barName) barName.textContent = u?.name || 'Message Privé';
    if (barDesc) barDesc.textContent = u?.status==='online' ? '🟢 En ligne' : '⚫ Hors ligne';
    const inp = q('#msgInput');
    if (inp) inp.placeholder = `Message à ${u?.name || ''}…`;
  } else if (APP.activeCh) {
    const ch = APP.activeSrv?.channels.find(c=>c.id===APP.activeCh);
    if (barIcon) barIcon.textContent = ch?.type==='announce' ? '📢' : '#';
    if (barName) barName.textContent = ch?.name || '';
    if (barDesc) barDesc.textContent = ch?.desc || '';
    const inp = q('#msgInput');
    if (inp) inp.placeholder = `Message #${ch?.name || ''}…`;
  }

  if (!key || msgs.length === 0) {
    const ch = APP.activeSrv?.channels.find(c=>c.id===APP.activeCh);
    el.innerHTML = `<div class="empty-state">
      <div class="big-emoji">${APP.view==='dm'?'💬':'💬'}</div>
      <h3>${APP.view==='dm'?'Début de la conversation':'#'+(ch?.name||'Bienvenue')}</h3>
      <p>${key?'Soyez le premier à écrire ici !':'Sélectionnez un salon ou une conversation.'}</p>
    </div>`;
    return;
  }

  el.innerHTML = msgs.map((m,i) => {
    if (m.system) return `<div class="sys-line">${m.content}</div>`;
    const prev = msgs[i-1];
    const same = prev && !prev.system && prev.author?.name === m.author?.name;
    const auth = m.author || APP.me;
    const isMe = auth.name === APP.me.name;
    const reacts = (m.reactions||[]).map(r=>
      `<span class="react-chip ${r.mine?'mine':''}" onclick="toggleReact('${key}',${m.id},'${r.e}')">${r.e} ${r.c}</span>`
    ).join('');
    const body = m.file ? renderFilePrev(m) : `<div class="msg-content">${esc(m.content)}</div>`;
    const actions = `<div class="msg-act">
      <button class="msg-act-btn" onclick="quickReact('${key}',${m.id})">😊</button>
      ${isMe?`<button class="msg-act-btn" onclick="editMsg('${key}',${m.id})">✏️</button>`:''}
      ${isMe?`<button class="msg-act-btn" style="color:var(--red)" onclick="delMsg('${key}',${m.id})">🗑</button>`:''}
    </div>`;
    if (same) return `<div class="msg-wrap">
      <div style="width:36px;text-align:center;font-size:10px;color:var(--text4);padding-top:3px;flex-shrink:0">${m.time}</div>
      <div class="msg-body">${body}<div class="react-row">${reacts}</div></div>${actions}
    </div>`;
    const avatarHtml = formatAvatar(auth.av||auth.avatar);
    return `<div class="msg-wrap">
      <div class="msg-avatar" style="background:${auth.color}22">${avatarHtml}</div>
      <div class="msg-body">
        <div class="msg-meta">
          <span class="msg-author" style="color:${auth.color}">${auth.name}</span>
          <span class="msg-time">${m.time}</span>
        </div>
        ${body}<div class="react-row">${reacts}</div>
      </div>${actions}
    </div>`;
  }).join('');

  scrollBottom();
}

function renderFilePrev(m) {
  if (m.file.type.startsWith('image/')) return `<img src="${m.file.data}" class="img-preview">`;
  return `<div class="file-chip"><span style="font-size:22px">📄</span><div><div style="font-size:13px;font-weight:700">${m.file.name}</div><div style="font-size:11px;color:var(--text4)">${m.file.size}</div></div></div>`;
}

// ─────────────────────────────────────────────
// NAVIGATION
// ─────────────────────────────────────────────
function showHome() {
  APP.view = 'home'; APP.activeSrv = null; APP.activeCh = null; APP.dmChannel = null;
  const barIcon = q('#chat-icon'); const barName = q('#chat-name'); const barDesc = q('#chat-desc');
  if (barIcon) barIcon.textContent = '✦';
  if (barName) barName.textContent = 'Likoo';
  if (barDesc) barDesc.textContent = '';
  const el = q('#messages-area');
  if (el) el.innerHTML = `<div class="empty-state">
    <div class="big-emoji">💜</div>
    <h3 style="font-size:28px">Likoo</h3>
    <p>Votre espace, vos règles.<br>Rejoignez un serveur ou démarrez une conversation.</p>
  </div>`;
  renderServers(); renderChannels(); renderMembers();
}

function showDM() {
  APP.view = 'dm'; APP.activeSrv = null; APP.activeCh = null;
  renderServers(); renderChannels();
  if (!APP.dmChannel) renderChat();
}

function selectServer(id) {
  APP.view = 'server';
  APP.activeSrv = APP.servers.find(s=>s.id===id);
  APP.dmChannel = null;
  renderServers(); renderChannels(); renderMembers();
  // Auto-select first text channel
  const first = APP.activeSrv?.channels.find(c=>c.type!=='voice');
  if (first) selectChannel(first.id);
  else renderChat();
  // Mobile: go to channels view
  if (APP.isMobile) switchMobTab('channels');
}

function selectChannel(id) {
  const ch = APP.activeSrv?.channels.find(c=>c.id===id);
  if (!ch) return;
  if (ch.type === 'voice') { joinVoice(id); return; }
  APP.activeCh = id; ch.notif = 0;
  renderChannels(); renderChat();
  if (APP.isMobile) switchMobTab('chat');
}

function selectDM(id) {
  APP.dmChannel = id; APP.view = 'dm';
  if (!APP.messages[id]) APP.messages[id] = [];
  renderChannels(); renderChat();
  if (APP.isMobile) switchMobTab('chat');
  // Simulate first message
  if (APP.messages[id].length === 0) {
    setTimeout(() => {
      const u = DEMO_DMS.find(d=>d.id===id);
      if (!u) return;
      const greets = ['Salut ! 👋','Hey, ça va ?','Yo ! T\'es là ?'];
      pushMsg(id, { author:u, content:greets[rndInt(0,greets.length-1)] });
    }, 900);
  }
}

// ─────────────────────────────────────────────
// MESSAGING
// ─────────────────────────────────────────────
function activeKey() {
  return APP.view === 'dm' ? APP.dmChannel : APP.activeCh;
}

function sendMessage() {
  const inp = q('#msgInput');
  const text = inp ? inp.value.trim() : '';
  const key = activeKey();
  if (!text || !key) return;
  pushMsg(key, { author: { name:APP.me.name, av:APP.me.av, color:APP.me.color }, content: text });
  inp.value = ''; inp.style.height = '';
  // Auto reply
  if (Math.random() > 0.45 && APP.view === 'server') {
    setTimeout(() => simReply(key), 1000 + rndInt(0,2000));
  }
  if (APP.view === 'dm') {
    setTimeout(() => simDMReply(key), 800 + rndInt(0,1500));
  }
}

function pushMsg(key, data) {
  if (!APP.messages[key]) APP.messages[key] = [];
  const msg = { id: Date.now(), time: now(), reactions: [], ...data };
  APP.messages[key].push(msg);
  renderChat();
}

function simReply(key) {
  const online = DEMO_MEMBERS.filter(m=>m.status==='online');
  const m = online[rndInt(0,online.length-1)];
  const lines = ['Trop bien !','Haha oui 😂','Je suis d\'accord','On vocal ce soir ?','Exactement !','++','❤️','Bien joué !','On s\'organise ?'];
  pushMsg(key, { author:m, content:lines[rndInt(0,lines.length-1)] });
}

function simDMReply(key) {
  if (APP.dmChannel !== key) return;
  const u = DEMO_DMS.find(d=>d.id===key); if (!u) return;
  const lines = ['😊','OK !','Ouais !','👍','Trop bien','Je vois 👀','Haha','Vraiment ?'];
  pushMsg(key, { author:u, content:lines[rndInt(0,lines.length-1)] });
}

let typingTimer;
function simTyping() {
  if (Math.random() > 0.65 && APP.view === 'server') {
    const m = DEMO_MEMBERS.filter(m=>m.status==='online')[rndInt(0,1)];
    const el = q('#typing-row');
    if (el) el.textContent = `${m.name} est en train d'écrire…`;
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => { const e = q('#typing-row'); if(e) e.textContent = ''; }, 2000);
  }
}

function toggleReact(key, id, e) {
  const msg = APP.messages[key]?.find(m=>m.id===id); if (!msg) return;
  const ex = msg.reactions.find(r=>r.e===e);
  if (ex) {
    ex.mine ? ex.c-- : ex.c++;
    ex.mine = !ex.mine;
    if (ex.c <= 0) msg.reactions = msg.reactions.filter(r=>r.e!==e);
  } else {
    msg.reactions.push({ e, c:1, mine:true });
  }
  renderChat();
}

function quickReact(key, id) {
  const opts = ['❤️','👍','😂','🔥','🎉','👀','💜','✨'];
  toggleReact(key, id, opts[rndInt(0,opts.length-1)]);
}

function editMsg(key, id) {
  const msg = APP.messages[key]?.find(m=>m.id===id); if (!msg) return;
  const t = prompt('Modifier :', msg.content);
  if (t && t.trim()) { msg.content = t.trim() + ' *(modifié)*'; renderChat(); }
}

function delMsg(key, id) {
  APP.messages[key] = APP.messages[key].filter(m=>m.id!==id);
  renderChat();
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function autoResize(t) { t.style.height = ''; t.style.height = Math.min(t.scrollHeight, 100) + 'px'; }

function handleFile(inp) {
  const file = inp.files[0]; if (!file) return;
  const key = activeKey(); if (!key) return;
  const r = new FileReader();
  r.onload = e => {
    pushMsg(key, {
      author: { name:APP.me.name, av:APP.me.av, color:APP.me.color },
      content: '',
      file: { name:file.name, type:file.type, size:fmtBytes(file.size), data:e.target.result }
    });
  };
  r.readAsDataURL(file); inp.value = '';
}

function scrollBottom() {
  const el = q('#messages-area');
  if (el) requestAnimationFrame(() => el.scrollTop = el.scrollHeight);
}

// ─────────────────────────────────────────────
// SERVERS & CHANNELS MANAGEMENT
// ─────────────────────────────────────────────
function createServer() {
  const name  = q('#new-srv-name')?.value.trim(); if (!name) return;
  const emoji = q('#new-srv-emoji')?.value.trim() || '🌐';
  const id    = 'srv_' + Date.now();
  const srv   = {
    id, name, emoji,
    channels: [
      { id:id+'_g', name:'général', type:'text', desc:'Salon principal' },
      { id:id+'_v', name:'Vocal',   type:'voice' },
    ],
    members: [DEMO_MEMBERS[rndInt(0,3)]],
  };
  APP.servers.push(srv);
  APP.messages[id+'_g'] = [{ id:Date.now(), system:true, content:`${APP.me.name} a créé "${name}" 🎉`, time:now(), reactions:[] }];
  q('#new-srv-name').value = ''; q('#new-srv-emoji').value = '';
  closeModal('modal-create-server');
  selectServer(id);
  renderMobileServers();
}

let newChType = 'text';
function selectChType(el) {
  qa('.chip').forEach(c=>c.classList.remove('sel'));
  el.classList.add('sel');
  newChType = el.dataset.type;
}

function createChannel() {
  if (!APP.activeSrv) return;
  const name = q('#new-ch-name')?.value.trim().toLowerCase().replace(/\s+/g,'-') || 'nouveau';
  APP.activeSrv.channels.push({
    id: APP.activeSrv.id+'_'+name+'_'+Date.now(),
    name, type: newChType, desc: '',
  });
  q('#new-ch-name').value = '';
  closeModal('modal-create-channel');
  renderChannels();
}

// ─────────────────────────────────────────────
// VOICE
// ─────────────────────────────────────────────
function joinVoice(id) {
  const ch = APP.activeSrv?.channels.find(c=>c.id===id);
  APP.inVoice = ch?.name || 'Vocal';
  APP.activeCh = id;
  renderChannels();
}
function leaveVoice() { APP.inVoice = null; APP.activeCh = null; renderChannels(); }

// ─────────────────────────────────────────────
// SETTINGS
// ─────────────────────────────────────────────
function openSettingsModal() {
  const el = q('#set-name'); if (el) el.value = APP.me.name;
  // preview current avatar if present
  const prev = q('#avatarPreview');
  if(prev){
    const av = APP.me.av;
    // use formatAvatar helper which already handles data/blobs
    prev.innerHTML = formatAvatar(av);
  }
  openModal('modal-settings');
}
function saveSettings() {
  // close modal first so user sees feedback immediately
  closeModal('modal-settings');
  const n = q('#set-name')?.value.trim() || APP.me.name;
  APP.me.name = n;
  // avatar may have been updated already via uploadAvatar
  // sync with backend if logged in
  if (APP.me && APP.me.token) {
    fetch('/api/auth/me', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + APP.me.token
      },
      body: JSON.stringify({ username: APP.me.name, avatar: APP.me.av })
    }).then(r=>r.json()).then(d=>{
      console.log('profile sync', d);
    }).catch(console.error);
  }
  save();
  const el = q('#my-display-name'); if (el) el.textContent = n;
  // refresh UI across the app
  renderUserDock();
  renderServers();
  renderChannels();
  renderMembers();
  const mem = q('#members-list .mem-item:first-child img');
  if(mem) mem.src = APP.me.av;
}
function setStatus(s) {
  APP.me.status = s; save();
  const colors = { online:'var(--green)', away:'var(--amber)', dnd:'var(--red)', offline:'var(--text4)' };
  const dot = q('#status-dot-main'); if (dot) dot.style.background = colors[s];
}
function toggleMute(b) { b.style.opacity = b.style.opacity === '0.4' ? '1' : '0.4'; }
function toggleDeaf(b) { b.style.opacity = b.style.opacity === '0.4' ? '1' : '0.4'; }

// ─────────────────────────────────────────────
// EMOJI PICKER
// ─────────────────────────────────────────────
function buildEmojiPicker() {
  const el = q('#emoji-picker');
  if (!el) return;
  el.innerHTML = `<div class="emoji-grid">${EMOJIS.map(e=>`<button class="emoji-cell" onclick="insertEmoji('${e}')">${e}</button>`).join('')}</div>`;
}
function toggleEmoji() { q('#emoji-picker')?.classList.toggle('open'); }
function insertEmoji(e) {
  const inp = q('#msgInput'); if (inp) { inp.value += e; inp.focus(); }
  q('#emoji-picker')?.classList.remove('open');
}

// ─────────────────────────────────────────────
// MODALS
// ─────────────────────────────────────────────
function openModal(id) { q(`#${id}`)?.classList.add('open'); }
function closeModal(id) { q(`#${id}`)?.classList.remove('open'); }

// ─────────────────────────────────────────────
// MOBILE
// ─────────────────────────────────────────────
function renderMobileServers() {
  const el = q('#mob-servers-grid');
  if (!el) return;
  el.innerHTML = `
    <div class="mob-srv-card ${APP.view==='dm'?'active':''}" onclick="showDM();switchMobTab('channels')">
      <div class="mob-srv-icon">💬</div>
      <div class="mob-srv-name">MP</div>
    </div>
    ${APP.servers.map(s=>`
      <div class="mob-srv-card ${APP.activeSrv?.id===s.id?'active':''}" onclick="selectServer('${s.id}')">
        <div class="mob-srv-icon">${s.emoji}</div>
        <div class="mob-srv-name">${s.name}</div>
      </div>
    `).join('')}
    <div class="mob-srv-card" onclick="openModal('modal-create-server')">
      <div class="mob-srv-icon" style="border:2px dashed rgba(139,92,246,0.4);font-size:28px;color:var(--violet)">+</div>
      <div class="mob-srv-name">Nouveau</div>
    </div>
  `;
}

function renderMobileChannels() {
  const el = q('#mob-channels-list');
  if (!el) return;
  const srv = APP.activeSrv;
  if (!srv && APP.view !== 'dm') { el.innerHTML = `<div style="padding:20px;text-align:center;color:var(--text4)">Sélectionnez un serveur</div>`; return; }
  if (APP.view === 'dm') {
    el.innerHTML = `<div class="ch-section-lbl">Messages Privés</div>
      ${DEMO_DMS.map(u=>`<div class="ch-item ${APP.dmChannel===u.id?'active':''}" onclick="selectDM('${u.id}')">${formatAvatar(u.av)} ${u.name}</div>`).join('')}`;
    return;
  }
  const texts  = srv.channels.filter(c=>c.type!=='voice');
  const voices = srv.channels.filter(c=>c.type==='voice');
  el.innerHTML = `
    <div class="ch-section-lbl">${srv.name}</div>
    ${texts.map(c=>`<div class="ch-item ${APP.activeCh===c.id?'active':''}" onclick="selectChannel('${c.id}')">${c.type==='announce'?'📢':'#'} ${c.name}</div>`).join('')}
    <div class="ch-section-lbl" style="margin-top:6px">Vocaux</div>
    ${voices.map(c=>`<div class="ch-item" onclick="selectChannel('${c.id}')">🔊 ${c.name}</div>`).join('')}
  `;
}

function renderMobileMembers() {
  const el = q('#mob-members-list');
  if (!el || !APP.activeSrv) return;
  el.innerHTML = renderMemberGroup('Membres', APP.activeSrv.members);
}

function switchMobTab(tab) {
  APP.mobTab = tab;
  qa('.mob-view').forEach(v => v.classList.remove('active'));
  const view = q(`#mob-view-${tab}`);
  if (view) view.classList.add('active');
  qa('.mob-nav-btn').forEach(b => b.classList.remove('active'));
  const btn = q(`#mob-btn-${tab}`);
  if (btn) btn.classList.add('active');
  // Render content
  if (tab === 'channels') renderMobileChannels();
  if (tab === 'members') renderMobileMembers();
  if (tab === 'chat') renderChat();
}

// ─────────────────────────────────────────────
// DRAG & DROP MODULE SYSTEM
// ─────────────────────────────────────────────
const DRAG = {
  active: null,
  startX: 0, startY: 0,
  origLeft: 0, origTop: 0,
  origW: 0, origH: 0,
  mode: null, // 'move' | 'resize'
};

const SNAP_MARGIN = 18;
const SNAP_EDGE = 60;

function initDrag(panelId) {
  const panel = q(`#${panelId}`);
  if (!panel) return;
  const header = panel.querySelector('.panel-header');
  const resizer = panel.querySelector('.panel-resize');

  if (header) {
    header.addEventListener('mousedown', e => startDrag(e, panel, 'move'));
    header.addEventListener('touchstart', e => startDrag(e, panel, 'move'), { passive:true });
  }
  if (resizer) {
    resizer.addEventListener('mousedown', e => startDrag(e, panel, 'resize'));
    resizer.addEventListener('touchstart', e => startDrag(e, panel, 'resize'), { passive:true });
  }
}

function startDrag(e, panel, mode) {
  e.preventDefault?.();
  const pt = getPoint(e);
  DRAG.active = panel;
  DRAG.mode = mode;
  DRAG.startX = pt.x;
  DRAG.startY = pt.y;
  DRAG.origLeft = parseInt(panel.style.left) || panel.offsetLeft;
  DRAG.origTop  = parseInt(panel.style.top)  || panel.offsetTop;
  DRAG.origW = panel.offsetWidth;
  DRAG.origH = panel.offsetHeight;
  panel.classList.add('dragging');
  panel.style.zIndex = getMaxZ() + 1;
  document.body.style.cursor = mode === 'resize' ? 'nwse-resize' : 'grabbing';
}

document.addEventListener('mousemove', onDrag);
document.addEventListener('touchmove', onDrag, { passive:false });
document.addEventListener('mouseup', stopDrag);
document.addEventListener('touchend', stopDrag);

function onDrag(e) {
  if (!DRAG.active) return;
  e.preventDefault?.();
  const pt = getPoint(e);
  const dx = pt.x - DRAG.startX;
  const dy = pt.y - DRAG.startY;
  const panel = DRAG.active;
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  if (DRAG.mode === 'move') {
    let newLeft = DRAG.origLeft + dx;
    let newTop  = DRAG.origTop  + dy;
    const pw = panel.offsetWidth;
    const ph = panel.offsetHeight;
    // Clamp inside viewport
    newLeft = Math.max(-pw * 0.4, Math.min(newLeft, vw - pw * 0.6));
    newTop  = Math.max(0, Math.min(newTop, vh - 40));
    // Edge snap
    if (Math.abs(newLeft) < SNAP_EDGE) newLeft = SNAP_MARGIN;
    if (Math.abs(newLeft + pw - vw) < SNAP_EDGE) newLeft = vw - pw - SNAP_MARGIN;
    if (Math.abs(newTop) < SNAP_EDGE/2) newTop = SNAP_MARGIN;
    if (Math.abs(newTop + ph - vh) < SNAP_EDGE) newTop = vh - ph - SNAP_MARGIN;
    panel.style.left = newLeft + 'px';
    panel.style.top  = newTop  + 'px';
  } else if (DRAG.mode === 'resize') {
    let newW = Math.max(140, DRAG.origW + dx);
    let newH = Math.max(80,  DRAG.origH + dy);
    // Clamp to viewport
    const left = parseInt(panel.style.left) || 0;
    const top  = parseInt(panel.style.top)  || 0;
    newW = Math.min(newW, vw - left - 12);
    newH = Math.min(newH, vh - top - 12);
    panel.style.width  = newW + 'px';
    panel.style.height = newH + 'px';
  }
}

function stopDrag() {
  if (!DRAG.active) return;
  DRAG.active.classList.remove('dragging');
  DRAG.active = null;
  document.body.style.cursor = '';
}

function bringToFront(panelId) {
  const panel = q(`#${panelId}`);
  if (panel) panel.style.zIndex = getMaxZ() + 1;
}

function getMaxZ() {
  let max = 10;
  qa('.panel').forEach(p => { const z = parseInt(p.style.zIndex)||0; if(z>max) max=z; });
  return max;
}

function getPoint(e) {
  if (e.touches && e.touches.length > 0) return { x:e.touches[0].clientX, y:e.touches[0].clientY };
  return { x:e.clientX, y:e.clientY };
}

// Panel minimize / maximize
function minimizePanel(id) {
  const p = q(`#${id}`);
  if (!p) return;
  if (p._minimized) {
    p.style.height = p._origH + 'px';
    p._minimized = false;
  } else {
    p._origH = p.offsetHeight;
    p.style.height = '42px';
    p.style.overflow = 'hidden';
    p._minimized = true;
  }
}

function closePanel(id) {
  const p = q(`#${id}`);
  if (p) p.style.display = 'none';
  // Show a restore button
  showRestoreBtn(id);
}

function showRestoreBtn(id) {
  const names = { 'panel-servers':'Serveurs', 'panel-channels':'Salons', 'panel-chat':'Chat', 'panel-members':'Membres' };
  const btn = document.createElement('button');
  btn.className = 'layout-toggle';
  btn.style.cssText = 'position:fixed;bottom:50px;left:unset;transform:none;';
  btn.textContent = '🔲 ' + (names[id]||id);
  btn.onclick = () => { const p=q(`#${id}`); if(p){p.style.display='flex';} btn.remove(); };
  document.body.appendChild(btn);
}

// ─────────────────────────────────────────────
// LAYOUT SAVE / RESTORE
// ─────────────────────────────────────────────
function saveLayout() {
  const layout = {};
  qa('.panel').forEach(p => {
    layout[p.id] = {
      left: p.style.left, top: p.style.top,
      width: p.style.width, height: p.style.height,
    };
  });
  localStorage.setItem('likoo_layout', JSON.stringify(layout));
}

function restoreLayout() {
  const saved = localStorage.getItem('likoo_layout');
  if (!saved) return;
  try {
    const layout = JSON.parse(saved);
    Object.entries(layout).forEach(([id, pos]) => {
      const p = q(`#${id}`);
      if (!p) return;
      if (pos.left)   p.style.left   = pos.left;
      if (pos.top)    p.style.top    = pos.top;
      if (pos.width)  p.style.width  = pos.width;
      if (pos.height) p.style.height = pos.height;
    });
  } catch(e) {}
}

// Save layout on panel interaction
setInterval(saveLayout, 3000);

// ─────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────
function q(sel) { return document.querySelector(sel); }
function qa(sel) { return document.querySelectorAll(sel); }
function now() { return new Date().toLocaleTimeString('fr',{hour:'2-digit',minute:'2-digit'}); }
function rndInt(a,b) { return Math.floor(Math.random()*(b-a+1))+a; }
function save() { localStorage.setItem('likoo_state', JSON.stringify(APP.me)); }
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function fmtBytes(b) {
  if (b<1024) return b+' B';
  if (b<1048576) return (b/1024).toFixed(1)+' KB';
  return (b/1048576).toFixed(1)+' MB';
}

// Close overlays on click outside
document.addEventListener('click', e => {
  if (!e.target.closest('#emoji-picker') && !e.target.closest('.inp-icon-btn')) {
    q('#emoji-picker')?.classList.remove('open');
  }
  if (e.target.classList.contains('overlay')) {
    e.target.classList.remove('open');
  }
});

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  boot();
  // Init drag for all panels
  ['panel-servers','panel-channels','panel-chat','panel-members'].forEach(id => initDrag(id));
  // Click panels to bring to front
  qa('.panel').forEach(p => {
    p.addEventListener('mousedown', () => bringToFront(p.id));
    p.addEventListener('touchstart', () => bringToFront(p.id));
  });
  // Restore layout
  restoreLayout();
  // Mobile default tab
  if (window.innerWidth < 700) switchMobTab('servers');
});
