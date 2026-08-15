"""Smoke test do modelo visual de plotar_grafico_stf (padrão 1.b2), pós-tema.

Aplica aplicar_tema antes de afirmar porque é o estado que o usuário efetivamente
vê: render_grafico (components/grafico.py) sempre chama aplicar_tema antes de
st.plotly_chart. Afirmar o estado pré-tema testaria uma figura que ninguém vê
na casca de catálogo.
"""
import pandas as pd

from visual.base import AZUL
from visual.paleta import cor
from pages.acervo.plots import plotar_grafico_stf
from visual.tema import aplicar_tema


def _df_fake() -> pd.DataFrame:
    anos = list(range(2016, 2026))
    rows = []
    for ano in anos:
        for classe, base in [("ADI", 100), ("ADPF", 40), ("ADC", 10), ("ADO", 5)]:
            rows.append({"ano": ano, "classe": classe, "quantidade_ativos": base + ano - 2016})
    return pd.DataFrame(rows)


def test_total_usa_azul_e_tem_er_espin():
    df = _df_fake()
    fig = plotar_grafico_stf(df, "TOTAL", "quantidade_ativos", "Processos Ativos", show_values=True)
    fig = aplicar_tema(fig, tema="novo", dark=False)
    assert fig.layout.height == 650
    assert fig.layout.margin.t == 150 and fig.layout.margin.b == 70
    # Agregado recebe o azul da paleta validada, não o AZUL de estilo.py.
    # Antes o nome "Total geral (...)" não casava com nenhuma chave e a cor
    # antiga sobrevivia ao tema, deixando dois azuis diferentes no dashboard.
    assert fig.data[0].marker.color == cor("Total")
    assert fig.data[0].marker.color != AZUL
    # eixo categórico por ano (igual 1.b2), não numérico contínuo
    assert list(fig.data[0].x) == [str(a) for a in range(2016, 2026)]
    # linhas ER (51/52/53) + vrect ESPIN + anotações "ER" e "ESPIN"
    shape_colors = {s.line.color for s in fig.layout.shapes if s.type == "line"}
    assert "#000000" in shape_colors  # ER
    assert "#C00000" in shape_colors  # ESPIN
    ann_texts = " ".join(a.text for a in fig.layout.annotations)
    assert "ER" in ann_texts and "ESPIN" in ann_texts
    assert fig.layout.legend.y == 0.95
    # escala padronizada pós-tema: tick 16, título de eixo 18, título 22
    assert fig.layout.xaxis.tickfont.size == 16
    assert fig.layout.yaxis.tickfont.size == 16
    assert fig.layout.xaxis.title.font.size == 18
    assert fig.layout.yaxis.title.font.size == 18
    assert fig.layout.title.font.size == 22
    assert fig.layout.xaxis.tickangle == 0
    assert fig.layout.font.family == "Times New Roman, Times, serif"


def test_classe_usa_cor_do_bloco1_e_titulo_dinamico():
    df = _df_fake()
    fig = plotar_grafico_stf(df, "ADPF", "quantidade_ativos", "Processos Ativos", show_values=False)
    fig = aplicar_tema(fig, tema="novo", dark=False)
    # "ADPF" está no vocabulário de paleta.CORES: a tema recolore pela paleta nova.
    assert fig.data[0].marker.color == cor("ADPF")
    # título deve conter o nome da classe (história calculada a partir dos dados reais, não fixa)
    assert "ADPF" in fig.layout.title.text
    assert fig.layout.xaxis.tickangle == 0



def test_recorte_de_periodo_nao_estica_o_eixo():
    """Marcador fora do recorte esticava o eixo e espremia as barras.

    O marcador da ER 51 usava ano-base fixo (1988) e posição fracionária da
    data. Com o filtro em 2021-2025 (5 categorias, índices 0-4) a linha caía
    em x=28,5, o Plotly estendia o eixo até lá e as barras ocupavam um sexto da
    largura. Agora os marcadores ficam nas fronteiras entre anos (recorte
    relativo), e só existem se a fronteira está no recorte plotado.
    """
    df = _df_fake()
    for lo, hi in [(2016, 2025), (2021, 2025), (2016, 2016), (2018, 2020)]:
        sub = df[df["ano"].between(lo, hi)]
        if sub.empty:
            continue
        fig = plotar_grafico_stf(sub, "TOTAL", "quantidade_ativos", "Processos Ativos")
        n = sub["ano"].nunique()
        limite = n - 0.5
        xs = [float(s.x0) for s in fig.layout.shapes if isinstance(s.x0, (int, float))]
        xs += [float(s.x1) for s in fig.layout.shapes if isinstance(s.x1, (int, float))]
        if xs:
            assert max(xs) <= limite + 0.01, (
                f"recorte {lo}-{hi}: shape em x={max(xs):.2f} com {n} categorias "
                f"(limite {limite})")


if __name__ == "__main__":
    # descoberta automática: chamar por nome deixava teste novo fora da execução
    for _nome, _fn in sorted(globals().items()):
        if _nome.startswith("test_"):
            _fn()
    print("ok")
