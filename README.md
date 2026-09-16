# Omatiller

Tiller pilot control for [Omahoy](https://github.com/shieldsworks/omahoy).

**Status: hardware concept.** The first [CAD assembly](cad/README.md) is ready
to explore. Control software, hardware validation, and boat trials are still ahead.

The [design plan](PLAN.md) covers the custom ram, heading sensor, code-based CAD,
interactive website model, and staged bench and boat testing.

The planned pilot uses its own heading sensor and controller: no NMEA network is
required for heading hold. Omahoy can still use NMEA for compatibility with
existing GPS and AIS equipment through omakeel.

## What it will do

- Hold a heading, or steer to a waypoint from
  [omahelm](https://github.com/shieldsworks/omahelm).
- Always give way to manual override.

## License

MIT
