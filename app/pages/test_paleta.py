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


def test_rampa_ordinal_das_faixas_de_sessao_mantem_ordem_sob_daltonismo():
    """Rampa das faixas de sessão revalidada sem o script da skill (que sumiu).

    Luminância monotônica crescente (ordinal), contraste mínimo com o fundo e
    distância perceptível entre degraus adjacentes nas três simulações de
    daltonismo (matrizes LMS de Machado-Oliveira-Fernandes) — no patamar dos
    pares aprovados (PP/vermelho 0.175, azul/índigo 0.264).
    """
    import math

    def _lum(hexc: str) -> float:
        h = hexc.lstrip("#")
        def f(c):
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    def _sim(rgbv, tipo):
        m = {
            "deuteranopia": [[0.367322, 0.860646, -0.227968],
                             [0.280085, 0.672501, 0.047413],
                             [-0.011820, 0.042940, 0.968881]],
            "protanopia":   [[0.152286, 1.052583, -0.204868],
                             [0.114503, 0.786281, 0.099216],
                             [-0.003882, -0.048116, 1.051998]],
            "tritanopia":   [[1.255528, -0.076749, -0.178779],
                             [-0.078411, 0.930809, 0.147602],
                             [0.004733, 0.691367, 0.303900]],
        }[tipo]
        return [sum(m[i][j] * rgbv[j] for j in range(3)) for i in range(3)]

    def _dist(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    for modo, degraus in (
        ("claro", [cor("1 sessão"), cor("2–3 sessões"), cor("4–5 sessões"), cor("6+ sessões")]),
        ("escuro", [cor(n, dark=True) for n in ("1 sessão", "2–3 sessões", "4–5 sessões", "6+ sessões")]),
    ):
        lums = [_lum(d) for d in degraus]
        assert lums == sorted(lums) and len(set(lums)) == len(lums), f"{modo}: luminância não monotônica {lums}"
        fundo = "#ffffff" if modo == "claro" else "#0e1117"
        for d in degraus:
            la, lb = sorted([_lum(d), _lum(fundo)], reverse=True)
            assert (la + 0.05) / (lb + 0.05) >= 2.0, f"{modo}: contraste baixo {d}"
        for tipo in ("deuteranopia", "protanopia", "tritanopia"):
            sims = [_sim([int(d.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)], tipo) for d in degraus]
            min_dist = min(_dist(a, b) for a, b in zip(sims, sims[1:]))
            assert min_dist >= 0.15, f"{modo}/{tipo}: adjacentes próximos demais {min_dist:.3f}"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
