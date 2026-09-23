/* PreceptorOS · la cara premium.
 *
 * LA Regla QUE Gobierna Este Fichero: la interfaz nunca cuenta.
 * Todo número que se pinta sale del payload que devolvió el endpoint. No hay
 * un solo `.length` sobre hallazgos, ni un contador local que se incremente.
 * Si el servidor no lo dijo, aquí no se enseña.
 *
 * Y la segunda: fail-closed. Si el filtro no termina, el envío se apaga y NO
 * hay forma de reactivarlo sin que el filtro corra limpio. No existe el botón
 * de "mandar de todos modos" porque no existe la ruta.
 */
"use strict";

const $ = (id) => document.getElementById(id);
const paneles = ["chat", "frontera", "captura"];

/* --- los dos idiomas -------------------------------------------------------
 * Esta cara hablaba solo castellano mientras el resto del producto declaraba
 * dos. Un producto que promete bilingue y traduce la mitad se nota mas que uno
 * que no traduce: es la misma cicatriz que ya se curo en `dashboard.js`.
 * El idioma lo manda la memoria, no el navegador. */
const textos = {
  es: {
    comprobando: "comprobando…", tab_chat: "Hablar", tab_frontera: "Frontera",
    tab_cuaderno: "Cuaderno", lo_que_dices: "Lo que dices",
    ph_dicho: "Escribe tu respuesta…", dilo: "Dilo",
    pie_chat: "Cada turno tarda minutos en un teléfono. No es que se haya colgado.",
    pie_hallazgos: "Lo de arriba nunca es el texto encontrado: clase y cantidad, nada más. Los números vienen del payload — esta interfaz no cuenta.",
    pie_captura: "Un turno capturado no es un turno consentido. Nada entra en un entrenamiento hasta que lo marcas tú, de uno en uno, y se puede retirar.",
    aria_inicio: "Ir a la portada", aria_redaccion: "Redacción", redaccion_on: "Redacción activa",
    redaccion_off: "Redacción apagada", sin_medir: "sin medir",
    texto_comprobar: "Texto a comprobar",
    ph_prueba: "Pega aquí lo que quieras comprobar antes de que salga…",
    pasar_filtro: "Pasar por el filtro", probando: "probar",
    payload_titulo: "El payload, tal cual llegó", sin_llamada: "(sin llamada todavía)",
    sin_servidor: "no alcanzo al servidor",
    sin_cerebro: "sin cerebro: puedo preguntar y recordar, no conversar",
    memoria: (t, c) => `memoria lista · ${t} turnos · ${c} consentidos`,
    tardo: (m) => `tardó más de la cuenta: ${m}`,
    no_pude: (m) => `no pude responder (${m})`,
    tal_cual: "el texto sale tal cual", sin_contador: "Sin contador: no se ha mirado.",
    sin_llamada2: "(no se hace ninguna llamada)", bloqueado: "envío bloqueado",
    con_hallazgos: "con hallazgos", nada_redactado: "nada redactado",
    no_llego: "(la llamada no llegó)",
    anidar_titulo: "Esto es lo que entraría en tu memoria",
    anidar_boton: "Anidar esto en tu memoria",
    anidar_porque: "Por qué te importa",
    ph_porque: "¿Por qué te importa? (opcional)",
    anidando: "anidando…",
    anidado: "Anidado. Vive en tu memoria, en esta máquina.",
    anidar_no: "no se pudo anidar",
    pie_anidar: "Se guarda el texto tachado, nunca el que pegaste. El filtro vuelve a correr en el servidor al guardar: esta pantalla no decide qué está limpio.",
  },
  en: {
    comprobando: "checking…", tab_chat: "Talk", tab_frontera: "Border",
    tab_cuaderno: "Notebook", lo_que_dices: "What you say",
    ph_dicho: "Write your answer…", dilo: "Say it",
    pie_chat: "Each turn takes minutes on a phone. It has not frozen.",
    pie_hallazgos: "What you see above is never the text that was found: class and count, nothing else. The numbers come from the payload — this interface does not count.",
    pie_captura: "A captured turn is not a consented turn. Nothing enters training until you mark it yourself, one at a time, and it can be withdrawn.",
    aria_inicio: "Go to the front page", aria_redaccion: "Redaction", redaccion_on: "Redaction on",
    redaccion_off: "Redaction off", sin_medir: "not measured",
    texto_comprobar: "Text to check",
    ph_prueba: "Paste here whatever you want checked before it leaves…",
    pasar_filtro: "Run it through the filter", probando: "check",
    payload_titulo: "The payload, exactly as it arrived",
    sin_llamada: "(no call yet)", sin_servidor: "cannot reach the server",
    sin_cerebro: "no brain: I can ask and remember, not converse",
    memoria: (t, c) => `memory ready · ${t} turns · ${c} consented`,
    tardo: (m) => `it took too long: ${m}`,
    no_pude: (m) => `could not answer (${m})`,
    tal_cual: "the text leaves as it is", sin_contador: "No counter: nothing was looked at.",
    sin_llamada2: "(no call is made)", bloqueado: "sending blocked",
    con_hallazgos: "with findings", nada_redactado: "nothing redacted",
    no_llego: "(the call never arrived)",
    anidar_titulo: "This is what would enter your memory",
    anidar_boton: "Nest this in your memory",
    anidar_porque: "Why it matters to you",
    ph_porque: "Why does it matter to you? (optional)",
    anidando: "nesting…",
    anidado: "Nested. It lives in your memory, on this machine.",
    anidar_no: "could not nest",
    pie_anidar: "What gets saved is the redacted text, never the one you pasted. The filter runs again on the server when saving: this screen does not decide what is clean.",
  },
  /* Las siete lenguas nuevas (2026-09-23), las mismas que la web y que
   * `textos.py`. Traducidas por Claude; nadie con oido nativo las ha leido.
   * El arabe se escribe de derecha a izquierda: lo pone `pintarEstaticos`. */
  fr: {
    comprobando: "vérification…", tab_chat: "Parler", tab_frontera: "Frontière",
    tab_cuaderno: "Carnet", lo_que_dices: "Ce que tu dis",
    ph_dicho: "Écris ta réponse…", dilo: "Dis-le",
    pie_chat: "Chaque tour prend des minutes sur un téléphone. Ce n'est pas bloqué.",
    pie_hallazgos: "Ce que tu vois au-dessus n'est jamais le texte trouvé : la classe et le nombre, rien d'autre. Les chiffres viennent du payload — cette interface ne compte pas.",
    pie_captura: "Un tour capturé n'est pas un tour consenti. Rien n'entre dans un entraînement tant que tu ne le marques pas toi-même, un par un, et on peut le retirer.",
    aria_inicio: "Aller à la page d'accueil", aria_redaccion: "Caviardage", redaccion_on: "Caviardage actif",
    redaccion_off: "Caviardage coupé", sin_medir: "non mesuré",
    texto_comprobar: "Texte à vérifier",
    ph_prueba: "Colle ici ce que tu veux vérifier avant que ça parte…",
    pasar_filtro: "Passer au filtre", probando: "vérifier",
    payload_titulo: "Le payload, tel qu'il est arrivé",
    sin_llamada: "(pas encore d'appel)", sin_servidor: "impossible de joindre le serveur",
    sin_cerebro: "pas de cerveau : je peux demander et me souvenir, pas converser",
    memoria: (t, c) => `mémoire prête · ${t} tours · ${c} consentis`,
    tardo: (m) => `ça a pris trop de temps : ${m}`,
    no_pude: (m) => `je n'ai pas pu répondre (${m})`,
    tal_cual: "le texte part tel quel", sin_contador: "Pas de compteur : rien n'a été regardé.",
    sin_llamada2: "(aucun appel n'est fait)", bloqueado: "envoi bloqué",
    con_hallazgos: "avec des trouvailles", nada_redactado: "rien de caviardé",
    no_llego: "(l'appel n'est jamais arrivé)",
    anidar_titulo: "Voici ce qui entrerait dans ta mémoire",
    anidar_boton: "Nicher ceci dans ta mémoire",
    anidar_porque: "Pourquoi ça compte pour toi",
    ph_porque: "Pourquoi ça compte pour toi ? (facultatif)",
    anidando: "nidification…",
    anidado: "Niché. Ça vit dans ta mémoire, sur cette machine.",
    anidar_no: "impossible de nicher",
    pie_anidar: "Ce qui est enregistré est le texte caviardé, jamais celui que tu as collé. Le filtre repasse sur le serveur à l'enregistrement : cet écran ne décide pas de ce qui est propre.",
  },
  pt: {
    comprobando: "a verificar…", tab_chat: "Falar", tab_frontera: "Fronteira",
    tab_cuaderno: "Caderno", lo_que_dices: "O que dizes",
    ph_dicho: "Escreve a tua resposta…", dilo: "Diz",
    pie_chat: "Cada turno demora minutos num telemóvel. Não está pendurado.",
    pie_hallazgos: "O que vês acima nunca é o texto encontrado: classe e quantidade, nada mais. Os números vêm do payload — esta interface não conta.",
    pie_captura: "Um turno captado não é um turno consentido. Nada entra num treino até o marcares tu, um a um, e pode ser retirado.",
    aria_inicio: "Ir para a página inicial", aria_redaccion: "Rasura", redaccion_on: "Rasura ativa",
    redaccion_off: "Rasura desligada", sin_medir: "sem medir",
    texto_comprobar: "Texto a verificar",
    ph_prueba: "Cola aqui o que quiseres verificar antes de sair…",
    pasar_filtro: "Passar pelo filtro", probando: "verificar",
    payload_titulo: "O payload, tal como chegou",
    sin_llamada: "(ainda sem chamada)", sin_servidor: "não chego ao servidor",
    sin_cerebro: "sem cérebro: posso perguntar e recordar, não conversar",
    memoria: (t, c) => `memória pronta · ${t} turnos · ${c} consentidos`,
    tardo: (m) => `demorou demasiado: ${m}`,
    no_pude: (m) => `não consegui responder (${m})`,
    tal_cual: "o texto sai tal como está", sin_contador: "Sem contador: nada foi analisado.",
    sin_llamada2: "(não se faz nenhuma chamada)", bloqueado: "envio bloqueado",
    con_hallazgos: "com achados", nada_redactado: "nada rasurado",
    no_llego: "(a chamada nunca chegou)",
    anidar_titulo: "Isto é o que entraria na tua memória",
    anidar_boton: "Aninhar isto na tua memória",
    anidar_porque: "Porque é que te importa",
    ph_porque: "Porque é que te importa? (opcional)",
    anidando: "a aninhar…",
    anidado: "Aninhado. Vive na tua memória, nesta máquina.",
    anidar_no: "não consegui aninhar",
    pie_anidar: "O que se guarda é o texto rasurado, nunca o que colaste. O filtro volta a correr no servidor ao guardar: este ecrã não decide o que está limpo.",
  },
  it: {
    comprobando: "verifica…", tab_chat: "Parla", tab_frontera: "Frontiera",
    tab_cuaderno: "Quaderno", lo_que_dices: "Quello che dici",
    ph_dicho: "Scrivi la tua risposta…", dilo: "Dillo",
    pie_chat: "Ogni turno richiede minuti su un telefono. Non si è bloccato.",
    pie_hallazgos: "Quello che vedi sopra non è mai il testo trovato: classe e quantità, nient'altro. I numeri vengono dal payload — questa interfaccia non conta.",
    pie_captura: "Un turno catturato non è un turno acconsentito. Niente entra in un addestramento finché non lo segni tu, uno alla volta, e si può ritirare.",
    aria_inicio: "Vai alla pagina iniziale", aria_redaccion: "Oscuramento", redaccion_on: "Oscuramento attivo",
    redaccion_off: "Oscuramento spento", sin_medir: "non misurato",
    texto_comprobar: "Testo da verificare",
    ph_prueba: "Incolla qui quello che vuoi verificare prima che esca…",
    pasar_filtro: "Passalo nel filtro", probando: "verifica",
    payload_titulo: "Il payload, così come è arrivato",
    sin_llamada: "(ancora nessuna chiamata)", sin_servidor: "non raggiungo il server",
    sin_cerebro: "senza cervello: posso chiedere e ricordare, non conversare",
    memoria: (t, c) => `memoria pronta · ${t} turni · ${c} acconsentiti`,
    tardo: (m) => `ci ha messo troppo: ${m}`,
    no_pude: (m) => `non sono riuscito a rispondere (${m})`,
    tal_cual: "il testo esce così com'è", sin_contador: "Nessun contatore: non si è guardato niente.",
    sin_llamada2: "(non si fa nessuna chiamata)", bloqueado: "invio bloccato",
    con_hallazgos: "con riscontri", nada_redactado: "niente oscurato",
    no_llego: "(la chiamata non è mai arrivata)",
    anidar_titulo: "Questo è ciò che entrerebbe nella tua memoria",
    anidar_boton: "Annida questo nella tua memoria",
    anidar_porque: "Perché ti importa",
    ph_porque: "Perché ti importa? (facoltativo)",
    anidando: "annidamento…",
    anidado: "Annidato. Vive nella tua memoria, su questa macchina.",
    anidar_no: "impossibile annidare",
    pie_anidar: "Si salva il testo oscurato, mai quello che hai incollato. Il filtro ripassa sul server al salvataggio: questo schermo non decide cosa è pulito.",
  },
  de: {
    comprobando: "wird geprüft…", tab_chat: "Reden", tab_frontera: "Grenze",
    tab_cuaderno: "Notizbuch", lo_que_dices: "Was du sagst",
    ph_dicho: "Schreib deine Antwort…", dilo: "Sag es",
    pie_chat: "Jede Runde dauert auf einem Telefon Minuten. Es hängt nicht.",
    pie_hallazgos: "Was du oben siehst, ist nie der gefundene Text: Klasse und Anzahl, sonst nichts. Die Zahlen kommen aus dem Payload — diese Oberfläche zählt nicht.",
    pie_captura: "Eine erfasste Runde ist keine eingewilligte Runde. Nichts geht in ein Training, bis du es selbst markierst, eine nach der anderen, und es lässt sich zurückziehen.",
    aria_inicio: "Zur Startseite", aria_redaccion: "Schwärzung", redaccion_on: "Schwärzung an",
    redaccion_off: "Schwärzung aus", sin_medir: "nicht gemessen",
    texto_comprobar: "Zu prüfender Text",
    ph_prueba: "Füge hier ein, was du prüfen willst, bevor es rausgeht…",
    pasar_filtro: "Durch den Filter schicken", probando: "prüfen",
    payload_titulo: "Der Payload, genau wie er ankam",
    sin_llamada: "(noch kein Aufruf)", sin_servidor: "Server nicht erreichbar",
    sin_cerebro: "kein Gehirn: ich kann fragen und mich erinnern, nicht sprechen",
    memoria: (t, c) => `Gedächtnis bereit · ${t} Runden · ${c} eingewilligt`,
    tardo: (m) => `es hat zu lange gedauert: ${m}`,
    no_pude: (m) => `konnte nicht antworten (${m})`,
    tal_cual: "der Text geht unverändert raus", sin_contador: "Kein Zähler: nichts wurde angesehen.",
    sin_llamada2: "(es wird kein Aufruf gemacht)", bloqueado: "Senden blockiert",
    con_hallazgos: "mit Funden", nada_redactado: "nichts geschwärzt",
    no_llego: "(der Aufruf kam nie an)",
    anidar_titulo: "Das würde in dein Gedächtnis gehen",
    anidar_boton: "Das in dein Gedächtnis legen",
    anidar_porque: "Warum es dir wichtig ist",
    ph_porque: "Warum ist es dir wichtig? (optional)",
    anidando: "wird abgelegt…",
    anidado: "Abgelegt. Es lebt in deinem Gedächtnis, auf dieser Maschine.",
    anidar_no: "konnte nicht ablegen",
    pie_anidar: "Gespeichert wird der geschwärzte Text, nie der, den du eingefügt hast. Der Filter läuft beim Speichern noch einmal auf dem Server: dieser Bildschirm entscheidet nicht, was sauber ist.",
  },
  ru: {
    comprobando: "проверка…", tab_chat: "Разговор", tab_frontera: "Граница",
    tab_cuaderno: "Тетрадь", lo_que_dices: "Что ты говоришь",
    ph_dicho: "Напиши свой ответ…", dilo: "Скажи",
    pie_chat: "На телефоне каждый ход занимает минуты. Оно не зависло.",
    pie_hallazgos: "То, что ты видишь выше, — никогда не найденный текст: класс и количество, больше ничего. Числа приходят из payload — этот интерфейс не считает.",
    pie_captura: "Записанный ход — не то же, что ход с согласием. Ничто не попадает в обучение, пока ты сам не отметишь его, по одному, и это можно отозвать.",
    aria_inicio: "На главную", aria_redaccion: "Вычёркивание", redaccion_on: "Вычёркивание включено",
    redaccion_off: "Вычёркивание выключено", sin_medir: "не измерено",
    texto_comprobar: "Текст для проверки",
    ph_prueba: "Вставь сюда то, что хочешь проверить, прежде чем оно уйдёт…",
    pasar_filtro: "Пропустить через фильтр", probando: "проверить",
    payload_titulo: "Payload, в том виде, в каком он пришёл",
    sin_llamada: "(вызова ещё не было)", sin_servidor: "не могу достучаться до сервера",
    sin_cerebro: "нет мозга: могу спрашивать и помнить, но не разговаривать",
    memoria: (t, c) => `память готова · ${t} ходов · ${c} с согласием`,
    tardo: (m) => `это заняло слишком много времени: ${m}`,
    no_pude: (m) => `не смог ответить (${m})`,
    tal_cual: "текст уходит как есть", sin_contador: "Счётчика нет: ничего не проверялось.",
    sin_llamada2: "(вызов не делается)", bloqueado: "отправка заблокирована",
    con_hallazgos: "с находками", nada_redactado: "ничего не вычеркнуто",
    no_llego: "(вызов так и не пришёл)",
    anidar_titulo: "Вот что попало бы в твою память",
    anidar_boton: "Положить это в твою память",
    anidar_porque: "Почему это важно для тебя",
    ph_porque: "Почему это важно для тебя? (необязательно)",
    anidando: "сохраняю…",
    anidado: "Сохранено. Это живёт в твоей памяти, на этой машине.",
    anidar_no: "не удалось сохранить",
    pie_anidar: "Сохраняется вычеркнутый текст, а не тот, что ты вставил. При сохранении фильтр снова проходит на сервере: этот экран не решает, что чисто.",
  },
  el: {
    comprobando: "έλεγχος…", tab_chat: "Μίλα", tab_frontera: "Σύνορο",
    tab_cuaderno: "Τετράδιο", lo_que_dices: "Τι λες",
    ph_dicho: "Γράψε την απάντησή σου…", dilo: "Πες το",
    pie_chat: "Κάθε γύρος παίρνει λεπτά σε ένα τηλέφωνο. Δεν έχει κολλήσει.",
    pie_hallazgos: "Αυτό που βλέπεις πάνω δεν είναι ποτέ το κείμενο που βρέθηκε: κατηγορία και πλήθος, τίποτα άλλο. Οι αριθμοί έρχονται από το payload — αυτή η διεπαφή δεν μετρά.",
    pie_captura: "Ένας γύρος που καταγράφηκε δεν είναι γύρος με συναίνεση. Τίποτα δεν μπαίνει σε εκπαίδευση μέχρι να το σημειώσεις εσύ, έναν έναν, και μπορεί να αποσυρθεί.",
    aria_inicio: "Στην αρχική σελίδα", aria_redaccion: "Σβήσιμο", redaccion_on: "Σβήσιμο ενεργό",
    redaccion_off: "Σβήσιμο ανενεργό", sin_medir: "χωρίς μέτρηση",
    texto_comprobar: "Κείμενο για έλεγχο",
    ph_prueba: "Επικόλλησε εδώ ό,τι θέλεις να ελεγχθεί πριν φύγει…",
    pasar_filtro: "Πέρασέ το από το φίλτρο", probando: "έλεγχος",
    payload_titulo: "Το payload, όπως ακριβώς έφτασε",
    sin_llamada: "(καμία κλήση ακόμη)", sin_servidor: "δεν φτάνω στον διακομιστή",
    sin_cerebro: "χωρίς εγκέφαλο: μπορώ να ρωτώ και να θυμάμαι, όχι να συζητώ",
    memoria: (t, c) => `μνήμη έτοιμη · ${t} γύροι · ${c} με συναίνεση`,
    tardo: (m) => `άργησε πολύ: ${m}`,
    no_pude: (m) => `δεν μπόρεσα να απαντήσω (${m})`,
    tal_cual: "το κείμενο φεύγει όπως είναι", sin_contador: "Χωρίς μετρητή: δεν εξετάστηκε τίποτα.",
    sin_llamada2: "(δεν γίνεται καμία κλήση)", bloqueado: "η αποστολή μπλοκαρίστηκε",
    con_hallazgos: "με ευρήματα", nada_redactado: "τίποτα σβησμένο",
    no_llego: "(η κλήση δεν έφτασε ποτέ)",
    anidar_titulo: "Αυτό θα έμπαινε στη μνήμη σου",
    anidar_boton: "Φώλιασέ το στη μνήμη σου",
    anidar_porque: "Γιατί σε ενδιαφέρει",
    ph_porque: "Γιατί σε ενδιαφέρει; (προαιρετικό)",
    anidando: "φώλιασμα…",
    anidado: "Φωλιάστηκε. Ζει στη μνήμη σου, σε αυτό το μηχάνημα.",
    anidar_no: "δεν ήταν δυνατό το φώλιασμα",
    pie_anidar: "Αποθηκεύεται το σβησμένο κείμενο, ποτέ αυτό που επικόλλησες. Το φίλτρο ξανατρέχει στον διακομιστή κατά την αποθήκευση: αυτή η οθόνη δεν αποφασίζει τι είναι καθαρό.",
  },
  ar: {
    comprobando: "جارٍ التحقق…", tab_chat: "تحدّث", tab_frontera: "الحدّ",
    tab_cuaderno: "الدفتر", lo_que_dices: "ما تقوله",
    ph_dicho: "اكتب جوابك…", dilo: "قُلها",
    pie_chat: "كل دور يستغرق دقائق على الهاتف. لم يتجمّد.",
    pie_hallazgos: "ما تراه في الأعلى ليس أبدًا النص الذي عُثر عليه: الفئة والعدد، لا غير. الأرقام تأتي من الـ payload — هذه الواجهة لا تعدّ.",
    pie_captura: "الدور الملتقط ليس دورًا موافَقًا عليه. لا شيء يدخل تدريبًا حتى تعلّمه أنت، واحدًا تلو الآخر، ويمكن سحبه.",
    aria_inicio: "اذهب إلى الصفحة الرئيسية", aria_redaccion: "الحجب", redaccion_on: "الحجب مفعّل",
    redaccion_off: "الحجب متوقف", sin_medir: "غير مقيس",
    texto_comprobar: "نص للتحقق",
    ph_prueba: "الصق هنا ما تريد التحقق منه قبل أن يخرج…",
    pasar_filtro: "مرّره عبر المرشّح", probando: "تحقّق",
    payload_titulo: "الـ payload، كما وصل تمامًا",
    sin_llamada: "(لا استدعاء بعد)", sin_servidor: "لا أصل إلى الخادم",
    sin_cerebro: "بلا دماغ: أستطيع أن أسأل وأتذكّر، لا أن أحاور",
    memoria: (t, c) => `الذاكرة جاهزة · ${t} أدوار · ${c} بموافقة`,
    tardo: (m) => `استغرق وقتًا أطول من اللازم: ${m}`,
    no_pude: (m) => `لم أستطع الإجابة (${m})`,
    tal_cual: "النص يخرج كما هو", sin_contador: "لا عدّاد: لم يُفحص شيء.",
    sin_llamada2: "(لا يُجرى أي استدعاء)", bloqueado: "الإرسال محظور",
    con_hallazgos: "مع نتائج", nada_redactado: "لم يُحجب شيء",
    no_llego: "(لم يصل الاستدعاء قط)",
    anidar_titulo: "هذا ما سيدخل ذاكرتك",
    anidar_boton: "احفظ هذا في ذاكرتك",
    anidar_porque: "لماذا يهمّك",
    ph_porque: "لماذا يهمّك؟ (اختياري)",
    anidando: "جارٍ الحفظ…",
    anidado: "حُفظ. يعيش في ذاكرتك، على هذا الجهاز.",
    anidar_no: "تعذّر الحفظ",
    pie_anidar: "ما يُحفظ هو النص المحجوب، لا الذي لصقته أبدًا. يعود المرشّح إلى العمل على الخادم عند الحفظ: هذه الشاشة لا تقرّر ما هو نظيف.",
  },
};
let t = textos.es;

