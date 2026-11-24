# ESP32-S3 Smart-Glasses Temple Camera PCB (KiCad Project)

## 1. Project Overview & Final Owner Decisions
- **Project Name**: `esp32s3_glasses_cam` (`esp32s3_glasses_cam.kicad_pro`, `esp32s3_glasses_cam.kicad_sch`, `esp32s3_glasses_cam.kicad_pcb`)
- **Form Factor**: 60.0 x 10.0 mm, 4-layer FR4 (1.6 mm total thickness), board origin (0, 0) at top-left corner (X = 0..60 mm, Y = 0..10 mm; `CPL_JLCPCB.csv` uses bottom-left origin PosY = 10.0 - y_kicad).
- **Final Owner Decisions (Confirmed by Owner)**:
  - **Single-Temple Architecture**: Self-contained single-temple camera, compute, Wi-Fi/BLE, USB-C, and LiPo power management board (no nose-bridge PCB or opposite-temple PCB).
  - **No microSD Slot**: Frames stream over 2.4 GHz Wi-Fi or buffer in the on-chip 2 MB PSRAM / 4 MB Flash of `ESP32-S3FH4R2`.
- **4-Layer Stackup (1.60 mm)**:
  - `F.Cu`: 0.035 mm copper (RF path, `U1`, `J1`, `J2`, crystal, matching network)
  - Prepreg 1: 0.210 mm FR4 (er = 4.5, tan_d = 0.02)
  - `In1.Cu`: 0.035 mm `GND` plane (script-generated zone fill, ~545 mm^2, notched around the antenna keepout at x = 0.0..3.3 mm, y = 5.5..10.0 mm; see Section 2 for zone refill note)
  - Core: 1.065 mm FR4 (er = 4.5)
  - `In2.Cu`: 0.035 mm inner signal and power routing layer (no adjacent reference plane)
  - Prepreg 2: 0.210 mm FR4 (er = 4.5, tan_d = 0.02)
  - `B.Cu`: 0.035 mm copper (LDOs `U2..U4`, charger `U5`, power path `Q1`/`D3`, bulk decoupling, test pads)
- **PCB Counts & Format**:
  - Format: KiCad 9 file format (`version 20241229`), `generator_version "10.0"`. KiCad 10 opens it directly; saving in KiCad 10 will upgrade the file format.
  - Totals: 59 footprints, 1546 track segments, 153 vias (`105` x `0.45/0.20 mm` with `0.125 mm` annular ring, `40` x `0.40/0.20 mm` with `0.100 mm` annular ring). Confirm `0.40/0.20 mm` via capability with your fab's 4-layer rules before ordering.
  - Zone fill in `esp32s3_glasses_cam.kicad_pcb` is script-generated (`GND` on `In1.Cu`, ~545 mm^2). KiCad will recompute it; run **Edit > Fill All Zones** before DRC and Plot.

## 2. Verification Status & Design Rules
- **Verification Status**: Own geometry checker (included in `verification/`): 0 clearance violations at 0.127 mm, 0 opens, 0 shorts, 0 dangling track ends, copper-to-edge >= 0.25 mm (measured minimum 0.260 mm), nothing inside the antenna keepout, 1 via-in-pad (`U1` EPAD only, `U1.57` at `(26.50, 4.50)`), schematic <-> PCB 222 pins 0 net mismatches. **KiCad ERC / DRC / Plot: NOT VERIFIED (owner runs them).**
- **Measured Minimum Copper Clearance**: `0.130 mm` between different nets on `F.Cu` (`L2` pad 1 `RF_MATCH` vs `C_X2` pad 2 `GND`, rule `>= 0.127 mm`).
- **Minimum Rules in `esp32s3_glasses_cam.kicad_pro`**:
  - Clearance `0.127 mm`, track width `0.127 mm`, via diameter `0.40 mm`, through-hole drill `0.20 mm`, copper-to-edge `0.25 mm`, hole-to-hole `0.20 mm`.
  - `.kicad_pro` has all DRC/ERC severities set to `error` (52 DRC keys set to `error`, 13 other keys left at KiCad defaults; ERC includes `single_global_label` and `four_way_junction` set to `error`).
