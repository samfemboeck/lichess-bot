"""
Some example strategies for people who want to create a custom, homemade bot.
And some handy classes to extend
"""

import chess
from chess.engine import PlayResult
import random
from engine_wrapper import EngineWrapper
import sys


class FillerEngine:
    """
    Not meant to be an actual engine.

    This is only used to provide the property "self.engine"
    in "MinimalEngine" which extends "EngineWrapper"
    """
    def __init__(self, main_engine, name=None):
        self.id = {
            "name": name
        }
        self.name = name
        self.main_engine = main_engine

    def __getattr__(self, method_name):
        main_engine = self.main_engine

        def method(*args, **kwargs):
            nonlocal main_engine
            nonlocal method_name
            return main_engine.notify(method_name, *args, **kwargs)

        return method


class MinimalEngine(EngineWrapper):
    """
    Subclass this to prevent a few random errors

    Even though MinimalEngine extends EngineWrapper,
    you don't have to actually wrap an engine.

    At minimum, just implement `search`,
    however you can also change other methods like
    `notify`, `first_search`, `get_time_control`, etc.
    """
    def __init__(self, commands, options, stderr, draw_or_resign, name=None, **popen_args):
        super().__init__(options, draw_or_resign)

        self.engine_name = self.__class__.__name__ if name is None else name

        self.engine = FillerEngine(self, name=self.name)
        self.engine.id = {
            "name": self.engine_name
        }

    def search(self, board, time_limit, ponder, draw_offered):
        """
        The method to be implemented in your homemade engine

        NOTE: This method must return an instance of "chess.engine.PlayResult"
        """
        raise NotImplementedError("The search method is not implemented")

    def notify(self, method_name, *args, **kwargs):
        """
        The EngineWrapper class sometimes calls methods on "self.engine".
        "self.engine" is a filler property that notifies <self>
        whenever an attribute is called.

        Nothing happens unless the main engine does something.

        Simply put, the following code is equivalent
        self.engine.<method_name>(<*args>, <**kwargs>)
        self.notify(<method_name>, <*args>, <**kwargs>)
        """
        pass

class ExampleEngine(MinimalEngine):
    pass

def square_bonus_board(board, color):
    bonus = [
        [[-175,-92,-74,-73],[-77,-41,-27,-15],[-61,-17,6,12],[-35,8,40,49],[-34,13,44,51],[-9,22,58,53],[-67,-27,4,37],[-201,-83,-56,-26]],
        [[-53,-5,-8,-23],[-15,8,19,4],[-7,21,-5,17],[-5,11,25,39],[-12,29,22,31],[-16,6,1,11],[-17,-14,5,0],[-48,1,-14,-23]],
        [[-31,-20,-14,-5],[-21,-13,-8,6],[-25,-11,-1,3],[-13,-5,-4,-6],[-27,-15,-4,3],[-22,-2,6,12],[-2,12,16,18],[-17,-19,-1,9]],
        [[3,-5,-5,4],[-3,5,8,12],[-3,6,13,7],[4,5,9,8],[0,14,12,5],[-4,10,6,8],[-5,6,10,8],[-2,-2,1,-2]],
        [[271,327,271,198],[278,303,234,179],[195,258,169,120],[164,190,138,98],[154,179,105,70],[123,145,81,31],[88,120,65,33],[59,89,45,-1]]
    ]

    pbonus = [
        [0,0,0,0,0,0,0,0],[3,3,10,19,16,19,7,-5],[-9,-15,11,15,32,22,5,-22],[-4,-23,6,20,40,17,4,-8],[13,0,-13,1,11,-2,-13,5],
        [5,-12,-7,22,-8,-5,-15,-8],[-7,7,-3,-13,5,-16,10,-8],[0,0,0,0,0,0,0,0]
    ]
    
    piece_map = board.piece_map()

    ret = 0

    for square in piece_map:
        if (piece_map[square].color != color):
            continue

        x = square % 8
        y = square // 8
        symbol = piece_map[square].symbol().upper()
        i = "PNBRQK".find(symbol)

        if (i == 0): 
            ret += pbonus[7 - y][x] if color is chess.BLACK else pbonus[y][x]
        else: 
            ret += bonus[i - 1][7 - y][min(x, 7 - x)] if color is chess.BLACK else bonus[i - 1][y][min(x, 7 - x)]

    return ret