function pintarEstaticos() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const v = t[el.dataset.i18n];
    if (typeof v === "string") el.textContent = v;
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    const v = t[el.dataset.i18nPh];
    if (typeof v === "string") el.placeholder = v;
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
    const v = t[el.dataset.i18nAria];
    if (typeof v === "string") el.setAttribute("aria-label", v);
  });
  const lengua = Object.keys(textos).find((k) => textos[k] === t) || "es";
  document.documentElement.lang = lengua;
  document.documentElement.dir = lengua === "ar" ? "rtl" : "ltr";
}

async function fijarIdioma() {
  try {
    const r = await fetch("/api/perfil");
    const d = await r.json();
    const l = (d.campos || d).language || d.idioma;
    // Nueve lenguas desde el 2026-09-23; una que no hay, al castellano de fabrica.
    t = textos[l] || textos.es;
  } catch { /* sin respuesta, se queda el de fabrica */ }
  pintarEstaticos();
}
let panelActual = 0;
let filtroCaido = false;

/* --- navegación · pestañas y deslizar ---------------------------------- */
function mostrar(i) {
  panelActual = Math.max(0, Math.min(paneles.length - 1, i));
  paneles.forEach((p, n) => {
    $("panel-" + p).hidden = n !== panelActual;
    document.querySelector(`[data-panel="${p}"]`)
            .setAttribute("aria-selected", String(n === panelActual));
  });
  if (paneles[panelActual] === "captura") cargarCuaderno();
}
document.querySelectorAll(".pestanas button").forEach((b, n) =>
  b.addEventListener("click", () => mostrar(n)));

