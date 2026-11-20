from datetime import timedelta
from random import Random
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from questions.models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag


BATCH_SIZE = 2_000
QUESTIONS_PER_BATCH = 500


class Command(BaseCommand):
    help = 'Добавляет тестовых пользователей, теги, вопросы, ответы и оценки.'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    @transaction.atomic
    def handle(self, *args, ratio, **options):
        if ratio < 2:
            raise CommandError('Укажите ratio ≥ 2. При одном пользователе 110 объектов допускают только 110 уникальных оценок.')

        run = uuid4().hex
        fake = Faker('ru_RU')
        rng = Random()
        now = timezone.now()

        User = get_user_model()
        user_ids = []
        tag_ids = []
        for start in range(0, ratio, BATCH_SIZE):
            indices = range(start, min(ratio, start + BATCH_SIZE))
            users = User.objects.bulk_create([
                User(
                    username=f'{fake.user_name()[:40]}_{run}_{i}',
                    first_name=fake.first_name(),
                    email=f'fake-{run}-{i}@example.com',
                    password=make_password(None),
                )
                for i in indices
            ], batch_size=BATCH_SIZE)
            Profile.objects.bulk_create([Profile(user_id=user.pk) for user in users], batch_size=BATCH_SIZE)
            user_ids.extend(user.pk for user in users)
            tags = Tag.objects.bulk_create([
                Tag(name=f'{fake.word()[:12]}-{run[:24]}-{i}') for i in indices
            ], batch_size=BATCH_SIZE)
            tag_ids.extend(tag.pk for tag in tags)

        # Небольшой пул текстов держит время генерации Faker ограниченным.
        titles = [fake.sentence(nb_words=6) for _ in range(1_000)]
        texts = [fake.paragraph(nb_sentences=4) for _ in range(2_000)]
        question_votes = min(ratio, 5)
        answer_votes, extra_votes = divmod(200 - 10 * question_votes, 100)
        through = Question.tags.through

        for start in range(0, ratio * 10, QUESTIONS_PER_BATCH):
            questions = Question.objects.bulk_create([
                Question(
                    title=rng.choice(titles), text=rng.choice(texts),
                    author_id=rng.choice(user_ids), created_at=now - timedelta(minutes=i),
                )
                for i in range(start, min(ratio * 10, start + QUESTIONS_PER_BATCH))
            ], batch_size=BATCH_SIZE)
            through.objects.bulk_create([
                through(question_id=question.pk, tag_id=tag_id)
                for question in questions
                for tag_id in rng.sample(tag_ids, min(3, ratio))
            ], batch_size=BATCH_SIZE)
            QuestionLike.objects.bulk_create([
                QuestionLike(question_id=question.pk, user_id=user_id, value=rng.choice((1, 1, -1)))
                for question in questions
                for user_id in rng.sample(user_ids, question_votes)
            ], batch_size=BATCH_SIZE)

            answers = Answer.objects.bulk_create([
                Answer(
                    question_id=question.pk, text=rng.choice(texts),
                    author_id=rng.choice(user_ids),
                    created_at=question.created_at + timedelta(seconds=position + 1),
                )
                for question in questions for position in range(10)
            ], batch_size=BATCH_SIZE)
            AnswerLike.objects.bulk_create([
                AnswerLike(answer_id=answer.pk, user_id=user_id, value=rng.choice((1, 1, -1)))
                for i, answer in enumerate(answers, start=start * 10)
                for user_id in rng.sample(user_ids, answer_votes + (i % 100 < extra_votes))
            ], batch_size=BATCH_SIZE)

        self.stdout.write(self.style.SUCCESS(
            f'Добавлено: {ratio} пользователей, {ratio * 10} вопросов, {ratio * 100} ответов, '
            f'{ratio} тегов и {ratio * 200} оценок.'
        ))
