"""
Raspberry Pi 4B version of the "Cam_RPI_auto_IR" enclosure bottom.

Derived from measurements of the Pi Zero W original (derotated by 15 deg):
  wall 2, floor 2, height 40, outer corner r=3, camera/IR front face,
  ribs + 4 mm pin hole in the camera zone, side vent slots, floor grille.

Coordinates: box centred on X/Y origin, Z=0 is the bottom face.
  +Y = back wall (Pi port edge: USB-C, 2x micro-HDMI, audio)
  -Y = front wall (camera + IR windows)
  -X = USB / Ethernet wall        +X = microSD wall
Pi board coords (bx, by; origin bottom-left, USB stack on the right) map to the
box by a 180 deg rotation:  X = BOARD_X0 - bx,  Y = BOARD_Y0 - by
"""
import numpy as np
import trimesh
from shapely.geometry import box as sbox, Point
from shapely.ops import unary_union
from trimesh.boolean import union, difference

# ---------------- parameters (mm) ----------------
WALL, FLOOR, H = 2.0, 2.0, 40.0
R_OUT, R_IN = 3.0, 1.0

PI_W, PI_D, PCB_T = 85.0, 56.0, 1.6
CAM_ZONE = 37.5           # depth of camera zone (same as original)
BACK_GAP = 2.0            # PCB port edge -> back wall inner face
USB_SIDE_GAP, SD_SIDE_GAP = 2.5, 1.5
STANDOFF_H = 5.0          # same as original
POST_D, PILOT_D, PILOT_DEPTH = 6.0, 2.2, 4.5

INNER_X = PI_W + USB_SIDE_GAP + SD_SIDE_GAP          # 89.0
INNER_Y = CAM_ZONE + PI_D + BACK_GAP                  # 95.5
OUT_X, OUT_Y = INNER_X + 2 * WALL, INNER_Y + 2 * WALL # 93.0 x 99.5
ix, iy = INNER_X / 2, INNER_Y / 2

BOARD_X0 = ix - SD_SIDE_GAP        # X of board left edge (bx=0)  -> +X side
BOARD_Y0 = iy - BACK_GAP           # Y of board port edge (by=0)  -> +Y side
PCB_BOT = FLOOR + STANDOFF_H
PCB_TOP = PCB_BOT + PCB_T

def bx2X(bx): return BOARD_X0 - bx
def by2Y(by): return BOARD_Y0 - by

# ---------------- helpers ----------------
def rrect(w, d, r):
    return sbox(-w/2 + r, -d/2 + r, w/2 - r, d/2 - r).buffer(r, resolution=32)

def prism(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m

def bx_(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1)/2, (y0 + y1)/2, (z0 + z1)/2])
    return m

def cyl(x, y, r, z0, z1, sections=48):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([x, y, (z0 + z1)/2])
    return m

# ---------------- shell ----------------
shell = prism(rrect(OUT_X, OUT_Y, R_OUT), 0, H)
cavity = prism(rrect(INNER_X, INNER_Y, R_IN), FLOOR, H + 1)
body = difference([shell, cavity], engine="manifold")

# ---------------- additive features ----------------
adds = []
# Pi 4B standoffs (58 x 49 pattern, 3.5 mm from edges)
holes_bd = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]
posts_xy = [(bx2X(a), by2Y(b)) for a, b in holes_bd]
for x, y in posts_xy:
    adds.append(cyl(x, y, POST_D/2, FLOOR - 0.2, FLOOR + STANDOFF_H))

# camera-zone ribs (same size/position relative to the front wall as original)
yf = -iy                                   # front wall inner face
adds.append(bx_(-29, -23, yf - 0.2, yf + 10, FLOOR - 0.2, 3.5))
adds.append(bx_( 23,  29, yf - 0.2, yf + 10, FLOOR - 0.2, 3.5))
adds.append(bx_( -3,   3, yf - 0.2, yf + 20, FLOOR - 0.2, 3.5))
body = union([body] + adds, engine="manifold")

# ---------------- subtractive features ----------------
cuts = []
for x, y in posts_xy:                       # blind pilot holes for M2.5
    cuts.append(cyl(x, y, PILOT_D/2, PCB_BOT - PILOT_DEPTH, PCB_BOT + 0.5, 32))
cuts.append(cyl(0, yf + 15, 2.0, -1, 5, 32))  # 4 mm pin/screw hole in centre rib

