from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    today = timezone.localtime(timezone.now())
    return {
        'year': today.year,
    }
