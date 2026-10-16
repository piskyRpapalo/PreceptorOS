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
const paneles = window.PreceptorZonas.zonas;

/* --- los dos idiomas -------------------------------------------------------
 * Esta cara hablaba solo castellano mientras el resto del producto declaraba
 * dos. Un producto que promete bilingue y traduce la mitad se nota mas que uno
 * que no traduce: es la misma cicatriz que ya se curo en `dashboard.js`.
 * El idioma lo manda la memoria, no el navegador. */
const textos = {
  es: {
    comprobando: "comprobando…", tab_mando: "Mando", tab_chat: "Hablar", tab_frontera: "Frontera",
    tab_cuaderno: "Cuaderno", lo_que_dices: "Lo que dices",
    tab_lab: "Lab", tab_harness: "Harness", tab_puerta: "Puerta pública",
    tab_modelos: "Modelos", tab_ajustes: "Ajustes", zona_no_data: "Sin datos: contenido de esta zona aún no declarado.", zona_activa: "Zona activa:",
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
    chat_sin_respuesta: (edad) => "El orquestador local no respondió. Última respuesta: {edad}.".replace("{edad}", edad), chat_edad_nd: "antigüedad no disponible", chat_listo: "Orquestador local preparado.",
    lab_canales_titulo: "Canales recientes", lab_modelos_titulo: "Modelos locales", lab_cargando: "Consultando el Lab local…", lab_actualizado: "Lectura actualizada.", lab_error: "No se pudo leer el Lab local.", lab_estado_live: "Disponible ahora", lab_estado_stale: "Dato antiguo", lab_estado_ausente: "No está disponible", lab_mensaje_vacio: "Mensaje sin texto", lab_causa_vacia: "Sin causa declarada", lab_mini: "Orquestador mini", lab_grande: "Orquestador grande", lab_eleccion: "Modelo de elección",
    aria_frontera: "Frontera del nodo",
    cuaderno_consentir: "Consentir", cuaderno_retirar: "Retirar", cuaderno_consentido: "Consentido", cuaderno_sin_consentir: "Sin consentir", cuaderno_recibo_pendiente: "Sin cambios recientes", cuaderno_recibo_ok: "Recibo recibido: turno {id}, {estado}.", cuaderno_recibo_error: "No se pudo cambiar este turno.", cuaderno_recibo_red: "No llegó el recibo; no hay cambios confirmados.", cuaderno_sin_texto: "Texto de turno no disponible", cuaderno_recuento: "{t} turnos · {c} consentidos · {r} corregidos",
    harness_cargando: 'Consultando los ciclos locales…', harness_error: 'No se pudieron leer los ciclos locales.',
    harness_frescura_live: (age) => `Actualizado hace ${age} · en directo`,
    harness_frescura_stale: (age) => `Dato antiguo · hace ${age}`,
    harness_vacio: 'Sin ciclos declarados', harness_ultima: 'Última pasada', harness_proxima: 'Próxima pasada', harness_causa: 'Causa', harness_hora_ausente: 'La fuente no suministró este horario',
    modelos_cargando: 'Consultando los modelos locales…', modelos_error: 'No se pudieron leer los modelos locales.', modelos_live: 'Disponible ahora', modelos_stale: 'Dato antiguo', modelos_ausente: 'No disponible', modelos_causa: 'Causa', modelos_causa_vacia: 'Sin causa declarada', modelos_tier1: 'Tier uno', modelos_tier2: 'Tier dos', modelos_adaptador: 'Adaptador',
    puerta_cargando: "Leyendo la puerta local…", puerta_error: "No se pudo leer la puerta local.", puerta_fiel: "La vista traduce las marcas de ausencia; los botones copian el texto fuente exacto.", puerta_llave_titulo: "Llave de entrada", puerta_copiar_llave: "Copiar llave", puerta_llave_ok: "Llave copiada.", puerta_copia_error: "No se pudo copiar la llave.", puerta_documento_titulo: "Documento que lee la IA", puerta_copiar_documento: "Copiar documento fuente", puerta_documento_ok: "Documento copiado.", puerta_documento_error: "No se pudo copiar el documento.", puerta_sin_dato: "Dato no disponible",
  },
  en: {
    comprobando: "checking…", tab_mando: "Command", tab_chat: "Talk", tab_frontera: "Boundary",
    tab_cuaderno: "Notebook", lo_que_dices: "What you say",
    tab_lab: "Lab", tab_harness: "Harness", tab_puerta: "Public gate",
    tab_modelos: "Models", tab_ajustes: "Settings", zona_no_data: "No data: content for this zone has not been declared.", zona_activa: "Active zone:",
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
    chat_sin_respuesta: (edad) => "The local orchestrator did not reply. Last reply: {edad}.".replace("{edad}", edad), chat_edad_nd: "age unavailable", chat_listo: "Local orchestrator ready.",
    lab_canales_titulo: "Recent channels", lab_modelos_titulo: "Local models", lab_cargando: "Checking the local Lab…", lab_actualizado: "Reading updated.", lab_error: "Could not read the local Lab.", lab_estado_live: "Available now", lab_estado_stale: "Stale data", lab_estado_ausente: "Unavailable", lab_mensaje_vacio: "Message has no text", lab_causa_vacia: "No cause declared", lab_mini: "Mini orchestrator", lab_grande: "Large orchestrator", lab_eleccion: "Selection model",
    aria_frontera: "Node boundary",
    cuaderno_consentir: "Consent", cuaderno_retirar: "Withdraw", cuaderno_consentido: "Consented", cuaderno_sin_consentir: "Not consented", cuaderno_recibo_pendiente: "No recent changes", cuaderno_recibo_ok: "Receipt received: turn {id}, {estado}.", cuaderno_recibo_error: "This turn could not be changed.", cuaderno_recibo_red: "No receipt arrived; no changes are confirmed.", cuaderno_sin_texto: "Turn text unavailable", cuaderno_recuento: "{t} turns · {c} consented · {r} corrected",
    harness_cargando: 'Reading local cycles…', harness_error: 'Could not read local cycles.',
    harness_frescura_live: (age) => `Updated ${age} ago · live`,
    harness_frescura_stale: (age) => `Stale · ${age} ago`,
    harness_vacio: 'No cycles declared', harness_ultima: 'Last run', harness_proxima: 'Next run', harness_causa: 'Cause', harness_hora_ausente: 'The source did not supply this schedule',
    modelos_cargando: 'Checking local models…', modelos_error: 'Could not read local models.', modelos_live: 'Available now', modelos_stale: 'Stale data', modelos_ausente: 'Unavailable', modelos_causa: 'Cause', modelos_causa_vacia: 'No cause declared', modelos_tier1: 'Tier one', modelos_tier2: 'Tier two', modelos_adaptador: 'Adapter',
    puerta_cargando: "Reading the local gate…", puerta_error: "Could not read the local gate.", puerta_fiel: "The view translates absence markers; the buttons copy the exact source text.", puerta_llave_titulo: "Entry key", puerta_copiar_llave: "Copy key", puerta_llave_ok: "Key copied.", puerta_copia_error: "Could not copy the key.", puerta_documento_titulo: "Document the AI reads", puerta_copiar_documento: "Copy source document", puerta_documento_ok: "Document copied.", puerta_documento_error: "Could not copy the document.", puerta_sin_dato: "Data unavailable",
  },
  /* Las siete lenguas nuevas (2026-09-23), las mismas que la web y que
   * `textos.py`. Traducidas por Claude; nadie con oido nativo las ha leido.
   * El arabe se escribe de derecha a izquierda: lo pone `pintarEstaticos`. */
  fr: {
    comprobando: "vérification…", tab_mando: "Pilotage", tab_chat: "Parler", tab_frontera: "Frontière",
    tab_cuaderno: "Carnet", lo_que_dices: "Ce que tu dis",
    tab_lab: "Lab", tab_harness: "Harness", tab_puerta: "Porte publique",
    tab_modelos: "Modèles", tab_ajustes: "Réglages", zona_no_data: "Pas de données : contenu de cette zone non déclaré.", zona_activa: "Zone active :",
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
    chat_sin_respuesta: (edad) => "L’orchestrateur local n’a pas répondu. Dernière réponse : {edad}.".replace("{edad}", edad), chat_edad_nd: "âge indisponible", chat_listo: "Orchestrateur local prêt.",
    lab_canales_titulo: "Canaux récents", lab_modelos_titulo: "Modèles locaux", lab_cargando: "Lecture du Lab local…", lab_actualizado: "Lecture actualisée.", lab_error: "Lecture du Lab local impossible.", lab_estado_live: "Disponible maintenant", lab_estado_stale: "Donnée ancienne", lab_estado_ausente: "Indisponible", lab_mensaje_vacio: "Message sans texte", lab_causa_vacia: "Aucune cause déclarée", lab_mini: "Orchestrateur mini", lab_grande: "Orchestrateur grand", lab_eleccion: "Modèle de sélection",
    aria_frontera: "Frontière du nœud",
    cuaderno_consentir: "Consentir", cuaderno_retirar: "Retirer", cuaderno_consentido: "Consentement donné", cuaderno_sin_consentir: "Sans consentement", cuaderno_recibo_pendiente: "Aucun changement récent", cuaderno_recibo_ok: "Reçu reçu : tour {id}, {estado}.", cuaderno_recibo_error: "Impossible de modifier ce tour.", cuaderno_recibo_red: "Aucun reçu reçu ; aucun changement confirmé.", cuaderno_sin_texto: "Texte du tour indisponible", cuaderno_recuento: "{t} tours · {c} consentis · {r} corrigés",
    harness_cargando: 'Lecture des cycles locaux…', harness_error: 'Impossible de lire les cycles locaux.',
    harness_frescura_live: (age) => `Actualisé il y a ${age} · en direct`,
    harness_frescura_stale: (age) => `Donnée ancienne · il y a ${age}`,
    harness_vacio: 'Aucun cycle déclaré', harness_ultima: 'Dernière exécution', harness_proxima: 'Prochaine exécution', harness_causa: 'Cause', harness_hora_ausente: 'La source n’a pas fourni cet horaire',
    modelos_cargando: 'Lecture des modèles locaux…', modelos_error: 'Impossible de lire les modèles locaux.', modelos_live: 'Disponible maintenant', modelos_stale: 'Donnée ancienne', modelos_ausente: 'Indisponible', modelos_causa: 'Cause', modelos_causa_vacia: 'Aucune cause déclarée', modelos_tier1: 'Niveau un', modelos_tier2: 'Niveau deux', modelos_adaptador: 'Adaptateur',
    puerta_cargando: "Lecture de la porte locale…", puerta_error: "Impossible de lire la porte locale.", puerta_fiel: "La vue traduit les marqueurs d’absence ; les boutons copient le texte source exact.", puerta_llave_titulo: "Clé d’entrée", puerta_copiar_llave: "Copier la clé", puerta_llave_ok: "Clé copiée.", puerta_copia_error: "Impossible de copier la clé.", puerta_documento_titulo: "Document lu par l’IA", puerta_copiar_documento: "Copier le document source", puerta_documento_ok: "Document copié.", puerta_documento_error: "Impossible de copier le document.", puerta_sin_dato: "Donnée indisponible",
  },
  pt: {
    comprobando: "a verificar…", tab_mando: "Comando", tab_chat: "Falar", tab_frontera: "Fronteira",
    tab_cuaderno: "Caderno", lo_que_dices: "O que dizes",
    tab_lab: "Lab", tab_harness: "Harness", tab_puerta: "Porta pública",
    tab_modelos: "Modelos", tab_ajustes: "Definições", zona_no_data: "Sem dados: conteúdo desta zona ainda não declarado.", zona_activa: "Zona ativa:",
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
    chat_sin_respuesta: (edad) => "O orquestrador local não respondeu. Última resposta: {edad}.".replace("{edad}", edad), chat_edad_nd: "idade indisponível", chat_listo: "Orquestrador local pronto.",
    lab_canales_titulo: "Canais recentes", lab_modelos_titulo: "Modelos locais", lab_cargando: "A consultar o Lab local…", lab_actualizado: "Leitura atualizada.", lab_error: "Não foi possível ler o Lab local.", lab_estado_live: "Disponível agora", lab_estado_stale: "Dado antigo", lab_estado_ausente: "Indisponível", lab_mensaje_vacio: "Mensagem sem texto", lab_causa_vacia: "Sem causa declarada", lab_mini: "Orquestrador mini", lab_grande: "Orquestrador grande", lab_eleccion: "Modelo de escolha",
    aria_frontera: "Fronteira do nó",
    cuaderno_consentir: "Consentir", cuaderno_retirar: "Retirar", cuaderno_consentido: "Consentido", cuaderno_sin_consentir: "Sem consentimento", cuaderno_recibo_pendiente: "Sem alterações recentes", cuaderno_recibo_ok: "Recibo recebido: turno {id}, {estado}.", cuaderno_recibo_error: "Não foi possível alterar este turno.", cuaderno_recibo_red: "O recibo não chegou; não há alterações confirmadas.", cuaderno_sin_texto: "Texto do turno indisponível", cuaderno_recuento: "{t} turnos · {c} consentidos · {r} corrigidos",
    harness_cargando: 'A consultar os ciclos locais…', harness_error: 'Não foi possível ler os ciclos locais.',
    harness_frescura_live: (age) => `Atualizado há ${age} · ao vivo`,
    harness_frescura_stale: (age) => `Dado antigo · há ${age}`,
    harness_vacio: 'Sem ciclos declarados', harness_ultima: 'Última execução', harness_proxima: 'Próxima execução', harness_causa: 'Causa', harness_hora_ausente: 'A fonte não forneceu este horário',
    modelos_cargando: 'A consultar os modelos locais…', modelos_error: 'Não foi possível ler os modelos locais.', modelos_live: 'Disponível agora', modelos_stale: 'Dado antigo', modelos_ausente: 'Indisponível', modelos_causa: 'Causa', modelos_causa_vacia: 'Sem causa declarada', modelos_tier1: 'Nível um', modelos_tier2: 'Nível dois', modelos_adaptador: 'Adaptador',
    puerta_cargando: "A ler a porta local…", puerta_error: "Não foi possível ler a porta local.", puerta_fiel: "A vista traduz as marcas de ausência; os botões copiam o texto original exato.", puerta_llave_titulo: "Chave de entrada", puerta_copiar_llave: "Copiar chave", puerta_llave_ok: "Chave copiada.", puerta_copia_error: "Não foi possível copiar a chave.", puerta_documento_titulo: "Documento lido pela IA", puerta_copiar_documento: "Copiar documento original", puerta_documento_ok: "Documento copiado.", puerta_documento_error: "Não foi possível copiar o documento.", puerta_sin_dato: "Dado indisponível",
  },
  it: {
    comprobando: "verifica…", tab_mando: "Comando", tab_chat: "Parla", tab_frontera: "Frontiera",
    tab_cuaderno: "Quaderno", lo_que_dices: "Quello che dici",
    tab_lab: "Lab", tab_harness: "Harness", tab_puerta: "Porta pubblica",
    tab_modelos: "Modelli", tab_ajustes: "Impostazioni", zona_no_data: "Nessun dato: contenuto di questa zona non dichiarato.", zona_activa: "Zona attiva:",
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
    chat_sin_respuesta: (edad) => "L’orchestratore locale non ha risposto. Ultima risposta: {edad}.".replace("{edad}", edad), chat_edad_nd: "età non disponibile", chat_listo: "Orchestratore locale pronto.",
    lab_canales_titulo: "Canali recenti", lab_modelos_titulo: "Modelli locali", lab_cargando: "Lettura del Lab locale…", lab_actualizado: "Lettura aggiornata.", lab_error: "Impossibile leggere il Lab locale.", lab_estado_live: "Disponibile ora", lab_estado_stale: "Dato non aggiornato", lab_estado_ausente: "Non disponibile", lab_mensaje_vacio: "Messaggio senza testo", lab_causa_vacia: "Nessuna causa dichiarata", lab_mini: "Orchestratore mini", lab_grande: "Orchestratore grande", lab_eleccion: "Modello di scelta",
    aria_frontera: "Frontiera del nodo",
    cuaderno_consentir: "Consenti", cuaderno_retirar: "Ritira", cuaderno_consentido: "Consenziente", cuaderno_sin_consentir: "Senza consenso", cuaderno_recibo_pendiente: "Nessuna modifica recente", cuaderno_recibo_ok: "Ricevuta ricevuta: turno {id}, {estado}.", cuaderno_recibo_error: "Impossibile modificare questo turno.", cuaderno_recibo_red: "Ricevuta non arrivata; nessuna modifica confermata.", cuaderno_sin_texto: "Testo del turno non disponibile", cuaderno_recuento: "{t} turni · {c} consentiti · {r} corretti",
    harness_cargando: 'Lettura dei cicli locali…', harness_error: 'Impossibile leggere i cicli locali.',
    harness_frescura_live: (age) => `Aggiornato ${age} fa · in diretta`,
    harness_frescura_stale: (age) => `Dato vecchio · ${age} fa`,
    harness_vacio: 'Nessun ciclo dichiarato', harness_ultima: 'Ultima esecuzione', harness_proxima: 'Prossima esecuzione', harness_causa: 'Causa', harness_hora_ausente: 'La fonte non ha fornito questo orario',
    modelos_cargando: 'Lettura dei modelli locali…', modelos_error: 'Impossibile leggere i modelli locali.', modelos_live: 'Disponibile ora', modelos_stale: 'Dato vecchio', modelos_ausente: 'Non disponibile', modelos_causa: 'Causa', modelos_causa_vacia: 'Nessuna causa dichiarata', modelos_tier1: 'Livello uno', modelos_tier2: 'Livello due', modelos_adaptador: 'Adattatore',
    puerta_cargando: "Lettura della porta locale…", puerta_error: "Impossibile leggere la porta locale.", puerta_fiel: "La vista traduce gli indicatori di assenza; i pulsanti copiano il testo sorgente esatto.", puerta_llave_titulo: "Chiave di ingresso", puerta_copiar_llave: "Copia chiave", puerta_llave_ok: "Chiave copiata.", puerta_copia_error: "Impossibile copiare la chiave.", puerta_documento_titulo: "Documento letto dall’IA", puerta_copiar_documento: "Copia documento sorgente", puerta_documento_ok: "Documento copiato.", puerta_documento_error: "Impossibile copiare il documento.", puerta_sin_dato: "Dato non disponibile",
  },
  de: {
    comprobando: "wird geprüft…", tab_mando: "Leitstand", tab_chat: "Reden", tab_frontera: "Grenze",
    tab_cuaderno: "Notizbuch", lo_que_dices: "Was du sagst",
    tab_lab: "Lab", tab_harness: "Harness", tab_puerta: "Öffentliches Tor",
    tab_modelos: "Modelle", tab_ajustes: "Einstellungen", zona_no_data: "Keine Daten: Inhalt dieser Zone ist noch nicht festgelegt.", zona_activa: "Aktive Zone:",
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
    chat_sin_respuesta: (edad) => "Der lokale Orchestrator hat nicht geantwortet. Letzte Antwort: {edad}.".replace("{edad}", edad), chat_edad_nd: "Alter nicht verfügbar", chat_listo: "Lokaler Orchestrator bereit.",
    lab_canales_titulo: "Neueste Kanäle", lab_modelos_titulo: "Lokale Modelle", lab_cargando: "Lokales Lab wird gelesen…", lab_actualizado: "Lesung aktualisiert.", lab_error: "Lokales Lab konnte nicht gelesen werden.", lab_estado_live: "Jetzt verfügbar", lab_estado_stale: "Veraltete Daten", lab_estado_ausente: "Nicht verfügbar", lab_mensaje_vacio: "Nachricht ohne Text", lab_causa_vacia: "Keine Ursache angegeben", lab_mini: "Mini-Orchestrator", lab_grande: "Großer Orchestrator", lab_eleccion: "Auswahlmodell",
    aria_frontera: "Knotengrenze",
    cuaderno_consentir: "Einwilligen", cuaderno_retirar: "Zurückziehen", cuaderno_consentido: "Einwilligung erteilt", cuaderno_sin_consentir: "Keine Einwilligung", cuaderno_recibo_pendiente: "Keine neuen Änderungen", cuaderno_recibo_ok: "Beleg erhalten: Runde {id}, {estado}.", cuaderno_recibo_error: "Diese Runde konnte nicht geändert werden.", cuaderno_recibo_red: "Kein Beleg erhalten; keine Änderung bestätigt.", cuaderno_sin_texto: "Rundentext nicht verfügbar", cuaderno_recuento: "{t} Runden · {c} eingewilligt · {r} korrigiert",
    harness_cargando: 'Lokale Zyklen werden gelesen…', harness_error: 'Lokale Zyklen konnten nicht gelesen werden.',
    harness_frescura_live: (age) => `Vor ${age} aktualisiert · live`,
    harness_frescura_stale: (age) => `Veraltete Daten · vor ${age}`,
    harness_vacio: 'Keine Zyklen angegeben', harness_ultima: 'Letzter Lauf', harness_proxima: 'Nächster Lauf', harness_causa: 'Ursache', harness_hora_ausente: 'Die Quelle hat diesen Zeitplan nicht geliefert',
    modelos_cargando: 'Lokale Modelle werden gelesen…', modelos_error: 'Lokale Modelle konnten nicht gelesen werden.', modelos_live: 'Jetzt verfügbar', modelos_stale: 'Veraltete Daten', modelos_ausente: 'Nicht verfügbar', modelos_causa: 'Ursache', modelos_causa_vacia: 'Keine Ursache angegeben', modelos_tier1: 'Stufe eins', modelos_tier2: 'Stufe zwei', modelos_adaptador: 'Adapter',
    puerta_cargando: "Lokales Tor wird gelesen…", puerta_error: "Lokales Tor konnte nicht gelesen werden.", puerta_fiel: "Die Ansicht übersetzt Abwesenheitsmarkierungen; die Schaltflächen kopieren den exakten Quelltext.", puerta_llave_titulo: "Eingangsschlüssel", puerta_copiar_llave: "Schlüssel kopieren", puerta_llave_ok: "Schlüssel kopiert.", puerta_copia_error: "Schlüssel konnte nicht kopiert werden.", puerta_documento_titulo: "Dokument für die KI", puerta_copiar_documento: "Quelldokument kopieren", puerta_documento_ok: "Dokument kopiert.", puerta_documento_error: "Dokument konnte nicht kopiert werden.", puerta_sin_dato: "Daten nicht verfügbar",
  },
  ru: {
    comprobando: "проверка…", tab_mando: "Командный центр", tab_chat: "Разговор", tab_frontera: "Граница",
    tab_cuaderno: "Тетрадь", lo_que_dices: "Что ты говоришь",
    tab_lab: "Лаборатория", tab_harness: "Harness", tab_puerta: "Публичный шлюз",
    tab_modelos: "Модели", tab_ajustes: "Настройки", zona_no_data: "Нет данных: содержимое этой зоны ещё не объявлено.", zona_activa: "Активная зона:",
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
    chat_sin_respuesta: (edad) => "Локальный оркестратор не ответил. Последний ответ: {edad}.".replace("{edad}", edad), chat_edad_nd: "возраст недоступен", chat_listo: "Локальный оркестратор готов.",
    lab_canales_titulo: "Последние каналы", lab_modelos_titulo: "Локальные модели", lab_cargando: "Чтение локальной лаборатории…", lab_actualizado: "Данные обновлены.", lab_error: "Не удалось прочитать локальную лабораторию.", lab_estado_live: "Сейчас доступно", lab_estado_stale: "Устаревшие данные", lab_estado_ausente: "Недоступно", lab_mensaje_vacio: "В сообщении нет текста", lab_causa_vacia: "Причина не указана", lab_mini: "Мини-оркестратор", lab_grande: "Большой оркестратор", lab_eleccion: "Модель выбора",
    aria_frontera: "Граница узла",
    cuaderno_consentir: "Согласиться", cuaderno_retirar: "Отозвать", cuaderno_consentido: "Согласие дано", cuaderno_sin_consentir: "Без согласия", cuaderno_recibo_pendiente: "Недавних изменений нет", cuaderno_recibo_ok: "Получена квитанция: ход {id}, {estado}.", cuaderno_recibo_error: "Не удалось изменить этот ход.", cuaderno_recibo_red: "Квитанция не получена; изменения не подтверждены.", cuaderno_sin_texto: "Текст хода недоступен", cuaderno_recuento: "{t} ходов · согласие: {c} · исправлено: {r}",
    harness_cargando: 'Читаю локальные циклы…', harness_error: 'Не удалось прочитать локальные циклы.',
    harness_frescura_live: (age) => `Обновлено ${age} назад · сейчас`,
    harness_frescura_stale: (age) => `Устарело · ${age} назад`,
    harness_vacio: 'Циклы не указаны', harness_ultima: 'Последний запуск', harness_proxima: 'Следующий запуск', harness_causa: 'Причина', harness_hora_ausente: 'Источник не указал это расписание',
    modelos_cargando: 'Читаю локальные модели…', modelos_error: 'Не удалось прочитать локальные модели.', modelos_live: 'Доступна сейчас', modelos_stale: 'Устаревшие данные', modelos_ausente: 'Недоступна', modelos_causa: 'Причина', modelos_causa_vacia: 'Причина не указана', modelos_tier1: 'Уровень один', modelos_tier2: 'Уровень два', modelos_adaptador: 'Адаптер',
    puerta_cargando: "Читаю локальную дверь…", puerta_error: "Не удалось прочитать локальную дверь.", puerta_fiel: "В представлении маркеры отсутствия переведены; кнопки копируют точный исходный текст.", puerta_llave_titulo: "Ключ входа", puerta_copiar_llave: "Копировать ключ", puerta_llave_ok: "Ключ скопирован.", puerta_copia_error: "Не удалось скопировать ключ.", puerta_documento_titulo: "Документ для ИИ", puerta_copiar_documento: "Копировать исходный документ", puerta_documento_ok: "Документ скопирован.", puerta_documento_error: "Не удалось скопировать документ.", puerta_sin_dato: "Данные недоступны",
  },
  el: {
    comprobando: "έλεγχος…", tab_mando: "Κέντρο", tab_chat: "Μίλα", tab_frontera: "Σύνορο",
    tab_cuaderno: "Τετράδιο", lo_que_dices: "Τι λες",
    tab_lab: "Εργαστήριο", tab_harness: "Harness", tab_puerta: "Δημόσια πύλη",
    tab_modelos: "Μοντέλα", tab_ajustes: "Ρυθμίσεις", zona_no_data: "Χωρίς δεδομένα: το περιεχόμενο αυτής της ζώνης δεν έχει δηλωθεί.", zona_activa: "Ενεργή ζώνη:",
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
    chat_sin_respuesta: (edad) => "Ο τοπικός ενορχηστρωτής δεν απάντησε. Τελευταία απάντηση: {edad}.".replace("{edad}", edad), chat_edad_nd: "η ηλικία δεν είναι διαθέσιμη", chat_listo: "Ο τοπικός ενορχηστρωτής είναι έτοιμος.",
    lab_canales_titulo: "Πρόσφατα κανάλια", lab_modelos_titulo: "Τοπικά μοντέλα", lab_cargando: "Έλεγχος του τοπικού Lab…", lab_actualizado: "Η ανάγνωση ενημερώθηκε.", lab_error: "Δεν ήταν δυνατή η ανάγνωση του τοπικού Lab.", lab_estado_live: "Διαθέσιμο τώρα", lab_estado_stale: "Παλιό δεδομένο", lab_estado_ausente: "Μη διαθέσιμο", lab_mensaje_vacio: "Μήνυμα χωρίς κείμενο", lab_causa_vacia: "Δεν δηλώθηκε αιτία", lab_mini: "Μικρός ενορχηστρωτής", lab_grande: "Μεγάλος ενορχηστρωτής", lab_eleccion: "Μοντέλο επιλογής",
    aria_frontera: "Όριο κόμβου",
    cuaderno_consentir: "Συγκατάθεση", cuaderno_retirar: "Ανάκληση", cuaderno_consentido: "Με συγκατάθεση", cuaderno_sin_consentir: "Χωρίς συγκατάθεση", cuaderno_recibo_pendiente: "Δεν υπάρχουν πρόσφατες αλλαγές", cuaderno_recibo_ok: "Λήφθηκε απόδειξη: γύρος {id}, {estado}.", cuaderno_recibo_error: "Δεν ήταν δυνατή η αλλαγή αυτού του γύρου.", cuaderno_recibo_red: "Δεν ήρθε απόδειξη· δεν επιβεβαιώνεται αλλαγή.", cuaderno_sin_texto: "Το κείμενο του γύρου δεν είναι διαθέσιμο", cuaderno_recuento: "{t} γύροι · {c} με συγκατάθεση · {r} διορθωμένοι",
    harness_cargando: 'Ανάγνωση τοπικών κύκλων…', harness_error: 'Δεν ήταν δυνατή η ανάγνωση των τοπικών κύκλων.',
    harness_frescura_live: (age) => `Ενημερώθηκε πριν από ${age} · ζωντανά`,
    harness_frescura_stale: (age) => `Παλιό δεδομένο · πριν από ${age}`,
    harness_vacio: 'Δεν δηλώθηκαν κύκλοι', harness_ultima: 'Τελευταία εκτέλεση', harness_proxima: 'Επόμενη εκτέλεση', harness_causa: 'Αιτία', harness_hora_ausente: 'Η πηγή δεν παρείχε αυτό το πρόγραμμα',
    modelos_cargando: 'Ανάγνωση τοπικών μοντέλων…', modelos_error: 'Δεν ήταν δυνατή η ανάγνωση των τοπικών μοντέλων.', modelos_live: 'Διαθέσιμο τώρα', modelos_stale: 'Παλιό δεδομένο', modelos_ausente: 'Μη διαθέσιμο', modelos_causa: 'Αιτία', modelos_causa_vacia: 'Δεν δηλώθηκε αιτία', modelos_tier1: 'Επίπεδο ένα', modelos_tier2: 'Επίπεδο δύο', modelos_adaptador: 'Προσαρμογέας',
    puerta_cargando: "Ανάγνωση της τοπικής πύλης…", puerta_error: "Δεν ήταν δυνατή η ανάγνωση της τοπικής πύλης.", puerta_fiel: "Η προβολή μεταφράζει τις ενδείξεις απουσίας· τα κουμπιά αντιγράφουν το ακριβές κείμενο πηγής.", puerta_llave_titulo: "Κλειδί εισόδου", puerta_copiar_llave: "Αντιγραφή κλειδιού", puerta_llave_ok: "Το κλειδί αντιγράφηκε.", puerta_copia_error: "Δεν ήταν δυνατή η αντιγραφή του κλειδιού.", puerta_documento_titulo: "Έγγραφο που διαβάζει η ΤΝ", puerta_copiar_documento: "Αντιγραφή εγγράφου πηγής", puerta_documento_ok: "Το έγγραφο αντιγράφηκε.", puerta_documento_error: "Δεν ήταν δυνατή η αντιγραφή του εγγράφου.", puerta_sin_dato: "Μη διαθέσιμα δεδομένα",
  },
  ar: {
    comprobando: "جارٍ التحقق…", tab_mando: "مركز القيادة", tab_chat: "تحدّث", tab_frontera: "الحدود",
    tab_cuaderno: "الدفتر", lo_que_dices: "ما تقوله",
    tab_lab: "المختبر", tab_harness: "Harness", tab_puerta: "البوابة العامة",
    tab_modelos: "النماذج", tab_ajustes: "الإعدادات", zona_no_data: "لا توجد بيانات: لم يُعلن محتوى هذه المنطقة بعد.", zona_activa: "المنطقة النشطة:",
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
    chat_sin_respuesta: (edad) => "لم يستجب المنسق المحلي. آخر رد: {edad}.".replace("{edad}", edad), chat_edad_nd: "العمر غير متاح", chat_listo: "المنسق المحلي جاهز.",
    lab_canales_titulo: "القنوات الأخيرة", lab_modelos_titulo: "النماذج المحلية", lab_cargando: "جارٍ فحص المختبر المحلي…", lab_actualizado: "تم تحديث القراءة.", lab_error: "تعذرت قراءة المختبر المحلي.", lab_estado_live: "متاح الآن", lab_estado_stale: "بيانات قديمة", lab_estado_ausente: "غير متاح", lab_mensaje_vacio: "رسالة بلا نص", lab_causa_vacia: "لم يُذكر سبب", lab_mini: "المنسق المصغر", lab_grande: "المنسق الكبير", lab_eleccion: "نموذج الاختيار",
    aria_frontera: "حدود العقدة",
    cuaderno_consentir: "موافقة", cuaderno_retirar: "سحب", cuaderno_consentido: "تمت الموافقة", cuaderno_sin_consentir: "بلا موافقة", cuaderno_recibo_pendiente: "لا تغييرات حديثة", cuaderno_recibo_ok: "وصل الإيصال: الدور {id}، {estado}.", cuaderno_recibo_error: "تعذر تغيير هذا الدور.", cuaderno_recibo_red: "لم يصل الإيصال؛ لا يوجد تغيير مؤكد.", cuaderno_sin_texto: "نص الدور غير متاح", cuaderno_recuento: "{t} أدوار · {c} بموافقة · {r} مصححة",
    harness_cargando: 'جارٍ قراءة الدورات المحلية…', harness_error: 'تعذرت قراءة الدورات المحلية.',
    harness_frescura_live: (age) => `حُدّث منذ ${age} · مباشر`,
    harness_frescura_stale: (age) => `بيانات قديمة · منذ ${age}`,
    harness_vacio: 'لا توجد دورات مُعلنة', harness_ultima: 'آخر تشغيل', harness_proxima: 'التشغيل التالي', harness_causa: 'السبب', harness_hora_ausente: 'لم يوفّر المصدر هذا الجدول',
    modelos_cargando: 'جارٍ فحص النماذج المحلية…', modelos_error: 'تعذرت قراءة النماذج المحلية.', modelos_live: 'متاح الآن', modelos_stale: 'بيانات قديمة', modelos_ausente: 'غير متاح', modelos_causa: 'السبب', modelos_causa_vacia: 'لم يُذكر سبب', modelos_tier1: 'المستوى الأول', modelos_tier2: 'المستوى الثاني', modelos_adaptador: 'المحوّل',
    puerta_cargando: "جارٍ قراءة البوابة المحلية…", puerta_error: "تعذرت قراءة البوابة المحلية.", puerta_fiel: "تعرض الواجهة علامات الغياب مترجمة؛ وتنسخ الأزرار نص المصدر كما هو.", puerta_llave_titulo: "مفتاح الدخول", puerta_copiar_llave: "نسخ المفتاح", puerta_llave_ok: "تم نسخ المفتاح.", puerta_copia_error: "تعذر نسخ المفتاح.", puerta_documento_titulo: "المستند الذي يقرؤه الذكاء الاصطناعي", puerta_copiar_documento: "نسخ مستند المصدر", puerta_documento_ok: "تم نسخ المستند.", puerta_documento_error: "تعذر نسخ المستند.", puerta_sin_dato: "البيانات غير متاحة",
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
    t = textos[l] || textos.en;
  } catch { /* sin respuesta, se queda el de fabrica */ }
  pintarEstaticos();
  actualizarGuionZona();
}
let panelActual = 0;
let filtroCaido = false;
let cancelarGusano = null;
let transicionVista = { origen: null, destino: "mando", tau: 1000000 };

