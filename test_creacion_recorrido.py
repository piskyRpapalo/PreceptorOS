"""E8: end-to-end HTTP measurement for a signed local creation."""
import hashlib
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import importlib.util
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

import creacion_import as I

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "tests/fixtures/creation/valid.json"
PACKAGE_JS = ROOT / "assets/creation-view/game/creation_package.js"
SPEC = importlib.util.spec_from_loader(
    "creation_e8_pwa", SourceFileLoader("creation_e8_pwa", str(ROOT / "bin/preceptoros-pwa")))
PWA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PWA)


class QuietPWA(PWA.PWA):
    def log_message(self, _format, *_args):
        pass


class CreationJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = FIXTURE.read_bytes()

    def test_python_and_browser_verifiers_match_manifest_frame_and_audio(self):
        checked = I.validate(self.package)
        script = ("const P=require(process.argv[1]);let s='';process.stdin.setEncoding('utf8');"
                  "process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>P.verify(s).then(async v=>{"
                  "const f=P.decode(v.package.files['frame.json']);const a=P.decode(v.package.files['declaration.wav']);"
                  "console.log(JSON.stringify({id:v.id,frame:await P.sha256(f),audio:await P.sha256(a)}));"
                  "}).catch(e=>{console.error(e);process.exitCode=1;}));")
        result = subprocess.run(["node", "-e", script, str(PACKAGE_JS)],
            input=self.package.decode("utf-8"), capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        browser = json.loads(result.stdout)
        self.assertEqual(browser["id"], checked["id"])
        for name, key in (("frame.json", "frame"), ("declaration.wav", "audio")):
            self.assertEqual(browser[key], hashlib.sha256(checked["files"][name]).hexdigest())

    def test_sabotage_switch_rejects_changed_signed_bytes(self):
        damaged = json.loads(self.package)
        value = damaged["files"]["declaration.wav"]
        damaged["files"]["declaration.wav"] = ("A" if value[0] != "A" else "B") + value[1:]
        if os.environ.get("CREATION_JOURNEY_SABOTAGE") == "1":
            I.validate(json.dumps(damaged).encode())
        with self.assertRaises(I.CreationError):
            I.validate(json.dumps(damaged).encode())

    def test_upload_fresh_read_fixed_resources_and_restart(self):
        with tempfile.TemporaryDirectory(prefix="creation-journey-") as directory:
            env = mock.patch.dict(os.environ, {"PRECEPTOROS_CREATION_DIR": str(Path(directory) / "store")})
            env.start(); servers=[]; threads=[]
            try:
                try:
                    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietPWA)
                except PermissionError as exc:
                    self.skipTest("NO_DATA · loopback bind denied: " + type(exc).__name__)
                servers.append(server)
                def start(instance):
                    thread=threading.Thread(target=instance.serve_forever,daemon=True)
                    thread.start();threads.append(thread)
                def request(port,method,path,body=None,headers=None):
                    conn=HTTPConnection("127.0.0.1",port,timeout=5)
                    conn.request(method,path,body=body,headers=headers or {})
                    response=conn.getresponse(); value=(response.status,response.getheaders(),response.read())
                    conn.close();return value
                start(server); port=server.server_address[1]
                origin=f"http://127.0.0.1:{port}"
                status,_headers,body=request(port,"POST","/api/creaciones",self.package,{
                    "Origin":origin,"Content-Type":"application/json","Content-Length":str(len(self.package))})
                self.assertEqual(status,201)
                receipt=json.loads(body); identifier=I.validate(self.package)["id"]
                self.assertEqual(receipt["id"],identifier)
                self.assertEqual(receipt["url"],"/creaciones/"+identifier)

                status,headers,exact=request(port,"GET","/api/creaciones/"+identifier)
                self.assertEqual(status,200);self.assertEqual(dict(headers).get("Cache-Control"),"no-store")
                self.assertEqual(exact,self.package);self.assertEqual(I.validate(exact)["id"],identifier)
                status,_headers,page=request(port,"GET",receipt["url"])
                self.assertEqual(status,200);self.assertIn(b"Verified creation",page)
                status,_headers,raw=request(port,"GET","/creation-view/manifest.json")
                self.assertEqual(status,200);manifest=json.loads(raw)
                for name,pin in manifest["files"].items():
                    status,_headers,data=request(port,"GET","/creation-view/"+name)
                    self.assertEqual(status,200,name)
                    self.assertEqual(len(data),pin["size"],name)
                    self.assertEqual(hashlib.sha256(data).hexdigest(),pin["sha256"],name)

                server.shutdown();server.server_close();threads[-1].join(timeout=5)
                restarted=ThreadingHTTPServer(("127.0.0.1",0),QuietPWA);servers.append(restarted);start(restarted)
                status,_headers,after=request(restarted.server_address[1],"GET","/api/creaciones/"+identifier)
                self.assertEqual(status,200);self.assertEqual(after,self.package)
            finally:
                for server in servers:
                    server.shutdown();server.server_close()
                for thread in threads:
                    thread.join(timeout=5)
                env.stop()


if __name__ == "__main__":
    unittest.main()
