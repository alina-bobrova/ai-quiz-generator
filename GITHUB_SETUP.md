# 🚀 Инструкции по загрузке проекта на GitHub

## Шаг 1: Создание репозитория на GitHub

1. **Войдите в GitHub** и перейдите на https://github.com
2. **Нажмите кнопку "New"** или "+" в правом верхнем углу
3. **Заполните форму создания репозитория:**
   - Repository name: `ai-quiz-generator`
   - Description: `AI-powered quiz generation web application with Django`
   - **Выберите "Private"** для приватного репозитория
   - **НЕ** инициализируйте с README, .gitignore или лицензией (у нас уже есть)
4. **Нажмите "Create repository"**

## Шаг 2: Подключение локального репозитория к GitHub

Выполните следующие команды в терминале:

```bash
# Перейдите в папку проекта
cd /Users/user/ai_quiz

# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ai-quiz-generator.git

# Переименуйте ветку в main (современный стандарт)
git branch -M main

# Загрузите код на GitHub
git push -u origin main
```

## Шаг 3: Проверка загрузки

1. **Обновите страницу** вашего репозитория на GitHub
2. **Убедитесь**, что все файлы загружены
3. **Проверьте**, что README.md отображается корректно

## Шаг 4: Настройка репозитория (опционально)

### Добавление тегов
```bash
git tag -a v1.0.0 -m "First release: AI Quiz Generator"
git push origin v1.0.0
```

### Настройка веток
```bash
# Создание ветки для разработки
git checkout -b develop
git push -u origin develop
```

## Шаг 5: Дополнительные настройки GitHub

### 1. Настройка репозитория
- Перейдите в **Settings** вашего репозитория
- В разделе **General** настройте:
  - Description: "AI-powered quiz generation web application"
  - Website: (если у вас есть деплой)
  - Topics: `django`, `python`, `ai`, `quiz`, `education`, `web-application`

### 2. Настройка защиты веток
- В **Settings** → **Branches**
- Добавьте правило для `main` ветки:
  - Require pull request reviews
  - Require status checks to pass

### 3. Настройка Issues и Projects
- Включите **Issues** для отслеживания багов и предложений
- Создайте **Project** для планирования задач

## Шаг 6: Создание GitHub Actions (опционально)

Создайте файл `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python manage.py test
```

## Шаг 7: Создание релиза

1. **Перейдите в раздел "Releases"** на GitHub
2. **Нажмите "Create a new release"**
3. **Заполните информацию:**
   - Tag version: `v1.0.0`
   - Release title: "AI Quiz Generator v1.0.0"
   - Description: описание функций и изменений
4. **Опубликуйте релиз**

## 🔒 Безопасность

### Важные файлы для защиты:
- `.env` - содержит API ключи (уже в .gitignore)
- `db.sqlite3` - база данных (уже в .gitignore)
- `media/` - загруженные файлы (уже в .gitignore)

### Рекомендации:
1. **Никогда не коммитьте** файлы с секретными ключами
2. **Используйте GitHub Secrets** для CI/CD
3. **Регулярно обновляйте** зависимости
4. **Следите за уязвимостями** в зависимостях

## 📝 Дальнейшая работа

### Ежедневный workflow:
```bash
# Получение изменений
git pull origin main

# Создание новой ветки для функции
git checkout -b feature/new-feature

# Внесение изменений и коммит
git add .
git commit -m "Add new feature"

# Отправка ветки
git push origin feature/new-feature

# Создание Pull Request на GitHub
```

### Полезные команды:
```bash
# Просмотр статуса
git status

# Просмотр истории
git log --oneline

# Отмена последнего коммита
git reset --soft HEAD~1

# Создание ветки
git checkout -b branch-name

# Переключение между ветками
git checkout main
git checkout develop
```

## 🎉 Готово!

Ваш проект теперь на GitHub! Вы можете:
- Поделиться ссылкой с коллегами
- Принимать вклад от других разработчиков
- Отслеживать изменения и баги
- Создавать релизы
- Использовать GitHub Pages для демо

**Ссылка на ваш репозиторий:** `https://github.com/YOUR_USERNAME/ai-quiz-generator`