/* --- reorganización · zonas en una sola pestaña ----------------------- */
function actualizarGuionZona() {
  const zona = paneles[panelActual];
  const boton = document.querySelector(`[data-panel="${zona.id}"]`);
  $("guion-zona").textContent = `${t.zona_activa} ${boton.textContent.trim()}.`;
}
function mostrar(i, opciones = {}) {
  const indiceAnterior = panelActual;
  const zonaAnterior = paneles[indiceAnterior];
  panelActual = Math.max(0, Math.min(paneles.length - 1, i));
  paneles.forEach((zona, n) => {
    const boton = document.querySelector(`[data-panel="${zona.id}"]`);
    $("panel-" + zona.panel).hidden = n !== panelActual;
    boton.setAttribute("aria-selected", String(n === panelActual));
    boton.tabIndex = n === panelActual ? 0 : -1;
  });
  actualizarGuionZona();
  if (indiceAnterior !== panelActual && window.PreceptorTransicion) {
    if (cancelarGusano) cancelarGusano();
    const zonaDestino = paneles[panelActual];
    transicionVista = { origen: zonaAnterior.id, destino: zonaDestino.id, tau: 0 };
    cancelarGusano = window.PreceptorTransicion.pintar(
      document.querySelector(`[data-panel="${zonaAnterior.id}"]`),
      document.querySelector(`[data-panel="${zonaDestino.id}"]`),
      {
        espejo: indiceAnterior > panelActual,
        onTau: (tau) => { transicionVista.tau = tau; },
      },
    );
  } else if (indiceAnterior === panelActual) {
    transicionVista = { origen: paneles[panelActual].id, destino: paneles[panelActual].id, tau: 1000000 };
  }
  if (opciones.enfocar) document.querySelector(`[data-panel="${paneles[panelActual].id}"]`).focus();
  if (paneles[panelActual].id === "cuaderno") cargarCuaderno();
  if (paneles[panelActual].id === "lab") cargarLab();
  if (paneles[panelActual].id === "harness") cargarHarness();
  if (paneles[panelActual].id === "modelos") cargarModelos();
  if (paneles[panelActual].id === "puerta") cargarPuerta();
}
document.querySelectorAll(".pestanas [role=tab]").forEach((b, n) => {
  b.addEventListener("click", () => mostrar(n));
  b.addEventListener("keydown", (e) => {
    let siguiente = null;
    if (e.key === "ArrowRight") siguiente = (panelActual + 1) % paneles.length;
    if (e.key === "ArrowLeft") siguiente = (panelActual + paneles.length - 1) % paneles.length;
    if (e.key === "Home") siguiente = 0;
    if (e.key === "End") siguiente = paneles.length - 1;
    if (siguiente !== null) {
      e.preventDefault();
      mostrar(siguiente, { enfocar: true });
    }
  });
});
$("ir-inicio").addEventListener("click", () => mostrar(0, { enfocar: true }));
mostrar(0);

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

