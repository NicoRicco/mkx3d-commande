// Cinématique du bras MKX3D : modèle Denavit-Hartenberg modifié (Craig),
// repris de jumeau-numerique/rtb/mkx3d.py. Longueurs en mètres, angles en degrés.

const DEG = Math.PI / 180;

export const DH = [
  { alpha: 0, a: 0, d: 0.22075, offset: -Math.PI / 2 },
  { alpha: Math.PI / 2, a: 0, d: 0, offset: Math.PI / 2 },
  { alpha: 0, a: 0.22152, d: 0, offset: Math.PI / 2 },
  { alpha: Math.PI / 2, a: 0, d: 0.228, offset: 0 },
  { alpha: -Math.PI / 2, a: 0, d: 0, offset: 0 },
  { alpha: Math.PI / 2, a: 0, d: 0.203, offset: Math.PI },
];

// Matrices 4x4 stockées en tableau de 16 (ligne par ligne)
function mul(A, B) {
  const C = new Array(16).fill(0);
  for (let i = 0; i < 4; i++)
    for (let j = 0; j < 4; j++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += A[i * 4 + k] * B[k * 4 + j];
      C[i * 4 + j] = s;
    }
  return C;
}

function lienMDH(p, theta) {
  const ca = Math.cos(p.alpha), sa = Math.sin(p.alpha);
  const ct = Math.cos(theta), st = Math.sin(theta);
  return [
    ct, -st, 0, p.a,
    st * ca, ct * ca, -sa, -sa * p.d,
    st * sa, ct * sa, ca, ca * p.d,
    0, 0, 0, 1,
  ];
}

const IDENTITE = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

/** Repères de chaque articulation (base incluse), q en degrés. */
export function reperes(q) {
  let T = IDENTITE;
  const liste = [T];
  for (let i = 0; i < 6; i++) {
    T = mul(T, lienMDH(DH[i], q[i] * DEG + DH[i].offset));
    liste.push(T);
  }
  return liste;
}

