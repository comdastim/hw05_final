import datetime


def year(request):
    today_date = datetime.date.today()
    return {'year': today_date.year}
