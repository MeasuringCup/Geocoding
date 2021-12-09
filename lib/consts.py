import csv


class Consts:
    def get_test_file(data_file):
        test_data = []
        with open(data_file, newline="") as csvfile:
            data = csv.reader(csvfile, delimiter=",")
            next(data)
            for row in data:
                test_data.append(row)
        return [test_data][0]
