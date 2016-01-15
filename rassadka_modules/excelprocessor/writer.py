import xlsxwriter as xw
import pandas as pd
import sys
# Излишество
class Writer:
    def __init__(self, stream):
        self.stream = stream

    def __call__(self, dolist, **kwargs):
        self.stream.write(dolist, **kwargs)
        self.stresm.close()
# Конец излишества


class My_excel_stream:
    def write(self, data):
        for item in data:
            if isinstance(item, int):
                name = "table_" + str(item) + ".xlsx"
            else:
                name = item + ".xlsx"
            pdr = pd.ExcelWriter(name)
            pd.DataFrame(data[item]).to_excel(pdr)
            pdr.close()

    def close(self):
        pass


class My_alone_excel_stream:
    def __init__(self, filename):
        self.writer = pd.ExcelWriter(filename)

    def write(self, data):
        for item in data:
            if isinstance(item, int):
                name = "Sheet" + str(item)
            else:
                name = item
            pd.DataFrame(data[item]).to_excel(self.writer, sheet_name=name)

    def close(self):
        self.writer.close()

class My_std_stream:
    def write(self, data):
        print(data)
    def close(self):
        pass


if __name__ == "__main__":
    table1 = pd.read_excel("../exceltestdata/auditories.xlsx", header=None)
    table2 = pd.read_excel("../exceltestdata/people.xlsx", header=None)
    task = {1: table1, "t": table2}
    task2 = {12: table1, "t2": table2}

    test1 = My_excel_stream()
    test2 = My_alone_excel_stream("output.xlsx")

    test1.write(task)
    test2.write(task)

    test1.close()
    test2.close()
