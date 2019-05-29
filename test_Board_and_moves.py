import unittest
import Board_and_moves as Chess


class TestBoardRep(unittest.TestCase):

    def test_do_move(self):
        board = Chess.BoardRep.read_fen("rn1qkb1r/p1pp1ppp/bp2pn2/8/4P3/5NPB/PPPP1P1P/RNBQK2R w KQkq - 0 1")
        self.assertIsInstance(board, Chess.BoardRep)

        s2n = Chess.BoardRep.SQUARE_TO_NUM

        # Test if castling through check is not legal
        move = Chess.Move(s2n['e1'], s2n['g1'], is_castle=True)
        with self.assertRaises(Chess.IllegalMoveError):
            board.do_move(move)

        # Test if walking into check is not legal
        move = Chess.Move(s2n['e1'], s2n['f1'])
        with self.assertRaises(Chess.IllegalMoveError):
            board.do_move(move)

        # Tests if it raises error if the move is not even pseudo-legal
        move = Chess.Move(s2n['e1'], s2n['b4'])
        with self.assertRaises(Chess.IllegalMoveError):
            board.do_move(move)

    def test_is_legal(self):
        board = Chess.BoardRep.read_fen("rn1qkb1r/p1pp1ppp/bp2pn2/8/4P3/5NPB/PPPP1P1P/RNBQK2R w KQkq - 0 1")
        self.assertIsInstance(board, Chess.BoardRep)

        s2n = Chess.BoardRep.SQUARE_TO_NUM

        # Test if castling through check is not legal
        move = Chess.Move(s2n['e1'], s2n['g1'], is_castle=True)
        self.assertFalse(board.is_legal(move))

        # Test if walking into check is not legal
        move = Chess.Move(s2n['e1'], s2n['f1'])
        self.assertFalse(board.is_legal(move))

        # Tests if it raises error if the move is not even pseudo-legal
        move = Chess.Move(s2n['e1'], s2n['b4'])
        self.assertFalse(board.is_legal(move))


if __name__ == '__main__':
    unittest.main()
