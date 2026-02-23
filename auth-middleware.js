/* ═══════════════════════════════════════════════════
   MIDDLEWARE D'AUTHENTIFICATION — app.js
   À ajouter au début de app.js
   ═══════════════════════════════════════════════════ */

// ─────────────────────────────────────────────
// AUTHENTIFICATION
// ─────────────────────────────────────────────
function checkAuth() {
  const token = localStorage.getItem('likoo_token');
  const user = localStorage.getItem('likoo_user');
  
  if (!token || !user) {
    window.location.href = '/auth.html';
    return false;
  }
  
  try {
    APP.me = JSON.parse(user);
    APP.token = token;
    return true;
  } catch(e) {
    localStorage.removeItem('likoo_token');
    localStorage.removeItem('likoo_user');
    window.location.href = '/auth.html';
    return false;
  }
}

function logout() {
  localStorage.removeItem('likoo_token');
  localStorage.removeItem('likoo_user');
  location.reload();
}

// API Helper avec JWT
async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('likoo_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
  
  const response = await fetch(`http://localhost:5000${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers
    }
  });
  
  if (response.status === 401) {
    // Token expiré
    logout();
    return null;
  }
  
  return response;
}

// ─────────────────────────────────────────────
// À AJOUTER À LA FONCTION boot()
// ─────────────────────────────────────────────
/*
function boot() {
  if (!checkAuth()) return;
  
  // ... reste du code existant
}
*/

// ─────────────────────────────────────────────
// REMPLACER LES APPELS FETCH
// ─────────────────────────────────────────────
/*
À la place de:
  fetch('/api/servers')
  
Utiliser:
  apiCall('/api/servers')
*/
