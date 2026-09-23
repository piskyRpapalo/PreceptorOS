#!/usr/bin/env python3
"""Las siete lenguas que el producto habla además de inglés y castellano.

sistema: MVP · solo biblioteca estandar.

POR QUE UN FICHERO APARTE (2026-09-23). `textos.py` es «un solo diccionario,
dos columnas», y eso sigue siendo verdad para quien lo lee: las dos columnas
de origen viven allí, juntas. Estas siete son TRADUCCIONES de esas dos, y
meterlas en el mismo fichero lo habría llevado de 400 líneas a 1.800. Aquí
están las siete, y `textos.py` las funde en `TEXTOS` al importarse: para el
resto del producto no hay diferencia, `TEXTOS["fr"]` existe igual que
`TEXTOS["es"]`.

Las mismas claves y los mismos huecos `{...}` que la columna inglesa: lo
comprueba el caso 10 de `test_idioma.py`. Los números de las preguntas («1 o
2») no se traducen: son la gramática de `elegir`.

PROCEDENCIA. Traducidas por Claude (Opus 5.5) desde el inglés y el castellano
el 2026-09-23. Nadie con oído nativo las ha leído: mismo estado que las
lenguas de la web, `pendiente-revision-nativa`. El plural es el de «1 frente
a más de 1», que en ruso y en árabe es una aproximación declarada.
"""
from __future__ import annotations

REVISION = "pendiente-revision-nativa"

TEXTOS_MAS = {}

TEXTOS_MAS["fr"] = {
    "sabe_de_mi": "Ce que je sais de moi-même, sans aucune mémoire :",
    "bullet_campos": "  - un souvenir a 4 champs : quoi, pourquoi, où, appris",
    "bullet_ausencia": "  - l'absence s'écrit {ausente}, jamais laissée vide",
    "bullet_vive": "  - ma mémoire vivrait dans : {ruta}",
    "bullet_frontera": "  - rien ne quitte cette machine sauf si tu l'exportes",
    "crear_pregunta": "Créer ma mémoire maintenant ?  (tape le numéro : 1 ou 2)",
    "crear_si": "Oui, crée-la",
    "crear_no": "Non, pas encore",
    "nada_creado": "\nRien n'a été créé. Je ne garde aucune trace de cette session.",
    "creado": "\nCréé : {ruta}",
    "perfil_cabecera": "\n--- d'abord, deux questions qui ne sont pas des souvenirs ",
    "perfil_intro": (
        "Je sépare deux choses : qui tu es et où je suis (cette partie),\n"
        "et ce dont tu te souviens (tout le reste). Aucune réponse n'est\n"
        "obligatoire. Appuie sur Entrée et ça reste {ausente} — c'est aussi\n"
        "une réponse : elle dit que personne ne me l'a dit, au lieu que je fasse semblant.\n"),
    "perfil_device": "Où suis-je ?  (la machine sur laquelle je tourne, avec tes mots)  ",
    "perfil_name": "Comment dois-je t'appeler ?  ",
    "perfil_nota": ("({ausente} n'est pas une case vide : c'est une question à laquelle\n"
                    " personne n'a répondu. On ne perd rien à la laisser ainsi.)"),
    "recuerdo_cabecera": "\n--- maintenant un souvenir, un champ à la fois ",
    "recuerdo_intro": (
        "Un souvenir, ici, c'est simplement quelque chose qui t'est arrivé et\n"
        "que tu as jugé digne d'être gardé. Il n'a pas besoin d'être important.\n"),
    "recuerdo_ejemplos": (
        "  ex.   l'imprimante a enfin marché après avoir changé un câble\n"
        "        j'ai cassé la base de données et je l'ai récupérée d'une copie\n"
        "        quelqu'un m'a expliqué le DNS et cette fois j'ai compris\n"),
    "recuerdo_que": "Alors — que s'est-il passé ?  ",
    "cerebro_afinado": "Cerveau : copie affinée · {motivo}",
    "charla_cabecera": "\n--- conversation ",
    "charla_sin_motor": (
        "Il n'y a pas de moteur de conversation dans cette copie, donc je ne\n"
        "peux pas encore parler. Tout le reste marche : ta mémoire est entière sans moi.\n"),
    "charla_sin_binario": (
        "Le cerveau est sur cette machine, mais il n'y a rien ici pour le faire\n"
        "tourner. Installe {motor} et je pourrai parler. Tout le reste marche\n"
        "déjà sans lui.\n"),
    "charla_sin_modelo": (
        "Je peux faire tourner un cerveau, mais je n'en trouve aucun. Il devrait être dans\n"
        "  {ruta}\n"
        "Si tu l'as téléchargé ailleurs, déplace-le là — je ne fouille pas\n"
        "ton disque.\n"),
    "charla_donde": "Tu es à {peldano}. {prueba}",
    "charla_decision": (
        "Le cœur est fait. À partir d'ici tu choisis : aller droit à ton propre\n"
        "projet, ou atteindre une étape facultative. Les deux sont le chemin.\n"),
    "charla_como_salir": "(ligne vide pour sortir ; rien ne se perd)",
    "charla_bloqueado": (
        "J'ai arrêté ça : ça avait la forme de quelque chose qui brûle. La\n"
        "marque est dans le registre ; ce que ça disait, non."),
    "charla_callado": "Le moteur n'a rien rendu. C'est un fait, pas une réponse.",
    "charla_tarde": "Ça n'a pas fini à temps. {motivo}",
    "recuerdo_sin_que": ("Sans « quoi », il n'y a pas de souvenir. Rien d'écrit,\n"
                         "et rien de mal : reviens quand il y aura quelque chose."),
    "sin_motor": ("\nCette copie n'a pas de moteur de conversation installé. Je peux garder\n"
                  "et retrouver tes notes, mais je ne peux pas encore parler. Tout ce\n"
                  "qui suit marche sans lui.\n"
                  "Pour activer la conversation, installe le moteur indiqué dans\n"
                  "README → Requirements.\n"),
    "recuerdo_opcionales": (
        "\nLes trois suivants peuvent rester vides. Entrée les laisse à {ausente},\n"
        "et un souvenir avec des trous déclarés reste un souvenir — c'est plus\n"
        "honnête qu'un souvenir où j'aurais deviné ce que tu ne m'as pas dit.\n"),
    "recuerdo_porque": "Pourquoi ça compte pour toi ?  (Entrée = {ausente})  ",
    "recuerdo_donde": "Y a-t-il un fichier, une photo, une note qui l'appuie ?  (Entrée = {ausente})  ",
    "recuerdo_aprendido": "As-tu appris quelque chose que tu dirais à quelqu'un ?  (Entrée = pour plus tard)  ",
    "recuerdo_guardado": "\nEnregistré, exactement comme tu l'as écrit :",
    "recuerdo_vacio": "(vide, pour plus tard)",
    "palabra_recuerdo": "souvenir",
    "palabra_recuerdos": "souvenirs",
    "palabra_hueco": "trou déclaré",
    "palabra_huecos": "trous déclarés",
    "bucle_recuento": "\n{n} {nombre_r}. Trois, c'est un bon début — pas une obligation.",
    "otro_pregunta": "Ajouter un autre souvenir ?  (tape le numéro : 1 ou 2)",
    "otro_si": "Oui, encore un",
    "otro_no": "Non, ça suffit pour aujourd'hui",
    "enlace_pregunta": "\nDeux d'entre eux sont-ils liés ?  (tape le numéro : 1 ou 2)",
    "enlace_si": "Oui, deux le sont",
    "enlace_no": "Non, ils tiennent seuls",
    "enlace_desde": "depuis l'id :  ",
    "enlace_hasta": "vers l'id :  ",
    "enlace_como": "avec tes mots, comment ?  (Entrée = {ausente})  ",
    "enlace_guardado": "Lien enregistré.",
    "vista_tabla": "\n=== TABLEAU ",
    "vista_arbol": "\n=== ARBRE ",
    "vista_recuento": "\n=== DÉCOMPTE ",
    "cierre_cabecera": "\n--- clôture honnête ",
    "cierre_recuento": "J'ai {engrams} {nombre_r} et {huecos} {nombre_h}.",
    "cierre_viven": "Ils vivent dans {ruta}. Tu peux copier ce fichier et l'emporter.",
    "cierre_frontera": "Caviardage à la frontière : ",
    "cierre_frontera_ok": "prêt",
    "cierre_frontera_no": "NON DISPONIBLE — l'export est bloqué",
    "cierre_pregunta": "\nQuelle pièce veux-tu comprendre en premier ?  ",
    "cierre_intencion_why": "la prochaine chose que je veux apprendre",
    "cierre_intencion": "Enregistré comme intention. Il oriente la prochaine mission.",
    "sello_no_hay": ("Sceller l'état d'aujourd'hui n'est pas disponible : le module du "
                     "manifeste n'est pas là."),
    "sello_no_hay_2": "Ta mémoire est en sécurité quand même. Rien n'a été perdu.",
    "sello_intro": "Avant de partir : je peux sceller l'état de ta mémoire en ce moment.",
    "sello_intro_2": "Un sceau prouve que rien n'a changé, sans dire ce que ça dit.",
    "sello_pregunta": "Sceller aujourd'hui ?  (tape le numéro : 1 ou 2)",
    "sello_si": "Oui, scelle-le",
    "sello_no": "Pas maintenant — je peux le faire quand je veux",
    "sello_sellando": "Scellement.",
    "sello_no_sellado": "Non scellé. La mémoire continue de grandir.",
    "sello_escrito": "Scellé : {destino}",
    "sello_copia": ("Garde une copie ailleurs : un sceau à côté de ce qu'il "
                    "certifie se perd avec lui."),
    "final": "\nMission M2 terminée : ",
    "final_si": "oui",
    "final_no": "non — rien n'a été écrit",
    "m3_intro": ("Il y a une deuxième chose, et c'est un jeu. Six salles, "
                 "et un buste qui veut sortir d'un musée."),
    "m3_reanudar": ("Tu as laissé un musée à mi-chemin. Il est toujours là, "
                    "exactement où tu t'es arrêté."),
    "m3_pregunta": "Entrer dans l'Évasion du Musée ?",
    "m3_si": "oui, allons-y",
    "m3_no": "pas aujourd'hui",
    "m3_luego": ("Ça se garde. C'est un fichier, pas un rendez-vous : rien "
                 "là-dedans n'expire."),
    "rechazo": "{entrada!r} n'en fait pas partie. Tape le numéro : {numeros}.",
    "o": "ou",
    "estado_sin_esquema": ("Je n'ai pas encore de mémoire. Rien n'a été créé sur "
                           "cette machine. Je peux la créer maintenant, si tu le dis."),
    "sin_memoria_aun": ("Il n'y a pas encore de mémoire sur cette machine, donc il n'y a\n"
                        "rien à faire ici. Lance ceci et on la fait ensemble :\n"
                        "  python3 preceptoros.py\n"),
    "ritual_saludo": "\nD'abord, trois choses sur toi. Aucune n'est obligatoire.",
    "ritual_nombre": "Comment dois-je t'appeler ?  (Entrée pour {ausente})  ",
    "ritual_ritmo": "Rythme des réponses (0-9, Entrée pour {ausente})  ",
    "ritual_hecho": "C'est fait. Ce que tu m'as dit est dans ta mémoire, pas dans un fichier à moi.",
    "estado_vacia": ("Ma mémoire existe et elle est vide. 0 souvenir. "
                     "Rien ne manque : rien n'a encore été écrit."),
    "estado_con_datos": "{n} souvenirs, {l} liens",
    "estado_archivados": ", {a} archivés",
    "estado_cola": ". Tout ce qui s'affiche vient de ce que tu as écrit.",
}

