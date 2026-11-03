import { Vue3D } from './vue3d.js';
import { mgi, pose, depuisRPY } from './cinematique.js';

const NOMS_AXES = ['Base', 'Épaule', 'Coude', 'Avant-bras', 'Poignet', 'Rotation pince'];
const LIMITES_DEFAUT = { min: [-90, -90, -100, -180, -90, -180], max: [90, 90, 90, 180, 90, 180] };

const $ = (s) => document.querySelector(s);
const fmt = (v, n = 1) => (Math.abs(v) < 0.05 && n <= 1 ? 0 : v).toFixed(n).replace('.', ',');

let etat = null;           // dernier état reçu du serveur
let limites = LIMITES_DEFAUT;
let consigne = [0, 0, 0, 0, 0, 0];
let consigneModifiee = false; // modifications non envoyées (envoi direct désactivé)
let qApercu = [0, 0, 0, 0, 0, 0]; // pose affichée hors connexion
let ws = null;

const vue = new Vue3D($('#vue3d'));
window.mkx3d = { vue }; // accès pour le débogage depuis la console
$('#vue3d').addEventListener('modele', (e) => {
  $('#legende-modele').textContent = e.detail === 'blender' ? 'Modèle 3D Blender' : 'Modèle simplifié (bras.glb absent)';
});

// ---------------------------------------------------------------- liaison serveur

function envoyer(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
  else toast("Serveur injoignable : vérifie que serveur/app.py tourne.", true);
}

function connecterWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => envoyer({ type: 'ports' });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.type === 'etat') majEtat(m);
    else if (m.type === 'journal') ajouterJournal(m);
    else if (m.type === 'ports') majPorts(m.ports);
    else if (m.type === 'erreur') toast(m.message, true);
  };
  ws.onclose = () => {
    etat = null;
    majEtatConnexion();
    setTimeout(connecterWS, 1500);
  };
}

function connecte() { return !!(etat && etat.connecte); }

// ---------------------------------------------------------------- barre du haut

function majPorts(ports) {
  const sel = $('#ports');
  const avant = sel.value;
  sel.innerHTML = '';
  for (const p of ports) {
    const o = new Option(`${p.port} — ${p.description}`, p.port);
    sel.add(o);
  }
  sel.add(new Option('Simulateur (sans bras)', 'simulateur'));
  if ([...sel.options].some((o) => o.value === avant)) sel.value = avant;
}

function majEtatConnexion() {
  const pastille = $('#pastille');
  pastille.className = 'pastille';
  let texte = 'Serveur déconnecté';
  if (etat) {
    if (etat.connexion_en_cours) { pastille.classList.add('attente'); texte = 'Connexion…'; }
    else if (etat.connecte) {
      pastille.classList.add(etat.simulateur ? 'sim' : 'ok');
      texte = etat.simulateur ? 'Simulateur' : `Connecté (${etat.port})`;
      if (etat.occupe) texte += ' · en mouvement';
    } else texte = 'Hors ligne : aperçu seulement';
  }
  $('#etat-texte').textContent = texte;
  const b = $('#bouton-connexion');
  b.textContent = connecte() ? 'Déconnecter' : 'Connecter';
  b.disabled = !etat || etat.connexion_en_cours;
  $('#ports').disabled = connecte();
  $('#bandeau-calibration').hidden = !(connecte() && !etat.calibre);
  $('#calib-derniere').hidden = !(etat && etat.derniere_connue);
  if (etat && etat.derniere_connue) {
    $('#calib-derniere').textContent = `Reprendre la dernière position (${etat.derniere_connue.map((v) => fmt(v, 0)).join(' / ')})`;
  }
  $('#firmware-info').textContent = !connecte() ? '' : etat.firmware_q
    ? 'Firmware avec retour de position (commande Q) : la position est relue après un arrêt.'
    : "Firmware d'origine : après un ARRÊT, la position affichée est estimée. Le firmware V2_011 fourni corrige ça.";
}

$('#bouton-connexion').onclick = () => {
  if (connecte()) envoyer({ type: 'deconnecter' });
  else envoyer({ type: 'connecter', port: $('#ports').value });
};
$('#rafraichir').onclick = () => envoyer({ type: 'ports' });

function arret() {
  envoyer({ type: 'stop' });
}
$('#arret').onclick = arret;
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.preventDefault(); arret(); } });

// ---------------------------------------------------------------- état

function qAffiche() { return connecte() ? etat.q : qApercu; }

