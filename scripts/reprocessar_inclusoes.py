"""Reprocessa inclusoes_em_pauta e compara com o parquet publicado.

Existe porque a correção do extrator de sufixo (src/inclusao_pauta.py) só chega
ao dashboard depois que o parquet é regerado e republicado. Enquanto isso não
acontece, o app exibe o dado como está no Hugging Face: 185 eventos com
`tipo_questao` = "Não identificado" que deveriam ser RC, PR ou IJ.

Não sobe nada sozinho. Regera, compara, relata e para — o upload é decisão
separada, via scripts/upload_hf.py.

Uso:
    PYTHONPATH=. .venv/bin/python scripts/reprocessar_inclusoes.py
    PYTHONPATH=. .venv/bin/python scripts/reprocessar_inclusoes.py --escrever

Sem --escrever, nada é gravado em disco: só o relatório.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PUBLICADO = RAIZ / "data" / "processed" / "inclusoes_em_pauta.parquet"
# O pipeline escreve num diretório à parte para a comparação acontecer antes
# de qualquer sobrescrita do dado publicado.
SAIDA = RAIZ / "data" / "interim" / "reprocessamento"

CHAVE = ["incidente", "data_inclusao", "andamento_origem"]


def _comparar(publicado: pd.DataFrame, novo: pd.DataFrame) -> dict:
    """Diferenças entre o parquet publicado e o regerado, por coluna."""
    p = publicado.set_index(CHAVE).sort_index()
    n = novo.set_index(CHAVE).sort_index()

    relatorio = {
        "linhas_publicado": len(p),
        "linhas_novo": len(n),
        "so_no_publicado": len(p.index.difference(n.index)),
        "so_no_novo": len(n.index.difference(p.index)),
        "colunas_divergentes": {},
    }

    comuns = p.index.intersection(n.index)
    for coluna in sorted(set(p.columns) & set(n.columns)):
        a, b = p.loc[comuns, coluna], n.loc[comuns, coluna]
        difere = (a != b) & ~(a.isna() & b.isna())
        if difere.any():
            transicoes = (
                pd.DataFrame({"antes": a[difere], "depois": b[difere]})
                .groupby(["antes", "depois"]).size().sort_values(ascending=False)
            )
            relatorio["colunas_divergentes"][coluna] = {
                "n": int(difere.sum()),
                "transicoes": transicoes.head(10).to_dict(),
            }
    return relatorio


def _portao(relatorio: dict) -> list[str]:
    """Falhas que impedem a publicação.

    A única mudança esperada é em `tipo_questao`, e sempre partindo de
    "Não identificado". Qualquer outra coisa — linha que sumiu, coluna nova
    divergente, reclassificação de valor que já existia — é motivo para parar e
    entender antes de subir.
    """
    falhas = []
    if relatorio["so_no_publicado"]:
        falhas.append(f'{relatorio["so_no_publicado"]} linhas sumiram no reprocessamento')
    if relatorio["so_no_novo"]:
        falhas.append(f'{relatorio["so_no_novo"]} linhas novas apareceram')

    for coluna, info in relatorio["colunas_divergentes"].items():
        if coluna != "tipo_questao":
            falhas.append(f'coluna "{coluna}" mudou em {info["n"]} linhas — só tipo_questao era esperado')
            continue
        de_outra_coisa = {k: v for k, v in info["transicoes"].items() if k[0] != "Não identificado"}
        if de_outra_coisa:
            falhas.append(
                f"tipo_questao ALTEROU classificações que já existiam, não só preencheu "
                f"lacuna: {de_outra_coisa}"
            )
    return falhas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--escrever", action="store_true",
                    help="grava o parquet regerado por cima do local (não sobe ao HF)")
    args = ap.parse_args()

    if not PUBLICADO.exists():
        print(f"parquet publicado não encontrado em {PUBLICADO}", file=sys.stderr)
        return 2

    from src.inclusao_pauta import run_pipeline  # import tardio: pesado

    print("regerando a partir dos andamentos...")
    run_pipeline(
        processed_dir=RAIZ / "data" / "processed",
        interim_dir=RAIZ / "data" / "interim",
        out_dir=SAIDA,
    )
    regerado = SAIDA / "inclusoes_em_pauta.parquet"
    if not regerado.exists():
        print(f"pipeline não gerou {regerado}", file=sys.stderr)
        return 2

    novo = pd.read_parquet(regerado)
    publicado = pd.read_parquet(PUBLICADO)

    relatorio = _comparar(publicado, novo)
    print(f'\npublicado: {relatorio["linhas_publicado"]:,} linhas')
    print(f'regerado : {relatorio["linhas_novo"]:,} linhas')
    if not relatorio["colunas_divergentes"]:
        print("\nnenhuma diferença — o parquet publicado já está correto.")
        return 0

    print("\ndiferenças por coluna:")
    for coluna, info in relatorio["colunas_divergentes"].items():
        print(f'  {coluna}: {info["n"]} linhas')
        for (antes, depois), n in info["transicoes"].items():
            print(f"      {antes!r} -> {depois!r}: {n}")

    falhas = _portao(relatorio)
    if falhas:
        print("\nPORTÃO REPROVOU — não publicar:", file=sys.stderr)
        for f in falhas:
            print(f"  {f}", file=sys.stderr)
        return 1

    print("\nportão aprovou: só tipo_questao mudou, e sempre a partir de 'Não identificado'.")
    if args.escrever:
        novo.to_parquet(PUBLICADO, index=False)
        print(f"gravado em {PUBLICADO}")
        print("para publicar: PYTHONPATH=. .venv/bin/python scripts/upload_hf.py")
    else:
        print("nada gravado. use --escrever para atualizar o parquet local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
