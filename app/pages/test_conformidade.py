"""Portão de estilo: toda figura das oito páginas obedece o padrão da Pessoa 2.

Constrói cada gráfico de cada catálogo contra os parquets reais, em todas as
formas de plotagem que a entrada declara, e afirma fonte, tamanhos, ângulo de
tick, rótulo de ambiente, cor de série e ausência de pizza.

Os Blocos Empíricos são deliberadamente excluídos: pertencem a outra leitora e
mantêm o visual original. Se algum dia aparecerem aqui, o portão está errado,
não os blocos.
"""

from __future__ import annotations

import re

import plotly.graph_objects as go

import visual.paleta as paleta
from components.grafico import _kwargs_aceitos
from visual.tema import FONTE, TAMANHOS, aplicar_tema, converter_tipo

TAMANHOS_PERMITIDOS = set(TAMANHOS.values())

# Fase 2 encerrou o pedido "zero gráficos de pizza". Conjunto vazio: nenhuma
# pizza é aceita em lugar nenhum das oito páginas.
PIZZAS_CONHECIDAS: set[tuple[str, str]] = set()

# Cor fora da paleta validada, pedida explicitamente pela Pessoa 2 pra um
# gráfico específico (não pro dashboard todo) — I1 (#b8136f/#5c5c5c, exceção
# de ambiente só nesse gráfico) e I12/I24/I25/I26 (#a2eb98/#d64e45, macro
# "Prevalência da relatoria/divergência"). Vetorial já fica de fora da
# checagem por natureza; isto cobre o caso em que ela também aparece como
# escalar — a linha de um gráfico "linha", que não tem como ser vetorial.
CORES_EXCECAO_LOCAL = {"#b8136f", "#5c5c5c", "#a2eb98", "#d64e45"}


def _cores_da_paleta() -> set[str]:
    """Todo hex que a paleta autoriza, nos dois modos, mais o cinza reservado."""
    permitidas = {paleta.CINZA_OUTROS.lower()}
    for claro, escuro in paleta.CORES.values():
        permitidas.add(claro.lower())
        permitidas.add(escuro.lower())
    for claro, escuro in paleta._RESERVA:
        permitidas.add(claro.lower())
        permitidas.add(escuro.lower())
    return permitidas


CORES_PERMITIDAS = _cores_da_paleta()


def _catalogos():
    """(página, catálogo, dataframe). Import tardio: layout.py importa streamlit.

    'geral' fica de fora por não ter catálogo — sua única figura é a linha do
    tempo normativa, coberta por pages/geral/test_layout.py.
    """
    from dados.loader import (
        load_evolucao_acervo,
        load_inclusoes_em_pauta,
        load_sessoes_virtuais,
        load_sustentacao_oral,
        load_tramitacoes,
    )
    from pages.acervo.layout import _CATALOGO as acervo
    from pages.inclusoes.layout import _CATALOGO as inclusoes
    from pages.narrativa.layout import _CATALOGO as narrativa
    from pages.reajuste.layout import _CATALOGO as reajuste
    from pages.sessoes_virtuais.layout import _montar_catalogo
    from pages.sustentacao.layout import _CATALOGO as sustentacao
    from pages.tramitacao.layout import _montar_catalogo as _montar_tram

    inc = load_inclusoes_em_pauta()
    tram = load_tramitacoes()
    sessoes = load_sessoes_virtuais()

    return [
        # Tramitação fecha as figuras do Bloco 2 sobre o df de inclusões.
        ("tramitacao", _montar_tram(inc), tram),
        ("inclusoes", inclusoes, inc),
        ("reajuste", reajuste, tram),
        ("sustentacao", sustentacao, load_sustentacao_oral()),
        # Sessões Virtuais monta o catálogo por função: o Bloco 5 precisa do
        # dataframe de inclusões capturado por closure. O `IJ → QI` reproduz o
        # que sessoes_virtuais.py faz antes de chamar o layout — sem isso o
        # portão testa um dataframe que a página nunca entrega, e a aba "QI"
        # sai vazia por artefato do teste, não por defeito do gráfico.
        ("sessoes_virtuais", _montar_catalogo(inc),
         sessoes.assign(tipo_questao=sessoes["tipo_questao"].replace({"IJ": "QI"}))),
        ("acervo", acervo, load_evolucao_acervo()),
        ("narrativa", narrativa, inc[inc["ano"].between(2020, 2025)]),
    ]


