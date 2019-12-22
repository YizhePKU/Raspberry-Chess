class RaspberryChessException(Exception):
    pass


class ChessboardNotFoundError(RaspberryChessException):
    pass


class IllegalMoveError(RaspberryChessException):
    pass
