"""Contratos de canal y tier 2 con vectores sintéticos, sin inferencia ni BD viva."""
import copy
import hashlib
import json
import socket
import sqlite3
import subprocess
import unittest
from unittest import mock

import decision_evento as D
import eleccion_tier2 as E

HUELLA = 'sha256:' + 'a' * 64
OPCIONES = ['seguir', 'esperar']


def decision(**cambios):
    dato = dict(v=1, rol='agente', alternativas=OPCIONES[:], eleccion='seguir',
                encargo_ref='issue:40', firmo_ref='issue:40#comment-1', sello='PROPUESTA',
                ancla='docs/contratos-decision.md:1', utc='2026-10-18T00:00:00Z')
    dato.update(cambios)
    return dato


def eleccion():
    return dict(schema_v='hexelion.eleccion.tier2/1', content_v=HUELLA,
                plan_hash=HUELLA, choice='seguir', score=0.25, noul=False,
                probs=[{'opcion':'seguir','p_bp':6000},{'opcion':'esperar','p_bp':4000}],
                judge={'veredicto':'acuerdo','contra':'fixture','regla':'igualdad',
                       'calibracion':{'estado':'SIMULATED','sha256':HUELLA,'muestras':2,
                                      'aciertos':1,'causa':'vector sintético, no calibración real'}},
                arnes={'tier':2,'donde':'EMULADO','modelo':'fixture','modo':'puntuar',
                       'hash':HUELLA,'build':'fixture-1','configuracion':{'semilla':1}},
                no_data=[])


class Decision(unittest.TestCase):
    def test_forma_dirimida_y_ningun_hlc(self):
        self.assertIsNone(D.validar_evento_decision(decision()))
        self.assertIsNotNone(D.validar_evento_decision(decision(hlc={})))
        self.assertIsNotNone(D.validar_evento_decision(decision(anclaje='doc.md:1')))

    def test_campos_cerrados(self):
        for clave in decision():
            with self.subTest(clave=clave):
                dato=decision();del dato[clave]
                self.assertIsNotNone(D.validar_evento_decision(dato))
        for dato in (None, [], decision(v=True), decision(v=2), decision(extra=1),
                     decision(utc='2026-02-30T00:00:00Z'),decision(utc='ayer'),
                     decision(eleccion='fuera'),decision(rol='nombre-personal'),
                     decision(alternativas=['seguir']*2),decision(ancla='../otra.md:1')):
            with self.subTest(dato=dato):self.assertIsNotNone(D.validar_evento_decision(dato))

    def test_orden_insercion_no_utc(self):
        filas=[{'n':2,'tipo':'decision','cuerpo':decision(utc='2026-10-17T00:00:00Z')},
               {'n':1,'tipo':'decision','cuerpo':decision()},
               {'n':3,'tipo':'decision','cuerpo':decision()}]
        self.assertEqual([f['n'] for f in D.ordenar_decisiones(filas)],[1,2,3])
        self.assertEqual(len(D.ordenar_decisiones(filas)),3)

    def test_techo_real_utf8(self):
        for largo in (1023,1024,1025):
            dato=decision(alternativas=['o'+str(i) for i in range(20)],eleccion='o0')
            resto=largo-len(D._canonico(dato))
            for i in range(19,0,-1):
                n=min(resto,64-len(dato['alternativas'][i].encode()))
                dato['alternativas'][i]+='x'*n;resto-=n
            self.assertEqual(resto,0)
            self.assertEqual(len(D._canonico(dato)),largo)
            self.assertEqual(D.validar_evento_decision(dato) is None,largo<1024)
        self.assertIsNotNone(D.validar_evento_decision(decision(ancla='é'*1024)))

    def test_referencia_no_es_firma(self):
        self.assertIsNotNone(D.validar_evento_decision(decision(firmo_ref=None)))
        self.assertIsNone(D.validar_evento_decision(decision(firmo_ref=None),
                         [{'campo':'firmo_ref','causa':'gesto pendiente'}]))

    def test_espejos_simulados_hash_y_discrepancia(self):
        dato=decision(); a=D.recibo_espejo(dato); b=D.recibo_espejo(dato)
        self.assertEqual(a['estado'],'SIMULATED')
        self.assertEqual(a['payload_sha256'],hashlib.sha256(D._canonico(dato)).hexdigest())
        self.assertTrue(D.cotejar_espejos(dato,a,b))
        for clave,valor in [('payload_sha256','0'*64),('estado','FIRMADO'),('recuento',2)]:
            with self.subTest(clave=clave):
                malo=dict(b,**{clave:valor})
                self.assertFalse(D.cotejar_espejos(dato,a,malo))
                self.assertFalse(D.cotejar_espejos(dato,malo,malo))


