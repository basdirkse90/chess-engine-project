from Board_and_moves import *
import json
import time


def run_test(data, prefix="", max_nodes=200000, max_depth=6, print_pos=True):
    fen = data["fen"]
    perft = data["perft"]
    if print_pos:
        print(prefix + "Testing position: " + fen)

    depth = 0
    nodes = 1
    split = None
    for d in perft:
        if d["nodes"] > max_nodes or d["depth"] > max_depth:  # To cap slow searches
            break
        depth = d["depth"]
        nodes = d["nodes"]
        split = d["split"]

    a = BoardRep.read_fen(fen)
    res_nodes, res_split = a.perft(depth, split=True)
    if res_nodes == nodes:
        print(prefix + "Perft({}) = {} computed successfully!".format(depth, nodes))
        return nodes
    else:
        print(prefix + "Perft({}) failed. Computed nodes = {}, should be {}.".format(depth, res_nodes, nodes))
        # run_test(data, max_depth=depth-1, print_pos=False)

        if split is None:
            print(prefix + "Splits not available...")
            return

        # Check splits
        for key, val in res_split.items():
            try:
                split_val = split[key]
            except KeyError:
                split_val = 0

            if split_val != val:
                b = BoardRep.read_fen(fen)
                mvto = key[0:2]
                mvfrm = key[2:4]
                if len(key) > 4:
                    prom = key[4]
                else:
                    prom = None
                move = b.find_move(mvto, mvfrm, prom)
                b.do_move(move)
                failed_fen = b.get_fen()

                if key in data.keys():
                    print(prefix + "Split {} failed. Computed {} = {}, should be {}. Testing position after move:".
                          format(key, key, val, split_val, failed_fen))
                    run_test(data[key], prefix=prefix + "\t", max_depth=depth - 1)
                else:
                    print(prefix + "Split {} failed. Computed {} = {}, should be {}. Failing FEN: {}".format(
                        key, key, val, split_val, failed_fen))


files = [
    # "perft_test/initposition.json",
    "perft_test/position2.json",
    # "perft_test/position3.json",
    # "perft_test/position4.json",
    # "perft_test/position5.json",
    # "perft_test/position6.json"
]

for f in files:
    with open(f) as json_file:
        print("Opening file: {}".format(f.split("/")[1]))
        t1 = time.time()
        data = json.load(json_file)

        n = run_test(data, max_nodes=5000000, max_depth=4)
        dt = time.time() - t1
        if n is not None:
            print("Nps: {:.0f}".format(n/dt))
        print("Test took: {:.2f} (s)".format(dt))
        print()
