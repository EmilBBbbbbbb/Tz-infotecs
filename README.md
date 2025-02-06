# Weather API

## Запуск API
```bash
python script.py
```
## Запуск тестов
```bash
python -m unittest discover -s tests -p "apiTests.py"
```

## Функции API

### 1. `POST /setup`
#### Описание
Создает базу данных для хранения информации о городах и погодных данных.
#### Запрос
```http
POST /setup
```
#### Ответ
```json
{
  "message": "Database created successfully"
}
```

---

### 2. `POST /weather/add_citi`
#### Описание
Добавляет город в базу данных и запрашивает для него текущие данные о погоде.
#### Запрос
```http
POST /weather/add_citi?citi_name=Berlin
```
#### Входные параметры
- `citi_name` (string, query-параметр) – Название города.

#### Ответ
```json
{
  "citi is add": true
}
```

---

### 3. `GET /weather/get_all_cities`
#### Описание
Возвращает список всех городов, сохраненных в базе данных.
#### Запрос
```http
GET /weather/get_all_cities
```
#### Ответ
```json
{
  "all_cities": ["Berlin", "Moscow", "New York"]
}
```

---

### 4. `GET /weather/current`
#### Описание
Возвращает текущие данные о погоде по заданным координатам.
#### Запрос
```http
GET /weather/current?latitude=52.52&longitude=13.405
```
#### Входные параметры
- `latitude` (float, query-параметр) – Широта.
- `longitude` (float, query-параметр) – Долгота.

#### Ответ
```json
{
  "Current temperature_2m": 5.1,
  "Current surface_pressure": 1035.24,
  "Current wind_speed_10m": 11.46
}
```

---

### 5. `GET /weather/forecast`
#### Описание
Возвращает прогноз погоды для указанного города на определенное время.
#### Запрос
```http
GET /weather/forecast?city=Berlin&time=15:00&parameters=temperature,humidity,wind_speed,precipitation
```
#### Входные параметры
- `city` (string, query-параметр) – Название города.
- `time` (string, query-параметр) – Время в формате `HH:MM`.
- `parameters` (list, query-параметр) – Список запрашиваемых метеорологических параметров (доступны `temperature`, `humidity`, `wind_speed`, `precipitation`).

#### Ответ
```json
{
  "city": "Berlin",
  "requested_time": "15:00",
  "closest_time": "15:10",
  "forecast": {
    "temperature": 7.2,
    "humidity": 80,
    "wind_speed": 5.3,
    "precipitation": 0.2
  }
}
```

---

## Фоновое обновление данных
Каждые 15 минут API автоматически обновляет данные о погоде для всех сохраненных в базе городов.

## Описание тестов

* Тест создания базы данных: проверяет, создается ли база данных корректно.

* Тест получения списка городов: проверяет, возвращает ли API корректный список сохраненных городов.

* Тест текущей погоды: проверяет, корректно ли API получает и возвращает текущие метеоданные по заданным координатам.

* Тест прогноза погоды: проверяет, правильно ли API извлекает и форматирует прогнозные данные по заданному городу и времени.
