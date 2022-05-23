import datetime as dt


def year(request):
    return {
        'year': int(dt.datetime.now().year)
    }
