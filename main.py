from controller import Controller


if __name__ == "__main__":
    while True:
        try:
            path_to_settings = input("Введите путь до файла с настройками: ")
            C = Controller(path_to_settings)
            break
        except FileNotFoundError as e:
            print(e)
    while True:
        try:
            path_to_people = input("Введите путь до файла с участниками: ")
            C.load_people(path_to_people)
            break
        except FileNotFoundError as e:
            print(e)
    C.place_them()
    C.whole_summary()
    answer = input("Выгрузить рассадку? [y]/n: ")
    if answer != "n":
        while True:
            filename = input("Введите файл вывода: ")
            try:
                C.dump_seated(filename)
                break
            except FileExistsError as e:
                print(e)
