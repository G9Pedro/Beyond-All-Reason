#!/usr/bin/env python3
"""Generate the true-scale infantry ("people soldiers") assets.

Writes, relative to the repo root:
  objects3d/Units/armsoldier.s3o, objects3d/Units/corsoldier.s3o
  unittextures/people_color.tga, unittextures/people_other.tga
  unitpics/armsoldier.dds, unitpics/corsoldier.dds  (needs Pillow)

Scale: measured from BAR's own vehicle models, ~6 elmos per metre
(armbull 47 elmos long ~ 7.9 m MBT hull, armstump 40 ~ 6.8 m, armfav 25 ~ 4.2 m jeep).
A 1.8 m soldier is therefore ~10.8 elmos tall. The Commander model is ~125 elmos (~21 m).

Run: python3 tools/people_soldiers/build_people.py
"""
import math
import os
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
M = 6.0  # elmos per metre

# ---------------------------------------------------------------- texture ---
# 8 full-height colour columns, 8 px wide each, in a 64x64 texture. Using full
# height columns means the V axis orientation never matters.
#            name        rgb               teamcolor  emissive metal rough
SWATCHES = [
	("skin",      (196, 150, 118), 0.00, 0.0, 0.0, 0.75),
	("uniform",   (92, 98, 66),    0.45, 0.0, 0.0, 0.90),
	("team",      (255, 255, 255), 1.00, 0.0, 0.1, 0.50),
	("boots",     (32, 28, 24),    0.00, 0.0, 0.0, 0.85),
	("gunmetal",  (46, 48, 52),    0.00, 0.0, 0.8, 0.35),
	("pack",      (70, 64, 46),    0.00, 0.0, 0.0, 0.90),
	("visor",     (255, 190, 60),  0.00, 1.0, 0.2, 0.20),
	("armor",     (64, 64, 70),    0.55, 0.0, 0.5, 0.55),
]
SW = {s[0]: i for i, s in enumerate(SWATCHES)}
TEX = 64
COLW = TEX // len(SWATCHES)


def uv(name):
	i = SW[name]
	return ((i * COLW + COLW / 2) / TEX, 0.5)


def write_tga(path, pixels_rgba):
	# uncompressed 32-bit, origin top-left
	header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, TEX, TEX, 32, 0x28)
	body = bytearray()
	for r, g, b, a in pixels_rgba:
		body += bytes((b, g, r, a))
	with open(path, "wb") as f:
		f.write(header + body)