- **ERC Annotation Note**:
  - ERC error `Item not annotated: C_3V3_B?` was seen once in the owner's real KiCad 10 run (and `C_PU?` on the follow-up run). 19 designators were renamed to end in a digit (`C_3V3_B1`, `C_PU1`, `C_SPI1`, `C_U2_OUT1`, `C_VBAT1`, `C_VBUS1`, `C_VSYS1`, `D_DM1`, `D_DP1`, `D_VBUS1`, `R_GATE1`, `R_LED1`, `R_PROG1`, `R_PU1`, `R_SCL1`, `R_SDA1`, `TP_CHG1`, `TP_GND1`, `TP_VBAT1`). Whether this clears the error is **NOT VERIFIED** until the owner re-runs ERC in KiCad 10.
- **Measured Power Track Widths (after Part C2 widening)**:
  - `VBAT`: `0.30 mm`
  - `VSYS`: `0.30 mm`
  - `+5V_USB`: `0.20 - 0.25 mm`
  - `+3V3`: `0.16 - 0.30 mm` (10 segments widened from `0.16 mm` to `0.20 mm`; 14 segments remain `0.16 mm` where widening to `0.20 mm` would violate `0.127 mm` clearance; see `CHANGELOG.md` item C2)
  - `+2V8`: `0.16 - 0.25 mm` (9 segments remain `0.16 mm` where widening to `0.20 mm` would violate `0.127 mm` clearance; see `CHANGELOG.md` item C2)
  - `+1V2`: `0.25 mm`

## 3. Datasheet vs. PCB Footprint Comparison Table (`NOT VERIFIED - owner to compare`)
Compare each footprint in `esp32s3_glasses_cam.kicad_pcb` against the manufacturer datasheet drawing before releasing Gerbers.

