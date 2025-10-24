from django.contrib.auth.models import User
from .models import UserStats, Achievement, UserAchievement, Quiz, UserAnswer


def get_or_create_user_stats(user):
    """Получает или создает статистику пользователя"""
    stats, created = UserStats.objects.get_or_create(user=user)
    return stats


def update_user_stats(user, quiz_completed=False, questions_answered=0, correct_answers=0, quiz_score=0):
    """Обновляет статистику пользователя"""
    stats = get_or_create_user_stats(user)
    
    if quiz_completed:
        stats.total_quizzes_completed += 1
        stats.total_questions_answered += questions_answered
        stats.total_correct_answers += correct_answers
        
        # Начисляем очки за прохождение теста
        points_earned = calculate_quiz_points(quiz_score, questions_answered, correct_answers)
        stats.total_points += points_earned
        
        # Пересчитываем средний балл на основе всех завершенных тестов
        from .models import Quiz
        completed_quizzes = Quiz.objects.filter(user=user, score__isnull=False)
        if completed_quizzes.exists():
            total_score = sum(quiz.score for quiz in completed_quizzes)
            stats.average_score = total_score / completed_quizzes.count()
    
    stats.save()
    check_achievements(user)
    return stats


def calculate_quiz_points(quiz_score, questions_answered, correct_answers):
    """Вычисляет очки за прохождение теста"""
    base_points = 10  # Базовые очки за прохождение теста
    
    # Бонус за точность
    if questions_answered > 0:
        accuracy = (correct_answers / questions_answered) * 100
        if accuracy >= 100:
            accuracy_bonus = 20
        elif accuracy >= 90:
            accuracy_bonus = 15
        elif accuracy >= 80:
            accuracy_bonus = 10
        elif accuracy >= 70:
            accuracy_bonus = 5
        else:
            accuracy_bonus = 0
    else:
        accuracy_bonus = 0
    
    # Бонус за количество вопросов
    questions_bonus = min(questions_answered * 2, 20)  # Максимум 20 очков за количество вопросов
    
    # Бонус за сложность (больше вопросов = больше очков)
    difficulty_bonus = 0
    if questions_answered >= 20:
        difficulty_bonus = 15
    elif questions_answered >= 15:
        difficulty_bonus = 10
    elif questions_answered >= 10:
        difficulty_bonus = 5
    
    total_points = base_points + accuracy_bonus + questions_bonus + difficulty_bonus
    return int(total_points)


def check_achievements(user):
    """Проверяет и разблокирует достижения"""
    stats = get_or_create_user_stats(user)
    achievements = Achievement.objects.all()
    
    for achievement in achievements:
        if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            if check_achievement_condition(user, achievement, stats):
                UserAchievement.objects.create(user=user, achievement=achievement)
                # Очки за достижения начисляются отдельно
                stats.total_points += achievement.points
                stats.save()


def check_achievement_condition(user, achievement, stats):
    """Проверяет условие для разблокировки достижения"""
    condition = achievement.condition
    
    if condition == "first_quiz":
        return stats.total_quizzes_created >= 1
    elif condition == "quiz_creator":
        return stats.total_quizzes_created >= 5
    elif condition == "quiz_master":
        return stats.total_quizzes_created >= 10
    elif condition == "perfectionist":
        return stats.average_score >= 90 and stats.total_quizzes_completed >= 5
    elif condition == "accuracy_king":
        return stats.get_accuracy_percentage() >= 95 and stats.total_quizzes_completed >= 3
    elif condition == "speed_demon":
        return stats.total_quizzes_completed >= 20
    elif condition == "dedicated_learner":
        return stats.total_quizzes_completed >= 50
    elif condition == "scholar":
        return stats.total_questions_answered >= 100
    elif condition == "question_master":
        return stats.total_questions_answered >= 500
    elif condition == "genius":
        return stats.average_score >= 95 and stats.total_quizzes_completed >= 10
    elif condition == "points_collector":
        return stats.total_points >= 500
    elif condition == "points_master":
        return stats.total_points >= 1000
    
    return False


def get_user_rank(user):
    """Получает ранг пользователя"""
    stats = get_or_create_user_stats(user)
    all_stats = UserStats.objects.all().order_by('-total_points')
    
    for i, stat in enumerate(all_stats):
        if stat.user == user:
            return i + 1
    return 0


def get_top_users(limit=10):
    """Получает топ пользователей"""
    return UserStats.objects.all().order_by('-total_points')[:limit]


