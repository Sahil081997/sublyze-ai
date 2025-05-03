# import srt
# from datetime import timedelta
# import os
# import numpy as np
# from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
# from PIL import Image, ImageDraw, ImageFont

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
#         subtitles.append(srt.Subtitle(index=i + 1, start=start, end=end, content=content))
#     return srt.compose(subtitles)

# def save_srt(srt_text, path="output.srt"):
#     with open(path, "w", encoding="utf-8") as f:
#         f.write(srt_text)
#     return path

# def create_subtitle_image(text, fontsize=24, font_color="#FFFFFF", bg_color="#000000", bg_opacity=0.5, width=720):
#     font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Production-safe font path
#     font = ImageFont.truetype(font_path, fontsize)
#     text_lines = text.split('\n')

#     padding = 10
#     line_height = fontsize + 4
#     img_height = line_height * len(text_lines) + 2 * padding
#     img_width = width

#     bg_rgba = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (int(255 * bg_opacity),)

#     img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
#     draw = ImageDraw.Draw(img)

#     # Draw rounded rectangle background
#     radius = 12
#     rect_shape = [(0, 0), (img_width, img_height)]
#     draw.rounded_rectangle(rect_shape, radius, fill=bg_rgba)

#     # Draw the text
#     y_text = padding
#     for line in text_lines:
#         bbox = draw.textbbox((0, 0), line, font=font)
#         text_width = bbox[2] - bbox[0]
#         x_text = (img_width - text_width) // 2
#         draw.text((x_text, y_text), line, font=font, fill=font_color)
#         y_text += line_height

#     return np.array(img)

# def burn_subtitles_to_video(video_path, chunks, output_path="sublyze_subtitled.mp4", fontsize=24, color="#FFFFFF", bg_color="#000000", bg_opacity=0.5):
#     video = VideoFileClip(video_path)
#     subtitle_clips = []

#     for chunk in chunks:
#         start, end = chunk["timestamp"]
#         text = chunk["text"].strip()
#         if not text:
#             continue

#         subtitle_img = create_subtitle_image(
#             text,
#             fontsize=fontsize,
#             font_color=color,
#             bg_color=bg_color,
#             bg_opacity=bg_opacity,
#             width=video.w
#         )

#         img_clip = (
#             ImageClip(subtitle_img, duration=(end - start))
#             .set_position(("center", video.h - 100))
#             .set_start(start)
#             .set_end(end)
#         )
#         subtitle_clips.append(img_clip)

#     final = CompositeVideoClip([video] + subtitle_clips)
#     final.write_videofile(output_path, codec="libx264", audio_codec="aac")

#     return output_path
import os
import srt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import timedelta
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import tempfile
import textwrap

def generate_srt(chunks):
    subtitles = []
    for i, chunk in enumerate(chunks):
        start, end = chunk["timestamp"]
        subtitle = srt.Subtitle(index=i + 1,
                                 start=timedelta(seconds=start),
                                 end=timedelta(seconds=end),
                                 content=chunk["text"])
        subtitles.append(subtitle)
    return srt.compose(subtitles)

def save_srt(srt_text, filename="output.srt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(srt_text)
    return filename

def create_subtitle_image(text, width, height, font_path, font_size, font_color, bg_color, bg_opacity):
    img_height = height // 6
    img_width = width
    image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if bg_color:
        rgba_bg = Image.new("RGBA", image.size, bg_color + (int(255 * bg_opacity),))
        image = Image.alpha_composite(rgba_bg, image)
        draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    # Wrap text to fit image width
    max_chars_per_line = 40
    wrapped_text = textwrap.wrap(text, width=max_chars_per_line)

    line_height = font_size + 10
    y_text = (img_height - line_height * len(wrapped_text)) // 2

    for line in wrapped_text:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x_text = (img_width - text_width) // 2
        draw.text((x_text, y_text), line, font=font, fill=font_color)
        y_text += line_height

    return image

def burn_subtitles_to_video(video_path, chunks, fontsize=24, color="#FFFFFF", bg_color="#000000", bg_opacity=0.5):
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    video = VideoFileClip(video_path)
    subtitle_clips = []

    for chunk in chunks:
        start, end = chunk['timestamp']
        duration = end - start
        subtitle_img = create_subtitle_image(
            chunk['text'],
            video.w,
            video.h,
            font_path,
            fontsize,
            color,
            tuple(int(bg_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)),
            bg_opacity
        )
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
            subtitle_img.save(tmp_img.name)
            txt_clip = (ImageClip(tmp_img.name)
                        .set_duration(duration)
                        .set_start(start)
                        .set_position(("center", "bottom")))
            subtitle_clips.append(txt_clip)

    final = CompositeVideoClip([video] + subtitle_clips)
    output_path = "burned_output.mp4"
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path
