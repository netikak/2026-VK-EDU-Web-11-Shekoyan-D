from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone


def related_total(model, relation, aggregate):
    totals = model.objects.filter(**{relation: OuterRef('pk')}).order_by().values(relation)
    totals = totals.annotate(total=aggregate).values('total')
    return Coalesce(Subquery(totals), Value(0))


class QuestionQuerySet(models.QuerySet):
    def with_rating(self):
        return self.annotate(rating=related_total(QuestionLike, 'question', Sum('value')))

    def for_display(self):
        return (
            self.with_rating()
            .annotate(answers_count=related_total(Answer, 'question', Count('pk')))
            .select_related('author__profile')
            .prefetch_related('tags')
        )


class QuestionManager(models.Manager.from_queryset(QuestionQuerySet)):
    def new(self):
        return self.for_display().order_by('-created_at', '-pk')

    def hot(self):
        return self.for_display().order_by('-rating', '-created_at', '-pk')

    def by_tag(self, tag):
        return self.new().filter(tags=tag)


class AnswerQuerySet(models.QuerySet):
    def with_rating(self):
        return self.annotate(rating=related_total(AnswerLike, 'answer', Sum('value')))

    def for_display(self):
        return self.with_rating().select_related('author__profile')


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile',
        verbose_name='Пользователь',
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='Аватар')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


class TagManager(models.Manager):
    def popular(self):
        return self.annotate(uses=Count('questions')).filter(uses__gt=0).order_by('-uses', 'name')


class Tag(models.Model):
    name = models.CharField(
        max_length=50, unique=True, verbose_name='Название',
        validators=[RegexValidator(
            r'^(?!\.{1,2}\Z)[\w.+#-]+\Z',
            'В теге допустимы буквы, цифры и символы «_», «-», «.», «+», «#».',
        )],
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    objects = TagManager()

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', args=[self.name])


class Question(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст вопроса')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(Tag, related_name='questions', blank=True, verbose_name='Теги')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    objects = QuestionManager()

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['-created_at', '-pk']
        indexes = [models.Index(fields=['-created_at', '-id'], name='question_new_idx')]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('question', args=[self.pk])


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='answers',
        verbose_name='Автор',
    )
    text = models.TextField(verbose_name='Текст ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    objects = AnswerQuerySet.as_manager()

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ['created_at', 'pk']
        indexes = [models.Index(fields=['question', 'created_at', 'id'], name='answer_page_idx')]
        constraints = [
            models.UniqueConstraint(
                fields=['question'], condition=models.Q(is_correct=True),
                name='one_correct_answer_per_question',
            ),
        ]

    def __str__(self):
        return f'Ответ №{self.pk}'


class Vote(models.Model):
    class Value(models.IntegerChoices):
        LIKE = 1, 'Лайк'
        DISLIKE = -1, 'Дизлайк'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь',
    )
    value = models.SmallIntegerField(choices=Value.choices, verbose_name='Оценка')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.get_value_display()} №{self.pk}'


class QuestionLike(Vote):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='question_likes', verbose_name='Вопрос',
    )

    class Meta:
        verbose_name = 'Оценка вопроса'
        verbose_name_plural = 'Оценки вопросов'
        unique_together = ('user', 'question')
        constraints = [
            models.CheckConstraint(check=models.Q(value__in=[-1, 1]), name='question_vote_value'),
        ]


class AnswerLike(Vote):
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, related_name='answer_likes', verbose_name='Ответ',
    )

    class Meta:
        verbose_name = 'Оценка ответа'
        verbose_name_plural = 'Оценки ответов'
        unique_together = ('user', 'answer')
        constraints = [
            models.CheckConstraint(check=models.Q(value__in=[-1, 1]), name='answer_vote_value'),
        ]
