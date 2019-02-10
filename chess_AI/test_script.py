from chess_AI import BoardRep


a = BoardRep.read_fen()
# b = BoardRep.read_fen("4r1k1/NN3ppp/bnb3r1/p1b1n1K1/2p5/P5PP/P2N2BP/1R1QR3 w - - 0 1")
# c = BoardRep.read_fen("rnbqkbnr/pp6/8/8/2p2p2/3pp1pp/PPPPPPPP/RNBQKBNR b KQkq - 0 1")

while len(a.pseudolegal_move()) > 0:
    print(a)
    print()
    a.test_random_pseudolegal_move()

if a.side_to_move:
    print("Black to move")
else:
    print("White to move")

print(a.get_fen())