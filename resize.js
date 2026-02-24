/**
 * RESIZABLE WORKSPACE — SMOOTH VERSION
 * Deux handles indépendants avec animations fluides
 * - Gauche: Salons ↔ Chat (flexible)
 * - Droit: Chat (flexible) ↔ Membres
 */

let isResizing = false;
let resizeDirection = null;
let startX = 0;
let startWidth = 0;
let animationFrame = null;

function initResize() {
  const workspace = document.getElementById('workspace');
  const zoneLeft = document.getElementById('zoneLeft');
  const zoneRight = document.getElementById('zoneRight');
  
  if (!workspace || !zoneLeft || !zoneRight) return;

  // Handle GAUCHE (entre Salons et Chat)
  const handleLeft = document.createElement('div');
  handleLeft.className = 'resize-handle resize-handle-v-left';
  handleLeft.id = 'handleLeftCenter';
  zoneLeft.appendChild(handleLeft);

  // Handle DROIT (entre Chat et Membres)
  const handleRight = document.createElement('div');
  handleRight.className = 'resize-handle resize-handle-v-right';
  handleRight.id = 'handleCenterRight';
  zoneRight.appendChild(handleRight);

  // Events
  handleLeft.addEventListener('mousedown', (e) => startResize(e, 'left'));
  handleRight.addEventListener('mousedown', (e) => startResize(e, 'right'));

  document.addEventListener('mousemove', onResize);
  document.addEventListener('mouseup', stopResize);
}

function startResize(e, direction) {
  isResizing = true;
  resizeDirection = direction;
  startX = e.clientX;
  
  const workspace = document.getElementById('workspace');
  const style = window.getComputedStyle(workspace);
  const columns = style.gridTemplateColumns.split(' ');
  
  if (direction === 'left') {
    startWidth = parseFloat(columns[0]); // Salons
    document.getElementById('handleLeftCenter').classList.add('active');
  } else {
    startWidth = parseFloat(columns[2]); // Membres
    document.getElementById('handleCenterRight').classList.add('active');
  }
  
  // Enlever la transition temporairement pour plus de fluidité
  workspace.style.transition = 'none';
  
  document.body.style.userSelect = 'none';
  document.body.style.cursor = 'col-resize';
}

function onResize(e) {
  if (!isResizing || !resizeDirection) return;
  
  // Annuler le frame précédent s'il existe
  if (animationFrame) {
    cancelAnimationFrame(animationFrame);
  }
  
  // Utiliser requestAnimationFrame pour une meilleure performance
  animationFrame = requestAnimationFrame(() => {
    const delta = e.clientX - startX;
    const workspace = document.getElementById('workspace');
    const style = window.getComputedStyle(workspace);
    const columns = style.gridTemplateColumns.split(' ');
    
    let leftWidth = parseFloat(columns[0]);   // Salons
    let rightWidth = parseFloat(columns[2]);  // Membres
    const minWidth = 150;
    
    if (resizeDirection === 'left') {
      // Handle gauche: Change la taille des Salons
      let newLeftWidth = startWidth + delta;
      if (newLeftWidth >= minWidth) {
        leftWidth = newLeftWidth;
      }
    } else if (resizeDirection === 'right') {
      // Handle droit: Change la taille des Membres
      let newRightWidth = startWidth - delta;
      if (newRightWidth >= minWidth) {
        rightWidth = newRightWidth;
      }
    }
    
    // Update le grid immédiatement (sans attendre un frame)
    workspace.style.gridTemplateColumns = `${leftWidth}px 1fr ${rightWidth}px`;
  });
}

function stopResize() {
  if (!isResizing) return;
  
  isResizing = false;
  
  // Sauvegarder les dimensions
  const workspace = document.getElementById('workspace');
  const style = window.getComputedStyle(workspace);
  const columns = style.gridTemplateColumns.split(' ');
  
  localStorage.setItem('layoutLeftWidth', parseFloat(columns[0]));
  localStorage.setItem('layoutRightWidth', parseFloat(columns[2]));
  
  const handleLeft = document.getElementById('handleLeftCenter');
  const handleRight = document.getElementById('handleCenterRight');
  if (handleLeft) handleLeft.classList.remove('active');
  if (handleRight) handleRight.classList.remove('active');
  
  // Remettre la transition
  workspace.style.transition = '';
  
  document.body.style.userSelect = 'auto';
  document.body.style.cursor = 'auto';
  
  resizeDirection = null;
  
  if (animationFrame) {
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }
}

// Réinitialiser
function resetLayout() {
  localStorage.removeItem('layoutLeftWidth');
  localStorage.removeItem('layoutRightWidth');
  
  const workspace = document.getElementById('workspace');
  if (workspace) {
    workspace.style.gridTemplateColumns = '240px 1fr 220px';
  }
  console.log('✅ Layout réinitialisé: Salons 240px | Chat flexible | Membres 220px');
}

// Charger les préférences
function loadLayoutPreferences() {
  const workspace = document.getElementById('workspace');
  if (!workspace) return;
  
  const leftWidth = localStorage.getItem('layoutLeftWidth');
  const rightWidth = localStorage.getItem('layoutRightWidth');
  
  let left = leftWidth ? parseFloat(leftWidth) : 240;
  let right = rightWidth ? parseFloat(rightWidth) : 220;
  
  // Validation
  const totalWidth = window.innerWidth;
  if (left >= 150 && right >= 150 && (left + right) < totalWidth - 100) {
    workspace.style.gridTemplateColumns = `${left}px 1fr ${right}px`;
  } else {
    resetLayout();
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    loadLayoutPreferences();
    initResize();
  }, 100);
});

if (window.location.search.includes('reset-layout')) {
  resetLayout();
}
