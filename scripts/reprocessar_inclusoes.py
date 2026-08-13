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


def _montar_entrada() -> Path:
    """Diretório com os três insumos do pipeline, resolvidos onde de fato estão.

    `run_pipeline` lê dim_andamentos, dim_decisoes e arquivosConcatenados todos
    de `processed_dir`, mas dim_andamentos mora em `data/interim/` neste repo.
    Em vez de mudar a assinatura do pipeline ou mover um parquet de 560 MB,
    monta um diretório de links simbólicos.
    """
    entrada = RAIZ / "data" / "interim" / "entrada_pipeline"
    entrada.mkdir(parents=True, exist_ok=True)

    candidatos = [RAIZ / "data" / "processed", RAIZ / "data" / "interim"]
    faltando = []
    for nome in ("dim_andamentos.parquet", "dim_decisoes.parquet",
                 "arquivosConcatenados.parquet"):
        origem = next((c / nome for c in candidatos if (c / nome).exists()), None)
        if origem is None:
            faltando.append(nome)
            continue
        alvo = entrada / nome
        if alvo.is_symlink() or alvo.exists():
            alvo.unlink()
        alvo.symlink_to(origem)

    if faltando:
        raise SystemExit(
            "insumos ausentes: " + ", ".join(faltando) +
            f"\nprocurados em: {', '.join(str(c) for c in candidatos)}"
        )
    return entrada


def _comparar(publicado: pd.DataFrame, novo: pd.DataFrame, recorte: int | None) -> dict:
    """Diferenças entre o parquet publicado e o regerado, por coluna.

    `recorte` é o menor ano do publicado. O pipeline cresceu a janela
    (2009–2015 entrou), então a regra é a do `_conferir_sessoes`: restringir o
    regerado aos anos do publicado tem que reproduzi-lo exatamente. Linhas do
    regerado anteriores ao recorte não contam como diferença.
    """
    if recorte is not None:
        ano = pd.to_numeric(novo["data_inclusao"].str[-4:], errors="coerce")
        novo = novo[ano >= recorte]

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


# Colunas que o conserto do extrator de sufixo legitimamente altera. São as três
# da mesma cadeia: o sufixo extraído, a classificação crua e a derivada.
_COLUNAS_ESPERADAS = {"sufixo_extraido", "tipo_questao_original", "tipo_questao"}

# A regra "só preenche lacuna, nunca altera resposta existente" tem que ser
# julgada na coluna CRUA. Em `tipo_questao` a lacuna já vem mascarada como "PR"
# (o pipeline mapeia "Não identificado" para PR na exibição), então uma
# transição PR->RC ali pode ser tanto um preenchimento legítimo quanto uma
# reclassificação indevida — só `tipo_questao_original` distingue as duas.
_COLUNA_CRUA = "tipo_questao_original"
_LACUNA = "Não identificado"


def _portao(relatorio: dict) -> list[str]:
    """Falhas que impedem a publicação."""
    falhas = []
    if relatorio["so_no_publicado"]:
        falhas.append(f'{relatorio["so_no_publicado"]} linhas sumiram no reprocessamento')
    if relatorio["so_no_novo"]:
        falhas.append(f'{relatorio["so_no_novo"]} linhas novas apareceram')

    for coluna, info in relatorio["colunas_divergentes"].items():
        if coluna not in _COLUNAS_ESPERADAS:
            falhas.append(
                f'coluna "{coluna}" mudou em {info["n"]} linhas — o conserto do '
                f'extrator só deveria afetar {sorted(_COLUNAS_ESPERADAS)}'
            )

    crua = relatorio["colunas_divergentes"].get(_COLUNA_CRUA)
    if crua:
        de_outra_coisa = {k: v for k, v in crua["transicoes"].items() if k[0] != _LACUNA}
        if de_outra_coisa:
            falhas.append(
                f"{_COLUNA_CRUA} ALTEROU classificações que já existiam, não só "
                f"preencheu lacuna: {de_outra_coisa}"
            )
    return falhas


def _conferir_sessoes() -> list[str]:
    """`run_pipeline` também escreve sessoes_virtuais.parquet.

    O publicado cobre 2020–2025; o pipeline atual produz desde 2016. Ganhar os
    anos anteriores é aceitável — o que não pode é o recorte já publicado
    mudar. Então a regra não é "mesmo número de linhas", é: **restringir o
    regerado aos anos do publicado tem que reproduzi-lo exatamente**. Assim o
    portão libera o acréscimo e continua barrando alteração retroativa.
    """
    pub_path = RAIZ / "data" / "processed" / "sessoes_virtuais.parquet"
    nov_path = SAIDA / "sessoes_virtuais.parquet"
    if not (pub_path.exists() and nov_path.exists()):
        return []

    pub, nov = pd.read_parquet(pub_path), pd.read_parquet(nov_path)
    ano_min = int(pd.to_numeric(pub["ano"], errors="coerce").min())
    recorte = nov[pd.to_numeric(nov["ano"], errors="coerce") >= ano_min]

    falhas = []
    if len(recorte) != len(pub):
        falhas.append(
            f"restrito a {ano_min}+, o regerado tem {len(recorte):,} linhas contra "
            f"{len(pub):,} do publicado — o recorte já publicado mudou"
        )
    novos = len(nov) - len(recorte)
    if novos:
        print(f"\nsessoes_virtuais: +{novos:,} linhas anteriores a {ano_min} "
              f"(o recorte {ano_min}+ é reproduzido exatamente)")
    return falhas


