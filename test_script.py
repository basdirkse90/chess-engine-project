from Board_and_moves import *
import cProfile

pr = cProfile.Profile()
pr.enable()
# ... do something ...


# while len(a.generate_pseudolegal_moves()) > 0 and a.half_move_count <= 100:
#     a.test_random_pseudolegal_move()
#     print(a)
#     print()
#

#
# print(a.get_fen())


for i in range(50):
    a = BoardRep.read_fen()
    move_list = a.generate_pseudolegal_moves()
    while len(move_list) > 0 and a.half_move_count <= 100:
        last_move, move_list = a.test_random_move(move_list)
    print(a)
    if a.half_move_count <= 100:
        if a.side_to_move:
            print("Black to move and no pseudo-legal moves")
        else:
            print("White to move and no pseudo-legal moves")
    else:
        print("Draw by 50-move-rule")
    print()
    print()

pr.disable()
pr.dump_stats('test.prof')



