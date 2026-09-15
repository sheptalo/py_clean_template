"""Composition Root — сборка и запуск приложения, снаружи всех слоёв.

Единственное место, которому разрешено знать конкретные классы всех
слоёв.

Сюда относится:
- Entrypoint'ы: фабрики приложений (например, api.py) и функции main()
  для [project.scripts].
- DI-провайдеры и выбор реализаций портов (bootstrap/).
- Общий граф провайдеров для всех entrypoint'ов (bootstrap/container):
  интеракторы и реализации портов из infrastructure. Общий для всех
  entrypoint'ов выбор реализации или scope — provide() в
  InfrastructureProvider.
- Провайдеры отдельного entrypoint: entrypoint передаёт в
  make_container() интеграцию своего фреймворка и PortProvider(<свой
  подпакет presentation>), например make_container(FastapiProvider(),
  PortProvider(fastapi_presentation)). Выбор реализации или scope
  только для одного entrypoint — provide() в подклассе PortProvider
  в модуле этого entrypoint.

Сюда не относится:
- Любая логика, кроме сборки и запуска: бизнес-правила → domain,
  сценарии → application, адаптеры → infrastructure или presentation.
- Получение зависимостей из контейнера в коде слоёв (Service Locator).
"""
