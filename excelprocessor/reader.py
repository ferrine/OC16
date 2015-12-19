#!python3.exe
import pandas as pd
import numpy as np
import sys


def split_by(table, _output, clean, axes=False, named=False, *, debug=False):
    """

    argument named: именовать ли таблицы? (в таком случае будет взята верхняя левая ячейка как имя)
    argument _output: куда выводить чистые табицы
    type table: Pandas DataFrame
    arg clean: насколько чиста таблица? [чисто по Y, чисто по X]
    argument axes: column?
    """
    assert type(table) is pd.DataFrame, "К сожалению, функция работает только с pandas.DataFrame"
    parse_list = []
    to_slise = []
    clean[axes] = True #Использую прием, что по индексу axes я меняю только текущую итерацию, при первом прогоне полюбому пройдет второй
    if debug:
        print("Checking: ", range(table.shape[axes]))
    for i in range(table.shape[axes]):
        if debug:
            print((table.iloc[:, i] if axes else table.iloc[i, :]).values)
        if not np.all(pd.isnull((table.iloc[:, i] if axes else table.iloc[i, :]))):     # если строка/столбец не пустая, то возвращает Ложь
            to_slise.append(i)
            if debug:
                print({0: "Row ", 1: "Col "}[axes] + str(i) +
                      "\t is not empty and to_slise = " + str(to_slise) + "\n" +
                      "-"*10)
        else:
            clean = [False, False]  # Если что-то не так, надо прогнать еще два раза
            if to_slise:
                if debug:
                    print("Appending: " + str(to_slise))
                parse_list.append((table.iloc[:, to_slise] if axes else table.iloc[to_slise, :]))
                to_slise = []
            if debug:
                print({0: "Row ", 1: "Col "}[axes] + str(i) + "\t is empty and to_slise = " + str(to_slise) + "\n" +
                      "-"*10)
    else:
        if to_slise:
            if debug:
                print("Appending: " + str(to_slise))
            parse_list.append((table.iloc[:, to_slise] if axes else table.iloc[to_slise, :]))
    if clean[0] and clean[1]:  #Проверим, отчистили ли мы эту таблицу
        move_x = int(np.all(pd.isnull(parse_list[0].iloc[1:, 0])))  # Проверяем крайние левый и верхний ряд, тк там
        move_y = int(np.all(pd.isnull(parse_list[0].iloc[0, 1:])))  # может быть имя и надо удалять пустоты
        if debug:
            print("x " + "-"*20 + "\n", parse_list[0].iloc[:, 0])
            print("y " + "-"*20 + "\n", parse_list[0].iloc[0, :])
            print("x : ", move_x, "\t y: ", move_y)
        if named:
            name = parse_list[0].iloc[0, 0]
        else:
            name = len(_output)
        _output[name] = parse_list[0].iloc[move_y:, move_x:].as_matrix()
    elif parse_list:  # Таблица не чиста, прогоняем все для тех, что выделились или продолжаем очищать единственную
        for item in parse_list:
            if debug:
                print("Clean for item is: ", clean, "\n", item)
            split_by(item, _output=_output, axes=(not axes), named=named, clean=clean, debug=debug)


def splitter(*args, **kwargs):
    result = dict()
    kwargs["_output"] = result
    kwargs["clean"] = [False, False]
    split_by(*args, **kwargs)
    return result

if __name__ == '__main__':
    if "debug" in sys.argv:
        debug = True
    else:
        debug = False
    xl = pd.ExcelFile("../exceltestdata/auditories.xlsx", header=None).parse(0)
    test = splitter(xl, debug=debug)
    for item in test:
        print(test[item])
