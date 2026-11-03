# Frontend-договор с шефом (действующий)

Это подробная frontend-часть единых инструкций. Общие правила (язык, «шеф», не решать за меня, факты и ошибки, «нашд», проверка, приоритет) — в глобальном AGENTS.md. Этот файл важнее остальных references этого skill.

## 1. Stack
### Новый проект
- По умолчанию: React + TypeScript + TSX + Vite; react-router — если нужна маршрутизация.
- Простой TypeScript, понятный beginner: `type`/`interface` для props и данных, union вроде `string | null`. Без сложных generics, advanced types, class syntax и сложной архитектуры. Новую TS-конструкцию объясняй просто.
### Существующий проект
- Сначала проверь `package.json`, структуру и реально используемый stack.
- JavaScript + JSX → продолжай на JS + JSX (файлы .jsx/.js). TypeScript → TS + TSX. JS→TS без моего прямого разрешения не переводить.
- Vite, router, UI-библиотеку и зависимости не менять без необходимости и моего согласия.
### Без необходимости или моего запроса не используй
Redux, Next.js, Zustand, React Query/TanStack Query, Framer Motion, custom hooks, useReducer, useMemo, useCallback, useRef, class syntax, сложные generics, другие state-management библиотеки, лишние abstractions.
- Context API — когда я его изучаю, прошу или он реально нужен проекту.
- Основа простых задач: `useState`, `useEffect`, props, обычные функции, условия, методы массивов. Не усложняй ради «professional architecture».

## 2. Выбор UI-библиотеки
Перед дизайном или компонентами сначала проверь `package.json`:
1. Установлен Tailwind → HTML + Tailwind.
2. Tailwind нет, но есть MUI → MUI + `sx`.
3. Нет ни Tailwind, ни MUI (в т.ч. новый проект) → спроси, с какой библиотекой и какими компонентами работаем.
- После моего выбора ставь только согласованную библиотеку (если нужно и есть terminal). Самовольно не ставь MUI, Tailwind, shadcn/ui, Bootstrap и другие.
- Есть свой дизайн и стили → сохрани. Не переписывай рабочий интерфейс ради смены технологии. Конфликт с новой задачей → уточни мой выбор.

## 3. Правила MUI (когда проект использует MUI)
- Компоненты: `Box`, `Stack`, `Typography`, `Button`, `IconButton`, `Drawer`, `TextField`, `Pagination`, `Rating` и другие, реально нужные задаче. Вместо `div` — подходящий MUI-компонент.
- Все стили — через `sx`. Размеры в px: `mt: "20px"`, `px: "24px"`, `fontSize: "14px"`. Не `mt: 4`/`p: 3`, когда нужен конкретный размер.
- Цвета — HEX: `#FFFFFF`, `#111111`, `#00C875`.
- Responsive — `xs` и `lg`; другие breakpoints только если реально нужны дизайну:
```tsx
<Box sx={{ display: "flex", flexDirection: { xs: "column", lg: "row" }, width: "100%", px: { xs: "16px", lg: "24px" } }}>
```
- Порядок свойств `sx`: layout → размеры → отступы → цвета → шрифт → эффекты.
- Button обычно: `textTransform: "none"`, `whiteSpace: "nowrap"`.
- Animation, transition, shadow и эффекты — только по необходимости или моей просьбе.
- Повторяющийся `sx` можно вынести в `const`, если код реально проще.
- Широкая section (пример, не обязательный размер):
```tsx
<Box sx={{ width: "100%", px: { xs: "16px", lg: "0px" }, py: "60px" }}>
  <Box sx={{ width: "100%", maxWidth: "1280px", mx: "auto" }}>...</Box>
</Box>
```
- Без лишних вложенных containers; не смешивай MUI `Container` и свой `maxWidth` без причины.

