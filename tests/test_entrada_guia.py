"""Pruebas de los puntos de entrada con los nombres de la guía (src/model.py, src/train.py) y
del reporte de resultados (tools/generar_resumen.py)."""

import importlib.util

from src import model, modeling, reglas, train
from src.utils import RAIZ


def test_model_reexporta_sin_duplicar():
    assert model.construir_modelo is modeling.construir_modelo
    assert model.puntaje_d2 is reglas.puntaje_d2
    assert model.espacio_de("hibrido") == modeling.espacio_de("hibrido")


def test_train_entrena_y_compara_en_c4(capsys, tmp_path):
    salida = tmp_path / "seleccion.csv"
    assert train.main(["--trials", "1", "--salida", str(salida)]) == 0
    texto = capsys.readouterr().out
    assert "D2 · señales administrativas" in texto and "diagnostico" in texto
    assert salida.exists()


def _resumen():
    ruta = RAIZ / "tools" / "generar_resumen.py"
    especificacion = importlib.util.spec_from_file_location("generar_resumen", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def test_resumen_de_resultados(tmp_path, monkeypatch):
    resumen = _resumen()
    monkeypatch.setattr(resumen, "REPORTES", tmp_path)
    ruta = resumen.generar("real")
    texto = ruta.read_text(encoding="utf-8")
    assert "1,97 [1,24; 2,56]" in texto and "Prueba final en C5" in texto
    assert "0.1" not in texto.replace("(0.076)", "")    # coma decimal en todo el reporte
