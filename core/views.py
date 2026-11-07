from django.shortcuts import render

from .stubs import CURRENT_USER


def login_view(request):
    context = {
        'current_user': None,
        'hide_ask': True,  # на странице входа кнопки ASK! в шапке нет
        # Заглушка ошибки формы: потом её будет формировать форма Django
        'form_error': 'Вы ввели неправильный логин или пароль.',
    }
    return render(request, 'core/login.html', context)


def signup_view(request):
    context = {
        'current_user': None,
        'hide_ask': True,
        'form_error': 'Не удалось зарегистрироваться. Исправьте ошибки в форме.',
        'errors': {
            'email': 'Вы ввели неверный email.',
            'password_repeat': 'Пароли не совпадают.',
        },
        'values': {'login': 'dr_pepper', 'email': 'dr.pepper@', 'nickname': 'Dr. Pepper'},
    }
    return render(request, 'core/signup.html', context)


def profile_view(request):
    context = {
        'current_user': CURRENT_USER,
        'form_error': 'Не удалось сохранить изменения. Исправьте ошибки в форме.',
        'errors': {'nickname': 'Этот ник уже занят.'},
        'values': {'login': 'dr_pepper', 'email': 'drpepper@mail.ru', 'nickname': 'Dr. Pepper'},
    }
    return render(request, 'core/profile.html', context)
