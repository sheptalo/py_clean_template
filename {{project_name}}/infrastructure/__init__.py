"""Слой infrastructure — реализации портов application.

Импорты: application, domain, фреймворки и драйверы (ORM, HTTP-клиенты,
брокеры). Нельзя: presentation.

Сюда относится:
- Реализации портов из application/interfaces: репозитории, шлюзы,
  клиенты внешних API, публикация сообщений.
- Перевод между внешним форматом (строка БД, ответ стороннего API,
  сообщение брокера) и сущностями или DTO.
- Имя отражает технологию и порт: InMemoryItemRepository,
  SqlItemRepository.

Реализация порта попадает в общий контейнер всех entrypoint'ов сама,
scope по умолчанию — REQUEST. Другой scope или выбор одной из
нескольких реализаций порта задаётся через provide() в
InfrastructureProvider (composition/bootstrap/ports.py). Реализация
для одного entrypoint (например, зависит от Request) лежит
в presentation.

Сюда не относится:
- Бизнес-правила и решения «что делать» → domain или application.
- Приём входящих запросов (HTTP, CLI, консьюмеры) → presentation.
- Выбор реализации порта и сборка графа зависимостей → composition.
"""
