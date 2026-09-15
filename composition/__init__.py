"""Composition Root — сборка и запуск приложения, снаружи всех слоёв.

Единственное место, которому разрешено знать конкретные классы всех
слоёв.

Сюда относится:
- Entrypoint'ы: фабрики запускаемых приложений (например, api.py) и
  функции main() для [project.scripts]. Клиенты внешних систем, которые
  нужны реализациям портов, к ним не относятся: их фабрики лежат
  в infrastructure.
- DI-провайдеры и выбор реализаций портов (bootstrap/).
- Общий граф провайдеров для всех entrypoint'ов (bootstrap/container):
  use case, реализации портов, настройки и фабрики клиентов из
  infrastructure. Общий для всех entrypoint'ов выбор реализации или
  scope — provide() в InfrastructureProvider.
- Провайдеры отдельного entrypoint: entrypoint передаёт в
  make_container() интеграцию своего фреймворка и PortProvider(<свой
  подпакет presentation>). Выбор реализации или scope только для
  одного entrypoint — provide() в подклассе PortProvider в модуле
  этого entrypoint.

Сюда не относится:
- Любая логика, кроме сборки и запуска: бизнес-правила → domain,
  сценарии → application, адаптеры → infrastructure или presentation.
- Получение зависимостей из контейнера в коде слоёв (Service Locator).
"""