/* --- Lab · lectura servida por el endpoint local ------------------------ */
async function cargarLab() {
  $("lab-estado").textContent = t.lab_cargando;
  try {
    const r = await fetch("/api/lab", { cache: "no-store" });
    const d = await r.json();
    if (!r.ok || !d || typeof d !== "object") throw new Error("respuesta inválida");
    const mensajes = d.conversacion && Array.isArray(d.conversacion.mensajes)
      ? d.conversacion.mensajes : [];
    const lista = $("lab-canales");
    lista.replaceChildren();
    mensajes.forEach((m) => {
      const li = document.createElement("li");
      const origen = typeof m.origen === "string" ? m.origen : t.lab_causa_vacia;
      const voz = typeof m.quien === "string" ? m.quien : t.lab_causa_vacia;
      const texto = typeof m.texto === "string" && m.texto.trim()
        ? m.texto : t.lab_mensaje_vacio;
      li.textContent = `${origen} · ${voz}: ${texto}`;
      lista.appendChild(li);
    });
    const modelos = d.modelos && typeof d.modelos === "object" ? d.modelos : {};
    const filas = [
      [t.lab_mini, modelos.mini], [t.lab_grande, modelos.grande],
      [t.lab_eleccion, modelos.eleccion],
    ];
    const ul = $("lab-modelos");
    ul.replaceChildren();
    filas.forEach(([nombre, ficha]) => {
      const li = document.createElement("li");
      const disponible = ficha && ficha.disponible === true;
      const nivel = ficha && (ficha.frescura || ficha.estado);
      const estado = nivel === String.fromCharCode(83, 84, 65, 76, 69) ? t.lab_estado_stale
        : disponible || nivel === String.fromCharCode(77, 69, 68, 73, 68, 79) ? t.lab_estado_live : t.lab_estado_ausente;
      const tag = ficha && typeof ficha.tag === "string" ? ` · ${ficha.tag}` : "";
      li.textContent = `${nombre}${tag}: ${estado}`;
      ul.appendChild(li);
    });
    $("lab-estado").textContent = t.lab_actualizado;
  } catch {
    $("lab-estado").textContent = t.lab_error;
  }
}

