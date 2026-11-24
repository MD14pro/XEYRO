// ============================================================================
// Ultra-Slim Universal Clip-On Smart Glasses Pod (Parametric OpenSCAD — v1.1)
// ============================================================================
// Rear-Tail USB-C Inline Layout (Matches J2 orientation on +X edge of PCB!):
//   - Outer Thickness:  7.4 mm  (inline LiPo + PCB, NOT stacked side-by-side!)
//   - Outer Height:    12.8 mm  (matches standard Wayfarer temple height)
//   - Total Length:   103.0 mm  (balanced weight from hinge to behind-ear tail)
// Internal Inline Order (Front -> Rear):
//   - Front (Y = 1.2..7.4 mm):   OV2640 lens bore (Ø 6.6 mm) + Privacy LED bore (Ø 2.2 mm)
//   - Mid   (Y = 8.5..39.5 mm):  Inline 401030 1S LiPo (30x10x4.0 mm) + inner 0.6 mm FPC channel
//                                (use standard 75 mm long-FPC OV2640 module to reach J1!)
//   - Rear  (Y = 41.0..101.0 mm): esp32s3_glasses_cam PCB (60x10x1.6 mm), SW1/SW2, D1,
//                                 and J2 USB-C exiting cleanly straight out the REAR TAIL (+Y)!
// Clip Mount:
//   - Two low-profile compliant C-clips on inner (-X) face that snap onto any glasses arm
// ============================================================================

/* [View & Print Mode] */
view_mode = "assembled"; // [assembled, exploded, print_layout]
show_electronics = true;

/* [Target Glasses Temple Arm Fit (Adjust to Your Glasses!)] */
arm_thickness     = 3.0;   // Thickness of your existing glasses temple arm (2.0..5.5 mm)
arm_height        = 7.0;   // Vertical height of your existing glasses temple arm (4.0..11.0 mm)
clip_wall         = 1.4;   // Flexible C-clip wall thickness (print in PETG / Nylon PA12 / Tough Resin)

/* [Ultra-Slim Pod Outer Dimensions (Inline Layout)] */
pod_thickness     = 7.4;   // Slim protrusion (fits 1.6mm PCB + components + walls)
pod_height        = 12.8;  // Matches normal temple height
pod_length        = 103.0; // Total streamlined length
wall_outer        = 1.1;
wall_cover        = 0.9;
fillet_r          = 1.6;

/* [Internal Component Dimensions (Exact PCB & LiPo)] */
lipo_len          = 30.5;  // 401030 1S LiPo (30 x 10 x 4.0 mm) in middle bay
lipo_h            = 10.0;
lipo_thk          = 4.2;
lipo_y_start      = 8.5;

pcb_len           = 60.0;  // esp32s3_glasses_cam PCB in rear bay (J2 at rear +Y tail!)
pcb_h             = 10.0;
pcb_thk           = 1.6;
pcb_y_start       = 41.0;

spk_y_start       = 22.0;  // Down-firing linear speaker grille slots under mid bay

// Exact PCB feature offsets along Y (from pcb_y_start = 41.0 mm):
sw2_boot_x        = 42.0;  // SW2 BOOT  (Y = 83.0 mm)
sw1_rst_x         = 47.0;  // SW1 RESET (Y = 88.0 mm)
d1_led_x          = 44.0;  // D1 Status LED (Y = 85.0 mm)

$fn = 48;

module rounded_box(w, d, h, r=1.4) {
    hull() {
        for (sx = [-1, 1], sy = [-1, 1], sz = [-1, 1]) {
            translate([sx*(w/2 - r), sy*(d/2 - r), sz*(h/2 - r)])
                sphere(r=r, $fn=20);
        }
    }
}