TEXTOS_MAS["pt"] = {
    "sabe_de_mi": "O que sei de mim mesmo, sem memória nenhuma:",
    "bullet_campos": "  - uma recordação tem 4 campos: o quê, porquê, onde, aprendido",
    "bullet_ausencia": "  - a ausência escreve-se {ausente}, nunca fica em branco",
    "bullet_vive": "  - a minha memória viveria em: {ruta}",
    "bullet_frontera": "  - nada sai desta máquina a não ser que o exportes",
    "crear_pregunta": "Criar a minha memória agora?  (escreve o número: 1 ou 2)",
    "crear_si": "Sim, cria-a",
    "crear_no": "Não, ainda não",
    "nada_creado": "\nNada criado. Não guardo registo desta sessão.",
    "creado": "\nCriado: {ruta}",
    "perfil_cabecera": "\n--- primeiro, duas perguntas que não são recordações ",
    "perfil_intro": (
        "Guardo duas coisas separadas: quem és e onde estou (esta parte),\n"
        "e o que recordas (tudo o resto). Nenhuma resposta é\n"
        "obrigatória. Carrega em Enter e fica como {ausente} — que também é\n"
        "uma resposta: diz que ninguém mo disse, em vez de eu fingir.\n"),
    "perfil_device": "Onde estou?  (a máquina onde corro, nas tuas palavras)  ",
    "perfil_name": "Como te devo chamar?  ",
    "perfil_nota": ("({ausente} não é uma célula em branco: é uma pergunta a que ninguém\n"
                    " respondeu. Não se perde nada por a deixar assim.)"),
    "recuerdo_cabecera": "\n--- agora uma recordação, um campo de cada vez ",
    "recuerdo_intro": (
        "Uma recordação, aqui, é só algo que te aconteceu e que\n"
        "decidiste que valia a pena guardar. Não tem de ser importante.\n"),
    "recuerdo_ejemplos": (
        "  ex.   a impressora finalmente funcionou depois de trocar um cabo\n"
        "        estraguei a base de dados e recuperei-a de uma cópia\n"
        "        alguém me explicou o DNS e desta vez percebi\n"),
    "recuerdo_que": "Então — o que aconteceu?  ",
    "cerebro_afinado": "Cérebro: cópia afinada · {motivo}",
    "charla_cabecera": "\n--- a conversar ",
    "charla_sin_motor": (
        "Não há motor de conversa nesta cópia, por isso ainda não consigo\n"
        "falar. Tudo o resto funciona: a tua memória está inteira sem mim.\n"),
    "charla_sin_binario": (
        "O cérebro está nesta máquina, mas não há aqui nada para o correr.\n"
        "Instala {motor} e consigo falar. Tudo o resto já\n"
        "funciona sem ele.\n"),
    "charla_sin_modelo": (
        "Consigo correr um cérebro, mas não encontro nenhum. Devia estar em\n"
        "  {ruta}\n"
        "Se o descarregaste para outro sítio, move-o para lá — não ando a\n"
        "vasculhar o teu disco.\n"),
    "charla_donde": "Estás em {peldano}. {prueba}",
    "charla_decision": (
        "O núcleo está feito. A partir daqui escolhes: ir direto ao teu próprio\n"
        "projeto, ou alcançar um marco opcional. Os dois são o caminho.\n"),
    "charla_como_salir": "(linha vazia para sair; nada se perde)",
    "charla_bloqueado": (
        "Parei isso: tinha a forma de algo que queima. A\n"
        "marca está no registo; o que dizia, não."),
    "charla_callado": "O motor não devolveu nada. É um facto, não uma resposta.",
    "charla_tarde": "Não terminou a tempo. {motivo}",
    "recuerdo_sin_que": ("Sem um «o quê» não há recordação. Nada escrito,\n"
                         "e nada de mal: volta quando houver alguma coisa."),
    "sin_motor": ("\nEsta cópia não tem motor de conversa instalado. Consigo guardar\n"
                  "e recuperar as tuas notas, mas ainda não consigo falar. Tudo\n"
                  "o que está abaixo funciona sem ele.\n"
                  "Para ligar a conversa, instala o motor indicado em\n"
                  "README → Requirements.\n"),
    "recuerdo_opcionales": (
        "\nOs três seguintes podem ficar vazios. Enter deixa-os como {ausente},\n"
        "e uma recordação com lacunas declaradas continua a ser uma recordação — é mais\n"
        "honesta do que uma em que eu adivinhei o que não me disseste.\n"),
    "recuerdo_porque": "Porque é que isto te importa?  (Enter = {ausente})  ",
    "recuerdo_donde": "Há um ficheiro, uma foto, uma nota que o sustente?  (Enter = {ausente})  ",
    "recuerdo_aprendido": "Aprendeste algo que dirias a outra pessoa?  (Enter = para depois)  ",
    "recuerdo_guardado": "\nGuardado, exatamente como o escreveste:",
    "recuerdo_vacio": "(vazio, para depois)",
    "palabra_recuerdo": "recordação",
    "palabra_recuerdos": "recordações",
    "palabra_hueco": "lacuna declarada",
    "palabra_huecos": "lacunas declaradas",
    "bucle_recuento": "\n{n} {nombre_r}. Três é um bom começo — não uma obrigação.",
    "otro_pregunta": "Acrescentar outra recordação?  (escreve o número: 1 ou 2)",
    "otro_si": "Sim, mais uma",
    "otro_no": "Não, chega por hoje",
    "enlace_pregunta": "\nHá duas relacionadas entre si?  (escreve o número: 1 ou 2)",
    "enlace_si": "Sim, duas estão",
    "enlace_no": "Não, estão por si",
    "enlace_desde": "do id:  ",
    "enlace_hasta": "para o id:  ",
    "enlace_como": "nas tuas palavras, como?  (Enter = {ausente})  ",
    "enlace_guardado": "Ligação guardada.",
    "vista_tabla": "\n=== TABELA ",
    "vista_arbol": "\n=== ÁRVORE ",
    "vista_recuento": "\n=== CONTAGEM ",
    "cierre_cabecera": "\n--- fecho honesto ",
    "cierre_recuento": "Tenho {engrams} {nombre_r} e {huecos} {nombre_h}.",
    "cierre_viven": "Vivem em {ruta}. Podes copiar esse ficheiro e levá-lo contigo.",
    "cierre_frontera": "Rasura na fronteira: ",
    "cierre_frontera_ok": "pronta",
    "cierre_frontera_no": "INDISPONÍVEL — a exportação está bloqueada",
    "cierre_pregunta": "\nQue peça queres perceber primeiro?  ",
    "cierre_intencion_why": "a próxima coisa que quero aprender",
    "cierre_intencion": "Guardado como intenção. Orienta a próxima missão.",
    "sello_no_hay": ("Selar o estado de hoje não está disponível: o módulo do "
                     "manifesto não está aqui."),
    "sello_no_hay_2": "A tua memória está segura na mesma. Nada se perdeu.",
    "sello_intro": "Antes de ires: posso selar como está a tua memória agora mesmo.",
    "sello_intro_2": "Um selo prova que nada mudou, sem dizer o que diz.",
    "sello_pregunta": "Selar hoje?  (escreve o número: 1 ou 2)",
    "sello_si": "Sim, sela",
    "sello_no": "Agora não — posso fazê-lo quando quiser",
    "sello_sellando": "A selar.",
    "sello_no_sellado": "Não selado. A memória continua a crescer.",
    "sello_escrito": "Selado: {destino}",
    "sello_copia": ("Guarda uma cópia noutro sítio: um selo ao lado do que "
                    "certifica perde-se com ele."),
    "final": "\nMissão M2 concluída: ",
    "final_si": "sim",
    "final_no": "não — nada foi escrito",
    "m3_intro": ("Há uma segunda coisa, e é um jogo. Seis salas, "
                 "e um busto que quer sair de um museu."),
    "m3_reanudar": ("Deixaste um museu a meio. Continua lá, "
                    "exatamente onde paraste."),
    "m3_pregunta": "Entrar na Fuga do Museu?",
    "m3_si": "sim, vamos",
    "m3_no": "hoje não",
    "m3_luego": ("Guarda-se. É um ficheiro, não uma marcação: nada "
                 "ali expira."),
    "rechazo": "{entrada!r} não é uma delas. Escreve o número: {numeros}.",
    "o": "ou",
    "estado_sin_esquema": ("Ainda não tenho memória. Nada foi criado nesta "
                           "máquina. Posso criá-la agora, se disseres."),
    "sin_memoria_aun": ("Ainda não há memória nesta máquina, por isso não há\n"
                        "nada a fazer aqui. Corre isto e fazemo-la juntos:\n"
                        "  python3 preceptoros.py\n"),
    "ritual_saludo": "\nPrimeiro, três coisas sobre ti. Nenhuma é obrigatória.",
    "ritual_nombre": "Como te devo chamar?  (Enter para {ausente})  ",
    "ritual_ritmo": "Ritmo das respostas (0-9, Enter para {ausente})  ",
    "ritual_hecho": "Feito. O que me disseste está na tua memória, não num ficheiro meu.",
    "estado_vacia": ("A minha memória existe e está vazia. 0 recordações. "
                     "Não falta nada: ainda não se escreveu nada."),
    "estado_con_datos": "{n} recordações, {l} ligações",
    "estado_archivados": ", {a} arquivadas",
    "estado_cola": ". Tudo o que se vê vem do que tu escreveste.",
}

TEXTOS_MAS["it"] = {
    "sabe_de_mi": "Cosa so di me stesso, senza alcuna memoria:",
    "bullet_campos": "  - un ricordo ha 4 campi: cosa, perché, dove, imparato",
    "bullet_ausencia": "  - l'assenza si scrive {ausente}, mai lasciata vuota",
    "bullet_vive": "  - la mia memoria vivrebbe in: {ruta}",
    "bullet_frontera": "  - niente lascia questa macchina a meno che tu non lo esporti",
    "crear_pregunta": "Creare la mia memoria adesso?  (scrivi il numero: 1 o 2)",
    "crear_si": "Sì, creala",
    "crear_no": "No, non ancora",
    "nada_creado": "\nNiente creato. Non tengo traccia di questa sessione.",
    "creado": "\nCreato: {ruta}",
    "perfil_cabecera": "\n--- prima, due domande che non sono ricordi ",
    "perfil_intro": (
        "Tengo separate due cose: chi sei e dove sono (questa parte),\n"
        "e cosa ricordi (tutto il resto). Nessuna risposta è\n"
        "obbligatoria. Premi Invio e resta {ausente} — che è anch'essa\n"
        "una risposta: dice che nessuno me l'ha detto, invece di fingere.\n"),
    "perfil_device": "Dove sono?  (la macchina su cui giro, con parole tue)  ",
    "perfil_name": "Come devo chiamarti?  ",
    "perfil_nota": ("({ausente} non è una cella vuota: è una domanda a cui nessuno\n"
                    " ha risposto. Lasciandola così non si perde nulla.)"),
    "recuerdo_cabecera": "\n--- ora un ricordo, un campo alla volta ",
    "recuerdo_intro": (
        "Un ricordo, qui, è solo qualcosa che ti è successo e che hai\n"
        "deciso valesse la pena tenere. Non deve essere importante.\n"),
    "recuerdo_ejemplos": (
        "  es.   la stampante ha finalmente funzionato dopo aver cambiato un cavo\n"
        "        ho rotto il database e l'ho recuperato da una copia\n"
        "        qualcuno mi ha spiegato il DNS e stavolta l'ho capito\n"),
    "recuerdo_que": "Allora — cos'è successo?  ",
    "cerebro_afinado": "Cervello: copia affinata · {motivo}",
    "charla_cabecera": "\n--- conversazione ",
    "charla_sin_motor": (
        "In questa copia non c'è un motore di conversazione, quindi non posso\n"
        "ancora parlare. Tutto il resto funziona: la tua memoria è intera senza di me.\n"),
    "charla_sin_binario": (
        "Il cervello è su questa macchina, ma qui non c'è niente per farlo\n"
        "girare. Installa {motor} e potrò parlare. Tutto il resto funziona\n"
        "già senza.\n"),
    "charla_sin_modelo": (
        "Posso far girare un cervello, ma non ne trovo nessuno. Dovrebbe essere in\n"
        "  {ruta}\n"
        "Se l'hai scaricato altrove, spostalo lì — non vado a frugare\n"
        "nel tuo disco.\n"),
    "charla_donde": "Sei a {peldano}. {prueba}",
    "charla_decision": (
        "Il nucleo è fatto. Da qui scegli tu: andare dritto al tuo\n"
        "progetto, o raggiungere una tappa facoltativa. Entrambi sono il cammino.\n"),
    "charla_como_salir": "(riga vuota per uscire; non si perde nulla)",
    "charla_bloqueado": (
        "L'ho fermato: aveva la forma di qualcosa che brucia. Il\n"
        "segno è nel registro; quello che diceva, no."),
    "charla_callado": "Il motore non ha restituito nulla. È un fatto, non una risposta.",
    "charla_tarde": "Non ha finito in tempo. {motivo}",
    "recuerdo_sin_que": ("Senza un «cosa» non c'è ricordo. Niente scritto,\n"
                         "e niente di male: torna quando ci sarà qualcosa."),
    "sin_motor": ("\nQuesta copia non ha un motore di conversazione installato. Posso tenere\n"
                  "e ritrovare le tue note, ma non posso ancora parlare. Tutto\n"
                  "quello che segue funziona senza.\n"
                  "Per attivare la conversazione, installa il motore indicato in\n"
                  "README → Requirements.\n"),
    "recuerdo_opcionales": (
        "\nI prossimi tre possono restare vuoti. Invio li lascia a {ausente},\n"
        "e un ricordo con lacune dichiarate è comunque un ricordo — è più\n"
        "onesto di uno in cui avessi indovinato le parti che non mi hai detto.\n"),
    "recuerdo_porque": "Perché ti importa?  (Invio = {ausente})  ",
    "recuerdo_donde": "C'è un file, una foto, una nota che lo sostenga?  (Invio = {ausente})  ",
    "recuerdo_aprendido": "Hai imparato qualcosa che diresti a qualcun altro?  (Invio = per dopo)  ",
    "recuerdo_guardado": "\nSalvato, esattamente come l'hai scritto:",
    "recuerdo_vacio": "(vuoto, per dopo)",
    "palabra_recuerdo": "ricordo",
    "palabra_recuerdos": "ricordi",
    "palabra_hueco": "lacuna dichiarata",
    "palabra_huecos": "lacune dichiarate",
    "bucle_recuento": "\n{n} {nombre_r}. Tre è un buon inizio — non un obbligo.",
    "otro_pregunta": "Aggiungere un altro ricordo?  (scrivi il numero: 1 o 2)",
    "otro_si": "Sì, ancora uno",
    "otro_no": "No, basta per oggi",
    "enlace_pregunta": "\nDue di questi sono collegati?  (scrivi il numero: 1 o 2)",
    "enlace_si": "Sì, due lo sono",
    "enlace_no": "No, stanno da soli",
    "enlace_desde": "dall'id:  ",
    "enlace_hasta": "all'id:  ",
    "enlace_como": "con parole tue, come?  (Invio = {ausente})  ",
    "enlace_guardado": "Collegamento salvato.",
    "vista_tabla": "\n=== TABELLA ",
    "vista_arbol": "\n=== ALBERO ",
    "vista_recuento": "\n=== CONTEGGIO ",
    "cierre_cabecera": "\n--- chiusura onesta ",
    "cierre_recuento": "Ho {engrams} {nombre_r} e {huecos} {nombre_h}.",
    "cierre_viven": "Vivono in {ruta}. Puoi copiare quel file e portarlo con te.",
    "cierre_frontera": "Oscuramento alla frontiera: ",
    "cierre_frontera_ok": "pronto",
    "cierre_frontera_no": "NON DISPONIBILE — l'esportazione è bloccata",
    "cierre_pregunta": "\nQuale pezzo vuoi capire per primo?  ",
    "cierre_intencion_why": "la prossima cosa che voglio imparare",
    "cierre_intencion": "Salvato come intenzione. Orienta la prossima missione.",
    "sello_no_hay": ("Sigillare lo stato di oggi non è disponibile: il modulo del "
                     "manifesto non c'è."),
    "sello_no_hay_2": "La tua memoria è comunque al sicuro. Non si è perso nulla.",
    "sello_intro": "Prima di andare: posso sigillare com'è la tua memoria in questo momento.",
    "sello_intro_2": "Un sigillo prova che nulla è cambiato, senza dire cosa dice.",
    "sello_pregunta": "Sigillare oggi?  (scrivi il numero: 1 o 2)",
    "sello_si": "Sì, sigillalo",
    "sello_no": "Non ora — posso farlo quando voglio",
    "sello_sellando": "Sigillo in corso.",
    "sello_no_sellado": "Non sigillato. La memoria continua a crescere.",
    "sello_escrito": "Sigillato: {destino}",
    "sello_copia": ("Tieni una copia altrove: un sigillo accanto a ciò che "
                    "certifica si perde con esso."),
    "final": "\nMissione M2 completata: ",
    "final_si": "sì",
    "final_no": "no — non è stato scritto nulla",
    "m3_intro": ("C'è una seconda cosa, ed è un gioco. Sei sale, "
                 "e un busto che vuole uscire da un museo."),
    "m3_reanudar": ("Hai lasciato un museo a metà. È ancora lì, "
                    "esattamente dove ti sei fermato."),
    "m3_pregunta": "Entrare nella Fuga dal Museo?",
    "m3_si": "sì, andiamo",
    "m3_no": "non oggi",
    "m3_luego": ("Si conserva. È un file, non un appuntamento: niente "
                 "lì dentro scade."),
    "rechazo": "{entrada!r} non è tra queste. Scrivi il numero: {numeros}.",
    "o": "o",
    "estado_sin_esquema": ("Non ho ancora una memoria. Non è stato creato nulla su "
                           "questa macchina. Posso crearla ora, se me lo dici."),
    "sin_memoria_aun": ("Non c'è ancora una memoria su questa macchina, quindi non c'è\n"
                        "niente da fare qui. Esegui questo e la facciamo insieme:\n"
                        "  python3 preceptoros.py\n"),
    "ritual_saludo": "\nPrima, tre cose su di te. Nessuna è obbligatoria.",
    "ritual_nombre": "Come devo chiamarti?  (Invio per {ausente})  ",
    "ritual_ritmo": "Ritmo delle risposte (0-9, Invio per {ausente})  ",
    "ritual_hecho": "Fatto. Quello che mi hai detto è nella tua memoria, non in un mio file.",
    "estado_vacia": ("La mia memoria esiste ed è vuota. 0 ricordi. "
                     "Non manca nulla: non è ancora stato scritto niente."),
    "estado_con_datos": "{n} ricordi, {l} collegamenti",
    "estado_archivados": ", {a} archiviati",
    "estado_cola": ". Tutto ciò che si vede viene da quello che hai scritto tu.",
}

