from Board_and_moves import *
import cProfile


def run_random_games(n=50, verbose=0):
    color = ['White', 'Black']
    for i in range(n):
        a = BoardRep.read_fen()
        a.generate_random_game()

        if verbose >= 1:
            if a.half_move_count <= 100:
                print(color[a.side_to_move] + " to move and no pseudo-legal moves:")
                print(a)
                if verbose == 2:
                    print(a.move_sequence)
                    print()
                else:
                    print()
            else:
                if verbose == 2:
                    print("Draw by 50-move-rule:")
                    print(a)
                    print(a.move_sequence)
                    print()
                else:
                    print("Draw by 50-move-rule")


# pr = cProfile.Profile()
# pr.enable()

# run_random_games(n=100, verbose=1)
a = BoardRep.read_fen("rnbqkbnr/ppppppPp/8/8/8/8/PPPPPPP1/RNBQKBNR w KQkq -")
a.do_move(a.find_move('g7', 'h8', 'Q'))
print(a.castling_rights)



# pr.disable()
# pr.dump_stats('test.prof')

