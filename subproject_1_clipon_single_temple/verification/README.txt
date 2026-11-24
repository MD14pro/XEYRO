Own Geometry & Schematic-to-PCB Parity Checker (NOT KiCad DRC / NOT KiCad ERC)
==============================================================================

- check_pcb.py: Standalone Python script that parses esp32s3_glasses_cam.kicad_pcb and
  esp32s3_glasses_cam.kicad_sch to verify copper clearances (>= 0.127 mm), shorts, opens,
  dangling track endpoints, copper-to-edge clearance (>= 0.25 mm), via-in-pad count,
  antenna keepout (0..3.3, 5.5..10.0 mm), RF path geometry, USB lengths, power track
  widths, and schematic-to-PCB pin/net parity.
- checker_output.txt: Raw unmodified output from running `python3 verification/check_pcb.py`.
- LIMITATION: This script is NOT KiCad DRC and NOT KiCad ERC. The owner must run
  Edit > Fill All Zones, Inspect > ERC, Inspect > DRC, and File > Plot in KiCad 10.