// Repère outil : tourné de 90° autour de z par rapport au dernier repère DH,
// pour afficher les mêmes orientations que le jumeau numérique (objet Rp).
const OUTIL = [0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

export function mgd(q) {
  const r = reperes(q);
  return mul(r[r.length - 1], OUTIL);
}

/** Rotation -> angles RPY (Rx, Ry, Rz) en degrés, convention ZYX comme RTB tr2rpy. */
export function versRPY(T) {
  const r11 = T[0], r21 = T[4], r31 = T[8], r32 = T[9], r33 = T[10];
  let rx, ry, rz;
  if (Math.abs(Math.abs(r31) - 1) < 1e-9) {
    rz = 0;
    ry = -Math.sign(r31) * Math.PI / 2;
    rx = Math.atan2(-Math.sign(r31) * T[1], T[5]);
  } else {
    ry = -Math.asin(r31);
    rx = Math.atan2(r32, r33);
    rz = Math.atan2(r21, r11);
  }
  return [rx / DEG, ry / DEG, rz / DEG];
}

export function depuisRPY(rx, ry, rz) {
  [rx, ry, rz] = [rx * DEG, ry * DEG, rz * DEG];
  const cx = Math.cos(rx), sx = Math.sin(rx), cy = Math.cos(ry), sy = Math.sin(ry), cz = Math.cos(rz), sz = Math.sin(rz);
  // R = Rz * Ry * Rx
  return [
    cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx,
    sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx,
    -sy, cy * sx, cy * cx,
  ];
}

/** Pose sous forme {x,y,z (mm), rx,ry,rz (°)}. */
export function pose(q) {
  const T = mgd(q);
  const [rx, ry, rz] = versRPY(T);
  return { x: T[3] * 1000, y: T[7] * 1000, z: T[11] * 1000, rx, ry, rz };
}

function rot3(T) {
  return [T[0], T[1], T[2], T[4], T[5], T[6], T[8], T[9], T[10]];
}

// Erreur d'orientation (vecteur rotation de R_courant vers R_cible), dans le repère de base
function erreurRotation(Rc, Rd) {
  // Re = Rd * Rc^T
  const Re = new Array(9).fill(0);
  for (let i = 0; i < 3; i++)
    for (let j = 0; j < 3; j++)
      for (let k = 0; k < 3; k++) Re[i * 3 + j] += Rd[i * 3 + k] * Rc[j * 3 + k];
  const c = Math.min(1, Math.max(-1, (Re[0] + Re[4] + Re[8] - 1) / 2));
  const angle = Math.acos(c);
  const v = [Re[7] - Re[5], Re[2] - Re[6], Re[3] - Re[1]];
  if (angle < 1e-6) return [v[0] / 2, v[1] / 2, v[2] / 2];
  const s = Math.sin(angle);
  if (s < 1e-6) {
    // angle proche de 180° : axe depuis la diagonale
    const ax = [Math.sqrt(Math.max(0, (Re[0] + 1) / 2)), Math.sqrt(Math.max(0, (Re[4] + 1) / 2)), Math.sqrt(Math.max(0, (Re[8] + 1) / 2))];
    return ax.map((a) => a * angle);
  }
  const f = angle / (2 * s);
  return v.map((a) => a * f);
}

function resoudre(A, b) {
  // Élimination de Gauss avec pivot partiel, A n x n
  const n = b.length;
  const M = A.map((ligne, i) => [...ligne, b[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    const piv = M[c][c] || 1e-12;
    for (let r = 0; r < n; r++) {
      if (r === c) continue;
      const f = M[r][c] / piv;
      for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k];
    }
  }
  return M.map((ligne, i) => ligne[n] / (ligne[i] || 1e-12));
}

/**
 * Modèle géométrique inverse numérique (moindres carrés amortis).
 * cible : {x,y,z en mm, R (3x3) ou rx,ry,rz en °}. Part de qDepart pour rester proche.
 * Renvoie { q, ok, erreurPos (mm), erreurRot (°) }.
 */
export function mgi(cible, qDepart, limites, options = {}) {
  const { iterations = 200, avecOrientation = true } = options;
  const pd = [cible.x / 1000, cible.y / 1000, cible.z / 1000];
  const Rd = cible.R || depuisRPY(cible.rx, cible.ry, cible.rz);
  let q = [...qDepart];
  const lambda = 0.02;
  const poidsRot = avecOrientation ? 0.3 : 0; // 1 rad d'orientation ~ 30 cm d'erreur

  const erreur = (qq) => {
    const T = mgd(qq);
    const ep = [pd[0] - T[3], pd[1] - T[7], pd[2] - T[11]];
    const er = erreurRotation(rot3(T), Rd).map((v) => v * poidsRot);
    return [...ep, ...er];
  };

  for (let it = 0; it < iterations; it++) {
    const e = erreur(q);
    const norme = Math.hypot(...e);
    if (norme < 1e-5) break;
    // Jacobienne numérique (6 x 6)
    const J = Array.from({ length: 6 }, () => new Array(6).fill(0));
    const h = 1e-3;
    for (let j = 0; j < 6; j++) {
      const qp = [...q];
      qp[j] += h;
      const ep = erreur(qp);
      for (let i = 0; i < 6; i++) J[i][j] = (e[i] - ep[i]) / (h * DEG); // par radian
    }
    // dq = J^T (J J^T + λ² I)^-1 e
    const JJt = Array.from({ length: 6 }, (_, i) =>
      Array.from({ length: 6 }, (_, k) => {
        let s = 0;
        for (let j = 0; j < 6; j++) s += J[i][j] * J[k][j];
        return s + (i === k ? lambda * lambda : 0);
      }));
    const y = resoudre(JJt, e);
    let pas = 0;
    const dq = new Array(6).fill(0);
    for (let j = 0; j < 6; j++) {
      for (let i = 0; i < 6; i++) dq[j] += J[i][j] * y[i];
      dq[j] /= DEG; // radians -> degrés
      pas = Math.max(pas, Math.abs(dq[j]));
    }
    const echelle = pas > 5 ? 5 / pas : 1; // au plus 5° par itération
    for (let j = 0; j < 6; j++) {
      q[j] += dq[j] * echelle;
      if (limites) q[j] = Math.min(limites.max[j], Math.max(limites.min[j], q[j]));
    }
  }
  const T = mgd(q);
  const erreurPos = Math.hypot(pd[0] - T[3], pd[1] - T[7], pd[2] - T[11]) * 1000;
  const erreurRot = (Math.hypot(...erreurRotation(rot3(T), Rd)) * 180) / Math.PI;
  return { q, ok: erreurPos < 1 && (!avecOrientation || erreurRot < 1), erreurPos, erreurRot };
}

export { rot3 };
