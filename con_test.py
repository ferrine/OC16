from controller import Controller
import pickle
import rassadka_exceptions

if __name__ == "__main__":
    settings = "exceltestdata/settings.xlsx"
    people = "exceltestdata/people.xlsx"
    print("getting settings")
    con = Controller(settings)
    print("got settings")
    print("getting people")
    con.load_people(people)
    con.split_people()
    print("got people")
    print("rassadka...")
    try:
        con.place_them()
        print("...end")
    except rassadka_exceptions.NoFreeAuditory:
        print("...bad end")
    print("making xlsx file...")
    con.dump_seated()
    print("done")
    print("printing self...")
    print(con.whole_summary(), file=open("whole_sum.txt", "w"))
    print("dumping self...")
    with open("dump.pkl", "wb") as d:
        pickle.dump(con, d)
    print("loading self...")
    n = pickle.load(open("dump.pkl", "rb"))
    print(n.auds)
    n.write_maps_with_data("with_klass.xlsx", "klass")
    n.write_maps_with_status("with_status.xlsx")
    n.xlsx_summary()


