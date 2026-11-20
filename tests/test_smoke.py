"""Verifica que o ambiente e os arquivos de referência estão no lugar (tarefa T00)."""
import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures"
RAIZ = Path(__file__).parent.parent


def _json(nome: str):
    with open(FIX / nome, encoding="utf-8") as f:
        return json.load(f)


def test_transcricao_de_referencia():
    d = _json("transcript_tuVNNEO-NKc_pt.json")
    assert d["error"] is None
    assert len(d["transcript_segments"]) == 685
    assert d["transcript_segments"][-1]["end"] == 1424.88


def test_gabaritos_existem():
    texto = _json("gabarito_textos_c1_c7_c8.json")
    assert [c["id"] for c in texto["cortes"]] == ["C1", "C7", "C8"]
    tempos = _json("gabarito_tempos.json")
    assert len(tempos["cortes"]) == 8


def test_schema_existe():
    assert (RAIZ / "schemas" / "saida_v1.schema.json").exists()
