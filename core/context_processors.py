"""Данные, которые нужны сайдбару на каждой странице.

Контекстный процессор добавляет их в контекст всех шаблонов,
поэтому не нужно передавать их из каждого view.
"""

POPULAR_TAGS = [
    {'name': 'perl', 'css': 'text-dark'},
    {'name': 'python', 'css': 'text-danger fs-5'},
    {'name': 'TechnoPark', 'css': 'text-dark'},
    {'name': 'MySQL', 'css': 'text-danger fs-5'},
    {'name': 'django', 'css': 'text-success fs-5'},
    {'name': 'Mail.Ru', 'css': 'text-dark'},
    {'name': 'Voloshin', 'css': 'text-dark'},
    {'name': 'Firefox', 'css': 'text-warning small'},
]

BEST_MEMBERS = ['Mr. Freeman', 'Dr. House', 'Bender', 'Queen Victoria', 'V. Pupkin']


def sidebar(request):
    return {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS,
    }
