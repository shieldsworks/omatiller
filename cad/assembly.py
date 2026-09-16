"""Omatiller 01: a dimensioned presentation concept, not fabrication geometry.

All dimensions in mm. X follows the ram; Z is up. Run with build123d 0.11.1.
Named solids and presentation metadata stay together across GLB and STEP exports.
"""
from pathlib import Path
import argparse
import json
import build123d as b

STROKE = 250
BODY_LENGTH = 410
BODY_WIDTH = 74
BODY_HEIGHT = 86
SCREW_LEAD = 8
parts = []
metadata = {}

COLORS = {
    "ceramic": "#dadbd2", "graphite": "#252f35", "rubber": "#101a20",
    "steel": "#aab9c1", "orange": "#ed743a", "bronze": "#b88b4d",
    "pcb": "#245b4f", "black": "#151b20", "silver": "#84949e",
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


def build():
    parts.clear()
    metadata.clear()
    # A deep tray and separate curved lid. The annular front opening clears the ram.
    outer = rounded_box(BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT, 12, (-80, 0, -4))
    cavity = rounded_box(BODY_LENGTH - 9, BODY_WIDTH - 9, BODY_HEIGHT - 9, 8,
                         (-80, 0, -4))
    hollow = outer - cavity - cyl(13, 30, (118, 0, 10))
    lower = hollow & b.Box(500, 100, 69).translate((-80, 0, -15.5))
    lid = hollow & b.Box(500, 100, 30).translate((-80, 0, 34.5))
    # Four screw holes through the service cover and real internal mounting bosses.
    for x in (-258, 96):
        for y in (-25, 25):
            lid = lid - cyl(1.8, 30, (x, y, 30), "z")
            boss = ring(4.5, 1.8, 20, (x, y, 9), "z")
            add(f"cover_boss_{x}_{y}", boss, "graphite", "housing")
            screw_head(f"cover_screw_{x}_{y}", (x, y, 34.5), "cover", (0, 0, 95))
    add("lower_housing", lower, "ceramic", "housing", (0, 0, -65))
    add("service_cover", lid, "graphite", "cover", (0, 0, 95))
    # Continuous perimeter gasket (not an asserted seal specification).
    gasket = (rounded_box(390, 65, 1.6, .7, (-80, 0, 19)) -
              rounded_box(384, 59, 4, 1.5, (-80, 0, 19)))
    add("cover_gasket", gasket, "orange", "cover", (0, 0, 55))

    # Front wiper, guide and anodized retaining ring.
    for name, ro, ri, length, x, mat, offset in [
        ("nose_bezel", 20, 11.3, 9, 124, "graphite", 45),
        ("nose_accent", 19.2, 11.3, 2, 129.5, "orange", 55),
        ("rod_wiper", 13, 11.05, 4, 133, "rubber", 65),
        ("guide_bushing", 13, 11.15, 22, 107, "bronze", 25),
    ]:
        add(name, ring(ro, ri, length, (x, 0, 10)), mat, "guide", (offset, 0, 0))

    # Sliding tube conceals the screw when assembled; hollow geometry works in cutaway.
    add("pushrod", ring(11, 8.1, 380, (105, 0, 10)), "steel", "ram", (75, 0, 0), True)
    add("rod_end_collar", ring(14, 10.7, 17, (289, 0, 10)), "graphite", "ram", (85, 0, 0), True)
    end = rounded_box(43, 30, 26, 6, (310, 0, 10))
    end = end - cyl(5, 40, (318, 0, 10), "z")
    add("tiller_attachment", end, "graphite", "ram", (95, 0, 0), True)
    add("tiller_bushing", ring(7, 5, 25, (318, 0, 10), "z"), "bronze", "ram", (95, 0, 0), True)
    add("release_tab", rounded_box(22, 25, 5, 2, (311, 0, 25.5)), "orange", "ram", (95, 0, 12), True)

    add("screw_shaft", cyl(5.2, 326, (-66, 0, 10)), "steel", "drive")
    # Helical ridge is illustrative; no claim of a selected ball-screw race profile.
    helix = b.Helix(SCREW_LEAD, 292, 5.7)
    profile = b.Plane(origin=helix @ 0, z_dir=helix % 0) * b.Circle(.9)
    thread = b.sweep(profile, path=helix, is_frenet=True)
    thread = thread.rotate(b.Axis.Y, 90).translate((-215, 0, 10))
    add("screw_helix", thread, "steel", "drive")
    add("traveling_nut", ring(15, 6.7, 22, (-80, 0, 10)), "bronze", "ram", (0, 0, 0), True)
    add("nut_flange", ring(21, 7, 4, (-91, 0, 10)), "bronze", "ram", (0, 0, 0), True)
    add("nut_carriage", rounded_box(20, 48, 8, 2, (-80, 0, -12)), "graphite", "ram", (0, 0, 0), True)
    for y in (-24, 24):
        add(f"guide_rail_{y}", cyl(3, 320, (-62, y, -12)), "steel", "drive")
    add("rear_bearing", ring(14, 5.3, 11, (-223, 0, 10)), "silver", "drive", (-20, 0, 0))
    add("bearing_bulkhead", rounded_box(9, 62, 65, 3, (-231, 0, -5)) -
        cyl(14.1, 15, (-231, 0, 10)) - cyl(8, 15, (-231, 0, -28)),
        "graphite", "drive", (-20, 0, 0))

    # Parallel brushed motor and timing belt, with flanged pulleys.
    add("motor_can", cyl(17, 81, (-184, 0, -28)), "silver", "motor", (0, -65, -25))
    for x in (-226, -141):
        add(f"motor_end_{x}", cyl(17.7, 5, (x, 0, -28)), "graphite", "motor", (0, -65, -25))
    add("motor_shaft", cyl(3, 20, (-238, 0, -28)), "steel", "motor", (0, -65, -25))
    for z, radius, label in [(10, 16, "screw"), (-28, 9, "motor")]:
        add(f"{label}_pulley", cyl(radius, 10, (-250, 0, z)), "bronze", "transmission", (-50, 0, 0))
        for x in (-256, -244):
            add(f"{label}_pulley_flange_{x}", ring(radius + 1.5, 3, 1.5, (x, 0, z)), "graphite", "transmission", (-50, 0, 0))
    # Belt envelope in the YZ plane around both pulley pitch circles.
    # Convex tangent path approximates the belt silhouette without small tooth geometry.
    with b.BuildSketch(b.Plane.YZ) as belt_sk:
        with b.Locations((0, 10)):
            b.Circle(17)
        with b.Locations((0, -28)):
            b.Circle(10)
        b.Polygon((-16.7, 13), (16.7, 13), (9.8, -30), (-9.8, -30))
        with b.Locations((0, 10)):
            b.Circle(15.5, mode=b.Mode.SUBTRACT)
        with b.Locations((0, -28)):
            b.Circle(8.5, mode=b.Mode.SUBTRACT)
        b.Polygon((-15.2, 12), (15.2, 12), (8.3, -29), (-8.3, -29), mode=b.Mode.SUBTRACT)
    add("timing_belt", b.extrude(belt_sk.sketch, amount=8).translate((-254, 0, 0)), "rubber", "transmission", (-50, 0, 0))

    # Electronics bay and components, kept below the rod's complete travel envelope.
    add("controller_board", rounded_box(100, 51, 1.6, .5, (12, 0, -35)), "pcb", "electronics", (0, -85, -15))
    for x, y, l, w, h, label, mat in [
        (-12, 0, 17, 17, 2, "mcu", "black"), (26, -10, 15, 12, 4, "driver", "black"),
        (44, 13, 13, 12, 9, "terminal", "orange"), (-26, 16, 10, 8, 4, "connector", "ceramic"),
    ]:
        add(label, rounded_box(l, w, h, .5, (x, y, -34 + h/2)), mat, "electronics", (0, -85, -15))
    for i in range(8):
        add(f"pcb_contact_{i}", b.Box(2, 4, .3).translate((-23+i*5, -21, -34)), "bronze", "electronics", (0, -85, -15))
    for x in (-29, 52):
        for y in (-19, 19):
            add(f"board_standoff_{x}_{y}", ring(3, 1.3, 6, (x, y, -39), "z"), "bronze", "electronics", (0, -85, -15))
    for x in (10, 25):
        add(f"capacitor_{x}", cyl(4, 10, (x, 13, -29), "z"), "graphite", "electronics", (0, -85, -15))
    # Limit sensors at the two ends of the nut-carriage travel.
    for x in (-213, 58):
        add(f"limit_sensor_{x}", rounded_box(13, 8, 7, 1, (x, 25, -5)), "orange", "drive")

    # Socket mount and removable pivot pin.
    add("mount_neck", cyl(9, 24, (-258, 0, -58), "z"), "steel", "mount", (0, 0, -35))
    add("socket_base", ring(21, 9.2, 6, (-258, 0, -73), "z"), "graphite", "mount", (0, 0, -55))
    add("socket_sleeve", ring(12, 9.2, 19, (-258, 0, -85), "z"), "bronze", "mount", (0, 0, -55))
    add("power_gland", ring(8, 4, 16, (-287, 0, -17)), "graphite", "housing", (-20, 0, -65))
    # Top badges, two flush controls, and a small status indicator.
    add("nameplate", rounded_box(114, 32, 1.3, .5, (-106, 0, 39.2)), "graphite", "cover", (0, 0, 95))
    for x, name, mat in [(41, "standby_button", "orange"), (70, "heading_button", "rubber")]:
        add(name, cyl(8, 2.4, (x, 0, 39), "z"), mat, "cover", (0, 0, 95))
    add("status_light", rounded_box(13, 2, 1, .4, (6, 0, 39)), "orange", "cover", (0, 0, 95))

    return b.Compound(label="omatiller_01", children=parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output")
    parser.add_argument("--step", action="store_true", help="Also export the concept STEP assembly")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    assembly = build()
    if args.step:
        b.export_step(assembly, args.output / "omatiller-01.step")
    if not b.export_gltf(assembly, args.output / "omatiller-01.glb", binary=True,
                         linear_deflection=.15, angular_deflection=.25):
        raise RuntimeError("GLB export failed")
    (args.output / "omatiller-01.json").write_text(json.dumps({
        "revision": "01", "status": "concept", "units": "mm",
        "stroke": STROKE, "screwLead": SCREW_LEAD, "parts": metadata,
    }, indent=2) + "\n")
    print(f"Exported {len(parts)} valid parts to {args.output}")
