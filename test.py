import chess
import chess.pgn

from positions import get_move_from_diff, get_position

with open("data/GM Vachier-Lagrave, Maxime.pgn") as pgn:
    game = chess.pgn.read_game(pgn)
    board = game.board()

for move in game.mainline_moves():
    old_position = get_position(board)
    board.push(move)
    new_position = get_position(board)

    diff_move = get_move_from_diff(board, old_position, new_position)
    print(f"diff_move: {diff_move}, actual move: {move}")
    assert(diff_move == move)