TEXTOS_MAS["de"] = {
    "sabe_de_mi": "Was ich über mich selbst weiß, ganz ohne Gedächtnis:",
    "bullet_campos": "  - eine Erinnerung hat 4 Felder: was, warum, wo, gelernt",
    "bullet_ausencia": "  - Fehlendes wird als {ausente} geschrieben, nie leer gelassen",
    "bullet_vive": "  - mein Gedächtnis würde hier leben: {ruta}",
    "bullet_frontera": "  - nichts verlässt diese Maschine, außer du exportierst es",
    "crear_pregunta": "Mein Gedächtnis jetzt anlegen?  (tippe die Zahl: 1 oder 2)",
    "crear_si": "Ja, leg es an",
    "crear_no": "Nein, noch nicht",
    "nada_creado": "\nNichts angelegt. Ich behalte keine Spur dieser Sitzung.",
    "creado": "\nAngelegt: {ruta}",
    "perfil_cabecera": "\n--- zuerst zwei Fragen, die keine Erinnerungen sind ",
    "perfil_intro": (
        "Ich halte zwei Dinge getrennt: wer du bist und wo ich bin (dieser Teil),\n"
        "und woran du dich erinnerst (alles danach). Keine Antwort ist\n"
        "Pflicht. Drück Enter, und es bleibt {ausente} — das ist auch\n"
        "eine Antwort: Sie sagt, dass es mir niemand gesagt hat, statt dass ich so tue.\n"),
    "perfil_device": "Wo bin ich?  (die Maschine, auf der ich laufe, in deinen Worten)  ",
    "perfil_name": "Wie soll ich dich nennen?  ",
    "perfil_nota": ("({ausente} ist keine leere Zelle: Es ist eine Frage, die niemand\n"
                    " beantwortet hat. Man verliert nichts, wenn man sie so lässt.)"),
    "recuerdo_cabecera": "\n--- jetzt eine Erinnerung, ein Feld nach dem anderen ",
    "recuerdo_intro": (
        "Eine Erinnerung ist hier einfach etwas, das dir passiert ist und von dem du\n"
        "entschieden hast, dass es sich lohnt, es zu behalten. Es muss nicht wichtig sein.\n"),
    "recuerdo_ejemplos": (
        "  z. B. der Drucker ging endlich, nachdem ich ein Kabel getauscht hatte\n"
        "        ich habe die Datenbank kaputt gemacht und aus einer Kopie zurückgeholt\n"
        "        jemand hat mir DNS erklärt, und diesmal habe ich es verstanden\n"),
    "recuerdo_que": "Also — was ist passiert?  ",
    "cerebro_afinado": "Gehirn: feinabgestimmte Kopie · {motivo}",
    "charla_cabecera": "\n--- im Gespräch ",
    "charla_sin_motor": (
        "In dieser Kopie gibt es keine Gesprächs-Engine, also kann ich noch\n"
        "nicht sprechen. Alles andere funktioniert: Dein Gedächtnis ist ohne mich vollständig.\n"),
    "charla_sin_binario": (
        "Das Gehirn ist auf dieser Maschine, aber hier gibt es nichts, um es\n"
        "auszuführen. Installiere {motor}, dann kann ich sprechen. Alles andere\n"
        "funktioniert schon ohne.\n"),
    "charla_sin_modelo": (
        "Ich kann ein Gehirn ausführen, finde aber keins. Es sollte hier liegen:\n"
        "  {ruta}\n"
        "Wenn du es woanders heruntergeladen hast, verschieb es dorthin — ich\n"
        "durchsuche deine Festplatte nicht.\n"),
    "charla_donde": "Du bist bei {peldano}. {prueba}",
    "charla_decision": (
        "Der Kern ist fertig. Ab hier entscheidest du: direkt zu deinem eigenen\n"
        "Projekt oder zu einem optionalen Meilenstein. Beides ist der Weg.\n"),
    "charla_como_salir": "(leere Zeile zum Verlassen; nichts geht verloren)",
    "charla_bloqueado": (
        "Das habe ich gestoppt: Es hatte die Form von etwas, das brennt. Die\n"
        "Markierung steht im Protokoll; was es sagte, nicht."),
    "charla_callado": "Die Engine hat nichts zurückgegeben. Das ist eine Tatsache, keine Antwort.",
    "charla_tarde": "Es wurde nicht rechtzeitig fertig. {motivo}",
    "recuerdo_sin_que": ("Ohne ein „was“ gibt es keine Erinnerung. Nichts geschrieben,\n"
                         "und nichts falsch: Komm wieder, wenn es etwas gibt."),
    "sin_motor": ("\nIn dieser Kopie ist keine Gesprächs-Engine installiert. Ich kann deine\n"
                  "Notizen behalten und wiederfinden, aber noch nicht sprechen. Alles\n"
                  "Folgende funktioniert ohne sie.\n"
                  "Um das Gespräch einzuschalten, installiere die Engine aus\n"
                  "README → Requirements.\n"),
    "recuerdo_opcionales": (
        "\nDie nächsten drei dürfen leer bleiben. Enter lässt sie bei {ausente},\n"
        "und eine Erinnerung mit erklärten Lücken ist trotzdem eine Erinnerung — sie ist\n"
        "ehrlicher als eine, in der ich erraten hätte, was du mir nicht gesagt hast.\n"),
    "recuerdo_porque": "Warum ist es dir wichtig?  (Enter = {ausente})  ",
    "recuerdo_donde": "Gibt es eine Datei, ein Foto, eine Notiz, die es belegt?  (Enter = {ausente})  ",
    "recuerdo_aprendido": "Hast du etwas gelernt, das du jemand anderem erzählen würdest?  (Enter = für später)  ",
    "recuerdo_guardado": "\nGespeichert, genau so, wie du es geschrieben hast:",
    "recuerdo_vacio": "(leer, für später)",
    "palabra_recuerdo": "Erinnerung",
    "palabra_recuerdos": "Erinnerungen",
    "palabra_hueco": "erklärte Lücke",
    "palabra_huecos": "erklärte Lücken",
    "bucle_recuento": "\n{n} {nombre_r}. Drei sind ein guter Anfang — keine Pflicht.",
    "otro_pregunta": "Noch eine Erinnerung hinzufügen?  (tippe die Zahl: 1 oder 2)",
    "otro_si": "Ja, noch eine",
    "otro_no": "Nein, genug für heute",
    "enlace_pregunta": "\nHängen zwei davon zusammen?  (tippe die Zahl: 1 oder 2)",
    "enlace_si": "Ja, zwei davon",
    "enlace_no": "Nein, sie stehen für sich",
    "enlace_desde": "von ID:  ",
    "enlace_hasta": "zu ID:  ",
    "enlace_como": "in deinen Worten, wie?  (Enter = {ausente})  ",
    "enlace_guardado": "Verknüpfung gespeichert.",
    "vista_tabla": "\n=== TABELLE ",
    "vista_arbol": "\n=== BAUM ",
    "vista_recuento": "\n=== ZÄHLUNG ",
    "cierre_cabecera": "\n--- ehrlicher Abschluss ",
    "cierre_recuento": "Ich habe {engrams} {nombre_r} und {huecos} {nombre_h}.",
    "cierre_viven": "Sie leben in {ruta}. Du kannst diese Datei kopieren und mitnehmen.",
    "cierre_frontera": "Schwärzung an der Grenze: ",
    "cierre_frontera_ok": "bereit",
    "cierre_frontera_no": "NICHT VERFÜGBAR — der Export ist gesperrt",
    "cierre_pregunta": "\nWelches Stück willst du zuerst verstehen?  ",
    "cierre_intencion_why": "das Nächste, was ich lernen will",
    "cierre_intencion": "Als Absicht gespeichert. Es gibt der nächsten Mission die Richtung.",
    "sello_no_hay": ("Den heutigen Stand zu versiegeln ist nicht verfügbar: Das "
                     "Manifest-Modul ist nicht da."),
    "sello_no_hay_2": "Dein Gedächtnis ist trotzdem sicher. Nichts ging verloren.",
    "sello_intro": "Bevor du gehst: Ich kann versiegeln, wie dein Gedächtnis gerade aussieht.",
    "sello_intro_2": "Ein Siegel beweist, dass sich nichts geändert hat, ohne zu sagen, was drinsteht.",
    "sello_pregunta": "Heute versiegeln?  (tippe die Zahl: 1 oder 2)",
    "sello_si": "Ja, versiegeln",
    "sello_no": "Jetzt nicht — das geht jederzeit",
    "sello_sellando": "Wird versiegelt.",
    "sello_no_sellado": "Nicht versiegelt. Das Gedächtnis wächst weiter.",
    "sello_escrito": "Versiegelt: {destino}",
    "sello_copia": ("Bewahre eine Kopie woanders auf: Ein Siegel neben dem, was es "
                    "bestätigt, geht mit ihm verloren."),
    "final": "\nMission M2 abgeschlossen: ",
    "final_si": "ja",
    "final_no": "nein — es wurde nichts geschrieben",
    "m3_intro": ("Es gibt noch etwas, und es ist ein Spiel. Sechs Säle "
                 "und eine Büste, die aus einem Museum hinauswill."),
    "m3_reanudar": ("Du hast ein Museum halb verlassen. Es ist noch da, "
                    "genau dort, wo du aufgehört hast."),
    "m3_pregunta": "In die Flucht aus dem Museum gehen?",
    "m3_si": "ja, los",
    "m3_no": "heute nicht",
    "m3_luego": ("Es bleibt. Es ist eine Datei, kein Termin: Nichts "
                 "darin läuft ab."),
    "rechazo": "{entrada!r} ist keine davon. Tippe die Zahl: {numeros}.",
    "o": "oder",
    "estado_sin_esquema": ("Ich habe noch kein Gedächtnis. Auf dieser Maschine wurde "
                           "nichts angelegt. Ich kann es jetzt anlegen, wenn du willst."),
    "sin_memoria_aun": ("Auf dieser Maschine gibt es noch kein Gedächtnis, also gibt es\n"
                        "hier nichts zu tun. Führ das aus, und wir legen es zusammen an:\n"
                        "  python3 preceptoros.py\n"),
    "ritual_saludo": "\nZuerst drei Dinge über dich. Keins ist Pflicht.",
    "ritual_nombre": "Wie soll ich dich nennen?  (Enter für {ausente})  ",
    "ritual_ritmo": "Tempo der Antworten (0-9, Enter für {ausente})  ",
    "ritual_hecho": "Fertig. Was du mir gesagt hast, steht in deinem Gedächtnis, nicht in einer Datei von mir.",
    "estado_vacia": ("Mein Gedächtnis existiert und ist leer. 0 Erinnerungen. "
                     "Es fehlt nichts: Es wurde noch nichts geschrieben."),
    "estado_con_datos": "{n} Erinnerungen, {l} Verknüpfungen",
    "estado_archivados": ", {a} archiviert",
    "estado_cola": ". Alles, was du siehst, kommt aus dem, was du geschrieben hast.",
}

