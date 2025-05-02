# import srt
# from datetime import timedelta
# import os
# # from moviepy.config import change_settings
# from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip
# import numpy as np
# from PIL import Image, ImageDraw

# # change_settings({
# #     "IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"
# # })

# def format_timestamp(seconds):
#     return timedelta(seconds=float(seconds))

# def generate_srt(chunks):
#     subtitles = []
#     for i, chunk in enumerate(chunks):
#         start = format_timestamp(chunk["timestamp"][0])
#         end = format_timestamp(chunk["timestamp"][1])
#         content = chunk["text"].strip()
#         if not content:
#             continue

#         subtitles.append(
#             srt.Subtitle(index=i + 1, start=start, end=end, content=content)
#         )
#     return srt.compose(subtitles)

# def save_srt(srt_text, path="output.srt"):
#     with open(path, "w", encoding="utf-8") as f:
#         f.write(srt_text)
#     return path

# def burn_subtitles_to_video(
#     video_path,
#     chunks,
#     output_path="sublyze_subtitled.mp4",
#     fontsize=16,
#     color="#ffffff",
#     bg_color="#000000",
#     bg_opacity=0.5,
#     position="bottom"
# ):
#     video = VideoFileClip(video_path)
#     subtitle_clips = []
#     padding = 10
#     radius = 15

#     for chunk in chunks:
#         start, end = chunk["timestamp"]
#         txt = chunk["text"].strip()
#         if not txt:
#             continue

#         lines = txt.split("\n") if "\n" in txt else [txt]
#         total_lines = len(lines)

#         for idx, line in enumerate(lines):
#             y_offset = -((total_lines - 1) * fontsize) // 2 + (idx * fontsize)

#             if position == "top":
#                 position_y = 100 + y_offset
#             elif position == "middle":
#                 position_y = video.h // 2 + y_offset
#             else:  # bottom
#                 position_y = video.h - 100 + y_offset

#             subtitle = TextClip(
#                 line,
#                 fontsize=fontsize,
#                 color=color,
#                 font="DejaVu-Sans",
#                 method="pillow",
#                 size=(int(video.w * 0.8), None),
#                 align='center'
#             ).set_position(("center", position_y)).set_start(start).set_end(end)

#             if bg_color:
#                 bg_width, bg_height = subtitle.size
#                 img = Image.new("RGBA", (bg_width + padding * 2, bg_height + padding * 2), (0, 0, 0, 0))
#                 draw = ImageDraw.Draw(img)

#                 bg_rgb = tuple(int(bg_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
#                 if bg_rgb == (0, 0, 0):
#                     bg_rgb = (1, 1, 1)

#                 bg_rgba = bg_rgb + (int(255 * bg_opacity),)
#                 draw.rounded_rectangle([(0, 0), (img.size[0], img.size[1])], radius=radius, fill=bg_rgba)
#                 np_img = np.array(img)

#                 bg_clip = ImageClip(np_img, transparent=True).set_position(("center", position_y - padding)).set_start(start).set_end(end)
#                 subtitle_clips.append(bg_clip)

#             subtitle_clips.append(subtitle)

#     final = CompositeVideoClip([video] + subtitle_clips)
#     final.write_videofile(output_path, codec="libx264", audio_codec="aac")

#     return output_path


import srt
from datetime import timedelta
import os
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont

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

def create_subtitle_image(text, fontsize=24, font_color="#FFFFFF", bg_color="#000000", bg_opacity=0.5, width=720):
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Production-safe font path
    font = ImageFont.truetype(font_path, fontsize)
    text_lines = text.split('\n')

    padding = 10
    line_height = fontsize + 4
    img_height = line_height * len(text_lines) + 2 * padding
    img_width = width

    bg_rgba = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (int(255 * bg_opacity),)

    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    radius = 12
    rect_shape = [(0, 0), (img_width, img_height)]
    draw.rounded_rectangle(rect_shape, radius, fill=bg_rgba)

    # Draw the text
    y_text = padding
    for line in text_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x_text = (img_width - text_width) // 2
        draw.text((x_text, y_text), line, font=font, fill=font_color)
        y_text += line_height

    return np.array(img)

def burn_subtitles_to_video(video_path, chunks, output_path="sublyze_subtitled.mp4", fontsize=24, color="#FFFFFF", bg_color="#000000", bg_opacity=0.5):
    video = VideoFileClip(video_path)
    subtitle_clips = []

    for chunk in chunks:
        start, end = chunk["timestamp"]
        text = chunk["text"].strip()
        if not text:
            continue

        subtitle_img = create_subtitle_image(
            text,
            fontsize=fontsize,
            font_color=color,
            bg_color=bg_color,
            bg_opacity=bg_opacity,
            width=video.w
        )

        img_clip = (
            ImageClip(subtitle_img, duration=(end - start))
            .set_position(("center", video.h - 100))
            .set_start(start)
            .set_end(end)
        )
        subtitle_clips.append(img_clip)

    final = CompositeVideoClip([video] + subtitle_clips)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path
