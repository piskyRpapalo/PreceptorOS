import json
import copy
from test_lab import Base, L

class TestFraseDeterminista(Base):
    def test_propuesta_no_json(self):
        # Prueba 1: Verificar que la frase contiene los valores esperados y no llaves JSON
        resultado = L.frase('propuesta', {'tarea':'ensayo','estado':'pendiente','runner':'banco'})
        assert 'ensayo' in resultado, "La frase debe contener 'ensayo'"
        assert 'pendiente' in resultado, "La frase debe contener 'pendiente'"
        # Verificar que no contiene llaves JSON (formato crudo)
        assert '{' not in resultado, "La frase no debe contener llaves JSON crudas"

        # Reordenar claves y verificar que la frase sea idéntica
        dict_reordenado = {'estado':'pendiente','tarea':'ensayo','runner':'banco'}
        resultado_reordenado = L.frase('propuesta', dict_reordenado)
        assert resultado == resultado_reordenado, "Reordenar claves no debe cambiar la frase"

    def test_evidencia_cero_consulta(self):
        # Prueba 2: Verificar conservación del cero y el valor 'consulta'
        resultado = L.frase('evidencia', {'pregunta':'consulta','hechos':0,'descartados':0})
        assert 'consulta' in resultado, "La frase debe contener 'consulta'"
        # Asegurar que los ceros se conservan implícitamente en la lógica de conversión a texto
        assert '0' in resultado or 'cero' in resultado.lower(), "La frase debe reflejar el valor cero"

    def test_registro_eventos_cuerpo(self):
        # Prueba 3: Verificar registro y eventos
        self.registro([('2026-10-15T00:00:00Z','propuesta','claude-app',
                       {'tarea':'ensayo','estado':'pendiente','dato':[1,2]} )])

        estado, filas = L.eventos(self.casa)
        assert len(filas) > 0, "Debe haber al menos una fila de eventos"

        # Verificar el cuerpo en la máquina
        assert filas[0]['maquina']['cuerpo'] == {'tarea':'ensayo','estado':'pendiente','dato':[1,2]}, \
            "El cuerpo registrado debe coincidir exactamente"

        # Verificar que el texto contenga 'ensayo' sin JSON crudo
        texto = filas[0]['texto']
        assert 'ensayo' in texto, "El texto debe contener 'ensayo'"
        assert '{' not in texto, "El texto no debe contener llaves JSON crudas"

    def test_inmutabilidad_copy_deep(self):
        cuerpo = {'tarea': 'ensayo', 'estado': 'pendiente', 'dato': [1, 2]}
        anterior = copy.deepcopy(cuerpo)
        L.frase('propuesta', cuerpo)
        self.assertEqual(cuerpo, anterior)

if __name__ == '__main__':
    import unittest
    unittest.main()
