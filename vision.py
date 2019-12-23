from enum import Enum
from collections import namedtuple

import cv2
import numpy as np

from exceptions import ChessboardNotFoundError


# width, height = 1280, 720
width, height = 640, 480

Point = namedtuple("Point", ["x", "y"])


# Colors in BGR mode, used by opencv.
class Colors(Enum):
    white = (255, 255, 255)
    black = (0, 0, 0)
    blue = (255, 0, 0)
    green = (0, 255, 0)
    red = (0, 0, 255)


# The "type" of a piece is the color of the pattern, not the background.
class SquareType(Enum):
    empty = 0
    white = 1
    black = 2

    def __str__(self):
        if self == SquareType.empty:
            return ' '
        if self == SquareType.white:
            return 'o'
        if self == SquareType.black:
            return 'x'
        return None


# Returns the four corners of the chessboard, or None if not found.
# Red: Upper left
# Green: Upper right
# Blue: Bottom left
# Pink: Bottom right
# Todo: make it more robust when the chessboard is facing other directions
def find_corners(image):
    # Draw a circle at [center] with [radius]
    def draw_circle(image, center, radius=1, color=Colors.white):
        cv2.circle(image, center, radius, color.value, 2)

    # Return a new image converted to black & white
    def threshold(image):
        blurred = cv2.blur(image, (10, 10))
        ret, thresholded = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)
        return thresholded

    # Extract center point from largest contour in a black & white image
    def find_point(image):
        def center(contour):
            x, y, w, h = cv2.boundingRect(contour)
            return Point(x + w // 2, y + h // 2)

        _, contours, hierarchy = cv2.findContours(
            image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
        )
        if len(contours) < 1:
            return None
        contour = max(contours, key=cv2.contourArea)
        return center(contour)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    masks = [
        # Red
        cv2.bitwise_or(
            cv2.inRange(hsv, (160, 60, 100), (180, 255, 255)),
            cv2.inRange(hsv, (0, 60, 100), (10, 255, 255)),
        ),
        # Green
        cv2.inRange(hsv, (60, 60, 100), (90, 255, 255)),
        # Blue
        cv2.inRange(hsv, (90, 100, 100), (120, 255, 255)),
        # Pink
        cv2.inRange(hsv, (130, 30, 100), (160, 255, 255)),
    ]
    points = [find_point(threshold(mask)) for mask in masks]

    if not all(points):
        return None

    x0, y0 = points[0]
    x1, y1 = points[1]
    x2, y2 = points[2]
    x3, y3 = points[3]

    adjusted_points = [
        Point(
            int(x0 + (x0 - x1) * 0.00 - (x0 - x2) * 0.05),
            int(y0 + (y0 - y1) * 0.00 - (y0 - y2) * 0.05),
        ),
        Point(
            int(x1 + (x1 - x0) * 0.08 - (x1 - x3) * 0.05),
            int(y1 + (y1 - y0) * 0.08 - (y1 - y3) * 0.05),
        ),
        Point(
            int(x2 + (x2 - x3) * 0.02 - (x2 - x0) * 0.05),
            int(y2 + (y2 - y3) * 0.02 - (y2 - y0) * 0.05),
        ),
        Point(
            int(x3 + (x3 - x2) * 0.08 - (x3 - x1) * 0.05),
            int(y3 + (y3 - y2) * 0.08 - (y3 - y1) * 0.05),
        ),
    ]

    # for point in adjusted_points:
    #     draw_circle(image, center=point, radius=3, color=Colors.white)

    # contours, _ = cv2.findContours(
    #                 threshold(masks[0]),
    #                 cv2.RETR_EXTERNAL,
    #                 cv2.CHAIN_APPROX_SIMPLE,
    #             )
    # if len(contours) > 0:
    #     contour = max(contours, key=cv2.contourArea)
    #     cv2.drawContours(image, contours, -1, -1, 1)

    return adjusted_points


# Returns a new image after a perspective transform,
# moving [corners] to the corners of the image.
def transform(image, corners):
    src = np.array(
        [
            (corners[0].x, corners[0].y),
            (corners[1].x, corners[1].y),
            (corners[2].x, corners[2].y),
            (corners[3].x, corners[3].y),
        ], np.float32)

    dst = np.array(
        [
            (0, 0),
            (width, 0),
            (0, height),
            (width, height),
        ], np.float32)

    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(image, matrix, (width, height))


# Return the square type of the given of image(usually a crop of the origial).
def detect_square_type(image):
    # Crop the edges away.
    h, w, _ = image.shape
    image = image[int(h * 0.15) : int(h * 0.85), int(w * 0.15) : int(w * 0.85)]

    # Convert the image to black & white
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, image = cv2.threshold(image, 125, 255, cv2.THRESH_BINARY)

    # Algorithm:
    # First, check if the square is empty.
    # Then, floodfill black.
    # If the square is now empty, this must be a black piece.
    # Finally, floodfill white.
    # If the square is now empty, this must be a white piece.
    # Otherwise, this must be a black piece.

    def is_empty(image):
        percentage = cv2.countNonZero(image) / (image.size)
        # print(percentage)
        return percentage < 0.05 or percentage > 0.95

    def floodfill(image, color):
        h, w = image.shape
        mask = np.zeros((h + 2, w + 2), np.uint8)
        seeds = [
            (0, 0),
            (w - 1, 0),
            (0, h - 1),
            (w - 1, h - 1),
        ]
        for seed in seeds:
            cv2.floodFill(image, mask, seed, color.value)

    if is_empty(image):
        return SquareType.empty

    floodfill(image, Colors.black)
    if is_empty(image):
        return SquareType.black

    floodfill(image, Colors.white)
    if is_empty(image):
        return SquareType.white
    else:
        return SquareType.black


# Recognize the chessboard in the image, and returns the coresponding position.
# A position is an 8x8 array of SquareType.
def get_position_from_image(image):
    # Crop the image into 8x8 squares.
    # Returns the square on the jth row, ith column(zero based).
    def crop(image, i, j):
        w = int(width / 8)
        h = int(height / 8)
        return image[h * j : h * (j + 1), w * i : w * (i + 1)]

    corners = find_corners(image)
    if corners is None:
        raise ChessboardNotFoundError()

    chessboard_image = transform(image, corners)

    debug_image = cv2.cvtColor(chessboard_image, cv2.COLOR_BGR2GRAY)
    cv2.imshow("Chess board", debug_image)

    _, debug_image = cv2.threshold(debug_image, 120, 255, cv2.THRESH_BINARY)
    cv2.imshow("Gray scale", debug_image)

    return [[detect_square_type(crop(chessboard_image, i, j)) for i in range(8)] for j in range(8)]
