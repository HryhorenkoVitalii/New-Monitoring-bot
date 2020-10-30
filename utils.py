from datetime import datetime


def str_to_date_converter(date_created):
    if date_created == 'now':
        data = datetime.now()
    else:
        if len(date_created) <= 10:
            data = datetime.strptime(date_created, "%Y-%m-%d")
        else:
            data = datetime.strptime(date_created, "%Y-%m-%d %H:%M:%S")
    return data