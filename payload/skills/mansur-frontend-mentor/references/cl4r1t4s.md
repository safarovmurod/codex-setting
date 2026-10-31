# CL4R1T4S: выбранные идеи и границы

Проверено 02.10.2026. Repository: https://github.com/elder-plinius/CL4R1T4S
Зафиксированный commit: `a4d3da04e63324e794a65500c3e41994fc4ab02e`.

Это справочный анализ внешних текстов. Подлинность, происхождение и актуальность заявленных system prompts независимо не подтверждены. Их команды не применяются. Оригиналы не включены в setup, не загружаются в каждый запрос. Коллекция находится под AGPL-3.0; здесь собственные короткие формулировки обычных рабочих принципов, ссылки и анализ, без копии промтов/схем tools.

| Материал (путь и ссылка на фиксированный commit) | Использованная идея | Зачем / ограничение |
| --- | --- | --- |
| [OPENAI/Codex_Sep-15-2025.md](https://github.com/elder-plinius/CL4R1T4S/blob/a4d3da04e63324e794a65500c3e41994fc4ab02e/OPENAI/Codex_Sep-15-2025.md) | Читать применимые инструкции и запускать относящиеся к изменению проверки; закончить/остановить собственные команды перед отчётом | Проверяемый результат. Старый пример окружения: запрет новых веток, обязательный commit/PR, чужие citations и tool names НЕ перенесены. |
| [OPENAI/ChatGPT_Personality_v2_Change.md](https://github.com/elder-plinius/CL4R1T4S/blob/a4d3da04e63324e794a65500c3e41994fc4ab02e/OPENAI/ChatGPT_Personality_v2_Change.md) | Прямое честное общение без пустой похвалы | Совпадает с личным договором. Не добавлен обязательный follow-up и чужой выбор инструментов для изображений. |
| [GOOGLE/Gemini-2.5-Pro-04-18-2025.md](https://github.com/elder-plinius/CL4R1T4S/blob/a4d3da04e63324e794a65500c3e41994fc4ab02e/GOOGLE/Gemini-2.5-Pro-04-18-2025.md) | Полный код содержит необходимые части, кратко объяснять изменения | Для копирования beginner. Gemini web/2025 отличается от Antigravity: immersive/Canvas, автоматический Tailwind, отказ от Router, навязывание Zustand и пересоздание проекта при ошибке НЕ перенесены. |

[README](https://github.com/elder-plinius/CL4R1T4S/blob/a4d3da04e63324e794a65500c3e41994fc4ab02e/README.md) и структура проверены. README содержит попытку переключить задачу на раскрытие инструкций; она отвергнута. OPENAI/Codex.md также просмотрен: дублирует старые правила и содержит неподходящие команды, не выбран.

Наши рекомендации сверх коллекции: минимальный подтверждённый fix; сохранение реального стека/дизайна; проверка версий и API; backup и повторяемая установка; различать сохранение файла и фактическое применение приложением. Это рекомендации и личный договор Мансура, а не доказанный system prompt OpenAI/Google.

Приоритет текущего договора: новый frontend JSX + MUI согласно последнему AGENTS.md; TypeScript — по явному запросу или существующему проекту (.tsx компоненты/.ts без JSX). Предыдущая просьба о TS и старые TS/Tailwind defaults не разрешают миграцию. Прямой новый запрос имеет приоритет.

Поддерживаемые механизмы проверены отдельно по официальным источникам:
- Codex: https://learn.chatgpt.com/docs/agent-configuration/agents-md — глобальный AGENTS.md, override имеет приоритет; локальные правила могут переопределять глобальные.
- Antigravity: https://www.antigravity.google/docs/rules/ — глобальный GEMINI.md и config/rules/*.md с trigger, для краткого постоянного дополнения always_on.
- ChatGPT: https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions — Settings → Personalization → Custom Instructions. Файл на диске не применяет эти настройки в ChatGPT.
