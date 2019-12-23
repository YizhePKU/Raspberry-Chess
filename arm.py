from serial.tools import list_ports

from pydobot import Dobot


class Arm:
    x0 = 0
    y0 = 0
    z0 = 0
    device = None

    def __init__(self):
        port = list_ports.comports()[0].device
        self.device = Dobot(port=port, verbose=False)

    # Put the arm back to waiting position.
    def reset(self):
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        # self.device.move_to(x, y, z + 10, r, wait=True)
        self.device.move_to(self.x0, self.y0, self.z0 + 130, 0, wait=True)

    # Set current pose as reference pose.
    def calibrate(self):
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        self.x0 = x
        self.y0 = y
        self.z0 = z

    # Execute a move according to the move and the board info.
    # The board should be in a state that **has NOT pushed the move**.
    def act(self, board, move):
        x1 = 7 - (move.from_square // 8)
        y1 = move.from_square % 8
        x2 = 7 - (move.to_square // 8)
        y2 = move.to_square % 8

        print(board)
        print("act:", x1, y1, x2, y2)

        if board.is_capture(move):
            self._move_piece(x2, y2, 4, -2)
            self._move_piece(x1, y1, x2, y2)
        elif board.is_kingside_castling(move):
            self._move_piece(x1, y1, x2, y2)
            self._move_piece(x1, 7, x2, 5)
        elif board.is_queenside_castling(move):
            self._move_piece(x1, y1, x2, y2)
            self._move_piece(x1, 0, x2, 3)
        else:
            self._move_piece(x1, y1, x2, y2)
        self.reset()

    # Move a piece from (x1, y1) to (x2, y2)
    # The center of the top left square is (0, 0)
    def _move_piece(self, x1, y1, x2, y2):
        dx = 20
        dy = 20
        dz = 15
        dz2 = -5
        self.device.move_to(self.x0, self.y0, self.z0 + dz, 0, wait=True)
        self.device.move_to(
            self.x0 + (x1 - 3.5) * dx,
            self.y0 + (y1 - 3.5) * dy,
            self.z0 + dz,
            0,
            wait=True,
        )
        self.device.move_to(
            self.x0 + (x1 - 3.5) * dx,
            self.y0 + (y1 - 3.5) * dy,
            self.z0 + dz2,
            0,
            wait=True,
        )
        self.device.suck(True)
        self.device.move_to(
            self.x0 + (x1 - 3.5) * dx,
            self.y0 + (y1 - 3.5) * dy,
            self.z0 + dz,
            0,
            wait=True,
        )

        self.device.move_to(
            self.x0 + (x2 - 3.5) * dx,
            self.y0 + (y2 - 3.5) * dy,
            self.z0 + dz,
            0,
            wait=True,
        )
        self.device.move_to(
            self.x0 + (x2 - 3.5) * dx,
            self.y0 + (y2 - 3.5) * dy,
            self.z0 + dz2,
            0,
            wait=True,
        )
        self.device.suck(False)
        self.device.move_to(
            self.x0 + (x2 - 3.5) * dx,
            self.y0 + (y2 - 3.5) * dy,
            self.z0 + dz,
            0,
            wait=True,
        )


if __name__ == "__main__":
    arm = Arm()
