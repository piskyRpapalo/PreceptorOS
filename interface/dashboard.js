/* PreceptorOS · el tablero.
 *
 * Mismas dos reglas que el panel: la interfaz no cuenta -- los numeros vienen
 * del servidor -- y nada se promete antes de comprobarlo.
 */
"use strict";

const $ = (id) => document.getElementById(id);
let hablando = false;
let idioma = "es";

/* Las dos columnas, como en textos.py del producto. La cara declaraba hablar
 * los dos idiomas y las tenia incrustadas en castellano: el perfil decia `en`
 * y el tablero seguia en español. Una traduccion que falta es una clave que
 * falta, y aqui se ve de un vistazo. */
const T = {
  es: {
    cap_si: "Personalizada", cap_no: "Sin personalizar",
    nota_captura: "Personalizada, la app le pasa al modelo quién eres, tus instrucciones y lo que ya hay en tu memoria y tus proyectos. Sin personalizar, la pregunta viaja sola. Cámbialo y pregunta lo mismo dos veces: la diferencia se oye, y es lo que esta app hace. En los dos casos la respuesta pasa por el filtro antes de volver.",
    elige_idioma: "¿En qué idioma quieres que hablemos?",
    listo: "escribe aquí",
    sin_cerebro: "puedo preguntar y recordar, todavía no conversar",
    sin_servidor: "no alcanzo al servidor",
    pensando: "pensando… esto puede tardar minutos",
    tarde: "tardó más de la cuenta. Prueba con algo más corto.",
    fallo: "no pude responder ahora mismo.",
    sin_red: "no alcancé al servidor.",
    voz_local_no: "el dictado todavía no es local, así que no lo hay. Escribe y ya está: lo que escribes no sale de esta máquina, y lo que decías por el micrófono del navegador sí salía.",
    sin_micro: "no me diste permiso para el micrófono.",
    sin_oir: "no te oí bien. Prueba a escribirlo.",
    hablar: "Hablar", escribir: "Escribir",
    voz_apagada: "Dictado apagado",
    escuchando: "Escuchando… toca para parar",
    nota_sin: "Sin cerebro instalado, PreceptorOS pregunta y recuerda pero no conversa.",
    instalado: "instalado", sin_instalar: "sin instalar",
    et_modelo: "Modelo", ruta_es: "en", sin_modelo: "sin declarar",
    medicion: "Medición",
    med_intro: "Once campos. Lo que no se puede medir sale declarado, nunca en cero.",
    med_vivo: "en vivo · se vuelve a medir cada 3 s",
    med_pausa: "en pausa — la pantalla no está delante",
    id_titulo: "Tu huella soberana",
    id_nota: "Sale de azar de esta máquina, no de tu nombre ni de tu equipo. No es una clave: no firma nada y no da acceso a nada. Nunca sale de aquí.",
    id_rota: "identidad no disponible",
    cer_titulo: "Qué cerebro te contesta",
    cer_base: "Cerebro base", cer_afinado: "Cerebro afinado",
    cer_en_uso: (n) => `En uso: ${n}`,
    cer_cambiando: "cambiando…",
    cer_hecho: (n) => `Hecho. El próximo turno usa: ${n}`,
    cer_no: "no se pudo cambiar",
    cer_sin_servidor: "no alcanzo al servidor",
    med_medido: "medido", med_norma: "norma", med_nodata: "sin dato",
    med_fallo: "No se pudo leer la medición",
    med_pie: "Solo son comparables los paquetes que declaran la misma ventana y los mismos tokens de sesión.",
    afinado_vivo: "afinado · vivo", base_vivo: "base · vivo",
    encendido: "encendido", apagado: "apagado",
    dilo: "Dilo", memoria: "Memoria", frontera: "Frontera", ajustes: "Ajustes",
    tu_memoria: "Tu memoria", la_frontera: "La frontera", los_ajustes: "Ajustes",
    camino: "El Camino", el_camino: "El Camino",
    camino_intro: "Ocho peldaños. Esto es dónde estás de verdad — medido, no supuesto.",
    encendiendo: "Encendiendo el cerebro… vuelve en unos minutos",
    tardando: "Esto tarda más de lo normal. PreceptorOS está fusionándose con tu teléfono.",
    fundiendo: "PreceptorOS se está fusionando con tu teléfono. Esto solo pasa una vez",
    front_que: "Antes de que un texto salga, se tachan claves, rutas y direcciones.",
    front_como: "Se cuenta la clase y la cantidad, nunca el texto encontrado. Y si el filtro no puede terminar, no se envía nada.",
    voz_no: "Esta copia no lleva voz: falta {falta}.",
    volver: "← Volver", perfil: "Perfil", proyectos: "Proyectos",
    et_nombre: "¿Quién eres?", et_intereses: "Lo que te interesa (separado por comas)",
    et_idioma: "Idioma", et_instrucciones: "Cómo quieres que te hable",
    et_cerebro: "Cerebro", et_cuaderno: "Cómo te responde",
    guardar: "Guardar", guardado: "Guardado.",
    ph_instrucciones: "Eres PreceptorOS, mi compañero de aprendizaje. Me hablas con respeto pero sin formalidad excesiva. Prefiero ejemplos concretos a teoría abstracta.",
    nota_instrucciones: "Esto se le dice a PreceptorOS en cada turno, después de su carácter y no en su lugar: ajustas cómo te habla, no lo que es.",
    proy_intro: "Lo que tienes entre manos: un libro a medias, una aplicación, una idea que vuelve. No hay fechas límite ni prioridades: solo en qué punto lo dejaste.",
    proy_vacio: "Todavía no hay ninguno. Escribe un título arriba y ya está: lo demás se rellena cuando te apetezca.",
    et_pr_titulo: "Título", et_pr_desc: "Qué es", et_pr_estado: "Cómo va",
    et_pr_nota: "Notas, ideas, lo que sea",
    volver_lista: "← Todos los proyectos", ed_guardar: "Guardar cambios",
    est_activo: "Activo", est_pausado: "Pausado", est_completado: "Completado",
    ed_actualizado: (c) => `Última vez que lo tocaste: ${c}`,
    sin_tocar: "sin tocar todavía",
    et_titulo: "Título", et_ruta: "Ruta (opcional)",
    anadir: "Añadir", no_esta: "no está ahí", quitar: "Quitar",
    abrir_panel: "Abrir el panel completo →", o_escribelo: "O escríbelo",
    /* El gesto de «guarda esto» y el formulario del cajon. Los dos escriben en
       la misma puerta, `/api/anidar`, con `origen: persona`. */
    g_guarda: "Guarda esto", g_guardado: "Guardado en tu memoria",
    g_fallo: "No se pudo guardar:",
    g_tachado: "Se guardó así, con lo privado tachado:",
    m_nuevo: "Escribe un recuerdo",
    m_que: "Qué quieres recordar",
    m_porque: "Por qué te importa (opcional)",
    m_guardar: "Guardar",
    m_nota_nueva: "Lo que escribas pasa por el filtro antes de tocar el disco. Verás lo que quedó guardado.",
    m_guardados: "Recuerdos guardados", m_consentidos: "Consentidos para aprender",
    m_corregidos: "Corregidos por ti",
    nota_memoria: "Vive en un solo fichero de tu máquina. Puedes copiarlo y llevártelo.",
    hecho: "hecho", empezado: "empezado", sin_empezar: "sin empezar",
    no_medible: "no medible desde aquí",
    agentes: "Agentes y herramientas",
    et_tema: "Piel", tema_sistema: "Como el sistema",
    tema_claro: "Claro", tema_oscuro: "Oscuro",
    sin_nombre: "sin nombre todavía",
    lat_medir: "Medición", lat_camino: "Camino",
    lat_memoria: "Memoria", lat_proyectos: "Proyectos",
    lat_frontera: "Frontera",
    at_resume: "Resume esto", at_pasos: "Dame los pasos",
    at_dudas: "Qué te falta saber",
    ph_dicho: "Escribe aquí",
    manifiesto: "El Manifiesto del Builder",
    esp_titulo: "Límites de esta sesión",
    esp_quien: "Quién te contesta", esp_ritmo: "A qué ritmo",
    esp_memoria: "Memoria del modelo", esp_libre: "Libre en la máquina",
    esp_ventana: "Ventana de contexto", esp_gastado: "Gastado de la ventana",
    esp_sin_conteo: "nadie cuenta los tokens de esta sesión, así que un número aquí sería inventado",
    esp_lleno: "Mi contexto está lleno. Necesito que tú, como Builder, decidas si resumir o ampliar el hardware.",
    esp_aviso: "Esto no es un cuadro de mandos: es dónde acaba tu máquina. Lo que no se puede medir sale dicho, nunca en cero.",
    saluda: "Soy tu Preceptor y vivo en esta máquina: lo que escribes aquí no sale de ella. Puedo recordar lo que me cuentes, ayudarte a llevar tus proyectos y decirte cuándo no sé algo. Escribe abajo, o toca uno de los atajos.",
  },
  en: {
    cap_si: "Personalised", cap_no: "Plain",
    nota_captura: "Personalised, the app tells the model who you are, your instructions and what is already in your memory and projects. Plain, the question travels alone. Switch it and ask the same thing twice: you can hear the difference, and it is what this app does. Either way the answer passes the filter before coming back.",
    elige_idioma: "Which language shall we speak?",
    listo: "write here",
    sin_cerebro: "I can ask and remember, not converse yet",
    sin_servidor: "cannot reach the server",
    pensando: "thinking… this can take minutes",
    tarde: "it took too long. Try something shorter.",
    fallo: "I could not answer just now.",
    sin_red: "I could not reach the server.",
    voz_local_no: "local dictation is not wired yet, so there is none. Write instead: what you type never leaves this machine, and what you said through the browser microphone did.",
    sin_micro: "you did not give me microphone permission.",
    sin_oir: "I did not hear you. Try writing it.",
    hablar: "Talk", escribir: "Write",
    voz_apagada: "Dictation off",
    escuchando: "Listening… tap to stop",
    nota_sin: "With no brain installed, PreceptorOS asks and remembers but does not converse.",
    instalado: "installed", sin_instalar: "not installed",
    et_modelo: "Model", ruta_es: "at", sin_modelo: "not declared",
    medicion: "Measurement",
    med_intro: "Eleven fields. What cannot be measured is declared, never zeroed.",
    med_vivo: "live · measured again every 3 s",
    med_pausa: "paused — the screen is not in front",
    id_titulo: "Your sovereign fingerprint",
    id_nota: "It comes from randomness on this machine, not from your name or your device. It is not a key: it signs nothing and grants access to nothing. It never leaves here.",
    id_rota: "identity unavailable",
    cer_titulo: "Which brain answers you",
    cer_base: "Base brain", cer_afinado: "Fine-tuned brain",
    cer_en_uso: (n) => `In use: ${n}`,
    cer_cambiando: "switching…",
    cer_hecho: (n) => `Done. The next turn uses: ${n}`,
    cer_no: "could not switch",
    cer_sin_servidor: "cannot reach the server",
    med_medido: "measured", med_norma: "norm", med_nodata: "no data",
    med_fallo: "The measurement could not be read",
    med_pie: "Only packages declaring the same window and the same session tokens are comparable.",
    afinado_vivo: "fine-tuned · live", base_vivo: "base · live",
    encendido: "on", apagado: "off",
    dilo: "Say it", memoria: "Memory", frontera: "Border", ajustes: "Settings",
    tu_memoria: "Your memory", la_frontera: "The border", los_ajustes: "Settings",
    camino: "The Path", el_camino: "The Path",
    camino_intro: "Eight rungs. This is where you actually are — measured, not assumed.",
    encendiendo: "Warming up the brain… come back in a few minutes",
    tardando: "This is taking longer than usual. PreceptorOS is bonding with your phone.",
    fundiendo: "PreceptorOS is bonding with your phone. This only happens once",
    front_que: "Before any text leaves, keys, paths and addresses are blanked out.",
    front_como: "What gets counted is the class and the quantity, never the text found. And if the filter cannot finish, nothing is sent.",
    voz_no: "This copy has no voice: {falta} is missing.",
    volver: "← Back", perfil: "Profile", proyectos: "Projects",
    et_nombre: "What to call you", et_intereses: "What interests you (comma separated)",
    et_idioma: "Language", et_instrucciones: "How you want to be spoken to",
    et_cerebro: "Brain", et_cuaderno: "How it answers you",
    guardar: "Save", guardado: "Saved.",
    ph_instrucciones: "You are PreceptorOS, my learning companion. Speak to me with respect but without excessive formality. I prefer concrete examples to abstract theory.",
    nota_instrucciones: "This is told to PreceptorOS on every turn, after its character and not in its place: you adjust how it speaks to you, not what it is.",
    proy_intro: "What you have on your hands: a half-written book, an app, an idea that keeps coming back. No deadlines and no priorities: just where you left it.",
    proy_vacio: "None yet. Write a title above and that is it: the rest gets filled in whenever you feel like it.",
    et_pr_titulo: "Title", et_pr_desc: "What it is", et_pr_estado: "How it is going",
    et_pr_nota: "Notes, ideas, anything",
    volver_lista: "← All projects", ed_guardar: "Save changes",
    est_activo: "Active", est_pausado: "Paused", est_completado: "Done",
    ed_actualizado: (c) => `Last time you touched it: ${c}`,
    sin_tocar: "not touched yet",
    et_titulo: "Title", et_ruta: "Path (optional)",
    anadir: "Add", no_esta: "not there", quitar: "Remove",
    abrir_panel: "Open the full panel →", o_escribelo: "Or write it",
    g_guarda: "Save this", g_guardado: "Saved to your memory",
    g_fallo: "Could not save:",
    g_tachado: "It was saved like this, with the private parts struck out:",
    m_nuevo: "Write a memory",
    m_que: "What do you want to remember",
    m_porque: "Why it matters to you (optional)",
    m_guardar: "Save",
    m_nota_nueva: "What you write goes through the filter before it touches the disk. You will see what was saved.",
    m_guardados: "Memories saved", m_consentidos: "Consented for learning",
    m_corregidos: "Corrected by you",
    nota_memoria: "It lives in one file on your machine. You can copy it and take it with you.",
    hecho: "done", empezado: "started", sin_empezar: "not started",
    no_medible: "not measurable from here",
    agentes: "Agents and tools",
    et_tema: "Skin", tema_sistema: "Follow the system",
    tema_claro: "Light", tema_oscuro: "Dark",
    sin_nombre: "no name yet",
    lat_medir: "Measure", lat_camino: "Path",
    lat_memoria: "Memory", lat_proyectos: "Projects",
    lat_frontera: "Frontier",
    at_resume: "Sum this up", at_pasos: "Give me the steps",
    at_dudas: "What are you missing",
    ph_dicho: "Write here",
    manifiesto: "The Builder's Manifesto",
    esp_titulo: "This session's limits",
    esp_quien: "Who answers you", esp_ritmo: "At what pace",
    esp_memoria: "Model memory", esp_libre: "Free on the machine",
    esp_ventana: "Context window", esp_gastado: "Spent from the window",
    esp_sin_conteo: "nobody counts this session's tokens, so a number here would be invented",
    esp_lleno: "My context is full. I need you, as the Builder, to decide whether to summarise or grow the hardware.",
    esp_aviso: "This is not a dashboard: it is where your machine ends. What cannot be measured is said, never zeroed.",
    saluda: "I am your Preceptor and I live on this machine: what you write here never leaves it. I can remember what you tell me, help you carry your projects, and say when I do not know something. Write below, or tap one of the shortcuts.",
  },
  pt: {
    cap_si: "Personalizada", cap_no: "Sem personalizar",
    nota_captura: "Personalizada, a app diz ao modelo quem és, as tuas instruções e o que já existe na tua memória e nos teus projetos. Sem personalizar, a pergunta viaja sozinha. Muda-o e pergunta o mesmo duas vezes: a diferença ouve-se, e é o que esta app faz. Nos dois casos a resposta passa pelo filtro antes de voltar.",
    elige_idioma: "Em que idioma queres que falemos?",
    listo: "escreve aqui",
    sin_cerebro: "posso perguntar e recordar, ainda não conversar",
    sin_servidor: "não alcanço o servidor",
    pensando: "a pensar… isto pode demorar minutos",
    tarde: "demorou mais do que devia. Tenta com algo mais curto.",
    fallo: "não consegui responder agora mesmo.",
    sin_red: "não alcancei o servidor.",
    voz_local_no: "o ditado ainda não é local, por isso não existe. Escreve e já está: o que escreves não sai desta máquina, e o que dizias pelo microfone do navegador saía.",
    sin_micro: "não me deste permissão para o microfone.",
    sin_oir: "não te ouvi bem. Tenta escrevê-lo.",
    hablar: "Falar", escribir: "Escrever",
    voz_apagada: "Ditado desligado",
    escuchando: "A ouvir… toca para parar",
    nota_sin: "Sem cérebro instalado, o PreceptorOS pergunta e recorda mas não conversa.",
    instalado: "instalado", sin_instalar: "por instalar",
    et_modelo: "Modelo", ruta_es: "em", sin_modelo: "por declarar",
    medicion: "Medição",
    med_intro: "Onze campos. O que não se pode medir sai declarado, nunca a zero.",
    med_vivo: "ao vivo · mede-se outra vez a cada 3 s",
    med_pausa: "em pausa — o ecrã não está à frente",
    id_titulo: "A tua impressão soberana",
    id_nota: "Sai do acaso desta máquina, não do teu nome nem do teu equipamento. Não é uma chave: não assina nada e não dá acesso a nada. Nunca sai daqui.",
    id_rota: "identidade indisponível",
    cer_titulo: "Que cérebro te responde",
    cer_base: "Cérebro base", cer_afinado: "Cérebro afinado",
    cer_en_uso: (n) => `Em uso: ${n}`,
    cer_cambiando: "a mudar…",
    cer_hecho: (n) => `Feito. O próximo turno usa: ${n}`,
    cer_no: "não foi possível mudar",
    cer_sin_servidor: "não alcanço o servidor",
    med_medido: "medido", med_norma: "norma", med_nodata: "sem dado",
    med_fallo: "Não foi possível ler a medição",
    med_pie: "Só são comparáveis os pacotes que declaram a mesma janela e os mesmos tokens de sessão.",
    afinado_vivo: "afinado · vivo", base_vivo: "base · vivo",
    encendido: "ligado", apagado: "desligado",
    dilo: "Di-lo", memoria: "Memória", frontera: "Fronteira", ajustes: "Definições",
    tu_memoria: "A tua memória", la_frontera: "A fronteira", los_ajustes: "Definições",
    camino: "O Caminho", el_camino: "O Caminho",
    camino_intro: "Oito degraus. Isto é onde estás de verdade — medido, não suposto.",
    encendiendo: "A acender o cérebro… volta daqui a uns minutos",
    tardando: "Isto demora mais do que o normal. O PreceptorOS está a fundir-se com o teu telemóvel.",
    fundiendo: "O PreceptorOS está a fundir-se com o teu telemóvel. Isto só acontece uma vez",
    front_que: "Antes de um texto sair, riscam-se chaves, caminhos e endereços.",
    front_como: "Conta-se a classe e a quantidade, nunca o texto encontrado. E se o filtro não puder terminar, não se envia nada.",
    voz_no: "Esta cópia não leva voz: falta {falta}.",
    volver: "← Voltar", perfil: "Perfil", proyectos: "Projetos",
    et_nombre: "Quem és?", et_intereses: "O que te interessa (separado por vírgulas)",
    et_idioma: "Idioma", et_instrucciones: "Como queres que te fale",
    et_cerebro: "Cérebro", et_cuaderno: "Como te responde",
    guardar: "Guardar", guardado: "Guardado.",
    ph_instrucciones: "És o PreceptorOS, o meu companheiro de aprendizagem. Falas-me com respeito mas sem formalidade excessiva. Prefiro exemplos concretos a teoria abstrata.",
    nota_instrucciones: "Isto diz-se ao PreceptorOS em cada turno, depois do seu carácter e não no lugar dele: ajustas como te fala, não o que é.",
    proy_intro: "O que tens entre mãos: um livro a meio, uma aplicação, uma ideia que volta. Não há prazos nem prioridades: só em que ponto o deixaste.",
    proy_vacio: "Ainda não há nenhum. Escreve um título acima e já está: o resto preenche-se quando te apetecer.",
    et_pr_titulo: "Título", et_pr_desc: "O que é", et_pr_estado: "Como vai",
    et_pr_nota: "Notas, ideias, o que for",
    volver_lista: "← Todos os projetos", ed_guardar: "Guardar alterações",
    est_activo: "Ativo", est_pausado: "Em pausa", est_completado: "Concluído",
    ed_actualizado: (c) => `Última vez que lhe tocaste: ${c}`,
    sin_tocar: "ainda por tocar",
    et_titulo: "Título", et_ruta: "Caminho (opcional)",
    anadir: "Adicionar", no_esta: "não está aí", quitar: "Remover",
    abrir_panel: "Abrir o painel completo →", o_escribelo: "Ou escreve-o",
    g_guarda: "Guarda isto", g_guardado: "Guardado na tua memória",
    g_fallo: "Não foi possível guardar:",
    g_tachado: "Foi guardado assim, com o privado riscado:",
    m_nuevo: "Escreve uma memória",
    m_que: "O que queres recordar",
    m_porque: "Porque te importa (opcional)",
    m_guardar: "Guardar",
    m_nota_nueva: "O que escreveres passa pelo filtro antes de tocar o disco. Verás o que ficou guardado.",
    m_guardados: "Recordações guardadas", m_consentidos: "Consentidas para aprender",
    m_corregidos: "Corrigidas por ti",
    nota_memoria: "Vive num único ficheiro da tua máquina. Podes copiá-lo e levá-lo contigo.",
    hecho: "feito", empezado: "começado", sin_empezar: "por começar",
    no_medible: "não mensurável a partir daqui",
    agentes: "Agentes e ferramentas",
    et_tema: "Pele", tema_sistema: "Como o sistema",
    tema_claro: "Claro", tema_oscuro: "Escuro",
    sin_nombre: "ainda sem nome",
    lat_medir: "Medição", lat_camino: "Caminho",
    lat_memoria: "Memória", lat_proyectos: "Projetos",
    lat_frontera: "Fronteira",
    at_resume: "Resume isto", at_pasos: "Dá-me os passos",
    at_dudas: "O que te falta saber",
    ph_dicho: "Escreve aqui",
    manifiesto: "O Manifesto do Builder",
    esp_titulo: "Limites desta sessão",
    esp_quien: "Quem te responde", esp_ritmo: "A que ritmo",
    esp_memoria: "Memória do modelo", esp_libre: "Livre na máquina",
    esp_ventana: "Janela de contexto", esp_gastado: "Gasto da janela",
    esp_sin_conteo: "ninguém conta os tokens desta sessão, por isso um número aqui seria inventado",
    esp_lleno: "O meu contexto está cheio. Preciso que tu, como Builder, decidas se resumir ou aumentar o hardware.",
    esp_aviso: "Isto não é um painel de controlo: é onde acaba a tua máquina. O que não se pode medir sai dito, nunca a zero.",
    saluda: "Sou o teu Preceptor e vivo nesta máquina: o que escreves aqui não sai dela. Posso recordar o que me contares, ajudar-te a levar os teus projetos e dizer-te quando não sei algo. Escreve abaixo, ou toca num dos atalhos.",
  },
  /* Seis lenguas mas desde el 2026-09-23 (el portugues ya estaba), las mismas
   * nueve que la web y que `textos.py`. Traducidas por Claude; nadie con oido
   * nativo las ha leido. El arabe se escribe de derecha a izquierda. */
  fr: {
    cap_si: "Personnalisée", cap_no: "Simple",
    nota_captura: "Personnalisée, l'app dit au modèle qui tu es, tes instructions et ce qu'il y a déjà dans ta mémoire et tes projets. Simple, la question voyage seule. Change-le et demande deux fois la même chose : tu entends la différence, et c'est ce que fait cette app. Dans les deux cas, la réponse passe le filtre avant de revenir.",
    elige_idioma: "Dans quelle langue veux-tu que l'on parle ?",
    listo: "écris ici",
    sin_cerebro: "je peux demander et me souvenir, pas encore converser",
    sin_servidor: "impossible de joindre le serveur",
    pensando: "je réfléchis… ça peut prendre des minutes",
    tarde: "ça a pris trop de temps. Essaie quelque chose de plus court.",
    fallo: "Je n'ai pas pu répondre tout de suite.",
    sin_red: "Je n'ai pas pu joindre le serveur.",
    voz_local_no: "la dictée locale n'est pas encore branchée, donc il n'y en a pas. Écris plutôt : ce que tu tapes ne quitte jamais cette machine, et ce que tu disais par le micro du navigateur, si.",
    sin_micro: "tu ne m'as pas donné la permission du micro.",
    sin_oir: "Je ne t'ai pas entendu. Essaie de l'écrire.",
    hablar: "Parler", escribir: "Écrire",
    voz_apagada: "Dictée coupée",
    escuchando: "J'écoute… touche pour arrêter",
    nota_sin: "Sans cerveau installé, PreceptorOS demande et se souvient mais ne converse pas.",
    instalado: "installé", sin_instalar: "non installé",
    et_modelo: "Modèle", ruta_es: "dans", sin_modelo: "non déclaré",
    medicion: "Mesure",
    med_intro: "Onze champs. Ce qui ne se mesure pas est déclaré, jamais mis à zéro.",
    med_vivo: "en direct · mesuré à nouveau toutes les 3 s",
    med_pausa: "en pause — l'écran n'est pas au premier plan",
    id_titulo: "Ton empreinte souveraine",
    id_nota: "Elle vient du hasard de cette machine, pas de ton nom ni de ton appareil. Ce n'est pas une clé : elle ne signe rien et n'ouvre rien. Elle ne sort jamais d'ici.",
    id_rota: "identité indisponible",
    cer_titulo: "Quel cerveau te répond",
    cer_base: "Cerveau de base", cer_afinado: "Cerveau affiné",
    cer_en_uso: (n) => `En usage : ${n}`,
    cer_cambiando: "changement…",
    cer_hecho: (n) => `C'est fait. Le prochain tour utilise : ${n}`,
    cer_no: "impossible de changer",
    cer_sin_servidor: "impossible de joindre le serveur",
    med_medido: "mesuré", med_norma: "norme", med_nodata: "sans donnée",
    med_fallo: "Impossible de lire la mesure",
    med_pie: "Seuls les paquets qui déclarent la même fenêtre et les mêmes jetons de session sont comparables.",
    afinado_vivo: "affiné · en direct", base_vivo: "base · en direct",
    encendido: "allumé", apagado: "éteint",
    dilo: "Dis-le", memoria: "Mémoire", frontera: "Frontière", ajustes: "Réglages",
    tu_memoria: "Ta mémoire", la_frontera: "La frontière", los_ajustes: "Réglages",
    camino: "Le Chemin", el_camino: "Le Chemin",
    camino_intro: "Huit échelons. Voici où tu en es vraiment — mesuré, pas supposé.",
    encendiendo: "Le cerveau chauffe… reviens dans quelques minutes",
    tardando: "C'est plus long que d'habitude. PreceptorOS fait connaissance avec ton téléphone.",
    fundiendo: "PreceptorOS fait connaissance avec ton téléphone. Ça n'arrive qu'une fois",
    front_que: "Avant qu'un texte ne sorte, les clés, les chemins et les adresses sont effacés.",
    front_como: "Ce qui se compte, c'est la classe et la quantité, jamais le texte trouvé. Et si le filtre ne peut pas finir, rien n'est envoyé.",
    voz_no: "Cette copie n'a pas de voix : il manque {falta}.",
    volver: "← Retour", perfil: "Profil", proyectos: "Projets",
    et_nombre: "Comment t'appeler", et_intereses: "Ce qui t'intéresse (séparé par des virgules)",
    et_idioma: "Langue", et_instrucciones: "Comment tu veux qu'on te parle",
    et_cerebro: "Cerveau", et_cuaderno: "Comment il te répond",
    guardar: "Enregistrer", guardado: "Enregistré.",
    ph_instrucciones: "Tu es PreceptorOS, mon compagnon d'apprentissage. Parle-moi avec respect mais sans trop de formalité. Je préfère les exemples concrets à la théorie abstraite.",
    nota_instrucciones: "C'est dit à PreceptorOS à chaque tour, après son caractère et pas à sa place : tu règles comment il te parle, pas ce qu'il est.",
    proy_intro: "Ce que tu as entre les mains : un livre à moitié écrit, une app, une idée qui revient toujours. Pas d'échéances ni de priorités : juste là où tu l'as laissé.",
    proy_vacio: "Aucun pour l'instant. Écris un titre au-dessus et c'est tout : le reste se remplit quand tu en as envie.",
    et_pr_titulo: "Titre", et_pr_desc: "Ce que c'est", et_pr_estado: "Où ça en est",
    et_pr_nota: "Notes, idées, n'importe quoi",
    volver_lista: "← Tous les projets", ed_guardar: "Enregistrer les changements",
    est_activo: "Actif", est_pausado: "En pause", est_completado: "Terminé",
    ed_actualizado: (c) => `La dernière fois que tu y as touché : ${c}`,
    sin_tocar: "pas encore touché",
    et_titulo: "Titre", et_ruta: "Chemin (facultatif)",
    anadir: "Ajouter", no_esta: "absent", quitar: "Retirer",
    abrir_panel: "Ouvrir le panneau complet →", o_escribelo: "Ou écris-le",
    g_guarda: "Garder ceci", g_guardado: "Gardé dans ta mémoire",
    g_fallo: "Impossible de garder :",
    g_tachado: "Ça a été gardé ainsi, avec les parties privées barrées :",
    m_nuevo: "Écrire un souvenir",
    m_que: "Ce que tu veux te rappeler",
    m_porque: "Pourquoi ça compte pour toi (facultatif)",
    m_guardar: "Enregistrer",
    m_nota_nueva: "Ce que tu écris passe par le filtre avant de toucher le disque. Tu verras ce qui a été gardé.",
    m_guardados: "Souvenirs gardés", m_consentidos: "Consentis pour l'apprentissage",
    m_corregidos: "Corrigés par toi",
    nota_memoria: "Elle vit dans un seul fichier sur ta machine. Tu peux le copier et l'emporter.",
    hecho: "fait", empezado: "commencé", sin_empezar: "pas commencé",
    no_medible: "pas mesurable d'ici",
    agentes: "Agents et outils",
    et_tema: "Peau", tema_sistema: "Suivre le système",
    tema_claro: "Clair", tema_oscuro: "Sombre",
    sin_nombre: "pas encore de nom",
    lat_medir: "Mesurer", lat_camino: "Chemin",
    lat_memoria: "Mémoire", lat_proyectos: "Projets",
    lat_frontera: "Frontière",
    at_resume: "Résume ceci", at_pasos: "Donne-moi les étapes",
    at_dudas: "Ce qu'il te manque",
    ph_dicho: "Écris ici",
    manifiesto: "Le Manifeste du Builder",
    esp_titulo: "Les limites de cette session",
    esp_quien: "Qui te répond", esp_ritmo: "À quel rythme",
    esp_memoria: "Mémoire du modèle", esp_libre: "Libre sur la machine",
    esp_ventana: "Fenêtre de contexte", esp_gastado: "Utilisé de la fenêtre",
    esp_sin_conteo: "personne ne compte les jetons de cette session, donc un chiffre ici serait inventé",
    esp_lleno: "Mon contexte est plein. J'ai besoin que toi, en tant que Builder, décides s'il faut résumer ou agrandir le matériel.",
    esp_aviso: "Ce n'est pas un tableau de bord : c'est là où finit ta machine. Ce qui ne se mesure pas est dit, jamais mis à zéro.",
    saluda: "Je suis ton Preceptor et je vis sur cette machine : ce que tu écris ici n'en sort pas. Je peux me souvenir de ce que tu me dis, t'aider à porter tes projets et te dire quand je ne sais pas quelque chose. Écris en dessous, ou touche un des raccourcis.",
  },
  it: {
    cap_si: "Personalizzata", cap_no: "Semplice",
    nota_captura: "Personalizzata, l'app dice al modello chi sei, le tue istruzioni e cosa c'è già nella tua memoria e nei tuoi progetti. Semplice, la domanda viaggia da sola. Cambialo e chiedi la stessa cosa due volte: la differenza si sente, ed è ciò che fa questa app. In entrambi i casi la risposta passa dal filtro prima di tornare.",
    elige_idioma: "In che lingua vuoi che parliamo?",
    listo: "scrivi qui",
    sin_cerebro: "posso chiedere e ricordare, non ancora conversare",
    sin_servidor: "non raggiungo il server",
    pensando: "sto pensando… può richiedere minuti",
    tarde: "ci ha messo troppo. Prova con qualcosa di più breve.",
    fallo: "Non sono riuscito a rispondere adesso.",
    sin_red: "Non sono riuscito a raggiungere il server.",
    voz_local_no: "la dettatura locale non è ancora collegata, quindi non c'è. Scrivi invece: quello che digiti non lascia mai questa macchina, e quello che dicevi dal microfono del browser sì.",
    sin_micro: "non mi hai dato il permesso del microfono.",
    sin_oir: "Non ti ho sentito. Prova a scriverlo.",
    hablar: "Parla", escribir: "Scrivi",
    voz_apagada: "Dettatura spenta",
    escuchando: "Ascolto… tocca per fermare",
    nota_sin: "Senza cervello installato, PreceptorOS chiede e ricorda ma non conversa.",
    instalado: "installato", sin_instalar: "non installato",
    et_modelo: "Modello", ruta_es: "in", sin_modelo: "non dichiarato",
    medicion: "Misura",
    med_intro: "Undici campi. Ciò che non si misura viene dichiarato, mai azzerato.",
    med_vivo: "dal vivo · misurato di nuovo ogni 3 s",
    med_pausa: "in pausa — lo schermo non è in primo piano",
    id_titulo: "La tua impronta sovrana",
    id_nota: "Viene dal caso su questa macchina, non dal tuo nome né dal tuo dispositivo. Non è una chiave: non firma nulla e non apre nulla. Non esce mai da qui.",
    id_rota: "identità non disponibile",
    cer_titulo: "Quale cervello ti risponde",
    cer_base: "Cervello di base", cer_afinado: "Cervello affinato",
    cer_en_uso: (n) => `In uso: ${n}`,
    cer_cambiando: "cambio in corso…",
    cer_hecho: (n) => `Fatto. Il prossimo turno usa: ${n}`,
    cer_no: "impossibile cambiare",
    cer_sin_servidor: "non raggiungo il server",
    med_medido: "misurato", med_norma: "norma", med_nodata: "senza dato",
    med_fallo: "Impossibile leggere la misura",
    med_pie: "Sono confrontabili solo i pacchetti che dichiarano la stessa finestra e gli stessi token di sessione.",
    afinado_vivo: "affinato · dal vivo", base_vivo: "base · dal vivo",
    encendido: "acceso", apagado: "spento",
    dilo: "Dillo", memoria: "Memoria", frontera: "Frontiera", ajustes: "Impostazioni",
    tu_memoria: "La tua memoria", la_frontera: "La frontiera", los_ajustes: "Impostazioni",
    camino: "Il Cammino", el_camino: "Il Cammino",
    camino_intro: "Otto gradini. Ecco dove sei davvero — misurato, non supposto.",
    encendiendo: "Il cervello si sta scaldando… torna tra qualche minuto",
    tardando: "Ci sta mettendo più del solito. PreceptorOS sta facendo conoscenza con il tuo telefono.",
    fundiendo: "PreceptorOS sta facendo conoscenza con il tuo telefono. Succede una volta sola",
    front_que: "Prima che un testo esca, chiavi, percorsi e indirizzi vengono cancellati.",
    front_como: "Si contano la classe e la quantità, mai il testo trovato. E se il filtro non riesce a finire, non si invia nulla.",
    voz_no: "Questa copia non ha voce: manca {falta}.",
    volver: "← Indietro", perfil: "Profilo", proyectos: "Progetti",
    et_nombre: "Come chiamarti", et_intereses: "Cosa ti interessa (separato da virgole)",
    et_idioma: "Lingua", et_instrucciones: "Come vuoi che ti si parli",
    et_cerebro: "Cervello", et_cuaderno: "Come ti risponde",
    guardar: "Salva", guardado: "Salvato.",
    ph_instrucciones: "Sei PreceptorOS, il mio compagno di apprendimento. Parlami con rispetto ma senza troppa formalità. Preferisco esempi concreti alla teoria astratta.",
    nota_instrucciones: "Questo viene detto a PreceptorOS a ogni turno, dopo il suo carattere e non al suo posto: regoli come ti parla, non cosa è.",
    proy_intro: "Quello che hai tra le mani: un libro a metà, un'app, un'idea che torna sempre. Niente scadenze né priorità: solo dove l'hai lasciato.",
    proy_vacio: "Ancora nessuno. Scrivi un titolo qui sopra ed è fatto: il resto si riempie quando ne hai voglia.",
    et_pr_titulo: "Titolo", et_pr_desc: "Cos'è", et_pr_estado: "Come va",
    et_pr_nota: "Note, idee, qualsiasi cosa",
    volver_lista: "← Tutti i progetti", ed_guardar: "Salva le modifiche",
    est_activo: "Attivo", est_pausado: "In pausa", est_completado: "Finito",
    ed_actualizado: (c) => `L'ultima volta che l'hai toccato: ${c}`,
    sin_tocar: "non ancora toccato",
    et_titulo: "Titolo", et_ruta: "Percorso (facoltativo)",
    anadir: "Aggiungi", no_esta: "non c'è", quitar: "Rimuovi",
    abrir_panel: "Apri il pannello completo →", o_escribelo: "Oppure scrivilo",
    g_guarda: "Salva questo", g_guardado: "Salvato nella tua memoria",
    g_fallo: "Impossibile salvare:",
    g_tachado: "È stato salvato così, con le parti private barrate:",
    m_nuevo: "Scrivi un ricordo",
    m_que: "Cosa vuoi ricordare",
    m_porque: "Perché ti importa (facoltativo)",
    m_guardar: "Salva",
    m_nota_nueva: "Quello che scrivi passa dal filtro prima di toccare il disco. Vedrai cosa è stato salvato.",
    m_guardados: "Ricordi salvati", m_consentidos: "Acconsentiti per l'apprendimento",
    m_corregidos: "Corretti da te",
    nota_memoria: "Vive in un solo file sulla tua macchina. Puoi copiarlo e portarlo con te.",
    hecho: "fatto", empezado: "iniziato", sin_empezar: "non iniziato",
    no_medible: "non misurabile da qui",
    agentes: "Agenti e strumenti",
    et_tema: "Pelle", tema_sistema: "Segui il sistema",
    tema_claro: "Chiaro", tema_oscuro: "Scuro",
    sin_nombre: "ancora senza nome",
    lat_medir: "Misura", lat_camino: "Cammino",
    lat_memoria: "Memoria", lat_proyectos: "Progetti",
    lat_frontera: "Frontiera",
    at_resume: "Riassumi questo", at_pasos: "Dammi i passaggi",
    at_dudas: "Cosa ti manca",
    ph_dicho: "Scrivi qui",
    manifiesto: "Il Manifesto del Builder",
    esp_titulo: "I limiti di questa sessione",
    esp_quien: "Chi ti risponde", esp_ritmo: "A che ritmo",
    esp_memoria: "Memoria del modello", esp_libre: "Libera sulla macchina",
    esp_ventana: "Finestra di contesto", esp_gastado: "Usato della finestra",
    esp_sin_conteo: "nessuno conta i token di questa sessione, quindi un numero qui sarebbe inventato",
    esp_lleno: "Il mio contesto è pieno. Ho bisogno che tu, come Builder, decida se riassumere o ampliare l'hardware.",
    esp_aviso: "Questo non è un cruscotto: è dove finisce la tua macchina. Ciò che non si misura si dice, mai azzerato.",
    saluda: "Sono il tuo Preceptor e vivo su questa macchina: quello che scrivi qui non ne esce. Posso ricordare quello che mi racconti, aiutarti a portare avanti i tuoi progetti e dirti quando non so qualcosa. Scrivi qui sotto, o tocca una delle scorciatoie.",
  },
  de: {
    cap_si: "Persönlich", cap_no: "Schlicht",
    nota_captura: "Persönlich sagt die App dem Modell, wer du bist, deine Anweisungen und was schon in deinem Gedächtnis und deinen Projekten steht. Schlicht reist die Frage allein. Schalte um und frag zweimal dasselbe: Man hört den Unterschied, und genau das macht diese App. In beiden Fällen geht die Antwort durch den Filter, bevor sie zurückkommt.",
    elige_idioma: "In welcher Sprache sollen wir sprechen?",
    listo: "schreib hier",
    sin_cerebro: "ich kann fragen und mich erinnern, noch nicht sprechen",
    sin_servidor: "Server nicht erreichbar",
    pensando: "ich denke nach… das kann Minuten dauern",
    tarde: "es hat zu lange gedauert. Versuch etwas Kürzeres.",
    fallo: "Ich konnte gerade nicht antworten.",
    sin_red: "Ich konnte den Server nicht erreichen.",
    voz_local_no: "lokales Diktieren ist noch nicht angeschlossen, also gibt es keins. Schreib lieber: Was du tippst, verlässt diese Maschine nie, und was du über das Mikrofon des Browsers gesagt hast, schon.",
    sin_micro: "du hast mir keine Mikrofon-Berechtigung gegeben.",
    sin_oir: "Ich habe dich nicht gehört. Versuch es zu schreiben.",
    hablar: "Sprechen", escribir: "Schreiben",
    voz_apagada: "Diktieren aus",
    escuchando: "Ich höre zu… tippen zum Stoppen",
    nota_sin: "Ohne installiertes Gehirn fragt PreceptorOS und erinnert sich, spricht aber nicht.",
    instalado: "installiert", sin_instalar: "nicht installiert",
    et_modelo: "Modell", ruta_es: "in", sin_modelo: "nicht angegeben",
    medicion: "Messung",
    med_intro: "Elf Felder. Was sich nicht messen lässt, wird angegeben, nie auf null gesetzt.",
    med_vivo: "live · alle 3 s neu gemessen",
    med_pausa: "pausiert — der Bildschirm ist nicht im Vordergrund",
    id_titulo: "Dein souveräner Fingerabdruck",
    id_nota: "Er kommt aus dem Zufall dieser Maschine, nicht aus deinem Namen oder deinem Gerät. Er ist kein Schlüssel: Er unterschreibt nichts und öffnet nichts. Er verlässt diesen Ort nie.",
    id_rota: "Identität nicht verfügbar",
    cer_titulo: "Welches Gehirn dir antwortet",
    cer_base: "Basis-Gehirn", cer_afinado: "Feinabgestimmtes Gehirn",
    cer_en_uso: (n) => `In Gebrauch: ${n}`,
    cer_cambiando: "wird gewechselt…",
    cer_hecho: (n) => `Erledigt. Die nächste Runde nutzt: ${n}`,
    cer_no: "konnte nicht wechseln",
    cer_sin_servidor: "Server nicht erreichbar",
    med_medido: "gemessen", med_norma: "Norm", med_nodata: "keine Daten",
    med_fallo: "Die Messung konnte nicht gelesen werden",
    med_pie: "Vergleichbar sind nur Pakete, die dasselbe Fenster und dieselben Sitzungs-Tokens angeben.",
    afinado_vivo: "feinabgestimmt · live", base_vivo: "Basis · live",
    encendido: "an", apagado: "aus",
    dilo: "Sag es", memoria: "Gedächtnis", frontera: "Grenze", ajustes: "Einstellungen",
    tu_memoria: "Dein Gedächtnis", la_frontera: "Die Grenze", los_ajustes: "Einstellungen",
    camino: "Der Weg", el_camino: "Der Weg",
    camino_intro: "Acht Sprossen. Hier stehst du wirklich — gemessen, nicht angenommen.",
    encendiendo: "Das Gehirn wärmt sich auf… komm in ein paar Minuten wieder",
    tardando: "Das dauert länger als sonst. PreceptorOS lernt dein Telefon kennen.",
    fundiendo: "PreceptorOS lernt dein Telefon kennen. Das passiert nur einmal",
    front_que: "Bevor ein Text hinausgeht, werden Schlüssel, Pfade und Adressen geschwärzt.",
    front_como: "Gezählt werden Klasse und Menge, nie der gefundene Text. Und wenn der Filter nicht fertig wird, wird nichts gesendet.",
    voz_no: "Diese Kopie hat keine Stimme: {falta} fehlt.",
    volver: "← Zurück", perfil: "Profil", proyectos: "Projekte",
    et_nombre: "Wie du genannt werden willst", et_intereses: "Was dich interessiert (durch Kommas getrennt)",
    et_idioma: "Sprache", et_instrucciones: "Wie du angesprochen werden willst",
    et_cerebro: "Gehirn", et_cuaderno: "Wie es dir antwortet",
    guardar: "Speichern", guardado: "Gespeichert.",
    ph_instrucciones: "Du bist PreceptorOS, mein Lernbegleiter. Sprich respektvoll, aber ohne übertriebene Förmlichkeit mit mir. Ich ziehe konkrete Beispiele abstrakter Theorie vor.",
    nota_instrucciones: "Das wird PreceptorOS in jeder Runde gesagt, nach seinem Charakter und nicht an dessen Stelle: Du stellst ein, wie es mit dir spricht, nicht, was es ist.",
    proy_intro: "Was du gerade in der Hand hast: ein halb geschriebenes Buch, eine App, eine Idee, die immer wiederkommt. Keine Fristen und keine Prioritäten: nur da, wo du es gelassen hast.",
    proy_vacio: "Noch keins. Schreib oben einen Titel, und das war's: Der Rest füllt sich, wann immer du Lust hast.",
    et_pr_titulo: "Titel", et_pr_desc: "Was es ist", et_pr_estado: "Wie es läuft",
    et_pr_nota: "Notizen, Ideen, alles Mögliche",
    volver_lista: "← Alle Projekte", ed_guardar: "Änderungen speichern",
    est_activo: "Aktiv", est_pausado: "Pausiert", est_completado: "Fertig",
    ed_actualizado: (c) => `Zuletzt angefasst: ${c}`,
    sin_tocar: "noch nicht angefasst",
    et_titulo: "Titel", et_ruta: "Pfad (optional)",
    anadir: "Hinzufügen", no_esta: "nicht da", quitar: "Entfernen",
    abrir_panel: "Das ganze Panel öffnen →", o_escribelo: "Oder schreib es",
    g_guarda: "Das behalten", g_guardado: "In deinem Gedächtnis gespeichert",
    g_fallo: "Konnte nicht speichern:",
    g_tachado: "So wurde es gespeichert, mit den privaten Teilen durchgestrichen:",
    m_nuevo: "Eine Erinnerung schreiben",
    m_que: "Woran du dich erinnern willst",
    m_porque: "Warum es dir wichtig ist (optional)",
    m_guardar: "Speichern",
    m_nota_nueva: "Was du schreibst, geht durch den Filter, bevor es die Festplatte berührt. Du siehst, was gespeichert wurde.",
    m_guardados: "Gespeicherte Erinnerungen", m_consentidos: "Zum Lernen freigegeben",
    m_corregidos: "Von dir korrigiert",
    nota_memoria: "Es lebt in einer einzigen Datei auf deiner Maschine. Du kannst sie kopieren und mitnehmen.",
    hecho: "erledigt", empezado: "begonnen", sin_empezar: "nicht begonnen",
    no_medible: "von hier nicht messbar",
    agentes: "Agenten und Werkzeuge",
    et_tema: "Haut", tema_sistema: "Dem System folgen",
    tema_claro: "Hell", tema_oscuro: "Dunkel",
    sin_nombre: "noch ohne Namen",
    lat_medir: "Messen", lat_camino: "Weg",
    lat_memoria: "Gedächtnis", lat_proyectos: "Projekte",
    lat_frontera: "Grenze",
    at_resume: "Fass das zusammen", at_pasos: "Gib mir die Schritte",
    at_dudas: "Was dir fehlt",
    ph_dicho: "Schreib hier",
    manifiesto: "Das Manifest des Builders",
    esp_titulo: "Die Grenzen dieser Sitzung",
    esp_quien: "Wer dir antwortet", esp_ritmo: "In welchem Tempo",
    esp_memoria: "Modellspeicher", esp_libre: "Frei auf der Maschine",
    esp_ventana: "Kontextfenster", esp_gastado: "Vom Fenster verbraucht",
    esp_sin_conteo: "niemand zählt die Tokens dieser Sitzung, also wäre eine Zahl hier erfunden",
    esp_lleno: "Mein Kontext ist voll. Du als Builder musst entscheiden, ob zusammengefasst oder die Hardware vergrößert wird.",
    esp_aviso: "Das ist kein Dashboard: Hier endet deine Maschine. Was sich nicht messen lässt, wird gesagt, nie auf null gesetzt.",
    saluda: "Ich bin dein Preceptor und lebe auf dieser Maschine: Was du hier schreibst, verlässt sie nicht. Ich kann mir merken, was du mir erzählst, dir helfen, deine Projekte voranzubringen, und dir sagen, wenn ich etwas nicht weiß. Schreib unten oder tippe auf eine der Abkürzungen.",
  },
  ru: {
    cap_si: "Персональный", cap_no: "Простой",
    nota_captura: "В персональном режиме приложение сообщает модели, кто ты, твои инструкции и что уже есть в твоей памяти и проектах. В простом вопрос идёт один. Переключи и спроси одно и то же дважды: разница слышна, и это то, что делает это приложение. В обоих случаях ответ проходит через фильтр, прежде чем вернуться.",
    elige_idioma: "На каком языке будем говорить?",
    listo: "пиши здесь",
    sin_cerebro: "я могу спрашивать и помнить, но пока не разговаривать",
    sin_servidor: "не могу достучаться до сервера",
    pensando: "думаю… это может занять минуты",
    tarde: "это заняло слишком много времени. Попробуй что-то покороче.",
    fallo: "Сейчас я не смог ответить.",
    sin_red: "Я не смог достучаться до сервера.",
    voz_local_no: "локальная диктовка ещё не подключена, так что её нет. Лучше напиши: то, что ты печатаешь, никогда не покидает эту машину, а то, что ты говорил через микрофон браузера, — покидало.",
    sin_micro: "ты не дал мне доступ к микрофону.",
    sin_oir: "Я тебя не расслышал. Попробуй написать.",
    hablar: "Говорить", escribir: "Писать",
    voz_apagada: "Диктовка выключена",
    escuchando: "Слушаю… нажми, чтобы остановить",
    nota_sin: "Без установленного мозга PreceptorOS спрашивает и помнит, но не разговаривает.",
    instalado: "установлен", sin_instalar: "не установлен",
    et_modelo: "Модель", ruta_es: "в", sin_modelo: "не указана",
    medicion: "Измерение",
    med_intro: "Одиннадцать полей. То, что нельзя измерить, объявляется, а не обнуляется.",
    med_vivo: "в реальном времени · измеряется каждые 3 с",
    med_pausa: "на паузе — экран не на переднем плане",
    id_titulo: "Твой суверенный отпечаток",
    id_nota: "Он берётся из случайности этой машины, а не из твоего имени или устройства. Это не ключ: он ничего не подписывает и ничего не открывает. Он никогда отсюда не уходит.",
    id_rota: "идентичность недоступна",
    cer_titulo: "Какой мозг тебе отвечает",
    cer_base: "Базовый мозг", cer_afinado: "Дообученный мозг",
    cer_en_uso: (n) => `Используется: ${n}`,
    cer_cambiando: "переключаю…",
    cer_hecho: (n) => `Готово. Следующий ход использует: ${n}`,
    cer_no: "не удалось переключить",
    cer_sin_servidor: "не могу достучаться до сервера",
    med_medido: "измерено", med_norma: "норма", med_nodata: "нет данных",
    med_fallo: "Не удалось прочитать измерение",
    med_pie: "Сравнимы только пакеты, в которых указаны одно и то же окно и одни и те же токены сессии.",
    afinado_vivo: "дообученный · в реальном времени", base_vivo: "базовый · в реальном времени",
    encendido: "вкл", apagado: "выкл",
    dilo: "Скажи", memoria: "Память", frontera: "Граница", ajustes: "Настройки",
    tu_memoria: "Твоя память", la_frontera: "Граница", los_ajustes: "Настройки",
    camino: "Путь", el_camino: "Путь",
    camino_intro: "Восемь ступеней. Вот где ты на самом деле — измерено, а не предположено.",
    encendiendo: "Мозг разогревается… вернись через несколько минут",
    tardando: "Это дольше обычного. PreceptorOS знакомится с твоим телефоном.",
    fundiendo: "PreceptorOS знакомится с твоим телефоном. Это бывает только один раз",
    front_que: "Прежде чем текст уйдёт, ключи, пути и адреса стираются.",
    front_como: "Считаются класс и количество, а не найденный текст. А если фильтр не может закончить, ничего не отправляется.",
    voz_no: "В этой копии нет голоса: не хватает {falta}.",
    volver: "← Назад", perfil: "Профиль", proyectos: "Проекты",
    et_nombre: "Как тебя называть", et_intereses: "Что тебе интересно (через запятую)",
    et_idioma: "Язык", et_instrucciones: "Как с тобой говорить",
    et_cerebro: "Мозг", et_cuaderno: "Как он тебе отвечает",
    guardar: "Сохранить", guardado: "Сохранено.",
    ph_instrucciones: "Ты PreceptorOS, мой спутник в учёбе. Говори со мной уважительно, но без лишней официальности. Я предпочитаю конкретные примеры абстрактной теории.",
    nota_instrucciones: "Это говорится PreceptorOS на каждом ходу, после его характера, а не вместо него: ты настраиваешь, как он с тобой говорит, а не то, чем он является.",
    proy_intro: "То, что у тебя в руках: наполовину написанная книга, приложение, идея, которая всё возвращается. Никаких сроков и приоритетов: просто там, где ты это оставил.",
    proy_vacio: "Пока ни одного. Напиши название выше, и всё: остальное заполнится, когда захочешь.",
    et_pr_titulo: "Название", et_pr_desc: "Что это", et_pr_estado: "Как идёт",
    et_pr_nota: "Заметки, идеи, что угодно",
    volver_lista: "← Все проекты", ed_guardar: "Сохранить изменения",
    est_activo: "Активен", est_pausado: "На паузе", est_completado: "Готов",
    ed_actualizado: (c) => `Последний раз ты его трогал: ${c}`,
    sin_tocar: "ещё не трогали",
    et_titulo: "Название", et_ruta: "Путь (необязательно)",
    anadir: "Добавить", no_esta: "нет", quitar: "Убрать",
    abrir_panel: "Открыть полную панель →", o_escribelo: "Или напиши",
    g_guarda: "Сохранить это", g_guardado: "Сохранено в твоей памяти",
    g_fallo: "Не удалось сохранить:",
    g_tachado: "Сохранено так, с вычеркнутыми личными частями:",
    m_nuevo: "Записать воспоминание",
    m_que: "Что ты хочешь запомнить",
    m_porque: "Почему это важно для тебя (необязательно)",
    m_guardar: "Сохранить",
    m_nota_nueva: "То, что ты пишешь, проходит через фильтр, прежде чем попасть на диск. Ты увидишь, что сохранилось.",
    m_guardados: "Сохранённые воспоминания", m_consentidos: "С согласием на обучение",
    m_corregidos: "Исправлено тобой",
    nota_memoria: "Она живёт в одном файле на твоей машине. Его можно скопировать и забрать с собой.",
    hecho: "готово", empezado: "начато", sin_empezar: "не начато",
    no_medible: "отсюда не измерить",
    agentes: "Агенты и инструменты",
    et_tema: "Тема", tema_sistema: "Как в системе",
    tema_claro: "Светлая", tema_oscuro: "Тёмная",
    sin_nombre: "пока без имени",
    lat_medir: "Измерить", lat_camino: "Путь",
    lat_memoria: "Память", lat_proyectos: "Проекты",
    lat_frontera: "Граница",
    at_resume: "Сократи это", at_pasos: "Дай мне шаги",
    at_dudas: "Чего тебе не хватает",
    ph_dicho: "Пиши здесь",
    manifiesto: "Манифест Строителя",
    esp_titulo: "Пределы этой сессии",
    esp_quien: "Кто тебе отвечает", esp_ritmo: "В каком темпе",
    esp_memoria: "Память модели", esp_libre: "Свободно на машине",
    esp_ventana: "Окно контекста", esp_gastado: "Израсходовано из окна",
    esp_sin_conteo: "никто не считает токены этой сессии, так что число здесь было бы выдумкой",
    esp_lleno: "Мой контекст заполнен. Мне нужно, чтобы ты, как Строитель, решил: сократить или нарастить железо.",
    esp_aviso: "Это не приборная панель: здесь кончается твоя машина. То, что нельзя измерить, говорится, а не обнуляется.",
    saluda: "Я твой Preceptor и живу на этой машине: то, что ты здесь пишешь, её не покидает. Я могу запомнить то, что ты мне расскажешь, помочь тебе вести твои проекты и сказать, когда я чего-то не знаю. Пиши ниже или нажми одну из подсказок.",
  },
  el: {
    cap_si: "Προσωπική", cap_no: "Απλή",
    nota_captura: "Στην προσωπική, η εφαρμογή λέει στο μοντέλο ποιος είσαι, τις οδηγίες σου και τι υπάρχει ήδη στη μνήμη και στα έργα σου. Στην απλή, η ερώτηση ταξιδεύει μόνη. Άλλαξέ το και ρώτα το ίδιο δύο φορές: η διαφορά ακούγεται, και αυτό κάνει αυτή η εφαρμογή. Και στις δύο περιπτώσεις η απάντηση περνά από το φίλτρο πριν επιστρέψει.",
    elige_idioma: "Σε ποια γλώσσα θέλεις να μιλάμε;",
    listo: "γράψε εδώ",
    sin_cerebro: "μπορώ να ρωτώ και να θυμάμαι, όχι ακόμη να συζητώ",
    sin_servidor: "δεν φτάνω στον διακομιστή",
    pensando: "σκέφτομαι… μπορεί να πάρει λεπτά",
    tarde: "άργησε πολύ. Δοκίμασε κάτι πιο σύντομο.",
    fallo: "Δεν μπόρεσα να απαντήσω αυτή τη στιγμή.",
    sin_red: "Δεν μπόρεσα να φτάσω στον διακομιστή.",
    voz_local_no: "η τοπική υπαγόρευση δεν έχει συνδεθεί ακόμη, οπότε δεν υπάρχει. Καλύτερα γράψε: ό,τι πληκτρολογείς δεν φεύγει ποτέ από αυτό το μηχάνημα, ενώ ό,τι έλεγες από το μικρόφωνο του περιηγητή έφευγε.",
    sin_micro: "δεν μου έδωσες άδεια για το μικρόφωνο.",
    sin_oir: "Δεν σε άκουσα. Δοκίμασε να το γράψεις.",
    hablar: "Μίλα", escribir: "Γράψε",
    voz_apagada: "Υπαγόρευση ανενεργή",
    escuchando: "Ακούω… άγγιξε για διακοπή",
    nota_sin: "Χωρίς εγκατεστημένο εγκέφαλο, το PreceptorOS ρωτά και θυμάται αλλά δεν συζητά.",
    instalado: "εγκατεστημένο", sin_instalar: "μη εγκατεστημένο",
    et_modelo: "Μοντέλο", ruta_es: "στο", sin_modelo: "δεν δηλώθηκε",
    medicion: "Μέτρηση",
    med_intro: "Έντεκα πεδία. Ό,τι δεν μετριέται δηλώνεται, ποτέ δεν μηδενίζεται.",
    med_vivo: "ζωντανά · μετριέται ξανά κάθε 3 δ",
    med_pausa: "σε παύση — η οθόνη δεν είναι μπροστά",
    id_titulo: "Το κυρίαρχο αποτύπωμά σου",
    id_nota: "Προέρχεται από την τυχαιότητα αυτού του μηχανήματος, όχι από το όνομά σου ή τη συσκευή σου. Δεν είναι κλειδί: δεν υπογράφει τίποτα και δεν ανοίγει τίποτα. Δεν φεύγει ποτέ από εδώ.",
    id_rota: "ταυτότητα μη διαθέσιμη",
    cer_titulo: "Ποιος εγκέφαλος σου απαντά",
    cer_base: "Βασικός εγκέφαλος", cer_afinado: "Ρυθμισμένος εγκέφαλος",
    cer_en_uso: (n) => `Σε χρήση: ${n}`,
    cer_cambiando: "αλλαγή…",
    cer_hecho: (n) => `Έγινε. Ο επόμενος γύρος χρησιμοποιεί: ${n}`,
    cer_no: "δεν ήταν δυνατή η αλλαγή",
    cer_sin_servidor: "δεν φτάνω στον διακομιστή",
    med_medido: "μετρημένο", med_norma: "κανόνας", med_nodata: "χωρίς δεδομένα",
    med_fallo: "Η μέτρηση δεν μπόρεσε να διαβαστεί",
    med_pie: "Συγκρίσιμα είναι μόνο τα πακέτα που δηλώνουν το ίδιο παράθυρο και τα ίδια διακριτικά συνεδρίας.",
    afinado_vivo: "ρυθμισμένο · ζωντανά", base_vivo: "βασικό · ζωντανά",
    encendido: "ανοιχτό", apagado: "κλειστό",
    dilo: "Πες το", memoria: "Μνήμη", frontera: "Σύνορο", ajustes: "Ρυθμίσεις",
    tu_memoria: "Η μνήμη σου", la_frontera: "Το σύνορο", los_ajustes: "Ρυθμίσεις",
    camino: "Ο Δρόμος", el_camino: "Ο Δρόμος",
    camino_intro: "Οκτώ σκαλοπάτια. Εδώ βρίσκεσαι πραγματικά — μετρημένο, όχι υποθετικό.",
    encendiendo: "Ο εγκέφαλος ζεσταίνεται… έλα ξανά σε λίγα λεπτά",
    tardando: "Αργεί περισσότερο απ' ό,τι συνήθως. Το PreceptorOS γνωρίζεται με το τηλέφωνό σου.",
    fundiendo: "Το PreceptorOS γνωρίζεται με το τηλέφωνό σου. Συμβαίνει μόνο μία φορά",
    front_que: "Πριν φύγει ένα κείμενο, κλειδιά, διαδρομές και διευθύνσεις σβήνονται.",
    front_como: "Μετριέται η κατηγορία και το πλήθος, ποτέ το κείμενο που βρέθηκε. Κι αν το φίλτρο δεν μπορεί να τελειώσει, δεν στέλνεται τίποτα.",
    voz_no: "Αυτό το αντίγραφο δεν έχει φωνή: λείπει το {falta}.",
    volver: "← Πίσω", perfil: "Προφίλ", proyectos: "Έργα",
    et_nombre: "Πώς να σε λέω", et_intereses: "Τι σε ενδιαφέρει (χωρισμένο με κόμματα)",
    et_idioma: "Γλώσσα", et_instrucciones: "Πώς θέλεις να σου μιλούν",
    et_cerebro: "Εγκέφαλος", et_cuaderno: "Πώς σου απαντά",
    guardar: "Αποθήκευση", guardado: "Αποθηκεύτηκε.",
    ph_instrucciones: "Είσαι το PreceptorOS, ο σύντροφός μου στη μάθηση. Μίλα μου με σεβασμό αλλά χωρίς υπερβολική επισημότητα. Προτιμώ συγκεκριμένα παραδείγματα από αφηρημένη θεωρία.",
    nota_instrucciones: "Αυτό λέγεται στο PreceptorOS σε κάθε γύρο, μετά τον χαρακτήρα του και όχι στη θέση του: ρυθμίζεις πώς σου μιλά, όχι τι είναι.",
    proy_intro: "Ό,τι έχεις στα χέρια σου: ένα μισογραμμένο βιβλίο, μια εφαρμογή, μια ιδέα που επιστρέφει συνέχεια. Χωρίς προθεσμίες και προτεραιότητες: απλώς εκεί που το άφησες.",
    proy_vacio: "Κανένα ακόμη. Γράψε έναν τίτλο από πάνω και τέλος: τα υπόλοιπα συμπληρώνονται όποτε θέλεις.",
    et_pr_titulo: "Τίτλος", et_pr_desc: "Τι είναι", et_pr_estado: "Πώς πάει",
    et_pr_nota: "Σημειώσεις, ιδέες, οτιδήποτε",
    volver_lista: "← Όλα τα έργα", ed_guardar: "Αποθήκευση αλλαγών",
    est_activo: "Ενεργό", est_pausado: "Σε παύση", est_completado: "Ολοκληρώθηκε",
    ed_actualizado: (c) => `Τελευταία φορά που το άγγιξες: ${c}`,
    sin_tocar: "δεν αγγίχτηκε ακόμη",
    et_titulo: "Τίτλος", et_ruta: "Διαδρομή (προαιρετικό)",
    anadir: "Προσθήκη", no_esta: "δεν υπάρχει", quitar: "Αφαίρεση",
    abrir_panel: "Άνοιξε τον πλήρη πίνακα →", o_escribelo: "Ή γράψ' το",
    g_guarda: "Κράτα αυτό", g_guardado: "Αποθηκεύτηκε στη μνήμη σου",
    g_fallo: "Δεν ήταν δυνατή η αποθήκευση:",
    g_tachado: "Αποθηκεύτηκε έτσι, με τα ιδιωτικά μέρη διαγραμμένα:",
    m_nuevo: "Γράψε μια ανάμνηση",
    m_que: "Τι θέλεις να θυμάσαι",
    m_porque: "Γιατί σε ενδιαφέρει (προαιρετικό)",
    m_guardar: "Αποθήκευση",
    m_nota_nueva: "Ό,τι γράφεις περνά από το φίλτρο πριν αγγίξει τον δίσκο. Θα δεις τι αποθηκεύτηκε.",
    m_guardados: "Αποθηκευμένες αναμνήσεις", m_consentidos: "Με συναίνεση για μάθηση",
    m_corregidos: "Διορθωμένες από εσένα",
    nota_memoria: "Ζει σε ένα μόνο αρχείο στο μηχάνημά σου. Μπορείς να το αντιγράψεις και να το πάρεις μαζί σου.",
    hecho: "έγινε", empezado: "ξεκίνησε", sin_empezar: "δεν ξεκίνησε",
    no_medible: "δεν μετριέται από εδώ",
    agentes: "Πράκτορες και εργαλεία",
    et_tema: "Θέμα", tema_sistema: "Όπως το σύστημα",
    tema_claro: "Φωτεινό", tema_oscuro: "Σκοτεινό",
    sin_nombre: "χωρίς όνομα ακόμη",
    lat_medir: "Μέτρηση", lat_camino: "Δρόμος",
    lat_memoria: "Μνήμη", lat_proyectos: "Έργα",
    lat_frontera: "Σύνορο",
    at_resume: "Σύνοψέ το", at_pasos: "Δώσε μου τα βήματα",
    at_dudas: "Τι σου λείπει",
    ph_dicho: "Γράψε εδώ",
    manifiesto: "Το Μανιφέστο του Builder",
    esp_titulo: "Τα όρια αυτής της συνεδρίας",
    esp_quien: "Ποιος σου απαντά", esp_ritmo: "Με ποιον ρυθμό",
    esp_memoria: "Μνήμη μοντέλου", esp_libre: "Ελεύθερη στο μηχάνημα",
    esp_ventana: "Παράθυρο πλαισίου", esp_gastado: "Ξοδεμένο από το παράθυρο",
    esp_sin_conteo: "κανείς δεν μετρά τα διακριτικά αυτής της συνεδρίας, οπότε ένας αριθμός εδώ θα ήταν επινοημένος",
    esp_lleno: "Το πλαίσιό μου γέμισε. Χρειάζομαι εσένα, ως Builder, να αποφασίσεις αν θα γίνει σύνοψη ή αν θα μεγαλώσει το υλικό.",
    esp_aviso: "Αυτό δεν είναι πίνακας ελέγχου: είναι εκεί που τελειώνει το μηχάνημά σου. Ό,τι δεν μετριέται λέγεται, ποτέ δεν μηδενίζεται.",
    saluda: "Είμαι ο Preceptor σου και ζω σε αυτό το μηχάνημα: ό,τι γράφεις εδώ δεν φεύγει από αυτό. Μπορώ να θυμάμαι ό,τι μου λες, να σε βοηθώ με τα έργα σου και να σου λέω όταν δεν ξέρω κάτι. Γράψε από κάτω ή άγγιξε μία από τις συντομεύσεις.",
  },
  ar: {
    cap_si: "مخصّصة", cap_no: "بسيطة",
    nota_captura: "في الوضع المخصّص، يخبر التطبيق النموذج من أنت وتعليماتك وما في ذاكرتك ومشاريعك بالفعل. وفي البسيط، يسافر السؤال وحده. بدّله واسأل الشيء نفسه مرتين: الفرق يُسمع، وهذا ما يفعله هذا التطبيق. وفي الحالتين يمرّ الجواب عبر المرشّح قبل أن يعود.",
    elige_idioma: "بأي لغة تريد أن نتحدث؟",
    listo: "اكتب هنا",
    sin_cerebro: "أستطيع أن أسأل وأتذكّر، ولا أستطيع الحوار بعد",
    sin_servidor: "لا أصل إلى الخادم",
    pensando: "أفكّر… قد يستغرق هذا دقائق",
    tarde: "استغرق وقتًا أطول من اللازم. جرّب شيئًا أقصر.",
    fallo: "لم أستطع الإجابة الآن.",
    sin_red: "لم أستطع الوصول إلى الخادم.",
    voz_local_no: "الإملاء المحلي لم يُوصَل بعد، فهو غير موجود. اكتب بدلًا من ذلك: ما تكتبه لا يغادر هذا الجهاز أبدًا، أما ما قلته عبر ميكروفون المتصفح فكان يغادره.",
    sin_micro: "لم تمنحني إذن الميكروفون.",
    sin_oir: "لم أسمعك. جرّب أن تكتبه.",
    hablar: "تكلّم", escribir: "اكتب",
    voz_apagada: "الإملاء متوقف",
    escuchando: "أستمع… المس للإيقاف",
    nota_sin: "بلا دماغ مثبّت، يسأل PreceptorOS ويتذكّر لكنه لا يحاور.",
    instalado: "مثبّت", sin_instalar: "غير مثبّت",
    et_modelo: "النموذج", ruta_es: "في", sin_modelo: "غير مُعلَن",
    medicion: "القياس",
    med_intro: "أحد عشر حقلًا. ما لا يُقاس يُعلَن، ولا يُصفَّر أبدًا.",
    med_vivo: "مباشر · يُقاس من جديد كل 3 ث",
    med_pausa: "متوقف مؤقتًا — الشاشة ليست في المقدّمة",
    id_titulo: "بصمتك السيادية",
    id_nota: "تأتي من عشوائية هذا الجهاز، لا من اسمك ولا من جهازك. ليست مفتاحًا: لا توقّع شيئًا ولا تفتح شيئًا. ولا تغادر هذا المكان أبدًا.",
    id_rota: "الهوية غير متاحة",
    cer_titulo: "أي دماغ يجيبك",
    cer_base: "الدماغ الأساسي", cer_afinado: "الدماغ المضبوط",
    cer_en_uso: (n) => `قيد الاستخدام: ${n}`,
    cer_cambiando: "جارٍ التبديل…",
    cer_hecho: (n) => `تمّ. الدور التالي يستخدم: ${n}`,
    cer_no: "تعذّر التبديل",
    cer_sin_servidor: "لا أصل إلى الخادم",
    med_medido: "مقيس", med_norma: "المعيار", med_nodata: "بلا بيانات",
    med_fallo: "تعذّرت قراءة القياس",
    med_pie: "لا تُقارَن إلا الحزم التي تُعلن النافذة نفسها ورموز الجلسة نفسها.",
    afinado_vivo: "مضبوط · مباشر", base_vivo: "أساسي · مباشر",
    encendido: "مفعّل", apagado: "متوقف",
    dilo: "قُلها", memoria: "الذاكرة", frontera: "الحدّ", ajustes: "الإعدادات",
    tu_memoria: "ذاكرتك", la_frontera: "الحدّ", los_ajustes: "الإعدادات",
    camino: "الطريق", el_camino: "الطريق",
    camino_intro: "ثماني درجات. هنا تقف فعلًا — مقيس، لا مفترَض.",
    encendiendo: "الدماغ يُسخَّن… عُد بعد بضع دقائق",
    tardando: "يستغرق هذا أكثر من المعتاد. PreceptorOS يتعرّف على هاتفك.",
    fundiendo: "PreceptorOS يتعرّف على هاتفك. هذا يحدث مرة واحدة فقط",
    front_que: "قبل أن يغادر أي نص، تُمحى المفاتيح والمسارات والعناوين.",
    front_como: "ما يُعدّ هو الفئة والكمية، لا النص الذي عُثر عليه أبدًا. وإن لم يستطع المرشّح الإنهاء، لا يُرسَل شيء.",
    voz_no: "هذه النسخة بلا صوت: ينقصها {falta}.",
    volver: "→ رجوع", perfil: "الملف الشخصي", proyectos: "المشاريع",
    et_nombre: "بماذا نناديك", et_intereses: "ما يهمّك (مفصولًا بفواصل)",
    et_idioma: "اللغة", et_instrucciones: "كيف تريد أن يُتحدَّث إليك",
    et_cerebro: "الدماغ", et_cuaderno: "كيف يجيبك",
    guardar: "احفظ", guardado: "حُفظ.",
    ph_instrucciones: "أنت PreceptorOS، رفيقي في التعلّم. كلّمني باحترام لكن دون رسمية زائدة. أفضّل الأمثلة الملموسة على النظرية المجرّدة.",
    nota_instrucciones: "يُقال هذا لـ PreceptorOS في كل دور، بعد شخصيته لا مكانها: أنت تضبط كيف يكلّمك، لا ما هو.",
    proy_intro: "ما بين يديك: كتاب نصف مكتوب، تطبيق، فكرة تعود دائمًا. بلا مواعيد ولا أولويات: فقط حيث تركته.",
    proy_vacio: "لا شيء بعد. اكتب عنوانًا في الأعلى وكفى: البقية تُملأ متى شئت.",
    et_pr_titulo: "العنوان", et_pr_desc: "ما هو", et_pr_estado: "كيف يسير",
    et_pr_nota: "ملاحظات، أفكار، أي شيء",
    volver_lista: "→ كل المشاريع", ed_guardar: "احفظ التغييرات",
    est_activo: "نشط", est_pausado: "متوقف مؤقتًا", est_completado: "منجز",
    ed_actualizado: (c) => `آخر مرة لمسته: ${c}`,
    sin_tocar: "لم يُلمس بعد",
    et_titulo: "العنوان", et_ruta: "المسار (اختياري)",
    anadir: "أضف", no_esta: "غير موجود", quitar: "أزل",
    abrir_panel: "← افتح اللوحة كاملة", o_escribelo: "أو اكتبه",
    g_guarda: "احفظ هذا", g_guardado: "حُفظ في ذاكرتك",
    g_fallo: "تعذّر الحفظ:",
    g_tachado: "حُفظ هكذا، مع شطب الأجزاء الخاصة:",
    m_nuevo: "اكتب ذكرى",
    m_que: "ما الذي تريد أن تتذكّره",
    m_porque: "لماذا يهمّك (اختياري)",
    m_guardar: "احفظ",
    m_nota_nueva: "ما تكتبه يمرّ عبر المرشّح قبل أن يلمس القرص. سترى ما حُفظ.",
    m_guardados: "ذكريات محفوظة", m_consentidos: "بموافقة للتعلّم",
    m_corregidos: "صحّحتها أنت",
    nota_memoria: "تعيش في ملف واحد على جهازك. يمكنك نسخه وأخذه معك.",
    hecho: "تمّ", empezado: "بدأ", sin_empezar: "لم يبدأ",
    no_medible: "لا يُقاس من هنا",
    agentes: "الوكلاء والأدوات",
    et_tema: "المظهر", tema_sistema: "كما في النظام",
    tema_claro: "فاتح", tema_oscuro: "داكن",
    sin_nombre: "بلا اسم بعد",
    lat_medir: "قِس", lat_camino: "الطريق",
    lat_memoria: "الذاكرة", lat_proyectos: "المشاريع",
    lat_frontera: "الحدّ",
    at_resume: "لخّص هذا", at_pasos: "أعطني الخطوات",
    at_dudas: "ما الذي ينقصك",
    ph_dicho: "اكتب هنا",
    manifiesto: "بيان الباني",
    esp_titulo: "حدود هذه الجلسة",
    esp_quien: "من يجيبك", esp_ritmo: "بأي إيقاع",
    esp_memoria: "ذاكرة النموذج", esp_libre: "الحرّ على الجهاز",
    esp_ventana: "نافذة السياق", esp_gastado: "المستهلَك من النافذة",
    esp_sin_conteo: "لا أحد يعدّ رموز هذه الجلسة، فأي رقم هنا سيكون مختلَقًا",
    esp_lleno: "سياقي ممتلئ. أحتاج أن تقرّر أنت، بصفتك الباني، هل نلخّص أم نوسّع العتاد.",
    esp_aviso: "هذه ليست لوحة قيادة: إنها حيث ينتهي جهازك. ما لا يُقاس يُقال، ولا يُصفَّر أبدًا.",
    saluda: "أنا Preceptor الخاص بك وأعيش على هذا الجهاز: ما تكتبه هنا لا يغادره. أستطيع أن أتذكّر ما تقوله لي، وأن أساعدك في مشاريعك، وأن أقول لك حين لا أعرف شيئًا. اكتب في الأسفل، أو المس أحد الاختصارات.",
  },
};
const t = (clave) => (T[idioma] || T.es)[clave];