/* Deslizar. Se exige que el gesto sea claramente horizontal (2:1) o el
 * scroll vertical del hilo cambiaría de panel sin querer. */
let x0 = null, y0 = null;
const carril = $("carril");
carril.addEventListener("touchstart", (e) => {
  x0 = e.changedTouches[0].clientX; y0 = e.changedTouches[0].clientY;
}, { passive: true });
carril.addEventListener("touchend", (e) => {
  if (x0 === null) return;
  const dx = e.changedTouches[0].clientX - x0;
  const dy = e.changedTouches[0].clientY - y0;
  if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 2) {
    mostrar(panelActual + (dx < 0 ? 1 : -1));
  }
  x0 = y0 = null;
}, { passive: true });

/* --- estado ------------------------------------------------------------ */
async function estado() {
  try {
    const r = await fetch("/api/estado");
    const d = await r.json();
    $("estado").textContent = d.motor
      ? t.memoria(d.turnos.turnos, d.turnos.consentidos)
      : t.sin_cerebro;
    $("enviar").disabled = !d.motor;
  } catch {
    $("estado").textContent = t.sin_servidor;
    $("enviar").disabled = true;
  }
}

/* --- hablar ------------------------------------------------------------ */
function burbuja(texto, clase) {
  const li = document.createElement("li");
  if (clase) li.className = clase;
  li.textContent = texto;
  $("hilo").appendChild(li);
  li.scrollIntoView({ block: "end" });
  return li;
}

