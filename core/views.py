from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.csrf import csrf_failure as default_csrf_failure
from django.views.decorators.http import require_http_methods

from .forms import ProfileForm, SignupForm


@require_http_methods(['GET', 'HEAD', 'POST'])
def signup_view(request):
    form = SignupForm(request.POST if request.method == 'POST' else None)
    if form.is_valid():
        login(request, form.save())
        return redirect('index')
    return render(request, 'core/signup.html', {'form': form, 'hide_ask': True})


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
def profile_view(request):
    form = ProfileForm(
        request.user,
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
    )
    if form.is_valid():
        form.save()
        return redirect('profile')
    return render(request, 'core/profile.html', {'form': form})


def csrf_failure(request, reason=''):
    match = request.resolver_match
    if match and match.namespace == 'ajax':
        return JsonResponse({'error': 'Не удалось проверить CSRF-токен. Обновите страницу.'}, status=403)
    return default_csrf_failure(request, reason=reason)