TEXTOS_MAS["ru"] = {
    "sabe_de_mi": "Что я знаю о себе, вообще без памяти:",
    "bullet_campos": "  - у воспоминания 4 поля: что, почему, где, чему научился",
    "bullet_ausencia": "  - отсутствие пишется как {ausente}, никогда не остаётся пустым",
    "bullet_vive": "  - моя память жила бы здесь: {ruta}",
    "bullet_frontera": "  - ничто не покидает эту машину, если ты это не экспортируешь",
    "crear_pregunta": "Создать мою память сейчас?  (введи номер: 1 или 2)",
    "crear_si": "Да, создай",
    "crear_no": "Нет, пока нет",
    "nada_creado": "\nНичего не создано. Я не храню следов этой сессии.",
    "creado": "\nСоздано: {ruta}",
    "perfil_cabecera": "\n--- сначала два вопроса, которые не являются воспоминаниями ",
    "perfil_intro": (
        "Я держу две вещи раздельно: кто ты и где я (эта часть),\n"
        "и что ты помнишь (всё остальное). Ни один ответ не\n"
        "обязателен. Нажми Enter, и останется {ausente} — это тоже\n"
        "ответ: он говорит, что мне никто не сказал, вместо того чтобы я притворялся.\n"),
    "perfil_device": "Где я?  (машина, на которой я работаю, своими словами)  ",
    "perfil_name": "Как мне тебя называть?  ",
    "perfil_nota": ("({ausente} — не пустая ячейка: это вопрос, на который никто\n"
                    " не ответил. Если оставить так, ничего не потеряется.)"),
    "recuerdo_cabecera": "\n--- теперь воспоминание, по одному полю ",
    "recuerdo_intro": (
        "Воспоминание здесь — это просто то, что с тобой случилось и что ты\n"
        "решил стоит сохранить. Оно не обязано быть важным.\n"),
    "recuerdo_ejemplos": (
        "  напр. принтер наконец заработал после замены одного кабеля\n"
        "        я сломал базу данных и восстановил её из копии\n"
        "        мне объяснили DNS, и на этот раз я понял\n"),
    "recuerdo_que": "Итак — что случилось?  ",
    "cerebro_afinado": "Мозг: дообученная копия · {motivo}",
    "charla_cabecera": "\n--- разговор ",
    "charla_sin_motor": (
        "В этой копии нет движка для разговора, поэтому я пока не могу\n"
        "говорить. Всё остальное работает: твоя память цела и без меня.\n"),
    "charla_sin_binario": (
        "Мозг есть на этой машине, но здесь нечем его запустить.\n"
        "Установи {motor}, и я смогу говорить. Всё остальное уже\n"
        "работает без него.\n"),
    "charla_sin_modelo": (
        "Я могу запустить мозг, но не нахожу ни одного. Он должен быть здесь:\n"
        "  {ruta}\n"
        "Если ты скачал его в другое место, перенеси его туда — я не\n"
        "обыскиваю твой диск.\n"),
    "charla_donde": "Ты на {peldano}. {prueba}",
    "charla_decision": (
        "Ядро готово. Дальше выбираешь ты: сразу к своему\n"
        "проекту или к необязательному рубежу. Оба варианта — это путь.\n"),
    "charla_como_salir": "(пустая строка — выйти; ничего не теряется)",
    "charla_bloqueado": (
        "Я это остановил: оно было похоже на что-то, что сжигает. Отметка\n"
        "есть в журнале; то, что там было сказано, — нет."),
    "charla_callado": "Движок ничего не вернул. Это факт, а не ответ.",
    "charla_tarde": "Не успело закончиться вовремя. {motivo}",
    "recuerdo_sin_que": ("Без «что» нет воспоминания. Ничего не записано,\n"
                         "и ничего страшного: возвращайся, когда что-то будет."),
    "sin_motor": ("\nВ этой копии не установлен движок для разговора. Я могу хранить\n"
                  "и находить твои заметки, но пока не могу говорить. Всё,\n"
                  "что ниже, работает без него.\n"
                  "Чтобы включить разговор, установи движок, указанный в\n"
                  "README → Requirements.\n"),
    "recuerdo_opcionales": (
        "\nСледующие три можно оставить пустыми. Enter оставит их как {ausente},\n"
        "и воспоминание с объявленными пробелами — всё равно воспоминание, оно\n"
        "честнее того, где я угадал бы то, чего ты мне не сказал.\n"),
    "recuerdo_porque": "Почему это важно для тебя?  (Enter = {ausente})  ",
    "recuerdo_donde": "Есть файл, фото или заметка, которые это подтверждают?  (Enter = {ausente})  ",
    "recuerdo_aprendido": "Ты научился чему-то, что рассказал бы другому?  (Enter = на потом)  ",
    "recuerdo_guardado": "\nСохранено точно так, как ты написал:",
    "recuerdo_vacio": "(пусто, на потом)",
    "palabra_recuerdo": "воспоминание",
    "palabra_recuerdos": "воспоминаний",
    "palabra_hueco": "объявленный пробел",
    "palabra_huecos": "объявленных пробелов",
    "bucle_recuento": "\n{n} {nombre_r}. Три — хорошее начало, но не обязательство.",
    "otro_pregunta": "Добавить ещё одно воспоминание?  (введи номер: 1 или 2)",
    "otro_si": "Да, ещё одно",
    "otro_no": "Нет, на сегодня хватит",
    "enlace_pregunta": "\nСвязаны ли два из них?  (введи номер: 1 или 2)",
    "enlace_si": "Да, два связаны",
    "enlace_no": "Нет, они сами по себе",
    "enlace_desde": "от id:  ",
    "enlace_hasta": "к id:  ",
    "enlace_como": "своими словами, как?  (Enter = {ausente})  ",
    "enlace_guardado": "Связь сохранена.",
    "vista_tabla": "\n=== ТАБЛИЦА ",
    "vista_arbol": "\n=== ДЕРЕВО ",
    "vista_recuento": "\n=== СЧЁТ ",
    "cierre_cabecera": "\n--- честное завершение ",
    "cierre_recuento": "У меня {engrams} {nombre_r} и {huecos} {nombre_h}.",
    "cierre_viven": "Они хранятся в {ruta}. Можешь скопировать этот файл и забрать с собой.",
    "cierre_frontera": "Вычёркивание на границе: ",
    "cierre_frontera_ok": "готово",
    "cierre_frontera_no": "НЕДОСТУПНО — экспорт заблокирован",
    "cierre_pregunta": "\nКакую часть ты хочешь понять первой?  ",
    "cierre_intencion_why": "следующее, чему я хочу научиться",
    "cierre_intencion": "Сохранено как намерение. Оно направляет следующую миссию.",
    "sello_no_hay": ("Запечатать сегодняшнее состояние нельзя: модуля "
                     "манифеста здесь нет."),
    "sello_no_hay_2": "Твоя память всё равно в безопасности. Ничего не потеряно.",
    "sello_intro": "Прежде чем уйти: я могу запечатать, как твоя память выглядит прямо сейчас.",
    "sello_intro_2": "Печать доказывает, что ничего не изменилось, не раскрывая содержимого.",
    "sello_pregunta": "Запечатать сегодня?  (введи номер: 1 или 2)",
    "sello_si": "Да, запечатай",
    "sello_no": "Не сейчас — это можно сделать в любой момент",
    "sello_sellando": "Запечатываю.",
    "sello_no_sellado": "Не запечатано. Память продолжает расти.",
    "sello_escrito": "Запечатано: {destino}",
    "sello_copia": ("Храни копию где-то ещё: печать рядом с тем, что она "
                    "удостоверяет, теряется вместе с ним."),
    "final": "\nМиссия M2 завершена: ",
    "final_si": "да",
    "final_no": "нет — ничего не записано",
    "m3_intro": ("Есть и вторая вещь, и это игра. Шесть залов "
                 "и бюст, который хочет выбраться из музея."),
    "m3_reanudar": ("Ты оставил музей на полпути. Он всё ещё там, "
                    "ровно там, где ты остановился."),
    "m3_pregunta": "Войти в Побег из музея?",
    "m3_si": "да, пошли",
    "m3_no": "не сегодня",
    "m3_luego": ("Это подождёт. Это файл, а не встреча: ничего "
                 "там не истекает."),
    "rechazo": "{entrada!r} — не из них. Введи номер: {numeros}.",
    "o": "или",
    "estado_sin_esquema": ("У меня пока нет памяти. На этой машине ничего не "
                           "создано. Могу создать её сейчас, если скажешь."),
    "sin_memoria_aun": ("На этой машине пока нет памяти, так что здесь\n"
                        "нечего делать. Запусти это, и мы создадим её вместе:\n"
                        "  python3 preceptoros.py\n"),
    "ritual_saludo": "\nСначала три вещи о тебе. Ни одна не обязательна.",
    "ritual_nombre": "Как мне тебя называть?  (Enter — {ausente})  ",
    "ritual_ritmo": "Темп ответов (0-9, Enter — {ausente})  ",
    "ritual_hecho": "Готово. То, что ты мне сказал, — в твоей памяти, а не в моём файле.",
    "estado_vacia": ("Моя память существует и пуста. 0 воспоминаний. "
                     "Ничего не упущено: просто ещё ничего не записано."),
    "estado_con_datos": "{n} воспоминаний, {l} связей",
    "estado_archivados": ", {a} в архиве",
    "estado_cola": ". Всё, что видно, — из того, что написал ты.",
}

