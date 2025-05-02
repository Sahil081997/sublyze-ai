import srt
from datetime import timedelta
import os
import numpy as np
from PIL import Image, ImageDraw
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip


def format_timestamp(seconds):
    return timedelta(seconds=float(seconds))


def generate_srt(chunks):
    subtitles = []
    for i, chunk in enumerate(chunks):
        start = format_timestamp(chunk["timestamp"][0])
        end = format_timestamp(chunk["timestamp"][1])
        content = chunk["text"].strip()
        if not content:
            continue
        subtitles.append(srt.Subtitle(index=i + 1, start=start, end=end, content=content))
    return srt.compose(subtitles)


def save_srt(srt_text, path="output.srt"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(srt_text)
    return path


def burn_subtitles_to_video(video_path, chunks, output_path="sublyze_subtitled.mp4", fontsize=24, color="#FFFFFF", bg_color=None, bg_opacity=1.0):
    video = VideoFileClip(video_path)
    subtitle_clips = []

    for chunk in chunks:
        start, end = chunk["timestamp"]
        txt = chunk["text"].strip()
        if not txt:
            continue

        lines = txt.split("\n") if "\n" in txt else [txt]
        total_lines = len(lines)

        for idx, line in enumerate(lines):
            y_offset = -((total_lines - 1) * fontsize) // 2 + (idx * fontsize)
            position_y = video.h - 100 + y_offset

            # Text clip
            txt_clip = TextClip(
                line,
                fontsize=fontsize,
                color=color,
                font="DejaVu-Sans",
                method="pillow",
                size=(int(video.w * 0.8), None),
                align='center'
            ).set_position(("center", position_y)).set_start(start).set_end(end)

            # Background with rounded corners if bg_color is set
            if bg_color:
                bg_width, bg_height = txt_clip.size
                bg_image = Image.new("RGBA", (bg_width + 20, bg_height + 10), (0, 0, 0, 0))
                draw = ImageDraw.Draw(bg_image)
                radius = 12
                fill = tuple(int(bg_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (int(bg_opacity * 255),)
                draw.rounded_rectangle(
                    [(0, 0), bg_image.size],
                    radius=radius,
                    fill=fill
                )

                bg_clip = ImageClip(np.array(bg_image)).set_position(txt_clip.pos).set_start(start).set_end(end)
                subtitle_clips.append(bg_clip)

            subtitle_clips.append(txt_clip)

    final = CompositeVideoClip([video] + subtitle_clips)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path
