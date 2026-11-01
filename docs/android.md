# Android → ҳамон Windows host
1. ChatGPT-и расмиро дар Android нав кун ва бо ҳамон ҳисоб/workspace даро.
2. Дар ПК Settings → Connections → Control this PC → Set up/Add-ро кушо. QR-ро худат бо телефон scan карда, pairing/MFA-ро тамом кун. ПК онлайн ва бедор мемонад.
3. Дар Android Codex ё Remote-ро кушо, ҳамон host ва ҳамон чатро интихоб кун. Барои насб ссылкаи private repo-ро дода бигӯ: «настройкаҳои ҳамин репоро дар ҳамин Windows host насб кун ва doctor-ро санҷ». Воридшавӣ ба GitHub-и private метавонад як бор лозим шавад.
4. Дар чат slash-ро санҷ ва AUTORUN-ро интихоб кун. Агар slash набошад, @AUTORUN-ро аз selector интихоб кун; танҳо навиштани номи номуайян далели даъвати скилл нест.
5. AUTORUN status бояд ҳамон host/task/thread UUID-и ПК-ро нишон диҳад. off аз телефон бояд иҷозати ҳамон вазифаро қатъ кунад. Ин қадамҳоро дар дастгоҳи воқеӣ санҷ.

Ин APK ё patch-и ChatGPT нест. Файлҳои Windows ба storage-и Android нусха намешаванд. Чати мустақили cloud-и бе host аз ин watcher идора намешавад. Барои Android-и пайвастшуда настройкаҳои кор аз host меоянд.
Баъди санҷиши воқеӣ android-evidence.json дар root-и насб нигоҳ дошта мешавад; то он вақт doctor ҳолати needs_owner_pairing_and_live_test медиҳад.
Манбаъ: https://learn.chatgpt.com/docs/remote-connections .

## Агар дар ПК бошаду дар Android набошад
Скилли personal-и маҳаллӣ худ аз худ cloud-плагини ҳисоб намешавад. Барои мобил бастаи plugins/autorun-ро ҳамчун архиви плагин дар ChatGPT → Plugins → Add → Upload plugin archive насб кун. Агар UI-и браузери агент интихоби файлро дастгирӣ накунад, соҳиби ҳисоб файлро интихоб мекунад. Архив танҳо manifest ва як скилли explicit-only дорад; personalization, credential ва source-и controller upload намешаванд. Баъди насби cloud-плагини AUTORUN дар Android selector-и @-ро аз нав кушо. Танҳо баъди намоиш ва санҷиши ҳамон host/thread натиҷа тасдиқ мешавад.

Як бор @AUTORUN-ро интихоб карда фирист. Баъд вазифаҳоро одӣ дар ҳамин чат деҳ; такрори @ лозим нест. AUTORUN off пайвастшавиро қатъ мекунад.
