import argparse
import ast
import os
from pathlib import Path

import pandas as pd

VAL_NULOS = ["NA", "nan", "None", "", " ", "[]"]
STR_NULOS = ["NA", "nan", ""]

CATEGORIA_COLS = ["classe", "classe_extenso", "tipo_processo", "origem", "relator", "status_processo"]
COLUNAS_JSON_PESADAS = ["partes_total", "andamentos_lista", "decisões", "deslocamentos_lista"]
COLUNAS_CONTEXTO = ["incidente", "classe", "tipo_processo"]


def load_raw(path):
    return pd.read_csv(path, dayfirst=True, low_memory=True)


def limpar_nulos(valor):
    try:
        if pd.isna(valor):
            return None
    except ValueError:
        return valor
    if str(valor).strip() in VAL_NULOS:
        return None
    return valor


def categorizar_esfera(orgao):
    if pd.isna(orgao) or str(orgao).strip() == "" or str(orgao).upper() in ["NAN", "NÃO IDENTIFICADO"]:
        return "Não Identificado"

    orgao_str = str(orgao).upper().strip()

    if "FEDERAL" in orgao_str or "TRF" in orgao_str:
        return "Justiça Federal"
    elif (
        "JUSTICA DO ESTADO" in orgao_str
        or "TRIBUNAL DE JUSTIÇA" in orgao_str
        or "TJ" in orgao_str
        or "COMARCA" in orgao_str
        or "JUIZ DE DIREITO" in orgao_str
    ):
        return "Justiça Estadual"
    elif "ELEITORAL" in orgao_str or "TRE" in orgao_str or "TSE" in orgao_str:
        return "Justiça Eleitoral"
    elif "TRABALHO" in orgao_str or "TRT" in orgao_str:
        return "Justiça do Trabalho"
    elif (
        "SUPREMO TRIBUNAL" in orgao_str
        or "STF" in orgao_str
        or "SUPERIOR TRIBUNAL" in orgao_str
        or "STJ" in orgao_str
    ):
        return "Tribunais Superiores"
    elif "PROCURADORIA" in orgao_str or "MINISTÉRIO PÚBLICO" in orgao_str:
        return "Ministério Público"
    elif "CONSELHO NACIONAL" in orgao_str or "CNJ" in orgao_str or "CNMP" in orgao_str:
        return "Conselhos de Justiça"
    else:
        return "Outros / Administração"


def converter_para_lista_real(texto):
    if pd.isna(texto) or str(texto).strip() in ["[]", "", "nan"]:
        return ["Não Informado"]
    try:
        return ast.literal_eval(str(texto))
    except (ValueError, SyntaxError):
        return [str(texto).strip()]


def clean(df):
    proc = df.copy()
    proc = proc.map(limpar_nulos)

    proc["numero_processo"] = pd.to_numeric(
        proc["nome_processo"].str.split(" ", n=1).str[1], errors="coerce"
    )

    proc["liminar"] = proc["liminar"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
    )

    proc["esfera_origem"] = proc["origem_orgao"].apply(categorizar_esfera)

    proc["lista_assuntos"] = proc["lista_assuntos"].apply(converter_para_lista_real)

    proc["data_protocolo"] = pd.to_datetime(proc["data_protocolo"], dayfirst=True, errors="coerce")
    proc["incidente"] = proc["incidente"].astype(int)

    for col in CATEGORIA_COLS:
        proc[col] = proc[col].astype("category")

    return proc


def build_fact_table(proc):
    return proc.drop(columns=COLUNAS_JSON_PESADAS)


def explodir_json_veloz(df, coluna, prefixo, colunas_contexto=None):
    if colunas_contexto is None:
        colunas_contexto = COLUNAS_CONTEXTO

    df_mini = df[colunas_contexto + [coluna]].copy()

    def tentar_eval(x):
        if pd.isna(x) or str(x).strip() in ["[]", "", "nan"]:
            return []
        try:
            res = ast.literal_eval(str(x))
            return res if isinstance(res, list) else []
        except Exception:
            return []

    df_mini[coluna] = df_mini[coluna].apply(tentar_eval)

    df_exploded = df_mini.explode(coluna)
    df_exploded = df_exploded.dropna(subset=[coluna])

    if df_exploded.empty:
        return pd.DataFrame(columns=colunas_contexto)

    df_normalizado = pd.json_normalize(df_exploded[coluna]).set_index(df_exploded.index)
    df_normalizado = df_normalizado.add_prefix(prefixo)

    df_final = pd.concat([df_exploded[colunas_contexto], df_normalizado], axis=1)
    df_final = df_final.replace(STR_NULOS, None)

    return df_final.reset_index(drop=True)


def explode_partes(proc):
    return explodir_json_veloz(proc, "partes_total", "par_")


def explode_andamentos(proc):
    return explodir_json_veloz(proc, "andamentos_lista", "and_")


def explode_decisoes(proc):
    return explodir_json_veloz(proc, "decisões", "dec_")


def explode_deslocamentos(proc):
    return explodir_json_veloz(proc, "deslocamentos_lista", "des_")


