"""Extend only the fixed nose-bay backing; preserve every animation node."""
import argparse
import hashlib
import math
import numpy as np
from scipy.spatial.transform import Rotation
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / 'model-source'))
import dnm
from mesh import Mesh


def patch(source, destination):
    expected = "dadaddbd32530a68b9ef80413fc37741df073df3eacaca23c580951198fdfce9"
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError("Use the unchanged Su-34 from su30sm-vectornozzles-before-cobra-20261115")
    packs, nodes = dnm.read(source)
    original_nodes = [n[:] for n in nodes]
    name = 'RecessedNoseBaySeal.srf'
    original = dnm.mesh(packs[name])
    backing = Mesh()
    # A 35 mm recessed overlap closes the hairline without a deep fascia.
    # Existing doors and all their animation states remain untouched.
    for ids, colour, bright in original.f:
        pts = [original.v[i] for i in ids]
        if not all(abs(p[0]) > .43 for p in pts):
            continue
        lower = [(x, y - .035, z) for x, y, z in pts]
        backing.face(lower, colour, bright)
        for a, b, aa, bb in zip(pts, pts[1:] + pts[:1], lower, lower[1:] + lower[:1]):
            backing.face([a, b, bb, aa], colour, bright)
            backing.face([aa, bb, b, a], colour, bright)
    # Four small stationary hinge seats per side, positioned from the actual
    # deployed door edge. Each is a U-shaped bracket rather than a long bar.
    for door_name in ('FlushDoorN0', 'FlushDoorN1'):
        door = next(n for n in nodes if dnm.name(n) == door_name)
        vertices = np.array(dnm.mesh(packs[dnm.fil(door)]).v)
        state = [line.split()[1:] for line in door if line.startswith('STA ')][-1]
        translation = np.array(state[:3], float)
        h, pitch, bank = np.array(state[3:6], float) * math.pi / 32768
        rotation = Rotation.from_euler('YXZ', [-h, -pitch, bank]).as_matrix()
        deployed = vertices @ rotation.T + translation
        for z in (1.30, 2.20, 3.10, 4.05):
            section = deployed[abs(deployed[:, 2] - z) < .055]
            edge = section[section[:, 1] > section[:, 1].max() - .009]
            x, y, _ = edge.mean(axis=0)
            x += math.copysign(.025, x)
            y -= .025
            # Side cheeks and a pin seat; the opening remains visible.
            colour = (65, 77, 80)
            for dz in (-.031, .031):
                backing.box(x, y + .012, z + dz, .052, .055, .012, colour)
            backing.box(x, y - .012, z, .052, .012, .074, (78, 88, 89))
    if not backing.f:
        raise ValueError('Expected nose bay side walls were not found')
    original.merge(backing)
    packs[name] = original.srf()
    assert nodes == original_nodes
    dnm.write(destination, packs, nodes)
    check_packs, check_nodes = dnm.read(destination)
    source_packs, source_nodes = dnm.read(source)
    assert check_nodes == source_nodes, 'Animation nodes changed'
    assert {k:v for k,v in check_packs.items() if k != name} == {k:v for k,v in source_packs.items() if k != name}
    print(f'Added {len(backing.f)} fixed backing faces; all nodes and other meshes preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.destination.resolve():
        parser.error('Use separate source and destination files')
    patch(args.source, args.destination)
