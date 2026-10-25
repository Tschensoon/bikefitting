#!/usr/bin/env python3
"""
Bikefit-Analyse aus einem seitlichen Video.

Erkennt Koerperhaltung mit YOLO11x-Pose, misst Gelenkwinkel am unteren
Totpunkt (UTP) des Pedaltritts und bewertet sie gegen forschungsbasierte
Rennrad-Zielbereiche. Zeichnet ein farbiges Skelett (gruen/orange/rot) auf
das Video und schreibt einen kurzen Textbericht.

Quellen fuer die Zielbereiche:
- Holmes-Methode / Bini et al. (Knie 36+-7 Grad, Ellbogen 19+-8 Grad):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/
- Dynamische vs. statische Validitaet (+~8 Grad im Video vs. Goniometer):
  https://pubmed.ncbi.nlm.nih.gov/24499342/
- Praxis-Gegencheck Oberkoerper/Schulter/Huefte:
  https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles
"""

import argparse
import math
import statistics
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# COCO-17 Keypoint-Indizes (Ultralytics-Reihenfolge)
# ---------------------------------------------------------------------------
NOSE, L_EYE, R_EYE, L_EAR, R_EAR = 0, 1, 2, 3, 4
L_SHOULDER, R_SHOULDER = 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16

CONF_THRESH = 0.35

# ---------------------------------------------------------------------------
# Zielbereiche (grün) mit ca. 2.5 Grad Toleranz an den Rändern für die
# gelbe (grenzwertige) Zone. Alles außerhalb ist rot.
#
# Knie- und Ellbogenbeugung sind biomechanische Vorgaben (Sattelhöhe relativ
# zur Beinlänge bzw. Ellbogen-Federung), die unabhängig vom Radtyp gelten
# und daher in beiden Profilen identisch sind. Nur der Oberkörperwinkel
# unterscheidet sich bewusst zwischen aggressiver Rennrad-Position und der
# aufrechteren, komfortorientierten Gravel-/Endurance-Geometrie - dort ist
# ein höherer (aufrechterer) Winkel kein Fit-Fehler, sondern Absicht des
# Rahmens. Schulter- und Hüftwinkel bleiben mangels belastbarer
# gravel-spezifischer Quellen unverändert (siehe Quellenangaben im Bericht).
# ---------------------------------------------------------------------------
PROFILES = {
    "road": {
        "knee": {"green": (30, 40), "label": "Kniebeugung unten"},
        "torso": {"green": (40, 50), "label": "Oberkörper zur Horizontalen"},
        "elbow": {"green": (15, 30), "label": "Ellbogenbeugung"},
        "shoulder": {"green": (80, 95), "label": "Schulterwinkel"},
        "hip": {"green": (85, 110), "label": "Hüftwinkel oben (nur Info)"},
    },
    "gravel": {
        "knee": {"green": (30, 40), "label": "Kniebeugung unten"},
        "torso": {"green": (55, 70), "label": "Oberkörper zur Horizontalen (Gravel/Endurance)"},
        "elbow": {"green": (15, 30), "label": "Ellbogenbeugung"},
        "shoulder": {"green": (80, 95), "label": "Schulterwinkel"},
        "hip": {"green": (85, 110), "label": "Hüftwinkel oben (nur Info)"},
    },
}
RANGES = PROFILES["road"]  # wird in main() per --profile überschrieben
YELLOW_MARGIN = 2.5


def classify(value, key):
    lo, hi = RANGES[key]["green"]
    if lo <= value <= hi:
        return "green"
    if (lo - YELLOW_MARGIN) <= value <= (hi + YELLOW_MARGIN):
        return "yellow"
    return "red"


COLOR_BGR = {
    "green": (0, 200, 0),
    "yellow": (0, 165, 255),
    "red": (0, 0, 255),
    "gray": (140, 140, 140),
}


def flex(joint_angle):
    """
    Wandelt den geometrischen Gelenk-Innenwinkel in den in der Bikefit-Literatur
    üblichen Beugewinkel um (0° = Gelenk ganz gestreckt). Nur für Knie und
    Ellbogen nötig, da deren Zielbereiche (z.B. Holmes-Methode) als Beugung
    ab Streckung angegeben sind, nicht als Innenwinkel der Gliedmaßen.
    """
    return 180.0 - joint_angle


