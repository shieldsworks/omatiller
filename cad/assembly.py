"""Omatiller 02: a dimensioned presentation concept, not fabrication geometry.

All dimensions in mm. X follows the ram; Z is up; the origin is on the ram's
center plane, 22 mm below the screw axis, just ahead of the ball nut at mid-travel.
Every modeled part is at mid-stroke.
Named solids and presentation metadata stay together across GLB and STEP exports.
"""
from pathlib import Path
import argparse
import json
import math
import build123d as b

REVISION = "02"

# Mounting geometry from Raymarine's ST1000 Plus/ST2000 Plus handbook (1996),
# pp. 35-37, so a standard socket and pin spacing carries over.
SOCKET_TO_PIN = 589     # dimension A, socket to tiller pin, tiller centered
STOCK_TO_PIN = 460      # dimension B, rudder stock centerline to tiller pin
PIN_SHOULDER = 12.5     # pin shoulder above the tiller face
PIN_HOLE = (6, 25)      # tiller pin hole: diameter, depth
SOCKET_HOLE = (12.5, 25)  # seat socket hole: diameter, depth

STROKE = 250            # provisional until Dash's tiller travel is measured
SCREW_LEAD = 5          # 1605 ball screw: 16 mm nominal, 5 mm per turn
SCREW_Z = 22
MOTOR_Z = -45

BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT = 445, 100, 138
BODY_X, BODY_Z = -77.5, -13           # housing spans x -300..145, z -82..56
SPLIT_Z = 36                          # cover joint
SOCKET_X = -265
PIN_X = SOCKET_X + SOCKET_TO_PIN      # 324
SEAT_Z = -110                         # top of the seat around the socket

parts = []
metadata = {}

COLORS = {
    "ceramic": "#dadbd2", "graphite": "#252f35", "rubber": "#101a20",
    "steel": "#aab9c1", "orange": "#ed743a", "bronze": "#b88b4d",
    "pcb": "#245b4f", "black": "#151b20", "silver": "#84949e",
    "wood": "#8a5a36", "gelcoat": "#c9cdc6",
}

DIMENSIONS = {
    "socketToPin": {"mm": SOCKET_TO_PIN, "source": "Raymarine ST1000/2000 Plus handbook, p. 35"},
    "stockToPin": {"mm": STOCK_TO_PIN, "source": "Raymarine ST1000/2000 Plus handbook, p. 35"},
    "pinShoulder": {"mm": PIN_SHOULDER, "source": "Raymarine ST1000/2000 Plus handbook, p. 36"},
    "pinHole": {"mm": list(PIN_HOLE), "source": "Raymarine ST1000/2000 Plus handbook, p. 36"},
    "socketHole": {"mm": list(SOCKET_HOLE), "source": "Raymarine ST1000/2000 Plus handbook, p. 37"},
    "stroke": {"mm": STROKE, "source": "provisional; measure Dash's tiller travel"},
    "ballScrew": {"mm": [16, SCREW_LEAD], "source": "catalog-typical SFU1605 screw and nut; confirm against the purchased part"},
    "motor": {"mm": [57, 155], "source": "provisional envelope for a 200 W brushless planetary gearmotor"},
    "odrive": {"mm": [66, 51], "source": "provisional envelope; confirm against ODrive S1 drawings"},
    "goproMount": {"mm": [3.0, 3.2, 5.0], "source": "commonly published prong thickness, gap and M5 bolt; verify before printing"},
    "mountBall": {"mm": 25.4, "source": "1-inch ball, as used by B-size ball mounts"},
}


def rounded_box(l, w, h, r, xyz):
    shape = b.Box(l, w, h)
    shape = b.fillet(shape.edges(), r)
    return shape.translate(xyz)


def cyl(radius, length, xyz, axis="x"):
    shape = b.Cylinder(radius, length)
    if axis == "x":
        shape = shape.rotate(b.Axis.Y, 90)
    elif axis == "y":
        shape = shape.rotate(b.Axis.X, 90)
    return shape.translate(xyz)