TEXTOS_MAS["el"] = {
    "sabe_de_mi": "Τι ξέρω για τον εαυτό μου, χωρίς καθόλου μνήμη:",
    "bullet_campos": "  - μια ανάμνηση έχει 4 πεδία: τι, γιατί, πού, τι έμαθα",
    "bullet_ausencia": "  - η απουσία γράφεται {ausente}, ποτέ δεν μένει κενή",
    "bullet_vive": "  - η μνήμη μου θα ζούσε εδώ: {ruta}",
    "bullet_frontera": "  - τίποτα δεν φεύγει από αυτό το μηχάνημα αν δεν το εξαγάγεις",
    "crear_pregunta": "Να δημιουργήσω τη μνήμη μου τώρα;  (γράψε τον αριθμό: 1 ή 2)",
    "crear_si": "Ναι, δημιούργησέ τη",
    "crear_no": "Όχι, ακόμη όχι",
    "nada_creado": "\nΔεν δημιουργήθηκε τίποτα. Δεν κρατώ ίχνος αυτής της συνεδρίας.",
    "creado": "\nΔημιουργήθηκε: {ruta}",
    "perfil_cabecera": "\n--- πρώτα, δύο ερωτήσεις που δεν είναι αναμνήσεις ",
    "perfil_intro": (
        "Κρατώ δύο πράγματα χωριστά: ποιος είσαι και πού είμαι (αυτό το μέρος),\n"
        "και τι θυμάσαι (όλα τα υπόλοιπα). Καμία απάντηση δεν είναι\n"
        "υποχρεωτική. Πάτα Enter και μένει {ausente} — που είναι κι αυτό\n"
        "απάντηση: λέει ότι δεν μου το είπε κανείς, αντί να προσποιούμαι.\n"),
    "perfil_device": "Πού είμαι;  (το μηχάνημα όπου τρέχω, με δικά σου λόγια)  ",
    "perfil_name": "Πώς να σε λέω;  ",
    "perfil_nota": ("(Το {ausente} δεν είναι κενό κελί: είναι μια ερώτηση που κανείς\n"
                    " δεν απάντησε. Δεν χάνεται τίποτα αν μείνει έτσι.)"),
    "recuerdo_cabecera": "\n--- τώρα μια ανάμνηση, ένα πεδίο τη φορά ",
    "recuerdo_intro": (
        "Ανάμνηση εδώ είναι απλώς κάτι που σου συνέβη και που\n"
        "αποφάσισες ότι αξίζει να κρατηθεί. Δεν χρειάζεται να είναι σημαντικό.\n"),
    "recuerdo_ejemplos": (
        "  π.χ.  ο εκτυπωτής δούλεψε επιτέλους όταν άλλαξα ένα καλώδιο\n"
        "        χάλασα τη βάση δεδομένων και την πήρα πίσω από αντίγραφο\n"
        "        κάποιος μου εξήγησε το DNS και αυτή τη φορά το κατάλαβα\n"),
    "recuerdo_que": "Λοιπόν — τι έγινε;  ",
    "cerebro_afinado": "Εγκέφαλος: ρυθμισμένο αντίγραφο · {motivo}",
    "charla_cabecera": "\n--- συζήτηση ",
    "charla_sin_motor": (
        "Σε αυτό το αντίγραφο δεν υπάρχει μηχανή συζήτησης, οπότε δεν μπορώ\n"
        "ακόμη να μιλήσω. Όλα τα άλλα λειτουργούν: η μνήμη σου είναι ολόκληρη χωρίς εμένα.\n"),
    "charla_sin_binario": (
        "Ο εγκέφαλος είναι σε αυτό το μηχάνημα, αλλά δεν υπάρχει εδώ τίποτα για να\n"
        "τρέξει. Εγκατάστησε το {motor} και θα μπορώ να μιλήσω. Όλα τα άλλα\n"
        "λειτουργούν ήδη χωρίς αυτό.\n"),
    "charla_sin_modelo": (
        "Μπορώ να τρέξω έναν εγκέφαλο, αλλά δεν βρίσκω κανέναν. Θα έπρεπε να είναι στο\n"
        "  {ruta}\n"
        "Αν τον κατέβασες αλλού, μετάφερέ τον εκεί — δεν ψάχνω\n"
        "τον δίσκο σου.\n"),
    "charla_donde": "Βρίσκεσαι στο {peldano}. {prueba}",
    "charla_decision": (
        "Ο πυρήνας έγινε. Από εδώ διαλέγεις: κατευθείαν στο δικό σου\n"
        "έργο, ή σε ένα προαιρετικό ορόσημο. Και τα δύο είναι ο δρόμος.\n"),
    "charla_como_salir": "(κενή γραμμή για έξοδο· τίποτα δεν χάνεται)",
    "charla_bloqueado": (
        "Το σταμάτησα: είχε τη μορφή κάτι που καίει. Το\n"
        "σημάδι είναι στο αρχείο· αυτό που έλεγε, όχι."),
    "charla_callado": "Η μηχανή δεν επέστρεψε τίποτα. Είναι γεγονός, όχι απάντηση.",
    "charla_tarde": "Δεν τελείωσε εγκαίρως. {motivo}",
    "recuerdo_sin_que": ("Χωρίς «τι» δεν υπάρχει ανάμνηση. Δεν γράφτηκε τίποτα,\n"
                         "και τίποτα κακό: έλα πίσω όταν υπάρχει κάτι."),
    "sin_motor": ("\nΑυτό το αντίγραφο δεν έχει εγκατεστημένη μηχανή συζήτησης. Μπορώ να κρατώ\n"
                  "και να βρίσκω τις σημειώσεις σου, αλλά δεν μπορώ ακόμη να μιλήσω. Όλα\n"
                  "όσα ακολουθούν λειτουργούν χωρίς αυτήν.\n"
                  "Για να ανοίξει η συζήτηση, εγκατάστησε τη μηχανή που αναφέρεται στο\n"
                  "README → Requirements.\n"),
    "recuerdo_opcionales": (
        "\nΤα επόμενα τρία μπορούν να μείνουν κενά. Το Enter τα αφήνει {ausente},\n"
        "και μια ανάμνηση με δηλωμένα κενά είναι πάλι ανάμνηση — είναι πιο\n"
        "τίμια από μία όπου θα είχα μαντέψει ό,τι δεν μου είπες.\n"),
    "recuerdo_porque": "Γιατί σε ενδιαφέρει;  (Enter = {ausente})  ",
    "recuerdo_donde": "Υπάρχει αρχείο, φωτογραφία ή σημείωση που το στηρίζει;  (Enter = {ausente})  ",
    "recuerdo_aprendido": "Έμαθες κάτι που θα έλεγες σε κάποιον άλλον;  (Enter = για αργότερα)  ",
    "recuerdo_guardado": "\nΑποθηκεύτηκε, ακριβώς όπως το έγραψες:",
    "recuerdo_vacio": "(κενό, για αργότερα)",
    "palabra_recuerdo": "ανάμνηση",
    "palabra_recuerdos": "αναμνήσεις",
    "palabra_hueco": "δηλωμένο κενό",
    "palabra_huecos": "δηλωμένα κενά",
    "bucle_recuento": "\n{n} {nombre_r}. Τρεις είναι καλή αρχή — όχι υποχρέωση.",
    "otro_pregunta": "Να προσθέσω άλλη μία ανάμνηση;  (γράψε τον αριθμό: 1 ή 2)",
    "otro_si": "Ναι, άλλη μία",
    "otro_no": "Όχι, αρκετά για σήμερα",
    "enlace_pregunta": "\nΣχετίζονται δύο από αυτές;  (γράψε τον αριθμό: 1 ή 2)",
    "enlace_si": "Ναι, δύο σχετίζονται",
    "enlace_no": "Όχι, στέκονται μόνες τους",
    "enlace_desde": "από id:  ",
    "enlace_hasta": "προς id:  ",
    "enlace_como": "με δικά σου λόγια, πώς;  (Enter = {ausente})  ",
    "enlace_guardado": "Ο σύνδεσμος αποθηκεύτηκε.",
    "vista_tabla": "\n=== ΠΙΝΑΚΑΣ ",
    "vista_arbol": "\n=== ΔΕΝΤΡΟ ",
    "vista_recuento": "\n=== ΚΑΤΑΜΕΤΡΗΣΗ ",
    "cierre_cabecera": "\n--- τίμιο κλείσιμο ",
    "cierre_recuento": "Έχω {engrams} {nombre_r} και {huecos} {nombre_h}.",
    "cierre_viven": "Ζουν στο {ruta}. Μπορείς να αντιγράψεις αυτό το αρχείο και να το πάρεις μαζί σου.",
    "cierre_frontera": "Σβήσιμο στα σύνορα: ",
    "cierre_frontera_ok": "έτοιμο",
    "cierre_frontera_no": "ΜΗ ΔΙΑΘΕΣΙΜΟ — η εξαγωγή είναι μπλοκαρισμένη",
    "cierre_pregunta": "\nΠοιο κομμάτι θέλεις να καταλάβεις πρώτο;  ",
    "cierre_intencion_why": "το επόμενο πράγμα που θέλω να μάθω",
    "cierre_intencion": "Αποθηκεύτηκε ως πρόθεση. Προσανατολίζει την επόμενη αποστολή.",
    "sello_no_hay": ("Η σφράγιση της σημερινής κατάστασης δεν είναι διαθέσιμη: η ενότητα "
                     "του μανιφέστου δεν είναι εδώ."),
    "sello_no_hay_2": "Η μνήμη σου είναι ασφαλής ούτως ή άλλως. Δεν χάθηκε τίποτα.",
    "sello_intro": "Πριν φύγεις: μπορώ να σφραγίσω πώς είναι η μνήμη σου αυτή τη στιγμή.",
    "sello_intro_2": "Μια σφραγίδα αποδεικνύει ότι τίποτα δεν άλλαξε, χωρίς να λέει τι γράφει.",
    "sello_pregunta": "Σφράγιση σήμερα;  (γράψε τον αριθμό: 1 ή 2)",
    "sello_si": "Ναι, σφράγισέ τη",
    "sello_no": "Όχι τώρα — μπορώ να το κάνω οποιαδήποτε στιγμή",
    "sello_sellando": "Σφράγιση.",
    "sello_no_sellado": "Δεν σφραγίστηκε. Η μνήμη συνεχίζει να μεγαλώνει.",
    "sello_escrito": "Σφραγίστηκε: {destino}",
    "sello_copia": ("Κράτα ένα αντίγραφο αλλού: μια σφραγίδα δίπλα σε αυτό που "
                    "πιστοποιεί χάνεται μαζί του."),
    "final": "\nΑποστολή M2 ολοκληρώθηκε: ",
    "final_si": "ναι",
    "final_no": "όχι — δεν γράφτηκε τίποτα",
    "m3_intro": ("Υπάρχει και δεύτερο πράγμα, και είναι παιχνίδι. Έξι αίθουσες "
                 "και μια προτομή που θέλει να βγει από ένα μουσείο."),
    "m3_reanudar": ("Άφησες ένα μουσείο στη μέση. Είναι ακόμη εκεί, "
                    "ακριβώς όπου σταμάτησες."),
    "m3_pregunta": "Να μπεις στη Διαφυγή από το Μουσείο;",
    "m3_si": "ναι, πάμε",
    "m3_no": "όχι σήμερα",
    "m3_luego": ("Περιμένει. Είναι αρχείο, όχι ραντεβού: τίποτα "
                 "εκεί μέσα δεν λήγει."),
    "rechazo": "Το {entrada!r} δεν είναι ένα από αυτά. Γράψε τον αριθμό: {numeros}.",
    "o": "ή",
    "estado_sin_esquema": ("Δεν έχω ακόμη μνήμη. Δεν έχει δημιουργηθεί τίποτα σε "
                           "αυτό το μηχάνημα. Μπορώ να τη δημιουργήσω τώρα, αν το πεις."),
    "sin_memoria_aun": ("Δεν υπάρχει ακόμη μνήμη σε αυτό το μηχάνημα, οπότε δεν υπάρχει\n"
                        "τίποτα να γίνει εδώ. Τρέξε αυτό και τη φτιάχνουμε μαζί:\n"
                        "  python3 preceptoros.py\n"),
    "ritual_saludo": "\nΠρώτα, τρία πράγματα για σένα. Κανένα δεν είναι υποχρεωτικό.",
    "ritual_nombre": "Πώς να σε λέω;  (Enter για {ausente})  ",
    "ritual_ritmo": "Ρυθμός απαντήσεων (0-9, Enter για {ausente})  ",
    "ritual_hecho": "Έγινε. Ό,τι μου είπες είναι στη μνήμη σου, όχι σε δικό μου αρχείο.",
    "estado_vacia": ("Η μνήμη μου υπάρχει και είναι άδεια. 0 αναμνήσεις. "
                     "Δεν λείπει τίποτα: απλώς δεν έχει γραφτεί ακόμη τίποτα."),
    "estado_con_datos": "{n} αναμνήσεις, {l} σύνδεσμοι",
    "estado_archivados": ", {a} αρχειοθετημένες",
    "estado_cola": ". Ό,τι φαίνεται προέρχεται από όσα έγραψες εσύ.",
}

