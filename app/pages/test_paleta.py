"""Testes de paleta.py — rótulos canônicos, sentence case e cor semântica."""
from visual.paleta import sentence_case, canonico


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


from visual.paleta import cor, cores, CINZA_OUTROS


def test_ambiente_tem_cor_fixa_nos_dois_modos():
    assert cor("Plenário Virtual") == "#2a78d6"
    assert cor("Plenário Virtual", dark=True) == "#3987e5"
    assert cor("Plenário Presencial") == "#eb6834"
    assert cor("Plenário Presencial", dark=True) == "#d95926"


def test_plenario_fisico_recebe_a_cor_de_presencial():
    assert cor("Plenário Físico") == cor("Plenário Presencial")


def test_cor_ignora_caixa():
    assert cor("PLENÁRIO VIRTUAL") == cor("Plenário Virtual")


def test_familia_de_desfecho_separa_concluido_de_nao_concluido():
    concluidos = [
        cor("Concluído - decisão unânime"),
        cor("Concluído - decisão maioria com o relator"),
        cor("Concluído - decisão maioria, vencido o relator"),
    ]
    nao = [
        cor("Não concluído - motivos diversos"),
        cor("Não concluído - retirado de pauta"),
        cor("Não concluído - pedido de vista"),
        cor("Não concluído - destaque"),
    ]
    assert len(set(concluidos)) == 3
    assert len(set(nao)) == 4
    assert not (set(concluidos) & set(nao))
    # o par que a Pessoa 2 reclamou tem que estar em famílias diferentes
    assert cor("Concluído - decisão maioria, vencido o relator") == "#86b6ef"
    assert cor("Não concluído - retirado de pauta") == "#c9541d"


def test_classes_tem_as_quatro_cores_validadas():
    assert cores(["ADI", "ADPF", "ADC", "ADO"]) == {
        "ADI": "#2a78d6", "ADPF": "#eb6834", "ADC": "#1baf7a", "ADO": "#eda100",
    }


def test_desconhecido_cai_em_cinza_deterministico():
    a = cor("categoria inexistente")
    b = cor("categoria inexistente")
    assert a == b
    assert a != cor("outra categoria inexistente")


def test_ausencia_usa_cinza_reservado():
    assert cor("Sem sustentação oral") == CINZA_OUTROS
    assert cor("Sem reajuste de voto") == CINZA_OUTROS


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
