import cv2
import os
import re

# === CONFIG ===
VIDEO_DIR = "videos"                  # folder with your .mp4 files
OUTPUT_BASE = "data/images"           # will save to Armflapping/, Headbanging/, Spinning/
FRAME_SKIP = 3                        # extract every 3rd frame (change to 5 or 10 if too many files)
FPS_DEFAULT = 30                      # fallback FPS if video metadata fails

# Create output folders
for cls in ["Armflapping", "Headbanging", "Spinning"]:
    os.makedirs(os.path.join(OUTPUT_BASE, cls), exist_ok=True)

# === FULL TIMESTAMPS DICT (padded to two digits) ===
timestamps = {
    "01": (18, 24),
    "02": (10, 20),
    "03": (20, 25),
    "04": (60, 70),
    "05": (2, 14),
    "06": (27, 30),
    "07": (4, 10),
    "08": (18, 22),
    "09": (5, 15),
    "10": (68, 85),
    "11": (60, 67),
    "12": (131, 155),
    "13": (40, 50),
    "14": (3, 7),
    "15": (17, 23),
    "16": (32, 46),
    "17": (2, 10),
    "18": (3, 8),
    "19": (175, 190),
    "20": (94, 98),
    "21": (12, 16),
    "22": (2, 6),
    "23": (49, 57),
    "24": (10, 15),
    "25": (4, 8),
    "26": (1, 4),
    "27": (4, 9),
    "28": (6, 14),
    "29": (16, 30),
    "30": (3, 17),
    "31": (10, 19),
    "32": (55, 64),
    "33": (85, 95),
    "34": (2, 10),
    "35": (16, 22),
    "36": (36, 39),
    "37": (2, 12),
    "38": (2, 20),
    "39": (4, 15),
    "40": (1, 23),
    "41": (10, 17),
    "42": (2, 20),
    "43": (1, 10),
    "44": (30, 40),
    "45": (1, 7),
    "46": (20, 44),
    "47": (19, 26),
    "48": (5, 10),
    "49": (3, 10),
    "50": (1, 7),
    "51": (68, 83),
    "52": (10, 20),
    "53": (10, 15),
    "54": (1, 70),
    "55": (2, 15),
    "56": (1, 20),
    "57": (6, 18),
    "58": (2, 59),
    "59": (4, 12),
    "60": (2, 15),
    "61": (3, 10),
    "62": (2, 35),
    "63": (1, 24),
    "64": (51, 58),
    "65": (1, 10),
    "66": (6, 12),
    "67": (2, 15),
    "68": (1, 47),
    "69": (56, 63),
    "70": (2, 9),
    "71": (2, 20),
    "72": (2, 7),
    "73": (1, 25),
    "74": (26, 43),
    "75": (25, 28),
}

# === MAIN EXTRACTION ===
video_files = [f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(('.mp4', '.avi', '.mov'))]

for video_file in video_files:
    video_path = os.path.join(VIDEO_DIR, video_file)
    base_name = os.path.splitext(video_file)[0]  # e.g. armflapping_01, v_ArmFlapping_05, headbanging_26

    # Extract the last 1-2 digits from filename
    match = re.search(r'(\d{1,2})$', base_name)
    if not match:
        print(f"Skipping {video_file} - no number found at end of name")
        continue

    num_str = match.group(1).zfill(2)  # "1" → "01", "5" → "05", "26" → "26"

    if num_str not in timestamps:
        print(f"Skipping {video_file} - no timestamp for number {num_str}")
        continue

    start_sec, end_sec = timestamps[num_str]

    # Determine class robustly
    base_lower = base_name.lower()
    if "arm" in base_lower and "flap" in base_lower:
        cls = "Armflapping"
    elif "head" in base_lower and "bang" in base_lower:
        cls = "Headbanging"
    elif "spin" in base_lower:
        cls = "Spinning"
    else:
        print(f"Skipping {video_file} - unknown class (cannot detect Armflapping/Headbanging/Spinning)")
        continue

    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Cannot open {video_file}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 120:  # sanity check
            fps = FPS_DEFAULT
        print(f"Processing {video_file} | FPS: {fps:.1f} | Class: {cls} | Time: {start_sec}-{end_sec}s")

        start_frame = max(0, int(start_sec * fps))
        end_frame = int(end_sec * fps)

        frame_count = 0
        extracted = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame_count > end_frame:
                break

            if frame_count >= start_frame and (frame_count - start_frame) % FRAME_SKIP == 0:
                out_filename = f"{base_name}_frame_{extracted:05d}.jpg"
                out_path = os.path.join(OUTPUT_BASE, cls, out_filename)
                cv2.imwrite(out_path, frame)
                extracted += 1

            frame_count += 1

        print(f" → Extracted {extracted} frames to {cls}/")

    except Exception as e:
        print(f"Error processing {video_file}: {e}")
    finally:
        if cap is not None:
            cap.release()

print("Extraction complete!")
# ─── NORMAL VIDEOS EXTRACTION (full duration) ───
normal_dir = "videos/normal"
if os.path.exists(normal_dir):
    cls = "Normal"
    normal_output = os.path.join(OUTPUT_BASE, cls)
    os.makedirs(normal_output, exist_ok=True)
    normal_files = [f for f in os.listdir(normal_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
    for video_file in normal_files:
        video_path = os.path.join(normal_dir, video_file)
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Cannot open normal video {video_file}")
                continue
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = FPS_DEFAULT
            print(f"Processing normal {video_file} | FPS: {fps:.1f}")
            frame_count = 0
            extracted = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % FRAME_SKIP == 0:  # Same skip as autistic videos
                    out_filename = f"{os.path.splitext(video_file)[0]}_frame_{extracted:05d}.jpg"
                    out_path = os.path.join(normal_output, out_filename)
                    cv2.imwrite(out_path, frame)
                    extracted += 1
                frame_count += 1
            print(f" → Extracted {extracted} normal frames from {video_file}")
        except Exception as e:
            print(f"Error extracting {video_file}: {e}")
        finally:
            if cap is not None:
                cap.release()
else:
    print("No 'videos/normal' folder found — skipping normal extraction")