def ring(ro, ri, length, xyz, axis="x"):
    return cyl(ro, length, xyz, axis) - cyl(ri, length + 2, xyz, axis)


def add(name, shape, material, group, explode=(0, 0, 0), moving=False):
    # three.js strips these characters from node names, so the site could not find the part.
    if any(c in name for c in "[].:/ "):
        raise ValueError(f"Part name not usable on the web: {name}")
    if isinstance(shape, b.ShapeList):
        shape = b.Compound(children=list(shape))
    if not shape.is_valid or shape.volume <= 0:
        raise ValueError(f"Invalid solid: {name}")
    shape.label = name
    shape.color = b.Color(COLORS[material])
    parts.append(shape)
    metadata[name] = dict(material=material, group=group, explode=explode,
                          moving=moving, volume_mm3=round(shape.volume, 3))


def screw_head(name, xyz, group, explode=(0, 0, 0)):
    head = cyl(3.1, 2.2, xyz, "z")
    recess = b.extrude(b.RegularPolygon(1.5, 6), amount=1.5).translate(
        (xyz[0], xyz[1], xyz[2] + .3))
    add(name, head - recess, "steel", group, explode)


def prong(x, y, z_axis, z_far, name, material, group, explode):
    """One GoPro-style prong: a 3 mm plate, rounded around an M5 hinge on Y."""
    height = abs(z_far - z_axis)
    plate = b.Box(15, 3, height).translate((x, y, (z_axis + z_far) / 2))
    shape = plate + cyl(7.5, 3, (x, y, z_axis), "y") - cyl(2.55, 5, (x, y, z_axis), "y")
    add(name, shape, material, group, explode)


def housing():
    outer = rounded_box(BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT, 12, (BODY_X, 0, BODY_Z))
    cavity = rounded_box(BODY_LENGTH - 9, BODY_WIDTH - 9, BODY_HEIGHT - 9, 8,
                         (BODY_X, 0, BODY_Z))
    hollow = (outer - cavity
              - cyl(13, 30, (145, 0, SCREW_Z))            # ram opening
              - cyl(9.2, 12, (SOCKET_X, 0, -80), "z")     # pivot neck
              - cyl(8.05, 12, (-300, 0, -40)))            # power gland
    # Sits in a groove on the wall between the cavity (436 x 91, r8) and the outside (445 x 100).
    gasket = (b.extrude(b.RectangleRounded(441, 96, 10), amount=1.6)
              - b.extrude(b.RectangleRounded(437, 92, 8.5), amount=1.6))
    gasket = gasket.translate((BODY_X, 0, SPLIT_Z - .8))
    hollow = hollow - gasket
    below = SPLIT_Z - (BODY_Z - BODY_HEIGHT / 2 - 5)
    lower = hollow & b.Box(500, 120, below).translate((BODY_X, 0, SPLIT_Z - below / 2))
    lid = hollow & b.Box(500, 120, 30).translate((BODY_X, 0, SPLIT_Z + 15))
    for x in (-280, 120):
        for y in (-38, 38):
            lid = lid - cyl(1.8, 40, (x, y, 50), "z")
            add(f"cover_boss_{x}_{y}", ring(4.5, 1.8, 14, (x, y, SPLIT_Z - 7), "z"),
                "graphite", "housing")
            screw_head(f"cover_screw_{x}_{y}", (x, y, 57.1), "cover", (0, 0, 70))
    add("lower_housing", lower, "ceramic", "housing", (0, 0, -55))
    add("service_cover", lid, "graphite", "cover", (0, 0, 70))
    add("cover_gasket", gasket, "orange", "cover", (0, 0, 40))

    add("nameplate", rounded_box(118, 32, 1.3, .5, (-150, 0, 56.65)), "graphite", "cover", (0, 0, 70))
    for x, name, mat in [(40, "standby_button", "orange"), (72, "auto_button", "rubber")]:
        add(name, cyl(8, 2.4, (x, 0, 57.2), "z"), mat, "cover", (0, 0, 70))
    add("status_light", rounded_box(13, 2, 1, .4, (8, 0, 56.5)), "orange", "cover", (0, 0, 70))
    add("power_gland", ring(8, 4, 16, (-306, 0, -40)), "graphite", "housing", (-25, 0, -55))


