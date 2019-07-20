from Board_and_moves import *
import json


def test_fen(data, prefix="", max_nodes=200000, max_depth=6):
    fen = data["fen"]
    perft = data["perft"]
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
    res_nodes, res_split = a.perft(depth, True)
    if res_nodes == nodes:
        print(prefix + "Perft({}) = {} computed successfully!".format(depth, nodes))
    else:
        print(prefix + "Perft({}) failed. Computed nodes = {}, should be {}.".format(depth, res_nodes, nodes))
        if split is None:
            print(prefix + "Splits not available...")
            return

        # Check splits
        for key, val in res_split.items():
            if split[key] != val:
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
                          format(key, key, val, split[key], failed_fen))
                    test_fen(data[key], prefix=prefix+"\t", max_depth=depth-1)
                else:
                    print(prefix + "Split {} failed. Computed {} = {}, should be {}. Failing FEN: {}".format(
                        key, key, val, split[key], failed_fen))


with open("perft_test/position2.json") as json_file:
    test_fen(json.load(json_file))