| Ref | MPN & Package | Datasheet Link | PCB Footprint Geometry | Pin-1 Position & Contact Notes | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `J1` | `AFC01-S24FCA-00` (Jushuo 24-pin 0.5 mm FPC) | [LCSC C262669](https://www.lcsc.com/product-detail/C262669.html) / [OV2640 Pinout Ref](https://docs.sunfounder.com/projects/esp-cam-kit/en/latest/component_esp32_extension.html) | 24 SMD signal pads (`0.28 x 0.72 mm`, `0.50 mm` pitch), 2 mechanical SMD tabs, `F.Cu` at `(8.80, 2.70)` rot `0` | Pin 1 at `(3.05, 1.28)`. Verify bottom-contact vs top-contact and pin-1 end against your OV2640 flex cable | NOT VERIFIED - owner to compare |
| `AE1` | `2450AT18A100E` (Johanson 2.45 GHz 1206 Chip Antenna) | [Johanson Ver 1.0](https://www.johansontechnology.com/docs/1129/2450AT18A100E-AEC_tCZ7Fpd.pdf) / [Rev 2.0](https://www.johansontechnology.com/docs/3828/Antenna-2450AT18A0100002E-Rev2.0.pdf) / [LCSC C89334](https://www.lcsc.com/product-detail/C89334.html) | 2 SMD pads (`0.80 x 1.50 mm`, center pitch `2.70 mm`), `F.Cu` at `(2.30, 7.80)` rot `0` | Pad 1 (NC anchor) at `(0.95, 7.80)`, Pad 2 (Feed, `RF_MATCH`) at `(3.65, 7.80)`. Keepout `(0..3.3, 5.5..10.0 mm)` empty | NOT VERIFIED - owner to compare |
| `Y1` | `XRCGB40M000F2P00R0` (Murata 40 MHz 2.0x1.6 mm Crystal) | [Murata XRCGB Series](https://www.murata.com/en-in/products/timingdevice/crystalu/overview/lineup/xrcgb) / [LCSC C2843083](https://www.lcsc.com/product-detail/C2843083.html) | 4 SMD pads (`0.85 x 0.70 mm`, `1.30 x 1.10 mm` pitch), `F.Cu` at `(19.20, 2.40)` rot `0` | Pad 1 `(18.55, 1.85)` `XTAL_P`, Pad 2 `(19.85, 1.85)` `GND`, Pad 3 `(19.85, 2.95)` `XTAL_N`, Pad 4 `(18.55, 2.95)` `GND` | NOT VERIFIED - owner to compare |
| `SW1, SW2` | `TS-1088-AR02016` (XUNPU 3.0x2.0 mm Tactile Switch) | [XUNPU Datasheet PDF](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_XUNPU-TS-1088-AR02016_C720477.pdf) / [LCSC C720477](https://www.lcsc.com/product-detail/C720477.html) | 4 SMD pads (`0.70 x 0.55 mm`, `2.80 x 1.10 mm` pitch), `F.Cu` at `SW1 (47.00, 2.00)` and `SW2 (42.00, 2.00)` | Pads 1 & 3 (`x - 1.40`) = `CHIP_PU` (`SW1`) / `GPIO0_BOOT` (`SW2`); Pads 2 & 4 (`x + 1.40`) = `GND` | NOT VERIFIED - owner to compare |
| `U1` | `ESP32-S3FH4R2` (Espressif QFN-56 7.0x7.0 mm, 0.4 mm pitch) | [Espressif ESP32-S3 Datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) / [LCSC C3013940](https://www.lcsc.com/product-detail/C3013940.html) | 56 perimeter pads (`0.80 x 0.20 mm`, `0.40 mm` pitch) + Pad 57 EPAD (`4.00 x 4.00 mm`) + 1 central thermal via `(26.50, 4.50)`, `F.Cu` at `(26.50, 4.50)` | Pad 1 (`LNA_IN`, `RF_ANT`) at `(23.05, 1.90)`. Counter-clockwise numbering | NOT VERIFIED - owner to compare |

## 4. Complete BOM & LCSC Table (`NOT VERIFIED - owner to check stock on lcsc.com`)
Every LCSC code below matches its link and `BOM_JLCPCB.csv`. Stock and package match on `lcsc.com` are **NOT VERIFIED** by us.

| Designator(s) | Qty | Value / Comment | MPN | Footprint | LCSC Part # | Mount Side | Status |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| `U1` | 1 | `ESP32-S3FH4R2` | `ESP32-S3FH4R2` | `esp32s3_glasses_cam:Espressif_QFN-56-1EP_7x7mm_P0.4mm_EP4.0x4.0mm` | [C3013940](https://www.lcsc.com/product-detail/C3013940.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `J1` | 1 | `AFC01-S24FCA-00` | `AFC01-S24FCA-00` | `esp32s3_glasses_cam:Jushuo_AFC01-S24FCA-00_1x24-1MP_P0.5mm_Horizontal` | [C262669](https://www.lcsc.com/product-detail/C262669.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `J2` | 1 | `TYPE-C-31-M-12` | `TYPE-C-31-M-12` | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` (pre-rotated project copy) | [C165948](https://www.lcsc.com/product-detail/C165948.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `AE1` | 1 | `2450AT18A100E` | `2450AT18A100E` | `esp32s3_glasses_cam:Johanson_2450AT18A100E_3.2x1.6mm` | [C89334](https://www.lcsc.com/product-detail/C89334.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `Y1` | 1 | `40MHz_10ppm` | `XRCGB40M000F2P00R0` | `esp32s3_glasses_cam:Murata_XRCGB40M000F2P00R0_2.0x1.6mm_4Pin` | [C2843083](https://www.lcsc.com/product-detail/C2843083.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `U2` | 1 | `TLV75733PDBVR` | `TLV75733PDBVR` | `Package_TO_SOT_SMD:SOT-23-5` | [C485517](https://www.lcsc.com/product-detail/C485517.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `U3` | 1 | `ME6211C28M5G-N` | `ME6211C28M5G-N` | `Package_TO_SOT_SMD:SOT-23-5` | [C53099](https://www.lcsc.com/product-detail/C53099.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `U4` | 1 | `ME6211C12M5G-N` | `ME6211C12M5G-N` | `Package_TO_SOT_SMD:SOT-23-5` | [C236672](https://www.lcsc.com/product-detail/C236672.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `U5` | 1 | `MCP73831T-2ACI/OT` | `MCP73831T-2ACI/OT` | `Package_TO_SOT_SMD:SOT-23-5` | [C424093](https://www.lcsc.com/product-detail/C424093.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `Q1` | 1 | `AO3401A` | `AO3401A` | `Package_TO_SOT_SMD:SOT-23` | [C15127](https://www.lcsc.com/product-detail/C15127.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `D3` | 1 | `BAT54WS` | `BAT54WS` | `Diode_SMD:D_SOD-323` | [C5251553](https://www.lcsc.com/product-detail/C5251553.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `D_DM1, D_DP1` | 2 | `PESD5V0U1BL` | `PESD5V0U1BL` | `Diode_SMD:D_SOD-882` | [C53477426](https://www.lcsc.com/product-detail/C53477426.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `D_VBUS1` | 1 | `PESD5V0S1BL` | `PESD5V0S1BL,315` | `Diode_SMD:D_SOD-882` | [C84374](https://www.lcsc.com/product-detail/C84374.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `D1` | 1 | `LED_GREEN_0402` (GPIO48 status LED) | `19-217/GHC-YR1S2/3T` | `LED_SMD:LED_0402_1005Metric` | [C72043](https://www.lcsc.com/product-detail/C72043.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `SW1, SW2` | 2 | `TS-1088-AR02016` (`SW1` RESET, `SW2` BOOT) | `TS-1088-AR02016` | `esp32s3_glasses_cam:XUNPU_TS-1088-AR02016_3.0x2.0mm` | [C720477](https://www.lcsc.com/product-detail/C720477.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `L2` | 1 | `2.4nH` (RF placeholder) | `LQG15HS2N4S02D` | `Inductor_SMD:L_0402_1005Metric` | [C13607](https://www.lcsc.com/product-detail/C13607.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `C11, C12` | 2 | `1.5pF` (RF placeholder) | `GRM1555C1H1R5CA01D` | `Capacitor_SMD:C_0402_1005Metric` | [C76958](https://www.lcsc.com/product-detail/C76958.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `C_X1, C_X2` | 2 | `12pF` | `GRM1555C1H120JA01D` | `Capacitor_SMD:C_0402_1005Metric` | [C1547](https://www.lcsc.com/product-detail/C1547.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `C_1V2, C_2V8, C_PU1, C_SPI1, C_U2_OUT1, C_VSYS1` | 6 | `1uF` | `CL05A105KA5NQNC` | `Capacitor_SMD:C_0402_1005Metric` | [C52923](https://www.lcsc.com/product-detail/C52923.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `C_3V3_1, C_3V3_2, C_3V3_3` | 3 | `100nF` | `CL05B104KO5NNNC` | `Capacitor_SMD:C_0402_1005Metric` | [C1525](https://www.lcsc.com/product-detail/C1525.html) | `C_3V3_1` Top; `C_3V3_2, C_3V3_3` Bottom | NOT VERIFIED - owner to check |
| `C_3V3_B1` | 1 | `10uF` | `CL10A106KP8NNNC` | `Capacitor_SMD:C_0603_1608Metric` | [C19702](https://www.lcsc.com/product-detail/C19702.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `C_VBAT1, C_VBUS1` | 2 | `4.7uF` | `CL10A475KP8NNNC` | `Capacitor_SMD:C_0603_1608Metric` | [C1705](https://www.lcsc.com/product-detail/C1705.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `R_45, R_46, R_PROG1, R_PU1` | 4 | `10k` | `0402WGF1002TCE` | `Resistor_SMD:R_0402_1005Metric` | [C25744](https://www.lcsc.com/product-detail/C25744.html) | `R_45, R_46, R_PU1` Top; `R_PROG1` Bottom | NOT VERIFIED - owner to check |
| `R_GATE1` | 1 | `100k` | `0402WGF1003TCE` | `Resistor_SMD:R_0402_1005Metric` | [C25741](https://www.lcsc.com/product-detail/C25741.html) | Bottom (`B.Cu`) | NOT VERIFIED - owner to check |
| `R_CC1, R_CC2` | 2 | `5.1k` | `0402WGF5101TCE` | `Resistor_SMD:R_0402_1005Metric` | [C25905](https://www.lcsc.com/product-detail/C25905.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `R_SCL1, R_SDA1` | 2 | `4.7k` | `0402WGF4701TCE` | `Resistor_SMD:R_0402_1005Metric` | [C25900](https://www.lcsc.com/product-detail/C25900.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `R_USB1, R_USB2` | 2 | `22R` | `0402WGF220JTCE` | `Resistor_SMD:R_0402_1005Metric` | [C25092](https://www.lcsc.com/product-detail/C25092.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `R_LED1` | 1 | `1k` | `0402WGF1001TCE` | `Resistor_SMD:R_0402_1005Metric` | [C11702](https://www.lcsc.com/product-detail/C11702.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `D_PRIV1` | 1 | `LED_RED_PRIV_0402` (Hardware Privacy LED) | `19-217/R6C-AL1M2VY/3T` | `LED_SMD:LED_0402_1005Metric` | [C84256](https://www.lcsc.com/product-detail/C84256.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `R_SENSE1` | 1 | `470R` (Privacy LED sense pulldown) | `0402WGF4700TCE` | `Resistor_SMD:R_0402_1005Metric` | [C25117](https://www.lcsc.com/product-detail/C25117.html) | Top (`F.Cu`) | NOT VERIFIED - owner to check |
| `TP_VBAT1` | 1 | `VBAT+` wire pad (not assembled) | `TP_SMD` | `esp32s3_glasses_cam:WirePad_1.4x1.6mm` | DNP (not assembled) | Bottom (`B.Cu`) at `(45.00, 2.00)` | Hand-solder |
| `TP_GND1` | 1 | `VBAT-` wire pad (not assembled) | `TP_SMD` | `esp32s3_glasses_cam:WirePad_1.4x1.6mm` | DNP (not assembled) | Bottom (`B.Cu`) at `(52.10, 8.65)` | Hand-solder |
| `TP_CHG1` | 1 | `CHG_STAT` test pad (not assembled) | `TP_SMD` | `esp32s3_glasses_cam:TestPad_0.8x0.8mm` | DNP (not assembled) | Bottom (`B.Cu`) at `(47.54, 5.30)` | Test pad |

## 5. JLCPCB Assembly Preview Verification Notes (Recomputed PCB Coordinates)
All coordinates below are KiCad board coordinates `(X, Y)` in mm with `(0, 0)` at top-left. Check every orientation and polarity in the JLCPCB 3D/2D assembly preview before confirming your order:
1. **`U1` (`ESP32-S3FH4R2`, `F.Cu` at `(26.50, 4.50)`, rot `0`)**: Pad 1 (`LNA_IN`, `RF_ANT`) is at `(23.05, 1.90)` (top of left `-X` edge).
2. **`J2` (`TYPE-C-31-M-12`, `F.Cu` at `(56.50, 5.00)`, rot `0`)**: Both PCB and `CPL_JLCPCB.csv` use rotation `0` because the project library copy of `J2` is a pre-rotated version of the KiCad HRO footprint (not the unmodified KiCad library file), with all 16 SMD signal pads in one column at `x = 53.605 mm` and the receptacle mouth facing the `+X` board edge (`x = 60.0 mm`).
3. **Bottom-Side `SOT-23-5` & `SOT-23` Parts (`B.Cu`, rot `0`)**:
   - `U2` at `(36.80, 7.30)`: Pad 1 (`VSYS`) at `(35.663, 6.35)`, Pad 2 (`GND`) at `(35.663, 7.30)`, Pad 3 (`VSYS`) at `(35.663, 8.25)`, Pad 4 (NC) at `(37.938, 8.25)`, Pad 5 (`+3V3`) at `(37.938, 6.35)`.
   - `U3` at `(40.85, 7.30)`: Pad 1 (`+3V3`) at `(39.712, 6.35)`, Pad 2 (`GND`) at `(39.712, 7.30)`, Pad 3 (`PRIV_SENSE` EN) at `(39.712, 8.25)`, Pad 4 (NC) at `(41.987, 8.25)`, Pad 5 (`+2V8`) at `(41.987, 6.35)`.
   - `U4` at `(44.90, 7.30)`: Pad 1 (`+3V3`) at `(43.763, 6.35)`, Pad 2 (`GND`) at `(43.763, 7.30)`, Pad 3 (`PRIV_SENSE` EN) at `(43.763, 8.25)`, Pad 4 (NC) at `(46.038, 8.25)`, Pad 5 (`+1V2`) at `(46.038, 6.35)`.
   - `U5` (`MCP73831T-2ACI/OT`) at `(48.95, 7.30)`: Pad 1 (`CHG_STAT` / `STAT`) at `(47.812, 6.35)`, Pad 2 (`GND` / `VSS`) at `(47.812, 7.30)`, Pad 3 (`VBAT`) at `(47.812, 8.25)`, Pad 4 (`+5V_USB` / `VDD`) at `(50.087, 8.25)`, Pad 5 (`PROG_CHG` / `PROG`) at `(50.087, 6.35)`.
   - `Q1` (`AO3401A`) at `(52.20, 4.00)`: Pad 1 (Gate, `+5V_USB`) at `(51.263, 3.05)`, Pad 2 (Source, `VSYS`) at `(51.263, 4.95)`, Pad 3 (Drain, `VBAT`) at `(53.138, 4.00)`.
4. **Diodes (`B.Cu` & `F.Cu`, rot `0`)**:
   - `D3` (`BAT54WS`, `B.Cu` at `(53.40, 6.20)`): Pad 1 (Cathode, `VSYS`) at `(52.35, 6.20)`, Pad 2 (Anode, `+5V_USB`) at `(54.45, 6.20)`.
   - `D1` (`LED_GREEN_0402`, `F.Cu` at `(44.00, 4.20)`): Pad 1 (Cathode, `GND`) at `(43.52, 4.20)`, Pad 2 (Anode, `STATUS_LED_ANODE`) at `(44.48, 4.20)`, driven by `U1` Pad 36 (`GPIO48`, net `STATUS_LED`) through `R_LED1` (`1k` at `(41.00, 4.20)`).
   - `D_DP1` (`F.Cu` at `(51.62, 3.92)`): Pad 1 (`USB_DP_R`) at `(51.14, 3.92)`, Pad 2 (`GND`) at `(52.10, 3.92)`.
   - `D_DM1` (`F.Cu` at `(51.20, 7.05)`): Pad 1 (`USB_DM_R`) at `(50.72, 7.05)`, Pad 2 (`GND`) at `(51.68, 7.05)`.
   - `D_VBUS1` (`F.Cu` at `(52.30, 0.90)`): Pad 1 (`+5V_USB`) at `(51.82, 0.90)`, Pad 2 (`GND`) at `(52.78, 0.90)`.
5. **Remaining Bottom-Side (`B.Cu`) Passives**:
   - `R_GATE1` `(49.85, 1.45)`, `R_PROG1` `(48.95, 4.60)`, `C_3V3_2` `(32.50, 2.20)`, `C_3V3_3` `(32.50, 7.40)`, `C_3V3_B1` `(36.00, 4.20)`, `C_VBAT1` `(47.40, 1.80)`, `C_VBUS1` `(52.80, 1.80)`.

## 6. RF, USB & Power Routing Reference
- **RF Front-End (2.45 GHz)**:
  - `RF_ANT` (`U1` pad 1 `(23.05, 1.90)` -> `C11` -> `L2`): `1.66 mm` long, `0.22 - 0.25 mm` wide, `F.Cu` only, `0` vias.
  - `RF_MATCH` (`L2` -> `C12` -> `AE1` pad 2 `(3.65, 7.80)`): `37.73 mm` long, `0.30 - 0.35 mm` wide, `F.Cu` only, `0` vias.
  - Total RF route length: `39.39 mm` (~0.57 wavelength in FR4; straight-line distance from `U1` pad 1 to `AE1` pad 2 is ~20 mm due to detour routing), `0` vias, ~94% over the `In1.Cu` `GND` fill.
  - Impedance (IPC-2141 microstrip approximation over 0.21 mm prepreg, er = 4.5): ~49.5 ohm at `0.35 mm` width and ~54 ohm at `0.30 mm` width (approximate; confirm with the fab impedance calculator).
  - **VNA-Tuning Warning**: `C11` (`1.5 pF`), `L2` (`2.4 nH`), and `C12` (`1.5 pF`) are initial placeholder values; because the RF path is ~0.57 wavelength, retune the pi-network on a VNA using the assembled board inside its enclosure.
  - **Nearby `GND` Vias within 1.0 mm of the RF Line (8 of 35 total `GND` vias)**: `(1.05, 1.15)`, `(1.05, 2.20)`, `(4.35, 6.50)`, `(4.80, 6.80)`, `(14.05, 2.70)`, `(15.52, 3.25)`, `(18.10, 3.05)`, and `(21.68, 0.50)`.
- **USB 2.0 Full-Speed (12 Mb/s)**:
  - `D-`: `U1` pad 25 (`GPIO19`, net `USB_DM`, `27.59 mm`) -> `R_USB1` (`22R`) -> `USB_DM_R` (`6.84 mm`) -> `J2` pads `A7`/`B7`. Total `D-` = `34.43 mm`.
  - `D+`: `U1` pad 26 (`GPIO20`, net `USB_DP`, `31.39 mm`) -> `R_USB2` (`22R`) -> `USB_DP_R` (`6.12 mm`) -> `J2` pads `A6`/`B6`. Total `D+` = `37.50 mm`.
  - Length delta = `3.08 mm` (`3.07 - 3.08 mm` with rounding). Tracks are `0.13 mm` wide (`0.15 mm` on resistor stubs) and routed mostly on `In2.Cu` (which has no adjacent reference plane); acceptable for 12 Mb/s full-speed USB.
- **Power Tree**:
  - `J2` `+5V_USB` feeds `U5` (`MCP73831T-2ACI/OT`, `R_PROG1 = 10k` -> 100 mA charge) and `D3` (`BAT54WS`, anode `+5V_USB`, cathode `VSYS`).
  - `Q1` (`AO3401A` P-MOSFET, gate `+5V_USB` pulled down by `R_GATE1 = 100k`, source `VSYS`, drain `VBAT`) switches battery power onto `VSYS` when USB is unplugged.
  - `U2` (`TLV75733PDBVR`) generates `+3V3` from `VSYS`; `U3` (`ME6211C28M5G-N`) generates `+2V8` and `U4` (`ME6211C12M5G-N`) generates `+1V2` from `+3V3`.

## 7. Owner Checklist (Run in KiCad 10 Before Ordering)
1. Open `esp32s3_glasses_cam.kicad_pro` with `symbols/` and `footprints/` in the project folder. Run **Edit > Fill All Zones**.
2. Run **Inspect > ERC** (target 0 errors) and **Inspect > DRC** (with all severities as set in `.kicad_pro`), and save both reports.
3. Run **File > Plot** for all layers (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`, `F.Mask`, `B.Mask`, `F.Silkscreen`, `B.Silkscreen`, `F.Paste`, `B.Paste`, `Edge.Cuts`; enable **Check zone fills before plotting** and **Gerber X2**) and **Generate Drill Files** (Excellon, PTH + NPTH, oval holes as slots, map). Inspect in GerbView: `In1.Cu` shows the `GND` plane with the antenna notch, mask openings exist on every pad and the `J2` shield slots, and the `60 x 10 mm` outline is closed.
4. Compare `J1` (`AFC01-S24FCA-00`: contact side and pin-1 end vs your OV2640 flex cable), `AE1`, `Y1`, `SW1`/`SW2`, and `U1` footprints against their datasheets. Check every LCSC part number and live stock on `lcsc.com`.
5. Upload to JLCPCB and verify the 2D/3D assembly preview for rotation and polarity (`U1`, `J2`, `SOT-23` / `SOT-23-5` parts, and all bottom-side parts).

## 8. Hardware-Enforced Camera Privacy Interlock (Rev 2 Addition)
- **Circuit**: `U1` pad 37 (`GPIO47`, `CAM_PWR_EN`) -> `D_PRIV1` (`LED_RED_PRIV_0402`, `19-217/R6C-AL1M2VY/3T`, `C84256`, `Vf ~ 1.8 V`, `F.Cu` at `(42.90, 6.60)`) -> `PRIV_SENSE` -> `R_SENSE1` (`470R`, `0402WGF4700TCE`, `C25117`, `F.Cu` at `(42.90, 8.05)` to `GND`) + `U3` pad 3 (`+2V8` LDO `EN`) + `U4` pad 3 (`+1V2` LDO `EN`).
- **Behavior**:
  - Firmware sets `GPIO47` (`PIN_CAM_PWR_EN`) HIGH -> `~3.2 mA` flows through `D_PRIV1` -> `PRIV_SENSE` rises to `~1.5 V` (`> 1.2 V` `ME6211` `V_CEH`) -> both `+2V8` (`U3`) and `+1V2` (`U4`) camera rails turn ON.
  - Firmware cannot power the camera without lighting `D_PRIV1`, and if `D_PRIV1` is cut/desoldered/open, `R_SENSE1` pulls `PRIV_SENSE` to `0 V` and shuts off both camera rails.

## 9. Hand-Solder Audio (Speaker & Mic) Pads (I2S Bus)
Six hand-solder `TestPad_0.8x0.8mm` pads (`DNP` in BOM/CPL) are provided on `B.Cu` (clean underside for easy hand-soldering) for connecting an external down-firing speaker/amp (`MAX98357A`) and I2S MEMS mic (`INMP441` / `ICS-43434`). All 4 signal GPIOs (`GPIO38`–`GPIO37`) are free of embedded flash/PSRAM (`GPIO26`–`GPIO32`), strapping (`GPIO0/3/45/46`), and native USB (`GPIO19/20`):
- `TP_I2S_BCLK1`: `I2S_BCLK` (`U1` pin 43, `GPIO38`)
- `TP_I2S_LRC1`: `I2S_LRC` (`U1` pin 47, `GPIO41`)
- `TP_SPK_DOUT1`: `I2S_SPK_DOUT` (`U1` pin 38, `GPIO33`)
- `TP_MIC_SD1`: `I2S_MIC_SD` (`U1` pin 42, `GPIO37`)
- `TP_AUD_3V31`: `+3V3` audio rail tap
- `TP_AUD_GND1`: `GND` audio return tap