def guide_and_ram():
    # Front support: a bushing inside the nose, then a bezel and a rod wiper outside it.
    for name, ro, ri, length, x, mat, offset in [
        ("guide_bushing", 13, 11.15, 25, 132.5, "bronze", 25),
        ("nose_bezel", 20, 11.3, 8, 149, "graphite", 45),
        ("nose_accent", 19.2, 11.3, 2, 152.5, "orange", 55),
        ("rod_wiper", 13, 11.05, 4, 155.5, "rubber", 65),
    ]:
        add(name, ring(ro, ri, length, (x, 0, SCREW_Z)), mat, "guide", (offset, 0, 0))

    # Hollow stainless pushrod over the screw, bolted to the ball-nut flange.
    add("pushrod", ring(11, 9, 309, (145.5, 0, SCREW_Z)), "steel", "ram", (80, 0, 0), True)
    # 10 mm long, so it clears the wiper (x 157.5) by 1.5 mm at full retraction.
    add("rod_end_collar", ring(14, 11.05, 10, (289, 0, SCREW_Z)), "graphite", "ram", (90, 0, 0), True)
    end = (rounded_box(48, 32, 26, 6, (318, 0, SCREW_Z)) - cyl(7.05, 40, (PIN_X, 0, SCREW_Z), "z")
           - cyl(11.05, 12, (300, 0, SCREW_Z)))  # socket for the rod end
    add("tiller_fitting", end, "graphite", "ram", (100, 0, 0), True)
    add("fitting_bushing", ring(7, 5.1, 26, (PIN_X, 0, SCREW_Z), "z"), "bronze", "ram", (100, 0, 0), True)
    add("release_tab", rounded_box(22, 26, 5, 2, (312, 0, SCREW_Z + 15.5)), "orange", "ram", (100, 0, 14), True)

    # Tiller pin: shoulder 12.5 mm above the tiller face, 6 mm shank 25 mm deep.
    fitting_bottom = SCREW_Z - 13
    tiller_top = fitting_bottom - 2 - PIN_SHOULDER
    fitting_top = SCREW_Z + 13
    add("pin_head", cyl(5, fitting_top - tiller_top, (PIN_X, 0, (fitting_top + tiller_top) / 2), "z"), "steel", "boat", (100, 0, -30), True)
    add("pin_shoulder", ring(8, 5, 2, (PIN_X, 0, fitting_bottom - 1), "z"), "steel", "boat", (100, 0, -30), True)
    add("pin_shank", cyl(PIN_HOLE[0] / 2, PIN_HOLE[1], (PIN_X, 0, tiller_top - PIN_HOLE[1] / 2), "z"),
        "steel", "boat", (100, 0, -30), True)
    tiller = (rounded_box(40, 150, 34, 8, (PIN_X, 30, tiller_top - 17))
              - cyl(PIN_HOLE[0] / 2 + .05, PIN_HOLE[1], (PIN_X, 0, tiller_top - PIN_HOLE[1] / 2), "z"))
    add("tiller_section", tiller, "wood", "boat", (100, 0, -60), True)


