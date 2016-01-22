import pickle

from rassadka_modules import rassadka_exceptions
from rassadka_modules.controller import Controller


def con_test(con):
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
    print("dumping self...")
    with open(prefix + "to_pickle.pkl", "wb") as d:
        pickle.dump(con, d)
    print("loading self...")
    n = pickle.load(open(prefix + "to_pickle.pkl", "rb"))
    n.write_maps_with_data(open(prefix + "with_klass.xlsx", "wb"), "klass")
    n.write_maps_with_status(open(prefix + "with_status.xlsx", "wb"))
    n.xlsx_summary(open(prefix + "Статистика по аудиториям.xlsx", "wb"))


if __name__ == "__main__":

    settings = "exceltestdata/settings.xlsx"

    print("getting settings")
    con = Controller(open(settings, "rb"))
    print("got settings")
    con_test(con)
