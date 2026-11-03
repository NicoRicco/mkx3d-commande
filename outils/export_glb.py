"""Export du bras MKX3D (fichier Blender du jumeau numérique) vers web/modele/bras.glb.

Utilisation :
    blender -b bras_mkx3d-9.blend --python outils/export_glb.py
ou, avec le module Python bpy :
    python outils/export_glb.py chemin/vers/bras_mkx3d-9.blend

Le script garde l'armature, les pièces rattachées à chaque os et le socle,
supprime tout le reste (interface du jumeau, repères, grilles...), simplifie
les maillages très détaillés puis exporte en glTF binaire (axe Z vers le haut,
comme dans Blender).
"""

import sys
from pathlib import Path

import bpy

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "web" / "modele" / "bras.glb"

OS_PIECES = ["Segment 1", "Segment 2", "Segment 3", "Segment 4", "Segment 5", "Segment 6", "Pince"]
SOCLE = ["Courroie S0", "Moteur S0", "Moteur support S0", "Plateau axe", "Plateau corps", "Poulie S0",
         "Table", "ARU", "Interrupteur"]
SOMMETS_MAX = 3000  # au-delà, le maillage est simplifié


def couleur_materiau(mat, objet):
    """Couleur affichée par UPBGE pour ce matériau sur cet objet."""
    couleur = tuple(mat.diffuse_color)
    arbre = mat.node_tree
    if arbre:
        noeuds = [n for n in arbre.nodes if n.type == "BSDF_DIFFUSE"]
        if noeuds:
            entree = noeuds[0].inputs["Color"]
            if entree.is_linked:
                source = entree.links[0].from_node
                if source.type == "RGB":
                    couleur = tuple(source.outputs[0].default_value)
                elif source.type == "OBJECT_INFO":
                    couleur = tuple(objet.color)
                else:
                    rgb = [n for n in arbre.nodes if n.type == "RGB"]
                    if any(n.type == "OBJECT_INFO" for n in arbre.nodes) and tuple(objet.color) != (1, 1, 1, 1):
                        couleur = tuple(objet.color)
                    elif rgb:
                        couleur = tuple(rgb[0].outputs[0].default_value)
            else:
                couleur = tuple(entree.default_value)
    return tuple(round(c, 3) for c in couleur[:3]) + (1.0,)


def materiau_simple(nom, couleur):
    mat = bpy.data.materials.new(f"{nom} web")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = couleur
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    fichiers = [a for a in args if a.endswith(".blend")]
    if fichiers:
        bpy.ops.wm.open_mainfile(filepath=fichiers[0])

    objets = bpy.data.objects
    armature = objets["Armature"]
    garder = {armature}
    for nom in OS_PIECES:
        vide = objets[nom]
        garder.add(vide)
        garder.update(vide.children_recursive)
        # L'objet vide porte le même nom que l'os : on le renomme pour que
        # l'interface web trouve l'os sans ambiguïté.
        vide.name = f"Pieces {nom}"
    for nom in SOCLE:
        if nom in objets:
            garder.add(objets[nom])
    garder = {o for o in garder if o.type in ("MESH", "EMPTY", "ARMATURE")}

    # Le parent de l'armature (« System ») disparaît : on fige sa position.
    for o in list(garder):
        if o.parent and o.parent not in garder:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw

    for o in list(objets):
        if o not in garder:
            objets.remove(o, do_unlink=True)

    scene = bpy.context.scene
    for o in garder:
        if o.name not in scene.collection.objects and not o.users_collection:
            scene.collection.objects.link(o)
        o.hide_set(False)
        o.hide_viewport = False
        o.hide_render = False

    # Pose de repos : tous les angles à 0
    for pb in armature.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)

    # Simplification des maillages lourds
    vus = set()
    for o in garder:
        if o.type != "MESH" or o.data in vus:
            continue
        vus.add(o.data)
        n = len(o.data.vertices)
        if n > SOMMETS_MAX:
            m = o.modifiers.new("simplifier", "DECIMATE")
            m.ratio = max(0.08, SOMMETS_MAX / n)

    # Les matériaux UPBGE (nœud Diffuse + RGB, ou couleur d'objet) ne passent pas
    # en glTF : on les remplace par des matériaux standards de même couleur.
    cache = {}
    for o in garder:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if slot.material:
                couleur = couleur_materiau(slot.material, o)
                cle = (slot.material.name, couleur)
                if cle not in cache:
                    cache[cle] = materiau_simple(slot.material.name, couleur)
                slot.link = "OBJECT"
                slot.material = cache[cle]

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(SORTIE),
        export_format="GLB",
        export_yup=False,
        export_apply=True,
        export_animations=False,
        export_skins=False,
        export_cameras=False,
        export_lights=False,
        export_extras=False,
    )
    print(f"Modèle exporté : {SORTIE} ({SORTIE.stat().st_size / 1e6:.1f} Mo)")


main()
