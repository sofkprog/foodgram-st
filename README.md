Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

Инструкция, как запускать проект:
1. Склонируйте репозиторий к себе на компьютер: git clone https://github.com/sofkprog/foodgram-st.git
2. Файл .env в директории /infra уже создан (для тестирования)
3. Запустите докер (приложение или в терминале)
4. Перейдите в директорию /infra
5. В терминале выполните команду docker compose -f infra/docker-compose.yml up -d --build

Перейдите по ссылке http://localhost/recipes

