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
        self.castling_rights = [True]*4
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
        clr = int(self.side_to_move)  # white = 0, black = 1

        for moving_piece in self.piece_list:
            i = moving_piece.position

            r = i // 8
            f = i % 8

            # Pawn moves
            d = [
                {'piece': 'P', 'f1': 8, 'f2': 16, 'f2rank': 1, 'xl': 7, 'xr': 9, 'promrank': 6, 'proms': 'QRBN'},
                {'piece': 'p', 'f1': -8, 'f2': -16, 'f2rank': 6, 'xl': -9, 'xr': -7, 'promrank': 1, 'proms': 'qrbn'}
            ]
            if self.square_list[i].piecetype == d[clr]['piece']:
                # move forward
                if self.square_list[i+d[clr]['f1']] is None:
                    if r == d[clr]['promrank']:
                        for prom in d[clr]['proms']:
                            moves.append(Move(i, i+d[clr]['f1'], False, promotion=prom))
                    else:
                        moves.append(Move(i, i+d[clr]['f1'], False))
                        # move 2 if allowed
                        if r == d[clr]['f2rank'] and self.square_list[i+d[clr]['f2']] is None:
                            moves.append(Move(i, i+d[clr]['f2'], False))

                # capture right
                if f < 7 and ((self.square_list[i+d[clr]['xr']] is not None
                               and self.square_list[i+d[clr]['xr']].color != self.side_to_move)
                              or self.en_passant_square == i+d[clr]['xr']):
                    if r == d[clr]['promrank']:
                        for prom in d[clr]['proms']:
                            moves.append(Move(i, i+d[clr]['xr'], True, promotion=prom))
                    else:
                        moves.append(Move(i, i+d[clr]['xr'], True))

                # capture left
                if f > 0 and ((self.square_list[i + d[clr]['xl']] is not None
                               and self.square_list[i + d[clr]['xl']].color != self.side_to_move)
                              or self.en_passant_square == i + d[clr]['xl']):
                    if r == d[clr]['promrank']:
                        for prom in d[clr]['proms']:
                            moves.append(Move(i, i + d[clr]['xl'], True, promotion=prom))
                    else:
                        moves.append(Move(i, i + d[clr]['xl'], True))

            # Rook moves or rook-like queen moves
            if self.square_list[i].piecetype in 'Rr'[clr] + 'Qq'[clr]:
                # TODO: Refactor this code?

                # move right
                offset = 1
                while f + offset < 8 and self.square_list[i + offset] is None:
                    moves.append(Move(i, i + offset, False))
                    offset += 1
                if f+offset < 8 and self.square_list[i+offset].color != self.side_to_move:
                    moves.append(Move(i, i + offset, True))

                # move left
                offset = -1
                while f + offset >= 0 and self.square_list[i + offset] is None:
                    moves.append(Move(i, i + offset, False))
                    offset -= 1
                if f + offset >= 0 and self.square_list[i + offset].color != self.side_to_move:
                    moves.append(Move(i, i + offset, True))

                # move up
                offset = 1
                while r + offset < 8 and self.square_list[i + 8*offset] is None:
                    moves.append(Move(i, i + 8*offset, False))
                    offset += 1
                if r + offset < 8 and self.square_list[i + 8*offset].color != self.side_to_move:
                    moves.append(Move(i, i + 8*offset, True))

                # move down
                offset = -1
                while r + offset >= 0 and self.square_list[i + 8 * offset] is None:
                    moves.append(Move(i, i + 8 * offset, False))
                    offset -= 1
                if r + offset >= 0 and self.square_list[i + 8 * offset].color != self.side_to_move:
                    moves.append(Move(i, i + 8*offset, True))

            # Bishop moves or bishop-like queen moves
            if self.square_list[i].piecetype in 'Bb'[clr] + 'Qq'[clr]:
                # TODO: Refactor this code?

                # move upright
                offset = 1
                while f + offset < 8 and r + offset < 8 and self.square_list[i + 9*offset] is None:
                    moves.append(Move(i, i + 9*offset, False))
                    offset += 1
                if f + offset < 8 and r + offset < 8 and self.square_list[i + 9*offset].color != self.side_to_move:
                    moves.append(Move(i, i + 9*offset, True))

                # move upleft
                offset = 1
                while f - offset >= 0 and r + offset < 8 and self.square_list[i + 7*offset] is None:
                    moves.append(Move(i, i + 7*offset, False))
                    offset += 1
                if f - offset >= 0 and r + offset < 8 and self.square_list[i + 7*offset].color != self.side_to_move:
                    moves.append(Move(i, i + 7*offset, True))

                # move downright
                offset = 1
                while f + offset < 8 and r - offset >= 0 and self.square_list[i - 7*offset] is None:
                    moves.append(Move(i, i - 7*offset, False))
                    offset += 1
                if f + offset < 8 and r - offset >= 0 and self.square_list[i - 7*offset].color != self.side_to_move:
                    moves.append(Move(i, i - 7*offset, True))

                # move downleft
                offset = 1
                while f - offset >= 0 and r - offset >= 0 and self.square_list[i - 9 * offset] is None:
                    moves.append(Move(i, i - 9 * offset, False))
                    offset += 1
                if f - offset >= 0 and r - offset >= 0 and self.square_list[i - 9*offset].color != self.side_to_move:
                    moves.append(Move(i, i - 9*offset, True))

            # King moves -- not castling moves
            if self.square_list[i].piecetype == 'Kk'[clr]:
                offsets = {7, 8, 9, -1, 1, -9, -8, -7}
                if r == 0:
                    offsets -= {-9, -8, -7}
                elif r == 7:
                    offsets -= {7, 8, 9}

                if f == 0:
                    offsets -= {7, -1, -9}
                elif f == 7:
                    offsets -= {9, 1, -7}

                for offset in offsets:
                    if self.square_list[i+offset] is not None:
                        if self.square_list[i+offset].color != self.side_to_move:
                            moves.append(Move(i, i + offset, True))
                    else:
                        moves.append(Move(i, i + offset, False))

            # Knight moves
            if self.square_list[i].piecetype == 'Nn'[clr]:
                offsets = {6, 15, 17, 10, -6, -15, -17, -10}
                if r == 0:
                    offsets -= {-6, -15, -17, -10}
                elif r == 1:
                    offsets -= {-15, -17}
                elif r == 7:
                    offsets -= {6, 15, 17, 10}
                elif r == 6:
                    offsets -= {15, 17}

                if f == 0:
                    offsets -= {-17, -10, 6, 15}
                elif f == 1:
                    offsets -= {-10, 6}
                elif f == 7:
                    offsets -= {17, 10, -6, -15}
                elif f == 6:
                    offsets -= {10, -6}

                for offset in offsets:
                    if self.square_list[i+offset] is not None:
                        if self.square_list[i+offset].color != self.side_to_move:
                            moves.append(Move(i, i + offset, True))
                    else:
                        moves.append(Move(i, i + offset, False))

        # Castling moves
        if self.castling_rights[2*clr] and self.square_list[7*8*clr+5] is None and self.square_list[7*8*clr+6] is None:
            moves.append(Move(7*8*clr + 4, 7*8*clr + 6, is_castle=True))

        if self.castling_rights[2*clr+1] and all(self.square_list[7*8*clr + x] is None for x in [1, 2, 3]):
            moves.append(Move(7*8*clr + 4, 7*8*clr + 2, is_castle=True))

        for move in moves:
            assert self.square_list[move.frm] is not None

        return moves

    def test_do_pseudolegal_move(self, mv, move_list=None):
        if move_list is None:
            move_list = self.generate_pseudolegal_moves()

        if mv in move_list:
            frm_piece = self.square_list[mv.frm]

            # Do move
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

            # Move rook if it was a castling move
            if mv.is_castle:
                if mv.to - mv.frm == 2:  # short castle
                    rook = self.square_list[mv.to+1]
                    self.square_list[mv.to + 1] = None
                    self.square_list[mv.to-1] = rook
                    rook.move(mv.to-1)
                elif mv.to - mv.frm == -2:  # long castle
                    rook = self.square_list[mv.to-2]
                    self.square_list[mv.to-2] = None
                    self.square_list[mv.to+1] = rook
                    rook.move(mv.to+1)

            # Handle promotion
            if mv.promotion is not None:
                promotedPiece = Piece(mv.promotion, mv.to)
                self.square_list[mv.to] = promotedPiece
                self.piece_count[frm_piece.piecetype] -= 1
                self.piece_count[promotedPiece.piecetype] += 1
                self.piece_list.remove(frm_piece)
                self.piece_list.append(promotedPiece)

            # Set en passant square if applicable
            if frm_piece.piecetype == 'P' and mv.to - mv.frm == 16:
                self.en_passant_square = mv.to - 8
            elif frm_piece.piecetype == 'p' and mv.to - mv.frm == -16:
                self.en_passant_square = mv.to + 8
            else:
                self.en_passant_square = None

            # Remove castling rights if applicable
            if any(self.castling_rights):  # avoid unnecessary checking
                # After king move
                if frm_piece.piecetype == 'K':
                    self.castling_rights[0] = False
                    self.castling_rights[1] = False
                if frm_piece.piecetype == 'k':
                    self.castling_rights[2] = False
                    self.castling_rights[3] = False

                # After rook move
                if frm_piece.piecetype == 'R':
                    if mv.frm == 7:
                        self.castling_rights[0] = False
                    elif mv.frm == 0:
                        self.castling_rights[1] = False
                if frm_piece.piecetype == 'r':
                    if mv.frm == 63:
                        self.castling_rights[2] = False
                    elif mv.frm == 56:
                        self.castling_rights[3] = False

                # After capture
                if mv.capture:
                    if captured_piece.is_type('K'):
                        self.castling_rights[0] = False
                        self.castling_rights[1] = False
                    if captured_piece.is_type('k'):
                        self.castling_rights[2] = False
                        self.castling_rights[3] = False
                    if captured_piece.is_type('Rr'):
                        for right, square in enumerate([7, 0, 63, 56]):
                            if mv.to == square:
                                self.castling_rights[right] = False




            # full move count
            if self.side_to_move:
                self.full_move_count += 1

            # half move count
            if mv.capture or frm_piece.piecetype in 'Pp' or mv.is_castle:
                self.half_move_count = 0
            else:
                self.half_move_count += 1

            self.side_to_move = not self.side_to_move

        else:
            print("Not a pseudolegal move!")

    def test_random_pseudolegal_move(self):
        move_list = self.generate_pseudolegal_moves()
        caslting_moves = [move for move in move_list if move.is_castle]
        if len(caslting_moves) > 0:
            mv = random.sample(caslting_moves, 1)
        else:
            mv = random.sample(move_list, 1)
        self.test_do_pseudolegal_move(mv[0], move_list)
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

    def is_type(self, piecetype):
        return self.piecetype in piecetype


class Move:
    def __init__(self, frm, to, capture=False, promotion=None, is_castle=False):
        self.frm = frm
        self.to = to
        self.capture = capture
        self.promotion = promotion
        self.is_castle = is_castle

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
