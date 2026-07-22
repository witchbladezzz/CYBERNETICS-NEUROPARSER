База данных: Мероприятия (`Event`)

Модель `Event` предназначена для хранения информации о событиях, хакатонах, соревнованиях и конференциях, включая их формат, географию, призовой фонд и условия участия.

---

Схема таблицы `events`

```mermaid
erDiagram
    Event {
        BigInt id PK
        String title "Заголовок"
        Text description "Описание"
        String event_type "Тип события"
        String direction "Направление/сфера"
        String source "Источник данных"
        String image "Ссылка на афишу"
        String registration_url UK "Ссылка на регистрацию"
        Decimal prize_fund "Призовой фонд"
        String currency "Валюта"
        DateTime deadline "Дедлайн регистрации"
        DateTime start_date "Дата начала"
        DateTime end_date "Дата окончания"
        Int age_from "Возраст от"
        Int age_to "Возраст до"
        String format "Формат (онлайн/офлайн)"
        String country "Страна"
        String region "Регион"
        String city "Город"
        String status "Статус активности"
        DateTime created_at "Дата создания"
        DateTime updated_at "Дата обновления"
    }