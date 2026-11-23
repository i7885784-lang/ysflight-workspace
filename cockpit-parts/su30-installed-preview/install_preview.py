"""Convert the trial GLB to a separate YSFlight cockpit DNM.

Run with Blender in background mode, passing source DNM, GLB and destination
DNM after --. The mesh faces carry flat colors, as in the classic aircraft.
"""
from pathlib import Path
import sys
import bpy
from mathutils import Vector


def panel_without_left_placeholder(lines):
    vertices = []
    kept = [lines[0]]
    faces = []
    removed = 0
    cursor = 1
    while cursor < len(lines) - 1:
        line = lines[cursor]
        if line == "F":
            end = lines.index("E", cursor)
            face = lines[cursor:end + 1]
            indices = next(s[2:].split() for s in face if s.startswith("V "))
            points = [vertices[int(index)] for index in indices]
            old_colors = {"C 15 22 25", "C 62 106 87"}
            bounded = all(-.316 <= x <= -.064 and .764 <= y <= .956
                          and 6.060 <= z <= 6.077 for x, y, z in points)
            if bounded and old_colors.intersection(face):
                removed += 1
            else:
                # The exposed face of the existing instrument board directly
                # behind the units. The dark glare shield is a different surface.
                if "C 30 34 37" in face and all(
                    abs(z - 6.085) < .00001 and .684 <= y <= .993
                    for x, y, z in points
                ):
                    face[face.index("C 30 34 37")] = "C 79 108 119"
                faces.extend(face)
            cursor = end + 1
        else:
            if line.startswith("V "):
                vertices.append(tuple(float(s) for s in line.split()[1:4]))
                kept.append(line)
            else:
                assert not faces, line
                kept.append(line)
            cursor += 1
    assert removed > 0, "Expected left placeholder faces"
    print(f"Removed {removed} placeholder faces")
    return kept + faces + ["E"]


def rgb(material):
    shader = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    linear = shader.inputs["Base Color"].default_value[:3]
    return tuple(round(255 * (12.92 * c if c < .0031308 else 1.055 * c ** (1 / 2.4) - .055))
                 for c in linear)


def surface(objects):
    vertices = []
    faces = []
    for obj in objects:
        offset = len(vertices)
        points = [obj.matrix_world @ v.co for v in obj.data.vertices]
        points = [Vector((-.190 + p.x * .9, .874 + p.y * .9, 6.041 - p.z * .9))
                  for p in points]
        vertices.extend(points)
        colors = [rgb(m) for m in obj.data.materials]
        for face in obj.data.polygons:
            ids = list(reversed(face.vertices))
            a, b, c = (points[i] for i in ids[:3])
            normal = (b - a).cross(c - a)
            if normal.length_squared < 1e-24:
                continue
            faces.extend(["F", "C %d %d %d" % colors[face.material_index],
                          "N %.7f %.7f %.7f" % tuple(normal.normalized()),
                          "V " + " ".join(str(i + offset) for i in ids), "E"])
    return ["SURF"] + ["V %.7f %.7f %.7f" % tuple(p) for p in vertices] + faces + ["E"]


def install(source, model, destination):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    buttons = sorted((obj for obj in objects if obj.get("control_id")), key=lambda obj: obj.name)
    assert len(buttons) == 24
    display = next(obj for obj in objects if obj.name == "Screen surface")
    moving = set(buttons + [display])
    groups = [("MFD_Left_Frame", [obj for obj in objects
                                  if obj not in moving and obj.parent not in moving]),
              ("MFD_Left_Glass", [display])]
    groups.extend((obj.name, [obj, *obj.children]) for obj in buttons)
    lines = source.read_text().splitlines()
    start = next(i for i, s in enumerate(lines) if s.startswith("PCK Su30Interior.srf "))
    end = start + 1 + int(lines[start].split()[-1])
    panel = panel_without_left_placeholder(lines[start + 1:end])
    result = lines[:start] + [f"PCK Su30Interior.srf {len(panel)}"] + panel
    nodes = []
    for name, group in groups:
        mesh = surface(group)
        result += [f"PCK {name}.srf {len(mesh)}"] + mesh
        nodes += [f'SRF "{name}"', f"FIL {name}.srf", "CLA 99", "NST 1",
                  "STA 0 0 0 0 0 0 1", "POS 0 0 0 0 0 0 1", "CNT 0 0 0",
                  "PAX 1 0 0", "REL DEP", "NCH 0", "END"]
    assert lines[-1] == "END"
    result += lines[end:-1] + nodes + ["END"]
    destination.write_text("\n".join(result) + "\n")


if __name__ == "__main__":
    install(*map(Path, sys.argv[sys.argv.index("--") + 1:]))
