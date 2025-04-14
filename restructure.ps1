# Скрипт для реструктуризации проекта
# Перед запуском закройте VS Code и другие редакторы!

# 1. Создаем папки
New-Item -Path "src", "config", "docs", "logs" -ItemType Directory -Force

# 2. Переносим файлы в src/
Move-Item -Path "motion_detector.py", "video_stream_handler.py", "gui_handler.py", "roi_manager.py", "image_saver.py" -Destination "src/" -Force

# 3. Переносим конфиги в config/
Move-Item -Path "config.ini", "config_manager.py" -Destination "config/" -Force

# 4. Обновляем .gitignore
$gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
venv/

# Данные приложения
captured_cars/
logs/
*.log

# Настройки IDE
.vscode/
.idea/
"@

Set-Content -Path ".gitignore" -Value $gitignoreContent -Force

# 5. Создаем requirements.txt (если его нет)
if (-not (Test-Path "requirements.txt")) {
    $requirementsContent = @"
opencv-python==4.9.0.80
numpy==1.26.0
PyQt5==5.15.9
"@
    Set-Content -Path "requirements.txt" -Value $requirementsContent
}

# 6. Удаляем пустые папки (если остались)
Get-ChildItem -Directory | Where-Object { $_.GetFiles().Count -eq 0 } | Remove-Item -Force

Write-Host "Структура успешно обновлена! 🎉"