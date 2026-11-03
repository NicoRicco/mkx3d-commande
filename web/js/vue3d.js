// Vue 3D : modèle Blender exporté (web/modele/bras.glb) ou, à défaut, bras simplifié
// construit à partir du modèle DH. Repère Z vers le haut, comme dans Blender.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mgd, reperes } from './cinematique.js';

// Os de l'armature Blender et axe de rotation de chacun (repris de bras.py)
const OS = ['Segment 1', 'Segment 2', 'Segment 3', 'Segment 4', 'Segment 5', 'Segment 6'];
const AXES_OS = [[0, 1, 0], [-1, 0, 0], [-1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, 1, 0]];

function matrice(T) {
  const m = new THREE.Matrix4();
  m.set(...T);
  return m;
}

export class Vue3D {
  constructor(conteneur) {
    this.conteneur = conteneur;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(40, 1, 0.01, 20);
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(1.1, -1.3, 0.9);
    this.rendu = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    this.rendu.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    conteneur.appendChild(this.rendu.domElement);
    this.controles = new OrbitControls(this.camera, this.rendu.domElement);
    this.controles.target.set(0, 0, 0.35);
    this.controles.enableDamping = true;

    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x445566, 2.2));
    const soleil = new THREE.DirectionalLight(0xffffff, 2.0);
    soleil.position.set(1, -1.5, 2);
    this.scene.add(soleil);

    const grille = new THREE.GridHelper(1.6, 16, 0x7a8699, 0x7a8699);
    grille.rotation.x = Math.PI / 2;
    grille.material.transparent = true;
    grille.material.opacity = 0.35;
    this.scene.add(grille);
    this.grille = grille;
    this.scene.add(new THREE.AxesHelper(0.15));

    // Repère de la cible (pose demandée) et de l'outil (pose estimée)
    this.reperesCible = new THREE.AxesHelper(0.08);
    this.reperesCible.matrixAutoUpdate = false;
    this.scene.add(this.reperesCible);
    this.pointCible = new THREE.Mesh(
      new THREE.SphereGeometry(0.012, 16, 12),
      new THREE.MeshBasicMaterial({ color: 0xff9f1c, transparent: true, opacity: 0.85 }));
    this.scene.add(this.pointCible);

    this.os = null;
    this.reposOs = null;
    this.simplifie = null;
    this.q = [0, 0, 0, 0, 0, 0];

    new ResizeObserver(() => this.redimensionner()).observe(conteneur);
    this.redimensionner();
    this.chargerModele();
    const boucle = () => {
      requestAnimationFrame(boucle);
      this.controles.update();
      this.rendu.render(this.scene, this.camera);
    };
    boucle();
  }

  redimensionner() {
    const { clientWidth: l, clientHeight: h } = this.conteneur;
    if (!l || !h) return;
    this.rendu.setSize(l, h);
    this.camera.aspect = l / h;
    this.camera.updateProjectionMatrix();
  }

  chargerModele() {
    new GLTFLoader().load('modele/bras.glb', (gltf) => {
      const racine = gltf.scene;
      const os = OS.map((nom) => racine.getObjectByName(nom.replace(/ /g, '_')) || racine.getObjectByName(nom));
      if (os.some((o) => !o)) {
        console.warn('Os manquants dans bras.glb, bras simplifié conservé.');
        return;
      }
      this.os = os;
      this.reposOs = os.map((o) => o.quaternion.clone());
      this.scene.add(racine);
      // La table descend sous le socle : la grille passe au niveau du sol
      const boite = new THREE.Box3().setFromObject(racine);
      this.grille.position.z = boite.min.z;
      this.camera.position.set(1.3, -1.6, 0.9);
      this.controles.target.set(0, 0, 0.25);
      if (this.simplifie) this.simplifie.visible = false;
      this.modeleCharge = true;
      this.majPose(this.q);
      this.conteneur.dispatchEvent(new CustomEvent('modele', { detail: 'blender' }));
    }, undefined, () => {
      this.conteneur.dispatchEvent(new CustomEvent('modele', { detail: 'simplifie' }));
    });
    this.construireSimplifie();
  }

  construireSimplifie() {
    const groupe = new THREE.Group();
    const matSeg = new THREE.MeshStandardMaterial({ color: 0xd8dde6, roughness: 0.5, metalness: 0.1 });
    const matArt = new THREE.MeshStandardMaterial({ color: 0x2f6fde, roughness: 0.4 });
    this.segments = [];
    this.articulations = [];
    for (let i = 0; i < 7; i++) {
      const seg = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 1, 20), matSeg);
      groupe.add(seg);
      this.segments.push(seg);
    }
    for (let i = 0; i < 6; i++) {
      const art = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.07, 24), matArt);
      art.matrixAutoUpdate = false;
      groupe.add(art);
      this.articulations.push(art);
    }
    const socle = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.1, 0.04, 32), matArt);
    socle.rotation.x = Math.PI / 2;
    socle.position.z = 0.02;
    groupe.add(socle);
    this.simplifie = groupe;
    this.scene.add(groupe);
  }

  majPose(q, qCible = null) {
    this.q = q;
    const R = reperes(q);
    const outil = matrice(R[6]);
    if (this.os) {
      for (let i = 0; i < 6; i++) {
        const delta = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(...AXES_OS[i]), (q[i] * Math.PI) / 180);
        this.os[i].quaternion.copy(this.reposOs[i]).multiply(delta);
      }
    }
    if (this.simplifie && this.simplifie.visible) {
      const origines = R.map((T) => new THREE.Vector3(T[3], T[7], T[11]));
      // le repère 5 coïncide avec le 4 : on trace les segments entre origines distinctes
      for (let i = 0; i < 6; i++) {
        const m = matrice(R[i + 1]);
        // cylindre orienté selon l'axe z local de l'articulation
        m.multiply(new THREE.Matrix4().makeRotationX(Math.PI / 2));
        this.articulations[i].matrix.copy(m);
      }
      const points = [new THREE.Vector3(0, 0, 0), ...origines.slice(1)];
      for (let i = 0; i < this.segments.length; i++) {
        const a = points[i], b = points[i + 1];
        const seg = this.segments[i];
        if (!b || a.distanceTo(b) < 1e-4) { seg.visible = false; continue; }
        seg.visible = true;
        seg.position.copy(a).add(b).multiplyScalar(0.5);
        seg.scale.set(1, a.distanceTo(b), 1);
        seg.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
      }
    }
    const qc = qCible || q;
    const Tc = matrice(mgd(qc));
    this.reperesCible.matrix.copy(Tc);
    this.pointCible.position.setFromMatrixPosition(Tc);
    const enMouvement = qCible && qCible.some((v, i) => Math.abs(v - q[i]) > 0.05);
    this.pointCible.visible = this.reperesCible.visible = !!enMouvement || !this.os;
    return outil;
  }
}
