"""Fit three displays and their shared housing to the front cockpit DNM.

Run with Blender in background mode, passing source DNM, GLB and destination
DNM after --. The mesh faces carry flat colors, as in the classic aircraft.
"""
from pathlib import Path
from math import cos, pi, sin
import sys
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


DISPLAY_POSITIONS = (
    ("Left", -.235, .874, 6.041, .9),
    ("Center", -.067, .874, 6.041, .9),
    ("Right", .242, .874, 6.041, .9),
)


def panel_without_placeholders(lines):
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
            bounded = all(.064 <= abs(x) <= .316 and .764 <= y <= .956
                          and 6.060 <= z <= 6.077 for x, y, z in points)
            if bounded and old_colors.intersection(face):
                removed += 1
            else:
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
    assert removed == 48, f"Expected two placeholder blocks, found {removed} faces"
    print(f"Removed {removed} placeholder faces")
    return kept + faces + ["E"]


def rgb(material):
    shader = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    linear = shader.inputs["Base Color"].default_value[:3]
    return tuple(round(255 * (12.92 * c if c < .0031308 else 1.055 * c ** (1 / 2.4) - .055))
                 for c in linear)


def surface(objects, position):
    vertices = []
    faces = []
    _, x, y, z, scale = position
    for obj in objects:
        offset = len(vertices)
        points = [obj.matrix_world @ v.co for v in obj.data.vertices]
        points = [Vector((x + p.x * scale, y + p.y * scale, z - p.z * scale))
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


def housing_surface():
    """Closed, tapered instrument housing kept within the original board."""
    vertices = []
    faces = []

    def extrude(outline, near, far, front, side):
        offset = len(vertices)
        count = len(outline)
        vertices.extend(Vector((x, y, z)) for z in (near, far) for x, y in outline)
        triangles = tessellate_polygon([[Vector((x, y, 0)) for x, y in outline]])
        orders = [(list(reversed(triangle)), front) for triangle in triangles]
        orders.extend(([i + count for i in triangle], side) for triangle in triangles)
        for current in range(count):
            following = (current + 1) % count
            orders.append(([current, following, following + count, current + count], side))
        for order, color in orders:
            ids = [offset + i for i in order]
            a, b, c = (vertices[i] for i in ids[:3])
            normal = (b - a).cross(c - a).normalized()
            faces.extend(["F", "C %d %d %d" % color,
                          "N %.7f %.7f %.7f" % tuple(normal),
                          "V " + " ".join(map(str, ids)), "E"])

    outline = [(-.278, .706), (.284, .706), (.329, .751), (.337, .936),
               (.321, .984), (-.321, .984), (-.337, .936), (-.329, .751)]
    extrude(outline, 6.066, 6.096, (88, 121, 132), (43, 62, 72))
    for _, x, y, _, _ in DISPLAY_POSITIONS:
        # The raised pad bridges the display mounting tabs to the casing.
        pad = [(x-.082, y-.080), (x+.082, y-.080), (x+.082, y+.080), (x-.082, y+.080)]
        extrude(pad, 6.045, 6.069, (42, 53, 59), (35, 45, 51))
        for tab_y in (y-.084, y+.084):
            for tab_x in (x-.060, x+.060):
                boss = [(tab_x-.011, tab_y-.010), (tab_x+.011, tab_y-.010),
                        (tab_x+.011, tab_y+.010), (tab_x-.011, tab_y+.010)]
                extrude(boss, 6.046, 6.069, (57, 70, 78), (39, 53, 62))
    return ["SURF"] + ["V %.7f %.7f %.7f" % tuple(p) for p in vertices] + faces + ["E"]


def standby_instrument(x, y, attitude, pointer_angle):
    """Decorative standby gauge with separate colored dial surfaces."""
    vertices = []
    faces = []

    def face(points, depth, color):
        offset = len(vertices)
        vertices.extend((a, b, depth) for a, b in reversed(points))
        ids = range(offset, len(vertices))
        faces.extend(["F", "C %d %d %d" % color, "N 0 0 -1",
                      "V " + " ".join(map(str, ids)), "E"])

    def radial(distance, angle):
        return x + distance * cos(angle), y + distance * sin(angle)

    angles = [2 * pi * i / 32 for i in range(32)]
    outer = [radial(.0245, angle) for angle in angles]
    inner = [radial(.0205, angle) for angle in angles]
    face(outer, 6.060, (19, 24, 27))
    for i in range(32):
        j = (i + 1) % 32
        face([outer[i], outer[j], inner[j], inner[i]], 6.057, (51, 61, 65))
    if attitude:
        face([radial(.0195, angle) for angle in angles[:17]], 6.056, (77, 145, 178))
        face([radial(.0195, angle) for angle in angles[16:] + angles[:1]],
             6.056, (134, 81, 48))
    else:
        face(inner, 6.056, (16, 20, 23))
    for angle in angles[::2]:
        face([radial(.017, angle-.026), radial(.019, angle-.026),
              radial(.019, angle+.026), radial(.017, angle+.026)],
             6.055, (177, 173, 153))
    if attitude:
        face([(x-.012, y-.0008), (x+.012, y-.0008),
              (x+.012, y+.0008), (x-.012, y+.0008)], 6.054, (221, 197, 133))
    else:
        face([radial(.002, pointer_angle+pi/2), radial(.014, pointer_angle),
              radial(.002, pointer_angle-pi/2), radial(.004, pointer_angle+pi)],
             6.054, (218, 212, 186))
    return ["SURF"] + ["V %.7f %.7f %.7f" % p for p in vertices] + faces + ["E"]


def install(source, model, destination):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    buttons = sorted((obj for obj in objects if obj.get("control_id")), key=lambda obj: obj.name)
    assert len(buttons) == 24
    display = next(obj for obj in objects if obj.name == "Screen surface")
    moving = set(buttons + [display])
    frame = [obj for obj in objects if obj not in moving and obj.parent not in moving]
    lines = source.read_text().splitlines()
    start = next(i for i, s in enumerate(lines) if s.startswith("PCK Su30Interior.srf "))
    end = start + 1 + int(lines[start].split()[-1])
    panel = panel_without_placeholders(lines[start + 1:end])
    result = lines[:start] + [f"PCK Su30Interior.srf {len(panel)}"] + panel
    nodes = []
    parts = [("Pilot_Display_Housing", housing_surface())]
    for row, y in enumerate((.929, .874, .819)):
        for column, x in enumerate((.050, .111)):
            parts.append((f"Pilot_Standby_{row+1}_{column+1}",
                          standby_instrument(x, y, row == 0 and column == 1,
                                             .8 + row * .42 + column * .6)))
    for position in DISPLAY_POSITIONS:
        station = position[0]
        groups = [("Frame", frame), ("Glass", [display])]
        groups.extend((obj.name, [obj, *obj.children]) for obj in buttons)
        parts.extend((f"MFD_{station}_{name}", surface(group, position)) for name, group in groups)
    for name, mesh in parts:
        result += [f"PCK {name}.srf {len(mesh)}"] + mesh
        nodes += [f'SRF "{name}"', f"FIL {name}.srf", "CLA 99", "NST 1",
                  "STA 0 0 0 0 0 0 1", "POS 0 0 0 0 0 0 1", "CNT 0 0 0",
                  "PAX 1 0 0", "REL DEP", "NCH 0", "END"]
    assert lines[-1] == "END"
    result += lines[end:-1] + nodes + ["END"]
    destination.write_text("\n".join(result) + "\n")


if __name__ == "__main__":
    install(*map(Path, sys.argv[sys.argv.index("--") + 1:]))