// ============================================================================
// 1. MAIN SLIM CLIP-ON POD SHELL (Rear-Tail USB-C + Compliant C-Clips)
// ============================================================================
module clipon_pod_body() {
    difference() {
        union() {
            hull() {
                // Front camera nose
                translate([pod_thickness/2, 4.0, 0])
                    rounded_box(pod_thickness, 8.0, pod_height - 0.6, r=fillet_r);
                // Main LiPo + PCB body
                translate([pod_thickness/2, 52.0, 0])
                    rounded_box(pod_thickness, 88.0, pod_height, r=fillet_r);
                // Rear tail housing J2 USB-C receptacle (flat rear face for clean USB-C plug entry)
                translate([pod_thickness/2, pod_length - 4.0, 0])
                    rounded_box(pod_thickness, 8.0, pod_height - 1.0, r=1.2);
            }

            // Two Low-Profile Compliant C-Clips on Inner Face (X < 0)
            for (cy = [22.0, 64.0]) {
                translate([0, cy, 0])
                    temple_c_clip(clip_len=11.0);
            }
        }

        // --- INTERNAL CAVITIES (Open on inner X=0 face for easy assembly) ---
        cav_w = pod_thickness - wall_outer + 0.5;

        // 1. Front OV2640 Camera Pocket (8.8 x 6.2 x 8.8 mm)
        translate([-0.5, 1.2, -4.4])
            cube([cav_w, 6.2, 8.8]);

        // Front Camera Lens Aperture (Ø 6.6 mm, facing -Y)
        translate([pod_thickness/2 + 0.2, 0.0, -0.8])
        rotate([90, 0, 0])
            cylinder(h=6.0, d=6.6, center=true);

        // Front Privacy LED Light-Pipe Bore (Ø 2.2 mm, directly above lens)
        translate([pod_thickness/2 + 0.2, 0.0, 3.8])
        rotate([90, 0, 0])
            cylinder(h=6.0, d=2.2, center=true);

        // 2. Inline 1S LiPo Bay in Middle (Y = 8.2..39.7 mm)
        translate([-0.5, lipo_y_start - 0.3, -5.3])
            cube([cav_w, lipo_len + 1.0, lipo_h + 0.6]);

        // Inner 0.8 mm OV2640 Long-FPC + Wire Pass-Through Channel (front -> rear PCB J1)
        translate([-0.5, 6.5, -4.5])
            cube([1.6, pcb_y_start + 12.0, 9.0]);

        // 3. Main ESP32-S3 PCB Bay in Rear (Y = 40.7..101.7 mm)
        translate([-0.5, pcb_y_start - 0.3, -5.3])
            cube([cav_w, pcb_len + 1.0, pcb_h + 0.6]);

        // 4. Local J2 USB-C 3.16 mm height clearance + REAR TAIL (+Y) USB-C Cutout!
        translate([-0.5, pod_length - 10.5, -4.6])
            cube([pod_thickness - 0.5, 10.0, 9.2]);
        // Clean Rear-End USB-C Port Opening (3.6 x 9.4 mm, facing +Y — matches J2 on PCB!)
        translate([pod_thickness/2, pod_length, 0])
            cube([3.8, 6.0, 9.6], center=true);

        // 5. Tactile Button Pin-Holes (SW1 RESET & SW2 BOOT) on top edge (+Z)
        for (bx = [sw2_boot_x, sw1_rst_x]) {
            translate([pod_thickness/2, pcb_y_start + bx, pod_height/2])
                cylinder(h=4.0, d=2.0, center=true);
        }

        // 6. Status LED Window (D1 GPIO48) on outer face (+X)
        translate([pod_thickness, pcb_y_start + d1_led_x, 0.8])
        rotate([0, 90, 0])
            cylinder(h=4.0, d=1.5, center=true);

        // 7. Down-Firing Linear Speaker Grille Slots at bottom (-Z)
        for (i = [0 : 4]) {
            translate([pod_thickness/2, spk_y_start + i*2.5, -pod_height/2 + 0.4])
                cube([2.8, 1.2, 3.0], center=true);
        }

        // 7b. Engraved XEYRO Logo on Outer +X Temple Face (0.35 mm deep, Y = 45..66 mm)
        translate([pod_thickness - 0.15, 45.0, 0.0])
            xeyro_logo_engrave(depth=0.35, scale_f=0.95);

        // 8. Flush Inner Snap-Cover Recess (0.9 mm deep)
        translate([-0.1, 4.0, -5.7])
            cube([wall_cover + 0.1, pod_length - 9.0, 11.4]);
    }
}

