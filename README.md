# DevOps
## Лабораторная Работа № 1
 
### Тема

Работа с системой контроля версии Git

### Цель

Научится создавать и управлять репозиториями, использовать тэги для версионирования, реализовать взаимодействие между фронтенд и бэкенд частями на разных версиях.

### Installation

Для установки проекта требует Python версии 3

```bash
git clone git@github.com:GlebBorisov1/DevOps_lab_1_backend.git
# или
git clone https://github.com/GlebBorisov1/DevOps_lab_1_backend.git

cd DevOps_lab_1_backend/

# Создайте виртуальную среду venv и установите зависимости
python -m venv venv

# активируйте среду
source venv/bin/activate            # или venv\Scripts\activate на Windows
pip install -r requirements.txt

python3 server.py
```