TEXTOS_MAS["ar"] = {
    "sabe_de_mi": "ما أعرفه عن نفسي، دون أي ذاكرة على الإطلاق:",
    "bullet_campos": "  - للذكرى 4 حقول: ماذا، لماذا، أين، ما تعلّمته",
    "bullet_ausencia": "  - الغياب يُكتب {ausente}، ولا يُترك فارغًا أبدًا",
    "bullet_vive": "  - ستعيش ذاكرتي في: {ruta}",
    "bullet_frontera": "  - لا شيء يغادر هذا الجهاز ما لم تصدّره",
    "crear_pregunta": "أأنشئ ذاكرتي الآن؟  (اكتب الرقم: 1 أو 2)",
    "crear_si": "نعم، أنشئها",
    "crear_no": "لا، ليس بعد",
    "nada_creado": "\nلم يُنشأ شيء. لا أحتفظ بأي أثر لهذه الجلسة.",
    "creado": "\nأُنشئ: {ruta}",
    "perfil_cabecera": "\n--- أولًا، سؤالان ليسا ذكريات ",
    "perfil_intro": (
        "أُبقي أمرين منفصلين: من أنت وأين أنا (هذا الجزء)،\n"
        "وما تتذكّره (كل ما بعده). لا جواب\n"
        "إلزامي. اضغط Enter فيبقى {ausente} — وهذا أيضًا\n"
        "جواب: يقول إن أحدًا لم يخبرني، بدل أن أتظاهر.\n"),
    "perfil_device": "أين أنا؟  (الجهاز الذي أعمل عليه، بكلماتك)  ",
    "perfil_name": "بماذا أناديك؟  ",
    "perfil_nota": ("({ausente} ليست خانة فارغة: إنها سؤال لم يُجب عنه\n"
                    " أحد. لا يضيع شيء بتركها هكذا.)"),
    "recuerdo_cabecera": "\n--- والآن ذكرى، حقلًا حقلًا ",
    "recuerdo_intro": (
        "الذكرى هنا مجرّد شيء حدث لك وقرّرت\n"
        "أنه يستحق الحفظ. لا يلزم أن يكون مهمًا.\n"),
    "recuerdo_ejemplos": (
        "  مثلًا  اشتغلت الطابعة أخيرًا بعد أن غيّرت كابلًا واحدًا\n"
        "        أفسدت قاعدة البيانات واستعدتها من نسخة\n"
        "        شرح لي أحدهم DNS وفهمته هذه المرة\n"),
    "recuerdo_que": "إذن — ماذا حدث؟  ",
    "cerebro_afinado": "الدماغ: نسخة مضبوطة · {motivo}",
    "charla_cabecera": "\n--- الحديث ",
    "charla_sin_motor": (
        "لا يوجد محرّك محادثة في هذه النسخة، لذا لا أستطيع\n"
        "الحديث بعد. كل ما عداه يعمل: ذاكرتك كاملة من دوني.\n"),
    "charla_sin_binario": (
        "الدماغ على هذا الجهاز، لكن لا يوجد هنا ما يشغّله.\n"
        "ثبّت {motor} وسأستطيع الحديث. كل ما عداه\n"
        "يعمل بالفعل من دونه.\n"),
    "charla_sin_modelo": (
        "أستطيع تشغيل دماغ، لكنني لا أجد أيًا منها. يُفترض أن يكون في\n"
        "  {ruta}\n"
        "إن نزّلته في مكان آخر، فانقله إلى هناك — لا أفتّش\n"
        "قرصك.\n"),
    "charla_donde": "أنت عند {peldano}. {prueba}",
    "charla_decision": (
        "النواة جاهزة. من هنا تختار: أن تمضي مباشرة إلى مشروعك\n"
        "الخاص، أو أن تبلغ محطة اختيارية. كلاهما هو الطريق.\n"),
    "charla_como_salir": "(سطر فارغ للخروج؛ لا يضيع شيء)",
    "charla_bloqueado": (
        "أوقفت ذلك: كان له شكل شيء يحرق. العلامة\n"
        "في السجلّ؛ أما ما قاله فلا."),
    "charla_callado": "لم يُعِد المحرّك شيئًا. هذه واقعة، لا جواب.",
    "charla_tarde": "لم ينتهِ في الوقت. {motivo}",
    "recuerdo_sin_que": ("بلا «ماذا» لا توجد ذكرى. لم يُكتب شيء،\n"
                         "ولا خطأ في ذلك: عُد حين يكون هناك شيء."),
    "sin_motor": ("\nلا يوجد محرّك محادثة مثبّت في هذه النسخة. أستطيع حفظ\n"
                  "ملاحظاتك واستعادتها، لكنني لا أستطيع الحديث بعد. كل\n"
                  "ما يلي يعمل من دونه.\n"
                  "لتشغيل الحديث، ثبّت المحرّك المذكور في\n"
                  "README → Requirements.\n"),
    "recuerdo_opcionales": (
        "\nيمكن أن تبقى الثلاثة التالية فارغة. Enter يتركها {ausente}،\n"
        "والذكرى ذات الفجوات المُعلَنة تبقى ذكرى — وهي أصدق\n"
        "من ذكرى خمّنتُ فيها ما لم تقله لي.\n"),
    "recuerdo_porque": "لماذا يهمّك هذا؟  (Enter = {ausente})  ",
    "recuerdo_donde": "هل هناك ملف أو صورة أو ملاحظة تسنده؟  (Enter = {ausente})  ",
    "recuerdo_aprendido": "هل تعلّمت شيئًا قد تقوله لشخص آخر؟  (Enter = لاحقًا)  ",
    "recuerdo_guardado": "\nحُفظ، كما كتبته بالضبط:",
    "recuerdo_vacio": "(فارغ، لاحقًا)",
    "palabra_recuerdo": "ذكرى",
    "palabra_recuerdos": "ذكريات",
    "palabra_hueco": "فجوة مُعلَنة",
    "palabra_huecos": "فجوات مُعلَنة",
    "bucle_recuento": "\n{n} {nombre_r}. ثلاث بداية جيدة — لا شرط.",
    "otro_pregunta": "أأضيف ذكرى أخرى؟  (اكتب الرقم: 1 أو 2)",
    "otro_si": "نعم، واحدة أخرى",
    "otro_no": "لا، يكفي لليوم",
    "enlace_pregunta": "\nهل اثنتان منها مترابطتان؟  (اكتب الرقم: 1 أو 2)",
    "enlace_si": "نعم، اثنتان منها",
    "enlace_no": "لا، كلٌّ قائمة بذاتها",
    "enlace_desde": "من المعرّف:  ",
    "enlace_hasta": "إلى المعرّف:  ",
    "enlace_como": "بكلماتك، كيف؟  (Enter = {ausente})  ",
    "enlace_guardado": "حُفظ الرابط.",
    "vista_tabla": "\n=== جدول ",
    "vista_arbol": "\n=== شجرة ",
    "vista_recuento": "\n=== عدّ ",
    "cierre_cabecera": "\n--- ختام صادق ",
    "cierre_recuento": "لديّ {engrams} {nombre_r} و{huecos} {nombre_h}.",
    "cierre_viven": "تعيش في {ruta}. يمكنك نسخ ذلك الملف وأخذه معك.",
    "cierre_frontera": "الحجب عند الحدّ: ",
    "cierre_frontera_ok": "جاهز",
    "cierre_frontera_no": "غير متاح — التصدير محظور",
    "cierre_pregunta": "\nأي قطعة تريد أن تفهمها أولًا؟  ",
    "cierre_intencion_why": "الشيء التالي الذي أريد تعلّمه",
    "cierre_intencion": "حُفظ كنيّة. يوجّه المهمة التالية.",
    "sello_no_hay": ("ختم حالة اليوم غير متاح: وحدة البيان "
                     "غير موجودة هنا."),
    "sello_no_hay_2": "ذاكرتك في أمان على أي حال. لم يضع شيء.",
    "sello_intro": "قبل أن تذهب: أستطيع أن أختم شكل ذاكرتك في هذه اللحظة.",
    "sello_intro_2": "الختم يُثبت أن شيئًا لم يتغيّر، دون أن يقول ما فيه.",
    "sello_pregunta": "أنختم اليوم؟  (اكتب الرقم: 1 أو 2)",
    "sello_si": "نعم، اختمها",
    "sello_no": "ليس الآن — أستطيع فعل ذلك في أي وقت",
    "sello_sellando": "جارٍ الختم.",
    "sello_no_sellado": "لم تُختم. الذاكرة تواصل النمو.",
    "sello_escrito": "خُتمت: {destino}",
    "sello_copia": ("احتفظ بنسخة في مكان آخر: الختم بجانب ما "
                    "يشهد له يضيع معه."),
    "final": "\nاكتملت المهمة M2: ",
    "final_si": "نعم",
    "final_no": "لا — لم يُكتب شيء",
    "m3_intro": ("هناك شيء ثانٍ، وهو لعبة. ست قاعات، "
                 "وتمثال نصفي يريد الخروج من متحف."),
    "m3_reanudar": ("تركت متحفًا في منتصفه. ما زال هناك، "
                    "حيث توقفت بالضبط."),
    "m3_pregunta": "أتدخل الهروب من المتحف؟",
    "m3_si": "نعم، لنذهب",
    "m3_no": "ليس اليوم",
    "m3_luego": ("إنه ينتظر. إنه ملف، لا موعد: لا شيء "
                 "فيه ينتهي."),
    "rechazo": "{entrada!r} ليست واحدة منها. اكتب الرقم: {numeros}.",
    "o": "أو",
    "estado_sin_esquema": ("ليست لديّ ذاكرة بعد. لم يُنشأ شيء على "
                           "هذا الجهاز. أستطيع إنشاءها الآن، إن قلت ذلك."),
    "sin_memoria_aun": ("لا توجد ذاكرة على هذا الجهاز بعد، فلا شيء\n"
                        "لفعله هنا. شغّل هذا وننشئها معًا:\n"
                        "  python3 preceptoros.py\n"),
    "ritual_saludo": "\nأولًا، ثلاثة أشياء عنك. لا شيء منها إلزامي.",
    "ritual_nombre": "بماذا أناديك؟  (Enter لـ {ausente})  ",
    "ritual_ritmo": "إيقاع الأجوبة (0-9، Enter لـ {ausente})  ",
    "ritual_hecho": "تمّ. ما قلته لي موجود في ذاكرتك، لا في ملف لي.",
    "estado_vacia": ("ذاكرتي موجودة وهي فارغة. 0 ذكريات. "
                     "لا ينقص شيء: لم يُكتب شيء بعد."),
    "estado_con_datos": "{n} ذكريات، {l} روابط",
    "estado_archivados": "، {a} مؤرشفة",
    "estado_cola": ". كل ما يظهر يأتي مما كتبته أنت.",
}


# --- LA CARA (`cara.py`) · las mismas 51 claves que `CARA_TEXTOS["en"]` ------
# «The voice speaks Spanish only» se traduce tal cual: la voz sigue siendo
# solo castellana en las nueve lenguas, y la cara lo dice en la de quien lee.
CARA_MAS = {}

CARA_MAS["fr"] = {
    "titulo": "Preceptor", "sub": "l'Eau · ta mémoire, sur ta machine",
    "saludo": "Je suis réveillé. Rien ici n'a quitté cette machine.",
    "saludo_vuelta": "Je suis réveillé, et j'ai encore ce que tu as écrit.",
    "campo": "Écris ta réponse…", "enviar": "DIS-LE", "pizarra": "Ardoise",
    "camino": "Le Chemin", "cerrar": "Fermer",
    "pz_titulo": "L'Ardoise · tout ce que ta mémoire contient",
    "pz_vacia": "Rien d'écrit encore. C'est un état, pas un échec.",
    "pz_sin_guardar": "capturé ici, pas encore écrit",
    "pz_bajar_json": "Enregistrer le formulaire",
    "pz_bajar_txt": "Enregistrer une copie lisible",
    "pz_aplicar": "Pour l'écrire dans ta mémoire, applique le fichier que tu viens d'enregistrer :",
    "pz_auto": "L'appliquer maintenant",
    "pz_auto_ok": "Écrit dans ta mémoire : {engrams} souvenirs, {profile} réponses. Rien n'a été remplacé.",
    "pz_auto_mal": "Non appliqué : {motivo}. Rien n'a été écrit.",
    "pz_col": ["id", "quoi", "pourquoi", "où", "appris"],
    "cm_titulo": "Le Chemin",
    "cm_intro": "Huit étapes. Voici où tu en es vraiment — mesuré, pas deviné.",
    "cm_nota": "Rien ici n'est téléchargé. Cette page est tout.",
    "fin": "C'est tout. Ouvre l'Ardoise pour l'emporter.",
    "idioma": "Langue", "voz_hablar": "Parler", "voz_callar": "Muet",
    "voz_no_hay": "Pas de voix dans cette copie",
    "voz_solo_es": "La voix ne parle qu'espagnol",
    "voz_nota": "Le texte est toujours là. Le bouton décide seulement s'il est aussi dit à voix haute.",
    "cm_hecho": "fait", "cm_empezado": "commencé", "cm_sin_empezar": "pas commencé",
    "cm_no_medible": "pas mesurable d'ici",
    "cm_prueba_M0": "les deux questions qui ne sont pas des souvenirs : {perfil}/2 répondues",
    "cm_prueba_M1": "le cerveau ne vit pas dans ce fichier, donc cette page ne peut pas le vérifier",
    "cm_prueba_M2": "{recuerdos} souvenirs écrits · sceau : {sello}",
    "cm_prueba_M3": "{salas}/6 salles terminées",
    "cm_prueba_M4": "{huellas} passages enregistrés",
    "cm_prueba_M5": "{senderos} sentiers ouverts",
    "cm_prueba_M6": "{cicatrices} cicatrices au registre",
    "cm_prueba_M7": "personne n'a écrit ce qui compte comme un succès signé, donc cette page ne l'inventera pas",
    "cm_ventaja_M3": "t'apporte : une façon de travailler sans bruit",
    "cm_ventaja_M4": "t'apporte : tu as vu tes propres mots partir",
    "cm_ventaja_M5": "t'apporte : inachevé est un état, pas une dette",
    "cm_ventaja_M6": "t'apporte : une erreur qui laisse une marque peut se lire",
    "cm_ventaja_M7": "t'apporte : moins d'explications, parce qu'il t'en faut moins",
    "cm_opcional": "facultatif", "cm_nucleo": "cœur",
    "cm_decision": "Le cœur est fait. À partir d'ici tu choisis : aller droit à ton projet, ou prendre une quête secondaire. Les deux sont le chemin.",
    "cm_pendiente": "pas encore de moyen de mesurer celle-ci — elle ne sera pas montrée comme un progrès tant qu'il n'y en aura pas",
    "cm_refrescar": "Cette page est un instantané. Pour la mettre à jour, régénère-la — elle lit ta mémoire et ton sceau tels qu'ils sont maintenant :",
}