def write_textures():
	color, other = [], []
	for _y in range(TEX):
		for x in range(TEX):
			name, rgb, tc, em, me, ro = SWATCHES[min(x // COLW, len(SWATCHES) - 1)]
			color.append((*rgb, int(round(tc * 255))))
			other.append((int(em * 255), int(me * 255), int(ro * 255), 255))
	write_tga(os.path.join(ROOT, "unittextures/people_color.tga"), color)
	write_tga(os.path.join(ROOT, "unittextures/people_other.tga"), other)


# ------------------------------------------------------------------ model ---
class Piece:
	def __init__(self, name, offset=(0, 0, 0)):
		self.name = name
		self.offset = offset
		self.verts = []  # (pos, normal, uv)
		self.tris = []
		self.children = []

	def add(self, child):
		self.children.append(child)
		return child

	def box(self, lo, hi, swatch):
		"""Axis aligned box in piece-local metres-free elmo coords."""
		x0, y0, z0 = lo
		x1, y1, z1 = hi
		t = uv(swatch)
		faces = [
			((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]),
			((-1, 0, 0), [(x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0)]),
			((0, 1, 0), [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)]),
			((0, -1, 0), [(x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)]),
			((0, 0, 1), [(x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (x0, y0, z1)]),
			((0, 0, -1), [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)]),
		]
		for n, quad in faces:
			b = len(self.verts)
			for p in quad:
				self.verts.append((p, n, t))
			# winding matches BAR's own s3o files: (v1-v0) x (v2-v0) points along the normal
			self.tris += [b, b + 1, b + 2, b, b + 2, b + 3]
		return self


def m(*v):
	return tuple(c * M for c in v)


def build_soldier(faction):
	cor = faction == "cor"
	body_sw = "armor" if cor else "uniform"

	base = Piece("base")
	pelvis = base.add(Piece("pelvis", m(0, 0.95, 0)))
	pelvis.box(m(-0.17, -0.10, -0.10), m(0.17, 0.10, 0.10), body_sw)

	torso = pelvis.add(Piece("torso", m(0, 0.08, 0)))
	torso.box(m(-0.21, 0.0, -0.12), m(0.21, 0.56, 0.12), body_sw)
	torso.box(m(-0.22, 0.10, -0.135), m(0.22, 0.40, 0.135), "team")  # chest rig / vest
	torso.box(m(-0.17, 0.12, -0.32), m(0.17, 0.50, -0.12), "pack")  # backpack
	if cor:
		torso.box(m(-0.30, 0.44, -0.14), m(0.30, 0.58, 0.14), "armor")  # pauldrons

	head = torso.add(Piece("head", m(0, 0.60, 0)))
	head.box(m(-0.09, 0.0, -0.10), m(0.09, 0.22, 0.10), "skin")
	if cor:
		head.box(m(-0.12, 0.08, -0.13), m(0.12, 0.30, 0.13), "armor")  # closed helmet
		head.box(m(-0.10, 0.11, 0.12), m(0.10, 0.17, 0.14), "visor")
	else:
		head.box(m(-0.12, 0.15, -0.13), m(0.12, 0.29, 0.13), "team")  # helmet
		head.box(m(-0.13, 0.15, -0.14), m(0.13, 0.19, 0.14), "team")  # brim

	# aim pivot at shoulder height: rifle + both arms pitch together
	aim = torso.add(Piece("aim", m(0, 0.48, 0)))
	rarm = aim.add(Piece("rarm", m(0.25, 0, 0)))
	rarm.box(m(-0.05, -0.05, -0.05), m(0.05, 0.05, 0.40), body_sw)
	rarm.box(m(-0.045, -0.045, 0.40), m(0.045, 0.045, 0.48), "skin")
	larm = aim.add(Piece("larm", m(-0.25, 0, 0)))
	larm.box(m(-0.05, -0.05, -0.05), m(0.05, 0.05, 0.55), body_sw)
	larm.box(m(-0.045, -0.045, 0.55), m(0.045, 0.045, 0.62), "skin")
	rifle = aim.add(Piece("rifle", m(0.10, -0.02, 0.35)))
	rifle.box(m(-0.025, -0.05, -0.30), m(0.025, 0.04, 0.30), "gunmetal")  # body
	rifle.box(m(-0.012, -0.012, 0.30), m(0.012, 0.012, 0.55), "gunmetal")  # barrel
	rifle.box(m(-0.02, -0.16, 0.02), m(0.02, -0.05, 0.10), "gunmetal")  # magazine
	rifle.add(Piece("flare", m(0, 0, 0.57)))

	for side, name in ((1, "r"), (-1, "l")):
		thigh = pelvis.add(Piece(name + "thigh", m(0.10 * side, -0.05, 0)))
		thigh.box(m(-0.075, -0.45, -0.075), m(0.075, 0.0, 0.075), body_sw)
		shin = thigh.add(Piece(name + "shin", m(0, -0.45, 0)))
		shin.box(m(-0.065, -0.40, -0.065), m(0.065, 0.0, 0.065), body_sw)
		shin.box(m(-0.07, -0.45, -0.08), m(0.07, -0.33, 0.16), "boots")
	return base


def collect(piece, origin=(0, 0, 0), out=None):
	out = [] if out is None else out
	o = tuple(a + b for a, b in zip(origin, piece.offset))
	for p, _n, _t in piece.verts:
		out.append(tuple(a + b for a, b in zip(o, p)))
	for c in piece.children:
		collect(c, o, out)
	return out


def write_s3o(path, root, tex1, tex2):
	pts = collect(root)
	ys = [p[1] for p in pts]
	height = max(ys)
	mid = (0.0, height / 2, 0.0)
	radius = max(math.dist(p, mid) for p in pts)

	buf = bytearray(b"\0" * 52)  # header placeholder

	def put_str(s):
		off = len(buf)
		buf.extend(s.encode() + b"\0")
		return off

	def put_piece(pc):
		name_off = put_str(pc.name)
		vert_off = len(buf)
		for p, n, t in pc.verts:
			buf.extend(struct.pack("<8f", *p, *n, *t))
		idx_off = len(buf)
		buf.extend(struct.pack("<%di" % len(pc.tris), *pc.tris))
		child_offs = [put_piece(c) for c in pc.children]
		children_off = len(buf)
		buf.extend(struct.pack("<%di" % len(child_offs), *child_offs))
		off = len(buf)
		buf.extend(struct.pack(
			"<10i3f", name_off, len(child_offs), children_off, len(pc.verts), vert_off,
			0, 0, len(pc.tris), idx_off, 0, *pc.offset))
		return off

	root_off = put_piece(root)
	t1 = put_str(tex1)
	t2 = put_str(tex2)
	struct.pack_into("<12si5f4i", buf, 0, b"Spring unit\0", 0, radius, height, *mid, root_off, 0, t1, t2)
	with open(path, "wb") as f:
		f.write(buf)
	return radius, height


# --------------------------------------------------------------- buildpic ---
def render_buildpic(path, root, team_rgb):
	try:
		from PIL import Image, ImageDraw
	except ImportError:
		print("Pillow not installed, skipping", path)
		return
	S = 256
	img = Image.new("RGBA", (S, S))
	d = ImageDraw.Draw(img)
	for y in range(S):  # sky-ish gradient
		k = y / S
		d.line([(0, y), (S, y)], fill=(int(40 + 30 * k), int(52 + 34 * k), int(60 + 20 * k), 255))
	d.ellipse([60, 212, 196, 236], fill=(24, 28, 26, 255))  # ground shadow

	yaw, pitch = math.radians(35), math.radians(-12)
	light = (0.4, 0.8, 0.45)
	tris = []

	def walk(pc, origin):
		o = tuple(a + b for a, b in zip(origin, pc.offset))
		for i in range(0, len(pc.tris), 3):
			vs = [pc.verts[pc.tris[i + k]] for k in range(3)]
			tris.append(([tuple(a + b for a, b in zip(o, v[0])) for v in vs], vs[0][1], vs[0][2]))
		for c in pc.children:
			walk(c, o)

	walk(root, (0, 0, 0))

	def rot(p):
		x, y, z = p
		x, z = x * math.cos(yaw) + z * math.sin(yaw), -x * math.sin(yaw) + z * math.cos(yaw)
		y, z = y * math.cos(pitch) - z * math.sin(pitch), y * math.sin(pitch) + z * math.cos(pitch)
		return x, y, z

	scale = S * 0.80 / 11.5
	cx, cy = S / 2, S * 0.88
	drawn = []
	for pts, n, t in tris:
		rp = [rot(p) for p in pts]
		rn = rot(n)
		if rn[2] <= 0:
			continue
		swatch = SWATCHES[int(t[0] * TEX) // COLW]
		_, rgb, tc, em, _me, _ro = swatch
		col = [rgb[k] * (1 - tc) + team_rgb[k] * tc for k in range(3)]
		lam = max(0.0, sum(a * b for a, b in zip(rot(n), light)))
		shade = max(lam * 0.85 + 0.30, em)
		col = tuple(min(255, int(c * shade)) for c in col) + (255,)
		depth = sum(p[2] for p in rp) / 3
		drawn.append((depth, [(cx + p[0] * scale, cy - p[1] * scale) for p in rp], col))
	for _dep, poly, col in sorted(drawn, key=lambda d: d[0]):
		d.polygon(poly, fill=col)
	img.save(path, format="DDS")


def main():
	write_textures()
	for fac, team in (("arm", (40, 110, 230)), ("cor", (220, 50, 40))):
		root = build_soldier(fac)
		r, h = write_s3o(os.path.join(ROOT, "objects3d/Units/%ssoldier.s3o" % fac), root,
			"people_color.tga", "people_other.tga")
		print("%ssoldier: height %.1f elmos (%.2f m), radius %.1f" % (fac, h, h / M, r))
		render_buildpic(os.path.join(ROOT, "unitpics/%ssoldier.dds" % fac), root, team)


if __name__ == "__main__":
	main()
