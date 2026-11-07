"""Данные-заглушки ("рыба"). Позже заменятся выборкой из базы данных."""
from datetime import datetime, timedelta

TAGS = ['black-jack', 'bender', 'python', 'django', 'perl', 'MySQL']
RATING_STATES = ['', 'liked', 'disliked']  # ничего / лайк / дизлайк
BASE_TIME = datetime(2026, 11, 1, 10, 30)


def make_questions(count=60):
    questions = []
    for i in range(1, count + 1):
        questions.append({
            'id': i,
            'title': f'How to build a moon park ? #{i}',
            'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut ornare molestie pellentesque.',
            'full_text': (
                'Lorem ipsum — dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh '
                'euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad '
                'minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut '
                'aliquip ex ea commodo consequat.'
            ),
            'rating': (i * 7) % 10,
            'rating_state': RATING_STATES[i % 3],
            'answers_count': (i * 3) % 13,
            'tags': [TAGS[i % len(TAGS)], TAGS[(i + 1) % len(TAGS)]],
            'created_at': BASE_TIME - timedelta(hours=i * 5),
        })
    return questions


def make_answers(question):
    answers = []
    for i in range(1, question['answers_count'] + 1):
        answers.append({
            'id': i,
            'text': (
                'First of all I would like to thank you for the invitation to participate '
                'in such a ... Russia is the huge territory which in many respects needs '
                'to be render habitable.'
            ),
            'rating': (i * 5) % 9,
            'rating_state': RATING_STATES[i % 3],
            'is_correct': i == 1,
            'created_at': question['created_at'] + timedelta(hours=i),
        })
    return answers


QUESTIONS = make_questions()