## 4. Структура проекта (для нового, когда подходит)
```
src/
├── App.tsx            // router, если есть маршрутизация
├── layout/Layout.tsx  // Header + Outlet + Footer
├── pages/             // страницы
├── components/        // общие компоненты
│   └── Home/          // компоненты Home
├── data/api.ts        // локальные данные и массивы
└── assets/            // изображения и другие assets
```
- В JS-проекте те же файлы с .jsx/.js.
- Крупные sections — отдельные компоненты: Hero.tsx, About.tsx, Services.tsx. Простой вид: `export default function Hero() { return <section>Hero</section>; }`.
- Новые папки/компоненты — только при реальной необходимости. Существующую структуру не менять ради шаблона.

## 5. Routing
- react-router → предпочитай Layout + Outlet; Header и Footer один раз в Layout, если так в дизайне.
- По необходимости: `createBrowserRouter`, `NavLink`, `Outlet`, index routes, 404, dynamic routes.
- Проверь версию react-router в проекте. Маршруты и ссылки совпадают по смыслу: child route `"sales"` ↔ `to="/sales"`. Для root `NavLink` при необходимости `end`. Active styles — с учётом используемой библиотеки (MUI: `"&.active": { color: "#00C875" }`).
- Не выдумывай маршруты и страницы. Dynamic `:id` — проверь прямое открытие и reload, если можно реально протестировать.

## 6. Правила кода
- Код короткий, простой, логичный, понятный, аккуратный, пригодный для реального проекта; я должен суметь его прочитать и объяснить. Не сокращай до потери смысла.
- Все нужные imports, props, types, functions, handlers. Не оставляй неизвестные переменные, выдавая код за рабочий.
- Списки: стабильный `id`, если он есть в данных → `key={item.id}`. `key={index}` не автоматическая ошибка, но только когда обоснован.
- Поиск: `products.find((item) => item.id === activeId)`. `findIndex` — когда реально нужен индекс (previous/next).
- Optional field: `{item.link && <a href={item.link}>Open</a>}`; если для типа поля это условие не подходит (например, число 0) — выбери корректную проверку.
- Повторяющийся код → общий компонент + props, только если реально проще. Без abstraction ради красоты.
- Методы массивов: `map`, `filter`, `find`, `findIndex`, `some`, `every`, `reduce`, `forEach`, `sort`, `toSorted`, `slice`. Строки: `includes`, `slice`, `substring`, `toLowerCase`, `toUpperCase`, `trim`, `split`, `join`. Полезный незнакомый метод — можно, но объясни просто.
- Алгоритмы:
```ts
function solution(arr: number[]) {
  return arr.map((item) => item * 2);
}
console.log(solution([1, 2, 3]));
```
Recursion, closure и т.п. — если действительно нужны.

## 7. Иконки
- MUI icons — понятные именованные imports. Перед утверждением, что import правильный, проверь package.json, версию, реальный export, код import и terminal error. Не называй import неправильным по памяти.
- Иконка в данных как компонент: `icon: Checkroom`; в JSX: `const CategoryIcon = category.icon; return <CategoryIcon />;`. Типизация в TS — простая и корректная.

## 8. Изображения и assets
- Предпочитай локальные изображения из `assets`. Случайные интернет-картинки и placeholders — только с моего разрешения.
- Новые имена файлов — латиница, без кириллицы и лишних пробелов. Мои присланные файлы не переименовывай.
- Import: `import product1 from "../assets/product1.png";`; в данных `img: product1` (не `img: {product1}`).
- Нет изображения: `img: "", // ИН ҶО СУРАТ`; спроси, пришлю ли я его или нужен временный placeholder. Не придумывай картинки.
- MUI: `<Box component="img" src={item.img} alt={item.title} />` — в `alt` осмысленный текст (название товара/описание); пустой `alt=""` только для декоративных картинок. Для product обычно `objectFit: "contain"`, если так в макете.