function majEtat(m) {
  const etaitConnecte = connecte();
  etat = m;
  limites = m.limites || LIMITES_DEFAUT;
  if (connecte() && (!consigneModifiee || !etaitConnecte)) {
    consigne = [...m.q_cible];
    consigneModifiee = false;
  }
  majEtatConnexion();
  majVue();
  majAxes();
  majPince();
  majLecture();
}

function majVue() {
  const q = qAffiche();
  vue.majPose(q, connecte() ? etat.q_cible : consigne);
  const p = pose(q);
  $('#pose').innerHTML =
    `X ${fmt(p.x)} · Y ${fmt(p.y)} · Z ${fmt(p.z)} mm<br>Rx ${fmt(p.rx)} · Ry ${fmt(p.ry)} · Rz ${fmt(p.rz)} °`;
  $('#mouvement').textContent = connecte() && etat.occupe ? 'En mouvement…' : '';
  if (!document.querySelector('#onglet-cartesien').hidden && !cartEnEdition) remplirCartesien();
}

// ---------------------------------------------------------------- axes

const elAxes = [];
function construireAxes() {
  const conteneur = $('#axes');
  for (let i = 0; i < 6; i++) {
    const div = document.createElement('div');
    div.className = 'axe';
    div.innerHTML = `
      <div class="entete-axe"><span>Axe ${i + 1}<small>${NOMS_AXES[i]}</small></span>
        <span><output class="reel" title="Position actuelle"></output><output class="consigne"></output></span></div>
      <button aria-label="Axe ${i + 1} moins">−</button>
      <input type="range" step="0.5" aria-label="Axe ${i + 1}">
      <button aria-label="Axe ${i + 1} plus">+</button>`;
    conteneur.appendChild(div);
    const [moins, plus] = div.querySelectorAll('button');
    const curseur = div.querySelector('input');
    const el = { curseur, reel: div.querySelector('.reel'), consigne: div.querySelector('.consigne'), glisse: false };
    elAxes.push(el);
    curseur.addEventListener('input', () => {
      el.glisse = true;
      consigne[i] = +curseur.value;
      apresModification(false);
    });
    curseur.addEventListener('change', () => { el.glisse = false; apresModification(true); });
    const pas = (s) => {
      consigne[i] = Math.min(limites.max[i], Math.max(limites.min[i], consigne[i] + s * +$('#pas-axe').value));
      apresModification(true);
    };
    moins.onclick = () => pas(-1);
    plus.onclick = () => pas(1);
  }
}

function apresModification(fin) {
  if (!connecte()) {
    qApercu = [...consigne];
    majVue();
    majAxes();
    return;
  }
  consigneModifiee = true;
  if (fin && $('#envoi-direct').checked) envoyerConsigne();
  majAxes();
  vue.majPose(etat.q, consigne);
}

function envoyerConsigne() {
  const duree = parseFloat($('#duree-axes').value);
  envoyer({ type: 'deplacer', q: consigne.map((v) => +v.toFixed(3)), duree: duree > 0 ? duree : null });
  consigneModifiee = false;
}

function majAxes() {
  const q = qAffiche();
  elAxes.forEach((el, i) => {
    el.curseur.min = limites.min[i];
    el.curseur.max = limites.max[i];
    if (!el.glisse) el.curseur.value = consigne[i];
    el.consigne.textContent = `${fmt(consigne[i])}°`;
    const ecart = Math.abs(q[i] - consigne[i]) > 0.05;
    el.reel.textContent = connecte() && ecart ? `${fmt(q[i])}° →` : '';
  });
}

$('#envoyer-axes').onclick = () => {
  if (!connecte()) return toast("Connecte d'abord la carte (ou le simulateur).", true);
  envoyerConsigne();
};
$('#axes-zero').onclick = () => { consigne = [0, 0, 0, 0, 0, 0]; apresModification(true); };
$('#axes-reprendre').onclick = () => { consigne = [...qAffiche()]; consigneModifiee = false; majAxes(); };

// ---------------------------------------------------------------- pince

let pinceGlisse = false;
function majPince() {
  if (!connecte() || pinceGlisse) return;
  $('#pince').value = etat.pince;
  $('#pince-val').textContent = `${Math.round(etat.pince)} %`;
}
$('#pince').addEventListener('input', () => { pinceGlisse = true; $('#pince-val').textContent = `${$('#pince').value} %`; });
$('#pince').addEventListener('change', () => { pinceGlisse = false; reglerPince(+$('#pince').value); });
function reglerPince(v) {
  $('#pince').value = v;
  $('#pince-val').textContent = `${v} %`;
  if (connecte()) envoyer({ type: 'pince', valeur: v });
}
$('#pince-ouvrir').onclick = () => reglerPince(100);
$('#pince-fermer').onclick = () => reglerPince(0);

