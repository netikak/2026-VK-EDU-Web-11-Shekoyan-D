from django.shortcuts import get_object_or_404, render

from core.utils import paginate
from .models import Question, Tag


def question_list(request, template, questions, **context):
    return render(request, template, {'page': paginate(questions, request), **context})


def index(request):
    return question_list(request, 'questions/index.html', Question.objects.new())


def hot(request):
    return question_list(request, 'questions/hot.html', Question.objects.hot())


def tag_questions(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    return question_list(request, 'questions/tag.html', Question.objects.by_tag(tag), tag_name=tag.name)


def question_detail(request, question_id):
    question = get_object_or_404(Question.objects.for_display(), pk=question_id)
    page = paginate(question.answers.for_display(), request, per_page=5)
    return render(request, 'questions/question.html', {'question': question, 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
