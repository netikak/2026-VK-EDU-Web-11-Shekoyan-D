from django.http import Http404
from django.shortcuts import render

from core.stubs import CURRENT_USER
from core.utils import paginate

from . import stubs


def index(request):
    page = paginate(stubs.QUESTIONS, request)
    context = {'page': page, 'current_user': CURRENT_USER}
    return render(request, 'questions/index.html', context)


def hot(request):
    hot_questions = sorted(stubs.QUESTIONS, key=lambda q: (-q['rating'], q['id']))
    page = paginate(hot_questions, request)
    context = {'page': page, 'current_user': CURRENT_USER}
    return render(request, 'questions/hot.html', context)


def tag_questions(request, tag_name):
    tagged = [q for q in stubs.QUESTIONS if tag_name in q['tags']]
    page = paginate(tagged, request)
    context = {'page': page, 'tag_name': tag_name, 'current_user': CURRENT_USER}
    return render(request, 'questions/tag.html', context)


def question_detail(request, question_id):
    question = next((q for q in stubs.QUESTIONS if q['id'] == question_id), None)
    if question is None:
        raise Http404('Вопрос не найден')
    page = paginate(stubs.make_answers(question), request, per_page=5)
    context = {'question': question, 'page': page, 'current_user': None}
    return render(request, 'questions/question.html', context)


def ask(request):
    context = {
        'current_user': None,
        'form_error': 'Не удалось опубликовать вопрос. Исправьте ошибки в форме.',
        'errors': {'tags': 'Можно указать не более 5 тегов.'},
        'values': {'tags': 'moon, park, puzzle, space, rocket, base'},
    }
    return render(request, 'questions/ask.html', context)