def _figuras(resultado) -> list[go.Figure]:
    if isinstance(resultado, dict):
        bruto = list(resultado.values())
    elif isinstance(resultado, (list, tuple)):
        bruto = list(resultado)
    else:
        bruto = [resultado]
    return [f for f in bruto if isinstance(f, go.Figure)]


def _todas_as_figuras():
    """Gera (página, id, tipo, figura já convertida e tematizada)."""
    for pagina, catalogo, df in _catalogos():
        for spec in catalogo:
            if spec.fn is None:
                continue
            kwargs = _kwargs_aceitos(
                spec.fn, dict(spec.kwargs_fixos, show_values=True, proporcao=False)
            )
            for tipo in spec.tipos:
                for fig in _figuras(spec.fn(df, **kwargs)):
                    yield pagina, spec.id, tipo, aplicar_tema(converter_tipo(fig, tipo))


def _eixos(fig: go.Figure):
    for chave in fig.layout:
        if chave.startswith("xaxis") or chave.startswith("yaxis"):
            yield chave, fig.layout[chave]


def _textos_renderizados(fig: go.Figure) -> list[str]:
    textos = [fig.layout.title.text or ""]
    textos += [tr.name or "" for tr in fig.data]
    textos += [a.text or "" for a in fig.layout.annotations]
    for _, eixo in _eixos(fig):
        textos.append(eixo.title.text or "")
        for v in (eixo.ticktext or ()):
            textos.append(str(v))
    for tr in fig.data:
        for eixo_dados in (getattr(tr, "x", None), getattr(tr, "y", None)):
            if eixo_dados is None:
                continue
            textos += [str(v) for v in eixo_dados if isinstance(v, str)]
    return textos


# ── Asserções ─────────────────────────────────────────────────────────────────


def test_nenhuma_pizza_nova():
    encontradas = {
        (pagina, gid)
        for pagina, gid, _tipo, fig in _todas_as_figuras()
        if "pie" in {tr.type for tr in fig.data}
    }
    novas = encontradas - PIZZAS_CONHECIDAS
    assert not novas, f"pizza nova: {sorted(novas)}"


def test_fonte_times_em_toda_figura():
    for pagina, gid, tipo, fig in _todas_as_figuras():
        onde = f"{pagina}/{gid} [{tipo}]"
        assert fig.layout.font.family == FONTE, onde
        assert fig.layout.title.font.family == FONTE, onde
        for chave, eixo in _eixos(fig):
            assert eixo.tickfont.family == FONTE, f"{onde} {chave}.tickfont"
            assert eixo.title.font.family == FONTE, f"{onde} {chave}.title"


def test_tick_do_eixo_x_sempre_horizontal():
    for pagina, gid, tipo, fig in _todas_as_figuras():
        for chave, eixo in _eixos(fig):
            if chave.startswith("xaxis"):
                assert eixo.tickangle == 0, f"{pagina}/{gid} [{tipo}] {chave} gira o rótulo"


def test_tamanhos_dentro_da_escala():
    for pagina, gid, tipo, fig in _todas_as_figuras():
        onde = f"{pagina}/{gid} [{tipo}]"
        medidos = [("title", fig.layout.title.font.size)]
        for chave, eixo in _eixos(fig):
            medidos.append((f"{chave}.tick", eixo.tickfont.size))
            medidos.append((f"{chave}.title", eixo.title.font.size))
        for ann in fig.layout.annotations:
            medidos.append(("annotation", ann.font.size))
        for i, tr in enumerate(fig.data):
            if getattr(tr, "textfont", None) is not None:
                medidos.append((f"trace[{i}].textfont", tr.textfont.size))
        for nome, tam in medidos:
            assert tam is None or tam in TAMANHOS_PERMITIDOS, f"{onde} {nome}={tam}"


def test_nenhum_texto_diz_plenario_fisico():
    for pagina, gid, tipo, fig in _todas_as_figuras():
        for t in _textos_renderizados(fig):
            assert "Plenário Físico" not in t, f'{pagina}/{gid} [{tipo}]: "{t}"'