$("form-chat").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (filtroCaido) return;                       // estado 4: nada sale
  const texto = $("dicho").value.trim();
  if (!texto) return;
  $("dicho").value = "";
  burbuja(texto, "mio");
  $("enviar").disabled = true;
  const esperando = burbuja("pensando… en un teléfono esto son minutos", "espera");
  try {
    const r = await fetch("/api/charla", {
      method: "Post", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    esperando.remove();
    if (r.ok) {
      burbuja(d.texto);
    } else {
      // Un motor que tardó y uno que falló se dicen distinto: se arreglan
      // distinto, y decirlos igual manda a mirar donde no es.
      burbuja(d.estado === "tarde"
        ? t.tardo(d.motivo)
        : t.no_pude(d.motivo || r.status), "malo");
    }
  } catch (err) {
    esperando.remove();
    burbuja("no alcancé al servidor", "malo");
  }
  $("enviar").disabled = false;
  estado();
});

/* --- frontera ---------------------------------------------------------- */
const sw = $("switch");
let redaccion = true;

function pintarApagado() {
  $("tarjeta-frontera").classList.add("is-off");
  $("tarjeta-frontera").classList.remove("is-blocked");
  $("switch-label").textContent = t.redaccion_off;
  $("insignia").className = "insignia insignia-warn";
  $("insignia").textContent = t.tal_cual;
  $("hallazgos").replaceChildren();
  $("bloqueado").hidden = true;
  // Estado 2: NINGÚN contador. Una lista vacía se leería como "no se encontró
  // nada", y no se buscó nada.
  $("vacio").hidden = false;
  $("vacio").textContent = t.sin_contador;
  $("payload").textContent = t.sin_llamada2;
}

