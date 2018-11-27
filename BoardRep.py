import numpy as np


class BoardRep:
    #### PieceTypes Constants
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
    WPAWN = 1
    WKNIGHT = 3
    WBISHOP = 4
    WROOK = 5
    WQUEEN = 6
    WKING = 7
    BPAWN = 10
    BKNIGHT = 11
    BBISHOP = 12
    BROOK = 13
    BQUEEN = 14
    BKING = 15

    FEN_TO_PIECE = {
        'P':  1, 'N':  3, 'B':  4, 'R':  5, 'Q':  6, 'K': 7,
        'p': 10, 'n': 11, 'b': 12, 'r': 13, 'q': 14, 'k': 15
    }
    PIECE_TO_FEN = {v: k for k, v in FEN_TO_PIECE.items()}
    PIECE_TO_UNICODE = {
        1:  '\u2659',  3: '\u2658',  4: '\u2657',  5: '\u2656',  6: '\u2655',  7: '\u2654',
        10: '\u265F', 11: '\u265E', 12: '\u265D', 13: '\u265C', 14: '\u265B', 15: '\u265A'
    }

    ## Initialize empty board
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
                10-11 -- White Bishops          26-27 -- Black Bishops
                12-13 -- White Rooks            28-29 -- Black Rooks
                14    -- White Queen            30    -- Black Queen
                15    -- White King             31    -- Black King
                33    -- White extra promotion  34    -- Black extra promotion
            Columns encode piece information:
                0 -- existence: 0 or 1 (0 is not existent, all other values are ignored)
                1 -- position: 0-63 (SquareNumbers)
                2 -- piece type: 0-15 (PieceTypes)
                3 -- lowest valued attacker: 0-15 (PieceTypes)
                4 -- lowest valued defender: 0-15 (PieceTypes)
                5 -- mobility, the number of moves the piece has (including captures)
        piece_count -- 16x1 array indexed by PieceTypes counting the number of each piece
        square_list -- 64x1 array indexed by SquareNumbers containing a PieceType,
                        indicating that the square is occupied by the piece.
        """
        self.side_to_move = False
        self.castling_rights = 0
        self.en_passant_square = None
        self.half_move_count = 0
        self.full_move_count = 1
        self.piece_list = np.zeros((34, 6), dtype=np.uint8)
        self.piece_count = np.zeros(16, dtype=np.uint8)
        self.square_list = np.zeros(64, dtype=np.uint8)

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
                    board.square_list[i] = pieceType
                    board.piece_count[pieceType] += 1
                    f += 1
            r -= 1
            # TODO: Update piece_list or create function that does it

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
                pieceType = self.square_list[r*8+f]
                if pieceType == 0:
                    res += '. '
                else:
                    res += self.PIECE_TO_FEN[pieceType] + ' '
        return res

    def get_fen(self):
        res = ""
        for r in range(7, -1, -1):
            number_of_whites = 0
            for f in range(0, 8):
                piece = self.square_list[r*8+f]
                if piece > 0:
                    if number_of_whites > 0:
                        res += str(number_of_whites)
                    res += self.PIECE_TO_FEN[piece]
                    number_of_whites = 0
                else:
                    number_of_whites += 1
            if number_of_whites > 0:
                res += str(number_of_whites)
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


if __name__ == "__main__":
    a = BoardRep.read_fen()
    print(a)
    b = BoardRep.read_fen("4r1k1/5ppp/b5r1/p1b1n1K1/2p5/6P1/P2N2BP/1R1QR3 w - - 0 1")
    print()
    print()
    print(b)

    print()
    print()
    print(b.square_list)
    print(b.get_fen())
    print()
    print(a.square_list)
    print(a.get_fen())