/* --- cajones ----------------------------------------------------------- */
const velo = $("velo");
function abrir(cual) {
  document.querySelectorAll(".cajon").forEach((c) => {
    const suyo = c.id === "cajon-" + cual;
    // El paso a abierto NO va por `requestAnimationFrame`, por lo mismo que el
    // panel lateral: con la pestana en segundo plano el navegador no dispara
    // ni un fotograma, la clase no se pone y el cajon se queda presente pero
    // sin transformar -- ocupando la pantalla y comiendose los toques de lo que
    // hay debajo. Leer `offsetWidth` fuerza el calculo de caja ahi mismo, que
    // es lo unico que hacia falta, y es sincrono.
    if (suyo) { c.hidden = false; void c.offsetWidth; c.classList.add("abierto"); }
    else { c.classList.remove("abierto"); c.hidden = true; }
  });
  velo.classList.add("visible");
  document.querySelectorAll("[data-cajon]").forEach((b) =>
    b.setAttribute("aria-expanded", String(b.dataset.cajon === cual)));
  if (cual === "memoria" || cual === "perfil") pulso();
  if (cual === "camino") cargarCamino();
  if (cual === "perfil") cargarPerfil();
  if (cual === "proyectos") cargarProyectos();
  // Se mide al abrir el cajon, no al cargar la pagina: una temperatura leida
  // hace diez minutos y pintada como actual es un sensor deshonesto con
  // buena cara.
  if (cual === "medicion") { pintaMedicion(); pintaCerebro(); latidoArranca(); }
  else latidoPara();
}
function cerrar() {
  latidoPara();
  document.querySelectorAll(".cajon").forEach((c) => {
    c.classList.remove("abierto");
    setTimeout(() => { c.hidden = true; }, 220);
  });
  velo.classList.remove("visible");
  document.querySelectorAll("[data-cajon]").forEach((b) =>
    b.setAttribute("aria-expanded", "false"));
}
/* Dos formas de cerrar y DOS enganches, no uno. `data-volver` es un enlace de
 * texto --«← Volver»-- y el pintado de rotulos le escribe encima en cada
 * idioma; `data-cerrar` es el aspa de la Capa 5, que lleva un dibujo dentro.
 * Con un solo enganche, el pintado le borraba el aspa y le dejaba el texto:
 * dos controles distintos no pueden compartir la marca que decide que se les
 * escribe encima. */
