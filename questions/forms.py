from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Answer, AnswerLike, Question, QuestionLike, Tag, Vote


MAX_ID = 2**63 - 1
TEXT_ATTRS = {'class': 'form-control field'}


class QuestionForm(forms.ModelForm):
    title = forms.CharField(label='Заголовок', max_length=100, widget=forms.TextInput(attrs=TEXT_ATTRS))
    text = forms.CharField(label='Текст вопроса', max_length=2000, widget=forms.Textarea(
        attrs={**TEXT_ATTRS, 'rows': 10},
    ))
    tags = forms.CharField(
        label='Теги', required=False, max_length=300, widget=forms.TextInput(attrs=TEXT_ATTRS),
        help_text='Через запятую, до 5 тегов, каждый длиной до 50 символов.',
    )

    class Meta:
        model = Question
        fields = ('title', 'text')

    def clean_tags(self):
        tags = list(dict.fromkeys(
            tag.strip().lower() for tag in self.cleaned_data['tags'].split(',') if tag.strip()
        ))
        if len(tags) > 5:
            raise ValidationError('Можно указать не более 5 тегов.')
        field = Tag._meta.get_field('name')
        return [field.clean(tag, None) for tag in tags]

    @transaction.atomic
    def save(self, *, author):
        question = super().save(commit=False)
        question.author = author
        question.save()
        tags = [Tag.objects.get_or_create(name=name)[0] for name in sorted(self.cleaned_data['tags'])]
        question.tags.set(tags)
        return question


class AnswerForm(forms.ModelForm):
    text = forms.CharField(
        label='Ваш ответ', max_length=2000, help_text='Максимум 2000 символов.',
        widget=forms.Textarea(attrs={**TEXT_ATTRS, 'rows': 4, 'placeholder': 'Напишите ответ'}),
    )

    class Meta:
        model = Answer
        fields = ('text',)

    def save(self, *, question, author):
        answer = super().save(commit=False)
        answer.question = question
        answer.author = author
        answer.save()
        return answer


class VoteForm(forms.Form):
    target_id = forms.IntegerField(min_value=1, max_value=MAX_ID)
    value = forms.TypedChoiceField(choices=Vote.Value.choices, coerce=int)

    def __init__(self, data, *, user):
        super().__init__(data)
        self.user = user

    @transaction.atomic
    def save(self):
        target_id = self.cleaned_data['target_id']
        target = self.target_model.objects.select_for_update(no_key=True).filter(pk=target_id).first()
        if target is None:
            raise ValidationError('Объект для оценки не найден.', code='not_found')

        value = self.cleaned_data['value']
        vote, created = self.vote_model.objects.get_or_create(
            **{self.target_field: target}, user=self.user, defaults={'value': value},
        )
        if not created:
            if vote.value == value:
                raise ValidationError('Такая оценка уже поставлена.', code='conflict')
            vote.value = value
            vote.save(update_fields=['value'])

        rating = self.target_model.objects.with_rating().get(pk=target_id).rating
        return {'rating': rating, 'vote': value}


class QuestionVoteForm(VoteForm):
    target_model = Question
    vote_model = QuestionLike
    target_field = 'question'


class AnswerVoteForm(VoteForm):
    target_model = Answer
    vote_model = AnswerLike
    target_field = 'answer'


class CorrectAnswerForm(forms.Form):
    question_id = forms.IntegerField(min_value=1, max_value=MAX_ID)
    answer_id = forms.IntegerField(min_value=1, max_value=MAX_ID)
    is_correct = forms.TypedChoiceField(
        choices=[('true', 'Отметить'), ('false', 'Снять отметку')],
        coerce=lambda value: value == 'true',
    )

    def __init__(self, data, *, user):
        super().__init__(data)
        self.user = user

    @transaction.atomic
    def save(self):
        question = Question.objects.select_for_update(no_key=True).filter(
            pk=self.cleaned_data['question_id'],
        ).first()
        if question is None:
            raise ValidationError('Вопрос не найден.', code='not_found')
        if question.author_id != self.user.pk:
            raise ValidationError('Только автор вопроса может выбрать правильный ответ.', code='forbidden')

        answers = question.answers.all()
        answer = answers.select_for_update(no_key=True).filter(pk=self.cleaned_data['answer_id']).first()
        if answer is None:
            raise ValidationError('Ответ к этому вопросу не найден.', code='not_found')
        if self.cleaned_data['is_correct']:
            answers.filter(is_correct=True).exclude(pk=answer.pk).update(is_correct=False)
            answers.filter(pk=answer.pk).update(is_correct=True)
            return {'correct_answer_id': answer.pk}

        answers.filter(pk=answer.pk, is_correct=True).update(is_correct=False)
        correct_id = answers.filter(is_correct=True).values_list('pk', flat=True).first()
        return {'correct_answer_id': correct_id}
