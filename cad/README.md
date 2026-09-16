# Omatiller 01

A presentation concept for a removable tiller pilot, modeled in build123d.
The assembly contains 69 named parts, including a hollow housing and pushrod,
helical screw, traveling nut, parallel motor, belt, guide rails, seals, and
controller-board envelopes. Dimensions are provisional, in millimeters.

This is not fabrication geometry. Component sizing, tolerances, clearances under
load, sealing, mounting strength, and the release mechanism remain unvalidated.
The screw ridge and belt are illustrative profiles, and the PCB is a layout study.

## Generate

```sh
python3 -m venv cad/.venv
cad/.venv/bin/pip install -r cad/requirements.txt
cad/.venv/bin/python cad/assembly.py --step
```

Run from the omatiller repository root. `--output PATH` changes the output folder;
`--step` adds the CAD assembly export. The GLB and JSON metadata are always emitted.
Generation checks every part for positive volume and OpenCascade shape validity.

Verified with Python 3.14 on aarch64, build123d 0.11.1 and
cadquery-ocp-novtk 7.9.3.1.1. The package dependency graph is not fully locked;
`requirements.txt` pins the authoring API, not every transitive dependency.

## Website

The sibling `omahoy` repository serves the page at `site/omatiller/`. Copy both
generated artifacts together after a model change:

```sh
cp cad/output/omatiller-01.glb cad/output/omatiller-01.json \
  ../omahoy/site/omatiller/model/
```

Metadata associates each named part with a material, component group, exploded
offset, and whether it travels with the ram. GLB positions are in meters, under a
root that maps CAD Z-up to glTF Y-up. Metadata vectors remain in CAD millimeters.
The viewer keeps these frames explicit and displays a 250 mm concept stroke.

The site's nameplate graphics, flexible cable, lighting, and ground shadow are
presentation additions. They are not part of the STEP assembly. The interactive
page uses the CAD tessellation rather than a separately hand-modeled approximation.
