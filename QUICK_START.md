# ⚡ Быстрый старт - Загрузка на GitHub

## 🚀 За 5 минут на GitHub

### 1. Создайте репозиторий на GitHub
- Идите на https://github.com/new
- Название: `ai-quiz-generator`
- Выберите **Private**
- **НЕ** добавляйте README, .gitignore, лицензию

### 2. Выполните команды в терминале:

```bash
# Перейдите в папку проекта
cd /Users/user/ai_quiz

# Добавьте удаленный репозиторий (замените YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ai-quiz-generator.git

# Переименуйте ветку в main
git branch -M main

# Загрузите на GitHub
git push -u origin main
```

### 3. Готово! 🎉
Ваш проект теперь на GitHub по адресу:
`https://github.com/YOUR_USERNAME/ai-quiz-generator`

---

## 📋 Что включено в проект:

✅ **Полнофункциональное Django приложение**
✅ **AI-генерация тестов с DeepSeek API**
✅ **Загрузка PDF/Word файлов**
✅ **Система очков и достижений**
✅ **Публикация тестов**
✅ **Художественный дизайн**
✅ **Статистика и рейтинги**
✅ **Адаптивный интерфейс**

## 🔧 Для запуска локально:

```bash
# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
cp env_example.txt .env
# Отредактируйте .env и добавьте ваш DEEPSEEK_API_KEY

# Миграции
python manage.py migrate

# Запуск
python manage.py runserver
```

## 📚 Подробная документация:
- `README.md` - полное описание проекта
- `GITHUB_SETUP.md` - детальные инструкции по GitHub
- `PROJECT_STRUCTURE.md` - структура проекта