CARA_MAS["pt"] = {
    "titulo": "Preceptor", "sub": "a Água · a tua memória, na tua máquina",
    "saludo": "Estou acordado. Nada daqui saiu desta máquina.",
    "saludo_vuelta": "Estou acordado, e ainda tenho o que escreveste.",
    "campo": "Escreve a tua resposta…", "enviar": "DIZ", "pizarra": "Ardósia",
    "camino": "O Caminho", "cerrar": "Fechar",
    "pz_titulo": "A Ardósia · tudo o que a tua memória guarda",
    "pz_vacia": "Ainda nada escrito. É um estado, não uma falha.",
    "pz_sin_guardar": "captado aqui, ainda não escrito",
    "pz_bajar_json": "Guardar o formulário",
    "pz_bajar_txt": "Guardar uma cópia legível",
    "pz_aplicar": "Para o escrever na tua memória, aplica o ficheiro que acabaste de guardar:",
    "pz_auto": "Aplicar agora",
    "pz_auto_ok": "Escrito na tua memória: {engrams} recordações, {profile} respostas. Nada foi substituído.",
    "pz_auto_mal": "Não aplicado: {motivo}. Nada foi escrito.",
    "pz_col": ["id", "o quê", "porquê", "onde", "aprendido"],
    "cm_titulo": "O Caminho",
    "cm_intro": "Oito passos. É aqui que estás de verdade — medido, não adivinhado.",
    "cm_nota": "Nada aqui é descarregado. Esta página é tudo.",
    "fin": "É tudo. Abre a Ardósia para o levares contigo.",
    "idioma": "Língua", "voz_hablar": "Falar", "voz_callar": "Silenciar",
    "voz_no_hay": "Sem voz nesta cópia",
    "voz_solo_es": "A voz só fala espanhol",
    "voz_nota": "O texto está sempre aqui. O botão só decide se também é dito em voz alta.",
    "cm_hecho": "feito", "cm_empezado": "começado", "cm_sin_empezar": "por começar",
    "cm_no_medible": "não mensurável daqui",
    "cm_prueba_M0": "as duas perguntas que não são recordações: {perfil}/2 respondidas",
    "cm_prueba_M1": "o cérebro não vive dentro deste ficheiro, por isso esta página não o pode verificar",
    "cm_prueba_M2": "{recuerdos} recordações escritas · selo: {sello}",
    "cm_prueba_M3": "{salas}/6 salas terminadas",
    "cm_prueba_M4": "{huellas} travessias registadas",
    "cm_prueba_M5": "{senderos} trilhos abertos",
    "cm_prueba_M6": "{cicatrices} cicatrizes em registo",
    "cm_prueba_M7": "ninguém escreveu o que conta como um êxito assinado, por isso esta página não o vai inventar",
    "cm_ventaja_M3": "dá-te: uma forma de trabalhar sem ruído",
    "cm_ventaja_M4": "dá-te: viste as tuas próprias palavras a sair",
    "cm_ventaja_M5": "dá-te: inacabado é um estado, não uma dívida",
    "cm_ventaja_M6": "dá-te: um erro que deixa marca pode ler-se",
    "cm_ventaja_M7": "dá-te: menos explicações, porque precisas de menos",
    "cm_opcional": "opcional", "cm_nucleo": "núcleo",
    "cm_decision": "O núcleo está feito. A partir daqui escolhes: ir direto ao teu projeto, ou fazer uma missão paralela. Os dois são o caminho.",
    "cm_pendiente": "ainda não há forma de medir esta — não será mostrada como progresso enquanto não houver",
    "cm_refrescar": "Esta página é um instantâneo. Para a atualizar, gera-a de novo — lê a tua memória e o teu selo como estão agora:",
}

CARA_MAS["it"] = {
    "titulo": "Preceptor", "sub": "l'Acqua · la tua memoria, sulla tua macchina",
    "saludo": "Sono sveglio. Niente qui ha lasciato questa macchina.",
    "saludo_vuelta": "Sono sveglio, e ho ancora quello che hai scritto.",
    "campo": "Scrivi la tua risposta…", "enviar": "DILLO", "pizarra": "Lavagna",
    "camino": "Il Cammino", "cerrar": "Chiudi",
    "pz_titulo": "La Lavagna · tutto ciò che la tua memoria contiene",
    "pz_vacia": "Ancora niente di scritto. È uno stato, non un fallimento.",
    "pz_sin_guardar": "catturato qui, non ancora scritto",
    "pz_bajar_json": "Salva il modulo",
    "pz_bajar_txt": "Salva una copia leggibile",
    "pz_aplicar": "Per scriverlo nella tua memoria, applica il file che hai appena salvato:",
    "pz_auto": "Applicalo ora",
    "pz_auto_ok": "Scritto nella tua memoria: {engrams} ricordi, {profile} risposte. Niente è stato sostituito.",
    "pz_auto_mal": "Non applicato: {motivo}. Non è stato scritto nulla.",
    "pz_col": ["id", "cosa", "perché", "dove", "imparato"],
    "cm_titulo": "Il Cammino",
    "cm_intro": "Otto passi. Ecco dove sei davvero — misurato, non indovinato.",
    "cm_nota": "Niente qui viene scaricato. Questa pagina è tutto.",
    "fin": "È tutto. Apri la Lavagna per portarlo con te.",
    "idioma": "Lingua", "voz_hablar": "Parla", "voz_callar": "Muto",
    "voz_no_hay": "Nessuna voce in questa copia",
    "voz_solo_es": "La voce parla solo spagnolo",
    "voz_nota": "Il testo è sempre qui. Il pulsante decide solo se viene anche detto ad alta voce.",
    "cm_hecho": "fatto", "cm_empezado": "iniziato", "cm_sin_empezar": "non iniziato",
    "cm_no_medible": "non misurabile da qui",
    "cm_prueba_M0": "le due domande che non sono ricordi: {perfil}/2 risposte",
    "cm_prueba_M1": "il cervello non vive in questo file, quindi questa pagina non può verificarlo",
    "cm_prueba_M2": "{recuerdos} ricordi scritti · sigillo: {sello}",
    "cm_prueba_M3": "{salas}/6 sale finite",
    "cm_prueba_M4": "{huellas} attraversamenti registrati",
    "cm_prueba_M5": "{senderos} sentieri aperti",
    "cm_prueba_M6": "{cicatrices} cicatrici a registro",
    "cm_prueba_M7": "nessuno ha scritto cosa conta come successo firmato, quindi questa pagina non lo inventerà",
    "cm_ventaja_M3": "ti dà: un modo di lavorare senza rumore",
    "cm_ventaja_M4": "ti dà: hai visto le tue parole andarsene",
    "cm_ventaja_M5": "ti dà: incompiuto è uno stato, non un debito",
    "cm_ventaja_M6": "ti dà: un errore che lascia un segno si può leggere",
    "cm_ventaja_M7": "ti dà: meno spiegazioni, perché te ne servono meno",
    "cm_opcional": "facoltativo", "cm_nucleo": "nucleo",
    "cm_decision": "Il nucleo è fatto. Da qui scegli tu: andare dritto al tuo progetto, o fare una missione secondaria. Entrambi sono il cammino.",
    "cm_pendiente": "ancora nessun modo di misurare questa — non sarà mostrata come progresso finché non ci sarà",
    "cm_refrescar": "Questa pagina è un'istantanea. Per aggiornarla, rigenerala — legge la tua memoria e il tuo sigillo come sono adesso:",
}

CARA_MAS["de"] = {
    "titulo": "Preceptor", "sub": "das Wasser · dein Gedächtnis, auf deiner Maschine",
    "saludo": "Ich bin wach. Nichts hier hat diese Maschine verlassen.",
    "saludo_vuelta": "Ich bin wach, und ich habe noch, was du geschrieben hast.",
    "campo": "Schreib deine Antwort…", "enviar": "SAG ES", "pizarra": "Schiefertafel",
    "camino": "Der Weg", "cerrar": "Schließen",
    "pz_titulo": "Die Schiefertafel · alles, was dein Gedächtnis enthält",
    "pz_vacia": "Noch nichts geschrieben. Das ist ein Zustand, kein Fehler.",
    "pz_sin_guardar": "hier erfasst, noch nicht geschrieben",
    "pz_bajar_json": "Formular speichern",
    "pz_bajar_txt": "Lesbare Kopie speichern",
    "pz_aplicar": "Um es in dein Gedächtnis zu schreiben, wende die gerade gespeicherte Datei an:",
    "pz_auto": "Jetzt anwenden",
    "pz_auto_ok": "In dein Gedächtnis geschrieben: {engrams} Erinnerungen, {profile} Antworten. Nichts wurde ersetzt.",
    "pz_auto_mal": "Nicht angewendet: {motivo}. Es wurde nichts geschrieben.",
    "pz_col": ["ID", "was", "warum", "wo", "gelernt"],
    "cm_titulo": "Der Weg",
    "cm_intro": "Acht Schritte. Hier stehst du wirklich — gemessen, nicht geraten.",
    "cm_nota": "Hier wird nichts heruntergeladen. Diese Seite ist alles.",
    "fin": "Das ist alles. Öffne die Schiefertafel, um es mitzunehmen.",
    "idioma": "Sprache", "voz_hablar": "Sprechen", "voz_callar": "Stumm",
    "voz_no_hay": "Keine Stimme in dieser Kopie",
    "voz_solo_es": "Die Stimme spricht nur Spanisch",
    "voz_nota": "Der Text ist immer da. Der Knopf entscheidet nur, ob er auch laut gesagt wird.",
    "cm_hecho": "erledigt", "cm_empezado": "begonnen", "cm_sin_empezar": "nicht begonnen",
    "cm_no_medible": "von hier aus nicht messbar",
    "cm_prueba_M0": "die zwei Fragen, die keine Erinnerungen sind: {perfil}/2 beantwortet",
    "cm_prueba_M1": "das Gehirn lebt nicht in dieser Datei, also kann diese Seite es nicht prüfen",
    "cm_prueba_M2": "{recuerdos} Erinnerungen geschrieben · Siegel: {sello}",
    "cm_prueba_M3": "{salas}/6 Säle abgeschlossen",
    "cm_prueba_M4": "{huellas} Übergänge verzeichnet",
    "cm_prueba_M5": "{senderos} Pfade geöffnet",
    "cm_prueba_M6": "{cicatrices} Narben im Protokoll",
    "cm_prueba_M7": "niemand hat aufgeschrieben, was als unterschriebener Erfolg zählt, also erfindet diese Seite es nicht",
    "cm_ventaja_M3": "bringt dir: eine Art, ohne Lärm zu arbeiten",
    "cm_ventaja_M4": "bringt dir: du hast deine eigenen Worte gehen sehen",
    "cm_ventaja_M5": "bringt dir: unfertig ist ein Zustand, keine Schuld",
    "cm_ventaja_M6": "bringt dir: ein Fehler, der eine Spur hinterlässt, lässt sich lesen",
    "cm_ventaja_M7": "bringt dir: weniger Erklären, weil du weniger brauchst",
    "cm_opcional": "optional", "cm_nucleo": "Kern",
    "cm_decision": "Der Kern ist fertig. Ab hier entscheidest du: direkt zu deinem Projekt oder eine Nebenaufgabe. Beides ist der Weg.",
    "cm_pendiente": "noch keine Möglichkeit, das zu messen — es wird nicht als Fortschritt gezeigt, solange es keine gibt",
    "cm_refrescar": "Diese Seite ist eine Momentaufnahme. Um sie zu aktualisieren, erzeuge sie neu — sie liest dein Gedächtnis und dein Siegel, wie sie jetzt sind:",
}

