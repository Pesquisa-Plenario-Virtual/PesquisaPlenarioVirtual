"""Camada de dados: reclassificação de desfecho excluindo um ministro divergente.

Hipótese que este módulo serve: o salto nas decisões unânimes (PV e PP) coincide
com a saída do Min. Marco Aurélio (2022), voto vencido frequente. Para testar,
recontamos como *unânimes* as decisões "por maioria" em que ele foi o **único**
voto vencido, e deixamos como "por maioria" as que tinham outros vencidos.

Lógica pura — não importa Streamlit. O texto da decisão
(`dim_decisoes.dec_complemento`) não está no dataset de inclusões; `casar_decisao`
liga um ao outro por janela temporal, o mesmo padrão de
`pages.inclusoes.plots._refinar_motivos_diversos`.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

MINISTRO_PADRAO = "Marco Aurélio"

_PREFIXO_MAIORIA = "Concluído - decisão maioria"

# "vencido(s) [, em parte,] o(s)/a(s) [Senhor(es)] Ministro(s) NOMES" até o fim
# da frase. Não paramos em "que ..." porque em lista com subordinada
# ("vencidos o Ministro X, que divergia, e o Ministro Y") isso cortaria Y.
_RE_VENCIDOS = re.compile(
    r"vencid[oa]s?\b"
    r"(?:\s*,?\s*(?:em\s+parte|parcialmente|integralmente))*"
    r"\s*,?\s*"
    r"(?:o|os|a|as)\s+"
    r"(?:senhor(?:es|as?)?\s+)?"
    r"ministr[oa]s?\s+"
    r"(.+?)"
    r"(?=\s*(?:\.|;|$| Plen[áa]rio| Ausente| Votou | Vota[- ]| Falou | Presidi))",
    re.IGNORECASE | re.DOTALL,
)

# Marco Aurélio marcado como relator/redator no próprio dispositivo.
_RE_RELATOR = re.compile(
    r"marco\s+aur[ée]lio\s*\(\s*(?:relator|redator)",
    re.IGNORECASE,
)

_PREFIXO_NOME = re.compile(
    r"^(?:e\s+)?(?:o|a|os|as)\s+(?:senhor(?:es|as?)?\s+)?ministr[oa]s?\s+",
    re.IGNORECASE,
)
# Corre de nome próprio: palavras iniciando maiúscula, ligadas por "de/da/do".
_RE_NOME = re.compile(
    r"^([A-ZÀ-Ý][\wÀ-ÿ'.\-]*(?:\s+(?:d[aeo]s?\s+)?[A-ZÀ-Ý][\wÀ-ÿ'.\-]*){0,3})"
)
_STOPWORDS = {"que", "e", "o", "a", "os", "as", "no", "nos", "na", "nas", "qual",
              "quais", "por", "com", "sem", "para", "quanto"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


def extrair_vencidos(texto: str) -> set[str]:
    """Nomes dos ministros dados como vencidos no texto de `dec_complemento`.

    Vazio quando o texto não nomeia ninguém ("vencido o relator", "por maioria"
    sem cláusula de vencido, texto ausente).
    """
    if not isinstance(texto, str) or not texto.strip():
        return set()

    nomes: set[str] = set()
    for m in _RE_VENCIDOS.finditer(texto):
        segmento = m.group(1)
        for pedaco in re.split(r",|\se\s", segmento):
            pedaco = re.sub(r"\([^)]*\)", "", pedaco).strip()
            pedaco = _PREFIXO_NOME.sub("", pedaco).strip()
            if not pedaco:
                continue
            primeira = pedaco.split()[0].lower().strip(".,")
            if primeira in _STOPWORDS:
                continue
            achado = _RE_NOME.match(pedaco)
            if achado:
                nomes.add(achado.group(1).strip())
    return nomes


def relator_no_texto(texto: str, ministro: str = MINISTRO_PADRAO) -> bool:
    """True se `ministro` aparece marcado como relator/redator do acórdão."""
    if not isinstance(texto, str):
        return False
    if _norm(ministro) == _norm(MINISTRO_PADRAO):
        return bool(_RE_RELATOR.search(texto))
    # forma genérica para outros ministros
    return bool(re.search(
        re.escape(ministro) + r"\s*\(\s*(?:relator|redator)", texto, re.IGNORECASE))


def reclassificar_desfecho(desfecho: str, vencidos: set[str], eh_relator: bool,
                           ministro: str = MINISTRO_PADRAO) -> str:
    """Novo desfecho ao excluir `ministro` do rol de vencidos.

    Só age em "Concluído - decisão maioria*". Se o ministro era o relator, ou não
    está entre os vencidos, nada muda. Se ao removê-lo não sobra ninguém vencido,
    a decisão passa a "Concluído - decisão unânime"; senão continua "por maioria".
    """
    if not isinstance(desfecho, str) or not desfecho.startswith(_PREFIXO_MAIORIA):
        return desfecho
    if eh_relator:
        return desfecho
    alvo = _norm(ministro)
    if not any(_norm(n) == alvo for n in vencidos):
        return desfecho
    restantes = [n for n in vencidos if _norm(n) != alvo]
    if not restantes:
        return "Concluído - decisão unânime"
    return desfecho


def _preparar_decisoes(dec_df: pd.DataFrame) -> pd.DataFrame:
    d = dec_df[dec_df["dec_complemento"].str.contains(
        r"maioria|vencid", case=False, na=False, regex=True)].copy()
    d["_dt"] = pd.to_datetime(d["dec_data"], dayfirst=True, errors="coerce")
    return d.dropna(subset=["_dt"])


def casar_decisao(incidente: int, inicio: pd.Timestamp, fim: pd.Timestamp,
                  dec_prep: pd.DataFrame) -> str | None:
    """Texto da decisão "por maioria" que corresponde a esta inclusão.

    Janela [inicio - 2d, fim). Desempate: a decisão que cita "vencid" mais
    próxima de `inicio`.

    # ponytail: casamento aproximado. Na base atual, 1.197/1.246 inclusões "por
    # maioria" têm decisão única na janela; 36 caem no desempate, 13 não casam
    # (ficam inalteradas). O pipeline (src/inclusao_pauta._classificar_desfechos)
    # casa isso com precisão de data de sessão — replicá-lo aqui seria reescrever
    # o pipeline no app.
    """
    d = dec_prep[(dec_prep["incidente"] == incidente)
                 & (dec_prep["_dt"] >= inicio - pd.Timedelta(days=2))
                 & (dec_prep["_dt"] < fim)]
    if d.empty:
        return None
    if len(d) == 1:
        return d.iloc[0]["dec_complemento"]
    com_vencido = d[d["dec_complemento"].str.contains("vencid", case=False, na=False)]
    escolha = com_vencido if not com_vencido.empty else d
    escolha = escolha.assign(_diff=(escolha["_dt"] - inicio).abs()).sort_values("_diff")
    return escolha.iloc[0]["dec_complemento"]


def anexar_desfecho_sem_ministro(df: pd.DataFrame, dec_df: pd.DataFrame,
                                 ministro: str = MINISTRO_PADRAO) -> pd.DataFrame:
    """Adiciona a coluna `desfecho_sem_ma`: `desfecho` reclassificado excluindo as
    divergências isoladas de `ministro`. `macro_desfecho` não muda (concluído
    segue concluído). Linhas que não são "maioria" ficam iguais a `desfecho`.
    """
    out = df.copy()
    out["desfecho_sem_ma"] = out["desfecho"]

    if dec_df is None or dec_df.empty or "dec_complemento" not in dec_df.columns:
        return out

    alvo = out["desfecho"].astype(str).str.startswith(_PREFIXO_MAIORIA)
    if not alvo.any():
        return out

    dec_prep = _preparar_decisoes(dec_df)

    ordenado = out.sort_values(["incidente", "data_inclusao_dt"])
    proxima = ordenado.groupby("incidente")["data_inclusao_dt"].shift(-1)
    fim_por_idx = proxima.reindex(out.index)

    novos = {}
    for idx in out.index[alvo]:
        linha = out.loc[idx]
        fim = fim_por_idx.loc[idx]
        if pd.isna(fim):
            fim = pd.Timestamp("2100-01-01")
        texto = casar_decisao(linha["incidente"], linha["data_inclusao_dt"], fim, dec_prep)
        if texto is None:
            continue
        novo = reclassificar_desfecho(
            linha["desfecho"], extrair_vencidos(texto),
            relator_no_texto(texto, ministro), ministro)
        if novo != linha["desfecho"]:
            novos[idx] = novo

    for idx, valor in novos.items():
        out.at[idx, "desfecho_sem_ma"] = valor
    return out


__all__ = [
    "MINISTRO_PADRAO",
    "extrair_vencidos",
    "relator_no_texto",
    "reclassificar_desfecho",
    "casar_decisao",
    "anexar_desfecho_sem_ministro",
]
