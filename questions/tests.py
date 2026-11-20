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


class WriteFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model

        from .models import Question

        cls.author = get_user_model().objects.create_user('asker')
        cls.reader = get_user_model().objects.create_user('reader')
        cls.question = Question.objects.create(author=cls.author, title='Вопрос', text='Описание')



class WritePageTests(WriteFixture):
    def test_guest_controls_and_protected_posts(self):
        detail = self.question.get_absolute_url()
        self.assertContains(self.client.get(detail), 'Войдите, чтобы ответить')
        self.assertRedirects(self.client.get('/ask/'), '/login/?next=/ask/')
        self.assertRedirects(self.client.post(detail, {'text': 'Текст'}), f'/login/?next={detail}')

    def test_ask_validation_and_tag_reuse(self):
        from .models import Question, Tag

        self.client.force_login(self.author)
        existing = Tag.objects.create(name='python')
        data = {'title': 'Мой вопрос', 'text': 'Моё описание', 'tags': 'Python, django, python'}
        invalid = self.client.post('/ask/', {**data, 'tags': '1, 2, 3, 4, 5, 6'})
        self.assertTrue(invalid.context['form'].errors['tags'])
        self.assertContains(invalid, data['title'])
        response = self.client.post('/ask/', data)
        question = Question.objects.get(title=data['title'])
        self.assertRedirects(response, question.get_absolute_url())
        self.assertEqual(question.tags.get(name='python'), existing)
        self.assertEqual(set(question.tags.values_list('name', flat=True)), {'python', 'django'})

    def test_answer_redirects_to_its_page_and_anchor(self):
        from .models import Answer

        Answer.objects.bulk_create([
            Answer(question=self.question, author=self.author, text=str(i))
            for i in range(5)
        ])
        self.client.force_login(self.reader)
        detail = self.question.get_absolute_url()
        invalid = self.client.post(detail, {'text': '   '})
        self.assertTrue(invalid.context['form'].errors['text'])
        response = self.client.post(detail, {'text': 'Шестой ответ'})
        answer = Answer.objects.get(text='Шестой ответ')
        self.assertRedirects(response, f'{detail}?page=2#answer-{answer.pk}')
        self.assertContains(self.client.get(f'{detail}?page=2'), f'id="answer-{answer.pk}"')


class AjaxTests(WriteFixture):
    def setUp(self):
        from .models import Answer

        self.answer = Answer.objects.create(question=self.question, author=self.reader, text='Ответ')
        self.other = Answer.objects.create(question=self.question, author=self.reader, text='Другой ответ')

    def test_auth_method_and_csrf_errors_are_json(self):
        from django.test import Client

        url = reverse('ajax:vote_question')
        data = {'target_id': self.question.pk, 'value': 1}
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, data).status_code, 401)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.reader)
        failure = protected.post(url, data)
        self.assertEqual(failure.status_code, 403)
        self.assertIn('CSRF', failure.json()['error'])
        protected.get('/')
        success = protected.post(url, data, HTTP_X_CSRFTOKEN=protected.cookies['csrftoken'].value)
        self.assertEqual(success.json()['rating'], 1)

    def test_votes_reject_duplicates_and_allow_switching(self):
        self.client.force_login(self.reader)
        for name, target in [('vote_question', self.question), ('vote_answer', self.answer)]:
            url = reverse(f'ajax:{name}')
            self.assertEqual(self.client.post(url, {'target_id': target.pk, 'value': 'oops'}).status_code, 400)
            self.assertEqual(self.client.post(url, {'target_id': 999999, 'value': 1}).status_code, 404)
            self.assertEqual(self.client.post(url, {'target_id': target.pk, 'value': 1}).json()['rating'], 1)
            self.assertEqual(self.client.post(url, {'target_id': target.pk, 'value': 1}).status_code, 409)
            self.assertEqual(self.client.post(url, {'target_id': target.pk, 'value': -1}).json()['rating'], -1)

    def test_only_question_author_can_mark_one_of_its_answers(self):
        from .models import Question

        url = reverse('ajax:correct_answer')
        data = {'question_id': self.question.pk, 'answer_id': self.answer.pk, 'is_correct': 'true'}
        self.client.force_login(self.reader)
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.client.force_login(self.author)
        another_question = Question.objects.create(author=self.author, title='Другой', text='Описание')
        self.assertEqual(self.client.post(url, {**data, 'question_id': another_question.pk}).status_code, 404)
        self.assertEqual(self.client.post(url, data).json()['correct_answer_id'], self.answer.pk)
        self.assertEqual(
            self.client.post(url, {**data, 'answer_id': self.other.pk}).json()['correct_answer_id'],
            self.other.pk,
        )
        self.answer.refresh_from_db()
        self.assertFalse(self.answer.is_correct)
        self.assertIsNone(self.client.post(url, {
            **data, 'answer_id': self.other.pk, 'is_correct': 'false',
        }).json()['correct_answer_id'])
