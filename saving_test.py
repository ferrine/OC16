from rassadka_modules.controller import Controller
import pickle
from tests import con_test, main, saving
import sys


if __name__ == "__main__":
    prefix = "test_out\\"
    filename = prefix + "controller.pkl"
    if len(sys.argv) > 1:
        con = Controller(open(filename, "rb"), from_pickle=True)
        print(con)
        print(con.seat_by_position(con.seated_people.iloc[0].to_dict()).data["fam"],
              con.seat_by_position(con.seated_people.iloc[0].to_dict()).aud,
              con.seat_by_position(con.seated_people.iloc[0].to_dict()))
        sys.exit(0)
    main()
    con_test()
    saving()