def _regerar_derivados() -> None:
    """tramitacoes e sustentacao_oral são derivados de inclusoes_em_pauta.

    `src/reajustes.py` os constrói a partir do parquet de inclusões, então
    atualizar só as inclusões deixaria os dois com o `tipo_questao` antigo — a
    página Inclusões mostraria RC e as páginas Tramitação e Sustentação
    mostrariam PR para as mesmas linhas.
    """
    from src.reajustes import run_pipeline as run_reajustes

    print("\nregerando os derivados (tramitacoes, sustentacao_oral)...")
    run_reajustes(
        processed_dir=RAIZ / "data" / "processed",
        interim_dir=RAIZ / "data" / "interim",
    )
    for nome in ("tramitacoes.parquet", "sustentacao_oral.parquet"):
        caminho = RAIZ / "data" / "processed" / nome
        print(f"  {nome}: {len(pd.read_parquet(caminho)):,} linhas")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--escrever", action="store_true",
                    help="grava o parquet regerado por cima do local (não sobe ao HF)")
    args = ap.parse_args()

    if not PUBLICADO.exists():
        print(f"parquet publicado não encontrado em {PUBLICADO}", file=sys.stderr)
        return 2

    from src.inclusao_pauta import run_pipeline  # import tardio: pesado

    entrada = _montar_entrada()
    print("regerando a partir dos andamentos...")
    run_pipeline(
        processed_dir=entrada,
        interim_dir=RAIZ / "data" / "interim",
        out_dir=SAIDA,
    )
    regerado = SAIDA / "inclusoes_em_pauta.parquet"
    if not regerado.exists():
        print(f"pipeline não gerou {regerado}", file=sys.stderr)
        return 2

    novo = pd.read_parquet(regerado)
    publicado = pd.read_parquet(PUBLICADO)

    recorte = int(pd.to_numeric(publicado["data_inclusao"].str[-4:], errors="coerce").min())
    relatorio = _comparar(publicado, novo, recorte)
    print(f'\npublicado: {relatorio["linhas_publicado"]:,} linhas')
    print(f'regerado : {relatorio["linhas_novo"]:,} linhas (recorte {recorte}+)')
    antes_do_recorte = len(novo) - relatorio["linhas_novo"]
    if antes_do_recorte:
        print(f'  +{antes_do_recorte:,} linhas anteriores a {recorte} (janela ampliada)')
    if not relatorio["colunas_divergentes"] and not antes_do_recorte:
        print("\nnenhuma diferença — o parquet publicado já está correto.")
        return 0

    if not relatorio["colunas_divergentes"]:
        print("\nrecorte publicado reproduzido exatamente; só há o acréscimo da "
              f"janela ampliada (+{antes_do_recorte} linhas pré-{recorte}).")
    else:
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

    print("\nportão aprovou: mudaram só as colunas da cadeia do sufixo, e a "
          "classificação crua só saiu de 'Não identificado'.")

    # O pipeline escreve DOIS parquets. Comparar só o de inclusões deixaria
    # passar mudança em sessoes_virtuais — e há uma: o publicado começa em
    # 2020 e o pipeline atual produz desde 2016.
    falhas_sessoes = _conferir_sessoes()
    if falhas_sessoes:
        print("\nATENÇÃO — sessoes_virtuais.parquet também diverge:", file=sys.stderr)
        for f in falhas_sessoes:
            print(f"  {f}", file=sys.stderr)
        print("\n  Isso não vem do conserto do extrator. Decidir antes de publicar.",
              file=sys.stderr)
        return 1

    if args.escrever:
        novo.to_parquet(PUBLICADO, index=False)
        print(f"\ngravado: {PUBLICADO.name}")
        sess = SAIDA / "sessoes_virtuais.parquet"
        if sess.exists():
            pd.read_parquet(sess).to_parquet(
                RAIZ / "data" / "processed" / "sessoes_virtuais.parquet", index=False)
            print("gravado: sessoes_virtuais.parquet")
        _regerar_derivados()
        print("\npara publicar: PYTHONPATH=. .venv/bin/python scripts/upload_hf.py")
    else:
        print("nada gravado. use --escrever para atualizar os parquets locais.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