def angle_at(a, b, c):
    """Winkel am Punkt b, gebildet durch die Strahlen b->a und b->c, in Grad."""
    a, b, c = np.array(a, float), np.array(b, float), np.array(c, float)
    v1, v2 = a - b, c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return None
    cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return math.degrees(math.acos(cos_a))


def torso_to_horizontal(shoulder, hip):
    """Winkel der Rumpflinie (Hüfte->Schulter) zur horizontalen Ebene, Grad."""
    dx = shoulder[0] - hip[0]
    dy = shoulder[1] - hip[1]
    return math.degrees(math.atan2(abs(dy), abs(dx) + 1e-6))


class Pose:
    """Kapselt die 17 Keypoints (xy, conf) einer Person in einem Frame."""

    def __init__(self, xy, conf):
        self.xy = xy      # (17, 2)
        self.conf = conf  # (17,)

    def pt(self, idx):
        return self.xy[idx]

    def ok(self, idx, thresh=CONF_THRESH):
        return self.conf[idx] >= thresh

    def side_confidence(self, side):
        idxs = {
            "left": [L_SHOULDER, L_ELBOW, L_WRIST, L_HIP, L_KNEE, L_ANKLE],
            "right": [R_SHOULDER, R_ELBOW, R_WRIST, R_HIP, R_KNEE, R_ANKLE],
        }[side]
        return float(np.mean(self.conf[idxs]))


def side_indices(side):
    if side == "left":
        return dict(shoulder=L_SHOULDER, elbow=L_ELBOW, wrist=L_WRIST,
                    hip=L_HIP, knee=L_KNEE, ankle=L_ANKLE)
    return dict(shoulder=R_SHOULDER, elbow=R_ELBOW, wrist=R_WRIST,
                hip=R_HIP, knee=R_KNEE, ankle=R_ANKLE)


def compute_angles(pose: Pose, side: str):
    idx = side_indices(side)
    needed = [idx["shoulder"], idx["elbow"], idx["wrist"], idx["hip"], idx["knee"], idx["ankle"]]
    if not all(pose.ok(i) for i in needed):
        return None

    shoulder, elbow, wrist = pose.pt(idx["shoulder"]), pose.pt(idx["elbow"]), pose.pt(idx["wrist"])
    hip, knee, ankle = pose.pt(idx["hip"]), pose.pt(idx["knee"]), pose.pt(idx["ankle"])

    knee_angle = angle_at(hip, knee, ankle)
    elbow_angle = angle_at(shoulder, elbow, wrist)
    shoulder_angle = angle_at(hip, shoulder, elbow)
    hip_angle = angle_at(shoulder, hip, knee)
    torso_angle = torso_to_horizontal(shoulder, hip)

    if None in (knee_angle, elbow_angle, shoulder_angle, hip_angle):
        return None

    return {
        "knee": knee_angle,
        "elbow": elbow_angle,
        "shoulder": shoulder_angle,
        "hip": hip_angle,
        "torso": torso_angle,
        "points": idx,
    }


SKELETON_EDGES = [
    ("shoulder", "elbow", "arm"),
    ("elbow", "wrist", "arm"),
    ("shoulder", "hip", "torso"),
    ("hip", "knee", "knee"),
    ("knee", "ankle", "knee"),
]


def draw_skeleton(frame, pose: Pose, side: str, angle_result, seg_colors):
    idx = side_indices(side)
    pts = {name: tuple(int(v) for v in pose.pt(i)) for name, i in idx.items()}

    for a, b, seg in SKELETON_EDGES:
        color = COLOR_BGR.get(seg_colors.get(seg, "gray"), COLOR_BGR["gray"])
        cv2.line(frame, pts[a], pts[b], color, 4, cv2.LINE_AA)

    for name, p in pts.items():
        cv2.circle(frame, p, 5, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, p, 5, (30, 30, 30), 1, cv2.LINE_AA)

    return frame


