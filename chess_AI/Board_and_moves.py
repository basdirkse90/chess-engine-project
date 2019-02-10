import numpy as np
import random
from ast import literal_eval


class BoardRep:
    # PieceTypes Constants
    # Bits 2-0 -- Piece type
        # 0 -- Empty
        # 1 -- White Pawn
        # 2 -- Black Pawn
        # 3 -- Knight
        # 4 -- Bishop
        # 5 -- Rook
        # 6 -- Queen
        # 7 -- King
    # Bit 3 -- Piece color
        # 0 -- White
        # 1 -- Black
    WP = 1
    WN = 3
    WB = 4
    WR = 5
    WQ = 6
    WK = 7
    BP = 10
    BN = 11
    BB = 12
    BR = 13
    BQ = 14
    BK = 15

    FEN_TO_PIECE = {
        'P':  1, 'N':  3, 'B':  4, 'R':  5, 'Q':  6, 'K': 7,
        'p': 10, 'n': 11, 'b': 12, 'r': 13, 'q': 14, 'k': 15
    }
    PIECE_TO_FEN = {v: k for k, v in FEN_TO_PIECE.items()}
    PIECE_TO_UNICODE = {
        1:  '\u2659',  3: '\u2658',  4: '\u2657',  5: '\u2656',  6: '\u2655',  7: '\u2654',
        10: '\u265F', 11: '\u265E', 12: '\u265D', 13: '\u265C', 14: '\u265B', 15: '\u265A'
    }

    # Initialize empty board
    def __init__(self):
        """ Docstring here

        Parameters:
        side_to_move -- (False = white, True = black)
        castling_rights -- (bit 0: White short,
                            bit 1: White long,
                            bit 2: Black short,
                            bit 3: Black long)
        en_passant_square -- Target square for en passant capture ((0-63) or None)
        half_move_count -- Counts half moves since last capture or pawn push
        full_move_count -- Counts full moves after black moves
        piece_list -- 34x5 array containing piece information for each piece on board
            Rows encode pieces:
                 0- 7 -- White Pawns            16-23 -- Black Pawns
                 8- 9 -- White Knights          24-25 -- Black Knights
                10-11 -- White Bishops (w-b)    26-27 -- Black Bishops  (w-b)
                12-13 -- White Rooks            28-29 -- Black Rooks
                14    -- White Queen            30    -- Black Queen
                15    -- White King             31    -- Black King
                32    -- White extra promotion  33    -- Black extra promotion
            Columns encode piece information:
                0 -- existence: 0 or 1 (0 is not existent, all other values are ignored)
                1 -- position: 0-63 (SquareNumbers)
                2 -- piece type: 0-15 (PieceTypes)
                3 -- mobility, the number of moves the piece has (including captures)
                4 -- lowest valued attacker: 0-15 (PieceTypes)
                5 -- lowest valued defender: 0-15 (PieceTypes)
        piece_count -- 16x1 array indexed by PieceTypes counting the number of each piece
        square_list -- 64x3 array  containing square information for each square,
            Rows indexed by SquareNumbers [0 <-> a1, 1 <-> b1, ..., 8 <-> a2, ... etc]
            Columns:
                0 -- PieceType if occupied by piece, otherwise 0
                1 -- lowest valued attacker: 0-15 (PieceTypes)
                2 -- lowest valued defender: 0-15 (PieceTypes)

        """
        self.side_to_move = None
        self.castling_rights = 0
        self.en_passant_square = None
        self.half_move_count = 0
        self.full_move_count = 1
        self.piece_list = np.zeros((34, 6), dtype=np.uint8)
        self.piece_count = np.zeros(16, dtype=np.uint8)
        self.square_list = np.zeros((64, 3), dtype=np.uint8)

    @classmethod
    def read_fen(cls, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        board = cls()
        lines = fen.split()
        ranks = lines[0].split("/")
        r = 7
        for rank in ranks:
            f = 0
            for piece in rank:
                # Try if character is a number and skip empty squares
                i = r*8 + f
                try:
                    x = int(piece)
                    f += x
                except ValueError:
                    pieceType = cls.FEN_TO_PIECE[piece]
                    board.square_list[i, 0] = pieceType
                    board.piece_count[pieceType] += 1
                    f += 1
            r -= 1

        # build square list with info
        for i in range(64):
            piece = board.square_list[i, 0]
            r = i // 8
            f = i % 8

            # positions 0-7 for white pawns and 16-23 for black pawns
            if piece == cls.WP or piece == cls.BP:
                j = f + piece // 8 * 16

                # Try to put on correct bin for each file
                succeeded = False
                k = 0
                while not succeeded:
                    if 0 <= f+k < 8 and board.piece_list[j + k, 0] == 0:
                        board.piece_list[j+k, 0] = 1
                        board.piece_list[j+k, 1] = i
                        board.piece_list[j+k, 2] = piece
                        succeeded = True
                    if k > 8:
                        raise IOError("Only the standard piece set is supported (with 1 possible extra promotion)")
                    if k > 0:
                        k = -k
                    else:
                        k = -k + 1

            # positions 8-9   for white knights and 24-25 for black knights
            # positions 12-13 for white rooks   and 28-29 for black knights
            # piecetypes 3/11 knights, 5/13 rooks
            if piece in [cls.WN, cls.WR, cls.BN, cls.BR]:
                j = piece // 8 * 16
                if piece in [cls.WN, cls.BN]:
                    j += 8
                else:
                    j += 12

                if board.piece_list[j, 0] == 0:
                    pos = j
                elif board.piece_list[j+1, 0] == 0:
                    pos = j+1
                elif board.piece_list[32, 0] == 0 and piece in [cls.WN, cls.WR]:
                    pos = 32
                elif board.piece_list[33, 0] == 0 and piece in [cls.BN, cls.BR]:
                    pos = 33
                else:
                    raise IOError("Only the standard piece set is supported (with 1 possible extra promotion)")

                board.piece_list[pos, 0] = 1
                board.piece_list[pos, 1] = i
                board.piece_list[pos, 2] = piece

            # 10-11 -- White Bishops(w-b)     26-27 -- Black Bishops(w-b)
            # bischops can be sorted by color
            if piece == cls.WB or piece == cls.BB:
                j = piece // 8
                c = (r+f+1) % 2

                if board.piece_list[10 + j*16 + c, 0] == 0:
                    board.piece_list[10 + j*16 + c, 0] = 1
                    board.piece_list[10 + j*16 + c, 1] = i
                    board.piece_list[10 + j*16 + c, 2] = piece
                elif board.piece_list[32+j, 0] == 0:
                    board.piece_list[32+j, 0] = 1
                    board.piece_list[32+j, 1] = i
                    board.piece_list[32+j, 2] = piece
                else:
                    raise IOError("Only the standard piece set is supported (with 1 possible extra promotion)")

            # Queens for slot 14 or 30
            # Kings  for slot 15 or 31
            if piece in [cls.WQ, cls.WK, cls.BQ, cls.BK]:
                j = piece // 8
                pos = 14 + j * 16
                if piece == cls.WK or piece == cls.BK:
                    pos += 1

                if board.piece_list[pos, 0] == 0:
                    board.piece_list[pos, 0] = 1
                    board.piece_list[pos, 1] = i
                    board.piece_list[pos, 2] = piece
                # only 1 king
                elif board.piece_list[32 + j, 0] == 0 and piece in [cls.WQ, cls.BQ]:
                    board.piece_list[32 + j, 0] = 1
                    board.piece_list[32 + j, 1] = i
                    board.piece_list[32 + j, 2] = piece
                else:
                    raise IOError("Only the standard piece set is supported (with 1 possible extra promotion)")

        # TODO: Update piece_list once move generation is implemented
        # TODO: Update square_list once move generation is implemented

        board.side_to_move = (lines[1] == 'b')

        for castle_opts in lines[2]:
            if castle_opts == 'K':
                board.castling_rights += 1
            if castle_opts == 'Q':
                board.castling_rights += 2
            if castle_opts == 'k':
                board.castling_rights += 4
            if castle_opts == 'q':
                board.castling_rights += 8

        if lines[3] != '-':
            f = ord(lines[3][0]) - 97
            r = int(lines[3][1]) - 1
            board.en_passant_square = r*8 + f

        board.half_move_count = int(lines[4])
        board.full_move_count = int(lines[5])
        return board

    def __str__(self):
        res = ""
        for r in range(7, -1, -1):
            for f in range(8):
                if f == 0 and r < 7:
                    res += '\n'
                pieceType = self.square_list[r*8+f, 0]
                if pieceType == 0:
                    res += '. '
                else:
                    res += self.PIECE_TO_FEN[pieceType] + ' '
        return res

    def get_fen(self):
        res = ""
        for r in range(7, -1, -1):
            number_of_empty = 0
            for f in range(0, 8):
                piece = self.square_list[r*8+f, 0]
                if piece > 0:
                    if number_of_empty > 0:
                        res += str(number_of_empty)
                    res += self.PIECE_TO_FEN[piece]
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

        if self.castling_rights == 0:
            res += "-"
        else:
            t = '{0:04b}'.format(self.castling_rights)
            if t[3] == '1':
                res += "K"
            if t[2] == '1':
                res += "Q"
            if t[1] == '1':
                res += "k"
            if t[0] == '1':
                res += "q"
        if self.en_passant_square is None:
            res += " -"
        else:
            f = self.en_passant_square % 8
            r = self.en_passant_square // 8
            res += " " + chr(f+97) + str(r+1)

        res += " " + str(self.half_move_count) + " " + str(self.full_move_count)
        return res

    def pseudolegal_move(self):
        moves = []
        for i in range(64):
            r = i // 8
            f = i % 8
            color = int(self.side_to_move)      # white = 0, black = 1

            # Pawn moves
            if self.square_list[i, 0] == self.WP + (color * 9):

                if r == 6 - 5*color:  # promote
                    # TODO implement promotion
                    pass
                else:
                    # move forward
                    if self.square_list[i+(1-2*color)*8, 0] == 0:
                        moves.append((i, i+(1-2*color)*8))
                        # move 2 if allowed
                        if r == 1 + 5*color and self.square_list[i+(1-2*color)*16, 0] == 0:
                            moves.append((i, i+(1-2*color)*16))
                            # TODO: how to pass en passant possibility?
                    # capture right
                    if f < 7 and (self.square_list[i+9-16*color, 0] != 0 and self.square_list[i+9-16*color, 0] // 8 != color or self.en_passant_square == i+9-16*color):
                        moves.append((i, i+9-16*color))
                    # capture left
                    if f > 0 and (self.square_list[i+7-16*color, 0] != 0 and self.square_list[i+7-16*color, 0] // 8 != color or self.en_passant_square == i+7-16*color):
                        moves.append((i, i+7-16*color))

        return moves

    def test_do_pseudolegal_move(self, frm, to):
        move_list = self.pseudolegal_move()

        if (frm, to) in move_list:
            frm_piece = self.square_list[frm, 0]
            self.square_list[frm, 0] = 0
            self.square_list[to, 0] = frm_piece

            if to - frm == 16:
                self.en_passant_square = to - 8
            if to - frm == -16:
                self.en_passant_square = to + 8

            if self.square_list[to, 0] == self.en_passant_square:
                print("En passant!")
                if to < 32:
                    self.square_list[to + 8, 0] = 0
                else:
                    self.square_list[to - 8, 0] = 0

            if self.side_to_move:
                self.full_move_count += 1

            self.side_to_move = not self.side_to_move

        else:
            print("Not a pseudolegal move!")

    def test_pseudolegal_move(self):
        move_list = self.pseudolegal_move()
        print(move_list)
        mv = literal_eval(input("What move would you like to make? "))
        self.test_do_pseudolegal_move(*mv)

    def test_random_pseudolegal_move(self):
        move_list = self.pseudolegal_move()
        mv = random.sample(move_list, 1)
        self.test_do_pseudolegal_move(*mv[0])
        return mv[0]





