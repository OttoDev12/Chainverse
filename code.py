import subprocess
import re

FFMPEG_CORE_JS = "https://unpkg.com/@ffmpeg/core@0.10.0/dist/ffmpeg-core.js"
FFMPEG_JS = "https://cdn.jsdelivr.net/npm/@ffmpeg/ffmpeg@0.10.1/dist/ffmpeg.min.js"
UPLOAD_FILE = "path/to/file"

def transcode():
    do_transcode(UPLOAD_FILE)

def do_transcode(file):
    # get video info
    info = subprocess.check_output(f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height,avg_frame_rate -of csv=p=0 {file}", shell=True)
    width, height, fps = re.search(r'(\d+),(\d+),(\d+/\d+)', info.decode()).groups()
    width, height, fps = int(width), int(height), eval(fps)

    # prepare ffmpeg command
    bitrate_table = [
        {"width": 1920, "height": 1080, "rate": 6600000, "tag": "1080p"},
        {"width": 1280, "height": 720, "rate": 3300000, "tag": "720p"},
        {"width": 640, "height": 480, "rate": 1100000, "tag": "480p"},
        {"width": 480, "height": 360, "rate": 600000, "tag": "360p"},
        {"width": 256, "height": 144, "rate": 200000, "tag": "144p"},
    ]
    bitrate_table = list(filter(lambda e: e["width"] <= width and e["height"] <= height, bitrate_table))
    bitrate_table = list(map(lambda e: {"width": e["width"], "height": e["height"], "rate": e["rate"] * 1.5 if fps > 30 else e["rate"], "tag": e["tag"]}, bitrate_table))

    # build arguments
    args = ["-i", file]
    if fps > 60:
        args.extend(["-r", "60"])
    args.extend(["-force_key_frames", "expr:gte(t,n_forced*2)", "-sc_threshold", "0"])

    if not info_audio:
        args.extend(["-c:v", "libx264", "-crf", "22"])
        for idx, item in enumerate(bitrate_table):
            args.extend([
                "-map", f"0:v:0",
                "-filter:v:{idx}", f"scale=w={item['width']}:h={item['height']}",
                "-maxrate:v:{idx}", str(item['rate']),
                f"name:{item['tag']}",
            ])
        var_stream_map = ",".join(map(lambda x: f"v:{x['tag']}", bitrate_table))
        args.extend(["-var_stream_map", var_stream_map])
    else:
        args.extend(["-c:v", "libx264", "-crf", "22", "-c:a", "aac", "-ar", "48000"])
        for idx, item in enumerate(bitrate_table):
            args.extend([
                "-map", f"0:v:0", "-map", f"0:a:0",
                "-filter:v:{idx}", f"scale=w={item['width']}:h={item['height']}",
                "-maxrate:v:{idx}", str(item['rate']), "-b:a:{idx}", "128k",
                f"name:{item['tag']}",
            ])
        var_stream_map = ",".join(map(lambda x
