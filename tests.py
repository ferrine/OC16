import pickle
import pandas as pd
from rassadka_modules import rassadka_exceptions
from rassadka_modules.controller import Controller
import xlsxwriter


def con_test():
    con = globals()["c"]
    prefix = "test_out\\"
    people = "exceltestdata/people.xlsx"
    print("getting people")
    con.load_people(people)
    print("got people")
    print("rassadka...")
    try:
        con.place_them()
        print("...end")
    except rassadka_exceptions.NoFreeAuditory:
        print("...bad end")
    print("making xlsx file...")
    con.dump_seated(open(prefix + "Рассаженные участники.xlsx", "wb"))
    print("done")
    print("printing self...")
    print(con.whole_summary(), file=open(prefix + "whole_sum.txt", "w"))
    con.write_maps_with_data(open(prefix + "with_klass.xlsx", "wb"), "klass")
    con.write_maps_with_status(open(prefix + "with_status.xlsx", "wb"))
    con.xlsx_summary(open(prefix + "Статистика по аудиториям.xlsx", "wb"))


def update_test():
    con = globals()["c"]
    prefix = "test_out\\"
    for_update = "exceltestdata\\people_for_update.xlsx"
    con.load_people(open(for_update, "rb"))
    s1 = open(prefix + "update_test_out_1.xlsx", "wb")
    s2 = open(prefix + "update_test_out_2.xlsx", "wb")
    con.dump_seated(s1)
    con.update_all(forced=True)
    con.dump_seated(s2)
    s1.close()
    s2.close()


def saving():
    prefix = "test_out\\"
    filename = prefix + "controller.pkl"
    globals()["c"].to_pickle(open(filename, "wb"))


def main():
    settings = "exceltestdata/settings.xlsx"
    print("getting settings")
    globals()["c"] = Controller(open(settings, "rb"))
    print("got settings")

if __name__ == "__main__":
    main()
    con_test()
