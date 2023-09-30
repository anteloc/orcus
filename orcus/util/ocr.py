# https://stackoverflow.com/a/57262099
import cv2
import numpy as np

from PIL import Image, ImageOps

from .functions import (
    std_to_kivy_xy,
    kivy_to_std_xy,
    std_to_kivy_rect_wh,
    rect_wh_to_xy,
    normalize_rect_wh,
)


def paragraphs_cv2_bounds(img, invert=True, smoothness=10):
    # Load image, grayscale, Gaussian blur, Otsu's threshold
    image = cv2.imread(img)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if invert:
        gray = cv2.bitwise_not(gray)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Create rectangular structuring element and dilate
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilate = cv2.dilate(thresh, kernel, iterations=smoothness)

    # Find contours and draw rectangle
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    bounds = [cv2.boundingRect(c) for c in cnts]

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)

    # cv2.imshow('thresh', thresh)
    # cv2.imshow('dilate', dilate)
    # cv2.imshow("image", image)
    # cv2.waitKey()

    return bounds


def kivy_paragraphs_bounds_xy(img, smoothness):
    image = Image.open(img)
    delta_y0s = image.height

    # Detect both with greyscale and inverted (negative) greyscale,
    # to better detect text on dark background, and then merge the results
    bounds_normal_wh = paragraphs_cv2_bounds(img, invert=False, smoothness=smoothness)
    bounds_inverted_wh = paragraphs_cv2_bounds(img, invert=True, smoothness=smoothness)

    bounds_wh = bounds_normal_wh + bounds_inverted_wh

    # Remove the most external bound, it doesn't actually detect text but frames the whole image
    ext_bound = max(bounds_wh, key=lambda b: b[2] * b[3])
    bounds_wh.remove(ext_bound)

    bounds_wh = [normalize_rect_wh(b, kivy_rect=True) for b in bounds_wh]

    kivy_bounds_wh = [std_to_kivy_rect_wh(b, delta_y0s) for b in bounds_wh]
    kivy_bounds_xy = [rect_wh_to_xy(b, kivy_rect=True) for b in kivy_bounds_wh]

    return kivy_bounds_xy
