#!/usr/bin/env python3
"""
Own Geometry & Schematic-to-PCB Parity Checker for esp32s3_glasses_cam.
IMPORTANT: This is an independent Python geometry/netlist checker, NOT KiCad DRC/ERC.
KiCad ERC, DRC, zone fill, and Gerber/Drill plotting MUST be run by the owner in KiCad 10.
"""
import os, re, csv, json, math, sys
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB_PATH = os.path.join(PROJECT_DIR, "esp32s3_glasses_cam.kicad_pcb")
SCH_PATH = os.path.join(PROJECT_DIR, "esp32s3_glasses_cam.kicad_sch")
PRO_PATH = os.path.join(PROJECT_DIR, "esp32s3_glasses_cam.kicad_pro")
BOM_PATH = os.path.join(PROJECT_DIR, "BOM_JLCPCB.csv")
CPL_PATH = os.path.join(PROJECT_DIR, "CPL_JLCPCB.csv")

def seg_seg_dist(x1, y1, x2, y2, x3, y3, x4, y4):
    def orient(ax, ay, bx, by, cx, cy):
        return (bx - ax)*(cy - ay) - (by - ay)*(cx - ax)
    def on_seg(ax, ay, bx, by, cx, cy):
        return min(ax, bx) - 1e-9 <= cx <= max(ax, bx) + 1e-9 and min(ay, by) - 1e-9 <= cy <= max(ay, by) + 1e-9
    o1 = orient(x1, y1, x2, y2, x3, y3)
    o2 = orient(x1, y1, x2, y2, x4, y4)
    o3 = orient(x3, y3, x4, y4, x1, y1)
    o4 = orient(x3, y3, x4, y4, x2, y2)
    if ((o1 * o2 < 0 and o3 * o4 < 0) or
        (abs(o1) < 1e-9 and on_seg(x1, y1, x2, y2, x3, y3)) or
        (abs(o2) < 1e-9 and on_seg(x1, y1, x2, y2, x4, y4)) or
        (abs(o3) < 1e-9 and on_seg(x3, y3, x4, y4, x1, y1)) or
        (abs(o4) < 1e-9 and on_seg(x3, y3, x4, y4, x2, y2))):
        return 0.0
    def pt_seg(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax)*dx + (py - ay)*dy) / (dx*dx + dy*dy)))
        return math.hypot(px - (ax + t*dx), py - (ay + t*dy))
    return min(pt_seg(x1, y1, x3, y3, x4, y4),
               pt_seg(x2, y2, x3, y3, x4, y4),
               pt_seg(x3, y3, x1, y1, x2, y2),
               pt_seg(x4, y4, x1, y1, x2, y2))

def seg_rect_dist(x1, y1, x2, y2, rx, ry, rsx, rsy):
    hx, hy = rsx / 2.0, rsy / 2.0
    if abs(x1 - rx) <= hx and abs(y1 - ry) <= hy: return 0.0
    if abs(x2 - rx) <= hx and abs(y2 - ry) <= hy: return 0.0
    corners = [(rx - hx, ry - hy), (rx + hx, ry - hy), (rx + hx, ry + hy), (rx - hx, ry + hy)]
    edges = [(corners[0], corners[1]), (corners[1], corners[2]), (corners[2], corners[3]), (corners[3], corners[0])]
    return min(seg_seg_dist(x1, y1, x2, y2, e[0][0], e[0][1], e[1][0], e[1][1]) for e in edges)

def rect_rect_dist(x1, y1, sx1, sy1, x2, y2, sx2, sy2):
    dx = max(0.0, abs(x1 - x2) - (sx1 + sx2)/2.0)
    dy = max(0.0, abs(y1 - y2) - (sy1 + sy2)/2.0)
    return math.hypot(dx, dy)