def drive():
    # Ball screw: 16 mm nominal, 5 mm lead. The ridge suggests the ball track.
    add("screw_shaft", cyl(7.2, 343, (-56.5, 0, SCREW_Z)), "steel", "drive")
    add("screw_journal", cyl(6, 44, (-250, 0, SCREW_Z)), "steel", "drive")
    helix = b.Helix(SCREW_LEAD, 340, 7.6)
    # A diamond profile tessellates far lighter than a circle over 70 turns.
    profile = b.Plane(origin=helix @ 0, z_dir=helix % 0) * b.RegularPolygon(1.0, 4)
    track = b.sweep(profile, path=helix, is_frenet=True)
    add("screw_helix", track.rotate(b.Axis.Y, 90).translate((-226, 0, SCREW_Z)), "steel", "drive")

    # SFU1605-style nut: 28 mm body, 48 mm flange at the front, six bolts.
    add("ball_nut", ring(14, 8.6, 42, (-40, 0, SCREW_Z)), "bronze", "ram", moving=True)
    flange = ring(24, 8.6, 10, (-14, 0, SCREW_Z))
    for i in range(6):
        angle = math.radians(60 * i)
        flange = flange - cyl(2.75, 14, (-14, 19 * math.cos(angle), SCREW_Z + 19 * math.sin(angle)))
    add("nut_flange", flange, "bronze", "ram", moving=True)
    carriage = (rounded_box(42, 72, 10, 2, (-40, 0, -8))
                + b.Box(30, 18, 11).translate((-40, 0, 2.5)))
    for y in (-30, 30):
        carriage = carriage - cyl(3.15, 50, (-40, y, -8))
    add("nut_carriage", carriage, "graphite", "ram", moving=True)
    for y in (-30, 30):
        add(f"guide_rail_{y}", cyl(3, 343, (-56.5, y, -8)), "steel", "drive")
    for x in (-196, 116):
        add(f"limit_sensor_{x}", rounded_box(13, 8, 7, 1, (x, 41, -8)), "orange", "drive")

    # Bulkhead carries the screw's fixed bearing and the motor flange.
    # Tall enough to close around the bearing bore (top z 38), short of the lid (z 51.5).
    bulkhead = (rounded_box(12, 88, 115, 3, (-234, 0, -16.5))
                - cyl(16.1, 20, (-234, 0, SCREW_Z)) - cyl(7, 20, (-234, 0, MOTOR_Z)))
    add("bearing_bulkhead", bulkhead, "graphite", "drive", (-25, 0, 0))
    add("fixed_bearing", ring(16, 6.1, 12, (-234, 0, SCREW_Z)), "silver", "drive", (-25, 0, 0))


def motor():
    # Brushless planetary gearmotor below the screw, flange on the bulkhead.
    ex = (0, -80, -30)
    add("gearbox_flange", rounded_box(8, 60, 60, 3, (-224, 0, MOTOR_Z)), "graphite", "motor", ex)
    add("gearbox", cyl(28, 57, (-191.5, 0, MOTOR_Z)), "silver", "motor", ex)
    add("motor_body", cyl(28.5, 80, (-123, 0, MOTOR_Z)), "black", "motor", ex)
    for x in (-150, -123, -96):
        add(f"motor_band_{x}", ring(29.2, 28.55, 3, (x, 0, MOTOR_Z)), "graphite", "motor", ex)
    add("motor_end_cap", cyl(26, 10, (-78, 0, MOTOR_Z)), "graphite", "motor", ex)
    add("motor_shaft", cyl(5, 40, (-248, 0, MOTOR_Z)), "steel", "motor", ex)

    # 1:1 timing belt behind the bulkhead; the gearbox already sets 300 rpm.
    for z, label, bore in [(SCREW_Z, "screw", 6.05), (MOTOR_Z, "motor", 5.05)]:
        add(f"{label}_pulley", ring(16, bore, 10, (-262, 0, z)), "bronze", "transmission", (-55, 0, 0))
        for x, side in ((-267.75, "rear"), (-256.25, "front")):
            add(f"{label}_pulley_flange_{side}", ring(17.5, bore, 1.5, (x, 0, z)), "graphite", "transmission", (-55, 0, 0))
    span = SCREW_Z - MOTOR_Z
    with b.BuildSketch(b.Plane.YZ) as belt:
        with b.Locations((0, (SCREW_Z + MOTOR_Z) / 2)):
            b.SlotCenterToCenter(span, 35, rotation=90)
            b.SlotCenterToCenter(span, 32, rotation=90, mode=b.Mode.SUBTRACT)
    add("timing_belt", b.extrude(belt.sketch, amount=8).translate((-266, 0, 0)), "rubber", "transmission", (-55, 0, 0))


