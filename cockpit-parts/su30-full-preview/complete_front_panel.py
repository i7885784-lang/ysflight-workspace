"""Finish the static front-panel preview in both aircraft representations."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import install_preview


class Surface:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def face(self, points, color):
        ids = list(range(len(self.vertices), len(self.vertices) + len(points)))
        self.vertices.extend(points)
        self.faces.extend(["F", "C " + " ".join(map(str, color)), "N 0 0 -1",
                           "V " + " ".join(map(str, ids)), "E"])

    def box(self, x, y, z, width, height, depth, color):
        p = [(x + a * width / 2, y + b * height / 2, z + c * depth / 2)
             for a, b, c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                             (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        for indices in [(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),
                        (0,1,5,4),(3,7,6,2)]:
            self.face([p[i] for i in indices], color)

    def lines(self):
        return (["SURF"] + ["V %.7f %.7f %.7f" % p for p in self.vertices]
                + self.faces + ["E"])


def add_upper_panel(destination):
    unit = Surface()
    unit.box(0, 1.062, 6.08, .178, .092, .038, (31, 39, 43))
    unit.box(0, 1.093, 6.058, .144, .016, .004, (9, 20, 24))
    unit.box(0, 1.015, 6.081, .105, .012, .049, (29, 36, 39))
    for row in range(4):
        for col in range(6):
            x, y = (col - 2.5) * .022, 1.074 - row * .014
            unit.box(x, y, 6.057, .014, .009, .004, (91, 99, 98))
            unit.box(x, y, 6.0545, .004, .0013, .0005, (173, 183, 177))
    frame = Surface()
    frame.box(0, 1.122, 6.12, .090, .019, .08, (29, 37, 39))
    for sign in (-1, 1):
        x = sign * .047
        frame.box(x, 1.187, 6.145, .004, .125, .005, (28, 36, 37))
    frame.box(0, 1.252, 6.145, .098, .004, .005, (28, 36, 37))
    glass = Surface()
    glass.face([(-.045,1.130,6.146),(-.045,1.250,6.146),
                (.045,1.250,6.146),(.045,1.130,6.146)], (93, 155, 146, 48))
    parts = [("Pilot_Upper_Control", unit.lines()), ("Pilot_HUD_Frame", frame.lines()),
             ("Pilot_HUD_Glass", glass.lines())]
    text = destination.read_text().splitlines()
    i = 2
    while text[i].startswith("PCK "):
        i += 1 + int(text[i].split()[-1])
    packed, nodes = text[:i], text[i:-1]
    for name, lines in parts:
        packed += [f"PCK {name}.srf {len(lines)}"] + lines
        nodes += [f'SRF "{name}"', f"FIL {name}.srf", "CLA 99", "NST 1",
                  "STA 0 0 0 0 0 0 1", "POS 0 0 0 0 0 0 1", "CNT 0 0 0",
                  "PAX 1 0 0", "REL DEP", "NCH 0", "END"]
    destination.write_text("\n".join(packed + nodes + ["END"]) + "\n")


if __name__ == "__main__":
    source, model, destination = map(Path, sys.argv[sys.argv.index("--") + 1:])
    install_preview.install(source, model, destination)
    add_upper_panel(destination)
