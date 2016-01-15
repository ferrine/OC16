from rassadka_modules.controller import Controller
import pickle
from con_test import test
import sys


if __name__ == "__main__":
    prefix = "test_out\\"
    filename = prefix + "controller.pkl"
    settings = "exceltestdata/settings.xlsx"
    people = "exceltestdata/people.xlsx"
    print("getting settings")
    con = Controller(settings)
    print(con.checker.settings, con.checker.allowed, sep="\n")
    test(con)
    print("dumping")
    con.to_pickle(filename)