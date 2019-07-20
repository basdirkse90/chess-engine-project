import unittest
import Board_and_moves as Chess


class TestBoardRep(unittest.TestCase):

    def test_do_move(self):
        board = Chess.BoardRep.read_fen("rn1qkb1r/p1pp1ppp/bp2pn2/8/4P3/5NPB/PPPP1P1P/RNBQK2R w KQkq - 0 1")
        self.assertIsInstance(board, Chess.BoardRep)

        s2n = Chess.BoardRep.SQUARE_TO_NUM
        sl = board.square_list

        # Test if castling through check is not legal
        move = Chess.Move(s2n['e1'], s2n['g1'], sl[s2n['e1']], is_castle=True)
        self.assertFalse(board.do_move(move))

        # Test if walking into check is not legal
        move = Chess.Move(s2n['e1'], s2n['f1'], sl[s2n['e1']])
        self.assertFalse(board.do_move(move))

        # Tests if it raises error if the move is not even pseudo-legal
        move = Chess.Move(s2n['e1'], s2n['b4'], sl[s2n['e1']])
        self.assertFalse(board.do_move(move))

    def test_is_legal(self):
        board = Chess.BoardRep.read_fen("rn1qkb1r/p1pp1ppp/bp2pn2/8/4P3/5NPB/PPPP1P1P/RNBQK2R w KQkq - 0 1")
        self.assertIsInstance(board, Chess.BoardRep)

        s2n = Chess.BoardRep.SQUARE_TO_NUM
        sl = board.square_list

        # Test if castling through check is not legal
        move = Chess.Move(s2n['e1'], s2n['g1'], sl[s2n['e1']], is_castle=True)
        self.assertFalse(board.is_legal(move))

        # Test if walking into check is not legal
        move = Chess.Move(s2n['e1'], s2n['f1'], sl[s2n['e1']])
        self.assertFalse(board.is_legal(move))

        # Tests if it raises error if the move is not even pseudo-legal
        move = Chess.Move(s2n['e1'], s2n['b4'], sl[s2n['e1']])
        self.assertFalse(board.is_legal(move))

    def test_perft(self):
        # test perft(3) on six positions

        fen_list = {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": (4, 197281),
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1": (3, 97862)
        }

        for fen, (n, res) in fen_list.items():
            board = Chess.BoardRep.read_fen(fen)
            self.assertEqual(res, board.perft(n))


if __name__ == '__main__':
    unittest.main()