CARA_MAS["ru"] = {
    "titulo": "Preceptor", "sub": "Вода · твоя память, на твоей машине",
    "saludo": "Я проснулся. Ничто отсюда не покинуло эту машину.",
    "saludo_vuelta": "Я проснулся, и у меня всё ещё есть то, что ты написал.",
    "campo": "Напиши свой ответ…", "enviar": "СКАЖИ", "pizarra": "Грифельная доска",
    "camino": "Путь", "cerrar": "Закрыть",
    "pz_titulo": "Грифельная доска · всё, что хранит твоя память",
    "pz_vacia": "Пока ничего не написано. Это состояние, а не провал.",
    "pz_sin_guardar": "записано здесь, но ещё не сохранено в памяти",
    "pz_bajar_json": "Сохранить форму",
    "pz_bajar_txt": "Сохранить читаемую копию",
    "pz_aplicar": "Чтобы записать это в свою память, примени файл, который ты только что сохранил:",
    "pz_auto": "Применить сейчас",
    "pz_auto_ok": "Записано в твою память: {engrams} воспоминаний, {profile} ответов. Ничего не заменено.",
    "pz_auto_mal": "Не применено: {motivo}. Ничего не записано.",
    "pz_col": ["id", "что", "почему", "где", "чему научился"],
    "cm_titulo": "Путь",
    "cm_intro": "Восемь шагов. Вот где ты на самом деле — измерено, а не угадано.",
    "cm_nota": "Здесь ничего не скачивается. Эта страница — всё.",
    "fin": "Это всё. Открой грифельную доску, чтобы забрать это с собой.",
    "idioma": "Язык", "voz_hablar": "Говорить", "voz_callar": "Без звука",
    "voz_no_hay": "В этой копии нет голоса",
    "voz_solo_es": "Голос говорит только по-испански",
    "voz_nota": "Текст всегда здесь. Кнопка решает только, произносится ли он ещё и вслух.",
    "cm_hecho": "готово", "cm_empezado": "начато", "cm_sin_empezar": "не начато",
    "cm_no_medible": "отсюда не измерить",
    "cm_prueba_M0": "два вопроса, которые не являются воспоминаниями: {perfil}/2 отвечено",
    "cm_prueba_M1": "мозг не живёт в этом файле, поэтому эта страница не может его проверить",
    "cm_prueba_M2": "{recuerdos} воспоминаний записано · печать: {sello}",
    "cm_prueba_M3": "{salas}/6 залов пройдено",
    "cm_prueba_M4": "{huellas} переходов записано",
    "cm_prueba_M5": "{senderos} тропинок открыто",
    "cm_prueba_M6": "{cicatrices} шрамов в журнале",
    "cm_prueba_M7": "никто не записал, что считается подписанным успехом, поэтому эта страница его не выдумает",
    "cm_ventaja_M3": "даёт тебе: способ работать без шума",
    "cm_ventaja_M4": "даёт тебе: ты видел, как уходят твои собственные слова",
    "cm_ventaja_M5": "даёт тебе: незаконченное — это состояние, а не долг",
    "cm_ventaja_M6": "даёт тебе: ошибку, оставившую след, можно прочитать",
    "cm_ventaja_M7": "даёт тебе: меньше объяснений, потому что тебе их нужно меньше",
    "cm_opcional": "необязательно", "cm_nucleo": "ядро",
    "cm_decision": "Ядро готово. Дальше выбираешь ты: сразу к своему проекту или к побочному заданию. Оба варианта — это путь.",
    "cm_pendiente": "пока нечем это измерить — оно не будет показано как прогресс, пока такой способ не появится",
    "cm_refrescar": "Эта страница — снимок. Чтобы обновить её, создай её заново — она читает твою память и твою печать такими, какие они сейчас:",
}

CARA_MAS["el"] = {
    "titulo": "Preceptor", "sub": "το Νερό · η μνήμη σου, στο μηχάνημά σου",
    "saludo": "Είμαι ξύπνιος. Τίποτα από εδώ δεν έφυγε από αυτό το μηχάνημα.",
    "saludo_vuelta": "Είμαι ξύπνιος, και έχω ακόμη ό,τι έγραψες.",
    "campo": "Γράψε την απάντησή σου…", "enviar": "ΠΕΣ ΤΟ", "pizarra": "Πλάκα",
    "camino": "Ο Δρόμος", "cerrar": "Κλείσιμο",
    "pz_titulo": "Η Πλάκα · όλα όσα κρατά η μνήμη σου",
    "pz_vacia": "Δεν έχει γραφτεί τίποτα ακόμη. Είναι κατάσταση, όχι αποτυχία.",
    "pz_sin_guardar": "καταγράφηκε εδώ, δεν γράφτηκε ακόμη",
    "pz_bajar_json": "Αποθήκευση της φόρμας",
    "pz_bajar_txt": "Αποθήκευση αναγνώσιμου αντιγράφου",
    "pz_aplicar": "Για να γραφτεί στη μνήμη σου, εφάρμοσε το αρχείο που μόλις αποθήκευσες:",
    "pz_auto": "Εφάρμοσέ το τώρα",
    "pz_auto_ok": "Γράφτηκε στη μνήμη σου: {engrams} αναμνήσεις, {profile} απαντήσεις. Τίποτα δεν αντικαταστάθηκε.",
    "pz_auto_mal": "Δεν εφαρμόστηκε: {motivo}. Δεν γράφτηκε τίποτα.",
    "pz_col": ["id", "τι", "γιατί", "πού", "τι έμαθα"],
    "cm_titulo": "Ο Δρόμος",
    "cm_intro": "Οκτώ βήματα. Εδώ βρίσκεσαι πραγματικά — μετρημένο, όχι μαντεμένο.",
    "cm_nota": "Τίποτα εδώ δεν κατεβαίνει. Αυτή η σελίδα είναι το παν.",
    "fin": "Αυτά είναι όλα. Άνοιξε την Πλάκα για να τα πάρεις μαζί σου.",
    "idioma": "Γλώσσα", "voz_hablar": "Μίλα", "voz_callar": "Σίγαση",
    "voz_no_hay": "Χωρίς φωνή σε αυτό το αντίγραφο",
    "voz_solo_es": "Η φωνή μιλά μόνο ισπανικά",
    "voz_nota": "Το κείμενο είναι πάντα εδώ. Το κουμπί αποφασίζει μόνο αν θα ειπωθεί και φωναχτά.",
    "cm_hecho": "έγινε", "cm_empezado": "ξεκίνησε", "cm_sin_empezar": "δεν ξεκίνησε",
    "cm_no_medible": "δεν μετριέται από εδώ",
    "cm_prueba_M0": "οι δύο ερωτήσεις που δεν είναι αναμνήσεις: {perfil}/2 απαντήθηκαν",
    "cm_prueba_M1": "ο εγκέφαλος δεν ζει μέσα σε αυτό το αρχείο, οπότε αυτή η σελίδα δεν μπορεί να τον ελέγξει",
    "cm_prueba_M2": "{recuerdos} αναμνήσεις γραμμένες · σφραγίδα: {sello}",
    "cm_prueba_M3": "{salas}/6 αίθουσες ολοκληρώθηκαν",
    "cm_prueba_M4": "{huellas} περάσματα καταγράφηκαν",
    "cm_prueba_M5": "{senderos} μονοπάτια άνοιξαν",
    "cm_prueba_M6": "{cicatrices} ουλές στο αρχείο",
    "cm_prueba_M7": "κανείς δεν έγραψε τι μετρά ως υπογεγραμμένη επιτυχία, οπότε αυτή η σελίδα δεν θα το επινοήσει",
    "cm_ventaja_M3": "σου δίνει: έναν τρόπο να δουλεύεις χωρίς θόρυβο",
    "cm_ventaja_M4": "σου δίνει: είδες τα δικά σου λόγια να φεύγουν",
    "cm_ventaja_M5": "σου δίνει: το ημιτελές είναι κατάσταση, όχι χρέος",
    "cm_ventaja_M6": "σου δίνει: ένα λάθος που αφήνει σημάδι διαβάζεται",
    "cm_ventaja_M7": "σου δίνει: λιγότερες εξηγήσεις, γιατί χρειάζεσαι λιγότερες",
    "cm_opcional": "προαιρετικό", "cm_nucleo": "πυρήνας",
    "cm_decision": "Ο πυρήνας έγινε. Από εδώ διαλέγεις: κατευθείαν στο έργο σου, ή μια παράπλευρη αποστολή. Και τα δύο είναι ο δρόμος.",
    "cm_pendiente": "δεν υπάρχει ακόμη τρόπος να μετρηθεί αυτό — δεν θα φανεί ως πρόοδος μέχρι να υπάρξει",
    "cm_refrescar": "Αυτή η σελίδα είναι στιγμιότυπο. Για να την ενημερώσεις, δημιούργησέ τη ξανά — διαβάζει τη μνήμη και τη σφραγίδα σου όπως είναι τώρα:",
}

CARA_MAS["ar"] = {
    "titulo": "Preceptor", "sub": "الماء · ذاكرتك، على جهازك",
    "saludo": "أنا مستيقظ. لم يغادر شيء من هنا هذا الجهاز.",
    "saludo_vuelta": "أنا مستيقظ، وما زال لديّ ما كتبته.",
    "campo": "اكتب جوابك…", "enviar": "قُلها", "pizarra": "اللوح",
    "camino": "الطريق", "cerrar": "أغلق",
    "pz_titulo": "اللوح · كل ما تحفظه ذاكرتك",
    "pz_vacia": "لم يُكتب شيء بعد. هذه حالة، لا إخفاق.",
    "pz_sin_guardar": "التُقط هنا، ولم يُكتب بعد",
    "pz_bajar_json": "احفظ النموذج",
    "pz_bajar_txt": "احفظ نسخة مقروءة",
    "pz_aplicar": "لكتابته في ذاكرتك، طبّق الملف الذي حفظته للتو:",
    "pz_auto": "طبّقه الآن",
    "pz_auto_ok": "كُتب في ذاكرتك: {engrams} ذكريات، {profile} أجوبة. لم يُستبدل شيء.",
    "pz_auto_mal": "لم يُطبَّق: {motivo}. لم يُكتب شيء.",
    "pz_col": ["المعرّف", "ماذا", "لماذا", "أين", "ما تعلّمته"],
    "cm_titulo": "الطريق",
    "cm_intro": "ثماني خطوات. هنا تقف فعلًا — مقيس، لا مخمَّن.",
    "cm_nota": "لا شيء هنا يُنزَّل. هذه الصفحة هي كل شيء.",
    "fin": "هذا كل شيء. افتح اللوح لتأخذه معك.",
    "idioma": "اللغة", "voz_hablar": "تكلّم", "voz_callar": "اصمت",
    "voz_no_hay": "لا صوت في هذه النسخة",
    "voz_solo_es": "الصوت يتكلّم الإسبانية فقط",
    "voz_nota": "النص موجود دائمًا. الزر يقرّر فقط هل يُقال بصوت عالٍ أيضًا.",
    "cm_hecho": "تمّ", "cm_empezado": "بدأ", "cm_sin_empezar": "لم يبدأ",
    "cm_no_medible": "لا يُقاس من هنا",
    "cm_prueba_M0": "السؤالان اللذان ليسا ذكريات: {perfil}/2 أُجيب عنهما",
    "cm_prueba_M1": "الدماغ لا يعيش داخل هذا الملف، فلا تستطيع هذه الصفحة التحقق منه",
    "cm_prueba_M2": "{recuerdos} ذكريات مكتوبة · الختم: {sello}",
    "cm_prueba_M3": "{salas}/6 قاعات منتهية",
    "cm_prueba_M4": "{huellas} عبورات مسجّلة",
    "cm_prueba_M5": "{senderos} دروب مفتوحة",
    "cm_prueba_M6": "{cicatrices} ندوب في السجلّ",
    "cm_prueba_M7": "لم يكتب أحد ما يُعدّ نجاحًا موقّعًا، فلن تخترعه هذه الصفحة",
    "cm_ventaja_M3": "يمنحك: طريقة للعمل بلا ضجيج",
    "cm_ventaja_M4": "يمنحك: رأيت كلماتك تغادر",
    "cm_ventaja_M5": "يمنحك: غير المنتهي حالة، لا دَين",
    "cm_ventaja_M6": "يمنحك: الخطأ الذي يترك أثرًا يمكن قراءته",
    "cm_ventaja_M7": "يمنحك: شرح أقل، لأنك تحتاج إلى أقل",
    "cm_opcional": "اختياري", "cm_nucleo": "النواة",
    "cm_decision": "النواة جاهزة. من هنا تختار: أن تمضي مباشرة إلى مشروعك، أو أن تخوض مهمة جانبية. كلاهما هو الطريق.",
    "cm_pendiente": "لا طريقة لقياس هذه بعد — لن تُعرض تقدّمًا حتى توجد",
    "cm_refrescar": "هذه الصفحة لقطة. لتحديثها، ولّدها من جديد — فهي تقرأ ذاكرتك وختمك كما هما الآن:",
}