class Tier2(unittest.TestCase):
    def test_valido_sin_umbral_semantico(self):
        for score in (None,-2,0.25,10001):
            dato=eleccion();dato['score']=score
            self.assertEqual(E.validar(dato,OPCIONES),[])
        dato=eleccion();dato['choice']='esperar'
        self.assertEqual(E.validar(dato,OPCIONES),[])

    def test_epsilon_declarado_y_suma_normalizada(self):
        self.assertEqual(E.EPSILON,0)
        self.assertEqual(E.validar(eleccion(),OPCIONES),[])
        for suma in (9999,10001):
            dato=eleccion();dato['probs'][1]['p_bp']=suma-6000
            self.assertTrue(E.validar(dato,OPCIONES))
        with mock.patch.object(E,'EPSILON',None):
            self.assertTrue(E.validar(eleccion(),OPCIONES))

    def test_epsilon_cero_no_redondea_desviaciones_pequenas(self):
        dato=eleccion()
        dato['probs']=[{'opcion':'seguir','p_bp':10000}, {'opcion':'esperar','p_bp':1e-300}]
        self.assertTrue(E.validar(dato,OPCIONES))
        dato['probs']=[{'opcion':'seguir','p_bp':6000.1}, {'opcion':'esperar','p_bp':3999.9}]
        self.assertEqual(E.validar(dato,OPCIONES),[])

    def test_cero_efectos_en_validacion(self):
        with mock.patch('builtins.open',side_effect=AssertionError('archivo')), \
             mock.patch.object(sqlite3,'connect',side_effect=AssertionError('BD')), \
             mock.patch.object(socket,'socket',side_effect=AssertionError('red')), \
             mock.patch.object(subprocess,'run',side_effect=AssertionError('proceso')):
            self.assertEqual(E.validar(eleccion(),OPCIONES),[])
            self.assertIsNone(D.validar_evento_decision(decision()))
            for clave in ('estado.nivel','ledger','interruptor','firma'):
                dato=eleccion();dato[clave]=True
                self.assertTrue(E.validar(dato,OPCIONES))

    def test_score_finito_o_null(self):
        for score in (True,'0.9',float('nan'),float('inf'),float('-inf')):
            with self.subTest(score=score):
                dato=eleccion();dato['score']=score
                self.assertTrue(E.validar(dato,OPCIONES))

    def test_abstencion_coherente(self):
        dato=eleccion();dato.update(choice='NO_DATA',noul=True,score=None,probs=[],
            no_data=[{'campo':'probs','causa':'medición ausente'}])
        self.assertEqual(E.validar(dato,OPCIONES),[])
        for cambio in ({'score':0},{'choice':'seguir'},{'noul':False},{'no_data':[]}):
            with self.subTest(cambio=cambio):self.assertTrue(E.validar(dict(dato,**cambio),OPCIONES))

    def test_probs_cerradas_y_finitas(self):
        for cambio in ([],[{'opcion':'seguir','p_bp':10000}],
                       [{'opcion':'seguir','p_bp':5000}]*2,
                       [{'opcion':'fuera','p_bp':6000},{'opcion':'esperar','p_bp':4000}]):
            dato=eleccion();dato['probs']=cambio
            self.assertTrue(E.validar(dato,OPCIONES))
        for valor in (-1,True,float('nan'),float('inf'),'6000',{},None):
            dato=eleccion();dato['probs'][0]['p_bp']=valor
            self.assertTrue(E.validar(dato,OPCIONES))

    def test_juez_sin_rastro_o_veredicto_ajeno(self):
        for cambio in ('ausente','nulo','ajeno','sin_huella','conteo_falso'):
            dato=eleccion()
            if cambio=='ausente':del dato['judge']['calibracion']
            elif cambio=='nulo':dato['judge']['calibracion']=None
            elif cambio=='ajeno':dato['judge']['veredicto']='seguro'
            elif cambio=='sin_huella':dato['judge']['calibracion']['sha256']=None
            else:dato['judge']['calibracion']['aciertos']=3
            self.assertTrue(E.validar(dato,OPCIONES))
        dato=eleccion();dato['judge']['veredicto']='NO_DATA'
        dato['judge']['calibracion']={'estado':'NO_DATA','sha256':None,'muestras':0,
             'aciertos':None,'causa':'no hay evaluación'}
        self.assertEqual(E.validar(dato,OPCIONES),[])
        dato['judge']['veredicto']='acuerdo'
        self.assertTrue(E.validar(dato,OPCIONES))

    def test_arnes_obligatorio_no_acepta_tier1(self):
        for clave in eleccion()['arnes']:
            dato=eleccion();del dato['arnes'][clave]
            self.assertTrue(E.validar(dato,OPCIONES))
        for cambio in ({'tier':1},{'tier':True},{'hash':'modelo'},{'build':''},
                       {'configuracion':None},{'extra':1}):
            dato=eleccion();dato['arnes'].update(cambio)
            self.assertTrue(E.validar(dato,OPCIONES))

    def test_campos_y_opciones_cerrados(self):
        for clave in eleccion():
            dato=eleccion();del dato[clave]
            self.assertTrue(E.validar(dato,OPCIONES))
        for opciones in ([],['seguir']*2,[True],[''],list(map(str,range(21)))):
            self.assertTrue(E.validar(eleccion(),opciones))
        self.assertTrue(E.validar(dict(eleccion(),extra=True),OPCIONES))

    def test_determinismo_y_no_mutacion(self):
        dato=eleccion();antes=copy.deepcopy(dato)
        self.assertEqual(E.validar(dato,OPCIONES),E.validar(dato,OPCIONES))
        self.assertEqual(dato,antes)


if __name__=='__main__':unittest.main()
