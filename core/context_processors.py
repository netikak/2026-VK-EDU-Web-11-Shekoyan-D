from django.contrib.auth import get_user_model
from django.db.models import Count

from questions.models import Tag


def sidebar(request):
    members = (
        get_user_model().objects.annotate(question_count=Count('questions'))
        .filter(question_count__gt=0)
        .order_by('-question_count', 'username')[:5]
    )
    return {'popular_tags': Tag.objects.popular()[:8], 'best_members': members}
