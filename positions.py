from collections import namedtuple

import chess

from exceptions import IllegalMoveError
from vision import SquareType


def print_position(position):
    for x in range(8):
        for y in range(8):
            print(position[x][y], sep="", end="")
        print()


# Extracts position from a chess.Board.
def get_position(board):
    mapping = {
        'P': 1,     # White Pawn
        'p': -1,    # Black Pawn
        'N': 2,     # White Knight
        'n': -2,    # Black Knight
        'B': 3,     # White Bishop
        'b': -3,    # Black Bishop
        'R': 4,     # White Rook
        'r': -4,    # Black Rook
        'Q': 5,     # White Queen
        'q': -5,    # Black Queen
        'K': 6,     # White King
        'k': -6     # Black King
    }

    def convert_to_int(board):
        epd_string = board.epd()
        list_int = []
        for i in epd_string:
            if i == " ":
                return list_int
            elif i != "/":
                if i in mapping:
                    list_int.append(mapping[i])
                else:
                    for counter in range(0, int(i)):
                        list_int.append(0)

    def type_of(x):
        if x > 0:
            return SquareType.white
        if x < 0:
            return SquareType.black
        else:
            return SquareType.empty

    lst = convert_to_int(board)
    return [[type_of(lst[i * 8 + j]) for j in range(8)] for i in range(8)]


# Returns a chess.Move object by analysing change of positions.
# [board] should be the board of the [new_position]
def get_move_from_diff(board, old_position, new_position):
    # A SquarePair denotes the starting and ending point of a move.
    Square = namedtuple("Square", ["x", "y"])
    SquarePair = namedtuple("SquarePair", ["start", "end"])

    # Convert a move(point pair) to algebraic notation.
    def pair_to_algebraic(pair):
        def square_to_string(square):
            mapping = "abcdefgh"
            return mapping[square.y] + str(8 - square.x)

        return square_to_string(pair.start) + square_to_string(pair.end)

    # Returns a move(point pair) by analysing differences between two positions.
    def diff_position(old_position, new_position):
        diff = [
            Square(x, y)
            for x in range(8)
            for y in range(8)
            if old_position[x][y] != new_position[x][y]
        ]

        # Number of differences between boards:
        # Castling has 4.
        # Capture en passant has 3.
        # Any other move, promotion, or normal capture has 2.
        if len(diff) == 4:
            # Castling
            king_points = [p for p in diff if p.y == 4]
            rook_points = [p for p in diff if p.y == 0 or p.y == 7]
            if len(king_points) != 1 or len(rook_points) != 1:
                raise IllegalMoveError

            p = king_points[0]
            q = rook_points[0]
            if q.y == 0:
                # Castle long
                return SquarePair(p, Square(p.x, 2))
            elif q.y == 7:
                # Castle short
                return SquarePair(p, Square(p.x, 6))
            else:
                raise Exception("")

        elif len(diff) == 3:
            # Capture en passant
            pawn_points = [
                p for p in diff if new_position[p.x][p.y] != SquareType.empty
            ]
            if len(pawn_points) != 1:
                raise IllegalMoveError

            p = pawn_points[0]
            start_points = [
                q
                for q in diff
                if q != p and old_position[q.x][q.y] == new_position[p.x][p.y]
            ]
            if len(start_points) != 1:
                raise IllegalMoveError

            return SquarePair(start_points[0], p)

        elif len(diff) == 2:
            # Normal move, capture, or promotion
            start_points = [
                p for p in diff if new_position[p.x][p.y] == SquareType.empty
            ]
            if len(start_points) != 1:
                raise IllegalMoveError
            start = start_points[0]

            end_points = [p for p in diff if p != start]
            if len(end_points) != 1:
                raise IllegalMoveError
            end = end_points[0]
            return SquarePair(start, end)

        else:
            raise IllegalMoveError

    square_pair = diff_position(old_position, new_position)
    assert square_pair is not None

    s = pair_to_algebraic(square_pair)

    # Todo: deal with promotion.
    # Algerbraic notation requires that promotion is identified like "a7a8q".
    # Currently it is not supported.
    return chess.Move.from_uci(s)
