from django.urls import include, path

from . import ajax, views


ajax_patterns = [
    path('questions/vote/', ajax.vote_question, name='vote_question'),
    path('answers/vote/', ajax.vote_answer, name='vote_answer'),
    path('answers/correct/', ajax.correct_answer, name='correct_answer'),
]

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag_questions, name='tag'),
    path('question/<int:question_id>/', views.question_detail, name='question'),
    path('ask/', views.ask, name='ask'),
    path('ajax/', include((ajax_patterns, 'ajax'))),
]