def find_bottom_dead_centers(frames_data, min_gap_frames):
    """
    frames_data: list of dict(frame_idx, knee_angle) or None for missed frames.
    UTP = lokales Maximum des Kniewinkels (Bein am meisten gestreckt) waehrend
    echtem Treten. Peaks werden per einfacher lokaler Maximum-Suche mit
    Mindestabstand gefunden; kurze Ausreisser (kein durchgehendes Treten)
    werden durch den Mindestabstand und eine Plausibilitaetsspanne gefiltert.
    """
    idxs = [f["frame_idx"] for f in frames_data if f["knee"] is not None]
    vals = [f["knee"] for f in frames_data if f["knee"] is not None]
    if len(vals) < 5:
        return []

    peaks = []
    for i in range(1, len(vals) - 1):
        if vals[i] >= vals[i - 1] and vals[i] >= vals[i + 1] and vals[i] > 100:
            peaks.append((idxs[i], vals[i]))

    filtered = []
    for fi, v in peaks:
        if filtered and fi - filtered[-1][0] < min_gap_frames:
            if v > filtered[-1][1]:
                filtered[-1] = (fi, v)
            continue
        filtered.append((fi, v))

    return filtered


def reencode_h264(src_path: Path, dst_path: Path):
    cmd = [
        "ffmpeg", "-y", "-i", str(src_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(dst_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    global RANGES
    ap = argparse.ArgumentParser(description="Bikefit-Analyse aus seitlichem Video")
    ap.add_argument("video", type=str, help="Pfad zum Eingabevideo (seitliche Ansicht)")
    ap.add_argument("--outdir", type=str, default=str(Path(__file__).parent / "output"))
    ap.add_argument("--model", type=str, default="yolo11x-pose.pt")
    ap.add_argument("--device", type=str, default="cpu")
    ap.add_argument("--profile", type=str, choices=sorted(PROFILES), default="road",
                     help="Zielbereiche: 'road' (aggressive Rennradposition) oder "
                          "'gravel' (aufrechtere Gravel-/Endurance-Geometrie)")
    args = ap.parse_args()
    RANGES = PROFILES[args.profile]

    video_path = Path(args.video)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    video_info = sv.VideoInfo.from_video_path(str(video_path))
    fps = video_info.fps
    min_gap_frames = max(1, int(fps * 0.25))  # kein UTP-Doppeltreffer < 0.25s auseinander

    print(f"Lade Modell {args.model} ...")
    model = YOLO(args.model)

    print("Pass 1/2: Erkenne Personen & Gelenke, bestimme Körperseite ...")
    frames_generator = sv.get_video_frames_generator(str(video_path))

    raw_results = []   # pro Frame: Pose-Objekt oder None
    side_votes = {"left": 0.0, "right": 0.0}

    for frame in frames_generator:
        result = model.predict(frame, verbose=False, device=args.device)[0]
        pose = None
        if result.keypoints is not None and len(result.keypoints.xy) > 0:
            box_conf = result.boxes.conf.cpu().numpy() if result.boxes is not None else None
            if box_conf is not None and len(box_conf) > 0:
                best = int(np.argmax(box_conf))
            else:
                best = 0
            xy = result.keypoints.xy[best].cpu().numpy()
            conf = result.keypoints.conf[best].cpu().numpy() if result.keypoints.conf is not None else np.ones(len(xy))
            pose = Pose(xy, conf)
            side_votes["left"] += pose.side_confidence("left")
            side_votes["right"] += pose.side_confidence("right")
        raw_results.append(pose)

    side = "left" if side_votes["left"] >= side_votes["right"] else "right"
    print(f"Kamerazugewandte Seite erkannt: {side} "
          f"(Konfidenz-Summe links={side_votes['left']:.1f}, rechts={side_votes['right']:.1f})")

    print("Werte Kniewinkel-Verlauf aus, suche echte Trittzyklen ...")
    frames_data = []
    angle_cache = {}
    for i, pose in enumerate(raw_results):
        if pose is None:
            frames_data.append({"frame_idx": i, "knee": None})
            continue
        res = compute_angles(pose, side)
        angle_cache[i] = res
        frames_data.append({"frame_idx": i, "knee": res["knee"] if res else None})

    utp_candidates = find_bottom_dead_centers(frames_data, min_gap_frames)
    utp_frames_with_valid_angles = [
        fi for fi, _ in utp_candidates if angle_cache.get(fi) is not None
    ]

    if not utp_frames_with_valid_angles:
        print("FEHLER: Kein unterer Totpunkt mit gültigen Gelenkwinkeln gefunden. "
              "Ist im Video wirklich durchgehend seitlich getreten worden?")
        sys.exit(1)

    print(f"{len(utp_frames_with_valid_angles)} untere Totpunkte erkannt "
          f"(von {len(utp_candidates)} Kandidaten).")

    # "knee"/"elbow" werden hier von Gelenk-Innenwinkeln in Beugewinkel
    # (0° = gestreckt) umgerechnet, weil die Zielbereiche aus der Literatur
    # (Holmes-Methode) so definiert sind. Für die Suche nach dem unteren
    # Totpunkt oben wurde bewusst noch der rohe Innenwinkel verwendet.
    metrics = {k: [] for k in ("knee", "elbow", "shoulder", "hip", "torso")}
    for fi in utp_frames_with_valid_angles:
        res = angle_cache[fi]
        metrics["knee"].append(flex(res["knee"]))
        metrics["elbow"].append(flex(res["elbow"]))
        for k in ("shoulder", "hip", "torso"):
            metrics[k].append(res[k])

    medians = {k: statistics.median(v) for k, v in metrics.items()}
    classes = {k: classify(medians[k], k) for k in ("knee", "elbow", "shoulder", "torso")}
    classes["hip"] = classify(medians["hip"], "hip")

    rep_frame_idx = min(
        utp_frames_with_valid_angles,
        key=lambda fi: abs(flex(angle_cache[fi]["knee"]) - medians["knee"]),
    )

    print("\nPass 2/2: Zeichne farbiges Skelett auf gesamten Clip ...")
    frames_generator = sv.get_video_frames_generator(str(video_path))
    raw_out_path = outdir / "_annotated_raw.mp4"
    still_path = outdir / "utp_standbild.jpg"

    with sv.VideoSink(str(raw_out_path), video_info=video_info) as sink:
        for i, frame in enumerate(frames_generator):
            pose = raw_results[i]
            annotated = frame.copy()
            if pose is not None:
                res = angle_cache.get(i)
                if res is not None:
                    arm_color = worse_of(classify(res["shoulder"], "shoulder"), classify(flex(res["elbow"]), "elbow"))
                    seg_colors = {
                        "arm": arm_color,
                        "torso": classify(res["torso"], "torso"),
                        "knee": classify(flex(res["knee"]), "knee"),
                    }
                else:
                    seg_colors = {"arm": "gray", "torso": "gray", "knee": "gray"}
                annotated = draw_skeleton(annotated, pose, side, res, seg_colors)

            if i == rep_frame_idx:
                cv2.imwrite(str(still_path), annotated)

            sink.write_frame(annotated)

    print("Re-encode nach H.264 ...")
    final_video_path = outdir / "bikefit_annotated.mp4"
    reencode_h264(raw_out_path, final_video_path)
    raw_out_path.unlink(missing_ok=True)

    report_path = outdir / "bikefit_report.txt"
    write_report(report_path, medians, classes, side, len(utp_frames_with_valid_angles), args.profile)

    print(f"\nFertig.\nVideo:   {final_video_path}\nBild:    {still_path}\nBericht: {report_path}")


def worse_of(status_a, status_b):
    order = {"green": 0, "yellow": 1, "red": 2}
    return status_a if order[status_a] >= order[status_b] else status_b


def write_report(path: Path, medians, classes, side, n_utp, profile):
    lines = []
    lines.append("BIKEFIT-ANALYSE – ZUSAMMENFASSUNG")
    lines.append("=" * 40)
    profile_label = {"road": "Rennrad (aggressive Position)",
                      "gravel": "Gravel/Endurance (aufrechtere Position)"}[profile]
    lines.append(f"Profil: {profile_label}")
    lines.append(f"Ausgewertete Körperseite (kamerazugewandt): {side}")
    lines.append(f"Anzahl ausgewerteter unterer Totpunkte: {n_utp}")
    lines.append("")

    def fmt(key):
        lo, hi = RANGES[key]["green"]
        label = RANGES[key]["label"]
        val = medians[key]
        status = classes[key]
        tag = {"green": "OK", "yellow": "GRENZWERTIG", "red": "KORRIGIEREN"}[status]
        return f"{label}: {val:.1f}° (Zielbereich grün {lo}-{hi}°) -> {tag}"

    for key in ("knee", "torso", "elbow", "shoulder", "hip"):
        lines.append(fmt(key))

    lines.append("")
    lines.append("EMPFEHLUNGEN")
    lines.append("-" * 40)

    knee = medians["knee"]
    if classes["knee"] == "red" and knee > RANGES["knee"]["green"][1]:
        mm = round((knee - RANGES["knee"]["green"][1]) * 3)
        lines.append(f"- Knie {knee:.0f}° unten (zu stark gebeugt) -> Sattel zu tief. "
                      f"Sattel ca. {max(mm,5)}-{max(mm,5)+5}mm höher stellen.")
    elif classes["knee"] == "red" and knee < RANGES["knee"]["green"][0]:
        mm = round((RANGES["knee"]["green"][0] - knee) * 3)
        lines.append(f"- Knie {knee:.0f}° unten (zu gestreckt) -> Sattel zu hoch. "
                      f"Sattel ca. {max(mm,5)}-{max(mm,5)+5}mm tiefer stellen.")
    elif classes["knee"] == "yellow":
        lines.append(f"- Knie {knee:.0f}° unten liegt an der Grenze des Zielbereichs "
                      f"({RANGES['knee']['green'][0]}-{RANGES['knee']['green'][1]}°). "
                      f"Kleine Sattelhöhen-Korrektur (ca. 3-5mm) in Erwägung ziehen.")
    else:
        lines.append(f"- Knie {knee:.0f}° unten liegt im grünen Bereich. Sattelhöhe passt.")

    shoulder = medians["shoulder"]
    elbow = medians["elbow"]
    if classes["shoulder"] == "red" and shoulder < RANGES["shoulder"]["green"][0]:
        lines.append(f"- Schulterwinkel {shoulder:.0f}° deutlich niedriger als der Zielbereich "
                      f"({RANGES['shoulder']['green'][0]}-{RANGES['shoulder']['green'][1]}°) "
                      f"-> geschlossenes, gestauchtes Cockpit. Reichweite vergrößern "
                      f"(längerer Vorbau, ca. 10-20mm) oder Sattel etwas nach hinten.")
    elif classes["shoulder"] != "green":
        lines.append(f"- Schulterwinkel {shoulder:.0f}° ist grenzwertig, im Auge behalten.")
    else:
        lines.append(f"- Schulterwinkel {shoulder:.0f}° liegt im grünen Bereich.")

    if classes["elbow"] == "red" and elbow < RANGES["elbow"]["green"][0]:
        lines.append(f"- Ellbogen {elbow:.0f}° sehr wenig gebeugt (durchgestreckt) -> "
                      f"oft zu viel Gewicht auf den Händen. Reichweite/Vorbaulänge prüfen "
                      f"oder Lenkerposition (Bremsgriffe) anpassen.")
    elif classes["elbow"] == "red" and elbow > RANGES["elbow"]["green"][1]:
        lines.append(f"- Ellbogen {elbow:.0f}° stark gebeugt -> Cockpit evtl. zu kurz oder "
                      f"Sattel zu weit vorne. Reichweite prüfen.")
    elif classes["elbow"] == "yellow":
        lines.append(f"- Ellbogen {elbow:.0f}° ist grenzwertig.")

    torso = medians["torso"]
    if classes["torso"] != "green":
        lines.append(f"- Oberkörperwinkel {torso:.0f}° zur Horizontalen ist "
                      f"{'zu flach/aggressiv' if torso < RANGES['torso']['green'][0] else 'zu aufrecht'}; "
                      f"hängt oft mit Sattel-/Lenkerhöhe und Reichweite zusammen.")

    lines.append("")
    lines.append(f"Hüftwinkel oben {medians['hip']:.0f}° (nur Info, hängt von Beweglichkeit ab, "
                  f"Zielbereich ca. {RANGES['hip']['green'][0]}-{RANGES['hip']['green'][1]}°).")

    lines.append("")
    lines.append("Quellen: Holmes-Methode / Bini et al. (PMC9219349), dynamische vs. statische")
    lines.append("Validität (PMID 24499342), Bikefit Adviser Praxis-Gegencheck.")
    if profile == "gravel":
        lines.append("Oberkörper-Zielbereich Gravel/Endurance: abgeleitet aus Pedalyze")
        lines.append("Road-Bike-Fit-Referenz (Endurance am oberen Ende des Toleranzbereichs)")
        lines.append("und allgemeinem Konsens zu Endurance-/Gravel-Geometrie (road.cc, CT Yeh).")
        lines.append("Weniger streng belegt als die übrigen (Knie/Ellbogen unverändert zum")
        lines.append("Rennrad-Profil, da radtyp-unabhängig).")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
