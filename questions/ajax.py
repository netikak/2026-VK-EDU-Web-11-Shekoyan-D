from django.core.exceptions import ValidationError
from django.http import JsonResponse

from .forms import AnswerVoteForm, CorrectAnswerForm, QuestionVoteForm


def submit_action(request, form_class):
    if request.method != 'POST':
        return JsonResponse({'error': 'Используйте метод POST.'}, status=405, headers={'Allow': 'POST'})
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Войдите, чтобы выполнить это действие.'}, status=401)

    form = form_class(request.POST, user=request.user)
    if not form.is_valid():
        return JsonResponse({
            'error': 'Неверные параметры запроса.', 'fields': form.errors.get_json_data(),
        }, status=400)

    try:
        return JsonResponse(form.save())
    except ValidationError as error:
        status = {'not_found': 404, 'forbidden': 403, 'conflict': 409}.get(error.code, 400)
        return JsonResponse({'error': error.messages[0]}, status=status)


def vote_question(request):
    return submit_action(request, QuestionVoteForm)


def vote_answer(request):
    return submit_action(request, AnswerVoteForm)


def correct_answer(request):
    return submit_action(request, CorrectAnswerForm)
