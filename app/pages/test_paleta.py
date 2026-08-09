"""Testes de paleta.py — rótulos canônicos, sentence case e cor semântica."""
from paleta import sentence_case, canonico


def test_sentence_case_desfaz_upper_preservando_acentos():
    assert sentence_case("CONCLUÍDO") == "Concluído"
    assert sentence_case("NÃO CONCLUÍDO - MOTIVOS DIVERSOS") == "Não concluído - motivos diversos"


def test_sentence_case_preserva_siglas():
    assert sentence_case("ADI") == "ADI"
    assert sentence_case("ADPF") == "ADPF"
    assert sentence_case("TOTAL ADI E ADPF") == "Total ADI e ADPF"
    assert sentence_case("PR") == "PR"


def test_sentence_case_ja_correto_nao_muda():
    assert sentence_case("Não concluído - motivos diversos") == "Não concluído - motivos diversos"
    assert sentence_case("1 - Maioria (relator vencedor)") == "1 - Maioria (relator vencedor)"


def test_canonico_traduz_plenario_fisico():
    assert canonico("Plenário Físico") == "Plenário Presencial"
    assert canonico("PLENÁRIO FÍSICO") == "Plenário Presencial"
    assert canonico("Plenário Presencial") == "Plenário Presencial"


def test_canonico_preserva_nome_proprio_de_ambiente():
    assert canonico("PLENÁRIO VIRTUAL") == "Plenário Virtual"
    assert canonico("plenário virtual") == "Plenário Virtual"


def test_canonico_normaliza_apelidos_de_tramitacao():
    assert canonico("Só Virtual") == "Só Virtual"
    assert canonico("Virtual") == "Só Virtual"
    assert canonico("Só Físico") == "Só Presencial"
    assert canonico("Físico") == "Só Presencial"
    assert canonico("Presencial") == "Só Presencial"
    assert canonico("Ambos os ambientes") == "Ambos os ambientes"


def test_canonico_desconhecido_cai_em_sentence_case():
    assert canonico("ALGUMA COISA NOVA") == "Alguma coisa nova"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
