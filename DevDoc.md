# Описание проекта

##Структура:

```
lib
  \ api
    config
    db
    logger
    models
    modules
    sql
    util
scripts
tests
  \ api
    utils
```

Директории:
- `lib` - сборник исходных кодов приложения
- `lib.api` - методы api приложения
- `lib.config` - парсинг конфига, его валидация
- `lib.db` - работа с базой данных (написан кастомный пул соединений для asyncpg с жадной балансировкой)
- `lib.logger` - форматтер логгера
- `lib.models` - данные, с которыми работает api
- `lib.modules` - внешние модули, которые выполняют какую-либо работу сбоку
- `lib.sql` - обертка над SQL запросами в базу
- `lib.util` - полезные функции

- `scripts` - различные скрипты для быстрой работы или выполнения рутины
- `tests` - тесты
- `tests.api` - тесты API
- `tests.utils` - тесты полезных функций

## Функции, методы, поля

### `lib/api`
Документацию к API лучше смотреть в swagger по пути `/docs`

### `lib/config/config.py`
Парсинг конфига и его стандартизация

`parse_config(filename: str)`
- Парсинг yaml конфига по пути файла
- Аргумент:


### `lib/config/schema.py`
Описание схемы конфига

Отдельную схему секции конфига для модуля можно прописывать в самих модулях

### `lib/db/balancer_policy.py`

#### `class BalancerPolicy`
- Выполняет выбор пула для создания нового соединения
- Среди всех соединений выбирает самое свободное

`async def get_pool(read_only: bool, fallback_master: bool, master_as_replica_weight: float)`
- Выбирает пул для подключения
- `read_only`: позволяет выбирать пул для read_only запросов
- `fallback_master`: позволяет выбрать мастер для read_only запросов
- `master_as_replica_weight`: [0, 1] вес мастера при выборе его для read_only подключения


### `lib/db/database.py`

#### `class Database`
- Класс для взаимодействия с базой
- Синглтон, может вызываться в любом месте взаимодействия

`def connect(read_only=False)`
- Возвращает контекстный менеджер с подключением

### `lib/db/pool.py`
Асинхронный мультихостовый пул коннектов к базе

#### `class PoolAcquireContext`
Контекстный менеджер для коннекта
Выбирает пул, создает контекст и соединение, при выходе, завершает соединение


#### `class PoolManager`
Менеджер соединений
Так же периодически проверяет живость соединений в бекграунде

### `lib/logger/formatter.py`
Форматтер для логгера, пишет либо в формате json, либо в обычном разделенном табами


### `lib/models/common.py`
Общие модели:

- `EDay` - Enum для дней недели: `mon, tue, wed, thu, fri, sat, sun`
- `Time` - Обозначает время в часах и минутах

### `lib/models/events.py`
Модели событий и встреч

- `EDecision` - Enum решение по участию в событии: `yes, maybe, no, undecided`
- `Participant` - Участник встречи: `user: User, decision: EDecision = undecided`
- `ERepeatType` - Enum тип повторения события:
  - `daily` - ежедневно
  - `weakly` - еженедельно
  - `monthly_number` - в определенное число месяца
  - `monthly_day_weekno` - в определенный день определенной недели месяца
  - `yearly` - ежегодно
  - `workday` - каждый рабочий день
- `Repetition` - Параметры повторений события
  - `type: ERepeatType` - тип повторения
  - `weekly_days: EDay[] = []` - дни недели для еженедельных повторений (например каждый понедельник и вторник), если не указано, повторяется только в один день
  - `monthly_last_week: bool` - Для `montly_day_weekno` - событие будет повторятся в этот день недели в последную неделю месяца
  - `due_date: datetime` - До какого числа надо повторять событие (может быть пустым, тогда событие будет повторяться бесконечно)
  - `each: int = 1` - Повторение каждые each единиц (напр для недели - каждые each недель)
- `EChannel` - ENum канал уведомлений: `sms, email, telegram, slack`
- `Notification` - Настройка уведомления
  - `offset: \d+[mhd]` - за сколько времени до события уведомлять (max = 50d), d - дней, h - часов, m - минут
  - `channel: EChannel`
- `Event` - событие
  - `id` - id события
  - `author: User` - автор события
  - `start_time` - время начала события
  - `end_time` - время окончания события
  - `name` - название события
  - `description`: описание события
  - `notifications: Notification[]` - уведомления о событии
  - `participatns: Participant[]` - участники события
  - `repetition: Repetition | None` - параметры повторения