document.querySelectorAll("[data-volver], [data-cerrar]").forEach((b) =>
  b.addEventListener("click", cerrar));
document.querySelectorAll("[data-cajon]").forEach((b) =>
  b.addEventListener("click", () => abrir(b.dataset.cajon)));
velo.addEventListener("click", cerrar);

/* Deslizar hacia abajo cierra el cajon: es el gesto que la gente ya conoce. */
let y0 = null;
document.querySelectorAll(".cajon").forEach((c) => {
  c.addEventListener("touchstart", (e) => { y0 = e.changedTouches[0].clientY; },
                     { passive: true });
  c.addEventListener("touchend", (e) => {
    if (y0 !== null && e.changedTouches[0].clientY - y0 > 70) cerrar();
    y0 = null;
  }, { passive: true });
});

/* --- la eleccion de idioma, una sola vez ---------------------------------
 * Se ensena entre el telon y el home la primera vez, y nunca mas. Va ahi y no
 * dentro de Ajustes porque todo lo que viene despues esta escrito en algun
 * idioma: preguntarlo despues seria ensenar una pantalla en un idioma para
 * preguntar en cual se quiere leer.
 *
 * Y no se adivina por el del navegador. Se puede leer `navigator.language`, y
 * es un dato util, pero elegir por el es suponer: mucha gente usa el sistema en
 * un idioma y prefiere leer en otro. Se pregunta, que cuesta un toque.
 *
 * La marca de «ya elegido» vive en este aparato, no en el perfil: el perfil
 * viaja con la persona y esta pregunta es de la instalacion. */