module temple_c_clip(clip_len=11.0) {
    outer_x = arm_thickness + clip_wall;
    outer_z = arm_height + 2*clip_wall;
    difference() {
        translate([-outer_x/2, 0, 0])
            rounded_box(outer_x + 1.0, clip_len, outer_z, r=0.8);
        translate([-arm_thickness/2 - 0.1, 0, 0])
            cube([arm_thickness + 0.2, clip_len + 1.0, arm_height], center=true);
        translate([-arm_thickness/2 - 0.1, 0, -outer_z/2])
            cube([arm_thickness - 0.5, clip_len + 1.0, clip_wall*2.2], center=true);
    }
}

module clipon_inner_cover() {
    difference() {
        translate([wall_cover/2, 4.0 + (pod_length - 9.0)/2, 0])
            rounded_box(wall_cover, pod_length - 9.4, 11.2, r=0.35);
        for (sy = [9.0, pod_length - 8.5]) {
            translate([wall_cover/2, sy, 0])
            rotate([0, 90, 0])
                cylinder(h=3.0, d=1.3, center=true);
        }
    }
}

module electronics_mockup() {
    // OV2640 Camera Module (Front)
    color([0.15, 0.15, 0.18])
        translate([pod_thickness/2, 4.2, -0.5])
            cube([5.2, 5.5, 8.2], center=true);
    // Inline 401030 1S LiPo (Mid)
    color([0.78, 0.65, 0.2, 0.9])
        translate([3.6, lipo_y_start + lipo_len/2, 0])
            cube([lipo_thk, lipo_len, lipo_h], center=true);
    // ESP32-S3 Main PCB (Rear, J2 USB-C at +Y tail!)
    color([0.1, 0.48, 0.22, 0.85])
        translate([3.2, pcb_y_start + pcb_len/2, 0])
            cube([pcb_thk, pcb_len, pcb_h], center=true);
}

if (view_mode == "assembled") {
    clipon_pod_body();
    color([0.2, 0.2, 0.22, 0.6]) clipon_inner_cover();
    if (show_electronics) electronics_mockup();
} else if (view_mode == "exploded") {
    clipon_pod_body();
    translate([-10, 0, 0]) clipon_inner_cover();
    if (show_electronics) translate([10, 0, 0]) electronics_mockup();
} else if (view_mode == "print_layout") {
    rotate([0, -90, 0]) clipon_pod_body();
    translate([20, 0, 0]) rotate([0, 90, 0]) clipon_inner_cover();
}

// ============================================================================
// XEYRO FINAL LOCKED VISOR LOGO (Tight Chamfered Visor + Deep Nose Notch + Red LED Dot + Italic XEYRO)
// ============================================================================
module xeyro_stroke_2d(p1, p2, w=0.45) {
    hull() {
        translate(p1) circle(d=w, $fn=16);
        translate(p2) circle(d=w, $fn=16);
    }
}

module xeyro_logo_2d(scale_f=1.0) {
    // Pure vector 2D geometry (font-independent!)
    // Total bounding box: ~21.0 mm wide x 6.8 mm tall (at scale_f=1.0), centered in Z
    s = scale_f;
    w_fr  = 0.72 * s;
    w_txt = 0.52 * s;