// ---------------------------------------------------------------- cartésien

const CHAMPS = [['x', 'X', 'mm'], ['y', 'Y', 'mm'], ['z', 'Z', 'mm'], ['rx', 'Rx', '°'], ['ry', 'Ry', '°'], ['rz', 'Rz', '°']];
let cartEnEdition = false;
function construireCartesien() {
  const g = $('#cartesien');
  for (const [cle, nom, unite] of CHAMPS) {
    g.insertAdjacentHTML('beforeend', `
      <span>${nom}</span>
      <button data-cle="${cle}" data-sens="-1" aria-label="${nom} moins">−</button>
      <input type="number" step="any" id="cart-${cle}" aria-label="${nom} (${unite})">
      <button data-cle="${cle}" data-sens="1" aria-label="${nom} plus">+</button>`);
  }
  g.querySelectorAll('button').forEach((b) => {
    b.onclick = () => {
      const cle = b.dataset.cle;
      const rot = cle.startsWith('r');
      const pas = +(rot ? $('#pas-rot').value : $('#pas-lin').value) * +b.dataset.sens;
      const cible = pose(consigne);
      if (rot) {
        // rotation autour de l'axe du repère de base, appliquée à l'orientation actuelle
        const R0 = depuisRPY(cible.rx, cible.ry, cible.rz);
        const ax = { rx: [1, 0, 0], ry: [0, 1, 0], rz: [0, 0, 1] }[cle];
        cible.R = multiplier3(rotationAxe(ax, pas), R0);
      } else cible[cle] += pas;
      allerA(cible);
    };
  });
  g.querySelectorAll('input').forEach((inp) => {
    inp.addEventListener('focus', () => { cartEnEdition = true; });
    inp.addEventListener('blur', () => { cartEnEdition = false; });
    inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') $('#aller-cart').click(); });
  });
}

function rotationAxe([x, y, z], deg) {
  const a = (deg * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a), t = 1 - c;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y,
    t * x * y + s * z, t * y * y + c, t * y * z - s * x,
    t * x * z - s * y, t * y * z + s * x, t * z * z + c];
}
function multiplier3(A, B) {
  const C = new Array(9).fill(0);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) for (let k = 0; k < 3; k++) C[i * 3 + j] += A[i * 3 + k] * B[k * 3 + j];
  return C;
}

function remplirCartesien() {
  const p = pose(consigne);
  for (const [cle] of CHAMPS) $(`#cart-${cle}`).value = p[cle].toFixed(cle.startsWith('r') ? 2 : 1);
}

$('#aller-cart').onclick = () => {
  const cible = Object.fromEntries(CHAMPS.map(([cle]) => [cle, parseFloat($(`#cart-${cle}`).value)]));
  if (Object.values(cible).some(Number.isNaN)) return message('#mgi-message', 'Valeur invalide.', true);
  allerA(cible);
};

function allerA(cible) {
  const orientation = $('#garder-orientation').checked;
  const r = mgi(cible, consigne, limites, { avecOrientation: orientation });
  if (!r.ok) {
    message('#mgi-message', `Pose inatteignable (écart ${fmt(r.erreurPos)} mm${orientation ? `, ${fmt(r.erreurRot)}°` : ''}). Le bras ne bouge pas.`, true);
    return;
  }
  message('#mgi-message', '');
  consigne = r.q;
  apresModification(true);
  remplirCartesien();
}

function message(sel, texte, erreur = false) {
  const el = $(sel);
  el.textContent = texte;
  el.classList.toggle('erreur', erreur);
}

// ---------------------------------------------------------------- trajectoire

let points = chargerBrouillon();

function chargerBrouillon() {
  try { return JSON.parse(localStorage.getItem('mkx3d-trajectoire')) || []; } catch { return []; }
}
function sauverBrouillon() {
  try { localStorage.setItem('mkx3d-trajectoire', JSON.stringify(points)); } catch { /* stockage indisponible */ }
}

function pinceActuelle() { return connecte() ? etat.pince : +$('#pince').value; }