def electronics():
    ex = (0, -95, -25)
    # 74 mm wide, so it sits on the flat of the floor, inside the wall fillets.
    add("heat_spreader", rounded_box(135, 74, 5.5, 1, (22.5, 0, -74.75)), "silver", "electronics", ex)
    # ODrive S1 motor controller (provisional envelope).
    add("odrive_board", rounded_box(66, 51, 1.6, .5, (-5, 0, -66)), "pcb", "electronics", ex)
    add("odrive_power_stage", rounded_box(34, 28, 8, 1, (-12, -4, -61)), "black", "electronics", ex)
    add("odrive_connector", rounded_box(10, 30, 7, .5, (22, 0, -61.5)), "orange", "electronics", ex)
    for x in (-10, 6):
        add(f"odrive_capacitor_{x}", cyl(4, 10, (x, 16, -60), "z"), "graphite", "electronics", ex)
    # ESP32 steering controller.
    add("esp32_board", rounded_box(52, 26, 1.6, .5, (60, 0, -66)), "pcb", "electronics", ex)
    add("esp32_module", rounded_box(18, 24, 3, .3, (52, 0, -63.7)), "silver", "electronics", ex)
    add("can_transceiver", rounded_box(8, 6, 2, .3, (76, -6, -64.2)), "black", "electronics", ex)
    for x, y in [(-35, -20), (-35, 20), (25, -20), (25, 20),
                 (38, -10), (38, 10), (82, -10), (82, 10)]:
        add(f"standoff_{x}_{y}", ring(2.5, 1.2, 5.2, (x, y, -69.4), "z"), "bronze", "electronics", ex)
    # 12 to 24 V converter, so the ODrive runs mid-range on a sagging battery.
    add("dc_dc_converter", rounded_box(44, 40, 25.5, 2, (112, 0, -64.75)), "graphite", "electronics", ex)
    add("dc_dc_fins", b.Compound(children=[
        b.Box(44, 1.5, 4).translate((112, y, -50)) for y in (-15, -9, -3, 3, 9, 15)]),
        "silver", "electronics", ex)


def mount():
    # Pivot neck under the housing, a pin in a sleeve, and the seat it sits in.
    # The neck runs up through the floor and stands 1.5 mm proud inside.
    add("mount_neck", cyl(9, 32, (SOCKET_X, 0, -92), "z"), "steel", "mount", (0, 0, -20))
    add("pivot_pin", cyl(4, 25, (SOCKET_X, 0, SEAT_Z - 10.5), "z"), "steel", "mount", (0, 0, -20))
    add("socket_flange", ring(12, 4.1, 2, (SOCKET_X, 0, SEAT_Z + 1), "z"), "bronze", "mount", (0, 0, -29))
    add("socket_sleeve", ring(SOCKET_HOLE[0] / 2, 4.1, SOCKET_HOLE[1], (SOCKET_X, 0, SEAT_Z - SOCKET_HOLE[1] / 2), "z"),
        "bronze", "mount", (0, 0, -25))
    seat = (rounded_box(150, 120, 25, 6, (SOCKET_X + 10, 0, SEAT_Z - 12.5))
            - cyl(SOCKET_HOLE[0] / 2 + .05, SOCKET_HOLE[1] + 2, (SOCKET_X, 0, SEAT_Z - SOCKET_HOLE[1] / 2), "z"))
    # Exploded parts stay above the site's ground plane (z -170), and the seat
    # (top z -140) below the exploded housing (bottom z -137).
    add("cockpit_seat", seat, "gelcoat", "boat", (0, 0, -30))


