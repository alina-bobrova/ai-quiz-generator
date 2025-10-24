import json
import requests
import string
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import Quiz, Question, Answer, UserAnswer, UserStats, Achievement, UserAchievement
from .file_utils import process_uploaded_file, clean_text_for_ai
from .forms import UserProfileForm, CustomPasswordChangeForm
from .stats_utils import get_or_create_user_stats, update_user_stats, get_user_rank, get_top_users, create_default_achievements, sync_user_stats, force_check_all_achievements, update_stats_after_quiz_deletion, check_achievements


def generate_share_code():
    """Генерирует уникальный код для публикации теста"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def index(request):
    """Главная страница с формой создания теста"""
    return render(request, 'index.html')


def quiz_detail(request, quiz_id):
    """Страница прохождения теста"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    
    if request.method == 'POST':
        # Обработка ответов пользователя
        user = request.user if request.user.is_authenticated else None
        correct_answers = 0
        total_questions = questions.count()
        session_answers = {}
        
        for question in questions:
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                try:
                    selected_answer = Answer.objects.get(id=answer_id)
                    is_correct = selected_answer.is_correct
                    
                    if is_correct:
                        correct_answers += 1
                    
                    # Сохраняем ответ пользователя, если он авторизован
                    if user:
                        UserAnswer.objects.update_or_create(
                            user=user,
                            question=question,
                            defaults={
                                'answer': selected_answer,
                                'is_correct': is_correct
                            }
                        )
                    else:
                        # Сохраняем в сессии для неавторизованных пользователей
                        session_answers[str(question.id)] = answer_id
                        
                except Answer.DoesNotExist:
                    pass
        
        # Сохраняем ответы в сессии для неавторизованных пользователей
        if not user and session_answers:
            request.session[f'quiz_{quiz.id}_answers'] = session_answers
        
        # Вычисляем процент правильных ответов
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Обновляем результат теста
        quiz.score = score
        quiz.save()
        
        # Обновляем статистику пользователя
        if request.user.is_authenticated:
            update_user_stats(
                request.user, 
                quiz_completed=True, 
                questions_answered=total_questions, 
                correct_answers=correct_answers,
                quiz_score=score
            )
        
        return redirect('quiz_results', quiz_id=quiz.id)
    
    return render(request, 'quiz.html', {'quiz': quiz, 'questions': questions})


