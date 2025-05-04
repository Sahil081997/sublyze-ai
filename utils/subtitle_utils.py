# import os
# import srt
# import numpy as np
# from PIL import Image, ImageDraw, ImageFont
# from datetime import timedelta
# from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
# import tempfile
# import textwrap

# def generate_srt(chunks):
#     subtitles = []
#     for i, chunk in enumerate(chunks):
#         start, end = chunk["timestamp"]
#         subtitle = srt.Subtitle(index=i + 1,
#                                  start=timedelta(seconds=start),
#                                  end=timedelta(seconds=end),
#                                  content=chunk["text"])
#         subtitles.append(subtitle)
#     return srt.compose(subtitles)

# def save_srt(srt_text, filename="output.srt"):
#     with open(filename, "w", encoding="utf-8") as f:
#         f.write(srt_text)
#     return filename

# def create_subtitle_image(text, width, height, font_path, font_size, font_color, bg_color, bg_opacity):
#     img_height = height // 6
#     img_width = width
#     image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
#     draw = ImageDraw.Draw(image)

#     if bg_color:
#         rgba_bg = Image.new("RGBA", image.size, bg_color + (int(255 * bg_opacity),))
#         image = Image.alpha_composite(rgba_bg, image)
#         draw = ImageDraw.Draw(image)

#     try:
#         font = ImageFont.truetype(font_path, font_size)
#     except:
#         font = ImageFont.load_default()

#     # Wrap text to fit image width
#     max_chars_per_line = 40
#     wrapped_text = textwrap.wrap(text, width=max_chars_per_line)

#     line_height = font_size + 10
#     y_text = (img_height - line_height * len(wrapped_text)) // 2

#     for line in wrapped_text:
#         bbox = draw.textbbox((0, 0), line, font=font)
#         text_width = bbox[2] - bbox[0]
#         x_text = (img_width - text_width) // 2
#         draw.text((x_text, y_text), line, font=font, fill=font_color)
#         y_text += line_height

#     return image

# def burn_subtitles_to_video(video_path, chunks, fontsize=24, color="#FFFFFF", bg_color="#000000", bg_opacity=0.5):
#     font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
#     video = VideoFileClip(video_path)
#     subtitle_clips = []

#     for chunk in chunks:
#         start, end = chunk['timestamp']
#         duration = end - start
#         subtitle_img = create_subtitle_image(
#             chunk['text'],
#             video.w,
#             video.h,
#             font_path,
#             fontsize,
#             color,
#             tuple(int(bg_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)),
#             bg_opacity
#         )
#         with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
#             subtitle_img.save(tmp_img.name)
#             txt_clip = (ImageClip(tmp_img.name)
#                         .set_duration(duration)
#                         .set_start(start)
#                         .set_position(("center", "bottom")))
#             subtitle_clips.append(txt_clip)

#     final = CompositeVideoClip([video] + subtitle_clips)
#     output_path = "burned_output.mp4"
#     final.write_videofile(output_path, codec="libx264", audio_codec="aac")
#     return output_path

import os
import srt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from datetime import timedelta
import textwrap

def generate_srt(chunks):
    subtitles = []
    for i, chunk in enumerate(chunks):
        start = timedelta(seconds=chunk['timestamp'][0])
        end = timedelta(seconds=chunk['timestamp'][1])
        subtitles.append(srt.Subtitle(index=i, start=start, end=end, content=chunk['text']))
    return srt.compose(subtitles)

def save_srt(srt_text, output_path="output_subtitles.srt"):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_text)
    return output_path

def burn_subtitles_to_video(video_path, chunks, fontsize=24, color="white", bg_color="#000000", bg_opacity=0.6):
    video = VideoFileClip(video_path)
    clips = [video]
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, fontsize)

    for chunk in chunks:
        text = chunk['text']
        start, end = chunk['timestamp']
        duration = end - start

        wrapped_text = textwrap.fill(text, width=40)

        # Create text image with padding
        lines = wrapped_text.split('\n')
        line_height = font.getbbox('A')[3] - font.getbbox('A')[1] + 6
        padding_x = 30
        padding_y = 20
        img_width = max(font.getbbox(line)[2] for line in lines) + 2 * padding_x
        img_height = line_height * len(lines) + 2 * padding_y

        img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded rectangle background
        radius = 20
        rect_color = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (int(255 * bg_opacity),)
        draw.rounded_rectangle([0, 0, img_width, img_height], radius=radius, fill=rect_color)

        for i, line in enumerate(lines):
            draw.text((padding_x, padding_y + i * line_height), line, font=font, fill=color)

        np_img = np.array(img)
        txt_clip = (ImageClip(np_img, transparent=True)
                    .set_duration(duration)
                    .set_start(start)
                    .set_position(('center', 'bottom')))

        clips.append(txt_clip)

    final = CompositeVideoClip(clips)
    output_path = "burned_output.mp4"
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path
