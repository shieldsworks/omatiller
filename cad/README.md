# Omatiller 02

A presentation concept for a removable tiller pilot, modeled in build123d.
The assembly has 105 named parts: a split housing, a 1605 ball screw and nut on a
guided carriage, a brushless planetary gearmotor with a 1:1 belt, an ESP32 and
ODrive S1 controller with a 12 to 24 V converter, the tiller pin and seat socket,
and a remote keypad on GoPro-style fingers and 1-inch ball mounts.
Dimensions are in millimeters.

This is not fabrication geometry. Tolerances, clearances under load, sealing,
mounting strength and the release mechanism remain unvalidated.

## Where the dimensions come from

`assembly.py` keeps each source beside its number, and the JSON metadata carries
them under `dimensions`.

| Dimension | Value | Source |
|---|---|---|
| Socket to tiller pin, tiller centered | 589 mm | Raymarine ST1000 Plus/ST2000 Plus handbook (1996), p. 35 |
| Rudder stock to tiller pin | 460 mm | same, p. 35 |
| Pin shoulder above the tiller | 12.5 mm | same, p. 36 |
| Tiller pin hole | 6 mm × 25 mm deep | same, p. 36 |
| Seat socket hole | 12.5 mm × 25 mm deep | same, p. 37 |
| Housing length | 445 mm | same, p. 35 (the handbook unit's length) |
| Ram travel | 250 mm | provisional; measure Dash's tiller travel |
| Ball screw and nut | 16 mm, 5 mm lead; SFU1605 nut | catalog-typical; confirm against the purchased part |
| Gearmotor | Ø57 × 155 mm (Ø56 gearbox) | provisional envelope for a 200 W brushless planetary |
| ODrive S1 | 66 × 51 mm | provisional envelope |
| GoPro-style prongs | 3.0 mm plates, 3.2 mm gaps, M5 | commonly published values; verify before printing |
| Mount balls | 25.4 mm | 1-inch ball, as used by B-size ball mounts |

The housing is 100 × 138 mm in section, wider and taller than the handbook unit,
to fit the brushless drive under the screw. The seat socket sits 132 mm below the
screw axis, and the modeled tiller top is 104.5 mm above the seat, against the
handbook's standard 64 mm. Dash's seat and tiller heights decide whether the socket
needs a pedestal.

## Generate

```sh
python3 -m venv cad/.venv
cad/.venv/bin/pip install -r cad/requirements.txt
cad/.venv/bin/python cad/assembly.py --step
```

Run from the omatiller repository root. `--output PATH` changes the output folder;
`--step` adds the CAD assembly export. The GLB and JSON metadata are always emitted.
Generation checks every part for positive volume and OpenCascade shape validity,
and rejects part names the website can't look up (three.js strips `[].:/` and
spaces from node names).

Before publishing a change, sweep the ram through its travel and check that no
moving part intersects a fixed one; Concept 02 has no intersections at 0, 125 and
250 mm, and its STEP export reimports with the same overall size. The remaining
overlaps between fixed parts are deliberate seatings: balls in their sockets, the
inset display and bezel accent, and the ball track sunk into the screw.

Verified with Python 3.14 on aarch64, build123d 0.11.1 and
cadquery-ocp-novtk 7.9.3.1.1. The package dependency graph is not fully locked;
`requirements.txt` pins the authoring API, not every transitive dependency.

## Website

The sibling `omahoy` repository serves the page at `site/omatiller/`. Copy both
generated artifacts together after a model change:

```sh
cp cad/output/omatiller-02.glb cad/output/omatiller-02.json \
  ../omahoy/site/omatiller/model/
```

Metadata associates each named part with a material, component group, exploded
offset, and whether it travels with the ram. It also carries the stroke, screw lead
and axis, and a `presentation` block for what only the website draws: the nameplate
text, the power cable path and the camera target. GLB positions are in meters, under
a root that maps CAD Z-up to glTF Y-up. Metadata vectors remain in CAD millimeters.

The ball-screw track uses a diamond profile: over 70 turns a round profile doubled
the GLB to 5.5 MB.
