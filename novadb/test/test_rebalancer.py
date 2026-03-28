import unittest
import numpy as np
from datetime import datetime, timedelta
from novadb.core.node import Node
from novadb.core.graph import NovaGraph, similitud_coseno
from novadb.core.rebalancer import Rebalancer

class MockEmbedder:
    def encode(self, text: str):
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

class TestRebalancer(unittest.TestCase):
    def setUp(self):
        self.graph = NovaGraph()
        self.rebalancer = Rebalancer(self.graph)
    
    def _crear_macro(self, texto="Macro Test", vector=None):
        if vector is None:
            vector = np.array([0.5, 0.5, 0.0])
        n = Node(text=texto, vector=vector, tipo="MACRO")
        self.graph.nodes[n.id] = n
        return n
    
    def _crear_medio(self, texto="Medio Test", padre_id=None, vector=None, hijos_ids=None):
        if vector is None:
            vector = np.array([0.6, 0.4, 0.0])
        n = Node(text=texto, vector=vector, tipo="MEDIO")
        if padre_id:
            n.padres.append(padre_id)
        if hijos_ids:
            n.hijos = list(hijos_ids)
        self.graph.nodes[n.id] = n
        if padre_id:
            padre = self.graph.nodes.get(padre_id)
            if padre:
                padre.hijos.append(n.id)
        return n
    
    def _crear_memoria(self, texto="Memoria Test", padre_id=None, vector=None):
        if vector is None:
            vector = np.array([0.7, 0.3, 0.0])
        n = Node(text=texto, vector=vector, tipo="MEMORIA")
        if padre_id:
            n.padres.append(padre_id)
        self.graph.nodes[n.id] = n
        if padre_id:
            padre = self.graph.nodes.get(padre_id)
            if padre:
                padre.hijos.append(n.id)
        return n
    
    def test_necesita_rebalanceo_semanal(self):
        self.rebalancer.ultimo_rebalanceo = datetime.now() - timedelta(days=8)
        self.assertTrue(self.rebalancer.necesita_rebalanceo())
    
    def test_necesita_rebalanceo_critico(self):
        macro = self._crear_macro()
        medio1 = self._crear_medio(padre_id=macro.id, texto="Medio1", vector=np.array([0.5, 0.5, 0.0]))
        medio2 = self._crear_medio(padre_id=macro.id, texto="Medio2", vector=np.array([0.6, 0.4, 0.0]))
        for i in range(20):
            self._crear_memoria(padre_id=medio1.id)
        for i in range(1):
            self._crear_memoria(padre_id=medio2.id)
        
        self.assertTrue(self.rebalancer.necesita_rebalanceo())
    
    def test_no_necesita_rebalanceo_reciente(self):
        self.rebalancer.ultimo_rebalanceo = datetime.now() - timedelta(days=2)
        self.assertFalse(self.rebalancer.necesita_rebalanceo())
    
    def test_grupo_ideal_vacio(self):
        ideal = self.rebalancer._grupo_ideal()
        self.assertEqual(ideal, 3)
    
    def test_grupo_ideal_calculo(self):
        macro = self._crear_macro()
        medio = self._crear_medio(padre_id=macro.id)
        for i in range(100):
            self._crear_memoria(padre_id=medio.id)
        
        ideal = self.rebalancer._grupo_ideal()
        self.assertGreater(ideal, 3)
    
    def test_calcular_balance_sin_medios(self):
        balance = self.rebalancer._calcular_balance()
        self.assertEqual(balance["balance_ratio"], 1.0)
    
    def test_calcular_balance(self):
        macro = self._crear_macro()
        medio = self._crear_medio(padre_id=macro.id)
        for i in range(10):
            self._crear_memoria(padre_id=medio.id)
        
        balance = self.rebalancer._calcular_balance()
        self.assertIn("balance_ratio", balance)
        self.assertGreaterEqual(balance["balance_ratio"], 0.0)
        self.assertLessEqual(balance["balance_ratio"], 1.0)
    
    def test_fusionar_medio_sin_hermanos(self):
        macro = self._crear_macro()
        medio_vacio = self._crear_medio(padre_id=macro.id, texto="Vacio")
        resultado = self.rebalancer._fusionar_medio(medio_vacio)
        self.assertFalse(resultado)
        self.assertIn(medio_vacio.id, self.graph.nodes)
    
    def test_fusionar_medio_exitoso(self):
        macro = self._crear_macro()
        medio_vacio = self._crear_medio(padre_id=macro.id, texto="Vacio", vector=np.array([0.5, 0.5, 0.0]))
        medio_hermano = self._crear_medio(padre_id=macro.id, texto="Hermano", vector=np.array([0.55, 0.45, 0.0]))
        
        mem1 = self._crear_memoria(padre_id=medio_vacio.id, vector=np.array([0.6, 0.4, 0.0]))
        mem2 = self._crear_memoria(padre_id=medio_vacio.id, vector=np.array([0.7, 0.3, 0.0]))
        
        self.assertEqual(len(medio_vacio.hijos), 2)
        self.assertEqual(len(medio_hermano.hijos), 0)
        
        resultado = self.rebalancer._fusionar_medio(medio_vacio)
        
        self.assertTrue(resultado)
        self.assertNotIn(medio_vacio.id, self.graph.nodes)
        self.assertEqual(len(medio_hermano.hijos), 2)
        self.assertIn(mem1.id, medio_hermano.hijos)
        self.assertIn(mem2.id, medio_hermano.hijos)
    
    def test_redistribuir_medio_sin_exceso(self):
        macro = self._crear_macro()
        medio = self._crear_medio(padre_id=macro.id)
        for i in range(3):
            self._crear_memoria(padre_id=medio.id)
        
        redistribuidos = self.rebalancer._redistribuir_medio(medio, grupo_ideal=5)
        self.assertEqual(redistribuidos, 0)
    
    def test_redistribuir_medio_sin_hermanos(self):
        macro = self._crear_macro()
        medio = self._crear_medio(padre_id=macro.id)
        for i in range(20):
            self._crear_memoria(padre_id=medio.id)
        
        redistribuidos = self.rebalancer._redistribuir_medio(medio, grupo_ideal=5)
        self.assertEqual(redistribuidos, 0)
    
    def test_redistribuir_medio_exitoso(self):
        macro = self._crear_macro()
        medio_sobrecargado = self._crear_medio(padre_id=macro.id, texto="Sobrecargado", vector=np.array([0.5, 0.5, 0.0]))
        medio_destino = self._crear_medio(padre_id=macro.id, texto="Destino", vector=np.array([0.55, 0.45, 0.0]))
        
        for i in range(15):
            self._crear_memoria(padre_id=medio_sobrecargado.id, vector=np.array([0.6 + i*0.01, 0.4 - i*0.01, 0.0]))
        
        self.assertGreater(len(medio_sobrecargado.hijos), 10)
        
        redistribuidos = self.rebalancer._redistribuir_medio(medio_sobrecargado, grupo_ideal=5)
        
        self.assertGreater(redistribuidos, 0)
        self.assertLess(len(medio_sobrecargado.hijos), 15)
    
    def test_rebalanceo_vacio(self):
        resultado = self.rebalancer.rebalancear()
        self.assertEqual(resultado["fusionados"], 0)
        self.assertEqual(resultado["redistribuidos"], 0)
    
    def test_rebalanceo_sin_medios(self):
        macro = self._crear_macro()
        for i in range(10):
            self._crear_memoria(padre_id=macro.id)
        
        resultado = self.rebalancer.rebalancear()
        self.assertEqual(resultado["fusionados"], 0)
        self.assertEqual(resultado["redistribuidos"], 0)
    
    def test_rebalanceoCompleto(self):
        macro = self._crear_macro()
        
        medio_vacio = self._crear_medio(padre_id=macro.id, texto="Vacio", vector=np.array([0.5, 0.5, 0.0]))
        medio_hermano = self._crear_medio(padre_id=macro.id, texto="Hermano", vector=np.array([0.55, 0.45, 0.0]))
        self._crear_memoria(padre_id=medio_vacio.id, vector=np.array([0.6, 0.4, 0.0]))
        
        medio_sobrecargado = self._crear_medio(padre_id=macro.id, texto="Sobrecargado", vector=np.array([0.5, 0.5, 0.0]))
        for i in range(15):
            self._crear_memoria(padre_id=medio_sobrecargado.id, vector=np.array([0.6 + i*0.01, 0.4 - i*0.01, 0.0]))
        
        self.rebalancer.ultimo_rebalanceo = datetime.now() - timedelta(days=8)
        
        resultado = self.rebalancer.rebalancear()
        
        self.assertGreater(resultado["fusionados"] + resultado["redistribuidos"], 0)
    
    def test_rebalanceo_no_rompe_relaciones(self):
        macro = self._crear_macro()
        medio = self._crear_medio(padre_id=macro.id)
        mems = []
        for i in range(10):
            m = self._crear_memoria(padre_id=medio.id, vector=np.array([0.5 + i*0.05, 0.5 - i*0.05, 0.0]))
            mems.append(m)
        
        self.rebalancer.ultimo_rebalanceo = datetime.now() - timedelta(days=8)
        self.rebalancer.rebalancear()
        
        for m in mems:
            nodo = self.graph.nodes.get(m.id)
            self.assertIsNotNone(nodo)
            tiene_padre_medio = any(
                self.graph.nodes.get(p) and self.graph.nodes[p].tipo == "MEDIO"
                for p in nodo.padres
            )
            self.assertTrue(tiene_padre_medio)
    
    def test_distancia_promedio(self):
        macro = self._crear_macro()
        medio = self._crear_medio(padre_id=macro.id)
        mem = self._crear_memoria(padre_id=medio.id, vector=np.array([0.7, 0.3, 0.0]))
        
        candidatos = [medio]
        distancia = self.rebalancer._distancia_promedio(mem.id, candidatos)
        
        self.assertGreaterEqual(distancia, 0.0)
    
    def test_distancia_promedio_sin_vector(self):
        macro = self._crear_macro()
        medio = self._crear_medio(padre_id=macro.id)
        mem = self._crear_memoria(padre_id=medio.id)
        mem.vector = None
        
        distancia = self.rebalancer._distancia_promedio(mem.id, [medio])
        self.assertEqual(distancia, float('inf'))

if __name__ == '__main__':
    unittest.main()
