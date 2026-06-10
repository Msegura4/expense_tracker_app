// ─── ÉTAT ──────────────────────────────────────────────────────────────
let currentFile = null;

// ─── ÉLÉMENTS ──────────────────────────────────────────────────────────
const fileInput     = document.getElementById('file-input');
const dropZone      = document.getElementById('drop-zone');
const dropText      = document.getElementById('drop-text');
const preview       = document.getElementById('preview');
const uploadActions = document.getElementById('upload-actions');
const analyzeBtn    = document.getElementById('analyze-btn');
const resetBtn      = document.getElementById('reset-btn');
const formSection   = document.getElementById('form-section');
const resultSection = document.getElementById('result-section');
const statusMsg     = document.getElementById('status-msg');

// ─── SÉLECTION FICHIER ─────────────────────────────────────────────────
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) loadFile(file);
});

// ─── DRAG & DROP ───────────────────────────────────────────────────────
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) loadFile(file);
});

// ─── CHARGEMENT IMAGE ──────────────────────────────────────────────────
function loadFile(file) {
  currentFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    preview.hidden = false;
    dropText.style.display = 'none';
    uploadActions.style.display = 'flex';
    setStatus(`> Image chargée : ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);
  };
  reader.readAsDataURL(file);
}

// ─── ANALYSE ───────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  if (!currentFile) return;

  setStatus('> Analyse en cours...');
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = '> ANALYSE EN COURS...';

  const formData = new FormData();
  formData.append('file', currentFile);

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      body: formData
    });

    const html = await res.text();

    if (!res.ok) {
      showError(html);
      return;
    }

    document.getElementById('form-container').innerHTML = html;
    formSection.style.display = 'block';
    formSection.scrollIntoView({ behavior: 'smooth' });
    setStatus('> Extraction terminée — vérifiez et corrigez les champs si nécessaire');

  } catch (err) {
    showError(`<div class="error"><p>❌ Erreur réseau : ${err.message}</p></div>`);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = '> ANALYSER L\'IMAGE';
  }
});

// ─── RÉINITIALISATION ──────────────────────────────────────────────────
resetBtn.addEventListener('click', () => {
  currentFile = null;
  fileInput.value = '';
  preview.src = '';
  preview.hidden = true;
  dropText.style.display = 'block';
  uploadActions.style.display = 'none';
  formSection.style.display = 'none';
  resultSection.style.display = 'none';
  document.getElementById('form-container').innerHTML = '';
  document.getElementById('result').innerHTML = '';
  setStatus('> En attente d\'une image...');
});

// ─── ÉVÉNEMENTS HTMX ───────────────────────────────────────────────────
document.body.addEventListener('htmx:afterSwap', (e) => {
  if (e.detail.target.id === 'result') {
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
    setStatus('> Note de frais envoyée vers Google Sheets ✓');
  }
});

document.body.addEventListener('htmx:responseError', (e) => {
  resultSection.style.display = 'block';
  document.getElementById('result').innerHTML = `
    <div class="error"><p>❌ Erreur serveur : ${e.detail.xhr.status}</p></div>
  `;
  setStatus('> Erreur lors de l\'envoi');
});

// ─── UTILS ─────────────────────────────────────────────────────────────
function setStatus(msg) {
  statusMsg.textContent = msg;
}

function showError(html) {
  formSection.style.display = 'block';
  document.getElementById('form-container').innerHTML = html;
  setStatus('> Erreur lors de l\'analyse');
}
