# Omatiller design plan

Draft recovered and continued from the interrupted Claude session, September 15, 2026.
This is a development plan, not a fabrication release or a tested steering system.

## Current progress

Casey prioritized a detailed website model and authorized provisional mounting
dimensions, with fitting to follow later. The first build123d concept now contains
69 named parts and exports GLB, metadata, and optional STEP. The sibling website
has an interactive omatiller page with assembled, exploded, and transparent views,
ram travel, component descriptions, keyboard controls, and a static fallback.
It highlights the planned sensor/controller path with no required NMEA network.
The following hardware and control milestones remain future work.

Concept 02 (September 17, 2026) replaced the first study's provisional drive and
geometry with the decisions below: 83 named parts, a 1605 ball screw, a brushless
gearmotor, the ESP32 and ODrive S1 controller, the handbook's socket and pin spacing,
a tiller pin and seat socket, and a keypad with a heading display on the cover. The
site shows it as a product shot, without a seat or tiller. `cad/README.md` lists every
dimension with its source. The moving parts clear the fixed ones at 0, 125 and
250 mm of travel.

## Decisions, September 17, 2026

- **The heading sensor is an omarig node.** It serves the whole suite (heading-up
  charts, AIS bearings, instruments), not only the pilot. It sits in its own box at
  least 750 mm from the ram's motor, bolted down, and reaches the pilot controller
  by wire. It also sends NMEA 0183 `HDG`/`ROT` over Wi-Fi, which omakeel ingests as
  a new `heading` key.
- **No commercial reference pilot.** Casey won't buy one. The mounting dimensions
  come from Raymarine's ST1000 Plus/ST2000 Plus handbook (1996), found in
  Raymarine's public document library (retired products, Autopilots, Tiller
  Pilots): socket to pin 589 mm with the tiller centered, rudder stock to pin
  460 mm at right angles, pilot mounted level on the starboard seat by default.
  The pin goes in a 6 mm hole 25 mm deep with its shoulder 12.5 mm above the tiller;
  the socket goes in a 12.5 mm hole 25 mm deep, backed if the seat is under 25 mm.
  The handbook gives no stroke, thrust, pin-head or socket-bore size, so Omatiller
  uses its own pin and socket at that spacing.
- **Brushless drive from the first bench build.** A 200 W-class brushless planetary
  gearmotor driven by an ODrive S1, which the ESP32 commands over CAN. The S1's
  minimum input is 12 V, so a 12 to 24 V converter feeds it and the motor is the
  24 V variant. At 10:1 the gearmotor gives the ball screw its 300 rpm target with
  several times the 0.88 N·m required. Writing our own motor control stays a later
  goal; the S1 runs ODrive's firmware.
- **A 1605 ball screw, not ACME.** It passes about 90% of the motor's work to the
  nut against about 40% for ACME, and it can be pushed back by hand.
- **The keypad lives on the unit.** Six keys (AUTO, STBY, ±1°, ±10°), a status light
  and a heading display on the cover, wired straight to the ESP32, as on the classic
  tiller pilots. Casey chose this over a remote pod on a mount.
- **GoPro-style and 1-inch ball mounts only for accessories**, such as a phone or
  cameras for filming trials. Never the pilot itself, whose ends carry the steering
  load, and never the compass, where a slipped mount would silently shift the
  heading.

## Direction already chosen

- Build a custom tiller pilot for Dash, a Pacific Seacraft 25.
- Dash has no existing pilot, mounting socket, or tiller pin.
- Use a removable linear ram between a cockpit socket and a tiller pin, targeting
  conventional commercial mounting geometry. Verify compatibility before claiming
  a commercial pilot is a drop-in replacement.
- Author dimensioned geometry in Python using build123d. Export STEP for CAD,
  STL for printing, and GLB for the website.
- Keep the control software original and in Rust, consistent with Omahoy.
- Show the design on an omatiller page at omahoy.org, including an interactive
  assembly. The site should distinguish concept, prototype, and tested hardware.

## What exists today

Dash's dimensions are already published in the website's “Aboard Dash” section
(`omahoy/site/index.html`): length 24.5 ft, beam 8.0 ft, draft 3.3 ft, and weight
5,700 lb (about 2,585 kg), with tiller steering. Use these as the documented boat
baseline for concept proportions and commercial pilot comparisons. The listed
weight is not a measurement of her current loaded displacement, and these overall
dimensions do not determine tiller force or mounting geometry.

At recovery, the omatiller repository contained only a README and MIT license.
It now includes the concept model in `cad/`; there is no pilot-control implementation.