sw.addEventListener("click", () => {
  if (filtroCaido) return;            // con el filtro caído no se toca nada
  redaccion = !redaccion;
  sw.classList.toggle("is-on", redaccion);
  sw.setAttribute("aria-checked", String(redaccion));
  $("probar").disabled = !redaccion;
  if (!redaccion) pintarApagado();
  else {
    $("tarjeta-frontera").classList.remove("is-off");
    $("switch-label").textContent = t.redaccion_on;
    $("insignia").className = "insignia insignia-ok";
    $("insignia").textContent = t.sin_medir;
    $("vacio").hidden = true;
    $("payload").textContent = t.sin_llamada;
  }
});

$("probar").addEventListener("click", async () => {
  const texto = $("prueba").value;
  if (!texto.trim()) return;
  $("probar").disabled = true;
  try {
    const r = await fetch("/api/frontera", {
      method: "Post", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    $("payload").textContent = JSON.stringify(d, null, 2);

    if (r.status === 409) {           // Estado 4 · fail-closed
      filtroCaido = true;
      $("tarjeta-frontera").classList.add("is-blocked");
      $("insignia").className = "insignia insignia-stop";
      $("insignia").textContent = t.bloqueado;
      $("hallazgos").replaceChildren();
      $("vacio").hidden = true;
      $("bloqueado").hidden = false;
      $("bloqueado").textContent =
        "El filtro no pudo terminar, así que no se envía nada. " +
        "El botón sigue apagado hasta que el filtro corra limpio.";
      $("enviar").disabled = true;
      sw.disabled = true;
      return;                          // y `probar` queda deshabilitado
    }

    // Los contadores salen del payload. Ni uno se calcula aquí.
    const hallazgos = d.hallazgos || [];
    const lista = $("hallazgos");
    lista.replaceChildren();
    for (const h of hallazgos) {
      const li = document.createElement("li");
      const p = document.createElement("span");
      p.className = "policy"; p.textContent = h.policy;
      const c = document.createElement("span");
      c.className = "count"; c.textContent = h.count;   // del payload
      li.append(p, c); lista.appendChild(li);
    }
    // Se pregunta por el primer elemento, no por el tamano de la lista: aqui
    // la pregunta es "¿hay algun hallazgo?" y no "¿cuantos hay?". El guardian
    // prohibe medir el tamano en un fichero de interfaz, y hace bien -- un
    // tamano es un recuento aunque se use como booleano, y los recuentos son
    // del servidor. Asi esta linea no puede volverse un numero por accidente.
    if (hallazgos[0]) {                      // Estado 1
      $("insignia").className = "insignia insignia-ok";
      $("insignia").textContent = t.con_hallazgos;
      $("vacio").hidden = true;
    } else {                                 // Estado 3 · declarado, no en blanco
      $("insignia").className = "insignia insignia-ok";
      $("insignia").textContent = t.nada_redactado;
      $("vacio").hidden = false;
      $("vacio").textContent =
        "Nada redactado — el texto ya estaba limpio. Declarado, no en blanco.";
    }
    $("bloqueado").hidden = true;
    $("probar").disabled = false;

    /* La aduana se abre. Se guarda el texto que devolvio el servidor -- no el
       que hay en el area de arriba -- porque es el unico que ha pasado por el
       filtro. Si esta linea leyera `$("prueba").value`, el boton de anidar
       estaria ofreciendo guardar el original sucio con cara de limpio. */
    ultimoLimpio = typeof d.texto === "string" ? d.texto : null;
    if (ultimoLimpio === null) {
      $("anidar-caja").hidden = true;
    } else {
      $("anidar-vista").textContent = ultimoLimpio;
      $("anidar-caja").hidden = false;
      $("anidar").disabled = false;
      $("anidar-dicho").hidden = true;
    }
  } catch {
    $("payload").textContent = t.no_llego;
    $("probar").disabled = false;
    $("anidar-caja").hidden = true;
  }
});

/* --- anidar · el paso que le faltaba a la frontera -----------------------
   Lo que se manda es el texto crudo otra vez, no el limpio que ya tenemos a
   mano. Parece un viaje de mas y es justo lo contrario: el servidor vuelve a
   filtrar por su cuenta y escribe el resultado de SU filtro. Si esta pantalla
   mandara el texto ya limpio, la memoria dependeria de que el navegador no
   tuviera un fallo -- y la promesa del producto no puede descansar sobre eso.

   Por eso `ultimoLimpio` sirve solo para ensenar (y nada mas). No viaja de vuelta. */
let ultimoLimpio = null;

$("anidar").addEventListener("click", async () => {
  const texto = $("prueba").value;
  if (!texto.trim() || ultimoLimpio === null) return;
  $("anidar").disabled = true;
  $("anidar-dicho").hidden = false;
  $("anidar-dicho").textContent = t.anidando;
  try {
    const r = await fetch("/api/anidar", {
      method: "Post", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto, porque: $("anidar-porque").value }),
    });
    const d = await r.json();
    $("payload").textContent = JSON.stringify(d, null, 2);
    if (!r.ok) {
      $("anidar-dicho").textContent = `${t.anidar_no}: ${d.motivo || r.status}`;
      $("anidar").disabled = false;
      return;
    }
    // Se repinta con lo que el servidor dice haber guardado, que puede no ser
    // identico a lo que se enseno antes. Ensenar lo mandado en vez de lo
    // guardado seria inventarse una confirmacion.
    $("anidar-vista").textContent = d.texto;
    $("anidar-dicho").textContent = t.anidado;
    $("anidar-porque").value = "";
    ultimoLimpio = null;          // un texto se anida una vez, no en bucle
  } catch {
    $("anidar-dicho").textContent = t.no_llego;
    $("anidar").disabled = false;
  }
});