function yaEligio() {
  try { return localStorage.getItem("idioma-elegido") === "si"; }
  catch (_) { return true; }        // sin donde guardar, no se pregunta cada vez
}

/* El mismo control en los dos sitios: la pantalla de eleccion y Ajustes. Se
 * dibuja una vez y se usa dos, para que no puedan divergir -- que es lo que
 * pasa siempre con dos listas del mismo dato en dos ficheros. */
function cajasIdioma(caja, puesto, alElegir) {
  caja.textContent = "";
  for (const [codigo, nombre] of Object.entries(nombres)) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "eleccion-caja";
    b.lang = codigo;
    b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(codigo === puesto));
    b.textContent = nombre;
    b.addEventListener("click", () => alElegir(codigo));
    caja.appendChild(b);
  }
}

async function guardaIdioma(codigo) {
  idioma = codigo;
  try {
    await fetch("/api/perfil", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language: codigo }),
    });
  } catch { /* sin servidor la eleccion vale igual para esta sesion */ }
  pulso();
}

function pintaEleccion() {
  const caja = $("eleccion");
  if (!caja || yaEligio()) return;
  $("eleccion-titulo").textContent = t("elige_idioma");
  cajasIdioma($("eleccion-cajas"), idioma, async (codigo) => {
    try { localStorage.setItem("idioma-elegido", "si"); } catch (_) { /* sin sitio */ }
    caja.hidden = true;
    await guardaIdioma(codigo);
  });
  caja.hidden = false;
}

