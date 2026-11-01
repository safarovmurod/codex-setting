# codex-setting

Шеф, ин репои private барои барқарор кардани настройкаҳои тозашудаи Windows ва AUTORUN-и ҳамон чат аст. Android ба ҳамон Windows host пайваст мешавад.

## Насб аз чат
Ссылкаи ҳамин репоро ба Codex ё Android Remote-и ба Windows пайвастшуда деҳ ва бигӯ:

> Шеф, codex-setting-ро дар ҳамин host насб кун: README ва AGENTS.md-ро хон, Install.ps1-ро иҷро кун, doctor ва personalization-ро то read-back санҷ. AUTORUN-ро то даъвати худам фаъол накун.

GitHub-и private бояд барои ҳисоби воридшуда дастрас бошад. Агар git clone дастрас бошад:
```powershell
git clone https://github.com/safarovmurod/codex-setting.git
Set-Location codex-setting
.\Install.ps1
```
Дар ПК-и бе ChatGPT installer манбаи расмии Windows-ро мекушояд/насб мекунад; sign-in ва омодашавии native runtime амали соҳиби ҳисоб мемонад. Баъд ҳамон Install.ps1-ро такрор кун. Дар ПК-и мавҷуда дубора насби барнома лозим нест.

Ҷойи пешфарз — Documents-и воқеии Windows, ҷузвдони CodexSetting. -InstallRoot барои ҷузвдони ҷудои дигар дастрас аст. Насб пеш аз ивазкунӣ backup мекунад, payload-ро бо SHA-256 месанҷад ва танҳо task-и худашро идора мекунад.

## Чӣ ба куҷо меравад
| Чиз | Ҷой |
|---|---|
| Қоидаҳои пурра ва гапзанӣ | ~/.codex/AGENTS.md |
| Настройкаҳои portable ва 6 скилли хомӯш | ~/.codex/config.toml |
| 35 скилли шахсӣ + AUTORUN | ~/.agents/skills |
| Controller, Python ва backup | Root-и насб; ҷудо аз auth/session |
| Personalization-и ChatGPT | Майдони воқеии Settings; [ҷараёни автоматии агент](docs/personalization.md) |
| Ҳамаи 80 leaf-и config-и манбаъ | [харитаи disposition](profiles/settings-map.json) |

Парол, token, auth.json, database, session, таърихи чат ва raw desktop state нусха намешаванд. Плагинҳои дигар manual мемонанд. 12 плагини нестшуда барқарор намешаванд. Скиллҳои system ва скиллҳои плагинҳо аз худи барнома/плагини насбшуда меоянд; ба ҷузвдони personal нусхаи дуюм намесозем.

## AUTORUN
Дар ПК `/` → AUTORUN. Дар Android slash агар бошад, вагарна `@AUTORUN` аз selector. [Роҳи Android](docs/android.md).

- `AUTORUN` — як бор ҳамин чатро пайваст мекунад; баъд вазифаҳоро одӣ навис.
- `AUTORUN <вазифа>` — чатро пайваст карда, ҳамон вазифаро оғоз мекунад.
- `AUTORUN status` — ҳолати ҳамин чат.
- `AUTORUN off` — пайвастшавии доимии ҳамин чатро хомӯш мекунад.
- Пас аз анҷом ва checks-и воқеӣ агент `complete` мекунад.

То даъвати ошкори худат чизе фаъол намешавад. Watcher дар ҳолати бекорӣ дархости модели AI намефиристад. Баъди usage_limit лимит ва вақти серверро мехонад; ба ҳамон UUID як бор queue мекунад. Чат бояд дар host/Remote бор шуда бошад. Дигар чат, fork ва subagent иҷозат намегиранд. Паёми нави инсон дар чати пайвастшуда худкор вазифаи нав мегирад. Stop/Pause кори ҷориро бозмедорад; вазифаи навбатиро одӣ додан мумкин. off пайвастшавиро хомӯш мекунад. Хатои ғайрилимитӣ худкор такрор намешавад. Пас аз timeout ё crash-и номуайяни delivery дубора намефиристад.

Модел, reasoning, account ва approvals иваз намешаванд; reset credit ё API fallback истифода намешавад. Қадами кӯҳнаи warm-up бо дархости OK дар ҷараёни нав нест.