def quiz_results(request, quiz_id):
    """Страница результатов теста"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    
    # Получаем ответы пользователя, если он авторизован
    user_answers = {}
    if request.user.is_authenticated:
        user_answers = {
            ua.question.id: ua for ua in UserAnswer.objects.filter(
                user=request.user, 
                question__in=questions
            )
        }
    else:
        # Если пользователь не авторизован, попробуем получить ответы из сессии
        session_answers = request.session.get(f'quiz_{quiz_id}_answers', {})
        if session_answers:
            # Создаем mock объекты для отображения
            for question_id, answer_id in session_answers.items():
                try:
                    answer = Answer.objects.get(id=answer_id)
                    user_answers[int(question_id)] = type('MockUserAnswer', (), {
                        'answer': answer,
                        'is_correct': answer.is_correct
                    })()
                except Answer.DoesNotExist:
                    pass
    
    return render(request, 'results.html', {
        'quiz': quiz, 
        'questions': questions,
        'user_answers': user_answers
    })


@login_required
def my_quizzes(request):
    """Список созданных пользователем тестов"""
    quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_quizzes.html', {'quizzes': quizzes})


@csrf_exempt
@require_http_methods(["POST"])
def generate_quiz(request):
    """API эндпоинт для генерации теста через DeepSeek"""
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '').strip()
        question_count = data.get('questionCount', 5)
        
        if not topic:
            return JsonResponse({'error': 'Тема теста не может быть пустой'}, status=400)
        
        # Валидация количества вопросов
        if not isinstance(question_count, int) or question_count < 1 or question_count > 50:
            return JsonResponse({'error': 'Количество вопросов должно быть от 1 до 50'}, status=400)
        
        # Настройка DeepSeek API
        deepseek_api_key = settings.DEEPSEEK_API_KEY
        
        if not deepseek_api_key:
            return JsonResponse({'error': 'DeepSeek API ключ не настроен'}, status=500)
        
        # Промпт для генерации теста
        prompt = f'''Создай JSON с викториной по теме "{topic}". 

ВАЖНО: Верни ТОЛЬКО валидный JSON без дополнительного текста, комментариев или markdown разметки.

Формат:
{{
"title": "Название теста",
"questions": [
{{
"question": "Текст вопроса",
"answers": [
{{"text": "Вариант ответа 1", "is_correct": true}},
{{"text": "Вариант ответа 2", "is_correct": false}},
{{"text": "Вариант ответа 3", "is_correct": false}},
{{"text": "Вариант ответа 4", "is_correct": false}}
]
}}
]
}}

Создай ровно {question_count} вопросов с 4 вариантами ответов каждый. Только один ответ должен быть правильным на каждый вопрос.'''
        
        # Вызов DeepSeek API
        headers = {
            'Authorization': f'Bearer {deepseek_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты эксперт по созданию образовательных тестов. Создавай качественные вопросы с четкими вариантами ответов."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': f'Ошибка API DeepSeek: {response.status_code}'}, status=500)
        
        response_data = response.json()
        quiz_content = response_data['choices'][0]['message']['content']
        
        # Очистка ответа от возможных markdown блоков
        if '```json' in quiz_content:
            quiz_content = quiz_content.split('```json')[1].split('```')[0].strip()
        elif '```' in quiz_content:
            quiz_content = quiz_content.split('```')[1].split('```')[0].strip()
        
        # Парсинг JSON ответа
        try:
            quiz_data = json.loads(quiz_content)
        except json.JSONDecodeError as e:
            # Если JSON невалидный, попробуем извлечь JSON из текста
            import re
            json_match = re.search(r'\{.*\}', quiz_content, re.DOTALL)
            if json_match:
                quiz_data = json.loads(json_match.group())
            else:
                return JsonResponse({'error': f'Не удалось распарсить JSON от DeepSeek: {str(e)}'}, status=500)
        
        # Создание теста в базе данных
        user = request.user if request.user.is_authenticated else None
        quiz = Quiz.objects.create(
            title=quiz_data['title'],
            user=user
        )
        
        # Создание вопросов и ответов
        for question_data in quiz_data['questions']:
            question = Question.objects.create(
                quiz=quiz,
                text=question_data['question']
            )
            
            for answer_data in question_data['answers']:
                Answer.objects.create(
                    question=question,
                    text=answer_data['text'],
                    is_correct=answer_data['is_correct']
                )
        
        # Обновляем статистику пользователя при создании теста
        if user:
            stats = get_or_create_user_stats(user)
            stats.total_quizzes_created += 1
            stats.save()
            check_achievements(user)
        
        return JsonResponse({
            'success': True,
            'quiz_id': quiz.id,
            'redirect_url': f'/quiz/{quiz.id}/'
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Неверный формат JSON в запросе: {str(e)}'}, status=400)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Ошибка сети при обращении к DeepSeek API: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при генерации теста: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_quiz_from_file(request):
    """API эндпоинт для генерации теста из загруженного файла"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Файл не был загружен'}, status=400)
        
        uploaded_file = request.FILES['file']
        question_count = int(request.POST.get('questionCount', 5))
        
        # Валидация количества вопросов
        if question_count < 1 or question_count > 50:
            return JsonResponse({'error': 'Количество вопросов должно быть от 1 до 50'}, status=400)
        
        # Настройка DeepSeek API
        deepseek_api_key = settings.DEEPSEEK_API_KEY
        
        if not deepseek_api_key:
            return JsonResponse({'error': 'DeepSeek API ключ не настроен'}, status=500)
        
        # Обрабатываем загруженный файл
        try:
            file_text = process_uploaded_file(uploaded_file)
            cleaned_text = clean_text_for_ai(file_text)
        except Exception as e:
            return JsonResponse({'error': f'Ошибка при обработке файла: {str(e)}'}, status=400)
        
        if not cleaned_text or len(cleaned_text.strip()) < 100:
            return JsonResponse({'error': 'Файл содержит слишком мало текста для создания теста'}, status=400)
        
        # Промпт для генерации теста на основе файла
        prompt = f'''Проанализируй следующий текст и создай JSON с викториной на его основе.

ТЕКСТ ДЛЯ АНАЛИЗА:
{cleaned_text}

ВАЖНО: Верни ТОЛЬКО валидный JSON без дополнительного текста, комментариев или markdown разметки.

Формат:
{{
"title": "Название теста на основе текста",
"questions": [
{{
"question": "Текст вопроса",
"answers": [
{{"text": "Вариант ответа 1", "is_correct": true}},
{{"text": "Вариант ответа 2", "is_correct": false}},
{{"text": "Вариант ответа 3", "is_correct": false}},
{{"text": "Вариант ответа 4", "is_correct": false}}
]
}}
]
}}

Создай ровно {question_count} вопросов с 4 вариантами ответов каждый на основе предоставленного текста. Только один ответ должен быть правильным на каждый вопрос.'''
        
        # Вызов DeepSeek API
        headers = {
            'Authorization': f'Bearer {deepseek_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты эксперт по созданию образовательных тестов. Анализируй предоставленный текст и создавай качественные вопросы с четкими вариантами ответов на основе содержания."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': f'Ошибка API DeepSeek: {response.status_code}'}, status=500)
        
        response_data = response.json()
        quiz_content = response_data['choices'][0]['message']['content']
        
        # Очистка ответа от возможных markdown блоков
        if '```json' in quiz_content:
            quiz_content = quiz_content.split('```json')[1].split('```')[0].strip()
        elif '```' in quiz_content:
            quiz_content = quiz_content.split('```')[1].split('```')[0].strip()
        
        # Парсинг JSON ответа
        try:
            quiz_data = json.loads(quiz_content)
        except json.JSONDecodeError as e:
            # Если JSON невалидный, попробуем извлечь JSON из текста
            import re
            json_match = re.search(r'\{.*\}', quiz_content, re.DOTALL)
            if json_match:
                quiz_data = json.loads(json_match.group())
            else:
                return JsonResponse({'error': f'Не удалось распарсить JSON от DeepSeek: {str(e)}'}, status=500)
        
        # Создание теста в базе данных
        user = request.user if request.user.is_authenticated else None
        quiz = Quiz.objects.create(
            title=quiz_data['title'],
            user=user
        )
        
        # Создание вопросов и ответов
        for question_data in quiz_data['questions']:
            question = Question.objects.create(
                quiz=quiz,
                text=question_data['question']
            )
            
            for answer_data in question_data['answers']:
                Answer.objects.create(
                    question=question,
                    text=answer_data['text'],
                    is_correct=answer_data['is_correct']
                )
        
        # Обновляем статистику пользователя при создании теста
        if user:
            stats = get_or_create_user_stats(user)
            stats.total_quizzes_created += 1
            stats.save()
            check_achievements(user)
        
        return JsonResponse({
            'success': True,
            'quiz_id': quiz.id,
            'redirect_url': f'/quiz/{quiz.id}/'
        })
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Ошибка сети при обращении к DeepSeek API: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при генерации теста: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def toggle_quiz_public(request, quiz_id):
    """Переключает публичность теста"""
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Проверяем права доступа
        if request.user != quiz.user:
            return JsonResponse({'error': 'Нет прав для изменения этого теста'}, status=403)
        
        if quiz.is_public:
            # Делаем приватным
            quiz.is_public = False
            quiz.share_code = None
        else:
            # Делаем публичным
            quiz.is_public = True
            if not quiz.share_code:
                quiz.share_code = generate_share_code()
        
        quiz.save()
        
        return JsonResponse({
            'success': True,
            'is_public': quiz.is_public,
            'share_code': quiz.share_code,
            'share_url': f'/quiz/shared/{quiz.share_code}/' if quiz.is_public else None
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при изменении публичности: {str(e)}'}, status=500)


def shared_quiz(request, share_code):
    """Показывает публичный тест по коду"""
    try:
        quiz = get_object_or_404(Quiz, share_code=share_code, is_public=True)
        questions = quiz.questions.all()
        
        context = {
            'quiz': quiz,
            'questions': questions,
            'is_shared': True
        }
        
        return render(request, 'quiz.html', context)
        
    except Exception as e:
        messages.error(request, f'Ошибка при загрузке теста: {str(e)}')
        return redirect('index')


@login_required
@require_http_methods(["POST"])
def delete_quiz(request, quiz_id):
    """Удаление теста"""
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Проверяем права доступа
        if request.user != quiz.user:
            return JsonResponse({'error': 'Нет прав для удаления этого теста'}, status=403)
        
        # Удаляем тест (каскадное удаление удалит все связанные объекты)
        quiz.delete()
        
        # Обновляем статистику пользователя после удаления
        update_stats_after_quiz_deletion(request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Тест успешно удален'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при удалении теста: {str(e)}'}, status=500)


@login_required
def profile_view(request):
    """Страница профиля пользователя"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Синхронизируем статистику пользователя
    stats = sync_user_stats(request.user)
    
    # Принудительно проверяем все достижения
    force_check_all_achievements(request.user)
    
    user_achievements = UserAchievement.objects.filter(user=request.user).order_by('-unlocked_at')
    user_rank = get_user_rank(request.user)
    top_users = get_top_users(5)
    
    context = {
        'form': form,
        'stats': stats,
        'user_achievements': user_achievements,
        'user_rank': user_rank,
        'top_users': top_users,
        'user_quizzes_count': stats.total_quizzes_created,
        'completed_quizzes': stats.total_quizzes_completed,
    }
    
    return render(request, 'profile.html', context)


@login_required
def change_password_view(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'change_password.html', {'form': form})


def register_view(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('index')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Вход выполнен успешно!')
            return redirect('index')
        else:
            messages.error(request, 'Неверные учетные данные.')
    
    return render(request, 'registration/login.html')


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('index')