Claude installed build123d 0.11.1 in a temporary Python 3.14/aarch64 environment
and generated a small filleted solid. Its STEP, STL, and GLB files remain present.
This proves the basic export path, not an assembly, browser rendering, or
manufacturability. Preserve the dependency versions in a reproducible CAD setup
when creating the first real model; the temporary environment is not a project
dependency installation.

The local omakeel protocol exposes GPS course over ground (`fix.cogDeg`) but no
own-boat heading. Its `targets.headingDeg` belongs to other vessels. Apps receive
messages and send nothing in protocol v1. Unknown message types and keys are
already allowed, so heading telemetry can be added without adding command traffic.

## Architecture proposal

1. A separate heading sensor measures orientation and rate of turn away from the
   motor and high-current wiring. Keep magnetic heading, true heading, and GPS
   course explicitly distinguished. Conversion to true heading requires a valid
   variation source; never silently relabel magnetic heading.
2. An embedded controller owns motor output, limits, watchdogs, and the local
   heading-control loop. A desktop process or Wi-Fi connection must not be the
   only mechanism that can stop drive output.
3. The omatiller Rust engine provides configuration, logging, simulation, and a
   dedicated command/status socket. Its UI follows the existing standalone app
   pattern. omakeel remains a telemetry hub.
4. Commands carry session identity, sequence, and bounded validity. On stale
   commands, stale heading, reset, or a fault, disable output and require explicit
   re-engagement. Reconnection must not replay an old engagement command.
5. A physical standby control inhibits the drive independently of the desktop.
   A mechanical release allows manual steering even if the drive is jammed.
   Removing electrical power alone does not establish manual override.

Ownership: reusable sensor hardware and Rust firmware in omarig; pilot-specific
mechanics, control, simulator, and UI in omatiller; heading ingestion and
distribution in omakeel. Casey confirmed the heading sensor belongs in omarig.

## Milestone 1 — CAD concept and website

Create `cad/` with parameter definitions, a reproducible dependency setup, assembly
generation, and export instructions. Label each parameter as measured, taken from
a named component drawing, or provisional. Use named parts and a stable origin so
the browser can separate the assembly without reverse-engineering a single mesh.

Model the housing, sliding rod, screw and nut envelope, motor and transmission
envelope, end bearings, socket pivot, tiller attachment, seals, cable exit, and
service cover. Purchased-component envelopes are placeholders until part numbers
are selected. Show the load path and reserve real space for fasteners and tools.

Start with a provisional 250 mm stroke. Sweep retracted, centered, and extended
positions for collisions and clearance. This number is a layout assumption, not a
confirmed requirement for Dash. Obtain exact mount, pin, socket, and installation
dimensions from boat measurements before fixing the interfaces. The commercial
spacing now comes from the Raymarine handbook (see the decisions above).

Add `omahoy/site/omatiller/index.html` using the existing styles and theme picker.
Use the exported GLB for orbit, zoom, labeled components, and an exploded-view
control. Include a static fallback and keyboard-accessible controls. Avoid automatic
continuous animation; accommodate reduced motion. Clearly label it a concept.

Acceptance: valid nonempty solids; STEP reimport with matching dimensions; GLB
scale and orientation checked in the browser; no collisions across the intended
stroke; usable page on narrow screens and with WebGL unavailable. A concept can
ship before actuator procurement, but must not offer unvalidated fabrication files
as ready-to-build parts.

## Milestone 2 — Heading sensor, without actuation

Evaluate available IMUs using manufacturer documentation, Rust driver feasibility,
calibration access, sample timing, and availability. Select the part only after
checking its current lifecycle and breakout-board electrical details.

Record raw gyro, accelerometer, magnetometer, temperature, timestamps, calibration
state, and fused orientation. Define mounting axes and rate-of-turn sign. Test
heading wrap, tilt compensation, magnetic disturbance, bias drift, reboot, delayed
data, and disconnected sensors. Motor-on interference testing follows on the bench.

Add timestamped heading telemetry with explicit reference, source, freshness, and
validity to omakeel. Keep the sensor path suitable for a wired pilot connection;
Wi-Fi telemetry for other apps does not establish control-loop reliability.

Acceptance: measured error and latency against an independent reference, including
heel and nearby electrical loads, plus reproducible recordings and calibration.
Set numerical acceptance limits before selecting the sensor. Heading alone does
not provide speed through water or eliminate leeway when calculating true wind.

## Milestone 3 — Requirements and bench actuator

The overall boat dimensions are already documented above. The remaining onboard
measurements concern the installation: proposed rudder-stock-to-pin distance,
socket location and backing structure,
tiller heights and angles, full steering travel, release access, and interference
with cockpit use. Establish operating tiller loads and transient loads using a
documented measurement method. No boat drilling follows from the concept model.