    // 1. Tight Chamfered Visor Frame + Deep Flat-Top Trapezoidal Nose-Bridge Notch (x = 0..21.0, y = -3.3..+3.3)
    // Top-right chamfer break reserved for the privacy LED dot
    difference() {
        union() {
            // Top bar
            xeyro_stroke_2d([1.4*s,  3.2*s], [19.6*s,  3.2*s], w_fr);
            // Top-right 45-deg chamfer
            xeyro_stroke_2d([19.6*s,  3.2*s], [21.0*s,  1.8*s], w_fr);
            // Right wall
            xeyro_stroke_2d([21.0*s,  1.8*s], [21.0*s, -1.8*s], w_fr);
            // Bottom-right chamfer
            xeyro_stroke_2d([21.0*s, -1.8*s], [19.6*s, -3.2*s], w_fr);
            // Bottom-right bar -> deep nose-bridge notch -> bottom-left bar
            xeyro_stroke_2d([19.6*s, -3.2*s], [12.4*s, -3.2*s], w_fr);
            xeyro_stroke_2d([12.4*s, -3.2*s], [11.2*s, -1.45*s], w_fr);
            xeyro_stroke_2d([11.2*s, -1.45*s], [10.3*s, -1.45*s], w_fr);
            xeyro_stroke_2d([10.3*s, -1.45*s], [ 9.1*s, -3.2*s], w_fr);
            xeyro_stroke_2d([ 9.1*s, -3.2*s], [ 1.4*s, -3.2*s], w_fr);
            // Bottom-left chamfer, left wall, top-left chamfer
            xeyro_stroke_2d([ 1.4*s, -3.2*s], [ 0.0*s, -1.8*s], w_fr);
            xeyro_stroke_2d([ 0.0*s, -1.8*s], [ 0.0*s,  1.8*s], w_fr);
            xeyro_stroke_2d([ 0.0*s,  1.8*s], [ 1.4*s,  3.2*s], w_fr);
        }
        // Clean halo break on top-right chamfer for the signature privacy LED dot
        translate([20.3*s, 2.5*s]) circle(r=0.72*s, $fn=24);
    }
    // Signature Privacy LED Dot
    translate([20.3*s, 2.5*s]) circle(r=0.40*s, $fn=24);

    // 2. Centered Italic 'XEYRO' Wordmark with Full Inverted-Lambda 'Y' (x = 2.6..18.4, y = -1.4..+1.5)
    translate([0.0, 0.25*s])
    multmatrix([[1, 0.36, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) {
        // X
        xeyro_stroke_2d([ 2.6*s,  1.45*s], [ 5.0*s, -1.35*s], w_txt);
        xeyro_stroke_2d([ 5.0*s,  1.45*s], [ 2.6*s, -1.35*s], w_txt);
        // E
        xeyro_stroke_2d([ 6.0*s,  1.45*s], [ 8.1*s,  1.45*s], w_txt);
        xeyro_stroke_2d([ 6.0*s,  1.45*s], [ 6.0*s, -1.35*s], w_txt);
        xeyro_stroke_2d([ 6.0*s,  0.05*s], [ 7.7*s,  0.05*s], w_txt);
        xeyro_stroke_2d([ 6.0*s, -1.35*s], [ 8.1*s, -1.35*s], w_txt);
        // Y (Inverted-Lambda: full continuous diagonal tail floating cleanly beside nose notch)
        xeyro_stroke_2d([11.3*s,  1.45*s], [ 8.7*s, -2.05*s], w_txt);
        xeyro_stroke_2d([ 9.3*s,  1.45*s], [10.1*s,  0.10*s], w_txt);
        // R
        xeyro_stroke_2d([12.3*s,  1.45*s], [12.3*s, -1.35*s], w_txt);
        xeyro_stroke_2d([12.3*s,  1.45*s], [14.2*s,  1.45*s], w_txt);
        xeyro_stroke_2d([14.2*s,  1.45*s], [14.2*s,  0.05*s], w_txt);
        xeyro_stroke_2d([14.2*s,  0.05*s], [12.3*s,  0.05*s], w_txt);
        xeyro_stroke_2d([13.3*s,  0.05*s], [14.4*s, -1.35*s], w_txt);
        // O
        xeyro_stroke_2d([15.6*s,  1.45*s], [17.9*s,  1.45*s], w_txt);
        xeyro_stroke_2d([17.9*s,  1.45*s], [17.9*s, -1.35*s], w_txt);
        xeyro_stroke_2d([17.9*s, -1.35*s], [15.6*s, -1.35*s], w_txt);
        xeyro_stroke_2d([15.6*s, -1.35*s], [15.6*s,  1.45*s], w_txt);
    }
}

module xeyro_logo_engrave(depth=0.35, scale_f=0.95) {
    rotate([90, 0, 90])
        linear_extrude(height=depth + 0.4, center=true)
            xeyro_logo_2d(scale_f=scale_f);
}