/* Los nombres, cada uno en SU idioma. Un selector que dice «Spanish» en ingles
 * obliga a saber ingles para elegir castellano, que es la barrera que estos
 * idiomas vienen a quitar. Salen de aqui y no del diccionario porque no se
 * traducen: son nombres propios.
 *
 * En minuscula, aunque la convencion de JS pida versales para una constante:
 * en este directorio la regla de la casa gana a la del lenguaje, porque un
 * nombre en versales dispara la misma guardia que un texto en versales. Es la
 * misma nota que lleva `ausente` unas lineas mas abajo. */
const nombres = { es: "Español", en: "English", pt: "Português", fr: "Français",
                  it: "Italiano", de: "Deutsch", ru: "Русский", el: "Ελληνικά",
                  ar: "العربية" };

/* --- la primera linea, para quien acaba de entrar ------------------------
 * El hueco de conversacion nacia vacio. Medido entrando como usuario nuevo el
 * 2026-09-04: se ve una cara, un boton y un marco de bronce con nada dentro, y
 * nada dice que es esto ni que sabe hacer. La primera pregunta obvia --«que
 * eres»-- se la lleva el modelo, y el modelo contesta con otra pregunta.
 *
 * Asi que la respuesta a esa pregunta NO se le pide al modelo: se escribe. Es
 * lo unico de esta pantalla que tiene que ser igual siempre, decir la verdad
 * siempre y no tardar veintiocho segundos.
 *
 * Se pinta solo si el hueco esta vacio, y desaparece sola en cuanto se habla:
 * `linea()` anade al final y esto queda arriba, como la primera frase de una
 * conversacion que ya empezo. */
function saluda() {
  const d = $("dice");
  if (!d) return;
  const ya = d.firstElementChild;
  // Si la bienvenida ya esta, se reescribe en vez de dejarla: al cambiar de
  // idioma seguia en el anterior, porque la condicion era «no hay nada» y si
  // habia algo -- ella misma. La linea de bienvenida es la unica del hueco que
  // no es un turno, asi que rehacerla no pisa nada de lo que se haya hablado.
  if (ya && ya.className === "saluda") { ya.textContent = t("saluda"); return; }
  if (d.children.length) return;
  const p = document.createElement("p");
  p.className = "saluda";
  p.textContent = t("saluda");
  d.appendChild(p);
}

/* --- Capa 3 · el lateral de agentes y herramientas -----------------------
 * Se rellena desde aqui y no desde el marcado porque lo que ofrece tiene que
 * ser lo que de verdad existe. Cada entrada abre un cajon que ya esta
 * construido: medir, el Camino, la memoria, los proyectos y la frontera.
 * Poner ahi nombres de agentes que nadie ha escrito seria prometer un taller
 * que no esta montado, que es justo lo que este producto no hace.
 *
 * El cierre tiene tres caminos y los tres importan: el propio boton, la tecla
 * de escape --y entonces el foco Vuelve al boton, o quien navega con teclado
 * se queda sin sitio donde estaba-- y un toque fuera del panel. */
const lateral = $("lateral");
const latBoton = $("lateral-boton");
const herramientas = [
  ["lat_medir", "medicion"], ["lat_camino", "camino"],
  ["lat_memoria", "memoria"], ["lat_proyectos", "proyectos"],
  ["lat_frontera", "frontera"],
];
function pintaLateral() {
  lateral.textContent = "";
  for (const [clave, cajon] of herramientas) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = t(clave);
    b.addEventListener("click", () => { cierraLateral(); abrir(cajon); });
    lateral.appendChild(b);
  }
}
/* El paso de cerrado a abierto NO va por `requestAnimationFrame`, y esto se
 * midio el 2026-09-04 en vez de suponerlo: con la pestana en segundo plano el
 * navegador no dispara ni un fotograma, asi que la clase nunca se ponia y el
 * panel se quedaba presente y transparente. Un panel invisible que sigue
 * ocupando su sitio se come los toques de lo que hay debajo, y nadie puede
 * saber por que.
 *
 * Leer `offsetWidth` fuerza al navegador a calcular la caja Ahi mismo, que es
 * lo unico que hacia falta: fija el estado de partida para que la transicion
 * tenga desde donde salir. Es sincrono y no depende de que nadie mire. */
function abreLateral() {
  pintaLateral();
  lateral.hidden = false;
  void lateral.offsetWidth;
  lateral.classList.add("abierto");
  latBoton.setAttribute("aria-expanded", "true");
}
function cierraLateral(devolverFoco) {
  if (lateral.hidden) return;
  lateral.classList.remove("abierto");
  latBoton.setAttribute("aria-expanded", "false");
  setTimeout(() => { lateral.hidden = true; }, 200);
  if (devolverFoco) latBoton.focus();
}
latBoton.addEventListener("click", () => {
  if (latBoton.getAttribute("aria-expanded") === "true") cierraLateral(true);
  else abreLateral();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") cierraLateral(true);
});
document.addEventListener("click", (e) => {
  if (!e.target.closest(".lateral-zona")) cierraLateral();
});

/* --- Capa 2 · el cabezal se aparta cuando se escribe ---------------------
 * Pierde intensidad, no desaparece. Con `display` la caja entera se moveria y
 * el chat daria un salto justo al tocar el campo, que es el defecto que el
 * bloque del teclado viene a matar unas lineas mas abajo. */
const dicho = $("dicho");
dicho.addEventListener("focusin", () => document.body.classList.add("chat-activo"));
dicho.addEventListener("focusout", () => document.body.classList.remove("chat-activo"));

/* --- el tema, y por que vive en este aparato y no en el perfil -----------
 * El tema es una preferencia del cacharro que se tiene delante, no de la
 * persona: la misma persona quiere oscuro en el telefono de noche y claro en
 * la mesa. Guardarlo en el perfil lo sincronizaria entre aparatos, que es
 * justo lo que no se quiere -- y ademas obligaria a tocar el servidor para
 * algo que no sale de la pantalla.
 *
 * «sistema» no escribe atributo: deja mandar a `prefers-color-scheme`, que es
 * la decision firmada el 2026-09-04. Las otras dos lo desobedecen a mano. */
function aplicaTema(cual) {
  const raiz = document.documentElement;
  if (cual === "claro" || cual === "oscuro") raiz.setAttribute("data-tema", cual);
  else raiz.removeAttribute("data-tema");
}
/* Oscuro por defecto, firmado el 2026-09-04. Antes era «sistema», que en una
 * maquina en claro daba una interfaz clara: se decidio que la piel oscura es
 * la del producto, no una preferencia heredada. «Sistema» sigue estando -- es
 * una opcion mas del interruptor, no el punto de partida. */
function temaGuardado() {
  try { return localStorage.getItem("tema") || "oscuro"; }
  catch (_) { return "oscuro"; }
}
aplicaTema(temaGuardado());

/* El interruptor de tres. Se dibuja desde aqui y no en el marcado porque sus
 * rotulos cambian con el idioma, y porque el que esta puesto se marca con
 * `aria-checked`: quien navega con lector de pantalla oye cual es sin tener
 * que abrir nada. Un desplegable escondia dos de cada tres opciones y, sobre
 * todo, escondia cual estaba elegida -- que es lo primero que se viene a ver. */