- `RCreateEvent` - запрос на создание события

### `/lib/models/funcs.py`
Модели апи /funcs

- `RCalcFreeTime` - запрос на подсчет свободного времени для пользователей
- `FreeTime` - интервал ближайшего свободного времени

### `/lib/models/users.py`
Модели пользователей

- `Name` - имя польщователя `first: str, last: str`
- `WorkDays` - рабочие дни пользователя
  - `day_from: EDay` - начало рабочей недели
  - `day_to: EDay` - конец рабочей недели
  - `time_from: Time` - начало рабочего времени
  - `time_to: Time` - конец рабочего времени (может быть меньше time_from, тогда конец рабочего дня будет считаться на следующий день)
- `User` - минимальная репрезентация пользователя `login: str, name: Name`
- `UserFull` - полная репрезентация пользователя `login: str, name: Name, work_days: WorkDays | None`
- `ReqUserEvents` - запрос на получение событий с участием пользователя


### `/lib/modules/auth.py`

#### `class Auth`
Авторизация пользователей
Синглтон

Простейшая авторизация по id сессий без паролей, смс, мам, пап и кредитов.<br>
Лучше для этих вещей создавать отдельный сервис, но тут просто id сессии записывается в базу.<br>
Планировалось использовать для видимости встреч, но не дошли руки ее сделать, поэтому авторизация просто существует и ничего не делает<br>

- `def authorize(connection, session_id: str)` - возвращает логин пользователя по id сессии
- `def create_session(connection, login: str)` - создает или обновляет сессию пользователя в базе

### `/lib/modules/notificator.py`

#### `class Notificator`
Уведомления пользователей
Синглтон

Собирает из базы уведомления и рассылает их (пишет в лог)
Для периодических уведомлений дальше устанавливает время следующего оповещения
Запускается в `main.py` на старте сервера


### '/lib/sql/const.py'
Тут лежат названия таблиц для базы

### '/lib/sql/event.py'
Функции для работы с базой событий

- `async def create_table_events(connection)` - создает таблицу событий (вызывается один раз на старте)
- `async def insert_event(connection, request: RCreateEvent) -> Event` - создает запись события в базе, создает записи уведомлений и участников 
- `async def get_one_event(connection, event_id: int)` - возвращает событие по id
- `async def get_many_user_events(connection: Connection, logins: set[str], time_from: datetime, time_to: datetime` - возвращает отсортированный по времени начала список событий нескольких пользователей за определенное время. Если событие имеет повторы в заданном интервале, будут возвращены все повторы


### '/lib/sql/funcs.py'
Работа с функциями календаря

- `async def get_users_busy_time(connection, logins: set[str], start_calc_from: datetime)` - считает занятое время пользователей из списка, учитывает события, где пользователь автор или от участия в которых он не отказался, а так же учитывает рабочие часы пользователей


### '/lib/sql/notifications.py'
Работа с уведомлениями

- `async def create_table_notifications(connection: Connection)` - создает таблицу
- `async def insert_notifications(connection, event: Event)` - создает из события задачи в базе для уведомления пользователей
- `async def get_pending_notifications(connection)` - возвращает список уведомлений, которые нужно взять в обработку
- `async def update_notifications(connection)` - обновляет времена уведомлений

### '/lib/sql/participation.py'
Работа с участниками (биекция пользователь - событие)

- `async def create_table_participation` - создает таблицу
- `async def insert_many_participation(connection, event_id: int, participants: Participant[])` - создает записи в базе
- `async def accept_participation(connection, event_id: int, user_login: str, decision: EDecision)` - принять или отклонить событие

### `/lib/sql/user.py`
Работа с пользователями

- `async def create_table_users` - создает таблицу
- `async def insert_user(connection, user: UserFull)` - создает пользователя
- `async def get_users_from_event_rows(connection, event_rows)` - из списка записей событий из базы возвращает словарь пользователей с логином в качестве ключа
- `async def get_many_users(connection, logins, full=False)` - возвращает список пользователей
- `async def get_user_by_session(connection, session_id)` - возвращает пользователя по session-id
- `async def set_user_session_id(connection, login)` - обновляет session-id пользователя


### `/util/date.py`
Функции для работы с датой


### `/util/module.py` 
базовый модуль и метакласс, превращающий модуль в синглтон


### `/util/repetitions.py`
Функции для итерации по повторам события