def run_pipeline(raw_csv_path, out_processed_dir, out_interim_dir):
    out_processed_dir = Path(out_processed_dir)
    out_interim_dir = Path(out_interim_dir)
    os.makedirs(out_processed_dir, exist_ok=True)
    os.makedirs(out_interim_dir, exist_ok=True)

    df = load_raw(raw_csv_path)
    proc = clean(df)

    fact = build_fact_table(proc)
    partes = explode_partes(proc)
    andamentos = explode_andamentos(proc)
    decisoes = explode_decisoes(proc)
    deslocamentos = explode_deslocamentos(proc)

    fact.to_parquet(out_processed_dir / "arquivosConcatenados.parquet", index=False)
    decisoes.to_parquet(out_processed_dir / "dim_decisoes.parquet", index=False)
    partes.to_parquet(out_interim_dir / "dim_partes.parquet", index=False)
    andamentos.to_parquet(out_interim_dir / "dim_andamentos.parquet", index=False)
    deslocamentos.to_parquet(out_interim_dir / "dim_deslocamentos.parquet", index=False)

    return fact, partes, andamentos, decisoes, deslocamentos


def _cli():
    parser = argparse.ArgumentParser(description="Roda o pipeline de limpeza do Plenário Virtual")
    parser.add_argument("raw_csv_path")
    parser.add_argument("out_processed_dir")
    parser.add_argument("out_interim_dir")
    args = parser.parse_args()
    run_pipeline(args.raw_csv_path, args.out_processed_dir, args.out_interim_dir)


def _selfcheck():
    raw = pd.DataFrame(
        {
            "incidente": [1, 2],
            "classe": ["ADI", "ADPF"],
            "nome_processo": ["ADI 1234", "ADPF 854"],
            "classe_extenso": ["AÇÃO DIRETA DE INCONSTITUCIONALIDADE", "ARGUIÇÃO DE DESCUMPRIMENTO DE PRECEITO FUNDAMENTAL"],
            "tipo_processo": ["Eletrônico", "Físico"],
            "liminar": ["['MEDIDA LIMINAR']", "[]"],
            "origem": ["DF", "SP"],
            "relator": ["MIN. FULANO", "MIN. SICRANO"],
            "autor1": ["PROCURADOR-GERAL DA REPÚBLICA", "PARTIDO X"],
            "len(partes_total)": [1, 2],
            "partes_total": [
                "[{'_index': 1, 'tipo': 'REQTE.(S)', 'nome': 'FULANO'}]",
                "[{'_index': 1, 'tipo': 'REQTE.(S)', 'nome': 'BELTRANO'}, {'_index': 2, 'tipo': 'ADV.', 'nome': 'CICRANO OAB/DF 1'}]",
            ],
            "data_protocolo": ["01/02/2000", "15/03/2020"],
            "origem_orgao": ["TRIBUNAL REGIONAL FEDERAL DA 1ª REGIÃO", "NA"],
            "lista_assuntos": ["['DIREITO CONSTITUCIONAL']", "[]"],
            "resumo": ["resumo do processo 1", "resumo do processo 2"],
            "len(andamentos_lista)": [1, 1],
            "andamentos_lista": [
                "[{'index': 1, 'data': '01/02/2000', 'nome': 'Petição', 'complemento': 'NA', 'julgador': 'NA'}]",
                "[{'index': 1, 'data': '15/03/2020', 'nome': 'Conclusos', 'complemento': 'NA', 'julgador': 'NA'}]",
            ],
            "len(decisões)": [1, 0],
            "decisões": [
                "[{'index': 1, 'data': '02/02/2000', 'nome': 'Despacho', 'julgador': 'MIN. FULANO'}]",
                "[]",
            ],
            "len(deslocamentos)": [1, 0],
            "deslocamentos_lista": [
                "[{'index': 1, 'data_recebido': '03/02/2000', 'enviado por': 'GAB1', 'recebido por': 'GAB2', 'guia': '123'}]",
                "[]",
            ],
            "status_processo": ["Finalizado", "Em andamento"],
        }
    )

    proc = clean(raw)
    assert proc["numero_processo"].tolist() == [1234, 854]
    assert proc.loc[0, "liminar"] == ["MEDIDA LIMINAR"]
    assert proc["esfera_origem"].tolist() == ["Justiça Federal", "Não Identificado"]
    assert str(proc["classe"].dtype) == "category"

    fact = build_fact_table(proc)
    assert not set(COLUNAS_JSON_PESADAS) & set(fact.columns)
    assert len(fact) == 2

    partes = explode_partes(proc)
    assert len(partes) == 3
    assert {"incidente", "classe", "tipo_processo", "par__index", "par_tipo", "par_nome"} <= set(partes.columns)

    andamentos = explode_andamentos(proc)
    assert len(andamentos) == 2
    assert "and_nome" in andamentos.columns

    decisoes = explode_decisoes(proc)
    assert len(decisoes) == 1
    assert decisoes.loc[0, "dec_nome"] == "Despacho"

    deslocamentos = explode_deslocamentos(proc)
    assert len(deslocamentos) == 1
    assert deslocamentos.loc[0, "des_guia"] == "123"

    print("cleaning.py selfcheck: OK")


if __name__ == "__main__":
    _selfcheck()