/* --- Puerta · documento de entrada servido, sin alterar la copia ---------- */
async function cargarPuerta() {
  const estadoVista = $("puerta-estado");
  estadoVista.textContent = t.puerta_cargando;
  try {
    const idioma = Object.keys(textos).find((k) => textos[k] === t) || "es";
    const r = await fetch(`/api/empieza-aqui?idioma=${encodeURIComponent(idioma)}`, { cache: "no-store" });
    const d = await r.json();
    if (!r.ok || !d || typeof d.llave !== "string" || typeof d.pegable !== "string") {
      throw new Error("documento de entrada no disponible");
    }
    const nd = String.fromCharCode(78, 79, 95, 68, 65, 84, 65);
    $("puerta-llave").textContent = d.llave.replaceAll(nd, t.puerta_sin_dato);
    $("puerta-documento").textContent = d.pegable.replaceAll(nd, t.puerta_sin_dato);
    $("puerta-copiar-llave").onclick = async () => {
      try { await navigator.clipboard.writeText(d.llave); estadoVista.textContent = t.puerta_llave_ok; }
      catch { estadoVista.textContent = t.puerta_copia_error; }
    };
    $("puerta-copiar-documento").onclick = async () => {
      try { await navigator.clipboard.writeText(d.pegable); estadoVista.textContent = t.puerta_documento_ok; }
      catch { estadoVista.textContent = t.puerta_documento_error; }
    };
    estadoVista.textContent = typeof d.bienvenida === "string" ? d.bienvenida : t.tab_puerta;
  } catch {
    estadoVista.textContent = t.puerta_error;
  }
}