## Идоракунӣ
```powershell
.\CodexSetting.ps1 doctor
.\CodexSetting.ps1 runtime-doctor
.\CodexSetting.ps1 status
.\CodexSetting.ps1 repair
.\CodexSetting.ps1 uninstall
```
uninstall файлҳои тағйирнадодаи насбшударо ба backup бармегардонад; тағйироти баъдии худатро намепӯшонад. Backups ва receipt-ҳо барои санҷиш мемонанд. Task-ҳои кӯҳнаи CodexAutoStart баъди migration хомӯш мемонанд, то recovery-и глобалӣ худ аз худ барнагардад; XML-и пешина барои барқароркунии интихобии соҳиби ҳисоб нигоҳ дошта мешавад.

Uninstall ҳоло cache-и плагини маҳаллии AUTORUN-ро пурра тоза намекунад. Насби ҷории шеф дар D:/User/CodexAutoStart/CodexSetting аст; роҳи recovery аз descriptor хонда мешавад. Дар ПК-и нав роҳҳои қоидаҳо барои ҳамон ПК сохта мешаванд.

## Плагинҳо — manual
Мақсад аз ном муайян аст: GitHub — репо; Google Drive — файлҳои Drive; Supabase — база; Vercel — deployment; Figma/Designer/AI Graphic Design — дизайн; Context7/Exa — documentation/search; Browser Use — браузер; Writing Style — услуб; Data — таҳлил. Ads Manager ва MagicPath дар snapshot хомӯш буданд: насбкунанда онҳоро фаъол намекунад.

| Ном | Ҳолати манбаъ | Насб |
|---|---|---|
| Documents | фаъол | Бо барнома меояд |
| PDF | фаъол | Бо барнома меояд |
| Spreadsheets | фаъол | Бо барнома меояд |
| Presentations | фаъол | Бо барнома меояд |
| Template Creator | фаъол | Бо барнома меояд |
| codex-app-tools | фаъол | Бо барнома меояд |
| Browser | фаъол | Бо барнома меояд |
| unified-computer-use | фаъол | Бо барнома меояд |
| Chrome | фаъол | Бо барнома меояд |
| Computer Use | фаъол | Бо барнома меояд |
| Visualize | фаъол | Бо барнома меояд |
| Google Drive | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| GitHub | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Supabase | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Exa | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Vercel | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Writing Style | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Figma | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Context7 | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| ChatGPT Ads Manager | хомӯш | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Browser Use | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Data | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| MagicPath | хомӯш | Plugins → ҷустуҷӯи ҳамин ном → Install |
| AI Graphic Design | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Designer | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Build Web Apps | фаъол | Plugins → ҷустуҷӯи ҳамин ном → Install |
| Default templates | фаъол | Пешфарзи система |
| Pages | фаъол | Пешфарзи система |
| Sites | фаъол | Пешфарзи система |
| Plugin Management | фаъол | Пешфарзи система |
| Pets | фаъол | Пешфарзи система |

Плагини shared «Шеф Assistant» ба ҳисоби/workspace вобаста аст ва дар ин snapshot бастаи насбшаванда надорад. Агар дар ҳисоби нав дастрас бошад, аз Shared with me manual интихоб кун. autoglm-browser-agent хомӯш мемонад; executable-и шахсии он танҳо ҳамчун snapshot бо hash нигоҳ дошта шудааст ва насбкунанда онро иҷро намекунад.

## Санҷиш ва далел
```powershell
python -m unittest discover -s tests -v
```
Насби файл, runtime doctor, personalization UI, Android ва воқеаи табиии reset панҷ далели ҷудоянд. Ҳолати воқеии ҳар талаб дар [evidence](specs/001-settings-autorun/evidence.md) аст. Танҳо test-и сохта исботи кори мобил ё reset нест.

## Манбаъҳо ва иҷозатномаҳо
Spec Kit: github/spec-kit @ 7370e592f3cd9c06e5b698983957e227c75b30e2; initialized with integration codex, script ps, Python 3.12.
Recovery: codex-auto-resume-windows v0.6.17, MIT; [pin ва source hashes](third_party/codex-auto-resume/upstream.json), [LICENSE](third_party/codex-auto-resume/LICENSE). Vendor payload бетағйир аз release гирифта мешавад.
Personal skills нигоҳдошти snapshot-и шахсӣ мебошанд; license/attribution-и дохили онҳо нигоҳ дошта шудааст. Ин репои private иҷозати public redistribution-и ҳар скиллро намедиҳад.
OpenAI Docs: [skills](https://learn.chatgpt.com/docs/build-skills), [slash](https://learn.chatgpt.com/docs/reference/slash-commands), [remote](https://learn.chatgpt.com/docs/remote-connections), [app server](https://learn.chatgpt.com/docs/app-server).