# floor grille under SoC/RAM: concentric quadrant arcs like the original
gx, gy = bx2X(32.0), by2Y(27.0)
cross = unary_union([sbox(-30, -1, 30, 1), sbox(-1, -30, 1, 30)])
rings = [(0, 5), (7, 9), (11, 13), (15, 17)]
for r0, r1 in rings:
    el = Point(0, 0).buffer(r1, resolution=48)
    if r0 > 0:
        el = el.difference(Point(0, 0).buffer(r0, resolution=48))
    el = el.difference(cross)
    geoms = list(el.geoms) if hasattr(el, "geoms") else [el]
    for g in geoms:
        if g.area < 0.5: continue
        m = prism(g, -1, FLOOR + 1)
        m.apply_translation([gx, gy, 0])
        cuts.append(m)

# front wall (camera face, -Y): lens window + 2 IR windows (same as original)
yfo = -iy - WALL
cuts.append(bx_(-7.5, 7.5,  yfo - 1, yfo + WALL + 0.3,  7.5, 22.5))
cuts.append(bx_(-36.5, -11.5, yfo - 1, yfo + WALL + 0.3, 4.5, 25.5))
cuts.append(bx_( 11.5,  36.5, yfo - 1, yfo + WALL + 0.3, 4.5, 25.5))

# back wall (+Y): Pi port edge. Centres from the Pi 4B mechanical drawing.
yb0, yb1 = iy - 0.3, iy + WALL + 1
def back_slot(bx_c, w, z0, z1):
    X = bx2X(bx_c)
    cuts.append(bx_(X - w/2, X + w/2, yb0, yb1, z0, z1))
back_slot(11.2, 13.0, PCB_TOP - 2.1, PCB_TOP + 5.3)      # USB-C
back_slot(26.0, 11.5, PCB_TOP - 2.0, PCB_TOP + 5.0)      # micro-HDMI 0
back_slot(39.5, 11.5, PCB_TOP - 2.0, PCB_TOP + 5.0)      # micro-HDMI 1
jack = trimesh.creation.cylinder(radius=4.0, height=yb1 - yb0, sections=48,
        transform=trimesh.transformations.concatenate_matrices(
            trimesh.transformations.translation_matrix([bx2X(53.5), (yb0 + yb1)/2, PCB_TOP + 3.0]),
            trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])))
cuts.append(jack)
# upper viewports kept from the original (8 x 8, z 26..34)
cuts.append(bx_(-23, -15, yb0, yb1, 26, 34))
cuts.append(bx_( 15,  23, yb0, yb1, 26, 34))

# -X wall: Ethernet + USB3 + USB2
xw0, xw1 = -ix - WALL - 1, -ix + 0.3
def usb_slot(by_c, w, z0, z1):
    Y = by2Y(by_c)
    cuts.append(bx_(xw0, xw1, Y - w/2, Y + w/2, z0, z1))
usb_slot(10.25, 17.0, PCB_TOP - 0.6, PCB_TOP + 14.4)     # Ethernet
usb_slot(29.0,  14.6, PCB_TOP - 0.6, PCB_TOP + 16.8)     # USB 3 stack
usb_slot(47.0,  14.6, PCB_TOP - 0.6, PCB_TOP + 16.8)     # USB 2 stack

# +X wall: microSD access
xs0, xs1 = ix - 0.3, ix + WALL + 1
Ysd = by2Y(28.0)
cuts.append(bx_(xs0, xs1, Ysd - 8, Ysd + 8, 4.5, 9.0))

# vent slots (3 x 3 mm, pitch 9) like the original; -X wall upper row only
for u in np.arange(-27, 27.1, 9):
    for (z0, z1) in ((26.5, 29.5), (32.5, 35.5)):
        cuts.append(bx_(xs0, xs1, u - 1.5, u + 1.5, z0, z1))          # +X
    cuts.append(bx_(xw0, xw1, u - 1.5, u + 1.5, 32.5, 35.5))           # -X

body = difference([body, union(cuts, engine="manifold")], engine="manifold")
body.merge_vertices()
body.export("pi4b_camera_enclosure_bottom.stl")

print("outer", OUT_X, "x", OUT_Y, "x", H, "| inner", INNER_X, "x", INNER_Y)
print("watertight", body.is_watertight, "volume mm3", round(body.volume, 1), "bounds", body.bounds.round(2).tolist())
print("posts XY", [(round(x, 2), round(y, 2)) for x, y in posts_xy])
print("PCB z", PCB_BOT, "->", PCB_TOP)