/* --- Modelos · tres fichas servidas por el Lab -------------------------- */
async function cargarModelos() {
  const lista = $("modelos-lista");
  const estadoVista = $("modelos-estado");
  lista.replaceChildren();
  estadoVista.textContent = t.modelos_cargando;
  const nd = String.fromCharCode(78, 79, 95, 68, 65, 84, 65);
  const medido = String.fromCharCode(77, 69, 68, 73, 68, 79);
  const stale = String.fromCharCode(83, 84, 65, 76, 69);
  const pintarFicha = (nombre, ficha) => {
    const li = document.createElement("li");
    const titulo = document.createElement("strong");
    const tag = ficha && typeof ficha.tag === "string" ? ` · ${ficha.tag}` : "";
    titulo.textContent = `${nombre}${tag}`;
    li.appendChild(titulo);
    const situacion = ficha && (ficha.frescura || ficha.estado);
    const disponible = ficha && ficha.disponible === true;
    const etiqueta = disponible || situacion === medido ? t.modelos_live
      : situacion === stale ? t.modelos_stale : t.modelos_ausente;
    const estadoTexto = document.createElement("p");
    estadoTexto.textContent = etiqueta;
    li.appendChild(estadoTexto);
    const causa = ficha && typeof ficha.causa === "string" && ficha.causa
      ? ficha.causa : ficha && ficha.adaptador && typeof ficha.adaptador.causa === "string"
        ? ficha.adaptador.causa : t.modelos_causa_vacia;
    if (causa) {
      const razon = document.createElement("p");
      razon.textContent = `${t.modelos_causa}: ${causa}`;
      li.appendChild(razon);
    }
    lista.appendChild(li);
  };
  try {
    const r = await fetch("/api/lab", { cache: "no-store" });
    const d = await r.json();
    const modelos = d && d.modelos;
    if (!r.ok || !modelos || typeof modelos !== "object") throw new Error("respuesta ausente");
    pintarFicha(t.lab_mini, modelos.mini);
    pintarFicha(t.lab_grande, modelos.grande);
    pintarFicha(t.lab_eleccion, modelos.eleccion);
    const eleccion = modelos.eleccion;
    if (eleccion && eleccion.tier1) pintarFicha(t.modelos_tier1, eleccion.tier1);
    if (eleccion && eleccion.tier2) pintarFicha(t.modelos_tier2, eleccion.tier2);
    if (eleccion && eleccion.adaptador) pintarFicha(t.modelos_adaptador, eleccion.adaptador);
    estadoVista.textContent = t.lab_actualizado;
  } catch {
    estadoVista.textContent = t.modelos_error;
  }
}

