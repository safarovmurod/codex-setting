# Personalization-и воқеӣ
Шеф, насб AGENTS.md-и пурраро ба Codex мегузорад. Барои ChatGPT ҳам майдони воқеиро пур кардан лозим аст; файли матн ҷойи он ҳисоб намешавад.

Агенти насбкунанда: бо Computer Use-и дастгиришаванда Settings → Personalization → Custom Instructions-ро кушо. Аввал майдонҳои ҳозираро ба backup-и маҳаллӣ нигоҳ дор. Матни docs/chatgpt-instructions.txt-ро ба майдони дастурҳо гузор; nickname, occupation ва more_about_you-ро аз profiles/chatgpt-personalization.json пур кун. Фаъол буданашро санҷ ва Save кун. Муҳаррир метавонад поёни саҳифа бошад: аввал viewport-ро scroll кун. Майдонҳоро дубора кушода, матни захирашударо муқоиса кун. Хотираҳо ва privacy-ро иваз накун. Агар даромад ба ҳисоб ё иҷозати соҳиби ҳисоб лозим шавад, ҳамон як амали дақиқро ба шеф деҳ; endpoint ё localStorage-и ғайрирасмӣ истифода набар.

Танҳо баъди read-back ва санҷиши ҷавоб, дар root-и насб personalization-evidence.json навис: {"status":"verified","surface":"ChatGPT actual Personalization UI","verified_at":"actual UTC timestamp"}. Ин файлро ба репо upload накун. Агар UI дастнорас бошад, doctor бояд needs_ui_verification монад. Дар Android бо ҳамон ҳисоб майдони personalization-ро ҳам хонда муқоиса кун; синхронизацияро аз рӯйи тахмин тайёр нагӯй.

OpenAI Docs: https://learn.chatgpt.com/docs/personalize .
