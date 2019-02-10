from chess_AI import *

a = BoardRep.read_fen()


while len(a.generate_pseudolegal_moves()) > 0:
    print(a)
    print(a.full_move_count)
    print()
    a.test_random_pseudolegal_move()

if a.side_to_move:
    print("Black to move")
else:
    print("White to move")

print(a.get_fen())