def get_board_value(board):
    piece_values = {'P': -1, 'N': -3, 'B': -3, 'R': -5, 'Q': -9, 'K': -90, 'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 90}
    board_value = 0
    piece_map = board.piece_map()
    
    for piece in piece_map.values():
        board_value += piece_values[str(piece)]

    board_value += square_bonus_board(board, chess.BLACK)
        
    return board_value

def minimax_ab(board, depth, is_max= True, alpha = -sys.maxsize - 1, beta = sys.maxsize):
    if (depth == 0 or board.is_game_over()):
        return chess.Move.null(), get_board_value(board)

    if (is_max):
        max_score = -sys.maxsize - 1
        max_move = chess.Move.null()

        for move in board.legal_moves:
            board.push(move)
            cur_move, score = minimax_ab(board, depth - 1, False, alpha, beta)
            board.pop()

            alpha = max(alpha, score)
            if (score > max_score):
                max_score = score
                max_move = move

            if (beta <= alpha):
                break

        return max_move, max_score
    else:
        min_score = sys.maxsize
        min_move = chess.Move.null()

        for move in board.legal_moves:
            board.push(move)
            cur_move, score = minimax_ab(board, depth - 1, True, alpha, beta)
            board.pop()

            beta = min(beta, score)
            if (score < min_score):
                min_score = score
                min_move = move

            if (beta <= alpha):
                break

        return min_move, min_score

def minimax_ab_deathmatch(board, depth, is_max=True, alpha=-sys.maxsize - 1, beta=sys.maxsize):
    if (depth == 0 or board.is_game_over()):
        return chess.Move.null(), get_board_value(board)

    moves = []
    for move in board.legal_moves:
        is_capture = board.is_capture(move)
        board.push(move)
        is_check = board.is_check()
        board.pop()
        if (is_capture or is_check):
            moves.append(move)

    if len(moves) == 0:
        return chess.Move.null(), 0

    if (is_max):
        max_score = -sys.maxsize - 1
        max_move = chess.Move.null()

        for move in moves:
            board.push(move)
            cur_move, score = minimax_ab(board, depth - 1, False, alpha, beta)
            board.pop()

            alpha = max(alpha, score)
            if (score > max_score):
                max_score = score
                max_move = move

            if (beta <= alpha):
                break

        return max_move, max_score

    else:
        min_score = sys.maxsize
        min_move = chess.Move.null()

        for move in moves:
            board.push(move)
            cur_move, score = minimax_ab(board, depth - 1, True, alpha, beta)
            board.pop()

            beta = min(beta, score)
            if (score < min_score):
                min_score = score
                min_move = move

            if (beta <= alpha):
                break

        return min_move, min_score

class WunderEngine(MinimalEngine):
    def search(self, board, *args):
        move, score = minimax_ab(board, 4, not board.turn)
        is_capture = board.is_capture(move)
        board.push(move)
        is_check = board.is_check()
        board.pop()
        if (is_capture or is_check):
            move_dm, score_dm = minimax_ab_deathmatch(board, 5, not board.turn)
            if (score_dm > score):
                print("better move found")
                print(move_dm)
                move = move_dm
        return PlayResult(move, None)
    pass

# Strategy names and ideas from tom7's excellent eloWorld video

class RandomMove(ExampleEngine):
    def search(self, board, *args):
        return PlayResult(random.choice(list(board.legal_moves)), None)


class Alphabetical(ExampleEngine):
    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=board.san)
        return PlayResult(moves[0], None)


class FirstMove(ExampleEngine):
    """Gets the first move when sorted by uci representation"""
    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=str)
        return PlayResult(moves[0], None)