def sync_user_stats(user):
    """Полная синхронизация статистики пользователя"""
    from .models import Quiz, UserAnswer
    
    stats = get_or_create_user_stats(user)
    
    # Подсчитываем все показатели заново
    created_quizzes = Quiz.objects.filter(user=user).count()
    completed_quizzes = Quiz.objects.filter(user=user, score__isnull=False).count()
    
    user_answers = UserAnswer.objects.filter(user=user)
    total_questions_answered = user_answers.count()
    total_correct_answers = user_answers.filter(is_correct=True).count()
    
    # Вычисляем средний балл
    completed_quiz_scores = Quiz.objects.filter(user=user, score__isnull=False).values_list('score', flat=True)
    average_score = sum(completed_quiz_scores) / len(completed_quiz_scores) if completed_quiz_scores else 0
    
    # Пересчитываем очки на основе всех завершенных тестов
    total_points = 0
    for quiz in Quiz.objects.filter(user=user, score__isnull=False):
        quiz_answers = UserAnswer.objects.filter(user=user, question__quiz=quiz)
        quiz_questions = quiz_answers.count()
        quiz_correct = quiz_answers.filter(is_correct=True).count()
        total_points += calculate_quiz_points(quiz.score, quiz_questions, quiz_correct)
    
    # Обновляем статистику
    stats.total_quizzes_created = created_quizzes
    stats.total_quizzes_completed = completed_quizzes
    stats.total_questions_answered = total_questions_answered
    stats.total_correct_answers = total_correct_answers
    stats.average_score = average_score
    stats.total_points = total_points
    stats.save()
    
    return stats


def force_check_all_achievements(user):
    """Принудительно проверяет все достижения для пользователя"""
    stats = get_or_create_user_stats(user)
    achievements = Achievement.objects.all()
    
    for achievement in achievements:
        if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            if check_achievement_condition(user, achievement, stats):
                UserAchievement.objects.create(user=user, achievement=achievement)
                stats.total_points += achievement.points
                stats.save()
                print(f"Разблокировано достижение: {achievement.name}")


def update_stats_after_quiz_deletion(user):
    """Обновляет статистику после удаления теста"""
    stats = get_or_create_user_stats(user)
    
    # Пересчитываем статистику
    from .models import Quiz, UserAnswer
    created_quizzes = Quiz.objects.filter(user=user).count()
    completed_quizzes = Quiz.objects.filter(user=user, score__isnull=False).count()
    
    user_answers = UserAnswer.objects.filter(user=user)
    total_questions_answered = user_answers.count()
    total_correct_answers = user_answers.filter(is_correct=True).count()
    
    # Вычисляем средний балл
    completed_quiz_scores = Quiz.objects.filter(user=user, score__isnull=False).values_list('score', flat=True)
    average_score = sum(completed_quiz_scores) / len(completed_quiz_scores) if completed_quiz_scores else 0
    
    # Пересчитываем очки
    total_points = 0
    for quiz in Quiz.objects.filter(user=user, score__isnull=False):
        quiz_answers = UserAnswer.objects.filter(user=user, question__quiz=quiz)
        quiz_questions = quiz_answers.count()
        quiz_correct = quiz_answers.filter(is_correct=True).count()
        total_points += calculate_quiz_points(quiz.score, quiz_questions, quiz_correct)
    
    # Обновляем статистику
    stats.total_quizzes_created = created_quizzes
    stats.total_quizzes_completed = completed_quizzes
    stats.total_questions_answered = total_questions_answered
    stats.total_correct_answers = total_correct_answers
    stats.average_score = average_score
    stats.total_points = total_points
    stats.save()
    
    return stats


def create_default_achievements():
    """Создает достижения по умолчанию"""
    achievements_data = [
        {
            'name': 'Первый шаг',
            'description': 'Создайте свой первый тест',
            'icon': '🎯',
            'condition': 'first_quiz',
            'points': 25
        },
        {
            'name': 'Создатель тестов',
            'description': 'Создайте 5 тестов',
            'icon': '📝',
            'condition': 'quiz_creator',
            'points': 50
        },
        {
            'name': 'Мастер тестов',
            'description': 'Создайте 10 тестов',
            'icon': '🏆',
            'condition': 'quiz_master',
            'points': 100
        },
        {
            'name': 'Перфекционист',
            'description': 'Получите средний балл 90%+ на 5+ тестах',
            'icon': '⭐',
            'condition': 'perfectionist',
            'points': 150
        },
        {
            'name': 'Король точности',
            'description': 'Получите точность 95%+ на 3+ тестах',
            'icon': '🎯',
            'condition': 'accuracy_king',
            'points': 200
        },
        {
            'name': 'Скоростной демон',
            'description': 'Завершите 20 тестов',
            'icon': '⚡',
            'condition': 'speed_demon',
            'points': 125
        },
        {
            'name': 'Преданный ученик',
            'description': 'Завершите 50 тестов',
            'icon': '🔥',
            'condition': 'dedicated_learner',
            'points': 300
        },
        {
            'name': 'Ученый',
            'description': 'Ответьте на 100 вопросов',
            'icon': '📚',
            'condition': 'scholar',
            'points': 100
        },
        {
            'name': 'Мастер вопросов',
            'description': 'Ответьте на 500 вопросов',
            'icon': '🧠',
            'condition': 'question_master',
            'points': 250
        },
        {
            'name': 'Гений',
            'description': 'Получите средний балл 95%+ на 10+ тестах',
            'icon': '🌟',
            'condition': 'genius',
            'points': 500
        },
        {
            'name': 'Собиратель очков',
            'description': 'Накопите 500 очков',
            'icon': '💰',
            'condition': 'points_collector',
            'points': 100
        },
        {
            'name': 'Мастер очков',
            'description': 'Накопите 1000 очков',
            'icon': '💎',
            'condition': 'points_master',
            'points': 200
        }
    ]
    
    for data in achievements_data:
        Achievement.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
