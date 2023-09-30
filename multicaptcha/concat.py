from PIL import Image as Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from wheezy.captcha.image import captcha
from wheezy.captcha.image import text


def get_text_img(txt, font, font_size):
    img = Image.new("RGB", (200, 75), (255, 255, 255))
    draw = Draw(img)
    bbox = draw.textbbox((0, 0), text=txt, font=truetype(font, font_size))

    return bbox, img


def generate_captcha(msg, font, font_size, width, height, output_path, noise_level=1, warp_level=1):
    # Create a captcha image
    image = captcha(
        drawings=[
            text(
                fonts=[font],
                font_sizes=[font_size],
                drawings=[],
                squeeze_factor=1.0
            ),
        ],
        width=width,
        height=height
    )

    captcha_image = image(msg)

    if output_path is not None:
        captcha_image.save(output_path, "PNG")
        captcha_image.show()

    return captcha_image


def captcha_concat(txt, font, font_size):
    # Remove empty lines, those cause errors in wheezy.captcha
    lines = [line for line in txt.split("\n") if len(line) > 0]

    lines_captchas = []

    for i, line in enumerate(lines):
        # Roughly calculate the size of the captcha image for the text line,
        # based on a non-captcha image of the text line
        text_bbox, text_img = get_text_img(line, font, font_size)
        line_x, line_y, line_width, line_height, = text_bbox

        line_captcha = generate_captcha(
            line,
            font,
            font_size,
            line_width,
            line_height,
            None,
            # f"./line_captcha-{i}.png",
            noise_level=2,
            warp_level=2)

        lines_captchas.append(line_captcha)

    captchas_widths = [c.width for c in lines_captchas]
    captchas_heights = [c.height for c in lines_captchas]

    # Required for tesseract to recognize the text,
    # otherwise it will miss text near the borders
    x_offset = 10
    y_offset = 10

    text_captcha_width = max(captchas_widths) + x_offset
    text_captcha_height = sum(captchas_heights) + y_offset

    text_captcha = Image.new("RGB", (text_captcha_width, text_captcha_height), (255, 255, 255))

    current_y = y_offset

    for line_captcha in lines_captchas:
        text_captcha.paste(line_captcha, (x_offset, current_y))
        current_y += line_captcha.height

    return text_captcha