Compare a purchased actuator with a custom screw drive at the same simultaneous
force and speed, voltage, duty cycle, environmental conditions, and release method.
Record loaded speed, continuous and peak current, thermal limits, backlash, and
end-stop behavior. Stall torque and no-load speed are not one operating point.

Useful sizing example, not a boat requirement: 1,000 N at 25 mm/s is 25 W of linear
output. For an assumed 90%-efficient 5 mm-lead screw, that requires approximately
0.884 N·m at 300 rpm and 27.8 W at the screw shaft, before motor/transmission losses.
Efficiency must be replaced with the selected screw's data. A higher reduction
ratio cannot make up a power deficit.

The [Pololu 12 V 37D family](https://www.pololu.com/category/271/12v-37d-metal-gearmotors)
lists maximum output powers of 6–12 W across its ratios and load limitations;
these motors cannot satisfy that example point. This eliminates one tempting
candidate, but does not select a replacement or prove Dash needs 1,000 N.

Use a restrained load rig to measure force versus speed, duty-cycle heating,
reversal, jam handling, limit switches, power loss, and release under load. Select
the motor driver, wiring, supply protection, and fuse together from measured and
documented currents. Define regeneration handling and the actual inhibit path.

Buy precision/load-bearing components initially: screw/nut, bearings, rod, motor,
fasteners, seals, and electrical connectors. Print fit-check parts and enclosure
prototypes. Validate materials, load paths, corrosion isolation, drainage, sealing,
and thermal behavior before assigning printed parts structural duty. Neither a
CAD export nor a sealed-looking rendering establishes an ingress rating.

## Milestone 4 — Original control software and fault tests

Start with standby and heading hold. Use gyro rate for damping, bounded drive
output, rate/acceleration limits, and explicit control states. Add integral action
only with anti-windup and measured need. Route following and wind steering follow
after heading hold is established.

Build a deterministic simulator with boat yaw response, actuator travel, backlash,
latency, sensor faults, and wave disturbances. Treat simulation as a development
tool, not proof of boat performance. Replay recordings through the same control
core used on hardware.

Required cases: 359°/0° crossing, wrong steering polarity, saturation, invalid or
stale samples, stuck sensor values, lost/reordered commands, duplicate engagement,
clock discontinuity, jam, end travel, undervoltage, controller reset, and desktop
failure. Verify output inhibition and that no fault recovery auto-engages the ram.
Validate mechanical release separately, including loss of power under load.

## Milestone 5 — Boat installation and staged trials

Release fabrication drawings only after measured geometry, selected components,
load calculations, bench results, and an independent mechanical/electrical review
agree. Confirm mounting strength and release access on the actual boat.

Start with dockside direction and manual-override checks, then supervised heading
hold in benign open-water conditions with a person immediately able to take the
tiller. Expand conditions only against written acceptance criteria and recorded
results. Track heading error, peak excursions, drive duty, current, temperature,
faults, and recovery. Route steering needs its own tests and engagement semantics.

## Next concrete work

Measure Dash: check that the 589/460 mm layout fits the starboard seat, the tiller's
height above the seat (the handbook's standard is 64 mm; Concept 02 needs about
105 mm), seat thickness and full tiller swing, then log tiller load with a luggage
scale on a windy afternoon. Those set the stroke, the thrust and any socket pedestal.
Then start the omarig compass node. Assemble a purchase shortlist with dated pricing
and availability: the drive family is chosen, but no motor, controller, screw or IMU
has been ordered.

## Recovery notes and references

The interrupted research covered prior art, actuator sizing, heading sensors,
marine electrics, sealing, and safety. Most jobs stopped before delivering final
results. Treat recovered prose as research leads, not verified specifications.
In particular, do not inherit blanket claims that all worm drives self-lock, all
commercial pilots are backdrivable or clutched, or a given material is waterproof.

- [build123d export documentation](https://build123d.readthedocs.io/en/stable/import_export.html)
  documents STEP, STL, and glTF export. An exported solid still needs engineering
  drawings, tolerances, materials, and validation to become a buildable part.
- [Raymarine ST1000/ST2000 product page](https://www.raymarine.com/en-gb/our-products/boat-autopilots/autopilot-packs/st1000-st2000)
  and its manuals provide commercial reference information, not proof of this
  design's suitability.
- Local architecture references: `omakeel/docs/protocol.md`, `omarig/README.md`,
  and `omahoy/site/README.md` in their sibling repositories.

The concept model and local website implementation are now present. Hardware
validation, control software, purchases, and boat modification remain pending.