function afficherPoints() {
  const ol = $('#traj-liste');
  ol.innerHTML = '';
  if (!points.length) {
    ol.innerHTML = '<li class="traj-vide" style="display:block">Aucun point. Place le bras puis « Ajouter la position actuelle ».</li>';
    return;
  }
  points.forEach((p, n) => {
    const li = document.createElement('li');
    li.innerHTML = `
      <span class="q">${p.q.map((v) => fmt(v)).join(' · ')}</span>
      <span class="outils">
        <button title="Aller à ce point">➜</button><button title="Remplacer par la position actuelle">⟳</button>
        <button title="Monter">↑</button><button title="Descendre">↓</button><button title="Supprimer">✕</button>
      </span>
      <span class="reglages">
        <label>Pince <input type="number" min="0" max="100" step="1" value="${p.pince ?? ''}" data-champ="pince"> %</label>
        <label>Durée <input type="number" min="0" step="0.5" value="${p.duree ?? ''}" placeholder="auto" data-champ="duree"> s</label>
        <label>Pause <input type="number" min="0" step="0.5" value="${p.pause ?? ''}" placeholder="0" data-champ="pause"> s</label>
      </span>`;
    const [aller, remplacer, haut, bas, suppr] = li.querySelectorAll('.outils button');
    aller.onclick = () => { consigne = [...p.q]; apresModification(true); };
    remplacer.onclick = () => { p.q = [...consigne]; sauverBrouillon(); afficherPoints(); };
    haut.onclick = () => { if (n > 0) { [points[n - 1], points[n]] = [points[n], points[n - 1]]; sauverBrouillon(); afficherPoints(); } };
    bas.onclick = () => { if (n < points.length - 1) { [points[n + 1], points[n]] = [points[n], points[n + 1]]; sauverBrouillon(); afficherPoints(); } };
    suppr.onclick = () => { points.splice(n, 1); sauverBrouillon(); afficherPoints(); };
    li.querySelectorAll('input').forEach((inp) => {
      inp.onchange = () => {
        const v = parseFloat(inp.value);
        p[inp.dataset.champ] = Number.isNaN(v) ? null : v;
        sauverBrouillon();
      };
    });
    ol.appendChild(li);
  });
  majLecture();
}

$('#traj-ajouter').onclick = () => {
  points.push({ q: [...consigne].map((v) => +v.toFixed(3)), pince: Math.round(pinceActuelle()), duree: null, pause: null });
  sauverBrouillon();
  afficherPoints();
};
$('#traj-lire').onclick = () => {
  if (!connecte()) return toast("Connecte d'abord la carte (ou le simulateur).", true);
  envoyer({ type: 'lire', points, boucle: $('#traj-boucle').checked });
};
$('#traj-stop').onclick = () => envoyer({ type: 'arreter_lecture' });
$('#traj-vider').onclick = () => {
  if (points.length && !confirm('Supprimer tous les points de la trajectoire ?')) return;
  points = [];
  sauverBrouillon();
  afficherPoints();
};

function majLecture() {
  const l = etat && etat.lecture;
  $('#traj-lire').disabled = !!l;
  $('#traj-progression').textContent = l ? `Lecture : point ${l.index + 1} / ${l.total}` : '';
  document.querySelectorAll('#traj-liste li').forEach((li, n) => li.classList.toggle('actif', !!l && l.index === n));
}

async function listerFichiers() {
  try {
    const noms = await (await fetch('api/trajectoires')).json();
    const ul = $('#traj-fichiers');
    ul.innerHTML = noms.length ? '' : '<li class="traj-vide">Aucune trajectoire enregistrée.</li>';
    for (const nom of noms) {
      const li = document.createElement('li');
      li.innerHTML = '<span></span><button class="secondaire">Charger</button><button class="discret" title="Supprimer">✕</button>';
      li.querySelector('span').textContent = nom;
      const [charger, suppr] = li.querySelectorAll('button');
      charger.onclick = async () => {
        const d = await (await fetch(`api/trajectoires/${encodeURIComponent(nom)}`)).json();
        points = d.points || [];
        $('#traj-nom').value = nom;
        sauverBrouillon();
        afficherPoints();
      };
      suppr.onclick = async () => {
        if (!confirm(`Supprimer « ${nom} » ?`)) return;
        await fetch(`api/trajectoires/${encodeURIComponent(nom)}`, { method: 'DELETE' });
        listerFichiers();
      };
      ul.appendChild(li);
    }
  } catch { /* serveur absent */ }
}