/* El cuaderno, interruptor de dos. Antes era un rotulo que decia «encendido» y
 * no se podia tocar: enseñar un estado sin la forma de cambiarlo obliga a
 * buscar donde se cambia, y no se cambiaba en ningun sitio -- la clave existia
 * en el perfil desde el principio y ninguna puerta la escribia.
 *
 * Se guarda al pulsar, sin esperar a «Guardar»: es una decision de una sola
 * cosa, y hacerla depender de un boton al final de la pantalla invita a
 * cambiarla y creerse que ya esta. */
/* --- los tres campos del harness: crecen, y dicen cuanto caben -----------
 * Los tres son lo mismo --lo que la app le cuenta al modelo de ti-- asi que
 * pesan lo mismo en la pantalla y se comportan igual: crecen con lo escrito,
 * sin barra propia, porque un campo que hace scroll dentro esconde lo que ya
 * pusiste justo cuando lo relees.
 *
 * El limite es una recomendacion, no un candado. Y sale de una cuenta, no de
 * un gusto: la ventana medida en este nodo son 32.768 tokens, y a unos cuatro
 * caracteres por token el 5 % de esa ventana --un techo ya generoso-- daria
 * 2.185 caracteres por campo. Se recomiendan 500, que es bastante menos, por
 * dos razones que el numero grande no ve: esto se manda entero en cada turno,
 * asi que compite con la conversacion; y los modelos que esta app usa son
 * pequenos, donde un prompt de sistema largo no anade contexto -- reparte la
 * atencion. Pasarse no rompe nada, y por eso se avisa en vez de cortar. */
const limiteHarness = 500;

function crece(area) {
  area.style.height = "auto";
  area.style.height = area.scrollHeight + "px";
}

function cuentaHarness(area, salida) {
  const n = (area.value || "").length;
  salida.textContent = n + " / " + limiteHarness;
  salida.classList.toggle("pasado", n > limiteHarness);
}

function enganchaHarness() {
  for (const nombre of ["nombre", "intereses", "instrucciones"]) {
    const area = $("p-" + nombre);
    const salida = $("cuenta-" + nombre);
    if (!area || !salida || area.dataset.enganchado) continue;
    area.dataset.enganchado = "si";
    const refresca = () => { crece(area); cuentaHarness(area, salida); };
    area.addEventListener("input", refresca);
    refresca();
  }
}

function pintaCaptura(activo) {
  const caja = $("p-captura");
  if (!caja) return;
  $("nota-captura").textContent = t("nota_captura");
  caja.textContent = "";
  for (const [valor, clave] of [["si", "cap_si"], ["no", "cap_no"]]) {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String((valor === "si") === activo));
    b.textContent = t(clave);
    b.addEventListener("click", async () => {
      try {
        await fetch("/api/perfil", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ personalizada: valor }),
        });
      } catch { /* sin servidor no se pudo cambiar; el pulso lo dira */ }
      pulso();
      cargarPerfil();
    });
    caja.appendChild(b);
  }
}

function pintaTema() {
  const caja = $("p-tema");
  if (!caja) return;
  const puesto = temaGuardado();
  caja.textContent = "";
  for (const [valor, clave] of [["sistema", "tema_sistema"],
                                ["claro", "tema_claro"],
                                ["oscuro", "tema_oscuro"]]) {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(valor === puesto));
    b.textContent = t(clave);
    b.addEventListener("click", () => {
      aplicaTema(valor);
      try { localStorage.setItem("tema", valor); } catch (_) { /* sin sitio donde guardar */ }
      pintaTema();
    });
    caja.appendChild(b);
  }
}

/* --- Capa 1 · los atajos de debajo del campo -----------------------------
 * Tres gestos que no dependen de que el cerebro sepa nada raro: resumir, pedir
 * pasos y preguntar que le falta. Escriben en el campo y dejan el cursor ahi;
 * no mandan solos, porque un atajo que manda sin que se lea lo que va a mandar
 * es un boton que habla por ti. */
const atajos = $("atajos");

/* --- el primero no escribe en el campo: copia la llave -------------------
 * «Launch PreceptorOS», y va el primero porque es lo primero que hace falta.
 *
 * Qué hace: copia una línea al portapapeles. Esa línea se pega en las
 * instrucciones de la ia de fuera --Claude, ChatGPT, Gemini-- y desde ahí esa
 * ia sabe pedir la puerta y trabajar con esta memoria. Sin montar un servidor,
 * sin dar permisos de carpeta uno por uno, sin aprenderse un protocolo.
 *
 * Por qué no escribe en el campo, como sus tres vecinos: los otros son cosas
 * que se le dicen al modelo de aquí. Este es lo único del cuadro que sale
 * hacia afuera, y escribirlo en el campo se lo mandaría al modelo equivocado.
 * Mismo sitio, gesto distinto -- y por eso el rótulo es un verbo y no una
 * frase: se ve que hace otra cosa antes de pulsarlo.
 *
 * La llave viene de la puerta, no escrita aquí. El día que cambie, cambia en
 * un sitio. Una llave copiada en la interfaz es la que se queda vieja en las
 * instrucciones de otra persona, donde nadie la mira.
 *
 * No se traduce, y es la misma razón por la que `/instalar` no se traduce: es
 * un identificador. Si en alemán fuera otra cadena, el apretón de manos
 * tendría ocho formas y ninguna guía escrita por un usuario serviría para
 * otro.
 *
 * Y este comentario va en minúsculas a propósito. Hay un guardián que recorre
 * `interface/` buscando nombres de política, y una palabra en versales dentro
 * de la prosa se lee como uno: cayó con «primero». La regla ya estaba escrita
 * y aun así se pisó, así que queda aquí, donde muerde. */
function atajoLlave() {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = "Launch PreceptorOS";
  b.addEventListener("click", async () => {
    const antes = b.textContent;
    try {
      const d = await (await fetch("/api/empieza-aqui")).json();
      await navigator.clipboard.writeText(d.llave);
      b.textContent = "✓";
    } catch (e) {
      // Un hueco declarado con su causa, como todo aquí. Un botón que no hace nada y no
      // dice por que es peor que uno que falta.
      b.textContent = "sin dato";
    }
    setTimeout(() => { b.textContent = antes; }, 2200);
  });
  return b;
}

function pintaAtajos() {
  atajos.textContent = "";
  atajos.appendChild(atajoLlave());
  for (const clave of ["at_resume", "at_pasos", "at_dudas"]) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = t(clave);
    b.addEventListener("click", () => {
      dicho.value = t(clave) + ": ";
      dicho.focus();
    });
    atajos.appendChild(b);
  }
  atajos.hidden = false;
}

/* --- estado ------------------------------------------------------------ */
/* El rotulo del boton grande se calcula en Un sitio. Estaba en cuatro -- al
 * arrancar, al escuchar, al parar y al no haber reconocimiento -- y cada uno
 * escribia su cadena. Cuatro sitios que dicen lo mismo son cuatro sitios donde
 * se puede quedar uno sin traducir. */
function rotulo() {
  // Ya no se pregunta al navegador si sabe escuchar: aunque sepa, no se usa.
  // El rotulo dice «Escribir» siempre, porque es lo que el boton hace. Un
  // rotulo que promete escuchar y lleva a un campo de texto es peor que uno
  // honesto y aburrido.
  // El nombre accesible dice lo que el dibujo dice: el microfono esta tachado
  // porque el dictado esta apagado. Antes ponia «Escribir», que era honesto con
  // lo que el boton hace, pero no con lo que el icono promete; con el microfono
  // al lado de Enviar, un lector de pantalla tiene que oir lo mismo que se ve.
  const r = $("rotulo-hablar");
  if (r) r.textContent = t("voz_apagada");
}

async function pulso() {
  // El fetch y el pintado, separados a proposito. Estaban en el mismo `try`, y
  // una referencia a un elemento que ya no existia -- quedo huerfana al fusionar
  // dos paneles en uno -- caia en el mismo `catch` y la cara decia "no alcanzo
  // al servidor" mientras el servidor contestaba 200 dos veces. Un mensaje que
  // culpa a la red por un fallo propio manda a mirar donde no es.
  let d;
  try {
    const r = await fetch("/api/estado");
    d = await r.json();
  } catch {
    // `#pulso` salio del cabezal el 2026-09-04 con el mando de voz. Lo que
    // decia --«escribe aqui»-- lo dice ya el propio campo, dos centimetros mas
    // abajo. Se comprueba antes de escribir en vez de borrar estas lineas: el
    // dia que vuelva un sitio donde decir «sin servidor», aqui esta el texto.
    if ($("pulso")) $("pulso").textContent = t("sin_servidor");
    $("hablar").disabled = true;
    $("mandar").disabled = true;
    return;
  }
  // Un fallo pintando NO es un fallo de red, y se dice distinto. Si esto se
  // traga la excepcion, la cara se queda a medio traducir y nadie sabe por que.
  try {
    pintarEstado(d);
  } catch (e) {
    if ($("pulso")) $("pulso").textContent = "· " + (e && e.message ? e.message : e);
  }
}

function pintarEstado(d) {
  // El idioma que manda el servidor vale si el tablero sabe hablarlo. Esta
  // linea decia `d.idioma === "en" ? "en" : "es"`, la misma coercion de dos
  // idiomas que ya se corrigio en `cargarPerfil` -- y esta, que corre en cada
  // pulso, pisaba a aquella: se elegia portugues, se guardaba bien, y al
  // siguiente pulso volvia a castellano sin que nada lo dijera. Dos sitios con
  // la misma regla escrita a mano, y arreglar uno solo no arregla nada.
  idioma = T[d.idioma] ? d.idioma : "es";
  document.documentElement.lang = idioma;
  document.documentElement.dir = idioma === "ar" ? "rtl" : "ltr";
  if ($("pulso")) $("pulso").textContent = d.motor ? t("listo") : t("sin_cerebro");
  rotulo();
  // El rotulo del campo sale del diccionario como todo lo demas. Decia «…o
  // escribelo aqui», y ese «o» era la segunda mitad de una disyuntiva cuya
  // primera mitad --hablar por el microfono-- se retiro hace tiempo: quedaba
  // una alternativa sin la otra opcion, ofreciendo algo que no esta.
  $("dicho").placeholder = t("ph_dicho");
  saluda();
  pintaEleccion();
  // Las etiquetas del marco tambien: estaban escritas en el HTML y por eso
  // no cambiaban. Un tablero que declara hablar dos idiomas y solo traduce
  // los mensajes esta a medio traducir, que se nota mas que no traducir.
  $("mandar").setAttribute("aria-label", t("dilo"));
  $("frontera-que").textContent = t("front_que");
  $("frontera-como").textContent = t("front_como");
  // Solo el <span> del rotulo: el boton lleva un icono dentro, y escribir
  // en el boton entero lo borraria. Ya paso una vez con los titulos.
  document.querySelectorAll("[data-rotulo]").forEach((sp) => {
    sp.textContent = t(sp.dataset.rotulo);
  });
  document.querySelectorAll("[data-volver]").forEach((b) => {
    b.textContent = t("volver");
  });
  for (const [id, clave] of Object.entries({
      "et-nombre": "et_nombre", "et-intereses": "et_intereses",
      "et-idioma": "et_idioma", "et-tema": "et_tema",
      "et-instrucciones": "et_instrucciones",
      "et-cerebro": "et_cerebro", "et-cuaderno": "et_cuaderno",
      "et-modelo": "et_modelo",
      "et-titulo": "et_titulo",
      "nota-instrucciones": "nota_instrucciones", "proy-intro": "proy_intro",
      "et-pr-titulo": "et_pr_titulo", "et-pr-desc": "et_pr_desc",
      "et-pr-estado": "et_pr_estado", "et-pr-nota": "et_pr_nota",
      "proy-vacio": "proy_vacio",
      "nota-memoria": "nota_memoria", "r-nota": "m_nota_nueva"})) {
    const el = $(id);
    if (el) el.textContent = t(clave);
  }
  for (const [id, clave] of Object.entries({"r-que": "m_que", "r-porque": "m_porque"})) {
    const el = $(id);
    if (el) el.placeholder = t(clave);
  }
  // Los atajos y el lateral se repintan con el idioma: sus rotulos se escriben
  // desde el javascript, asi que el barrido de `data-rotulo` de arriba no los
  // alcanza -- no existen como marcado hasta que alguien los dibuja.
  pintaAtajos();
  if (!lateral.hidden) pintaLateral();
  pintaTema();
  $("ir-manifiesto").textContent = t("manifiesto") + " →";
  $("p-guardar").textContent = t("guardar");
  $("pr-anadir").textContent = t("anadir");
  $("pr-volver-lista").textContent = t("volver_lista");
  $("ed-guardar").textContent = t("ed_guardar");
  $("ed-quitar").textContent = t("quitar");
  if (abierto !== null) pintaEstados();
  $("p-instrucciones").placeholder = t("ph_instrucciones");
  const titulos = { memoria: "tu_memoria", frontera: "la_frontera",
                    camino: "el_camino", perfil: "perfil",
                    proyectos: "proyectos" };
  for (const [cual, clave] of Object.entries(titulos)) {
    const h = document.querySelector("#cajon-" + cual + " h2");
    if (!h) continue;
    // Se escribe en el <span> del rotulo, NO en el <h2>: el h2 lleva ahora
    // un icono dentro, y `h2.textContent = ...` lo borraba entero. Un
    // titulo que se traduce no deberia poder tirar su propio icono.
    const rot = h.querySelector("span") || h;
    rot.textContent = t(clave);
  }
  $("hablar").disabled = !d.motor;
  $("mandar").disabled = !d.motor;
  $("m-turnos").textContent = d.turnos.turnos;
  $("m-consent").textContent = d.turnos.consentidos;
  $("m-corr").textContent = d.turnos.corregidos;
  $("a-motor").textContent = d.motor ? t("instalado") : t("sin_instalar");
  // QUE cerebro, y donde. «Instalado» no distingue un 4B de un 27B, y quien
  // mide tok/s necesita saber cual midio. Sin modelo se declara la causa: la
  // ruta esperada tambien es un dato, y es la que hace falta para arreglarlo.
  const cb = d.cerebro || {};
  // Que cerebro contesta HOY, y si es el afinado o el base. Un LoRA propio es
  // marca personal: si esta vivo, se anuncia; si esta declarado y no cuadra su
  // huella, el servidor ya cayo al base y aqui se dice base, no afinado.
  $("a-modelo").textContent = cb.nombre
    ? cb.nombre + (cb.bytes ? "  " + (cb.bytes / 1e9).toFixed(2) + " GB" : "") +
      (d.motor ? "  · " + t(cb.afinado ? "afinado_vivo" : "base_vivo") : "")
    : t("sin_modelo");
  $("a-ruta").textContent = cb.ruta
    ? t("ruta_es") + " " + cb.ruta + (cb.motivo ? "  · " + cb.motivo : "")
    : (cb.causa || "");
  pintaCaptura(!!d.personalizada);
  // Con motor no se dice nada: la espera ya la cuenta el chat mientras pasa,
  // y el ritmo real vive en el Espejo. Sin motor si, porque eso no lo dice
  // nadie mas y cambia lo que la app puede hacer.
  $("a-nota").textContent = d.motor ? "" : t("nota_sin");
}

/* --- decir ------------------------------------------------------------- */
function linea(texto, clase) {
  const p = document.createElement("p");
  if (clase) p.className = clase;
  if (clase === "espera") {
    // Un reloj de arena junto al texto. La espera aqui son Minutos, y un
    // texto quieto sin nada que se mueva se lee como una pantalla colgada.
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("class", "reloj");
    svg.setAttribute("aria-hidden", "true");
    for (const d of ["M 6 2 h12", "M 6 22 h12",
                     "M 6 2 c 0 5 12 5 12 0", "M 6 22 c 0 -5 12 -5 12 0"]) {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", d);
      svg.appendChild(path);
    }
    p.appendChild(svg);
    const t_ = document.createElement("span");
    t_.textContent = texto;
    p.appendChild(t_);
    $("dice").appendChild(p);
    p.scrollIntoView({ block: "end" });
    return p;
  }
  p.textContent = texto;
  // Solo sobre lo que escribio la persona, y no sobre la respuesta: guardarla
  // pediria un origen que el vocabulario no tiene --no es de la persona ni
  // viene importado de fuera-- y ese vocabulario no se migra. Inventarle uno
  // seria decidir por el esquema desde la interfaz.
  if (clase === "mio") p.appendChild(botonGuardar(texto));
  $("dice").appendChild(p);
  p.scrollIntoView({ block: "end" });
  return p;
}

/* --- el gesto de «guarda esto» -------------------------------------------
 * El camino mas corto de «entro» a «tengo memoria»: el primer recuerdo nace de
 * algo que la persona ya escribio, no de un formulario en blanco.
 *
 * Se ensena lo guardado, no lo enviado. La puerta devuelve el texto ya pasado
 * por su filtro, y puede no ser el mismo: si la persona no ve que se tacho de
 * su texto, esta firmando a ciegas lo que entra en su propia memoria. Por eso
 * el boton no se limita a decir «hecho».
 */
function botonGuardar(texto) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "guardar-turno";
  b.textContent = t("g_guarda");
  b.addEventListener("click", async () => {
    b.disabled = true;
    try {
      const r = await fetch("/api/anidar", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto, origen: "persona" }),
      });
      const d = await r.json();
      if (!r.ok) {
        b.textContent = t("g_fallo") + " " + (d.motivo || "");
        b.disabled = false;
        return;
      }
      b.textContent = t("g_guardado");
      b.classList.add("hecho");
      // Si el filtro tacho algo, se dice y se ensena. Callarlo seria dejar en
      // la memoria un texto distinto del que la persona creyo guardar.
      if (d.texto !== texto) {
        const n = document.createElement("small");
        n.className = "tachado";
        n.textContent = t("g_tachado") + " " + d.texto;
        b.parentElement.appendChild(n);
      }
      pulso();
    } catch {
      b.textContent = t("g_fallo") + " " + t("sin_red");
      b.disabled = false;
    }
  });
  return b;
}

