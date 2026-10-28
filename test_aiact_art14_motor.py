"""VT11: modelo residente local; fixtures, sin daemon ni bases vivas."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class MotorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        contenido = b'GGUF' + b'fixture-modelo'
        self.sha = hashlib.sha256(contenido).hexdigest()
        self.blob = self.raiz / 'blobs' / ('sha256-' + self.sha)
        self.blob.parent.mkdir()
        self.blob.write_bytes(contenido)
        self.llamadas = []

    def modulo(self):
        import aiact_art14_motor as M
        return M

    def transporte(self, ruta, cuerpo=None):
        self.llamadas.append((ruta, cuerpo))
        if ruta == '/api/show':
            return {'modelfile': 'FROM ' + str(self.blob) + '\n'}
        if ruta == '/api/ps':
            return {'models': [{'name': 'mini:fixture', 'size': 4096, 'size_vram': 0}]}
        return {'done': True, 'model': 'mini:fixture', 'response': 'Dato local.', 'done_reason': 'stop'}

    def motor(self, transporte=None):
        M = self.modulo()
        parche = patch.object(M.consola, 'modelos_pc', return_value={
            'modelos': [{'id': 'mini:fixture', 'sha256': self.sha}]})
        parche.start()
        self.addCleanup(parche.stop)
        return M.MotorLocal('mini:fixture', self.sha, raiz=self.raiz,
                            peticion=transporte or self.transporte)

    def test_carga_explicita_residente_y_dos_turnos(self):
        m = self.motor()
        self.assertEqual(self.llamadas, [])
        with self.assertRaises(self.modulo().MotorNoDisponible):
            m('consulta')
        self.assertEqual(self.llamadas, [])
        self.assertEqual(m.activar()['estado'], 'MEDIDO')
        self.assertEqual(m('consulta'), 'Dato local.')
        self.assertEqual(m('consulta'), 'Dato local.')
        generaciones = [c for r, c in self.llamadas if r == '/api/generate']
        self.assertEqual(sum(c['prompt'] == '' for c in generaciones), 1)
        self.assertEqual(len(generaciones), 3)
        self.assertTrue(all(c['options']['temperature'] == 0 for c in generaciones))
        self.assertEqual(m.estado()['bytes_residentes'], 4096)
        self.assertIs(m.estado()['autoridad'], False)

    def test_hash_malo_cero_red(self):
        m = self.motor()
        self.blob.write_bytes(b'GGUFalterado')
        self.assertEqual(m.activar()['estado'], 'NO_DATA')
        self.assertEqual(self.llamadas, [])

    def test_gguf_falso_cero_red(self):
        m = self.motor()
        self.blob.write_bytes(b'HTML')
        with patch.object(self.modulo().consola, 'verificar_blob', return_value={'estado':'MEDIDO','bytes':4}):
            self.assertEqual(m.activar()['estado'], 'NO_DATA')
        self.assertEqual(self.llamadas, [])

    def test_from_ajeno_no_carga(self):
        def remoto(ruta, cuerpo=None):
            return {'modelfile': 'FROM otro.gguf'}
        m = self.motor(remoto)
        self.assertEqual(m.activar()['estado'], 'NO_DATA')
        self.assertIn('daemon', m.estado()['causa'])

    def test_timeout_fusible_sin_reintento(self):
        m = self.motor()
        m.activar()
        with patch.object(m, '_peticion', side_effect=TimeoutError) as p:
            with self.assertRaises(self.modulo().MotorNoDisponible):
                m('consulta')
            n = p.call_count
            with self.assertRaises(self.modulo().MotorNoDisponible):
                m('consulta')
            self.assertEqual(p.call_count, n)
        self.assertEqual(m.estado()['estado'], 'NO_DATA')

    def test_salida_invalida_abre_fusible(self):
        for alteracion in ({'response':''}, {'response':'x'*600}, {'done':False},
                           {'model':'otro'}, {'done_reason':'length'}, {'response':3}):
            with self.subTest(alteracion=alteracion):
                m = self.motor()
                m.activar()
                def respuesta(ruta, cuerpo=None):
                    original = self.transporte(ruta, cuerpo)
                    return {**original, **alteracion} if ruta == '/api/generate' else original
                with patch.object(m, '_peticion', side_effect=respuesta):
                    with self.assertRaises(self.modulo().MotorNoDisponible):
                        m('consulta')
                    n = len(self.llamadas)
                    with self.assertRaises(self.modulo().MotorNoDisponible):
                        m('consulta')
                    self.assertEqual(len(self.llamadas), n)

    def test_prompt_excesivo_no_infiere(self):
        m = self.motor()
        m.activar()
        n = len(self.llamadas)
        with self.assertRaises(self.modulo().MotorNoDisponible):
            m('é'*1537)
        self.assertEqual(len(self.llamadas), n)


    def test_transporte_cerrado_sin_proxy_ni_redireccion(self):
        from unittest.mock import MagicMock
        M = self.modulo()
        for status, cuerpo in ((302, b'{}'), (500, b'{}'), (200, b'{' ),
                               (200, b'{"x":NaN}'), (200, b'{"x":1,"x":2}'),
                               (200, b'[]'), (200, b'x'*65537)):
            with self.subTest(status=status, cuerpo=cuerpo[:24]):
                conexion = MagicMock()
                respuesta = conexion.getresponse.return_value
                respuesta.status = status
                respuesta.read.return_value = cuerpo
                with patch.object(M.http.client, 'HTTPConnection', return_value=conexion) as crear:
                    with self.assertRaises((ValueError, M.MotorNoDisponible)):
                        M._peticion('/api/ps')
                    crear.assert_called_once_with('127.0.0.1', 11434, timeout=60)
                    conexion.close.assert_called_once()
        with patch.object(M.http.client, 'HTTPConnection') as crear:
            with self.assertRaises(ValueError):
                M._peticion('/api/pull', {'model':'ajeno'})
            crear.assert_not_called()

    def test_tag_cambiado_tras_carga_cierra_antes_de_inferir(self):
        m = self.motor()
        m.activar()
        n = len(self.llamadas)
        with patch.object(self.modulo().consola, 'modelos_pc', return_value={'modelos':[]}):
            with self.assertRaises(self.modulo().MotorNoDisponible):
                m('consulta')
        self.assertEqual(len(self.llamadas), n)

    def test_rag_con_causa_segura_sin_fallback(self):
        import lab, memory
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'memory.db'
            memory.crear(str(db))
            with memory.abrir(str(db)) as c:
                memory.escribir_engrama(c, 'La arena usa rondas enteras', why='fixture', learned='rondas')
            m = self.motor()
            antes = db.read_bytes()
            with patch.object(lab, 'modelos_lab', side_effect=AssertionError('fallback prohibido')):
                result = lab.consultar_rag('arena', tmp, motor=m)
            self.assertEqual(result['estado'], 'NO_DATA')
            self.assertEqual(result['causa'], 'motor_no_activado')
            self.assertEqual(db.read_bytes(), antes)

    def test_fusible_no_concede_acciones(self):
        import orquestador
        from test_ficha_cartucho import manifiesto
        m = self.motor()
        for intent, payload, esperado in (
                ('DEPLOY_BUILDING', {'manifiesto':manifiesto()}, 'PROPOSED'),
                ('UPDATE_RAG', {}, 'NO_DATA')):
            raw = json.dumps({'esquema':orquestador.ESQUEMA,'intent':intent,'payload':payload}).encode()
            r = orquestador.enrutar(raw, consultar_rag=lambda _: self.fail('acción jamás llama al modelo'))
            self.assertEqual(r['estado'], esperado)
        self.assertEqual(self.llamadas, [])


    def test_cambio_durante_generacion_no_entrega_texto(self):
        m = self.motor()
        m.activar()
        def cambia(ruta, cuerpo=None):
            r = self.transporte(ruta, cuerpo)
            if ruta == '/api/generate':
                self.blob.write_bytes(b'GGUFotro')
            return r
        with patch.object(m, '_peticion', side_effect=cambia):
            with self.assertRaises(self.modulo().MotorNoDisponible):
                m('consulta')

    def test_adaptador_no_se_autoriza_por_hash_de_base(self):
        M = self.modulo()
        m = self.motor()
        with patch.object(M.consola, 'modelos_pc', return_value={'modelos':[
                {'id':'mini:fixture','sha256':self.sha,'adaptador':{'sha256':'a'*64}}]}):
            self.assertEqual(m.activar()['estado'], 'NO_DATA')
        self.assertEqual(self.llamadas, [])
        def remoto(ruta, cuerpo=None):
            r = self.transporte(ruta, cuerpo)
            if ruta == '/api/show':
                r['modelfile'] += 'ADAPTER distinto.gguf\n'
            return r
        m = self.motor(remoto)
        self.assertEqual(m.activar()['estado'], 'NO_DATA')
        self.assertFalse(any(r == '/api/generate' for r, _ in self.llamadas))

    def test_residencia_ausente_no_recarga_silenciosamente(self):
        m = self.motor()
        m.activar()
        def desaparecido(ruta, cuerpo=None):
            if ruta == '/api/ps':
                return {'models':[]}
            return self.transporte(ruta, cuerpo)
        n = sum(r == '/api/generate' for r, _ in self.llamadas)
        with patch.object(m, '_peticion', side_effect=desaparecido):
            with self.assertRaises(self.modulo().MotorNoDisponible):
                m('consulta')
        self.assertEqual(sum(r == '/api/generate' for r, _ in self.llamadas), n)

    def test_dos_hilos_comparten_un_fusible(self):
        import threading
        m = self.motor()
        m.activar()
        inicio = threading.Barrier(3)
        fallos = []
        def turno():
            inicio.wait()
            try:
                m('consulta')
            except self.modulo().MotorNoDisponible:
                fallos.append(1)
        with patch.object(m, '_peticion', side_effect=TimeoutError) as transporte:
            hilos = [threading.Thread(target=turno) for _ in range(2)]
            for hilo in hilos:
                hilo.start()
            inicio.wait()
            for hilo in hilos:
                hilo.join(timeout=2)
                self.assertFalse(hilo.is_alive())
            self.assertEqual(transporte.call_count, 1)
        self.assertEqual(len(fallos), 2)

    def test_arranque_cli_no_expone_motor_y_conserva_fallo(self):
        import contextlib, io
        from test_pwa import PWA
        M = self.modulo()
        with patch.object(PWA, 'ThreadingHTTPServer') as servidor, patch.object(PWA, 'BIND','127.0.0.1'):
            for args in (['--mini-local','mini:fixture'], ['--mini-sha256', self.sha]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    PWA.main(args)
            servidor.assert_not_called()
        with patch.object(PWA, 'BIND','exterior'), patch.object(PWA, 'ThreadingHTTPServer') as servidor:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                PWA.main(['--mini-local','mini:fixture','--mini-sha256',self.sha])
            servidor.assert_not_called()
        m = self.motor()
        with patch.object(PWA._motor_local, 'MotorLocal', return_value=m), patch.object(m,'activar',return_value=m.estado()), patch.object(PWA,'BIND','127.0.0.1'), patch.object(PWA,'ThreadingHTTPServer') as servidor:
            with contextlib.redirect_stdout(io.StringIO()):
                PWA.main(['--mini-local','mini:fixture','--mini-sha256',self.sha])
            self.assertIs(servidor.return_value.motor_orquestador, m)
            self.assertIsNotNone(servidor.return_value.motor_orquestador)


if __name__ == '__main__':
    unittest.main()