def test_texto_do_catalogo_tambem_nao_diz_plenario_fisico():
    """O rótulo, o subtítulo e a descrição são texto renderizado também.

    Aparecem no seletor, no sumário e acima do gráfico. O portão só varria a
    figura, então três entradas com "Plenário Físico" no catálogo passaram sem
    ser vistas.
    """
    achados = []
    for pagina, catalogo, _df in _catalogos():
        for spec in catalogo:
            for campo in ("rotulo", "subtitulo", "descricao"):
                texto = getattr(spec, campo, "") or ""
                if "Plenário Físico" in texto:
                    achados.append(f"{pagina}/{spec.id} .{campo}: {texto[:70]}")
    assert not achados, "texto de catálogo com 'Plenário Físico':\n  " + "\n  ".join(achados)


def test_nenhum_grafico_renderiza_vazio():
    """Gráfico sem nenhum ponto é defeito silencioso, não resultado.

    O I31 filtrava por um valor de ambiente que o loader já havia renomeado, e
    saía com zero traces sem que nada reclamasse — o portão só olhava estilo.
    Entradas legitimamente vazias, se surgirem, entram na lista de exceção com
    o motivo escrito.
    """
    vazios = []
    for pagina, gid, tipo, fig in _todas_as_figuras():
        pontos = 0
        for tr in fig.data:
            for campo in ("x", "y"):
                v = getattr(tr, campo, None)
                if v is not None:
                    pontos = max(pontos, len(v))
        if pontos == 0:
            vazios.append(f"{pagina}/{gid} [{tipo}]")
    assert not vazios, "gráfico sem nenhum ponto:\n  " + "\n  ".join(vazios)


def test_numero_no_padrao_brasileiro_sem_abreviacao_si():
    """Eixo mostra 8.000, nunca '8k'; e ano continua 2025, nunca '2.025'.

    Sem tickformat o Plotly abrevia em SI a partir de mil. Com agrupamento
    aplicado sem cuidado, o eixo de ano viraria '2.025' — daí o guard.
    """
    from visual.tema import _parece_ano, _valores_numericos

    faltando, anos_quebrados = [], []
    for pagina, gid, tipo, fig in _todas_as_figuras():
        onde = f"{pagina}/{gid} [{tipo}]"
        assert fig.layout.separators == ",.", f"{onde} sem separators brasileiros"
        for chave in _eixos_de(fig):
            eixo = fig.layout[chave]
            valores = _valores_numericos(fig, "y" if chave.startswith("yaxis") else "x")
            if not valores:
                continue
            if _parece_ano(valores):
                if eixo.tickformat != "d":
                    anos_quebrados.append(f"{onde} {chave}={eixo.tickformat!r}")
            elif max(abs(v) for v in valores) >= 1000 and eixo.tickformat != ",":
                faltando.append(f"{onde} {chave} (max {int(max(valores)):,}) = {eixo.tickformat!r}")
    assert not faltando, "eixo grande sem separador de milhar:\n  " + "\n  ".join(faltando)
    assert not anos_quebrados, "eixo de ano com formato errado:\n  " + "\n  ".join(anos_quebrados)


_ROTULO_SEM_SEPARADOR = re.compile(r"^-?\d{4,}$")
_PERCENTUAL_COM_PONTO = re.compile(r"^-?[\d.]+\.\d+\s*%$")


def test_rotulo_de_valor_no_padrao_brasileiro():
    """Milhar com ponto e decimal com vírgula em TODO rótulo de valor.

    As páginas montavam esse rótulo de três jeitos — já formatado, `str(int(v))`
    cru e float para o Plotly formatar — então uns gráficos mostravam 2.168 e
    outros 4230, uns 63,9% e outros 63.9%.
    """
    sem_milhar, pct_com_ponto = [], []
    for pagina, gid, tipo, fig in _todas_as_figuras():
        for tr in fig.data:
            texto = getattr(tr, "text", None)
            if texto is None:
                continue
            for v in ([texto] if isinstance(texto, str) else list(texto)):
                s = str(v).strip()
                if _ROTULO_SEM_SEPARADOR.match(s):
                    sem_milhar.append(f"{pagina}/{gid} [{tipo}]: {s}")
                elif _PERCENTUAL_COM_PONTO.match(s):
                    pct_com_ponto.append(f"{pagina}/{gid} [{tipo}]: {s}")
    assert not sem_milhar, "rótulo de 4+ dígitos sem ponto de milhar:\n  " + "\n  ".join(sem_milhar[:15])
    assert not pct_com_ponto, "percentual com ponto decimal:\n  " + "\n  ".join(pct_com_ponto[:15])