/* --- cuaderno ---------------------------------------------------------- */
async function cargarCuaderno() {
  try {
    const r = await fetch("/api/captura");
    const d = await r.json();
    $("recuento").textContent =
      `${d.recuento.turnos} turnos · ${d.recuento.consentidos} consentidos · ` +
      `${d.recuento.corregidos} corregidos`;
    const ul = $("turnos");
    ul.replaceChildren();
    for (const t of d.turnos) {
      const li = document.createElement("li");
      const p = document.createElement("div");
      p.className = "p"; p.textContent = t.prompt;
      const resp = document.createElement("div");
      resp.className = "r"; resp.textContent = t.correccion || t.respuesta;
      const acc = document.createElement("div");
      acc.className = "acciones";
      const si = document.createElement("button");
      si.className = "si"; si.textContent = "consentir";
      si.disabled = t.consent;
      const no = document.createElement("button");
      no.className = "no"; no.textContent = "retirar";
      no.disabled = !t.consent;
      const marca = document.createElement("span");
      marca.className = "marca " + (t.consent ? "si" : "no");
      marca.textContent = t.consent ? "consentido" : "sin consentir";
      si.addEventListener("click", () => marcar(t.id, true));
      no.addEventListener("click", () => marcar(t.id, false));
      acc.append(si, no, marca);
      li.append(p, resp, acc);
      ul.appendChild(li);
    }
  } catch {
    $("recuento").textContent = t.sin_servidor;
  }
}

/* Uno por petición. El carbono marca de uno en uno: no hay "consentir todo",
 * porque un consentimiento en bloque no es un consentimiento. */
async function marcar(id, consent) {
  await fetch("/api/captura", {
    method: "Post", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, consent }),
  });
  cargarCuaderno();
  estado();
}

/* --- arranque ---------------------------------------------------------- */
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
// El idioma primero: si `estado()` pinta antes, la barra sale en castellano y
// cambia sola medio segundo despues, que se ve peor que tardar medio segundo.
fijarIdioma().then(estado);