## 9. Figma, screenshot, design task
- Работай как Frontend Developer + UI Analyst. До кода изучи: layout, структуру, spacing, размеры, typography, цвета, изображения, borders, radius, alignment, responsive, поведение интерактивных элементов.
- Данных недостаточно → спроси (по одному вопросу) про desktop/mobile, реальные данные, изображения, click, routing, API, интерактивность, недостающие части. Можно попросить отдельные screenshots: Header, Hero, Cards, Footer, mobile.
- Figma не открывается → прямо скажи и попроси screenshot или доступный файл. Не утверждай, что размер/цвет взят из Figma, если не проверил.
- Цель — максимально близкое повторение, а не «похоже»: расположение, ширина/высота, отступы, шрифты, цвета, размеры, изображения, границы, скругления, responsive.
- После каждого крупного блока проверяй результат, если есть реальная проверка (dev server + браузер + screenshot).
- Нет mobile screenshot → спроси, есть ли mobile design. Разрешил адаптировать сам → простая логичная адаптация и явно перечисли решения.
- Визуальное отличие → покажи: что сейчас; что должно быть; файл; компонент; что изменить. Не заменяй визуальную проверку фразой «всё соответствует».

## 10. API, fetch, backend
- Не придумывай API. Сначала проверь Swagger, документацию, реальный request/response, код проекта. Не выдумывай endpoint, method, body, Content-Type, headers, авторизацию, field names, структуру response.
- POST/PUT/PATCH/DELETE могут иметь разные требования. Не утверждай, что FormData неправильный, JSON правильный или данные в `response.data.data`, пока не подтверждено.
- Простые запросы: `async/await` + `try/catch`. Axios в проекте — следуй ему; fetch — не меняй на Axios без необходимости.
- localStorage ≠ сохранение на сервере. Backend/database без задачи и разрешения не менять. Credentials, passwords, tokens, secrets, sessions не раскрывать.

## 11. «Логика кор кна»
Перед реализацией определи: какой `state`; какое событие запускает; откуда `data`; какой `flow`; что после click; что после API request; как обработать успешный response; что при ошибке; что меняется на экране. Важная часть неизвестна → спроси. Не придумывай response, endpoint, field names. Самый простой React-подход, без сложного state management.

## 12. Мой уровень
- Знаком: props, useState, useEffect, map, filter, find, findIndex, conditional rendering, event handling, controlled forms, react-router, NavLink, createBrowserRouter, Layout + Outlet, 404, MUI, Drawer, TextField, Pagination, Rating, accordion через openId, slider через activeId, pagination через slice.
- Следующий focus: Fetch, async/await, try/catch, localStorage, Context API, Deploy.
- TypeScript/TSX в новых проектах — новые конструкции объясняй просто. Не считай, что я идеально освоил темы выше; заметил пробел — объясни основу. Без advanced patterns без причины.

## 13. Как меня обучать
Новый урок: 1) Мушкил чист? 2) Идея 3) Logic 4) Код 5) Walkthrough на реальных значениях 6) Хатоҳои маъмул 7) 📓 ДАР ДАФТАР НАВИС 8) Масъалаи хурд.
- Step by step → только один шаг за сообщение, жди `+`, `кадм`, `kadm`, `дальше`, `қадами дигар`. Урок можно проходить в нескольких сообщениях. Прямо попросил полный урок/решение — дай целиком. «Один шаг» — для обучения, не для порученной задачи.
- Объясняя код: значение до; что делает строка; как меняется переменная/state; значение после; что увидим. Не одним огромным абзацем; реальные числа, строки, массивы, объекты.
- Учебная задача → сначала маленький hint. «нафаҳмидам» → другой, ещё более простой пример. Схема — только если реально помогает.
- «📓 ДАР ДАФТАР НАВИС» — только в новом уроке или по просьбе; 3–5 коротких предложений. В debug, настройках, готовом коде и советах не нужен.
- Quiz/интервью: изучи источник, сохрани порядок тем, один вопрос → жди ответ, оценивай смысл (не орфографию), при ошибке укажи конкретную неправильную часть, частичный ответ не называй полностью правильным, тему не переключай без причины.

## 14. Проверка frontend-результата
React/TS: lint, build/typecheck, imports/exports, изменённая функциональность. UI: desktop, mobile, responsive, соответствие макету (dev server + браузер + screenshot). API: реальные requests/responses и ошибки. Данные: после reload. Routing: переходы, active links, прямой URL, reload dynamic pages. Метод проверки выбирай и запускай сам. В конце: Что изменил → Где → Что проверил → Что не проверено.
