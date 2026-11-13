"""Autonomy parity S3b · turn sounds: off until the person turns them on, never without the words, malformed is silent."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import audio_feedback as AF
from test_talk_turn_parity import node

ROOT = Path(__file__).resolve().parent

HOST = """
const made = [];
function host(opts) {
  const kept = {};
  const storage = opts.noStorage ? undefined : { getItem: k => { if (opts.throwing) throw new Error('x'); return k in kept ? kept[k] : null; },
    setItem: (k, v) => { if (opts.throwing) throw new Error('x'); kept[k] = String(v); }, removeItem: k => { delete kept[k]; } };
  const param = () => ({ setValueAtTime(v) { this.v = v; }, exponentialRampToValueAtTime(v) { this.max = Math.max(this.max || 0, v); } });
  function Ctx() { made.push(this); this.state = 'running'; this.currentTime = 0; this.destination = {}; this.osc = 0; this.gains = []; }
  Ctx.prototype.createGain = function () { const g = { gain: param(), connect() {} }; this.gains.push(g); return g; };
  Ctx.prototype.createOscillator = function () { this.osc++; return { frequency: param(), connect() {}, start() {}, stop() {} }; };
  const h = { localStorage: storage };
  if (!opts.noAudio) h.AudioContext = Ctx;
  return h;
}
const S = require('./interface/acho_sonido.js');
"""


def run(body):
    return node(HOST + body)


class Sound(unittest.TestCase):
    MOTIFS = {c: AF.motif_for_class(c) for c in AF.ACHO_CLASSES}

    def test_off_until_turned_on_and_off_plays_nothing(self):
        got = run("(async()=>{const h=host({});const a=await S.play({class:'ok',motif:%s},h);"
                  "console.log(JSON.stringify([S.enabled(h),a,made.length,S.describe(h)]))})()" % json.dumps(self.MOTIFS["ok"]))
        self.assertEqual(got[:3], [False, {"state": "off", "cause": "sound is off until you turn it on"}, 0])
        self.assertIn("The words are always on screen and for screen readers", got[3])

    def test_every_class_the_server_sends_plays_once_turned_on(self):
        got = run("(async()=>{const h=host({});S.set(true,h);const m=%s;const out=[];"
                  "for (const c of Object.keys(m)) out.push([c,(await S.play({class:c,motif:m[c]},h)).state]);"
                  "const ctx=made[0];console.log(JSON.stringify([out,made.length,Math.max(...ctx.gains.map(g=>g.gain.max||0))]))})()"
                  % json.dumps(self.MOTIFS))
        rows, contexts, loudest = got
        self.assertEqual(sorted(rows), sorted([c, "played"] for c in AF.ACHO_CLASSES))
        self.assertEqual(contexts, 1)                 # one audio context, reused
        self.assertLessEqual(loudest, 0.12)

    def test_malformed_is_no_data_and_silent(self):
        ok = self.MOTIFS["ok"]
        bad = [None, {}, {"class": "success", "motif": ok}, {"class": "ok"},
               {"class": "ok", "motif": dict(ok, portadora=5000)}, {"class": "ok", "motif": dict(ok, dur="0.3")},
               {"class": "ok", "motif": dict(ok, vibrato="yes")}, {"class": "ok", "motif": dict(ok, indice=-1)}]
        got = run("(async()=>{const h=host({});S.set(true,h);const out=[];for (const b of %s) out.push(await S.play(b,h));"
                  "console.log(JSON.stringify([out,made.length]))})()" % json.dumps(bad))
        states, contexts = got
        self.assertTrue(all(s["state"] == "NO_DATA" for s in states))
        self.assertEqual([s["cause"] for s in states[:4]], ["acho_missing", "acho_class_unknown", "acho_class_unknown",
                                                           "acho_motif_invalid"])
        self.assertEqual(contexts, 0)

    def test_no_web_audio_or_no_storage_fail_closed(self):
        got = run("(async()=>{const a=host({noAudio:true});S.set(true,a);const b=host({throwing:true});"
                  "const c=host({noStorage:true});console.log(JSON.stringify([await S.play({class:'ok',motif:%s},a),"
                  "S.set(true,b),S.enabled(b),S.set(true,c),S.enabled(c)]))})()" % json.dumps(self.MOTIFS["ok"]))
        self.assertEqual(got, [{"state": "NO_DATA", "cause": "web_audio_unavailable"}, False, False, False, False])

    def test_the_switch_and_the_wiring(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        js = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn('<input type="checkbox" id="acho-sonido" aria-describedby="acho-sonido-estado">', html)
        self.assertIn('<p class="pie" id="acho-sonido-estado" role="status" aria-live="polite">', html)
        self.assertLess(html.index('src="/acho_sonido.js?v=2"'), html.index('src="/app.js?v=38"'))
        self.assertIn("if (turno && turno.sentence && window.PreceptorAchoSonido)", js)   # never without the words
        self.assertIn('"/acho_sonido.js?v=2"', sw)
        self.assertIn('const Cache = "preceptoros-armazon-v191";', sw)
        self.assertIn('"/acho_sonido.js": ("acho_sonido.js"', (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8"))
        src = (ROOT / "interface/acho_sonido.js").read_text(encoding="utf-8")
        for word in ("fetch(", "XMLHttpRequest", "sendBeacon"):
            self.assertNotIn(word, src)
        self.assertEqual(sorted(run("console.log(JSON.stringify(S.classes))")), sorted(AF.ACHO_CLASSES))


if __name__ == "__main__":
    unittest.main()
