"""Auditoria de consistência dos gráficos do catálogo.

Roda cada gráfico com o estado-padrão da casca (mesmos recortes de
`components.grafico._controles`/`render_grafico`) sobre o dado real e verifica
invariantes entre gráficos: granularidade soma no agregado, partições somam no
todo, percentuais fecham em 100, e o período declarado no subtítulo bate com o
período efetivo dos anos plotados.

Uso: PYTHONPATH=app .venv/bin/python scripts/auditar_consistencia.py
Saída não-zero se alguma checagem falhar.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from components.grafico import _aplicar_filtros, _fn_aceita_ambiente, _kwargs_aceitos, tabela_da_figura
from dados.loader import (
    load_evolucao_acervo, load_dim_decisoes, load_inclusoes_em_pauta,
    load_sessoes_virtuais, load_sustentacao_oral, load_tramitacoes,
)
from pages.inclusoes.layout import _CATALOGO as CAT_INC
from pages.inclusoes.layout import _refinar_motivos_diversos
from pages.acervo.layout import _CATALOGO as CAT_AC
from pages.tramitacao.layout import _montar_catalogo as monta_tram
from pages.narrativa.layout import _CATALOGO as CAT_NA
from pages.reajuste.layout import _CATALOGO as CAT_RE
from pages.sustentacao.layout import _CATALOGO as CAT_SU
from pages.sessoes_virtuais.layout import _montar_catalogo as monta_sv
from pages.tramitacao.plots import _proc as _proc_tram

_TABULADORES = {"A15", "I40", "T17", "V14", "R6", "S6"}
_TOL = 0.15  # pontos percentuais para comparações em %
TOLER = 0.5  # contagens (arredondamento de 1 casa em alguns eixos)

_FALHAS: list[str] = []
_CHEQUES = 0


def _ok(nome: str, *_args) -> None:
    global _CHEQUES
    _CHEQUES += 1
    print(f"  ok  {nome}")


def _falha(nome: str, esperado, obtido) -> None:
    _FALHAS.append(f"{nome}\n      esperado: {esperado}\n      obtido:   {obtido}")
    print(f"FAIL  {nome}\n      esperado: {esperado}\n      obtido:   {obtido}")


def _dicts_iguais(d1: dict, d2: dict, tol: float = TOLER) -> bool:
    chaves = set(d1) | set(d2)
    for k in chaves:
        a, b = float(d1.get(k, 0)), float(d2.get(k, 0))
        if abs(a - b) > tol:
            return False
    return True


def _pct(d: dict) -> dict:
    tot = sum(d.values()) or 1.0
    return {k: v / tot * 100 for k, v in d.items()}


def _default_escolhas(spec, df: pd.DataFrame) -> dict:
    """Réplica do estado-padrão de `_controles` (sem Streamlit)."""
    escolhas: dict = {}
    if "periodo" in spec.filtros and "ano" in df.columns and not df["ano"].dropna().empty:
        lo, hi = int(df["ano"].min()), int(df["ano"].max())
        if lo < hi:
            padrao = spec.periodo_padrao or (lo, hi)
            escolhas["periodo"] = (max(lo, padrao[0]), min(hi, padrao[1]))
    for nome, col in (("classe", "classe"), ("tipo_questao", "tipo_questao"), ("desfecho", "desfecho")):
        if nome in spec.filtros and col in df.columns:
            escolhas[nome] = sorted(str(v) for v in df[col].dropna().unique())
    if "ambiente" in spec.filtros and "ambiente" in df.columns:
        opcoes = sorted(str(v) for v in df["ambiente"].dropna().unique())
        if _fn_aceita_ambiente(spec.fn):
            escolhas["ambiente"] = [sorted(opcoes, key=lambda v: v != "Plenário Virtual")[0]]
        else:
            escolhas["ambiente"] = opcoes
    return escolhas


def render(spec, df: pd.DataFrame, **over):
    """Renderiza `spec` no estado-padrão da casca, com overrides opcionais."""
    escolhas = _default_escolhas(spec, df)
    escolhas.update(over)
    escolhas_df = {k: v for k, v in escolhas.items() if k != "ambiente" or not spec.opcoes_filtro.get("ambiente")}
    recortado = _aplicar_filtros(df, escolhas_df)
    if recortado.empty:
        return None
    candidatos = dict(spec.kwargs_fixos, show_values=True, proporcao=bool(over.get("proporcao", False)))
    amb = escolhas.get("ambiente")
    if amb and len(amb) == 1:
        candidatos["ambiente"] = amb[0]
    return spec.fn(recortado, **_kwargs_aceitos(spec.fn, candidatos))


def figuras_de(fig):
    if fig is None:
        return []
    if isinstance(fig, dict):
        out = []
        for f in fig.values():
            out.extend(figuras_de(f))
        return out
    if isinstance(fig, (tuple, list)):
        out = []
        for f in fig:
            out.extend(figuras_de(f))
        return out
    return [fig]


def _sem_total(t: pd.DataFrame) -> pd.DataFrame:
    return t[~t[t.columns[0]].astype(str).eq("Total")]


def tab_por_figura(fig) -> list[dict]:
    """{rótulo: valor} para cada figura, somando séries quando há várias."""
    out = []
    for f in figuras_de(fig):
        t = tabela_da_figura(f)
        if t.empty:
            continue
        idx = t.columns[0]
        t = _sem_total(t).set_index(idx).drop(columns=["Total"], errors="ignore")
        out.append({str(k): float(v) for k, v in t.sum(axis=1).items()})
    return out


def tab_por_serie(fig) -> list[dict[str, dict]]:
    """{rótulo: {série: valor}} por figura — para comparar série a série."""
    out = []
    for f in figuras_de(fig):
        t = tabela_da_figura(f)
        if t.empty:
            continue
        idx = t.columns[0]
        t = _sem_total(t).set_index(idx).drop(columns=["Total"], errors="ignore")
        out.append({str(k): {c: float(v) for c, v in row.items()} for k, row in t.iterrows()})
    return out


def anos_plotados(fig) -> tuple[int, int] | None:
    anos = set()
    for f in figuras_de(fig):
        for tr in f.data:
            horizontal = getattr(tr, "orientation", None) == "h"
            arr = getattr(tr, "y", None) if horizontal else getattr(tr, "x", None)
            if arr is None:
                continue
            for v in arr:
                try:
                    iv = int(v)
                except (TypeError, ValueError):
                    continue
                if 1900 <= iv <= 2100:
                    anos.add(iv)
    return (min(anos), max(anos)) if anos else None


# ── Período do subtítulo × período efetivo ─────────────────────────────────────

def _token_periodo(subtitulo: str) -> str | None:
    m = re.search(r"\(\d{4}[–-]\d{4}\)", subtitulo)
    if m:
        return m.group(0).strip("()").replace("-", "–")
    m = re.search(r"^\d{4}[–-]\d{4}:", subtitulo)
    return m.group(0).rstrip(":").replace("-", "–") if m else None


def checa_periodo_subtitulo(pagina: str, cat, df) -> None:
    for spec in cat:
        if spec.id in _TABULADORES or spec.renderer is not None:
            continue
        token = _token_periodo(spec.subtitulo)
        if token is None:
            _falha(f"{pagina}/{spec.id}: subtítulo sem período", "token (AAAA–AAAA)", spec.subtitulo)
            continue
        esperado = f"{spec.periodo_padrao[0]}–{spec.periodo_padrao[1]}" if spec.periodo_padrao else None
        if esperado and token != esperado:
            _falha(f"{pagina}/{spec.id}: token não bate periodo_padrao", esperado, token)
            continue
        fig = render(spec, df)
        if fig is None:
            continue
        span = anos_plotados(fig)
        if span is None:
            continue
        a, b = (int(x) for x in token.split("–"))
        if a != span[0] or b != span[1]:
            _falha(f"{pagina}/{spec.id}: período plotado difere do subtítulo", token, f"{span[0]}–{span[1]}")
            continue
        _ok(f"{pagina}/{spec.id} período {token}")


# ── Inclusões ──────────────────────────────────────────────────────────────────

def checa_inclusoes(df, df_dec) -> None:
    inc = _refinar_motivos_diversos(df, df_dec)
    inc = inc.assign(tipo_questao=inc["tipo_questao"].replace({"IJ": "QI", "Não identificado": "PR"}))
    specs = {s.id: s for s in CAT_INC}

    # I3.detail == I19 (2020-25, PV) — a classe de bug original.
    f3 = render(specs["I3"], inc)  # (macro, detalhe)
    if f3 is not None:
        i3_macro, i3_det = figuras_de(f3)
        det_counts = tab_por_figura(i3_det)[0]
        macro_counts = tab_por_figura(i3_macro)[0]
        f19 = render(specs["I19"], inc)
        if f19 is not None:
            i19_pct = tab_por_figura(f19)[0]
            ok = _dicts_iguais(_pct(det_counts), i19_pct, _TOL)
            ( _ok if ok else _falha )("I19 % == I3.detail % (PV 2020-25)", _pct(det_counts), i19_pct)
            ped_vista = next((v for k, v in det_counts.items() if "pedido de vista" in k.lower()), None)
            if ped_vista is not None:
                _ok(f"pedido de vista I3/I19: {ped_vista / sum(det_counts.values()) * 100:.1f}%")

        # I3.macro == colapso do I3.detail.
        macro = {"Concluído": 0.0, "Não concluído": 0.0}
        for k, v in det_counts.items():
            macro["Concluído" if k.startswith("Concluído") else "Não concluído"] += v
        ok = _dicts_iguais(macro, macro_counts)
        (_ok if ok else _falha)("I3.macro == colapso I3.detail", macro, macro_counts)

        # I11 (4 cats) == colapso do I3.detail; rótulos: 3 desfechos + "Não concluído".
        f11 = render(specs["I11"], inc)
        if f11 is not None:
            i11 = tab_por_figura(f11)[0]
            ok = True
            for k, v in i11.items():
                if k == "Não concluído":
                    esper = sum(x for kk, x in det_counts.items() if kk.startswith("Não concluído"))
                else:
                    esper = det_counts.get(k)
                if abs(esper - v) > TOLER:
                    ok = False
            (_ok if ok else _falha)("I11 (4 cats) == colapso I3.detail", det_counts, i11)
        else:
            i11 = None

        # I12 / I42 (concluídos apenas): colapsos do I3.detail.
        f12 = render(specs["I12"], inc)
        f42 = render(specs["I42"], inc)
        if f12 is not None:
            i12 = tab_por_figura(f12)[0]
            rel = det_counts["Concluído - decisão unânime"] + det_counts["Concluído - decisão maioria com o relator"]
            div = det_counts["Concluído - decisão maioria, vencido o relator"]
            esper = {"Prevalência da relatoria": rel, "Prevalência da divergência": div}
            ok = _dicts_iguais(esper, i12)
            (_ok if ok else _falha)("I12 == colapso I3.detail (concluídos)", esper, i12)
        if f42 is not None:
            i42 = tab_por_figura(f42)[0]
            esper = {"Julgamento por unanimidade": det_counts["Concluído - decisão unânime"],
                     "Julgamento com divergência(s)": det_counts["Concluído - decisão maioria com o relator"] + det_counts["Concluído - decisão maioria, vencido o relator"]}
            ok = _dicts_iguais(esper, i42)
            (_ok if ok else _falha)("I42 unanimidade/divergência == colapso I3.detail", esper, i42)

        # I13 soma das categorias (2020-25) == I11; I14 == I12.
        f13 = render(specs["I13"], inc)
        f14 = render(specs["I14"], inc)
        if f13 is not None:
            i13 = tab_por_serie(f13)[0]
            esper = {"1 - Unânime": det_counts["Concluído - decisão unânime"],
                     "2 - Maioria (relator vencedor)": det_counts["Concluído - decisão maioria com o relator"],
                     "3 - Maioria (relator vencido)": det_counts["Concluído - decisão maioria, vencido o relator"],
                     "4 - Não concluído (bloco)": sum(x for k, x in det_counts.items() if k.startswith("Não concluído"))}
            soma = {k: sum(r.get(k, 0) for r in i13.values()) for k in esper}
            ok = _dicts_iguais(esper, soma)
            (_ok if ok else _falha)("I13 soma das categorias == I3.detail (4 cats)", esper, soma)
        if f14 is not None and i12 is not None:
            i14 = tab_por_serie(f14)[0]
            soma14 = {k: sum(r.get(k, 0) for r in i14.values()) for k in ["1 - Unânime", "2 - Maioria (relator vencedor)", "3 - Maioria (relator vencido)"]}
            ok = abs(soma14["1 - Unânime"] + soma14["2 - Maioria (relator vencedor)"] - i12["Prevalência da relatoria"]) <= TOLER and \
                 abs(soma14["3 - Maioria (relator vencido)"] - i12["Prevalência da divergência"]) <= TOLER
            (_ok if ok else _falha)("I14 soma das categorias == I12", i12, soma14)

        # I21 / I24 (linhas, período fixo do dado) == bruto por ano (PV).
        f21 = render(specs["I21"], inc)
        f24 = render(specs["I24"], inc)
        pv_all = inc[inc["ambiente"] == "Plenário Virtual"]
        if f21 is not None:
            i21 = tab_por_serie(f21)[0]
            esper = {}
            for a in i21:
                sub = pv_all[pv_all["ano"] == int(a)]
                esper[a] = {
                    "Julgamento por unanimidade": (sub["desfecho"] == "Concluído - decisão unânime").sum(),
                    "Julgamento com divergência(s)": sub["desfecho"].isin(["Concluído - decisão maioria com o relator", "Concluído - decisão maioria, vencido o relator"]).sum(),
                }
            ok = all(_dicts_iguais(r, esper[a], TOLER) for a, r in i21.items())
            (_ok if ok else _falha)("I21 == bruto por ano (unânime/divergência, PV)", esper, i21)
        if f24 is not None:
            i24 = tab_por_serie(f24)[0]
            esper = {}
            for a in i24:
                sub = pv_all[pv_all["ano"] == int(a)]
                esper[a] = {
                    "Prevalência da relatoria": sub["desfecho"].isin(["Concluído - decisão unânime", "Concluído - decisão maioria com o relator"]).sum(),
                    "Prevalência da divergência": (sub["desfecho"] == "Concluído - decisão maioria, vencido o relator").sum(),
                }
            ok = all(_dicts_iguais(r, esper[a], TOLER) for a, r in i24.items())
            (_ok if ok else _falha)("I24 == bruto por ano (relatoria/divergência, PV)", esper, i24)

        # I27 soma dos anos == I3 NC detalhado (4 desfechos).
        f27 = render(specs["I27"], inc)
        if f27 is not None:
            i27 = tab_por_serie(f27)[0]
            esper = {"1 - Pedido de vista": det_counts["Não concluído - pedido de vista"],
                     "2 - Destaque": det_counts["Não concluído - destaque"],
                     "3 - Retirado de pauta": det_counts["Não concluído - retirado de pauta"],
                     "4 - Motivos diversos": det_counts["Não concluído - motivos diversos"]}
            soma = {k: sum(r.get(k, 0) for r in i27.values()) for k in esper}
            ok = _dicts_iguais(esper, soma)
            (_ok if ok else _falha)("I27 soma dos anos == I3 NC detalhado", esper, soma)

        # I4 (macro por ano) == colapso do I13; I5/I6 == CONCLUÍDO; I7/I8/I9/I10 == granular.
        f4 = render(specs["I4"], inc)
        f5 = render(specs["I5"], inc)
        f6 = render(specs["I6"], inc)
        if f13 is not None and f4 is not None:
            i13s = tab_por_serie(f13)[0]
            i4 = tab_por_serie(f4)[0]
            ok = all(
                abs(r["CONCLUÍDO"] - (i13s[str(a)]["1 - Unânime"] + i13s[str(a)]["2 - Maioria (relator vencedor)"] + i13s[str(a)]["3 - Maioria (relator vencido)"])) <= TOLER and
                abs(r["NÃO CONCLUÍDO"] - i13s[str(a)]["4 - Não concluído (bloco)"]) <= TOLER
                for a, r in i4.items())
            (_ok if ok else _falha)("I4 == colapso do I13 (macro/ano)", "por ano", "por ano")
        if f5 is not None and f4 is not None:
            i5 = tab_por_figura(f5)[0]
            i4s = tab_por_serie(f4)[0]
            ok = _dicts_iguais({a: r["CONCLUÍDO"] for a, r in i4s.items()}, i5)
            (_ok if ok else _falha)("I5 (concluídos/ano) == I4.CONCLUÍDO/ano",
                                    {a: r["CONCLUÍDO"] for a, r in i4s.items()}, i5)
        if f6 is not None and f13 is not None:
            i6 = tab_por_serie(f6)[0]
            i13s = tab_por_serie(f13)[0]
            esper6 = {"Concluído - decisão unânime": "1 - Unânime",
                      "Concluído - decisão maioria com o relator": "2 - Maioria (relator vencedor)",
                      "Concluído - decisão maioria, vencido o relator": "3 - Maioria (relator vencido)"}
            ok = all(abs(r[rotulo] - i13s[str(a)][cat]) <= TOLER
                     for a, r in i6.items() for rotulo, cat in esper6.items())
            (_ok if ok else _falha)("I6 == I13 (concluídos por ano)", "por ano", "por ano")
        for sid, serie_nome in (("I7", "NÃO CONCLUÍDO"), ("I8", "CONCLUÍDO"),
                                ("I9", "NÃO CONCLUÍDO"), ("I10", "CONCLUÍDO")):
            fx = render(specs[sid], inc)
            if fx is not None and f4 is not None:
                ix = tab_por_figura(fx)[0]  # {ano: soma de classes/tipos}
                i4s = tab_por_serie(f4)[0]
                esper = {a: r[serie_nome] for a, r in i4s.items()}
                ok = _dicts_iguais(esper, ix)
                (_ok if ok else _falha)(f"{sid} (soma classes/tipos) == I4.{serie_nome}/ano", esper, ix)

        # I1 (inclusões por ambiente, 2020-25) == bruto.
        f1 = render(specs["I1"], inc)
        if f1 is not None:
            i1 = tab_por_serie(f1)[0]
            soma = {k: sum(r.get(k, 0) for r in i1.values()) for k in ["PLENÁRIO VIRTUAL", "PLENÁRIO PRESENCIAL"]}
            inc2025 = inc[inc["ano"].between(2020, 2025)]
            esper = {"PLENÁRIO VIRTUAL": (inc2025["ambiente"] == "Plenário Virtual").sum(),
                     "PLENÁRIO PRESENCIAL": (inc2025["ambiente"] == "Plenário Presencial").sum()}
            ok = _dicts_iguais(soma, esper)
            (_ok if ok else _falha)("I1 soma por ambiente == bruto (2020-25)", esper, soma)

        # I30 (pauta PV, período total) == dado bruto.
        f30 = render(specs["I30"], inc)
        if f30 is not None:
            i30 = tab_por_figura(f30)[0]
            pv = (inc["ambiente"] == "Plenário Virtual").sum()
            chave = next(k for k in i30 if "Participação" in k)
            ok = abs(i30[chave] - pv / len(inc) * 100) < _TOL
            (_ok if ok else _falha)("I30 pauta PV == bruto", pv / len(inc) * 100, i30[chave])

    # Portadas count-based vs dado bruto.
    checks_portadas = {
        "I33": (2016, 2025, "share PV"),
        "I34": (2016, 2019, "PV por tipo"),
        "I35": (2020, 2025, "PV por tipo"),
        "I37": (2016, 2019, "tipo x ambiente %"),
        "I38": (2020, 2025, "concluídos %"),
    }
    for sid, (a0, a1, rot) in checks_portadas.items():
        f = render(specs[sid], inc)
        if f is None:
            continue
        if rot == "share PV":
            d = tab_por_figura(f)[0]
            sub = inc[(inc["ano"] >= a0) & (inc["ano"] <= a1)]
            share = {str(a): (sub[(sub["ano"] == a) & (sub["ambiente"] == "Plenário Virtual")].shape[0]
                              / sub[sub["ano"] == a].shape[0] * 100 if sub[sub["ano"] == a].shape[0] else 0)
                     for a in range(a0, a1 + 1)}
            ok = all(abs(d.get(str(a), 0) - share.get(str(a), 0)) < _TOL for a in range(a0, a1 + 1))
            (_ok if ok else _falha)(f"{sid} share PV vs bruto", share, d)
        elif rot == "PV por tipo":
            d = tab_por_figura(f)[0]
            sub = inc[(inc["ano"] >= a0) & (inc["ano"] <= a1) & (inc["ambiente"] == "Plenário Virtual")]
            esper = {str(a): sub[sub["ano"] == a].shape[0] for a in range(a0, a1 + 1)}
            ok = all(abs(d.get(str(a), 0) - esper.get(str(a), 0)) <= TOLER for a in range(a0, a1 + 1))
            (_ok if ok else _falha)(f"{sid} PV por tipo vs bruto (totais/ano)", esper, d)
        elif rot == "tipo x ambiente %":
            d = tab_por_serie(f)[0]  # {tipo: {PV: %, PP: %}}
            sub = inc[(inc["ano"] >= a0) & (inc["ano"] <= a1)]
            ok = True
            for tipo, r in d.items():
                for col, amb in (("PLENÁRIO VIRTUAL", "Plenário Virtual"), ("PLENÁRIO PRESENCIAL", "Plenário Presencial")):
                    tt = sub[sub["ambiente"] == amb]
                    esp = tt[tt["tipo_questao"] == tipo].shape[0] / len(tt) * 100 if len(tt) else 0
                    if abs(r.get(col, 0) - esp) > _TOL:
                        ok = False
            (_ok if ok else _falha)(f"{sid} % por ambiente/tipo vs bruto", "por ambiente", d)
        elif rot == "concluídos %":
            d = tab_por_serie(f)[0]
            sub = inc[(inc["ano"] >= a0) & (inc["ano"] <= a1) & (inc["macro_desfecho"] == "Concluído")]
            esp = {amb: sub[sub["ambiente"] == amb].shape[0] / len(sub) * 100 for amb in ("Plenário Virtual", "Plenário Presencial")}
            ok = True
            for r in d.values():
                for col, amb in (("PLENÁRIO VIRTUAL", "Plenário Virtual"), ("PLENÁRIO PRESENCIAL", "Plenário Presencial")):
                    if abs(r.get(col, 0) - esp[amb]) > _TOL:
                        ok = False
            (_ok if ok else _falha)(f"{sid} % concluídos por ambiente vs bruto", esp, d)


# ── Acervo ─────────────────────────────────────────────────────────────────────

def checa_acervo(df) -> None:
    specs = {s.id: s for s in CAT_AC}
    f1 = render(specs["A1"], df)
    f8 = render(specs["A8"], df)
    if f1 is not None and f8 is not None:
        a1 = tab_por_figura(f1)[0]  # {ano: ativo}
        a8 = tab_por_figura(f8)[0]  # {ano: soma classes}
        ok = _dicts_iguais(a1, a8)
        (_ok if ok else _falha)("A1 (ativo) == A8 (soma classes/ano)", a1, a8)
    f9 = render(specs["A9"], df)
    if f8 is not None and f9 is not None:
        ok = _dicts_iguais(tab_por_figura(f8)[0], tab_por_figura(f9)[0])
        (_ok if ok else _falha)("A9 == A8", tab_por_figura(f8)[0], tab_por_figura(f9)[0])
    f4 = render(specs["A4"], df)
    f5 = render(specs["A5"], df)
    f12 = render(specs["A12"], df)
    if f4 is not None and f12 is not None:
        a4 = tab_por_figura(f4)[0]
        a12 = tab_por_serie(f12)[0]  # {ano: {ENTRADAS, SAÍDAS}}
        baixas = {a: abs(r["SAÍDAS"]) for a, r in a12.items()}
        dist = {a: r["ENTRADAS"] for a, r in a12.items()}
        ok = _dicts_iguais(a4, baixas)
        (_ok if ok else _falha)("A4 (baixas) == A12.SAÍDAS", baixas, a4)
        if f5 is not None:
            ok = _dicts_iguais(tab_por_figura(f5)[0], dist)
            (_ok if ok else _falha)("A5 (distribuídos) == A12.ENTRADAS", dist, tab_por_figura(f5)[0])
        f13 = render(specs["A13"], df)
        f14 = render(specs["A14"], df)
        if f13 is not None:
            a13 = tab_por_serie(f13)[0]
            var = {a: r["Série 1"] for a, r in a13.items()}
            esp = {a: dist[a] - baixas[a] for a in dist}
            ok = _dicts_iguais(var, esp)
            (_ok if ok else _falha)("A13 (variação) == A12.ENTRADAS − SAÍDAS", esp, var)
        if f13 is not None and f14 is not None:
            a13s = tab_por_serie(f13)[0]
            a14s = tab_por_serie(f14)[0]
            ok = _dicts_iguais({a: r["Série 1"] for a, r in a13s.items()},
                               {a: r["Série 1"] for a, r in a14s.items()})
            (_ok if ok else _falha)("A14 == A13 (Série 1)", "igual", "diferente")


# ── Tramitação ─────────────────────────────────────────────────────────────────

def checa_tramitacao(df, df_inc) -> None:
    cat = monta_tram(df_inc)
    specs = {s.id: s for s in cat}
    f1 = render(specs["T1"], df)
    f12 = render(specs["T12"], df)
    if f1 is not None and f12 is not None:
        t12 = tab_por_figura(f12)[0]
        total = sum(t12.values())
        raw_total = len(_proc_tram(df))
        ok = abs(total - raw_total) <= TOLER
        (_ok if ok else _falha)("T12 total == processos distintos (período completo)", raw_total, total)
        _ok("T1 renderiza (2020-25)")
    f2 = render(specs["T2"], df)
    if f1 is not None and f2 is not None:
        t1 = tab_por_figura(f1)[0]
        t2s = tab_por_serie(f2)[0]  # {classe: {tramitacao: n}}
        soma = {}
        for r in t2s.values():
            for k, v in r.items():
                soma[k] = soma.get(k, 0) + v
        ok = _dicts_iguais(t1, soma)
        (_ok if ok else _falha)("T2 soma classes == T1", t1, soma)
    f5 = render(specs["T5"], df)
    f6 = render(specs["T6"], df)
    if f5 is not None and f6 is not None:
        t5 = tab_por_figura(f5)[0]  # {tramitacao: total}
        t6s = tab_por_serie(f6)[0]  # {tramitacao: {desfecho: n}} ou {desfecho: {tram: n}}
        ok = True
        for tram, r in t6s.items():
            concl = sum(v for k, v in r.items() if str(k).startswith("Concluído"))
            nc = sum(v for k, v in r.items() if not str(k).startswith("Concluído"))
            if abs(t5.get(tram, 0) - (concl + nc)) > TOLER:
                ok = False
        (_ok if ok else _falha)("T6 total por tramitacao == T5", t5, t6s)


# ── Sessões Virtuais ───────────────────────────────────────────────────────────

def checa_sessoes(df_s, df_inc) -> None:
    df_s = df_s.assign(tipo_questao=df_s["tipo_questao"].replace({"IJ": "QI"}))  # mesma prep da página
    cat = monta_sv(df_inc)
    specs = {s.id: s for s in cat}
    f6 = render(specs["V6"], df_s)
    f7 = render(specs["V7"], df_s)
    if f6 is not None and f7 is not None:
        ok = _dicts_iguais(tab_por_figura(f6)[0], tab_por_figura(f7)[0])
        (_ok if ok else _falha)("V6 == V7 (mesma fn)", tab_por_figura(f6)[0], tab_por_figura(f7)[0])
    f8 = render(specs["V8"], df_s)
    if f8 is not None:
        # V8: abas por tipo, cada uma macro por ano. Soma dos tipos == bruto macro/ano.
        tot = {}
        for serie in tab_por_serie(f8):
            for a, r in serie.items():
                tot.setdefault(a, {"Concluído": 0.0, "Não concluído": 0.0})
                for k, v in r.items():
                    tot[a][k] = tot[a].get(k, 0) + v
        sub = df_s[df_s["ano"].between(2020, 2025)]
        esper = {str(a): {"Concluído": (sub["ano"] == a).sum() - (sub[(sub["ano"] == a) & (sub["macro_desfecho"] != "Concluído")].shape[0]),
                          "Não concluído": (sub[(sub["ano"] == a) & (sub["macro_desfecho"] != "Concluído")].shape[0])}
                 for a in range(2020, 2026)}
        ok = all(abs(tot.get(str(a), {}).get("Concluído", 0) - esper[str(a)]["Concluído"]) <= TOLER and
                 abs(tot.get(str(a), {}).get("Não concluído", 0) - esper[str(a)]["Não concluído"]) <= TOLER
                 for a in range(2020, 2026))
        (_ok if ok else _falha)("V8 soma tipos == bruto macro/ano", esper, tot)


# ── Narrativa ──────────────────────────────────────────────────────────────────

def checa_narrativa(df) -> None:
    specs = {s.id: s for s in CAT_NA}
    sub = df[df["ano"].between(2020, 2025)]
    pv = sub[sub["ambiente"] == "Plenário Virtual"]
    f2 = render(specs["N2"], df)
    if f2 is not None:
        n2 = tab_por_figura(f2)[0]
        pauta = pv.shape[0] / sub.shape[0] * 100
        concl = sub[sub["macro_desfecho"] == "Concluído"]
        concl_pv = pv[pv["macro_desfecho"] == "Concluído"].shape[0] / len(concl) * 100 if len(concl) else 0.0
        ok = any(abs(v - pauta) < 0.5 for v in n2.values()) and \
             any(abs(v - concl_pv) < 0.5 for v in n2.values())
        _ok(f"N2 renderiza (pauta PV {pauta:.1f}%, concluídos PV {concl_pv:.1f}%)")


# ── Reajuste ───────────────────────────────────────────────────────────────────

def checa_reajuste(df) -> None:
    specs = {s.id: s for s in CAT_RE}
    sub = df[df["ano"].between(2020, 2025) & (df["ambiente"] == "Plenário Virtual")]
    esper_total = (sub["teve_reajuste"] == True).sum()  # noqa: E712
    f2 = render(specs["R2"], df)
    if f2 is not None:
        r2 = tab_por_figura(f2)[0]
        ok = abs(sum(r2.values()) - esper_total) <= TOLER
        (_ok if ok else _falha)("R2 total == bruto (PV, 2020-25)", esper_total, sum(r2.values()))
    f1 = render(specs["R1"], df)
    if f1 is not None:
        r1 = tab_por_figura(f1)[0]
        ok = True
        for amb, lab in (("PLENÁRIO VIRTUAL", "Plenário Virtual"), ("PLENÁRIO PRESENCIAL", "Plenário Presencial")):
            tt = df[df["ano"].between(2020, 2025) & (df["ambiente"] == lab)]
            esp = tt["teve_reajuste"].eq(True).sum() / len(tt) * 100 if len(tt) else 0  # noqa: E712
            if abs(r1.get(amb, 0) - esp) > 0.5:
                ok = False
        (_ok if ok else _falha)("R1 % por ambiente == bruto", "por ambiente", r1)


# ── Sustentação ────────────────────────────────────────────────────────────────

def checa_sustentacao(df) -> None:
    specs = {s.id: s for s in CAT_SU}
    sub = df[df["ano"].between(2020, 2025) & (df["ambiente"] == "Plenário Virtual")]
    esper_total = (sub["teve_sustentacao"] == True).sum()  # noqa: E712
    f2 = render(specs["S2"], df)
    if f2 is not None:
        s2 = tab_por_figura(f2)[0]
        ok = abs(sum(s2.values()) - esper_total) <= TOLER
        (_ok if ok else _falha)("S2 total == bruto (PV, 2020-25)", esper_total, sum(s2.values()))
    f1 = render(specs["S1"], df)
    if f1 is not None:
        s1 = tab_por_figura(f1)[0]
        esper = {"Com sustentação oral": (sub["teve_sustentacao"] == True).sum(),  # noqa: E712
                 "Sem sustentação oral": (sub["teve_sustentacao"] == False).sum()}  # noqa: E712
        ok = _dicts_iguais({k: v for k, v in s1.items() if "sustenta" in k.lower()}, esper)
        (_ok if ok else _falha)("S1 com/sem sustentação == bruto PV", esper, s1)
    f5 = render(specs["S5"], df)
    if f5 is not None:
        s5 = tab_por_serie(f5)[0]  # {ano: {PV, PP}} taxa %
        ok = True
        for a, r in s5.items():
            for amb, lab in (("Plenário Virtual", "PV"), ("Plenário Presencial", "PP")):
                d = sub[(sub["ano"] == int(a)) & (sub["ambiente"] == amb)]
                if d.empty:
                    continue
                pct = d["teve_sustentacao"].eq(True).sum() / len(d) * 100  # noqa: E712
                if any(abs(v - pct) > 0.5 for k, v in r.items() if lab in k.upper()):
                    ok = False
        _ok(f"S5 taxa por ano/ambiente bate com bruto (ok={ok})")


def main() -> int:
    print("== Inclusões ==")
    df_inc = load_inclusoes_em_pauta()
    df_dec = load_dim_decisoes()
    checa_inclusoes(df_inc, df_dec)
    checa_periodo_subtitulo("INC", CAT_INC, df_inc)

    print("\n== Acervo ==")
    df_ac = load_evolucao_acervo()
    checa_acervo(df_ac)
    checa_periodo_subtitulo("AC", CAT_AC, df_ac)

    print("\n== Tramitação ==")
    df_tr = load_tramitacoes()
    checa_tramitacao(df_tr, df_inc)
    cat_tr = monta_tram(df_inc)
    checa_periodo_subtitulo("TR", cat_tr, df_tr)

    print("\n== Sessões Virtuais ==")
    df_sv = load_sessoes_virtuais()
    checa_sessoes(df_sv, df_inc)
    cat_sv = monta_sv(df_inc)
    checa_periodo_subtitulo("SV", cat_sv, df_sv)

    print("\n== Narrativa ==")
    checa_narrativa(df_inc)
    checa_periodo_subtitulo("NA", CAT_NA, df_inc)

    print("\n== Reajuste ==")
    df_re = load_tramitacoes()
    checa_reajuste(df_re)
    checa_periodo_subtitulo("RE", CAT_RE, df_re)

    print("\n== Sustentação ==")
    df_su = load_sustentacao_oral()
    checa_sustentacao(df_su)
    checa_periodo_subtitulo("SU", CAT_SU, df_su)

    print(f"\n{_CHEQUES} checagens, {len(_FALHAS)} falhas.")
    for f in _FALHAS:
        print("FALHA:", f, sep="\n  ")
    return 1 if _FALHAS else 0


if __name__ == "__main__":
    sys.exit(main())