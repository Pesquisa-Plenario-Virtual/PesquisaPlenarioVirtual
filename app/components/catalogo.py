"""Casca de página: busca, sumário navegável, seletor e compartilhamento.

Substitui os seis render_graficos duplicados nas páginas temáticas.
filtrar_por_busca e sumario_por_bloco são puros para poderem ser testados.
"""

from __future__ import annotations

import unicodedata

import streamlit as st

from components.grafico import GraficoSpec, render_grafico


def _sem_acento(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def filtrar_por_busca(catalogo: list[GraficoSpec], termo: str) -> list[GraficoSpec]:
    """Filtra o catálogo por id, rótulo ou descrição, ignorando caixa e acento."""
    alvo = _sem_acento(termo.strip())
    if not alvo:
        return list(catalogo)
    return [
        s for s in catalogo
        if alvo in _sem_acento(f"{s.id} {s.rotulo} {s.descricao}")
    ]


def sumario_por_bloco(catalogo: list[GraficoSpec]) -> dict[str, list[GraficoSpec]]:
    """Agrupa o catálogo pelo prefixo alfabético do id (T5 -> 'T', 2.a -> '2')."""
    blocos: dict[str, list[GraficoSpec]] = {}
    for spec in catalogo:
        prefixo = "".join(c for c in spec.id if not c.isdigit()).split("/")[0].split(".")[0]
        blocos.setdefault(prefixo.strip() or spec.id[:1], []).append(spec)
    return blocos


def distribuir_em_colunas(specs: list[GraficoSpec], n: int = 3) -> list[list[GraficoSpec]]:
    """Reparte o catálogo em `n` colunas de altura parecida, preservando a ordem.

    Uma coluna por bloco não serve: páginas como Inclusões têm 18 entradas com o
    mesmo prefixo, então tudo caía numa coluna só e o sumário ficava mais alto
    que o resto da página.
    """
    if not specs:
        return []
    n = max(1, min(n, len(specs)))
    por_coluna, resto = divmod(len(specs), n)
    colunas, inicio = [], 0
    for i in range(n):
        fim = inicio + por_coluna + (1 if i < resto else 0)
        colunas.append(specs[inicio:fim])
        inicio = fim
    return colunas


def nome_param_url(key_prefix: str) -> str:
    """Nome do query param que semeia a seleção, isolado por página."""
    return f"g_{key_prefix}"


def render_pagina(catalogo: list[GraficoSpec], df, key_prefix: str,
                  sumario_titulo: str = "Sumário — visualizações disponíveis") -> None:
    """Renderiza uma página inteira a partir do seu catálogo."""
    chave_sel = f"{key_prefix}_selecionado"

    # Estado vindo do link compartilhado, lido só uma vez.
    if chave_sel not in st.session_state:
        do_link = st.query_params.get(nome_param_url(key_prefix))
        st.session_state[chave_sel] = do_link if any(
            s.id == do_link for s in catalogo) else catalogo[0].id

    # A busca filtra só o sumário (os botões); o gráfico em exibição não muda.
    busca = st.text_input("🔎 Buscar gráfico", key=f"{key_prefix}_busca",
                          placeholder="id, título ou palavra da descrição")
    visiveis = filtrar_por_busca(catalogo, busca)

    with st.expander(f"{sumario_titulo} ({len(catalogo)})", expanded=False):
        if not visiveis:
            st.warning(f"Nenhum gráfico corresponde a “{busca}”.")
        else:
            for coluna, specs in zip(st.columns(3), distribuir_em_colunas(visiveis, 3)):
                with coluna:
                    for spec in specs:
                        if st.button(spec.rotulo, key=f"{key_prefix}_ir_{spec.id}",
                                     width="stretch"):
                            st.session_state[chave_sel] = spec.id
                            st.rerun()

    st.markdown("---")

    atual = st.session_state[chave_sel]
    spec = next((s for s in catalogo if s.id == atual), catalogo[0])

    st.subheader(spec.subtitulo)
    st.caption(spec.descricao)

    # Uma entrada pode trazer o próprio renderizador — é assim que o tabulador
    # de eixos livres entra no catálogo em vez de ficar fixo no rodapé de toda
    # página, aparecendo embaixo de qualquer gráfico selecionado.
    if spec.renderer is not None:
        spec.renderer(df, f"{key_prefix}_{spec.id}")
    else:
        render_grafico(spec, df, key=f"{key_prefix}_{spec.id}")