/* --- Harness · timers servidos por el sensor local del Nexo ------------- */
async function cargarHarness() {
  const frescura = $("harness-frescura");
  const causa = $("harness-causa");
  const lista = $("harness-bucles");
  frescura.textContent = t.harness_cargando;
  causa.hidden = true;
  lista.replaceChildren();
  try {
    const r = await fetch("/api/harness", { cache: "no-store" });
    const d = await r.json();
    const fecha = typeof d.medido === "string" ? Date.parse(d.medido) : NaN;
    if (!r.ok || !Number.isFinite(fecha) || fecha > Date.now() || !Array.isArray(d.bucles)) {
      throw new Error("medición ausente");
    }
    const edad = Math.floor((Date.now() - fecha) / 1000);
    const delta = edad < 60 ? `${edad} s` : `${Math.floor(edad / 60)} min`;
    const nd = String.fromCharCode(78, 79, 95, 68, 65, 84, 65);
    frescura.textContent = d.estado === nd || edad > 300
      ? t.harness_frescura_stale(delta) : t.harness_frescura_live(delta);
    if (d.estado === nd && typeof d.causa === "string") {
      causa.hidden = false;
      causa.textContent = `${t.harness_causa}: ${d.causa}`;
      return;
    }
    if (d.bucles.length === 0) {
      causa.hidden = false;
      causa.textContent = t.harness_vacio;
      return;
    }
    for (const bucle of d.bucles) {
      const li = document.createElement("li");
      const titulo = document.createElement("strong");
      titulo.textContent = typeof bucle.unidad === "string" ? bucle.unidad : t.harness_vacio;
      li.appendChild(titulo);
      const detalle = document.createElement("p");
      const ultima = typeof bucle.ultima === "string" && bucle.ultima !== nd ? bucle.ultima : t.harness_hora_ausente;
      const proxima = typeof bucle.proxima === "string" && bucle.proxima !== nd ? bucle.proxima : t.harness_hora_ausente;
      detalle.textContent = `${t.harness_ultima}: ${ultima} · ${t.harness_proxima}: ${proxima}`;
      li.appendChild(detalle);
      if (typeof bucle.causa === "string" && bucle.causa) {
        const razon = document.createElement("p");
        razon.textContent = `${t.harness_causa}: ${bucle.causa}`;
        li.appendChild(razon);
      }
      lista.appendChild(li);
    }
  } catch {
    frescura.textContent = t.harness_error;
  }
}

