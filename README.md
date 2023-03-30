# foodgram_project

foodgram_project

![foodgram_project](https://github.com/sugatosansiro/foodgram-project-react/actions/workflows/main.yml/badge.svg)

## Описание

Данный проект представляет собой социальную сеть по кулинарным рецептам. 


## Инструкция по запуску проекта
Клиенируйте проект на свой на ПК:
```
git clone https://github.com/sugatosansiro/foodgram-project-react.git
```
В проекте настроен workflow для автоматического запуска тестов, а также развертки проекта на удаленном сервере 
( foodgram-project-react/.github/workflows/main.yml )

Чтобы запуск workflow прошел успешно, выполните последовательно следующие шаги

### 1. Подготовка сервера перед установкой проекта
Проект устойчиво работает на виртуальных машинах с Ubuntu 20.04.
1.1 Выполните вход на сервер
1.2 Установите на сервер Docker и Docker Compose:
```
sudo apt update
sudo apt install docker.io
sudo apt install docker-compose
```
### 2. Подготовка проекта перед запуском
Укажите значения Secrets, которые нужно обязательно создать для запуска проекта, в вашем репозитории на GitHub - <ваш-репозиторий>/Settings/Security/Secrets and variables/Actions далее "New repository secret".
В ходе выполнения workflow эти secrets используются в том числе и для создания переменных в .env.
Ниже указаны Secrets с примерами:
```
    SECRET_KEY = 'Secretniy#Klyuch#Dlya#Shifrovaniya ' 
    
    HOST = <IP-адрес вашего сервера>
    USER = <имя пользователя для подключения к серверу>
    SSH_KEY = <приватный ключ с компьютера, имеющего доступ к серверу> # по команде на ПК: cat ~/.ssh/id_rsa
    PASSPHRASE = <ваш_пароль_на_севрере> # если при создании ssh-ключа вы использовали фразу-пароль, то сохраните её в эту secret-переменную 

    DOCKER_USERNAME = <ваш_логин_докерхаб>
    DOCKER_PASSWORD = <ваш_пароль_в_докерхаб>

    DB_ENGINE = django.db.backends.postgresql # указываем, что работаем с postgresql
    DB_NAME = postgres # имя базы данных, оставляем его таким во избежании ошибок контейнера
    DB_HOST=db # название сервиса (контейнера), оставляем его таким во избежании ошибок контейнера
    DB_PORT=5432 # порт для подключения к БД
    POSTGRES_USER = postgres # логин для подключения к базе данных
    POSTGRES_PASSWORD = postgres # пароль для подключения к БД (установите свой)

    TELEGRAM_TO = <ID своего телеграм-аккаунта> # Узнать свой ID можно у бота @userinfobot
    TELEGRAM_TOKEN =  <токен вашего телеграм-бота>. # Получить этот токен можно у бота @BotFather
```

### 3. Запуск проекта и проверка его работы:
Проект должен автоматически установиться на указанный сервер и запуститься после выполнения push в ветку master на GitHub
3.1 Выполните push и убедитесь что все шаги успешно выполнены в разделе Actions на GitHub.
3.2 Войдите на сервер и убедитесь что 3 контейнера (*nginx*, *web*, *db*) созданы и запущены - имеют статус "Up":
```
sudo docker container ls -a
```
3.3 Теперь на сервере в контейнере web нужно выполнить миграции, создать суперпользователя и собрать статику.
Для этого последовательно выполните команды, находясь в той же директории с файлом docker-compose.yaml:
```
sudo docker-compose exec web python manage.py migrate
sudo docker-compose exec web python manage.py createsuperuser
sudo docker-compose exec web python manage.py collectstatic --no-input 
```
После успешного выполнения команд, зайдите на < IP-адрес вашего сервера >/admin (например http://130.193.43.181/admin/) и убедитесь, что страница отображается полностью - статика подгрузилась.

3.4 На сервере заполнените базу тестовыми данными, ранее сохраненными в файле fixtures.json - находясь в той же директории с файлом docker-compose.yaml, выполните команду:
```
sudo docker-compose exec web python manage.py loaddata fixtures.json
```
Зайдите на < IP-адрес вашего сервера >/admin, авторизуйтесь под аккаунтом суперпользователя и убедитесь, что на сайте присутсвую ингредиенты и другие данные из fixtures.json

3.5 После завершения работы с контейнерами их можно остановить и удалить, выполнив команду:
```
sudo docker-compose down -v 
```


### Документация к API:
После запуска контейнеров, документация к API будет доступна по адресу:  
```
< IP-адрес вашего сервера >/api/docs/

```

### Автор:
```
Никита Татауров  - https://github.com/sugatosansiro
```
