"""Bench: how much of natural phrasing does Talk's exact grammar route today, and what would a zero-weight lexical
router add? Corpus written BEFORE the router rules (same author: not independent; real-user phrasing is NO_DATA)."""
import re
import sys
import json
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
import hexelion_acciones as A

C = {
 "/estado": ["how is the rack doing", "rack status please", "is everything up", "como esta el rack ahora",
             "estado del rack", "va todo bien en el rack", "esta el rack bien", "como vai o rack", "o rack esta bem",
             "status of the machines"],
 "/capacidades": ["what are you able to do", "what tools do you have", "list your capabilities", "que sabes hacer",
                  "que herramientas tienes", "que puedes hacer por mi", "o que sabes fazer", "quais ferramentas tens",
                  "what can hexelion do", "show me what you can do"],
 "/registro 5": ["what have you done lately", "show your last actions", "recent actions", "que has hecho ultimamente",
                 "tus ultimas acciones", "que hiciste hoy", "o que fizeste ultimamente", "ultimas acoes",
                 "what did you just do", "history of your actions"],
 "/firmas": ["what needs my signature", "anything waiting for me to sign", "pending signatures", "que tengo que firmar",
             "hay algo pendiente de firma", "firmas pendientes", "o que tenho de assinar", "assinaturas pendentes",
             "which prs wait for my hitl", "what is waiting for my approval"],
 "/lab": ["show lab results", "latest benchmark", "how did the last bench go", "resultados del laboratorio",
          "ultimo benchmark", "que dice el lab", "resultados do laboratorio", "ultimo bench do lab",
          "lab results please", "what did the lab measure"],
 "/preceptores": ["who is working right now", "which agents are active", "which preceptors are busy",
                  "quien esta trabajando", "que preceptores trabajan ahora", "agentes activos", "quem esta a trabalhar",
                  "que preceptores estao ativos", "who is online", "are the agents working"],
 "/dispositivos": ["which devices are online", "list my devices", "what phones are connected", "que dispositivos hay",
                   "lista de dispositivos", "que moviles estan conectados", "quais dispositivos estao ligados",
                   "lista dos meus dispositivos", "show the nodes and phones", "what hardware do we have"],
 "/modelos": ["which models are installed", "what llms do we have", "list the models", "que modelos hay instalados",
              "que modelos tiene el rack", "lista de modelos", "quais modelos temos", "que modelos estao instalados",
              "is the jetson busy", "what models run on the nodes"],
}
NEG = ["explain the fog of war", "write me a poem", "why is the sky blue", "como juego al cangrejo", "que es preceptoros",
       "translate hello to french", "what is a hex", "como funciona la niebla", "o que e o hexelion", "tell me a joke",
       "should i sign 266", "what is the weather", "como se llama el juego", "help me plan my day", "who are you",
       "how do i walk on the map", "que significa no_data", "explica el contrato del lab", "what is acurast",
       "por que el jetson es arm", "train a model for me", "install a model on the jetson", "como instalo la app",
       "delete my lab results", "sign the pr for me", "reboot the rack", "apaga el jetson", "who signs prs",
       "what does stale mean", "summarise the last meeting"]

# Zero-weight lexical router: a command only when BOTH a topic word and no action verb appear.
TOPIC = {
 "/firmas": r"\b(sign\w*|firm\w*|assin\w*|hitl|approv\w*|aprob\w*)\b",
 "/lab": r"\b(lab\w*|bench\w*)\b",
 "/preceptores": r"\b(preceptor\w*|agent\w*|working|trabaj\w*|online)\b",
 "/dispositivos": r"\b(devices?|dispositiv\w*|phones?|moviles?|hardware|nodes?)\b",
 "/modelos": r"\b(models?|modelos?|llms?|busy)\b",
 "/registro 5": r"\b(done|did|hecho|hiciste|fizeste|actions?|acciones|acoes|history)\b",
 "/capacidades": r"\b(capabilit\w*|tools?|herramientas|ferramentas|able|can|puedes|sabes)\b",
 "/estado": r"\b(status|estado|rack|up|bien|bem)\b",
}
ORDER = ["/firmas", "/lab", "/modelos", "/dispositivos", "/preceptores", "/registro 5", "/capacidades", "/estado"]
ACT = r"\b(sign the|for me|install|delete|borra|reboot|apaga|train|write|explain|explica|why|por que|what is|que es|que significa|o que e|who signs|how do i|como (juego|instalo|funciona|se llama))\b"


def lexical(q):
    n = A.normaliza(q)
    if re.search(ACT, n):
        return None
    for cmd in ORDER:
        if re.search(TOPIC[cmd], n):
            return cmd
    return None


def run(route):
    hit = tot = 0
    wrong = []
    for cmd, qs in C.items():
        for q in qs:
            tot += 1
            r = route(q)
            hit += r == cmd
            if r not in (None, cmd):
                wrong.append((q, r))
    fp = [(q, route(q)) for q in NEG if route(q)]
    return {"routed": "%d/%d" % (hit, tot), "misrouted": wrong, "false_positive": "%d/%d" % (len(fp), len(NEG)), "fp": fp}


exact = run(lambda q: {"state": "/estado", "capabilities": "/capacidades", "audit_last": "/registro 5", "signatures": "/firmas",
                       "lab": "/lab", "preceptors": "/preceptores", "devices": "/dispositivos", "models": "/modelos"}
            .get((lambda o: A.interpreta(o)[0] if o else None)(A.frase(q))) if A.frase(q) else None)
print("exact grammar :", json.dumps(exact, ensure_ascii=False))
print("lexical router:", json.dumps(run(lexical), ensure_ascii=False))