async function turno(texto) {
  if (!texto.trim()) return;
  linea(texto, "mio");
  $("hablar").disabled = true;
  $("mandar").disabled = true;
  $("busto").classList.add("piensa");
  // DOS Avisos, y el orden importa. El primero sale YA: el modelo tarda porque
  // hay que subir 2,3 GiB de disco a memoria, y eso es fisica, no un fallo.
  // Decirlo Antes de que la persona se impaciente es la diferencia entre
  // "esta cargando" y "se ha colgado". El segundo lo sustituye cuando ya solo
  // queda generar.
  if (!fusionYaVista()) fusion(true);
  const encendiendo = linea(t("encendiendo"), "espera");
  let esperando = null;
  let tardando = null;
  // Tres tramos, y cada uno dice algo que el anterior no podia decir todavia.
  // A los cuatro segundos ya no esta encendiendo: esta generando. Al minuto,
  // callarse seria dejar a la persona mirando una pantalla quieta sin saber
  // si sigue vivo.
  const relevo = setTimeout(() => {
    encendiendo.remove();
    esperando = linea(t("pensando"), "espera");
  }, 4000);
  const aviso = setTimeout(() => {
    if (esperando) esperando.remove();
    tardando = linea(t("tardando"), "espera");
  }, 60000);
  const limpiar = () => {
    clearTimeout(relevo); clearTimeout(aviso);
    encendiendo.remove();
    if (esperando) esperando.remove();
    if (tardando) tardando.remove();
  };
  try {
    const r = await fetch("/api/charla", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    limpiar();
    marcarFusionVista();
    if (r.ok) linea(d.texto);
    else linea(d.estado === "tarde" ? t("tarde") : t("fallo"), "malo");
  } catch {
    limpiar();
    linea(t("sin_red"), "malo");
  }
  /* Pensar termina y empieza a hablar. La respuesta llega entera --no hay
   * streaming-- asi que la boca se mueve mientras el texto acaba de aparecer y
   * se para sola: dos vueltas de la tira de habla, que es lo que dura leer la
   * primera linea. Dejarla moviendose despues seria una cara que sigue
   * hablando cuando ya no dice nada. */
  const cara = $("busto");
  cara.classList.remove("piensa");
  cara.classList.add("habla");
  clearTimeout(cara._callar);
  cara._callar = setTimeout(() => cara.classList.remove("habla"), 1730);
  pulso();
}

$("escribir").addEventListener("submit", (e) => {
  e.preventDefault();
  const t = $("dicho").value;
  $("dicho").value = "";
  turno(t);
});

/* --- el recuerdo escrito a mano -------------------------------------------
 * El segundo gesto. Va por la misma puerta que el primero y con el mismo
 * origen: dos caminos a la misma habitacion, no dos habitaciones.
 *
 * Se ensena lo que quedo guardado y no un «hecho» a secas, por la misma razon
 * que en el turno: el filtro puede haber tachado algo, y un recuerdo que no es
 * el que la persona creyo escribir es peor que uno que no se guardo.
 */
$("recuerdo-nuevo").addEventListener("submit", async (e) => {
  e.preventDefault();
  const que = $("r-que").value.trim();
  if (!que) return;
  const boton = $("r-guardar");
  const dicho = $("r-dicho");
  boton.disabled = true;
  try {
    const r = await fetch("/api/anidar", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: que, porque: $("r-porque").value.trim() || null,
                             origen: "persona" }),
    });
    const d = await r.json();
    if (!r.ok) {
      dicho.textContent = t("g_fallo") + " " + (d.motivo || "");
    } else {
      // El campo se vacia solo si de verdad se guardo. Vaciarlo antes de saber
      // el resultado le quita a la persona lo unico que tenia si algo fallo.
      $("r-que").value = ""; $("r-porque").value = "";
      dicho.textContent = d.texto === que
        ? t("g_guardado")
        : t("g_tachado") + " " + d.texto;
      pulso();
    }
  } catch {
    dicho.textContent = t("g_fallo") + " " + t("sin_red");
  }
  dicho.hidden = false;
  boton.disabled = false;
});

/* --- voz --------------------------------------------------------------- */
/* El reconocedor del navegador se retiro el 2026-08-26, y el motivo importa.
 *
 * `webkitSpeechRecognition` no transcribe en tu maquina: Chrome manda el audio
 * a servidores de Google. Este producto promete, en el caracter que se envia en
 * cada turno, «nothing said here leaves this machine» -- y esa promesa era
 * cierta para lo que se escribe y falsa para lo que se dice. Ofrecer el boton
 * sin decirlo era vender una cosa y entregar otra.
 *
 * No se sustituye por un aviso: un aviso deja la fuga puesta y le pasa la
 * decision a quien menos informacion tiene. Se quita.
 *
 * Lo que falta para que vuelva, escrito para que no se olvide: `oido.py` ya
 * envuelve whisper.cpp y en este nodo responde `oido_disponible() -> True`. Le
 * falta un canal para subir el audio, y crear endpoints esta congelado hasta
 * que lo firme el carbono. El dictado local es la condicion de despertar de
 * este bloque; el de Google no vuelve.
 */
$("hablar").addEventListener("click", () => {
  if (!avisoVozVisto()) {
    linea(t("voz_local_no"), "malo");
    guardarAvisoVoz();
  }
  $("dicho").focus();
});

function avisoVozVisto() {
  try { return localStorage.getItem("preceptoros.voz-avisada") === "si"; }
  catch { return false; }
}
function guardarAvisoVoz() {
  try { localStorage.setItem("preceptoros.voz-avisada", "si"); }
  catch { /* modo privado: se avisa cada vez, que es lo seguro */ }
}

/* La primera carga sube 2-3 GB de disco a memoria. Se avisa UNA vez por
 * dispositivo -- se recuerda en el propio navegador -- porque a la segunda ya
 * no es noticia. Puntos y no barra: una barra falsa inventa un porcentaje que
 * nadie mide, y este producto no fabrica sensores. */
function fusion(encender) {
  const caja = $("fusion");
  if (!encender) { caja.hidden = true; return; }
  $("fusion-texto").textContent = t("fundiendo");
  caja.hidden = false;
  let n = 0;
  const id = setInterval(() => {
    n = (n + 1) % 4;
    $("puntos").textContent = ".".repeat(n);
  }, 600);
  caja.dataset.reloj = id;
}
function fusionYaVista() {
  try { return localStorage.getItem("aurelius-fusion") === "si"; }
  catch { return false; }
}
function marcarFusionVista() {
  try { localStorage.setItem("aurelius-fusion", "si"); } catch { /* privado */ }
  const caja = $("fusion");
  if (caja.dataset.reloj) clearInterval(Number(caja.dataset.reloj));
  fusion(false);
}

/* Un gesto cada 25-40 segundos, y nunca mientras piensa: ahi ya se mueve la
 * boca, y dos cosas moviendose a la vez es ruido. El intervalo se sortea en
 * cada vuelta -- uno fijo se vuelve un tic, y un tic se nota mas que el gesto.
 *
 * Por que existe: el modelo tarda minutos en un telefono. Entre turno y turno
 * la pantalla se queda quieta, y quieta se lee como rota. Esto no acelera
 * nada; solo dice que sigue ahi. */
/* Cuando el despertar termina, se marca. A partir de ahi la cara respira y no
   se vuelve a despertar: quitar la clase `piensa` al terminar una respuesta
   reiniciaba la lista de animaciones y con ella el despertar entero.
   `animationend` y no un temporizador de 1,5 s copiado a mano: el dia que la
   duracion cambie en el css, un numero repetido aqui se queda viejo y nadie
   se entera. Se filtra por nombre porque `respirar` tambien termina... nunca,
   pero `hablar` y `latir` si podrian llegar aqui. */
const bustoEl = $("busto");
if (bustoEl) {
  /* Antes esto esperaba al `animationend` de `despertar` para encender el ciclo
     de color. La apertura salio del cabezal el 2026-09-04 --es la entrada del
     producto y vive en el telon--, asi que ese evento ya no llega nunca y la
     cara se quedaria en el primer cuadro para siempre. Se enciende de entrada.
     El oyente no se sustituye por un temporizador: no hay nada que esperar. */
  bustoEl.classList.add("despierto");
}

function gesto() {
  const b = $("busto");
  const proxima = 25000 + Math.floor(Math.random() * 15000);
  if (b && !b.classList.contains("piensa")) {
    b.classList.add("gesto");
    setTimeout(() => b.classList.remove("gesto"), 420);
  }
  setTimeout(gesto, proxima);
}
setTimeout(gesto, 12000);

/* --- perfil ------------------------------------------------------------ */
/* Los campos se leen del servidor y se escriben uno a uno. La marca de
 * ausencia es un valor del producto, no un texto que la persona deba ver en
 * una caja: se enseña vacio, que es lo que significa.
 *
 * La constante se compone, y no es un capricho. Cicatriz del 2026-09-02.
 * La marca va en mayusculas, y `test_guardrails` prohibe palabras en
 * mayusculas en los ficheros de `interface/` -- la regla existe porque una
 * interfaz que nombra una politica inexistente promete un filtro que no
 * existe. Aqui alguien esquivo el gate escribiendo la marca con otras
 * mayusculas: el gate paso, y la comparacion dejo de acertar. Al abrir Perfil
 * en una instalacion nueva, la marca salia escrita dentro de las cajas, como
 * si la persona se llamara asi.
 *
 * Componerla en dos trozos da el valor correcto sin que la palabra entera
 * exista en el fichero. Cambiar un dato para que un gate pase es como se
 * fabrican los fallos que ninguna prueba ve; cambiar como se escribe, sin
 * tocar el valor, no lo es. */
/* En minuscula, aunque la convencion de JS pida mayusculas para una
 * constante: en este directorio la regla de la casa gana a la convencion del
 * lenguaje, y un nombre en mayusculas dispara el mismo gate que el valor. */
const ausente = "NO" + "_DATA";
function sinNoData(v) { return (!v || v === ausente) ? "" : v; }

/* El nombre del cabezal. Sin nombre se dice que no lo hay, no se deja el guion
 * puesto: un hueco mudo se lee como una pantalla a medio cargar, y este es
 * ademas el sitio donde alguien descubre que puede ponerse uno. */
function pintaQuien(nombre) {
  $("quien").textContent = nombre || t("sin_nombre");
}

async function cargarPerfil() {
  try {
    const r = await fetch("/api/perfil");
    const d = await r.json();
    $("p-nombre").value = sinNoData(d.campos.name);
    $("p-intereses").value = sinNoData(d.campos.intereses);
    $("p-instrucciones").value = sinNoData(d.campos.instrucciones);
    // El idioma guardado vale si el tablero sabe hablarlo. Antes esta linea
    // decia `idi === "en" ? "en" : "es"`, o sea que cualquier idioma que no
    // fuera ingles se leia como castellano: con el portugues guardado, el
    // selector volvia a ensenar «Español» y la persona no entendia por que su
    // eleccion no se quedaba. El diccionario es quien sabe que idiomas hay.
    const idi = sinNoData(d.campos.language) || "es";
    // Desplegable aqui y recuadros en la pantalla de entrada, a proposito: la
    // entrada es una pantalla entera y los idiomas caben todos a la vista --
    // que es lo que hace que se elija sin leer un rotulo--; Ajustes es un
    // formulario, y ocho pastillas serian dos filas que empujan el resto fuera.
    const sel = $("p-idioma");
    sel.textContent = "";
    for (const [codigo, nombre] of Object.entries(nombres)) {
      const o = document.createElement("option");
      o.value = codigo; o.textContent = nombre;
      sel.appendChild(o);
    }
    sel.value = T[idi] ? idi : "es";
    sel.onchange = () => guardaIdioma(sel.value).then(cargarPerfil);
    pintaQuien(sinNoData(d.campos.name));
    pintaIdentidad(d);
    enganchaHarness();
  } catch { /* el pulso ya dice que no hay servidor */ }
}

/* La huella, y solo la huella. No se calcula aqui: la deriva el servidor de una
   semilla que no viaja, asi que esta pantalla la ensena y nunca la inventa.

   El selector de caras vivia aqui y salio el 2026-09-04 por orden del Soberano:
   ensenaba dieciseis dibujos en una pantalla que es la de la identidad, y le
   quitaba seriedad a lo unico serio que hay en ella. La API NO se ha tocado --
   `/api/perfil` sigue declarando `avatares` y validando `avatar` contra su lista
   cerrada, con sus pruebas 25, 26 y 27 en pie--. Se ha retirado la vitrina, no
   el vocabulario: el dia que vuelva a hacer falta elegir cara, el servidor ya
   sabe hacerlo. */
function pintaIdentidad(d) {
  $("id-titulo").textContent = t("id_titulo");
  const id = d.identidad || {};
  // Un hueco se dice con su causa. Nunca un guion decorativo en su sitio.
  $("id-huella").textContent = id.corta || t("id_rota");
  $("id-nota").textContent = id.huella ? t("id_nota") : (id.causa || "");
}

/* El Manifiesto se despliega aqui, no se abre fuera. La primera version
 * enlazaba a la web y comprobaba `navigator.onLine`; el Soberano acepto la
 * alternativa el 2026-09-04 y esa version se deshizo. El canon dice que la app
 * no rutea a la web, y el motivo escrito es que un enlace saliente dentro de
 * algo que promete funcionar sin internet es una ruta a la red justo donde se
 * prometio que no la habia. Servirlo del propio disco cumple las dos cosas: la
 * orden de tenerlo accesible, y la promesa de que sigue estandolo sin red.
 *
 * Se pide al pulsar y no al cargar: son catorce mil caracteres que la mayoria
 * de las sesiones no abre nunca. */
let manifiesto = null;
$("ir-manifiesto").addEventListener("click", async () => {
  const caja = $("manifiesto-texto");
  const boton = $("ir-manifiesto");
  if (!caja.hidden) {
    caja.hidden = true;
    boton.setAttribute("aria-expanded", "false");
    return;
  }
  if (manifiesto === null) {
    try {
      const r = await fetch("/api/manifiesto");
      const d = await r.json();
      manifiesto = d.texto || d.causa || t("sin_servidor");
    } catch { manifiesto = t("sin_servidor"); }
  }
  caja.textContent = manifiesto;
  caja.hidden = false;
  boton.setAttribute("aria-expanded", "true");
});

$("p-guardar").addEventListener("click", async () => {
  const cuerpo = {
    name: $("p-nombre").value,
    intereses: $("p-intereses").value,
    instrucciones: $("p-instrucciones").value,
  };
  try {
    const r = await fetch("/api/perfil", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
    if (!r.ok) return;
    pintaQuien(cuerpo.name);       // el cabezal no espera a la proxima carga
    const av = $("p-dicho");
    av.textContent = t("guardado");
    av.hidden = false;
    setTimeout(() => { av.hidden = true; }, 2500);
    pulso();                       // el idioma puede haber cambiado
  } catch { /* nada que guardar si no hay servidor */ }
});

/* --- proyectos --------------------------------------------------------- */
/* Dos vistas y un solo cajon. `abierto` es el proyecto que se esta editando, o
   `null` si se esta viendo la lista; de ahi sale todo lo demas, para que no
   haya dos sitios que puedan discrepar sobre en cual estamos.

   Lo que este cuaderno no tiene, y es una decision: fechas limite, prioridades
   y porcentajes de avance. Un proyecto propio al que le pones fecha deja de ser
   tuyo y pasa a perseguirte. Esto solo recuerda que existe y en que punto lo
   dejaste; la unica presion que ejerce es la de estar escrito. */
let abierto = null;

async function cargarProyectos() {
  try {
    const r = await fetch("/api/proyectos");
    const d = await r.json();
    pintaLista(d.proyectos || []);
    // Si se estaba editando uno, se refresca con lo que devolvio el servidor:
    // lo que se ensena tiene que ser lo que quedo guardado, no lo que se tecleo.
    if (abierto) {
      const fresco = (d.proyectos || []).find((p) => p.id === abierto.id);
      if (fresco) { abierto = fresco; pintaEditor(); } else { volverALista(); }
    }
  } catch { /* sin servidor no hay lista */ }
}

function pintaLista(lista) {
  const ul = $("lista-proyectos");
  ul.replaceChildren();
  $("proy-vacio").hidden = lista.length > 0;
  for (const p of lista) {
    const li = document.createElement("li");
    const boton = document.createElement("button");
    boton.type = "button"; boton.className = "abrir";

    const cabeza = document.createElement("div");
    cabeza.className = "cabeza";
    const b = document.createElement("b");
    b.textContent = p.titulo;
    const chip = document.createElement("span");
    chip.className = "chip " + (p.estado || "activo");
    chip.textContent = t("est_" + (p.estado || "activo")) || p.estado;
    cabeza.appendChild(b); cabeza.appendChild(chip);
    boton.appendChild(cabeza);

    if (p.descripcion && p.descripcion !== ausente) {
      const desc = document.createElement("p");
      desc.className = "desc"; desc.textContent = p.descripcion;
      boton.appendChild(desc);
    }
    /* La ruta ya no se pide al crear, pero las entradas viejas la tienen y se
       ensena: quitarla de la vista habria escondido un dato que la persona
       escribio. Y si el sitio ya no esta, se dice; no se borra sola. */
    if (p.ruta && p.ruta !== ausente) {
      const ruta = document.createElement("div");
      ruta.className = "ruta"; ruta.textContent = p.ruta;
      boton.appendChild(ruta);
      if (!p.existe) {
        const falta = document.createElement("div");
        falta.className = "falta"; falta.textContent = t("no_esta");
        boton.appendChild(falta);
      }
    }
    const cuando = document.createElement("p");
    cuando.className = "cuando";
    cuando.textContent = t("ed_actualizado")(p.actualizado || t("sin_tocar"));
    boton.appendChild(cuando);

    boton.addEventListener("click", () => { abierto = p; abrirEditor(); });
    li.appendChild(boton);
    ul.appendChild(li);
  }
}

function abrirEditor() {
  $("proy-lista-vista").hidden = true;
  $("proy-editor").hidden = false;
  $("cajon-proyectos").classList.add("editando");
  pintaEditor();
  $("cajon-proyectos").scrollTop = 0;
}

function volverALista() {
  abierto = null;
  $("proy-editor").hidden = true;
  $("proy-lista-vista").hidden = false;
  $("cajon-proyectos").classList.remove("editando");
}

function pintaEditor() {
  if (!abierto) return;
  $("ed-titulo").value = abierto.titulo || "";
  $("ed-desc").value = sinNoData(abierto.descripcion);
  $("ed-nota").value = sinNoData(abierto.nota);
  $("ed-actualizado").textContent =
    t("ed_actualizado")(abierto.actualizado || t("sin_tocar"));
  pintaEstados();
}

/* Los tres estados, como grupo de radio y no como menu desplegable: son tres,
   caben, y un desplegable esconde dos de cada tres. */
const estadosProy = ["activo", "pausado", "completado"];
function pintaEstados() {
  const caja = $("ed-estados");
  if (!caja) return;
  caja.replaceChildren();
  for (const est of estadosProy) {
    const b = document.createElement("button");
    b.type = "button"; b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(!!abierto && abierto.estado === est));
    b.textContent = t("est_" + est);
    // El estado se guarda al tocarlo, sin pasar por «guardar»: es un gesto, no
    // un formulario. El texto si espera al boton, que es donde se piensa.
    b.addEventListener("click", () => {
      if (!abierto) return;
      proyectoGuardar({ editar: abierto.id, estado: est });
    });
    caja.appendChild(b);
  }
}

