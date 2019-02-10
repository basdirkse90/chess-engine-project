import numpy as np
import random
from ast import literal_eval
from itertools import product


class BoardRep:
    # Constants that relate square name to square number:
    #   a1 = 0, a2 = 1, a3 = 2, ..., a2 = 8, b2 = 9, ... h8 = 63
    NUM_TO_SQUARE = [f + r for r, f in product('12345678', 'abcdefgh')]
    SQUARE_TO_NUM = {v: k for k, v in enumerate(NUM_TO_SQUARE)}
    SQUARE_TO_NUM['-'] = None

    # Pieces are identified by their FEN character:
    #   Capital for white:    P, N, B, R, Q, K  (pawn, knight, bisschop, rook, queen, king)
    #   Lowercase for black:  p, n, b, r, q, k  (pawn, knight, bisschop, rook, queen, king)
    PIECES = 'PNBRQKpnbrqk'

    FEN_TO_UNICODE = {
        'P': '\u265F', 'N': '\u265E', 'B': '\u265D', 'R': '\u265C', 'Q': '\u265B', 'K': '\u265A',
        'p': '\u2659', 'n': '\u2658', 'b': '\u2657', 'r': '\u2656', 'q': '\u2655', 'k': '\u2654'
    }

    # Initialize empty board
    def __init__(self):
        """ Docstring here

        Parameters:
        side_to_move -- (False = white, True = black)
        castling_rights -- [White short, white long, black short, black long]
        en_passant_square -- Target square for en passant capture ((0-63) or None)
        half_move_count -- Counts half moves since last capture or pawn push
        full_move_count -- Counts full moves after black moves
        piece_list -- Simple list of piece objects that are in existence
        piece_count -- Dict of pieces and their counts
        square_list -- List of length 64 with each piece object at the square it occupies (empty squares have None)
        attack_map
        defence_map

        """
        self.side_to_move = None
        self.castling_rights = [False]*4
        self.en_passant_square = None
        self.half_move_count = 0
        self.full_move_count = 1
        self.piece_list = []
        self.piece_count = {key: 0 for key in self.PIECES}
        self.square_list = [None]*64

    @classmethod
    def read_fen(cls, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        board = cls()
        lines = fen.split()
        ranks = lines[0].split("/")
        r = 7
        for rank in ranks:
            f = 0
            for piece in rank:
                if piece in cls.PIECES:
                    pos = r*8+f
                    newpiece = Piece(piecetype=piece, position=pos)
                    board.square_list[pos] = newpiece
                    board.piece_list.append(newpiece)
                    board.piece_count[piece] += 1
                    f += 1
                else:
                    f += int(piece)
            r -= 1

        # TODO: Make attack_map once move generation is implemented
        # TODO: Make defence_map once move generation is implemented
        # TODO: Calculate piece mobility once move generation is implemented

        board.side_to_move = (lines[1] == 'b')

        for i, opt in enumerate('KQkq'):
            board.castling_rights[i] = opt in lines[2]

        board.en_passant_square = cls.SQUARE_TO_NUM[lines[3]]
        board.half_move_count = int(lines[4])
        board.full_move_count = int(lines[5])

        return board

    def __str__(self):
        res = ""
        for r in range(7, -1, -1):
            for f in range(8):
                if f == 0 and r < 7:
                    res += '\n'
                piece = self.square_list[r*8+f]
                if piece is None:
                    res += '. '
                else:
                    res += piece.piecetype + ' '
        return res

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def get_fen(self):
        res = ""
        for r in range(7, -1, -1):
            number_of_empty = 0
            for f in range(0, 8):
                piece = self.square_list[r*8+f]
                if piece is not None:
                    if number_of_empty > 0:
                        res += str(number_of_empty)
                    res += piece.piecetype
                    number_of_empty = 0
                else:
                    number_of_empty += 1
            if number_of_empty > 0:
                res += str(number_of_empty)
            res += "/"
        res = res[0:-1]

        if self.side_to_move:
            res += " b "
        else:
            res += " w "

        castle = ''
        for i, opt in enumerate('KQkq'):
            if self.castling_rights[i]:
                castle += opt
        if len(castle) == 0:
            castle = '-'
        res += castle

        if self.en_passant_square is None:
            res += " -"
        else:
            res += " " + self.NUM_TO_SQUARE[self.en_passant_square]

        res += " " + str(self.half_move_count) + " " + str(self.full_move_count)

        return res

    def generate_pseudolegal_moves(self):
        moves = []
        for i in range(64):
            if self.square_list[i] is None:
                continue

            r = i // 8
            f = i % 8
            color = int(self.side_to_move)      # white = 0, black = 1

            # White Pawn moves
            if self.square_list[i].piecetype == 'P' and not self.side_to_move:
                if r == 6:  # promote
                    # TODO implement promotion
                    pass
                else:
                    # move forward
                    if self.square_list[i+8] is None:
                        moves.append(Move(i, i+8, False))
                        # move 2 if allowed
                        if r == 1 and self.square_list[i+16] is None:
                            moves.append(Move(i, i+16, False))
                    # capture right
                    if f < 7 and ((self.square_list[i+9] is not None and
                                   self.square_list[i+9].color != self.side_to_move) or self.en_passant_square == i+9):
                        moves.append(Move(i, i+9, True))
                    # capture left
                    if f > 0 and ((self.square_list[i+7] is not None and
                                   self.square_list[i+7].color != self.side_to_move) or self.en_passant_square == i+7):
                        moves.append(Move(i, i+7, True))

            # Black Pawn moves
            if self.square_list[i].piecetype == 'p' and self.side_to_move:
                if r == 1:  # promote
                    # TODO implement promotion
                    pass
                else:
                    # move forward
                    if self.square_list[i-8] is None:
                        moves.append(Move(i, i-8, False))
                        # move 2 if allowed
                        if r == 6 and self.square_list[i-16] is None:
                            moves.append(Move(i, i-16, False))
                    # capture right
                    if f < 7 and ((self.square_list[i-7] is not None and
                                   self.square_list[i-7].color != self.side_to_move) or self.en_passant_square == i-7):
                        moves.append(Move(i, i-7, True))
                    # capture left
                    if f > 0 and ((self.square_list[i-9] is not None and
                                   self.square_list[i-9].color != self.side_to_move) or self.en_passant_square == i-9):
                        moves.append(Move(i, i-9, True))

            # TODO: Implement other pseudo_moves

        return moves

    def test_do_pseudolegal_move(self, mv):
        move_list = self.generate_pseudolegal_moves()

        if mv in move_list:
            assert mv.capture == (self.square_list[mv.to] is not None or self.en_passant_square == mv.to)

            # Do move
            frm_piece = self.square_list[mv.frm]
            self.square_list[mv.frm] = None
            if mv.capture:
                if self.square_list[mv.to] is not None:
                    captured_piece = self.square_list[mv.to]
                else:  # capture must be en passant
                    if mv.to < 32:
                        captured_piece = self.square_list[mv.to+8]
                        self.square_list[mv.to+8] = None
                    else:
                        captured_piece = self.square_list[mv.to-8]
                        self.square_list[mv.to-8] = None
                self.piece_count[captured_piece.piecetype] -= 1
                self.piece_list.remove(captured_piece)
            self.square_list[mv.to] = frm_piece
            frm_piece.move(mv.to)

            # Set en passant square if applicable
            if frm_piece.piecetype == 'P' and mv.to - mv.frm == 16:
                self.en_passant_square = mv.to - 8
            elif frm_piece.piecetype == 'p' and mv.to - mv.frm == -16:
                self.en_passant_square = mv.to + 8
            else:
                self.en_passant_square = None

            if self.side_to_move:
                self.full_move_count += 1

            if mv.capture or frm_piece.piecetype in 'Pp':
                self.half_move_count = 0
            else:
                self.half_move_count += 1

            self.side_to_move = not self.side_to_move

        else:
            print("Not a pseudolegal move!")

    def test_random_pseudolegal_move(self):
        move_list = self.generate_pseudolegal_moves()
        mv = random.sample(move_list, 1)
        self.test_do_pseudolegal_move(mv[0])
        return mv[0]


class Piece:
    PIECE_TO_NAME = {'P': 'Pawn', 'N': 'Knight', 'B': 'Bishop', 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}
    COLOR_TO_NAME = {False: 'White', True: 'Black'}

    def __init__(self, piecetype, position):
        """"
        piecetype:  Type of the piece (by FEN letter)
        color:      Boolean (False = white, True = Black)
        position:   The square it occupies 0-63
        mobility:   The number of moves the piece has (including captures)
        attack:     Lowest valued attacker (by FEN letter)
        defend:     Lowest valued defender (by FEN letter)
        """
        self.piecetype = piecetype
        self.color = piecetype.islower()
        self.piecename = self.PIECE_TO_NAME[piecetype.upper()]
        self.colorname = self.COLOR_TO_NAME[self.color]

        self.position = position
        self.mobility = None
        self.attack = None
        self.defend = None

    def __str__(self):
        return self.colorname + ' ' + self.piecename + ' on ' + BoardRep.NUM_TO_SQUARE[self.position]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def move(self, to):
        self.position = to


class Move:
    def __init__(self, frm, to, capture=False, promotion=None):
        self.frm = frm
        self.to = to
        self.capture = capture
        self.promotion = promotion

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __str__(self):
        res = BoardRep.NUM_TO_SQUARE[self.frm]
        if self.capture:
            res += 'x'
        else:
            res += '-'
        res += BoardRep.NUM_TO_SQUARE[self.to]
        if self.promotion is not None:
            res+= ('=' + self.promotion.upper())
        return res
