class Csv_not_found(Exception):
    def __init__(self, msg: str = "csv file not faund") -> None:
        super().__init__(msg)


class Less_num(Exception):
    def __init__(self, msg: str = "csv file not faund") -> None:
        super().__init__(msg)