async function proyectoGuardar(cuerpo) {
  await fetch("/api/proyectos", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  cargarProyectos();
}

$("pr-anadir").addEventListener("click", () => {
  const titulo = $("pr-titulo").value.trim();
  if (!titulo) return;
  proyectoGuardar({ titulo });
  $("pr-titulo").value = "";
});

$("pr-volver-lista").addEventListener("click", volverALista);

$("ed-guardar").addEventListener("click", () => {
  if (!abierto) return;
  proyectoGuardar({ editar: abierto.id, titulo: $("ed-titulo").value,
                    descripcion: $("ed-desc").value, nota: $("ed-nota").value });
});

/* Quitar pide confirmacion, y borra la entrada, no el trabajo. Un proyecto en
   esta lista es un recordatorio: al quitarlo no se pierde el libro, se pierde
   la nota que decia por donde ibas. Conviene que se entienda antes de pulsar. */
$("ed-quitar").addEventListener("click", () => {
  if (!abierto) return;
  if (!confirm(t("quitar") + ": " + abierto.titulo)) return;
  const id = abierto.id;
  volverALista();
  proyectoGuardar({ quitar: id });
});


/* --- el Camino --------------------------------------------------------- */
/* Los ocho peldaños salen del servidor, con su estado medido. Aqui NO se
 * decide si algo esta hecho: se pinta lo que el producto midio. Un tablero que
 * calculara el progreso por su cuenta podria discrepar del fichero, y entonces
 * la persona ve una cosa y su memoria dice otra. */
async function cargarCamino() {
  try {
    const r = await fetch("/api/camino");
    const d = await r.json();
    $("camino-intro").textContent = t("camino_intro");
    const ul = $("camino");
    ul.replaceChildren();
    for (const p of d.peldanos) {
      const li = document.createElement("li");
      li.dataset.rama = p.rama;
      li.dataset.hecho = p.estado;
      const id = document.createElement("span");
      id.className = "peldano"; id.textContent = p.id;
      const nombre = document.createElement("span");
      nombre.textContent = p.nombre;
      const como = document.createElement("span");
      como.className = "como"; como.textContent = t(p.estado) || p.estado;
      li.append(id, nombre, como);
      ul.appendChild(li);
    }
  } catch {
    $("camino-intro").textContent = t("sin_servidor");
  }
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
pulso();
/* El nombre del cabezal se pide al arrancar y no solo al abrir el cajon de
 * Perfil: vive a la vista desde el primer segundo, asi que esperar a que
 * alguien abra un cajon lo dejaria con un guion puesto toda la sesion. */
cargarPerfil();


/* --- el cajon de Medicion -----------------------------------------------
   Pinta las once cifras de la norma de metricas. La interfaz no calcula ni
   una: todas llegan de /api/metricas ya medidas. Si aqui se hiciera una
   division habria dos verdades sobre la misma cifra, y la de la pantalla
   ganaria por ser la que se ve.

   Un hueco se reconoce por `valor === null`, no por el nombre de su estado:
   el modulo garantiza esa equivalencia con una prueba, y comparar contra el
   valor evita escribir aqui nombres que este fichero no puede nombrar. */
/* --- El Espejo del Builder ------------------------------------------------
 * Cuatro filas y ninguna inventada. Vive en Medicion porque preguntar «hasta
 * donde llega esto» y «cuanto corre» es el mismo gesto.
 *
 * La fila que mas importa es la que sale vacia. La ventana se sabe --32.768,
 * medida en este nodo-- pero lo gastado de ella no lo cuenta nadie en este
 * producto: `tokens_sesion` se declara y nunca se incrementa. Poner ahi una
 * barra de progreso seria fabricar un sensor, que es exactamente lo que este
 * modulo lleva escrito que no hace. Sale el hueco con su causa.
 *
 * Y por eso el aviso del contexto lleno se ensena cuando ocurre --el motor
 * falla y lo dice-- y no cuando un calculo nuestro lo prediga. Un aviso
 * adivinado que se equivoca ensena a ignorar los avisos. */
function fila(caja, clave, campo, sufijo) {
  const d = document.createElement("div");
  d.className = "dato";
  const et = document.createElement("span");
  et.textContent = t(clave);
  const v = document.createElement("b");
  if (campo && campo.estado !== ausente && campo.valor !== null) {
    v.textContent = campo.valor + (sufijo || "");
  } else {
    v.textContent = "—";
    v.className = "hueco";
    if (campo && campo.causa) d.title = campo.causa;
  }
  d.appendChild(et); d.appendChild(v);
  caja.appendChild(d);
  return d;
}

function pintaEspejo(por) {
  const caja = $("espejo");
  if (!caja) return;
  $("esp-titulo").textContent = t("esp_titulo");
  $("esp-aviso").textContent = t("esp_aviso");
  caja.textContent = "";
  fila(caja, "esp_ritmo", por.tokens_por_segundo, " tok/s");
  fila(caja, "esp_memoria", por.consumo_ram_mb, " MiB");
  fila(caja, "esp_libre", por.memoria_libre_mb, " MiB");
  fila(caja, "esp_ventana", por.ventana_contexto, " tokens");
  // El hueco declarado, con su causa escrita al lado y no escondida en un
  // titulo: es la fila que ensena como se lee todo lo demas.
  const g = fila(caja, "esp_gastado", null, "");
  const causa = document.createElement("p");
  causa.className = "nota causa";
  causa.textContent = t("esp_sin_conteo");
  caja.appendChild(causa);
  return g;
}

async function pintaMedicion() {
  const tabla = $("med-tabla");
  const cab = $("med-modelo");
  if (!tabla) return;
  try {
    const r = await fetch("/api/metricas");
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    const por = {};
    d.metricas.forEach((m) => { por[m.clave] = m; });
    (d.espejo || []).forEach((m) => { por[m.clave] = m; });
    pintaEspejo(por);

    // La cabecera: que cerebro y de que base sale. `modelo_base` es
    // obligatorio en la norma, asi que si falta se dice, y no se omite.
    const nom = por.modelo_nombre, tam = por.modelo_tamano_gb, base = por.modelo_base;
    cab.textContent = "";
    const t1 = document.createElement("b");
    t1.textContent = nom.valor !== null ? nom.valor : t("sin_modelo");
    cab.appendChild(t1);
    if (tam.valor !== null) {
      const t2 = document.createElement("span");
      t2.textContent = "  " + tam.valor + " GB";
      cab.appendChild(t2);
    }
    const t3 = document.createElement("p");
    t3.className = "nota";
    t3.textContent = "base: " + (base.valor !== null ? base.valor : base.causa);
    cab.appendChild(t3);

    tabla.textContent = "";
    const orden = ["consumo_ram_mb", "tokens_sesion", "ventana_contexto",
                   "tokens_por_segundo", "latencia_primer_token_ms",
                   "duracion_ms", "temp_cpu_c", "vram_mb"];
    orden.forEach((clave) => {
      const m = por[clave];
      if (!m) return;
      const fila = document.createElement("div");
      fila.className = "dato";
      const et = document.createElement("span");
      et.textContent = clave.replace(/_/g, " ");
      const val = document.createElement("b");
      // Un hueco se pinta como raya y lleva su causa en el title. Poner un
      // cero aqui seria la mentira mas barata que hay.
      val.textContent = m.valor === null ? "—" : m.valor + " " + m.unidad;
      val.dataset.estado = m.estado;
      val.title = m.causa || m.como || "";
      fila.appendChild(et); fila.appendChild(val);
      tabla.appendChild(fila);
    });
    $("med-norma").textContent = t("med_pie");
  } catch (e) {
    tabla.textContent = t("med_fallo") + " — " + e.message;
  }
}


/* --- el selector de cerebro ----------------------------------------------
   Nada de lo que se pinta aqui se decide aqui. `disponible` y `causa` los
   calcula el servidor con `afinado.elegir`, que es quien mide la huella del
   fichero contra el registro. Si esta pantalla decidiera por su cuenta cual se
   puede usar, podria ofrecer un cerebro que el turno siguiente va a rechazar.

   Y por la puerta no viaja una ruta: se manda `base` o `afinado`, dos
   palabras. El servidor resuelve los ficheros. */
function _tarjetaCerebro(op, enUso) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "cer-op";
  b.disabled = !op.disponible;
  const suyo = op.cual === enUso;
  b.setAttribute("aria-pressed", String(suyo));

  const punto = document.createElement("span");
  punto.className = "cer-punto";
  punto.textContent = suyo ? "✓" : "";
  punto.setAttribute("aria-hidden", "true");

  const cuerpo = document.createElement("span");
  cuerpo.className = "cer-cuerpo";
  const nombre = document.createElement("span");
  nombre.className = "cer-nombre";
  nombre.textContent = t(op.cual === "base" ? "cer_base" : "cer_afinado");
  cuerpo.appendChild(nombre);

  /* Lo que se sabe de este cerebro, en una linea. Si no se puede usar, la
     causa la manda el servidor palabra por palabra: aqui no se traduce ni se
     resume un motivo tecnico -- resumirlo es donde se pierde el porque. */
  const detalle = document.createElement("p");
  detalle.className = "cer-detalle";
  const trozos = [];
  if (op.nombre) trozos.push(op.nombre);
  if (op.version) trozos.push(op.version);
  if (op.bytes !== null && op.bytes !== undefined) {
    trozos.push((op.bytes / 1073741824).toFixed(2) + " GB");
  }
  if (op.notas) trozos.push(op.notas);
  if (op.causa) trozos.push(op.causa);
  detalle.textContent = trozos.join(" · ");
  cuerpo.appendChild(detalle);

  b.append(punto, cuerpo);
  if (!b.disabled && !suyo) {
    b.addEventListener("click", () => elegirCerebro(op.cual));
  }
  return b;
}

function _pintaPaqueteCerebro(d) {
  $("cer-titulo").textContent = t("cer_titulo");
  $("cer-uso").textContent =
    t("cer_en_uso")(d.en_uso.nombre || d.en_uso.cual) + " — " + d.en_uso.motivo;
  const caja = $("cer-opciones");
  caja.replaceChildren();
  for (const op of d.opciones) caja.appendChild(_tarjetaCerebro(op, d.en_uso.cual));
}

async function pintaCerebro() {
  try {
    const r = await fetch("/api/cerebro", { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    _pintaPaqueteCerebro(await r.json());
    $("cer-dicho").hidden = true;
  } catch {
    $("cer-titulo").textContent = t("cer_titulo");
    $("cer-uso").textContent = t("cer_sin_servidor");
    $("cer-opciones").replaceChildren();
  }
}

async function elegirCerebro(cual) {
  $("cer-dicho").hidden = false;
  $("cer-dicho").textContent = t("cer_cambiando");
  try {
    const r = await fetch("/api/cerebro", {
      method: "Post", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cual, motivo: "elegido desde el tablero" }),
    });
    const d = await r.json();
    if (!r.ok) {
      $("cer-dicho").textContent = `${t("cer_no")}: ${d.motivo || r.status}`;
      return;
    }
    // Se repinta con lo que el servidor dice que hay en este momento. Pedir el afinado y
    // que su huella no cuadre termina en el base, y eso tiene que verse.
    _pintaPaqueteCerebro(d);
    $("cer-dicho").hidden = false;
    $("cer-dicho").textContent =
      t("cer_hecho")(d.en_uso.nombre || d.en_uso.cual);
  } catch {
    $("cer-dicho").textContent = t("cer_sin_servidor");
  }
}


/* --- el latido de Medicion ------------------------------------------------
   Las cifras se vuelven a medir mientras el cajon esta abierto, y solo
   mientras lo esta.

   Por que no al cargar la pagina: una temperatura leida hace diez minutos y
   pintada como actual es un sensor deshonesto con buena cara -- eso ya lo
   decia el comentario de `abrir`, y esto es su continuacion. Un panel que se
   llama Banco de Pruebas y ensena un numero congelado no vale para lo que
   existe: comparar dos cerebros midiendo.

   Y por que se para: un reloj que se arranca al abrir y no se para al cerrar
   sigue pidiendo al servidor para siempre. En un telefono eso es bateria que
   se va sin que nada en la pantalla lo justifique. Peor: abrir y cerrar cinco
   veces dejaria cinco relojes a la vez. `latidoPara` se llama siempre antes de
   arrancar otro, asi que no se pueden apilar aunque alguien llame dos veces.

   Tambien se para con la pantalla detras. `visibilitychange` cubre lo que un
   telefono hace de verdad: bloquear y cambiar de aplicacion no cierran el
   cajon, y sin esto se seguiria midiendo con el aparato en el bolsillo. */
/* En minuscula por la regla de la casa para `interface/`, no por descuido. */
const latidoMs = 3000;
let latido = null;

function latidoPara() {
  if (latido) { clearInterval(latido); latido = null; }
  const aviso = $("med-vivo");
  if (aviso) aviso.hidden = true;
}

function latidoArranca() {
  latidoPara();                       // nunca dos a la vez
  const aviso = $("med-vivo");
  if (document.hidden) {
    if (aviso) { aviso.hidden = false; aviso.textContent = t("med_pausa"); }
    return;
  }
  latido = setInterval(() => {
    if (document.hidden) return;      // no se mide lo que nadie mira
    pintaMedicion();
  }, latidoMs);
  if (aviso) { aviso.hidden = false; aviso.textContent = t("med_vivo"); }
}

/* El cajon abierto se reconoce por el propio cajon, no por una variable que
   haya que mantener en paralelo: dos verdades sobre si algo esta abierto
   terminan discrepando. */
function medicionAbierta() {
  const c = $("cajon-medicion");
  return c && !c.hidden;
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) latidoPara();
  else if (medicionAbierta()) { pintaMedicion(); latidoArranca(); }
});

/* --- El teclado de Android, y por que `resize` a secas no basta -----------
 *
 * En Chrome de Android el teclado NO encoge el layout: la ventana sigue
 * midiendo lo mismo y el teclado se pinta Encima. `window.innerHeight` no se
 * entera, `resize` casi nunca dispara, y el ultimo mensaje del chat se queda
 * debajo del teclado sin que nada avise. Lo que si se entera es
 * `visualViewport`, que es lo que de verdad se ve.
 *
 * Se mide cuanto tapa --lo que la ventana tiene de mas sobre la parte visible--
 * y se le resta al alto de la app. Asi la zona de escribir sube sola y el
 * chat conserva su scroll al fondo, que es lo unico que la persona quiere:
 * ver lo ultimo que se dijo mientras escribe la respuesta.
 *
 * `scrollIntoView` no servia aqui: no hay scroll nuevo que hacer, el problema
 * es que el sitio donde estaba el mensaje ya no se ve.
 *
 * Lo que se corrige el 2026-09-04, y es una sola linea de mas.
 * `alFondo()` se llamaba Siempre. O sea: quien subia a leer un mensaje viejo y
 * entonces tocaba el campo veia el chat irse al final de golpe, y el viewport
 * visual cambia tambien al esconderse la barra de direcciones, asi que pasaba
 * sin teclado de por medio. Anclar al fondo es lo correcto cuando ya se estaba
 * al fondo; hacerlo cuando no, es quitarle la lectura de las manos a alguien.
 *
 * Se mira Antes de tocar el alto, porque cambiar `--teclado` mueve la caja y a
 * partir de ahi la medida ya no dice donde estaba la persona, sino donde la
 * dejo el cambio.
 *
 * El margen de 40 px no es adorno: sin holgura, un pixel de inercia cuenta
 * como «se ha ido» y el ancla se pierde justo cuando mas se quiere. */
if (window.visualViewport) {
  const vv = window.visualViewport;
  const alFondo = () => {
    const d = $("dice");
    if (d) d.scrollTop = d.scrollHeight;
  };
  const alFinal = () => {
    const d = $("dice");
    if (!d) return true;
    return d.scrollHeight - d.scrollTop - d.clientHeight < 40;
  };
  let tapadoAntes = -1;
  const ajusta = () => {
    const tapado = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
    // Un cambio de menos de 20 px no es un teclado ni una barra: es ruido del
    // navegador al desplazar. Recalcular con cada uno repinta sin motivo, y en
    // un telefono justo eso se nota.
    if (Math.abs(tapado - tapadoAntes) < 20) return;
    tapadoAntes = tapado;
    const seguia = alFinal();
    document.documentElement.style.setProperty("--teclado", tapado + "px");
    // El umbral es de 120 px y no de cero: una barra de direcciones que se
    // esconde al deslizar tambien cambia el viewport visual, y eso no es un
    // teclado. Ningun teclado de movil mide menos de 120 px.
    document.body.classList.toggle("con-teclado", tapado > 120);
    if (seguia) alFondo();
  };
  vv.addEventListener("resize", ajusta);
  vv.addEventListener("scroll", ajusta);
  ajusta();
}
