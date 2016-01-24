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
        print(con.coords_by_email("sacha_pltnicov@mail.ru"))
        print(con.coords_by_email("strange_email"))
        sys.exit(0)
    main()
    con_test()
    saving()