def remote():
    # Keypad pod on GoPro-style fingers, a 1-inch ball arm, and a base.
    x, y = 215, -95
    ex = (75, -35, 0)
    add("remote_body", rounded_box(96, 60, 20, 6, (x, y, -20)), "graphite", "remote", ex)
    add("remote_display", rounded_box(56, 12, 1, .4, (x, y + 20, -9.6)), "black", "remote", ex)
    for i, bx in enumerate((x - 28, x, x + 28)):
        for j, by in enumerate((y - 16, y + 4)):
            mat = "orange" if (i, j) == (1, 1) else "rubber"
            add(f"remote_key_{i}_{j}", cyl(5.5, 2, (bx, by, -9), "z"), mat, "remote", ex)
    hinge = -45
    for dy, side in ((-3.1, "near"), (3.1, "far")):
        prong(x, y + dy, hinge, -30, f"remote_finger_{side}", "graphite", "remote", ex)
    for dy, side in ((-6.2, "near"), (0.0, "middle"), (6.2, "far")):
        prong(x, y + dy, hinge, -60, f"mount_prong_{side}", "ceramic", "remote", ex)
    add("mount_adapter", b.Box(15, 15.4, 6).translate((x, y, -63)), "ceramic", "remote", ex)
    add("thumbscrew", cyl(2.5, 22, (x, y, hinge), "y"), "steel", "remote", ex)
    add("thumbscrew_knob", cyl(7, 8, (x, y - 15, hinge), "y"), "orange", "remote", ex)
    add("upper_ball_stem", cyl(5, 6, (x, y, -69), "z"), "ceramic", "remote", ex)
    for z, name in [(-82, "upper_ball"), (-150, "lower_ball")]:
        add(name, b.Sphere(12.7).translate((x, y, z)), "rubber", "remote", ex)
        add(f"{name}_socket", ring(17, 11, 18, (x, y, z), "z"), "graphite", "remote", ex)
    add("ball_arm", b.Box(26, 14, 50).translate((x, y, -116)), "graphite", "remote", ex)
    add("arm_knob", cyl(10, 12, (x, y - 13, -116), "y"), "orange", "remote", ex)
    add("lower_ball_stem", cyl(5, 13.5, (x, y, -156.75), "z"), "ceramic", "remote", ex)
    add("mount_base", cyl(28, 5, (x, y, -166), "z"), "graphite", "remote", ex)


def build():
    parts.clear()
    metadata.clear()
    housing()
    guide_and_ram()
    drive()
    motor()
    electronics()
    mount()
    remote()
    return b.Compound(label=f"omatiller_{REVISION}", children=parts)


PRESENTATION = {
    # Everything here is drawn by the website, not part of the STEP assembly.
    "label": {"text": "omatiller", "subtext": f"OPEN MARINE HARDWARE / {REVISION}",
              "position": [-150, 0, 57.6], "size": [112, 28]},
    "cable": [[-314, 0, -40], [-330, 0, -44], [-346, 3, -72], [-362, 6, -108], [-392, 2, -132]],
    "target": [90, -30, -30],  # centers the assembled and exploded views at full travel
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output")
    parser.add_argument("--step", action="store_true", help="Also export the concept STEP assembly")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    stem = f"omatiller-{REVISION}"
    assembly = build()
    if args.step:
        b.export_step(assembly, args.output / f"{stem}.step")
    if not b.export_gltf(assembly, args.output / f"{stem}.glb", binary=True,
                         linear_deflection=.15, angular_deflection=.25):
        raise RuntimeError("GLB export failed")
    (args.output / f"{stem}.json").write_text(json.dumps({
        "revision": REVISION, "status": "concept", "units": "mm",
        "root": assembly.label, "stroke": STROKE, "screwLead": SCREW_LEAD,
        "screwAxis": [0, SCREW_Z], "dimensions": DIMENSIONS,
        "presentation": PRESENTATION, "parts": metadata,
    }, indent=2) + "\n")
    print(f"Exported {len(parts)} valid parts to {args.output}")
