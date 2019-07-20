import random
from itertools import product
from contextlib import suppress
from math import ceil
import copy


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
        self.side_to_move = False
        self.castling_rights = [True]*4
        self.en_passant_square = None
        self.half_move_count = 0
        self.full_move_count = 1
        self.piece_list = []
        self.piece_count = {key: 0 for key in self.PIECES}
        self.square_list = [None]*64
        self.in_check = False

        self.pseudolegal_moves = []
        self.move_sequence = []
        self.fen_sequence = []

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

        board.pseudolegal_moves = board.generate_pseudolegal_moves()
        board.fen_sequence.append(fen)

        # TODO: Check if King is in check
        # TODO: Check if position is legal? [e.g. are there Kings, is the side not to move not in check?]

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
        on_move = self.side_to_move
        squares = self.square_list
        clr = int(on_move)  # white = 0, black = 1

        pawn = 'Pp'[clr]
        rooklike = 'Rr'[clr] + 'Qq'[clr]
        bishoplike = 'Bb'[clr] + 'Qq'[clr]
        king = 'Kk'[clr]
        knight = 'Nn'[clr]

        proms = 'Qq'[clr] + 'Rr'[clr] + 'Bb'[clr] + knight

        for moving_piece in self.piece_list:
            i = moving_piece.position

            r = i // 8
            f = i % 8

            # Pawn moves
            if moving_piece.piecetype == pawn:
                # move forward
                if squares[i + 8*(-1)**clr] is None:
                    if r == 6-5*clr:
                        for prom in proms:
                            moves.append(Move(i, i + 8*(-1)**clr, moving_piece, promotion=prom))
                    else:
                        moves.append(Move(i, i + 8*(-1)**clr, moving_piece))
                        # move 2 if allowed
                        if r == 1+5*clr and squares[i + 16*(-1)**clr] is None:
                            moves.append(Move(i, i + 16*(-1)**clr, moving_piece))

                # capture right
                if f < 7 and squares[i + 9-16*clr] is not None and squares[i + 9-16*clr].color != on_move:
                    if r == 6-5*clr:
                        for prom in proms:
                            moves.append(
                                Move(i, i + 9-16*clr, moving_piece,
                                     capture=squares[i + 9-16*clr].piecetype, promotion=prom))
                    else:
                        moves.append(Move(i, i + 9-16*clr, moving_piece, capture=squares[i + 9-16*clr].piecetype))

                # capture right en passant
                if f < 7 and self.en_passant_square == i + 9-16*clr:
                    moves.append(Move(i, i + 9-16*clr, moving_piece, capture='pP'[clr], is_enpassant=True))

                # capture left
                if f > 0 and squares[i + 7-16*clr] is not None and squares[i + 7-16*clr].color != on_move:
                    if r == 6-5*clr:
                        for prom in proms:
                            moves.append(Move(i, i + 7-16*clr, moving_piece,
                                              capture=squares[i + 7-16*clr].piecetype, promotion=prom))
                    else:
                        moves.append(Move(i, i + 7-16*clr, moving_piece, capture=squares[i + 7-16*clr].piecetype))

                # capture left en passant
                if f > 0 and self.en_passant_square == i + 7-16*clr:
                    moves.append(Move(i, i + 7-16*clr, moving_piece, capture='pP'[clr], is_enpassant=True))

            # Rook moves or rook-like queen moves
            if moving_piece.piecetype in rooklike:
                # move right
                offset = 1
                while f + offset < 8 and squares[i + offset] is None:
                    moves.append(Move(i, i + offset, moving_piece))
                    offset += 1
                if f + offset < 8 and squares[i + offset].color != on_move:
                    moves.append(Move(i, i + offset, moving_piece, capture=squares[i + offset].piecetype))

                # move left
                offset = -1
                while f + offset >= 0 and squares[i + offset] is None:
                    moves.append(Move(i, i + offset, moving_piece))
                    offset -= 1
                if f + offset >= 0 and squares[i + offset].color != on_move:
                    moves.append(Move(i, i + offset, moving_piece, capture=squares[i + offset].piecetype))

                # move up
                offset = 1
                while r + offset < 8 and squares[i + 8 * offset] is None:
                    moves.append(Move(i, i + 8 * offset, moving_piece))
                    offset += 1
                if r + offset < 8 and squares[i + 8 * offset].color != on_move:
                    moves.append(Move(i, i + 8 * offset, moving_piece, capture=squares[i + 8 * offset].piecetype))

                # move down
                offset = -1
                while r + offset >= 0 and squares[i + 8 * offset] is None:
                    moves.append(Move(i, i + 8 * offset, moving_piece))
                    offset -= 1
                if r + offset >= 0 and squares[i + 8 * offset].color != on_move:
                    moves.append(Move(i, i + 8 * offset, moving_piece, capture=squares[i + 8 * offset].piecetype))

            # Bishop moves or bishop-like queen moves
            if moving_piece.piecetype in bishoplike:
                # move upright
                offset = 1
                while f + offset < 8 and r + offset < 8 and squares[i + 9 * offset] is None:
                    moves.append(Move(i, i + 9 * offset, moving_piece))
                    offset += 1
                if f + offset < 8 and r + offset < 8 and squares[i + 9 * offset].color != on_move:
                    moves.append(Move(i, i + 9 * offset, moving_piece, capture=squares[i + 9 * offset].piecetype))

                # move upleft
                offset = 1
                while f - offset >= 0 and r + offset < 8 and squares[i + 7 * offset] is None:
                    moves.append(Move(i, i + 7 * offset, moving_piece))
                    offset += 1
                if f - offset >= 0 and r + offset < 8 and squares[i + 7 * offset].color != on_move:
                    moves.append(Move(i, i + 7 * offset, moving_piece, capture=squares[i + 7 * offset].piecetype))

                # move downright
                offset = 1
                while f + offset < 8 and r - offset >= 0 and squares[i - 7 * offset] is None:
                    moves.append(Move(i, i - 7 * offset, moving_piece))
                    offset += 1
                if f + offset < 8 and r - offset >= 0 and squares[i - 7 * offset].color != on_move:
                    moves.append(Move(i, i - 7 * offset, moving_piece, capture=squares[i - 7 * offset].piecetype))

                # move downleft
                offset = 1
                while f - offset >= 0 and r - offset >= 0 and squares[i - 9 * offset] is None:
                    moves.append(Move(i, i - 9 * offset, moving_piece))
                    offset += 1
                if f - offset >= 0 and r - offset >= 0 and squares[i - 9 * offset].color != on_move:
                    moves.append(Move(i, i - 9 * offset, moving_piece, capture=squares[i - 9 * offset].piecetype))

            # King moves
            if moving_piece.piecetype == king:
                # -- not castling moves first --
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
                    if squares[i + offset] is not None:
                        if squares[i + offset].color != on_move:
                            moves.append(Move(i, i + offset, moving_piece, capture=squares[i + offset].piecetype))
                    else:
                        moves.append(Move(i, i + offset, moving_piece))

                # -- Castling moves --
                if self.castling_rights[2 * clr] and squares[7 * 8 * clr + 5] is None and squares[
                    7 * 8 * clr + 6] is None:
                    moves.append(Move(7 * 8 * clr + 4, 7 * 8 * clr + 6, moving_piece, is_castle=True))

                if self.castling_rights[2 * clr + 1] and all(
                        squares[7 * 8 * clr + x] is None for x in [1, 2, 3]):
                    moves.append(Move(7 * 8 * clr + 4, 7 * 8 * clr + 2, moving_piece, is_castle=True))

            # Knight moves
            if moving_piece.piecetype == knight:
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
                    if squares[i + offset] is not None:
                        if squares[i + offset].color != on_move:
                            moves.append(Move(i, i + offset, moving_piece, capture=squares[i + offset].piecetype))
                    else:
                        moves.append(Move(i, i + offset, moving_piece))

        return moves

    def do_pseudolegal_move(self, mv):
        move_list = self.pseudolegal_moves
        assert mv in move_list  # This check is handled by do_move()

        # Do move
        squares = self.square_list

        frm_piece = squares[mv.frm]
        squares[mv.frm] = None
        if mv.capture is not None:
            if not mv.is_enpassant:
                captured_piece = squares[mv.to]
            else:
                captured_piece = squares[mv.to - 8 * (-1) ** self.side_to_move]
                squares[mv.to - 8 * (-1) ** self.side_to_move] = None
            self.piece_count[captured_piece.piecetype] -= 1
            self.piece_list.remove(captured_piece)
        else:
            captured_piece = None
        squares[mv.to] = frm_piece
        try:
            frm_piece.move(mv.to)
        except AttributeError:
            print(self.get_fen())
            exit()

        # Move rook if it was a castling move
        if mv.is_castle:
            if mv.to - mv.frm == 2:  # short castle
                rook = squares[mv.to + 1]
                squares[mv.to + 1] = None
                squares[mv.to - 1] = rook
                rook.move(mv.to-1)
            elif mv.to - mv.frm == -2:  # long castle
                rook = squares[mv.to - 2]
                squares[mv.to - 2] = None
                squares[mv.to + 1] = rook
                rook.move(mv.to+1)

        # Handle promotion
        if mv.promotion is not None:
            promotedPiece = Piece(mv.promotion, mv.to)
            squares[mv.to] = promotedPiece
            self.piece_count[frm_piece.piecetype] -= 1
            self.piece_count[promotedPiece.piecetype] += 1
            self.piece_list.remove(frm_piece)
            self.piece_list.append(promotedPiece)

        return frm_piece, captured_piece

    def undo_pseudolegal_move(self, mv):
        # Unpromote
        if mv.promotion is not None:
            promotedPiece = self.square_list[mv.to]
            self.piece_count[promotedPiece.piecetype] -= 1
            self.piece_list.remove(promotedPiece)
            oldPawn = Piece('Pp'[self.side_to_move], mv.to)
            self.square_list[mv.to] = oldPawn
            self.piece_count[oldPawn.piecetype] += 1
            self.piece_list.append(oldPawn)

        # Unmove castling rook
        if mv.is_castle:
            if mv.to - mv.frm == 2:  # short castle
                rook = self.square_list[mv.to-1]
                self.square_list[mv.to-1] = None
                self.square_list[mv.to+1] = rook
                rook.move(mv.to+1)
            elif mv.to - mv.frm == -2:  # long castle
                rook = self.square_list[mv.to+1]
                self.square_list[mv.to+1] = None
                self.square_list[mv.to-2] = rook
                rook.move(mv.to-2)

        to_piece = self.square_list[mv.to]
        self.square_list[mv.to] = None
        self.square_list[mv.frm] = to_piece
        to_piece.move(mv.frm)

        if mv.capture is not None:
            if not mv.is_enpassant:
                restored_piece = Piece(mv.capture, mv.to)
                self.square_list[mv.to] = restored_piece
            else:
                restored_piece = Piece('pP'[self.side_to_move], mv.to-8*(-1)**self.side_to_move)
                self.square_list[mv.to-8*(-1)**self.side_to_move] = restored_piece
            self.piece_count[restored_piece.piecetype] += 1
            self.piece_list.append(restored_piece)

    def do_move(self, mv, update_movelist=True):
        # if update_movelist = False, then next_move_list is returned instead of updated.

        move_list = self.pseudolegal_moves

        # First check if even pseudolegal
        if mv not in move_list:
            return False

        # Then do move
        moved_piece, captured_piece = self.do_pseudolegal_move(mv)

        # already flip side to move
        self.side_to_move = not self.side_to_move

        # already set en passant square (save old in case of undo move)
        old_enpassant = self.en_passant_square
        if moved_piece.piecetype == 'P' and mv.to - mv.frm == 16:
            self.en_passant_square = mv.to - 8
        elif moved_piece.piecetype == 'p' and mv.to - mv.frm == -16:
            self.en_passant_square = mv.to + 8
        else:
            self.en_passant_square = None

        # Generate new move list (with correct side to move and en-passant square)
        next_move_list = self.generate_pseudolegal_moves()

        if mv.is_castle:
            # Can not castle through check
            c2 = mv.to - mv.frm == 2 and any(nxt_mv.to == mv.to - 1 for nxt_mv in next_move_list)
            c3 = mv.to - mv.frm == -2 and any(nxt_mv.to == mv.to + 1 for nxt_mv in next_move_list)
            if c2 or c3:
                # undo side_to_move, en_passant and pseudo_legal move
                self.side_to_move = not self.side_to_move
                self.en_passant_square = old_enpassant
                self.undo_pseudolegal_move(mv)
                move_list.remove(mv)
                return False

        if any(nxt_mv.capture == 'kK'[self.side_to_move] for nxt_mv in next_move_list):
            # undo side_to_move, en_passant and pseudo_legal move
            self.side_to_move = not self.side_to_move
            self.en_passant_square = old_enpassant
            self.undo_pseudolegal_move(mv)
            move_list.remove(mv)
            return False

        # --- Setting the remaining board attributes after legal move!

        # Remove castling rights if applicable
        if any(self.castling_rights):  # avoid unnecessary checking
            # After king move
            if moved_piece.piecetype == 'K':
                self.castling_rights[0] = False
                self.castling_rights[1] = False
            if moved_piece.piecetype == 'k':
                self.castling_rights[2] = False
                self.castling_rights[3] = False

            # After rook move
            if moved_piece.piecetype == 'R':
                if mv.frm == 7:
                    self.castling_rights[0] = False
                elif mv.frm == 0:
                    self.castling_rights[1] = False
            if moved_piece.piecetype == 'r':
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
        if not self.side_to_move:  # side_to_move was already flipped!
            self.full_move_count += 1

        # half move count
        if mv.capture is not None or moved_piece.piecetype in 'Pp' or mv.is_castle:
            self.half_move_count = 0
        else:
            self.half_move_count += 1

        self.move_sequence.append(mv)
        self.fen_sequence.append(self.get_fen())

        if update_movelist:
            self.pseudolegal_moves = next_move_list
            return True
        else:
            return next_move_list

    def undo_move(self, regenerate_movelist=True):
        try:
            last_move = self.move_sequence.pop()
            last_fen = self.fen_sequence.pop()
        except IndexError:
            return

        lines = last_fen.split()

        # restore castling rights and en_passant square
        for i, opt in enumerate('KQkq'):
            self.castling_rights[i] = opt in lines[2]
        self.en_passant_square = self.SQUARE_TO_NUM[lines[3]]

        # restore move counts
        self.half_move_count = int(lines[4])
        self.full_move_count = int(lines[5])

        # flip side to move back
        self.side_to_move = not self.side_to_move

        # undo_pseudolegal_move
        self.undo_pseudolegal_move(last_move)

        # regenerate pseudo_legal moves
        if regenerate_movelist:
            self.pseudolegal_moves = self.generate_pseudolegal_moves()

    def is_legal(self, mv):
        res = self.do_move(mv)
        if res:
            self.undo_move()
        return res

    def test_random_move(self, special_moves_first=True):
        move_list = self.pseudolegal_moves

        if len(move_list) == 0:
            return

        special_moves = []
        if special_moves_first:
            special_moves = [move for move in move_list if move.is_castle or move.capture is not None or move.promotion is not None]

        if len(special_moves) > 0:
            mv = random.sample(special_moves, 1)[0]
        else:
            mv = random.sample(move_list, 1)[0]

        try:
            self.do_move(mv)
        except IllegalMoveError:
            self.test_random_move()

    def ask_for_move(self):
        move_list = self.pseudolegal_moves

        if len(move_list) == 0:
            return

        move_list.sort()
        printable_moves = []
        for i, mv in enumerate(move_list):
            printable_moves.append('{:2d}. {}\t'.format(i+1, mv))

        col = ceil(len(printable_moves) / 5)

        for i in range(col):
            res = ''
            for j in range(5):
                with suppress(IndexError):
                    res += printable_moves[j*col+i]
            print(res)

        while True:
            try:
                x = input('What move would you like to make?')
                proposed_move = move_list[int(x)-1]
                break
            except (ValueError, IndexError):
                if x == 'exit':
                    raise(KeyboardInterrupt('User aborted'))
                print('Invalid input!')

        try:
            self.do_move(proposed_move)
        except IllegalMoveError:
            print("Move {} turned out not to be legal!".format(proposed_move))
            self.ask_for_move()

        print(proposed_move)

    def generate_random_game(self):
        while len(self.pseudolegal_moves) > 0 and self.half_move_count <= 100:
            self.test_random_move()

    def perft(self, n, split=False):
        if n == 0:
            return 1

        nodes = 0
        i = 0

        if split:
            split_dict = {}

        while i < len(self.pseudolegal_moves):
            move = self.pseudolegal_moves[i]
            temp = self.do_move(move, update_movelist=False)
            if temp:
                old_moves = self.pseudolegal_moves
                self.pseudolegal_moves = temp
                add = self.perft(n-1)
                nodes += add
                self.undo_move(regenerate_movelist=False)
                self.pseudolegal_moves = old_moves
                i += 1

            # No need to increase i if the move was not legal, since it is then removed from the list
            if split:
                k = str(move)
                k = k[0:2] + k[3:5]
                split_dict[k] = add

        if split:
            return nodes, split_dict
        else:
            return nodes


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
    def __init__(self, frm, to, moving_piece, capture=None, promotion=None, is_castle=False, is_enpassant=False):
        self.frm = frm  # int of square
        self.to = to    # int of square
        self.moving_piece = moving_piece  # Piece object that is supposed to move
        self.moving_piece_FEN = moving_piece.piecetype.upper()  # FEN of moved piece (for notation)
        self.capture = capture  # FEN letter of captured piece
        self.promotion = promotion  # FEN letter of promoted piece
        self.is_castle = is_castle  # Bool
        self.is_enpassant = is_enpassant  # Bool

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def fen(self):
        # Prints a best-effort FEN (does not check if multiple pieces of same type can move to target square)
        if self.is_castle:
            if self.to % 8 > 4:
                return "O-O"
            else:
                return "O-O-O"
        res = ""
        if self.moving_piece_FEN != "P":
            res += self.moving_piece_FEN
        if self.capture:
            res += 'x'
        res += BoardRep.NUM_TO_SQUARE[self.to]
        if self.promotion is not None:
            res += ('=' + self.promotion.upper())
        return res

    def __str__(self):
        res = BoardRep.NUM_TO_SQUARE[self.frm]
        if self.capture:
            res += 'x'
        else:
            res += '-'
        res += BoardRep.NUM_TO_SQUARE[self.to]
        if self.promotion is not None:
            res += ('=' + self.promotion.upper())
        return res

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return str(self) < str(other)


class IllegalMoveError(Exception):
    def __init__(self, mv):
        super(IllegalMoveError, self).__init__("The move " + str(mv) + " is not legal!")