from django.test import TestCase
from django.urls import reverse


class PublicPageTests(TestCase):
    def test_empty_database_and_missing_objects(self):
        for name in ('index', 'hot'):
            self.assertContains(self.client.get(reverse(name)), 'Вопросов пока нет.')
        self.assertEqual(self.client.get(reverse('tag', args=['absent'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('question', args=[999])).status_code, 404)

    def test_real_questions_tags_answers_and_rating(self):
        from django.contrib.auth import get_user_model

        from .models import Answer, Question, QuestionLike, Tag

        user = get_user_model().objects.create_user('author')
        first = Question.objects.create(author=user, title='Старый вопрос', text='Описание')
        second = Question.objects.create(author=user, title='Новый вопрос', text='Описание')
        QuestionLike.objects.create(user=user, question=first, value=1)
        tag = Tag.objects.create(name='python')
        first.tags.add(tag)
        Answer.objects.create(question=first, author=user, text='Настоящий ответ')

        self.assertEqual(list(self.client.get('/').context['page']), [second, first])
        self.assertEqual(list(self.client.get('/hot/').context['page']), [first, second])
        self.assertEqual(list(self.client.get(tag.get_absolute_url()).context['page']), [first])
        self.assertContains(self.client.get(first.get_absolute_url()), 'Настоящий ответ')
        self.assertContains(self.client.get(second.get_absolute_url()), 'Ответов пока нет.')


class FillDatabaseTests(TestCase):
    def test_fill_db_is_additive_and_has_exact_counts(self):
        from io import StringIO

        from django.contrib.auth import get_user_model
        from django.core.management import call_command

        from .models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag

        for _ in range(2):
            call_command('fill_db', 2, stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 4)
        self.assertEqual(Profile.objects.count(), 4)
        self.assertEqual(Tag.objects.count(), 4)
        self.assertEqual(Question.objects.count(), 40)
        self.assertEqual(Answer.objects.count(), 400)
        self.assertEqual(QuestionLike.objects.count() + AnswerLike.objects.count(), 800)