def get_footprint_spans(text):
    spans = []
    for m in re.finditer(r'(?m)^[ \t]*\(footprint\s+"', text):
        start = text.find("(footprint", m.start())
        depth, i, n, in_str = 0, start, len(text), False
        while i < n:
            ch = text[i]
            if ch == '"' and (i == 0 or text[i-1] != '\\'):
                in_str = not in_str
            elif not in_str:
                if ch == '(': depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        spans.append((start, i + 1))
                        break
            i += 1
    return spans

def main():
    with open(PCB_PATH, "r", encoding="utf-8") as f:
        pcb = f.read()
    with open(SCH_PATH, "r", encoding="utf-8") as f:
        sch = f.read()
    with open(PRO_PATH, "r", encoding="utf-8") as f:
        pro = json.load(f)

    ver = re.search(r'\(version\s+(\d+)\)', pcb).group(1)
    gen = re.search(r'\(generator_version\s+"([^"]+)"\)', pcb).group(1)
    nets = {int(m.group(1)): m.group(2) for m in re.finditer(r'^\s*\(net\s+(\d+)\s+"([^"]*)"\)', pcb, re.M)}
    n2id = {v: k for k, v in nets.items()}

    spans = get_footprint_spans(pcb)
    footprints, pads = [], []
    for s, e in spans:
        fp = pcb[s:e]
        fplink = re.match(r'\(footprint\s+"([^"]+)"', fp).group(1)
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', fp).group(1)
        val = re.search(r'\(property\s+"Value"\s+"([^"]+)"', fp).group(1)
        layer = re.search(r'\(layer\s+"([^"]+)"\)', fp).group(1)
        at_m = re.search(r'^\s*\(footprint\s+"[^"]+"\s+[\s\S]*?\(at\s+([\d\.-]+)\s+([\d\.-]+)(?:\s+([\d\.-]+))?\)', fp)
        fx, fy, frot = float(at_m.group(1)), float(at_m.group(2)), float(at_m.group(3) or 0.0)
        rad = math.radians(frot)
        fp_pads = []
        for line in fp.splitlines():
            if "(pad " not in line: continue
            pm = re.search(r'\(pad\s+"([^"]*)"\s+(\S+)\s+(\S+)\s+\(at\s+([\d\.-]+)\s+([\d\.-]+)(?:\s+([\d\.-]+))?\)\s+\(size\s+([\d\.-]+)\s+([\d\.-]+)\)(.*?)\(layers\s+([^\)]+)\)(.*)', line)
            if not pm: continue
            pnum, ptype, pshape, lx, ly, prot, sx, sy, mid_drill, players, rest = pm.groups()
            lx, ly, sx, sy = float(lx), float(ly), float(sx), float(sy)
            gx = round(fx + lx*math.cos(rad) + ly*math.sin(rad), 4)
            gy = round(fy - lx*math.sin(rad) + ly*math.cos(rad), 4)
            gsx, gsy = (sy, sx) if int(round(frot)) % 180 == 90 else (sx, sy)
            m_net = re.search(r'\(net\s+(\d+)\s+"([^"]*)"\)', rest)
            nid = int(m_net.group(1)) if m_net else 0
            nname = m_net.group(2) if m_net else ""
            pobj = {"ref": ref, "pin": pnum, "type": ptype, "x": gx, "y": gy, "sx": gsx, "sy": gsy, "net": nid, "net_name": nname, "layers": players}
            pads.append(pobj)
            fp_pads.append(pobj)
        footprints.append({"ref": ref, "val": val, "fplink": fplink, "layer": layer, "x": fx, "y": fy, "rot": frot, "pads": fp_pads})

    segs = []
    for sm in re.finditer(r'\(segment\s+\(start\s+([\d\.-]+)\s+([\d\.-]+)\)\s+\(end\s+([\d\.-]+)\s+([\d\.-]+)\)\s+\(width\s+([\d\.-]+)\)\s+\(layer\s+"([^"]+)"\)\s+\(net\s+(\d+)\)\s+\(uuid\s+"([^"]+)"\)\)', pcb):
        x1, y1, x2, y2, w, lyr, nid, uid = sm.groups()
        segs.append({"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2), "w": float(w), "layer": lyr, "net": int(nid), "uuid": uid})

    vias = []
    for vm in re.finditer(r'\(via\s+\(at\s+([\d\.-]+)\s+([\d\.-]+)\)\s+\(size\s+([\d\.-]+)\)\s+\(drill\s+([\d\.-]+)\).*?\(net\s+(\d+)\)', pcb):
        vx, vy, vs, vd, nid = vm.groups()
        vias.append({"x": float(vx), "y": float(vy), "size": float(vs), "drill": float(vd), "net": int(nid)})

    # 1. Clearances & shorts (< 0.127 mm)
    min_clr, min_pair, violations, shorts = 999.0, None, [], []
    for i in range(len(segs)):
        s1 = segs[i]
        for j in range(i+1, len(segs)):
            s2 = segs[j]
            if s1["layer"] != s2["layer"] or s1["net"] == s2["net"]: continue
            if max(s1["x1"], s1["x2"]) + 0.8 < min(s2["x1"], s2["x2"]) or max(s2["x1"], s2["x2"]) + 0.8 < min(s1["x1"], s1["x2"]): continue
            d = seg_seg_dist(s1["x1"], s1["y1"], s1["x2"], s1["y2"], s2["x1"], s2["y1"], s2["x2"], s2["y2"]) - (s1["w"]+s2["w"])/2.0
            if d < min_clr: min_clr, min_pair = d, ("seg-seg", s1["layer"], nets[s1["net"]], nets[s2["net"]], round(d, 4))
            if d < 0.127: violations.append(("seg-seg", s1["layer"], nets[s1["net"]], nets[s2["net"]], round(d, 4)))
            if d < 0.0: shorts.append(("seg-seg", s1["layer"], nets[s1["net"]], nets[s2["net"]], round(d, 4)))
    for i in range(len(pads)):
        p1 = pads[i]
        if p1["type"] == "np_thru_hole" or p1["net"] == 0: continue
        for j in range(i+1, len(pads)):
            p2 = pads[j]
            if p2["type"] == "np_thru_hole" or p2["net"] == 0 or p1["net"] == p2["net"] or p1["ref"] == p2["ref"]: continue
            if ("F.Cu" in p1["layers"] and "F.Cu" in p2["layers"]) or ("B.Cu" in p1["layers"] and "B.Cu" in p2["layers"]) or ("*" in p1["layers"]) or ("*" in p2["layers"]):
                d = rect_rect_dist(p1["x"], p1["y"], p1["sx"], p1["sy"], p2["x"], p2["y"], p2["sx"], p2["sy"])
                if d < min_clr: min_clr, min_pair = d, ("pad-pad", f"{p1['ref']}.{p1['pin']}({p1['net_name']})", f"{p2['ref']}.{p2['pin']}({p2['net_name']})", round(d, 4))
                if d < 0.127: violations.append(("pad-pad", f"{p1['ref']}.{p1['pin']}", f"{p2['ref']}.{p2['pin']}", round(d, 4)))
                if d < 0.0: shorts.append(("pad-pad", f"{p1['ref']}.{p1['pin']}", f"{p2['ref']}.{p2['pin']}", round(d, 4)))
    for s in segs:
        for p in pads:
            if p["type"] == "np_thru_hole" or p["net"] == 0 or s["net"] == p["net"]: continue
            if s["layer"] not in p["layers"] and "*" not in p["layers"]: continue
            d = seg_rect_dist(s["x1"], s["y1"], s["x2"], s["y2"], p["x"], p["y"], p["sx"], p["sy"]) - s["w"]/2.0
            if d < min_clr: min_clr, min_pair = d, ("seg-pad", s["layer"], nets[s["net"]], f"{p['ref']}.{p['pin']}({p['net_name']})", round(d, 4))
            if d < 0.127: violations.append(("seg-pad", s["layer"], nets[s["net"]], f"{p['ref']}.{p['pin']}", round(d, 4)))
            if d < 0.0: shorts.append(("seg-pad", s["layer"], nets[s["net"]], f"{p['ref']}.{p['pin']}", round(d, 4)))
    for v in vias:
        for p in pads:
            if p["type"] == "np_thru_hole" or p["net"] == 0 or v["net"] == p["net"]: continue
            d = seg_rect_dist(v["x"], v["y"], v["x"], v["y"], p["x"], p["y"], p["sx"], p["sy"]) - v["size"]/2.0
            if d < min_clr: min_clr, min_pair = d, ("via-pad", (v["x"], v["y"]), f"{p['ref']}.{p['pin']}({p['net_name']})", round(d, 4))
            if d < 0.127: violations.append(("via-pad", (v["x"], v["y"]), f"{p['ref']}.{p['pin']}", round(d, 4)))
            if d < 0.0: shorts.append(("via-pad", (v["x"], v["y"]), f"{p['ref']}.{p['pin']}", round(d, 4)))
    for v in vias:
        for s in segs:
            if v["net"] == s["net"]: continue
            d = seg_seg_dist(v["x"], v["y"], v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"]) - (v["size"]+s["w"])/2.0
            if d < min_clr: min_clr, min_pair = d, ("via-seg", (v["x"], v["y"]), s["layer"], nets[s["net"]], round(d, 4))
            if d < 0.127: violations.append(("via-seg", (v["x"], v["y"]), s["layer"], nets[s["net"]], round(d, 4)))
            if d < 0.0: shorts.append(("via-seg", (v["x"], v["y"]), s["layer"], nets[s["net"]], round(d, 4)))

    # 2. Connectivity (opens) via union-find per net (GND vias connect via In1.Cu GND zone)
    opens = []
    for nid, nname in nets.items():
        if nid == 0: continue
        npads = [p for p in pads if p["net"] == nid]
        if len(npads) <= 1: continue
        nsegs = [s for s in segs if s["net"] == nid]
        nvias = [v for v in vias if v["net"] == nid]
        items = [("pad", p) for p in npads] + [("seg", s) for s in nsegs] + [("via", v) for v in nvias]
        parent = list(range(len(items)))
        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb: parent[ra] = rb
        # On GND (net 1), all vias and through-hole pads connect to the In1.Cu GND zone
        if nid == 1:
            g_indices = [idx for idx, (t, obj) in enumerate(items) if t == "via" or (t == "pad" and obj["type"] == "thru_hole")]
            for gi in g_indices[1:]:
                union(g_indices[0], gi)
        for i in range(len(items)):
            t1, o1 = items[i]
            for j in range(i+1, len(items)):
                t2, o2 = items[j]
                conn = False
                if t1 == "seg" and t2 == "seg" and o1["layer"] == o2["layer"]:
                    if seg_seg_dist(o1["x1"], o1["y1"], o1["x2"], o1["y2"], o2["x1"], o2["y1"], o2["x2"], o2["y2"]) <= (o1["w"]+o2["w"])/2.0 + 1e-3:
                        conn = True
                elif (t1 == "seg" and t2 == "pad") or (t1 == "pad" and t2 == "seg"):
                    s, p = (o1, o2) if t1 == "seg" else (o2, o1)
                    if s["layer"] in p["layers"] or "*" in p["layers"]:
                        if seg_rect_dist(s["x1"], s["y1"], s["x2"], s["y2"], p["x"], p["y"], p["sx"], p["sy"]) <= s["w"]/2.0 + 1e-3:
                            conn = True
                elif (t1 == "seg" and t2 == "via") or (t1 == "via" and t2 == "seg"):
                    s, v = (o1, o2) if t1 == "seg" else (o2, o1)
                    if seg_seg_dist(v["x"], v["y"], v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"]) <= (v["size"]+s["w"])/2.0 + 1e-3:
                        conn = True
                elif (t1 == "pad" and t2 == "via") or (t1 == "via" and t2 == "pad"):
                    p, v = (o1, o2) if t1 == "pad" else (o2, o1)
                    if seg_rect_dist(v["x"], v["y"], v["x"], v["y"], p["x"], p["y"], p["sx"], p["sy"]) <= v["size"]/2.0 + 1e-3:
                        conn = True
                elif t1 == "pad" and t2 == "pad":
                    if ("F.Cu" in o1["layers"] and "F.Cu" in o2["layers"]) or ("B.Cu" in o1["layers"] and "B.Cu" in o2["layers"]) or ("*" in o1["layers"]) or ("*" in o2["layers"]):
                        if rect_rect_dist(o1["x"], o1["y"], o1["sx"], o1["sy"], o2["x"], o2["y"], o2["sx"], o2["sy"]) <= 1e-3:
                            conn = True
                if conn:
                    union(i, j)
        pad_roots = set(find(i) for i in range(len(npads)))
        if len(pad_roots) > 1:
            opens.append((nid, nname, len(pad_roots)))

    # 3. Dangling track endpoints
    dangling = []
    for idx_s, s in enumerate(segs):
        for ex, ey in [(s["x1"], s["y1"]), (s["x2"], s["y2"])]:
            anchored = False
            for idx_s2, s2 in enumerate(segs):
                if idx_s == idx_s2 or s["layer"] != s2["layer"] or s["net"] != s2["net"]: continue
                if seg_seg_dist(ex, ey, ex, ey, s2["x1"], s2["y1"], s2["x2"], s2["y2"]) < 1e-3:
                    anchored = True; break
            if anchored: continue
            for v in vias:
                if v["net"] == s["net"] and math.hypot(ex - v["x"], ey - v["y"]) <= v["size"]/2.0 + 1e-3:
                    anchored = True; break
            if anchored: continue
            for p in pads:
                if p["net"] == s["net"] and (s["layer"] in p["layers"] or "*" in p["layers"]):
                    if abs(ex - p["x"]) <= p["sx"]/2.0 + 1e-3 and abs(ey - p["y"]) <= p["sy"]/2.0 + 1e-3:
                        anchored = True; break
            if not anchored:
                dangling.append((s["layer"], nets[s["net"]], (ex, ey)))

    # 4. Copper-to-edge clearance (board 0..60 x 0..10)
    min_edge = 999.0
    for v in vias:
        r = v["size"] / 2.0
        min_edge = min(min_edge, v["x"] - r, 60.0 - (v["x"] + r), v["y"] - r, 10.0 - (v["y"] + r))
    for s in segs:
        r = s["w"] / 2.0
        for px, py in [(s["x1"], s["y1"]), (s["x2"], s["y2"])]:
            min_edge = min(min_edge, px - r, 60.0 - (px + r), py - r, 10.0 - (py + r))

    # 5. Via-in-pad (via center inside SMD pad rectangle)
    via_in_pads = []
    for v in vias:
        for p in pads:
            if p["type"] != "smd": continue
            if abs(v["x"] - p["x"]) <= p["sx"]/2.0 + 1e-4 and abs(v["y"] - p["y"]) <= p["sy"]/2.0 + 1e-4:
                via_in_pads.append((f"{p['ref']}.{p['pin']}", (v["x"], v["y"])))

    # 6. Antenna keepout (x 0..3.3, y 5.5..10.0)
    ko_vias = [v for v in vias if 0.0 <= v["x"] <= 3.3 and 5.5 <= v["y"] <= 10.0]
    ko_segs = [s for s in segs if (0.0 <= s["x1"] < 3.3 and 5.5 <= s["y1"] <= 10.0) or (0.0 <= s["x2"] < 3.3 and 5.5 <= s["y2"] <= 10.0)]

    # 7. RF path & GND vias within 1.0 mm edge-to-edge (or 1.15 mm center-to-center)
    rf_ant_segs = [s for s in segs if s["net"] == n2id["RF_ANT"]]
    rf_match_segs = [s for s in segs if s["net"] == n2id["RF_MATCH"]]
    rf_all_segs = rf_ant_segs + rf_match_segs
    rf_vias = [v for v in vias if v["net"] in (n2id["RF_ANT"], n2id["RF_MATCH"])]
    rf_ant_len = sum(math.hypot(s["x2"]-s["x1"], s["y2"]-s["y1"]) for s in rf_ant_segs)
    rf_match_len = sum(math.hypot(s["x2"]-s["x1"], s["y2"]-s["y1"]) for s in rf_match_segs)
    gnd_vias = [v for v in vias if v["net"] == 1]
    rf_near_gnd = []
    for v in gnd_vias:
        md = min(seg_seg_dist(v["x"], v["y"], v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"]) - s["w"]/2.0 - v["size"]/2.0 for s in rf_all_segs)
        if md <= 1.0:
            rf_near_gnd.append((round(v["x"], 2), round(v["y"], 2)))
    rf_near_gnd.sort()

    # 8. Schematic-to-PCB pin parity
    # Map schematic global labels connected to symbol pins via wires
    lib_end = sch.find("\n  (symbol (lib_id")
    lib_part, inst_part = sch[:lib_end], sch[lib_end:]
    sym_pins = {}
    for m in re.finditer(r'\(symbol\s+"Custom:([^"]+)"([\s\S]*?)(?=\n    \(symbol\s+"Custom:|\n  \)\s*$)', lib_part):
        sname, body = m.group(1), m.group(2)
        pins_xy = []
        for pm in re.finditer(r'\(pin\s+\w+\s+\w+\s+\(at\s+([\d\.-]+)\s+([\d\.-]+)\s+[\d\.-]+\)[\s\S]*?\(number\s+"([^"]+)"', body):
            pins_xy.append((pm.group(3), float(pm.group(1)), float(pm.group(2))))
        sym_pins[sname] = pins_xy
    wires = []
    for wm in re.finditer(r'\(wire\s+\(pts\s+\(xy\s+([\d\.-]+)\s+([\d\.-]+)\)\s+\(xy\s+([\d\.-]+)\s+([\d\.-]+)\)\)', inst_part):
        wires.append((round(float(wm.group(1)), 2), round(float(wm.group(2)), 2), round(float(wm.group(3)), 2), round(float(wm.group(4)), 2)))
    glabels = {}
    for gm in re.finditer(r'\(global_label\s+"([^"]+)"[\s\S]*?\(at\s+([\d\.-]+)\s+([\d\.-]+)\s+[\d\.-]+\)', inst_part):
        glabels[(round(float(gm.group(2)), 2), round(float(gm.group(3)), 2))] = gm.group(1)
    wire_adj = defaultdict(list)
    for x1, y1, x2, y2 in wires:
        wire_adj[(x1, y1)].append((x2, y2))
        wire_adj[(x2, y2)].append((x1, y1))
    sch_pin_nets = {}
    for sm in re.finditer(r'\(symbol\s+\(lib_id\s+"Custom:([^"]+)"\)\s+\(at\s+([\d\.-]+)\s+([\d\.-]+)\s+0\)[\s\S]*?\(property\s+"Reference"\s+"([^"]+)"', inst_part):
        sname, sx, sy, sref = sm.group(1), float(sm.group(2)), float(sm.group(3)), sm.group(4)
        for pnum, px, py in sym_pins.get(sname, []):
            wx, wy = round(sx + px, 2), round(sy - py, 2)
            net_found = glabels.get((wx, wy), "")
            if not net_found:
                for nx, ny in wire_adj.get((wx, wy), []):
                    if (nx, ny) in glabels:
                        net_found = glabels[(nx, ny)]
                        break
            sch_pin_nets[(sref, pnum)] = net_found
    pcb_pin_nets = {(p["ref"], p["pin"]): p["net_name"] for p in pads if p["type"] != "np_thru_hole" and p["pin"] != ""}
    parity_checked = 0
    parity_mismatches = []
    for key, pnet in pcb_pin_nets.items():
        if key in sch_pin_nets:
            parity_checked += 1
            if sch_pin_nets[key] != pnet:
                parity_mismatches.append((key, sch_pin_nets[key], pnet))

    # 9. Power track widths
    pwr_widths = {}
    for pn in ["VBAT", "VSYS", "+5V_USB", "+3V3", "+2V8", "+1V2"]:
        ws = sorted(set(s["w"] for s in segs if s["net"] == n2id[pn]))
        pwr_widths[pn] = ws

    # 10. USB lengths
    usb_lens = {un: sum(math.hypot(s["x2"]-s["x1"], s["y2"]-s["y1"]) for s in segs if s["net"] == n2id[un]) for un in ["USB_DP", "USB_DP_R", "USB_DM", "USB_DM_R"]}

    # 11. Via sizes
    via_sizes = defaultdict(int)
    for v in vias:
        via_sizes[(v["size"], v["drill"])] += 1

    print("========================================================================")
    print("OWN GEOMETRY & PARITY CHECKER OUTPUT (NOT KiCad DRC / NOT KiCad ERC)")
    print("========================================================================")
    print(f"PCB format version      : {ver} (generator_version {gen})")
    print(f"PCB counts              : {len(footprints)} footprints, {len(segs)} segments, {len(vias)} vias")
    print(f"Via size breakdown      : {dict(via_sizes)}")
    print(f"Clearance violations    : {len(violations)} (rule >= 0.127 mm)")
    print(f"Minimum clearance       : {min_clr:.4f} mm -> {min_pair}")
    print(f"Shorts (< 0 mm)         : {len(shorts)}")
    print(f"Opens (unconnected)     : {len(opens)} {opens}")
    print(f"Dangling track ends     : {len(dangling)} {dangling}")
    print(f"Min copper-to-edge      : {min_edge:.4f} mm (rule >= 0.250 mm)")
    print(f"Via-in-pad (center in)  : {len(via_in_pads)} -> {via_in_pads}")
    print(f"Antenna keepout items   : {len(ko_vias)} vias, {len(ko_segs)} segments inside (0..3.3, 5.5..10.0)")
    print(f"RF_ANT                  : {rf_ant_len:.2f} mm, widths={sorted(set(s['w'] for s in rf_ant_segs))} mm, layers={sorted(set(s['layer'] for s in rf_ant_segs))}")
    print(f"RF_MATCH                : {rf_match_len:.2f} mm, widths={sorted(set(s['w'] for s in rf_match_segs))} mm, layers={sorted(set(s['layer'] for s in rf_match_segs))}")
    print(f"RF total                : {rf_ant_len + rf_match_len:.2f} mm, vias={len(rf_vias)}")
    print(f"GND vias near RF (<=1mm): {len(rf_near_gnd)} of {len(gnd_vias)} -> {rf_near_gnd}")
    print(f"USB D+ total            : {usb_lens['USB_DP']:.2f} + {usb_lens['USB_DP_R']:.2f} = {usb_lens['USB_DP']+usb_lens['USB_DP_R']:.2f} mm")
    print(f"USB D- total            : {usb_lens['USB_DM']:.2f} + {usb_lens['USB_DM_R']:.2f} = {usb_lens['USB_DM']+usb_lens['USB_DM_R']:.2f} mm")
    print(f"USB delta               : {abs((usb_lens['USB_DP']+usb_lens['USB_DP_R'])-(usb_lens['USB_DM']+usb_lens['USB_DM_R'])):.2f} mm")
    print(f"Power track widths (mm) : {pwr_widths}")
    print(f"Schematic <-> PCB parity: {parity_checked} pins checked, {len(parity_mismatches)} mismatches {parity_mismatches}")
    print(f"KiCad ERC / DRC / Plot  : NOT VERIFIED (owner must run in KiCad 10)")

if __name__ == "__main__":
    main()