/* --- estado ------------------------------------------------------------ */
async function estado() {
  try {
    const r = await fetch("/api/estado");
    const d = await r.json();
    $("estado").textContent = d.motor
      ? t.memoria(d.turnos.turnos, d.turnos.consentidos)
      : t.sin_cerebro;
  } catch {
    $("estado").textContent = t.sin_servidor;
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
  const texto = $("dicho").value.trim();
  if (!texto) return;
  $("dicho").value = "";
  burbuja(texto, "mio");
  $("enviar").disabled = true;
  const esperando = burbuja("pensando… en un teléfono esto son minutos", "espera");
  try {
    const r = await fetch("/api/lab", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    esperando.remove();
    const respuesta = d.respuesta;
    if (r.ok && respuesta && respuesta.estado !== String.fromCharCode(78, 79, 95, 68, 65, 84, 65) && respuesta.texto) {
      burbuja(respuesta.texto);
      $("estado-chat-lab").textContent = t.chat_listo;
    } else {
      const edad = await edadUltimaRespuestaLab();
      $("estado-chat-lab").textContent = t.chat_sin_respuesta(edad);
    }
  } catch {
    esperando.remove();
    $("estado-chat-lab").textContent = t.chat_sin_respuesta(t.chat_edad_nd);
  }
  $("enviar").disabled = false;
});

async function edadUltimaRespuestaLab() {
  try {
    const r = await fetch("/api/lab", { cache: "no-store" });
    const d = await r.json();
    const mensajes = d.conversacion && Array.isArray(d.conversacion.mensajes)
      ? d.conversacion.mensajes : [];
    const ultima = [...mensajes].reverse().find((m) => m.quien === "orquestador" && m.t);
    const marca = ultima ? Date.parse(ultima.t) : NaN;
    if (!Number.isFinite(marca)) return t.chat_edad_nd;
    const segundos = Math.max(0, Math.floor((Date.now() - marca) / 1000));
    return `${segundos} s`;
  } catch {
    return t.chat_edad_nd;
  }
}

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
    const cuenta = d && d.recuento;
    $("recuento").textContent = cuenta && [cuenta.turnos, cuenta.consentidos, cuenta.corregidos].every(Number.isFinite)
      ? t.cuaderno_recuento.replace("{t}", cuenta.turnos).replace("{c}", cuenta.consentidos).replace("{r}", cuenta.corregidos)
      : t.cuaderno_sin_texto;
    const ul = $("turnos");
    ul.replaceChildren();
    for (const t of d.turnos) {
      const li = document.createElement("li");
      const p = document.createElement("div");
      p.className = "p"; p.textContent = typeof t.prompt === "string" ? t.prompt : t.cuaderno_sin_texto;
      const resp = document.createElement("div");
      resp.className = "r"; resp.textContent = typeof (t.correccion || t.respuesta) === "string"
        ? (t.correccion || t.respuesta) : t.cuaderno_sin_texto;
      const acc = document.createElement("div");
      acc.className = "acciones";
      const si = document.createElement("button");
      si.className = "si"; si.dataset.i18n = "cuaderno_consentir";
      si.textContent = t.cuaderno_consentir;
      si.disabled = t.consent;
      const no = document.createElement("button");
      no.className = "no"; no.dataset.i18n = "cuaderno_retirar";
      no.textContent = t.cuaderno_retirar;
      no.disabled = !t.consent;
      const marca = document.createElement("span");
      marca.className = "marca " + (t.consent ? "si" : "no");
      marca.textContent = t.consent ? t.cuaderno_consentido : t.cuaderno_sin_consentir;
      const recibo = document.createElement("span");
      recibo.className = "recibo";
      recibo.dataset.i18n = "cuaderno_recibo_pendiente";
      recibo.setAttribute("role", "status");
      recibo.setAttribute("aria-live", "polite");
      recibo.textContent = t.cuaderno_recibo_pendiente;
      si.addEventListener("click", () => marcar(t.id, true, si, no, marca, recibo));
      no.addEventListener("click", () => marcar(t.id, false, si, no, marca, recibo));
      acc.append(si, no, marca, recibo);
      li.append(p, resp, acc);
      ul.appendChild(li);
    }
  } catch {
    $("recuento").textContent = t.sin_servidor;
  }
}

