from pathlib import Path

import pandas as pd

TERMOS_BAIXA_REGEX = (
    r"baixa\s+ao\s+arquivo"
    r"|baixa\s+definitiva\s+dos\s+autos"
    r"|baixa\s+dos\s+autos"
    r"|processo\s+findo"
)

CLASSES_ACERVO = ("ADI", "ADC", "ADO", "ADPF", "CC")
ANOS_ACERVO = range(1988, 2026)


def primeira_baixa_por_processo(dim_andamentos: pd.DataFrame) -> pd.Series:
    and_data = pd.to_datetime(dim_andamentos["and_data"], format="%d/%m/%Y", errors="coerce")
    mask_baixa = (
        dim_andamentos["and_nome"]
        .str.lower()
        .str.strip()
        .str.contains(TERMOS_BAIXA_REGEX, regex=True, na=False)
    )
    return (
        and_data[mask_baixa]
        .groupby(dim_andamentos.loc[mask_baixa, "incidente"])
        .min()
        .rename("data_baixa")
    )


def construir_acervo_historico(fato: pd.DataFrame, primeira_baixa: pd.Series) -> pd.DataFrame:
    acervo = fato[["incidente", "classe", "data_protocolo"]].merge(
        primeira_baixa, left_on="incidente", right_index=True, how="left"
    )
    acervo["data_protocolo"] = pd.to_datetime(acervo["data_protocolo"], errors="coerce")
    acervo["data_baixa"] = pd.to_datetime(acervo["data_baixa"])
    return acervo


def snapshot_ativos_por_ano(
    acervo_historico: pd.DataFrame, anos=ANOS_ACERVO, classes=CLASSES_ACERVO
) -> pd.DataFrame:
    registros = []
    for ano in anos:
        limite = pd.Timestamp(f"{ano}-12-31")
        existentes = acervo_historico[acervo_historico["data_protocolo"] <= limite]
        ativos_mask = existentes["data_baixa"].isna() | (existentes["data_baixa"] > limite)

        total = existentes["classe"].value_counts()
        ativos = existentes[ativos_mask]["classe"].value_counts()
        inativos = existentes[~ativos_mask]["classe"].value_counts()

        for classe in classes:
            registros.append(
                {
                    "ano": ano,
                    "classe": classe,
                    "total_geral": total.get(classe, 0),
                    "quantidade_ativos": ativos.get(classe, 0),
                    "quantidade_inativos": inativos.get(classe, 0),
                }
            )
    return pd.DataFrame(registros)


def contagem_baixas_por_ano(
    acervo_historico: pd.DataFrame, anos=ANOS_ACERVO, classes=CLASSES_ACERVO
) -> pd.DataFrame:
    registros = []
    for ano in anos:
        inicio, limite = pd.Timestamp(f"{ano}-01-01"), pd.Timestamp(f"{ano}-12-31")
        baixados = acervo_historico[
            acervo_historico["data_baixa"].between(inicio, limite)
        ]
        contagem = baixados["classe"].value_counts()
        for classe in classes:
            registros.append(
                {"ano": ano, "classe": classe, "quantidade_baixas": contagem.get(classe, 0)}
            )
    return pd.DataFrame(registros)


def contagem_distribuicoes_por_ano(
    acervo_historico: pd.DataFrame, anos=ANOS_ACERVO, classes=CLASSES_ACERVO
) -> pd.DataFrame:
    registros = []
    for ano in anos:
        inicio, limite = pd.Timestamp(f"{ano}-01-01"), pd.Timestamp(f"{ano}-12-31")
        distribuidos = acervo_historico[
            acervo_historico["data_protocolo"].between(inicio, limite)
        ]
        contagem = distribuidos["classe"].value_counts()
        for classe in classes:
            registros.append(
                {"ano": ano, "classe": classe, "quantidade_distribuidos": contagem.get(classe, 0)}
            )
    return pd.DataFrame(registros)


def evolucao_acervo_por_ano(
    acervo_historico: pd.DataFrame, anos=ANOS_ACERVO, classes=CLASSES_ACERVO
) -> pd.DataFrame:
    evolucao = (
        snapshot_ativos_por_ano(acervo_historico, anos, classes)
        .merge(contagem_baixas_por_ano(acervo_historico, anos, classes), on=["ano", "classe"])
        .merge(contagem_distribuicoes_por_ano(acervo_historico, anos, classes), on=["ano", "classe"])
    )
    assert (
        (evolucao["quantidade_ativos"] + evolucao["quantidade_inativos"]) == evolucao["total_geral"]
    ).all(), "Soma de ativos e inativos deve ser igual ao total geral."
    return evolucao


def run_pipeline(processed_dir: Path, interim_dir: Path, out_dir: Path) -> pd.DataFrame:
    fato = pd.read_parquet(Path(processed_dir) / "arquivosConcatenados.parquet", engine="pyarrow")
    dim_andamentos = pd.read_parquet(Path(interim_dir) / "dim_andamentos.parquet", engine="pyarrow")

    primeira_baixa = primeira_baixa_por_processo(dim_andamentos)
    acervo_historico = construir_acervo_historico(fato, primeira_baixa)
    evolucao = evolucao_acervo_por_ano(acervo_historico)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    evolucao.to_parquet(out_dir / "evolucao_acervo.parquet", engine="pyarrow", index=False)
    return evolucao


def _selfcheck() -> None:
    fato = pd.DataFrame(
        {
            "incidente": [1, 2, 3],
            "classe": ["ADI", "ADI", "ADC"],
            "data_protocolo": ["2000-01-01", "2005-06-01", "2010-01-01"],
        }
    )
    dim_andamentos = pd.DataFrame(
        {
            "incidente": [1, 1, 2],
            "and_nome": ["Baixa definitiva dos autos", "Remessa dos autos", "Decisão"],
            "and_data": ["15/03/2010", "01/03/2010", "10/06/2005"],
        }
    )

    primeira_baixa = primeira_baixa_por_processo(dim_andamentos)
    assert primeira_baixa.loc[1] == pd.Timestamp("2010-03-15")
    assert 2 not in primeira_baixa.index

    acervo_historico = construir_acervo_historico(fato, primeira_baixa)
    evolucao = evolucao_acervo_por_ano(acervo_historico, anos=range(2008, 2011), classes=("ADI", "ADC"))

    linha_2009 = evolucao[(evolucao["ano"] == 2009) & (evolucao["classe"] == "ADI")].iloc[0]
    assert linha_2009["total_geral"] == 2
    assert linha_2009["quantidade_ativos"] == 2
    assert linha_2009["quantidade_inativos"] == 0

    linha_2010 = evolucao[(evolucao["ano"] == 2010) & (evolucao["classe"] == "ADI")].iloc[0]
    assert linha_2010["quantidade_ativos"] == 1
    assert linha_2010["quantidade_inativos"] == 1
    assert linha_2010["quantidade_baixas"] == 1

    linha_2010_adc = evolucao[(evolucao["ano"] == 2010) & (evolucao["classe"] == "ADC")].iloc[0]
    assert linha_2010_adc["quantidade_distribuidos"] == 1

    print("acervo self-check ok")


if __name__ == "__main__":
    _selfcheck()