$('#traj-enregistrer').onclick = async () => {
  const nom = $('#traj-nom').value.trim();
  if (!nom) return toast('Donne un nom à la trajectoire.', true);
  const r = await fetch(`api/trajectoires/${encodeURIComponent(nom)}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ points }),
  });
  if (r.ok) { toast('Trajectoire enregistrée.'); listerFichiers(); } else toast('Enregistrement impossible.', true);
};

$('#traj-exporter').onclick = () => {
  const lien = document.createElement('a');
  lien.href = URL.createObjectURL(new Blob([JSON.stringify({ points }, null, 1)], { type: 'application/json' }));
  lien.download = `${$('#traj-nom').value.trim() || 'trajectoire'}.json`;
  lien.click();
  URL.revokeObjectURL(lien.href);
};

$('#traj-importer').onchange = async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const texte = await f.text();
  try {
    points = f.name.endsWith('.csv') ? lireCSV(texte) : JSON.parse(texte).points;
    sauverBrouillon();
    afficherPoints();
    toast(`${points.length} points importés.`);
  } catch (err) {
    toast(`Fichier illisible : ${err.message}`, true);
  }
  e.target.value = '';
};

// Format CSV du jumeau numérique : label;q1;...;q6;ot;x;y;z;rx;ry;rz;prop;mode (virgule décimale)
function lireCSV(texte) {
  const lignes = texte.trim().split(/\r?\n/).slice(1);
  const nombre = (s) => parseFloat(String(s).replace(',', '.'));
  return lignes.filter((l) => l.trim()).map((l) => {
    const c = l.split(';');
    const q = c.slice(1, 7).map(nombre);
    if (q.some(Number.isNaN)) throw new Error('angles manquants');
    const ot = nombre(c[7]);
    return { q, pince: Number.isNaN(ot) ? null : ot, duree: null, pause: null };
  });
}

// ---------------------------------------------------------------- calibration

function construireCalibration() {
  const g = $('#calib-axes');
  for (let i = 0; i < 6; i++) {
    g.insertAdjacentHTML('beforeend', `<label>Axe ${i + 1} (°)<input type="number" step="0.1" value="0" id="calib-${i}"></label>`);
  }
}
function lireCalibration() { return [...Array(6)].map((_, i) => parseFloat($(`#calib-${i}`).value) || 0); }
function remplirCalibration(q) { q.forEach((v, i) => { $(`#calib-${i}`).value = v; }); }

$('#calib-appliquer').onclick = () => {
  if (!connecte()) return toast("Connecte d'abord la carte.", true);
  envoyer({ type: 'definir_position', q: lireCalibration() });
};
$('#calib-remplir-derniere').onclick = () => {
  if (etat && etat.derniere_connue) remplirCalibration(etat.derniere_connue);
  else toast('Aucune position mémorisée.', true);
};
$('#calib-zero').onclick = () => envoyer({ type: 'definir_position', q: [0, 0, 0, 0, 0, 0] });
$('#calib-derniere').onclick = () => envoyer({ type: 'definir_position', q: etat.derniere_connue });
$('#calib-ouvrir').onclick = () => ouvrirOnglet('calibration');

// ---------------------------------------------------------------- journal

function ajouterJournal(m) {
  const j = $('#journal');
  const d = document.createElement('div');
  d.className = m.sens;
  const fleche = { tx: '→', rx: '←', erreur: '!', info: '·' }[m.sens] || '';
  d.textContent = `${m.t} ${fleche} ${m.texte}`;
  j.appendChild(d);
  while (j.childElementCount > 300) j.firstChild.remove();
  j.parentElement.scrollTop = j.parentElement.scrollHeight;
  if (m.sens === 'erreur') toast(m.texte, true);
}

// ---------------------------------------------------------------- onglets & divers

function ouvrirOnglet(nom) {
  document.querySelectorAll('.onglets button').forEach((b) => b.setAttribute('aria-selected', b.dataset.onglet === nom));
  document.querySelectorAll('.onglet').forEach((s) => { s.hidden = s.id !== `onglet-${nom}`; });
  if (nom === 'cartesien') remplirCartesien();
  if (nom === 'trajectoire') listerFichiers();
  try { localStorage.setItem('mkx3d-onglet', nom); } catch { /* ignoré */ }
}
document.querySelectorAll('.onglets button').forEach((b) => { b.onclick = () => ouvrirOnglet(b.dataset.onglet); });

let minuteurToast;
function toast(texte, erreur = false) {
  const t = $('#toast');
  t.textContent = texte;
  t.classList.toggle('erreur', erreur);
  t.hidden = false;
  clearTimeout(minuteurToast);
  minuteurToast = setTimeout(() => { t.hidden = true; }, erreur ? 6000 : 2500);
}

construireAxes();
construireCartesien();
construireCalibration();
afficherPoints();
majAxes();
majVue();
majEtatConnexion();
try { ouvrirOnglet(localStorage.getItem('mkx3d-onglet') || 'articulaire'); } catch { ouvrirOnglet('articulaire'); }
connecterWS();
