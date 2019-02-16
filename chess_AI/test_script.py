from chess_AI import *


# while len(a.generate_pseudolegal_moves()) > 0 and a.half_move_count <= 100:
#     a.test_random_pseudolegal_move()
#     print(a)
#     print()
#
# if a.half_move_count <= 100:
#     if a.side_to_move:
#         print("Black to move and no pseudo-legal moves")
#     else:
#         print("White to move and no pseudo-legal moves")
# else:
#     print("Draw by 50-move-rule")
#
# print(a.get_fen())

for i in range(100):
    a = BoardRep.read_fen()
    while len(a.generate_pseudolegal_moves()) > 0 and a.half_move_count <= 100:
        last_move = a.test_random_pseudolegal_move()

