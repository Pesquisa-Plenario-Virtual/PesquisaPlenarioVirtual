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


def nome_param_url(key_prefix: str) -> str:
    """Nome do query param de compartilhamento, isolado por página."""
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

    # A busca filtra só o sumário (os botões), nunca as opções do selectbox.
    # O selectbox sempre carrega o catálogo inteiro com uma key fixa, então
    # suas opções nunca mudam e seu estado nunca precisa ser invalidado —
    # nenhum jogo de key por valor é necessário.
    busca = st.text_input("🔎 Buscar gráfico", key=f"{key_prefix}_busca",
                          placeholder="id, título ou palavra da descrição")
    visiveis = filtrar_por_busca(catalogo, busca)

    with st.expander(sumario_titulo, expanded=True):
        if not visiveis:
            st.warning(f"Nenhum gráfico corresponde a “{busca}”.")
        else:
            blocos = sumario_por_bloco(visiveis)
            cols = st.columns(min(len(blocos), 2) or 1)
            for i, (bloco, specs) in enumerate(blocos.items()):
                with cols[i % len(cols)]:
                    st.markdown(f"**Bloco {bloco}**")
                    for spec in specs:
                        if st.button(spec.rotulo, key=f"{key_prefix}_ir_{spec.id}",
                                     width="stretch"):
                            st.session_state[chave_sel] = spec.id
                            st.rerun()

    st.markdown("---")

    ids = [s.id for s in catalogo]
    atual = st.session_state[chave_sel]
    indice = ids.index(atual) if atual in ids else 0
    escolhido = st.selectbox(
        "Selecione a visualização", ids, index=indice, key=f"{key_prefix}_sel",
        format_func=lambda i: next(s.rotulo for s in catalogo if s.id == i),
    )
    st.session_state[chave_sel] = escolhido
    spec = next(s for s in catalogo if s.id == escolhido)

    st.subheader(spec.subtitulo)
    st.caption(spec.descricao)

    render_grafico(spec, df, key=f"{key_prefix}_{spec.id}")

    if st.button("🔗 Copiar link deste gráfico", key=f"{key_prefix}_link"):
        param = nome_param_url(key_prefix)
        st.query_params[param] = spec.id
        st.code(f"?{param}={spec.id}", language=None)
        st.caption("Link atualizado na barra de endereço.")
