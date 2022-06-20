from datetime import date


def year(request):
    today = date.today().year
    return {
        'year': today,
    }