def test_portadas_do_bloco_empirico_nao_declaram_periodo():
    """Figuras portadas dos Blocos Empíricos têm o período fixo por dentro.

    Toda entrada marcada `portada=True` veio de um Bloco Empírico: filtra o ano
    internamente, então qualquer `periodo` no filtro devolveria gráfico vazio
    ou KeyError em silêncio.
    """
    com_periodo = []
    for pagina, catalogo, _df in _catalogos():
        for spec in catalogo:
            if not spec.portada:
                continue
            if "periodo" in spec.filtros:
                com_periodo.append(f"{pagina}/{spec.id}: {spec.filtros}")
    assert not com_periodo, "entrada portada com filtro de período:\n  " + "\n  ".join(com_periodo)


def test_tabulador_tambem_recebe_o_tema():
    """O tabulador é gráfico como qualquer outro e obedece o mesmo padrão.

    Existiam seis cópias do tabulador, uma por página, e nenhuma chamava
    aplicar_tema — era o único gráfico do dashboard fora do padrão visual, e
    nenhum teste pegava porque o portão só varria os catálogos.
    """
    from components.tabulador import figura_tabulador
    from dados.filters import dimensoes_disponiveis
    from dados.loader import load_inclusoes_em_pauta, load_sessoes_virtuais

    casos = [
        ("inclusoes", load_inclusoes_em_pauta()),
        ("sessoes_virtuais", load_sessoes_virtuais()),
    ]
    for nome, df in casos:
        dims = list(dimensoes_disponiveis(df.columns).values())
        assert len(dims) >= 2, f"{nome} sem dimensões para o tabulador"
        for barmode in ("group", "stack", "100%"):
            fig = figura_tabulador(df, dims[0], dims[1], "inclusoes", barmode, True)
            onde = f"tabulador/{nome} [{barmode}]"
            assert fig.layout.font.family == FONTE, onde
            assert fig.layout.separators == ",.", onde
            for chave in _eixos_de(fig):
                if chave.startswith("xaxis"):
                    assert fig.layout[chave].tickangle == 0, f"{onde} {chave}"
                assert fig.layout[chave].tickfont.family == FONTE, f"{onde} {chave}"
            for tr in fig.data:
                assert "Plenário Físico" not in (tr.name or ""), onde


def _eixos_de(fig: go.Figure):
    return [c for c in fig.layout if c.startswith("xaxis") or c.startswith("yaxis")]


def test_cor_de_serie_vem_da_paleta():
    """Cor sólida de série tem que ser um degrau autorizado.

    Pega o caso de dois azuis diferentes no mesmo dashboard: o hex antigo de
    estilo.py sobrevivendo num gráfico enquanto o resto usa a paleta validada.
    Cor vetorial (uma por barra) é codificação própria e fica de fora.
    """
    fora_da_paleta = []
    for pagina, gid, tipo, fig in _todas_as_figuras():
        for tr in fig.data:
            for origem in ("marker", "line"):
                obj = getattr(tr, origem, None)
                cor = getattr(obj, "color", None) if obj is not None else None
                if not isinstance(cor, str) or not cor.startswith("#"):
                    continue
                if cor.lower() not in CORES_PERMITIDAS and cor.lower() not in CORES_EXCECAO_LOCAL:
                    fora_da_paleta.append((pagina, gid, tipo, tr.name, origem, cor))
    assert not fora_da_paleta, "cores fora da paleta:\n" + "\n".join(
        f"  {p}/{g} [{t}] {n!r} {o}={c}" for p, g, t, n, o, c in fora_da_paleta
    )


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
