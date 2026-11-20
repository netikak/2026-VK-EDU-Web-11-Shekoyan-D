from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.utils import paginate
from .forms import AnswerForm, QuestionForm
from .models import ANSWERS_PER_PAGE, Question, Tag


def question_list(request, template, questions, **context):
    return render(request, template, {'page': paginate(questions, request), **context})


def index(request):
    return question_list(request, 'questions/index.html', Question.objects.new(request.user))


def hot(request):
    return question_list(request, 'questions/hot.html', Question.objects.hot(request.user))


def tag_questions(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    questions = Question.objects.by_tag(tag, request.user)
    return question_list(request, 'questions/tag.html', questions, tag_name=tag.name)


def render_question(request, question, form):
    page = paginate(question.answers.for_display(request.user), request, per_page=ANSWERS_PER_PAGE)
    return render(request, 'questions/question.html', {'question': question, 'page': page, 'form': form})


@login_required
def add_answer(request, question):
    form = AnswerForm(request.POST)
    if form.is_valid():
        return redirect(form.save(question=question, author=request.user))
    return render_question(request, question, form)


@require_http_methods(['GET', 'HEAD', 'POST'])
def question_detail(request, question_id):
    question = get_object_or_404(Question.objects.for_display(request.user), pk=question_id)
    if request.method == 'POST':
        return add_answer(request, question)
    return render_question(request, question, AnswerForm())


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
def ask(request):
    form = QuestionForm(request.POST if request.method == 'POST' else None)
    if form.is_valid():
        return redirect(form.save(author=request.user))
    return render(request, 'questions/ask.html', {'form': form})
