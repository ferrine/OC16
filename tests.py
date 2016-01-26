import pickle
import pandas as pd
from rassadka_modules import rassadka_exceptions
from rassadka_modules.controller import Controller
import xlsxwriter


def con_test():
    con = globals()["c"]
    prefix = "test_out\\"
    people = "exceltestdata\\people.xlsx"
    emails = "exceltestdata\\people1.xlsx"
    print("getting people")
    con.load_people(people)
    con.load_emails(emails)
    print("got people")
    print("rassadka...")
    try:
        con.place_loaded_people()
        con.mark_arrival_by_email()
        print("...end")
    except rassadka_exceptions.NoFreeAuditory:
        print("...bad end")
    print("making xlsx file...")
    print("\tРассаженные участники.xlsx")
    con.seated_to_excel(open(prefix + "Рассаженные участники.xlsx", "wb"))

    print("\tРассаженные участники full.xlsx")
    con.seated_to_excel(open(prefix + "Рассаженные участники full.xlsx", "wb"), full=True)

    print("\twhole_sum.txt")
    con.summary_to_txt(file=open(prefix + "whole_sum.txt", "w"))

    print("\twith_klass.xlsx")
    con.maps_with_data_to_excel("klass", open(prefix + "with_klass.xlsx", "wb"))

    print("\twith_status.xlsx")
    con.maps_with_status_to_excel(open(prefix + "with_status.xlsx", "wb"))

    print("\tСтатистика по аудиториям.xlsx")
    con.summary_to_excel(open(prefix + "Статистика по аудиториям.xlsx", "wb"))

    print("\tРаздатка.xlsx")
    con.razdatka_to_excel(open(prefix + "Раздатка.xlsx", "wb"))
    print(con)
    print("add П2")
    con.switch_on_aud("П2")
    print(con)
    print("remove П2")
    con.switch_off_aud("П2")
    print(con)


def update_test():
    con = globals()["c"]
    prefix = "test_out\\"
    for_update = "exceltestdata\\people_for_update.xlsx"
    con.load_people(open(for_update, "rb"))
    s1 = open(prefix + "update_test_out_1.xlsx", "wb")
    s2 = open(prefix + "update_test_out_2.xlsx", "wb")
    con.seated_to_excel(s1)
    con.update_seated_by_coords(forced=True)
    con.seated_to_excel(s2)
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
