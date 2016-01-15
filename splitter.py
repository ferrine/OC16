import argparse
import sys

import pandas as pd

from rassadka_modules.excelprocessor import reader, writer


def init_stream(aStream, addition):
    if aStream == "std":
        if addition:
            print("Unsupported usage, see -help for more info\n(stream not changed, std by default)")
            sys.exit(1)
        return writer.My_std_stream()
    elif addition:
        if not addition.endswith(".xlsx"):
            print("{0} should have .xlsx extension".format(addition))
            sys.exit(1)
        return writer.My_alone_excel_stream(addition)
    else:
        return writer.My_excel_stream()


if __name__ == '__main__':
    description = "\
            This program allows you to parse excel documents and split multiple sequences to different tables or sheets. \
            It is also possible to name them depending on the mark of the table. You can choose stream in {std, \
            excel}. If you want single file output it is possible to stream output into it. \
            See more information below."

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", nargs='*', help="name of the file that you want to split should have .xlsx extension")
    parser.add_argument("-d", "--debug", action='store_true', default=False, help="this flag allows to make a log file")
    parser.add_argument("-n", "--named", action='store_true', default=False,
                        help="name every table, or excel sheet with a mark as top left side cell")
    parser.add_argument("-s", "--stream", default="std", choices=["std", "excel"],
                        help="where to store the results, std by default")
    parser.add_argument("-f", "--file", help="if you want to store all results in one excel book? name it")
    opts = vars(parser.parse_args(sys.argv[1:]))
    if (not opts["input"]) or (not opts["input"][0].endswith(".xlsx")):
        print("INPUT name of the file that you want to split should have .xlsx extension")
        parser.print_usage()
        sys.exit(1)
    # Init stream
    stream = init_stream(opts["stream"], opts["file"])
    table = pd.read_excel(opts["input"][0], header=None)
    result_dict = reader.splitter(table, named=opts["named"], debug=opts["debug"])
    stream.write(result_dict)
    stream.close()