/* Uno por petición. El carbono marca de uno en uno: no hay "consentir todo",
 * porque un consentimiento en bloque no es un consentimiento. */
async function marcar(id, consent, si, no, marca, recibo) {
  si.disabled = true;
  no.disabled = true;
  try {
    const r = await fetch("/api/captura", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, consent }),
    });
    const d = await r.json();
    if (!r.ok || !d || d.estado !== "ok" || !d.recuento) {
      recibo.textContent = t.cuaderno_recibo_error;
      const actualConsentido = marca.classList.contains("si");
      si.disabled = actualConsentido;
      no.disabled = !actualConsentido;
      return;
    }
    marca.className = "marca " + (consent ? "si" : "no");
    marca.textContent = consent ? t.cuaderno_consentido : t.cuaderno_sin_consentir;
    si.disabled = consent;
    no.disabled = !consent;
    const estado = consent ? t.cuaderno_consentido : t.cuaderno_sin_consentir;
    recibo.textContent = t.cuaderno_recibo_ok.replace("{id}", id).replace("{estado}", estado);
    const c = d.recuento;
    $("recuento").textContent = [c.turnos, c.consentidos, c.corregidos].every(Number.isFinite)
      ? t.cuaderno_recuento.replace("{t}", c.turnos).replace("{c}", c.consentidos).replace("{r}", c.corregidos)
      : t.cuaderno_sin_texto;
  } catch {
    recibo.textContent = t.cuaderno_recibo_red;
    const actualConsentido = marca.classList.contains("si");
    si.disabled = actualConsentido;
    no.disabled = !actualConsentido;
  }
}

/* --- arranque ---------------------------------------------------------- */
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
// El idioma primero: si `estado()` pinta antes, la barra sale en castellano y
// cambia sola medio segundo despues, que se ve peor que tardar medio segundo.
fijarIdioma().then(estado);
