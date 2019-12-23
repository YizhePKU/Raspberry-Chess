import cv2
import chess
import chess.engine

from arm import Arm
from exceptions import ChessboardNotFoundError, IllegalMoveError
from positions import get_position, get_move_from_diff, print_position
from vision import get_position_from_image, width, height


# Setup USB camera
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

# Setup robotic arm
arm = Arm()

# Setup Stockfish engine
engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")


# Returns a single frame of image captured from camera.
def capture_image():
    _, image = camera.read()
    return image


def main():
    # while True:
    #     image = capture_image()
    #     try:
    #         position = get_position_from_image(image)
    #         print_position(position)
    #     except ChessboardNotFoundError:
    #         pass
    #     cv2.waitKey(1)

    board = chess.Board()
    current_position = get_position(board)
    stable_counter = 10

    # Test with an "almost" full chessboard
    board.remove_piece_at(chess.square(0, 0))
    board.remove_piece_at(chess.square(1, 7))
    board.remove_piece_at(chess.square(0, 7))
    current_position = get_position(board)
    cached_position = None

    # Arm calibration
    while cv2.waitKey(100) != 32:
        image = capture_image()
        cv2.imshow("Camera view", image)
        print()
        print("-" * 80)
        print("First, adjust the chessboard so that it fits in the screen.")
        print("Then, move the arm to the center crosspoint of the board.")
        print("Make sure the arm touches the board.")
        print("Finally, press spacebar to complete calibration.")
        print("-" * 80)
        print()
    arm.calibrate()
    arm.reset()
    print("Calibration complete.")

    while not board.is_game_over():
        image = capture_image()
        cv2.imshow("Camera view", image)

        try:
            position = get_position_from_image(image)

            # Todo: noise reduction
            if position == cached_position and position != current_position:
                if stable_counter > 0:
                    stable_counter -= 1
                    print(f"Counter: {stable_counter}")
                    # print("Current position:")
                    # print_position(current_position)
                    # print()
                    # print("Captured position:")
                    # print_position(position)
                    # print()
                    continue

                player_move = get_move_from_diff(board, current_position, position)
                if player_move not in board.legal_moves:
                    raise IllegalMoveError

                print("Player move: ", player_move)
                board.push(player_move)

                engine_move = engine.play(board, chess.engine.Limit(time=1)).move
                print("Engine move: ", engine_move)
                arm.act(board, engine_move)
                board.push(engine_move)

                current_position = get_position(board)

            else:
                cached_position = position
                stable_counter = 5

        except ChessboardNotFoundError:
            print("Chess board not found!")
            stable_counter = 15
        except IllegalMoveError:
            print("Illegal move!")
            print_position(cached_position)
            stable_counter = 15

        cv2.waitKey(1)


if __name__ == "__main__":
    main()
