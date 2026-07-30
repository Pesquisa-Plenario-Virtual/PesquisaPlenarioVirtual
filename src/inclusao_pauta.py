import re
import unicodedata
from pathlib import Path

import pandas as pd

ANO_INI, ANO_FIM = 2016, 2025

ANDAMENTOS_PAUTA = [
    'Inclua-se em pauta - minuta extraída',
    'Incluído no calendário de julgamento pelo Presidente',
    'Incluído no calendário de julgamento pela Presidente',
    'Incluído no calendário de julgamento',
    'Incluído na lista de julgamento',
    'Apresentado em mesa para julgamento',
    'INCLUA-SE EM PAUTA - MINUTA EXTRAÍDA',
    'APRESENTADO EM MESA PARA JULGAMENTO - MINUTA EXTRAÍDA',
    'PROCESSO A JULGAMENTO - PAUTA, DJ:',
    'PROCESSO EM MESA',
]

INICIO_JULGAMENTO_VIRTUAL = "Iniciado Julgamento Virtual"

SESSION_VISTA_NAMES = {
    'Vista ao(à) Ministro(a)',
    'VISTA AO MINISTRO',
    'VISTA À MINISTRA',
    'Vista',
    'VISTA',
}

VISTA_EXCLUSIONS = {'agu', 'procurador', 'advocacia-geral'}

DESTAQUE_NOMES = {
    'Processo destacado no Julgamento Virtual',
    'Destaque do(a) Ministro(a)',
}

DESTAQUE_NOMES_FISICO = {
    'Destaque do(a) Ministro(a)',
}

ANDAMENTOS_RETIRADA = {
    'Retirado de pauta',
    'RETIRADO DE PAUTA',
    'Pauta cancelada',
    'Retirado de mesa',
    'RETIRADO DA MESA DO PLENÁRIO',
    'Excluído do calendário de julgamento pelo Presidente',
    'Excluído do calendário de julgamento pela Presidente',
    'Retirado do Julgamento Virtual',
}

ANDAMENTOS_RETIRADA_FISICO = ANDAMENTOS_RETIRADA - {'Retirado do Julgamento Virtual'}

ANDAMENTOS_ADIAMENTO = {
    'ADIADO O JULGAMENTO',
    'Adiado o julgamento',
    'Suspenso o julgamento',
    'SOBRESTADO O PROCESSO',
    'Sobrestado',
}

RE_LIMPEZA_DECISOES = (
    r'Incluído na Lista|Agendado para|Julgamento Presencial|'
    r'Sess[ãa]o (?:Ordinária|Extraordinária|Ordinaria|Extraordinaria) Virtual'
)

RE_SUFIXO_MODERNO = re.compile(
    r'Julgamento Virtual:\s*([A-Z]{2,5})([\-\s][A-Za-z][\w\-]*)?\s*[\.{]'
)
RE_SUFIXO_ANTIGO = re.compile(
    r'-\s*([A-Z]{2,5})([\-][A-Za-z][\w\-]*)?\s*$'
)
RE_SUFIXO_FISICO = re.compile(
    r'\b(ADI|ADPF|ADC|ADO)([-\s][A-Za-z][\w\-]*)?\b'
)

COLS_FINAL = [
    'incidente', 'nome_processo', 'classe', 'relator', 'ano',
    'data_inclusao', 'data_inclusao_dt', 'ambiente',
    'tipo_questao', 'tipo_questao_original', 'sufixo_extraido',
    'desfecho', 'macro_desfecho', 'andamento_origem', 'virou_sessao',
]

COLS_SESSOES = [
    'incidente', 'nome_processo', 'classe', 'relator', 'ano',
    'data_sessao', 'data_sessao_dt', 'ambiente',
    'tipo_questao', 'tipo_questao_original', 'sufixo_extraido',
    'desfecho', 'macro_desfecho',
]


def extrair_sufixo(complemento: str):
    """
    Extrai o sufixo de classe do and_complemento de um evento virtual.
    Retorna None se não encontrar (indica PR ou formato não reconhecido).
    """
    if not isinstance(complemento, str):
        return None

    m = RE_SUFIXO_MODERNO.search(complemento)
    if m:
        classe = m.group(1)
        sufixo = (m.group(2) or '').strip(' -')
        return f"{classe}-{sufixo}" if sufixo else classe

    if 'Julgamento Virtual' in complemento:
        m2 = RE_SUFIXO_ANTIGO.search(complemento)
        if m2:
            classe = m2.group(1)
            sufixo = (m2.group(2) or '').strip(' -')
            return f"{classe}-{sufixo}" if sufixo else classe

    return None


def extrair_sufixo_fisico(complemento):
    """Extrai o sufixo de classe do complemento de um evento físico."""
    if not isinstance(complemento, str):
        return None

    m = RE_SUFIXO_FISICO.search(complemento)
    if m:
        classe = m.group(1)
        sufixo = (m.group(2) or '').strip(' -')
        return f"{classe}-{sufixo}" if sufixo else classe

    return None


def classificar_tipo_questao(sufixo) -> str:
    """
    Classifica o tipo de questão conforme Tabela 2 da dissertação (p. 62).

    PR — Principal: julgamento de mérito (sem sufixo)
    RC — Recurso: AgR, ED, AgR-ED, ED-AgR, ED-ED, ED-segundos...
    IJ — Questão incidental: MC, MC-Ref, TPI, TPI-Ref, QO, Acordo
    """
    if not isinstance(sufixo, str):
        return 'Não identificado'

    partes = sufixo.upper().split('-')[1:]
    if not partes:
        return 'PR'

    s = '-'.join(partes)

    if re.search(r'\bED\b|AGR', s):
        return 'RC'

    if re.search(r'\bMC\b|\bTPI\b|\bREF\b|\bQO\b|ACORDO', s):
        return 'IJ'

    return 'Não identificado'


def normalizar_texto(txt: str) -> str:
    """Remove acentos e converte para minúsculas para busca de termos."""
    if not isinstance(txt, str):
        return ''

    txt = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii')
    return txt.lower()


def eh_vista_ministro(and_nome, and_complemento) -> bool:
    """
    True se o andamento é pedido de vista de MINISTRO.
    Exclui vista processual (AGU, PGR, advocacia-geral).
    Captura também "Suspenso o julgamento" quando o complemento cita vista.
    """
    nome = str(and_nome or '')
    comp = str(and_complemento or '')

    if nome in SESSION_VISTA_NAMES or (
        nome == 'Suspenso o julgamento' and 'vista' in comp.lower()
    ):
        if not any(exc in (nome + ' ' + comp).lower() for exc in VISTA_EXCLUSIONS):
            return True
    return False


def classificar_desfecho_texto(texto):
    """
    Classifica desfecho pelo texto de dec_complemento.
    Cobre apenas os CONCLUÍDOS — vista, destaque e retirada vêm dos andamentos.
    Retorna None se o texto não tiver fórmula de votação.
    """
    t = normalizar_texto(texto)
    if not t:
        return None

    if re.search(r'unanimidade|unanime', t):
        return 'Concluído - decisão unânime'

    if re.search(r'por\s+maioria', t):
        if re.search(r'vencid[oa]s?\s+o[s]?\s+(?:senhor[es]?\s+)?'
                     r'ministr[oa]s?\s+[^.]{0,120}\(relator[a]?\)', t):
            return 'Concluído - decisão maioria, vencido o relator'
        return 'Concluído - decisão maioria com o relator'

    return None


def extrair_janela_sessao(complemento, data_inclusao, eh_virtual=True):
    """
    Extrai (sessao_inicio, sessao_fim) do complemento do andamento.

    Virtual:
      "Agendado para: 10/03/2023 a 17/03/2023" → (10/03, 17/03 + 7d)
      "Agendado para: 19/06/2020"              → (19/06, 19/06 + 14d)
      fallback                                 → (data_inclusao, +30d)

    Físico:
      "Data de Julgamento: 23/02/2023"         → (data_inclusao, 23/02 + 3d)
      "Pleno em 23/02/2023"                    → (data_inclusao, 23/02 + 3d)
      fallback                                 → (data_inclusao, +7d)

    A janela agendada é essencial: cobre pautas que atravessam o recesso
    (inclusão em dez → sessão em fev, ~52 dias), que uma tolerância fixa
    de dias cortaria indevidamente.
    """
    if isinstance(complemento, str):
        if eh_virtual:
            m = re.search(
                r'Agendado para:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})',
                complemento
            )
            if m:
                ini = pd.to_datetime(m.group(1), dayfirst=True)
                fim = pd.to_datetime(m.group(2), dayfirst=True)
                return ini, fim + pd.Timedelta(days=7)

            m = re.search(r'Agendado para:\s*(\d{2}/\d{2}/\d{4})', complemento)
            if m:
                ini = pd.to_datetime(m.group(1), dayfirst=True)
                return ini, ini + pd.Timedelta(days=14)
        else:
            m = re.search(
                r'Data d[eo] [Jj]ulgamento:\s*(\d{2}/\d{2}/\d{4})'
                r'|Pleno em\s*(\d{2}/\d{2}/\d{4})',
                complemento
            )
            if m:
                data_str = m.group(1) or m.group(2)
                dt = pd.to_datetime(data_str, dayfirst=True)
                return data_inclusao, dt + pd.Timedelta(days=3)

    if eh_virtual:
        return data_inclusao, data_inclusao + pd.Timedelta(days=30)
    return data_inclusao, data_inclusao + pd.Timedelta(days=7)


def _extrair_janelas(df_pauta, eh_virtual):
    if df_pauta.empty:
        return pd.Series(dtype='datetime64[ns]'), pd.Series(dtype='datetime64[ns]')

    janelas = df_pauta.apply(
        lambda r: extrair_janela_sessao(r.get('and_complemento', ''), r['and_data_dt'], eh_virtual=eh_virtual),
        axis=1, result_type='expand'
    )
    return janelas[0], janelas[1]


def _classificar_desfechos(pauta_df, and_ambiente_df, dec_df, retirada_nomes, destaque_nomes):
    """
    Loop de classificação de desfecho compartilhado entre pautas virtuais,
    pautas físicas e sessões virtuais iniciadas.

    pauta_df precisa ter as colunas: incidente, and_data_dt, and_index,
    fim_janela (fim da janela de observação de eventos/decisões) e dec_ref
    (data de referência para casar e ordenar decisões dentro da janela).
    """
    if pauta_df.empty:
        return pd.DataFrame(columns=['incidente', 'and_index', 'desfecho'])

    resultados = []

    for _, pauta in pauta_df.iterrows():
        inc = pauta['incidente']
        inicio = pauta['and_data_dt']
        and_idx = pauta['and_index']
        fim_janela = pauta['fim_janela']
        dec_ref = pauta['dec_ref']

        eventos = and_ambiente_df[
            (and_ambiente_df['incidente'] == inc) &
            (and_ambiente_df['and_data_dt'] >= inicio) &
            (and_ambiente_df['and_data_dt'] < fim_janela) &
            (and_ambiente_df['and_index'] > and_idx)
        ]

        if eventos['and_nome'].isin(retirada_nomes).any():
            desfecho = 'Não concluído - retirado de pauta'

        elif eventos['and_nome'].isin(destaque_nomes).any():
            desfecho = 'Não concluído - destaque'

        elif eventos.apply(
            lambda r: eh_vista_ministro(r['and_nome'], r['and_complemento']), axis=1
        ).any():
            desfecho = 'Não concluído - pedido de vista'

        else:
            dec_janela = dec_df[
                (dec_df['incidente'] == inc) &
                (dec_df['dec_data_dt'] >= dec_ref - pd.Timedelta(days=1)) &
                (dec_df['dec_data_dt'] < fim_janela)
            ].copy()

            desfecho = None
            if not dec_janela.empty:
                dec_janela['diff'] = (dec_janela['dec_data_dt'] - dec_ref).dt.days.abs()
                dec_janela = dec_janela.sort_values('diff')
                for _, d in dec_janela.iterrows():
                    r = classificar_desfecho_texto(d['dec_complemento'])
                    if r:
                        desfecho = r
                        break

            if desfecho is None:
                desfecho = 'Não concluído - motivos diversos'

        resultados.append({'incidente': inc, 'and_index': and_idx, 'desfecho': desfecho})

    return pd.DataFrame(resultados)


def inclusao_virou_sessao(row, df_sessoes):
    inc = row['incidente']
    sessao_inicio, sessao_fim = extrair_janela_sessao(
        row.get('and_complemento', ''), row['and_data_dt'], eh_virtual=True
    )
    s = df_sessoes[
        (df_sessoes['incidente'] == inc) &
        (df_sessoes['and_data_dt'] >= sessao_inicio - pd.Timedelta(days=3)) &
        (df_sessoes['and_data_dt'] <= sessao_fim)
    ]
    return not s.empty


def herdar_tipo_questao(sessao, df_virt_pauta):
    inc = sessao['incidente']
    data_sessao = sessao['and_data_dt']

    candidatas = df_virt_pauta[df_virt_pauta['incidente'] == inc]

    melhor = None
    for _, incl in candidatas.iterrows():
        s_ini, s_fim = extrair_janela_sessao(
            incl.get('and_complemento', ''), incl['and_data_dt'], eh_virtual=True
        )
        if s_ini - pd.Timedelta(days=3) <= data_sessao <= s_fim:
            melhor = incl
            break

    if melhor is None:
        anteriores = candidatas[
            (candidatas['and_data_dt'] <= data_sessao) &
            (candidatas['and_data_dt'] >= data_sessao - pd.Timedelta(days=60))
        ].sort_values('and_data_dt')
        if not anteriores.empty:
            melhor = anteriores.iloc[-1]

    if melhor is not None:
        return pd.Series([melhor['tipo_questao'], melhor['sufixo_extraido']])
    return pd.Series([None, None])


def selecionar_e_classificar_pauta(df_and):
    df_pauta = df_and[df_and['and_nome'].isin(ANDAMENTOS_PAUTA)].copy()

    df_pauta['eh_virtual'] = df_pauta['and_complemento'].str.contains(
        'Julgamento Virtual', case=False, na=False
    )

    df_pauta['sufixo_extraido'] = df_pauta.apply(
        lambda r: extrair_sufixo(r['and_complemento']) if r['eh_virtual']
        else extrair_sufixo_fisico(r['and_complemento']),
        axis=1
    )
    df_pauta['tipo_questao'] = df_pauta['sufixo_extraido'].apply(classificar_tipo_questao)

    df_pauta['ambiente'] = df_pauta['eh_virtual'].map({
        True: 'Plenário Virtual', False: 'Plenário Físico'
    })

    df_pauta['and_data_dt'] = pd.to_datetime(
        df_pauta['and_data'], dayfirst=True, errors='coerce'
    )

    df_virt_pauta = df_pauta[df_pauta['eh_virtual']].copy()
    df_fis_pauta = df_pauta[~df_pauta['eh_virtual']].copy()

    return df_virt_pauta, df_fis_pauta


def limpar_decisoes_virtuais(df_dec):
    dec_virt = df_dec[
        df_dec['dec_julgador'].str.contains(
            'VIRTUAL|SESSÃO VIRTUAL|SESSAO VIRTUAL', case=False, na=False
        )
    ].copy()
    dec_virt['dec_data_dt'] = pd.to_datetime(
        dec_virt['dec_data'], dayfirst=True, errors='coerce'
    )
    dec_virt = dec_virt[
        ~dec_virt['dec_complemento'].str.contains(
            RE_LIMPEZA_DECISOES, case=False, na=False, regex=True
        )
    ]
    return dec_virt


def classificar_desfecho_virtual(df_virt_pauta, df_and, dec_virt):
    incidentes_virt = set(df_virt_pauta['incidente'].unique())
    df_and_virt = df_and[df_and['incidente'].isin(incidentes_virt)].copy()
    df_and_virt['and_data_dt'] = pd.to_datetime(
        df_and_virt['and_data'], dayfirst=True, errors='coerce'
    )

    df_virt_pauta = df_virt_pauta.sort_values(
        ['incidente', 'and_data_dt', 'and_index']
    ).copy()
    df_virt_pauta['proxima_entrada_dt'] = (
        df_virt_pauta.groupby('incidente')['and_data_dt'].shift(-1)
    )

    df_virt_pauta['sessao_inicio'], df_virt_pauta['sessao_fim'] = _extrair_janelas(df_virt_pauta, eh_virtual=True)

    proxima = df_virt_pauta['proxima_entrada_dt']
    depois_do_inicio = proxima.notna() & (proxima > df_virt_pauta['sessao_inicio'])
    df_virt_pauta['fim_janela'] = df_virt_pauta['sessao_fim'].where(
        ~depois_do_inicio, df_virt_pauta[['sessao_fim', 'proxima_entrada_dt']].min(axis=1)
    )
    df_virt_pauta['dec_ref'] = df_virt_pauta['sessao_inicio']

    df_desfechos = _classificar_desfechos(
        df_virt_pauta, df_and_virt, dec_virt, ANDAMENTOS_RETIRADA, DESTAQUE_NOMES
    )
    df_virt_pauta = df_virt_pauta.drop(columns=['desfecho'], errors='ignore').merge(
        df_desfechos, on=['incidente', 'and_index'], how='left'
    )
    df_virt_pauta['desfecho'] = df_virt_pauta['desfecho'].fillna(
        'Não concluído - motivos diversos'
    )

    return df_virt_pauta, df_and_virt


def classificar_desfecho_fisico(df_fis_pauta, df_and, df_dec):
    incidentes_fis = set(df_fis_pauta['incidente'].unique())
    df_and_fis = df_and[df_and['incidente'].isin(incidentes_fis)].copy()
    df_and_fis['and_data_dt'] = pd.to_datetime(
        df_and_fis['and_data'], dayfirst=True, errors='coerce'
    )

    dec_fisica = df_dec[
        df_dec['incidente'].isin(incidentes_fis) &
        (~df_dec['dec_julgador'].str.contains(
            'VIRTUAL|SESSÃO VIRTUAL|SESSAO VIRTUAL', case=False, na=False
        ))
    ].copy()
    dec_fisica['dec_data_dt'] = pd.to_datetime(
        dec_fisica['dec_data'], dayfirst=True, errors='coerce'
    )
    dec_fisica = dec_fisica[
        ~dec_fisica['dec_complemento'].str.contains(
            RE_LIMPEZA_DECISOES, case=False, na=False, regex=True
        )
    ]

    df_fis_pauta = df_fis_pauta.sort_values(
        ['incidente', 'and_data_dt', 'and_index']
    ).copy()
    df_fis_pauta['proxima_entrada_dt'] = (
        df_fis_pauta.groupby('incidente')['and_data_dt'].shift(-1)
    )

    df_fis_pauta['sessao_inicio'], df_fis_pauta['sessao_fim'] = _extrair_janelas(df_fis_pauta, eh_virtual=False)

    proxima = df_fis_pauta['proxima_entrada_dt']
    depois_do_inicio = proxima.notna() & (proxima > df_fis_pauta['sessao_inicio'])
    df_fis_pauta['fim_janela'] = df_fis_pauta['sessao_fim'].where(
        ~depois_do_inicio, df_fis_pauta[['sessao_fim', 'proxima_entrada_dt']].min(axis=1)
    )
    df_fis_pauta['dec_ref'] = df_fis_pauta['and_data_dt']

    df_desfechos_fis = _classificar_desfechos(
        df_fis_pauta, df_and_fis, dec_fisica, ANDAMENTOS_RETIRADA_FISICO, DESTAQUE_NOMES_FISICO
    )
    df_fis_pauta = df_fis_pauta.drop(columns=['desfecho'], errors='ignore').merge(
        df_desfechos_fis, on=['incidente', 'and_index'], how='left'
    )
    df_fis_pauta['desfecho'] = df_fis_pauta['desfecho'].fillna(
        'Não concluído - motivos diversos'
    )

    return df_fis_pauta


def montar_sessoes_virtuais(df_and, df_virt_pauta, df_and_virt, dec_virt, ano_ini=ANO_INI, ano_fim=ANO_FIM):
    df_sessoes = df_and[df_and['and_nome'] == INICIO_JULGAMENTO_VIRTUAL].copy()
    df_sessoes['and_data_dt'] = pd.to_datetime(
        df_sessoes['and_data'], dayfirst=True, errors='coerce'
    )
    df_sessoes['ano'] = df_sessoes['and_data_dt'].dt.year
    df_sessoes = df_sessoes[df_sessoes['ano'].between(ano_ini, ano_fim)].copy()

    df_virt_pauta['virou_sessao'] = df_virt_pauta.apply(
        lambda r: inclusao_virou_sessao(r, df_sessoes), axis=1
    )

    if df_sessoes.empty:
        df_sessoes['tipo_questao'] = pd.Series(dtype='object')
        df_sessoes['sufixo_extraido'] = pd.Series(dtype='object')
    else:
        df_sessoes[['tipo_questao', 'sufixo_extraido']] = df_sessoes.apply(
            lambda r: herdar_tipo_questao(r, df_virt_pauta), axis=1
        )
    df_sessoes['tipo_questao'] = df_sessoes['tipo_questao'].fillna('Não identificado')

    df_sessoes = df_sessoes.sort_values(
        ['incidente', 'and_data_dt', 'and_index']
    ).copy()
    df_sessoes['proxima_sessao_dt'] = (
        df_sessoes.groupby('incidente')['and_data_dt'].shift(-1)
    )

    proxima = df_sessoes['proxima_sessao_dt']
    depois_do_inicio = proxima.notna() & (proxima > df_sessoes['and_data_dt'])
    df_sessoes['fim_janela'] = df_sessoes['and_data_dt'] + pd.Timedelta(days=21)
    df_sessoes.loc[depois_do_inicio, 'fim_janela'] = proxima[depois_do_inicio]
    df_sessoes['dec_ref'] = df_sessoes['and_data_dt']

    df_desfechos_sessao = _classificar_desfechos(
        df_sessoes, df_and_virt, dec_virt, ANDAMENTOS_RETIRADA, DESTAQUE_NOMES
    )
    df_sessoes = df_sessoes.drop(columns=['desfecho'], errors='ignore').merge(
        df_desfechos_sessao, on=['incidente', 'and_index'], how='left'
    )
    df_sessoes['desfecho'] = df_sessoes['desfecho'].fillna(
        'Não concluído - motivos diversos'
    )

    df_sessoes['macro_desfecho'] = df_sessoes['desfecho'].apply(
        lambda d: 'Concluído' if str(d).startswith('Concluído')
        else ('Não concluído' if str(d).startswith('Não concluído') else 'Sem registro')
    )

    return df_sessoes


def montar_tabela_final(df_virt_pauta, df_fis_pauta, df_fato, ano_ini=ANO_INI, ano_fim=ANO_FIM):
    df_final = pd.concat([df_virt_pauta, df_fis_pauta], ignore_index=True)

    if 'virou_sessao' in df_final.columns:
        df_final['virou_sessao'] = df_final['virou_sessao'].fillna(False).astype(bool)
    else:
        df_final['virou_sessao'] = False

    df_final = df_final.merge(df_fato, on='incidente', how='left')

    df_final['ano'] = df_final['and_data_dt'].dt.year
    df_final = df_final[df_final['ano'].between(ano_ini, ano_fim)].copy()

    df_final = df_final.rename(columns={
        'and_data': 'data_inclusao',
        'and_data_dt': 'data_inclusao_dt',
        'and_nome': 'andamento_origem',
    })

    df_final['macro_desfecho'] = df_final['desfecho'].apply(
        lambda d: 'Concluído' if str(d).startswith('Concluído')
        else ('Não concluído' if str(d).startswith('Não concluído') else 'Sem registro')
    )

    df_final['tipo_questao_original'] = df_final['tipo_questao']

    mask_virt = df_final['ambiente'] == 'Plenário Virtual'
    df_final.loc[mask_virt, 'tipo_questao'] = (
        df_final.loc[mask_virt, 'tipo_questao'].replace('Não identificado', 'PR')
    )

    return df_final[[c for c in COLS_FINAL if c in df_final.columns]]


def montar_tabela_sessoes(df_sessoes, df_fato):
    df_sessoes_final = df_sessoes.merge(df_fato, on='incidente', how='left')

    df_sessoes_final = df_sessoes_final.rename(columns={
        'and_data': 'data_sessao',
        'and_data_dt': 'data_sessao_dt',
    })
    df_sessoes_final['ambiente'] = 'Plenário Virtual'

    df_sessoes_final['tipo_questao_original'] = df_sessoes_final['tipo_questao']
    df_sessoes_final['tipo_questao'] = (
        df_sessoes_final['tipo_questao'].replace('Não identificado', 'PR')
    )

    return df_sessoes_final[[c for c in COLS_SESSOES if c in df_sessoes_final.columns]]


def run_pipeline(processed_dir, interim_dir, out_dir):
    processed_dir = Path(processed_dir)
    out_dir = Path(out_dir)

    df_and = pd.read_parquet(
        processed_dir / 'dim_andamentos.parquet',
        columns=['incidente', 'and_index', 'and_data', 'and_nome', 'and_complemento']
    )
    df_dec = pd.read_parquet(
        processed_dir / 'dim_decisoes.parquet',
        columns=['incidente', 'dec_index', 'dec_data', 'dec_complemento', 'dec_julgador']
    )
    df_fato = pd.read_parquet(
        processed_dir / 'arquivosConcatenados.parquet',
        columns=['incidente', 'classe', 'nome_processo', 'relator']
    )

    df_virt_pauta, df_fis_pauta = selecionar_e_classificar_pauta(df_and)

    dec_virt = limpar_decisoes_virtuais(df_dec)
    df_virt_pauta, df_and_virt = classificar_desfecho_virtual(df_virt_pauta, df_and, dec_virt)
    df_fis_pauta = classificar_desfecho_fisico(df_fis_pauta, df_and, df_dec)

    df_sessoes = montar_sessoes_virtuais(df_and, df_virt_pauta, df_and_virt, dec_virt)

    df_final = montar_tabela_final(df_virt_pauta, df_fis_pauta, df_fato)
    df_sessoes_final = montar_tabela_sessoes(df_sessoes, df_fato)

    out_dir.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(out_dir / 'inclusoes_em_pauta.parquet', index=False)
    df_sessoes_final.to_parquet(out_dir / 'sessoes_virtuais.parquet', index=False)

    return df_final, df_sessoes_final


def _selfcheck():
    assert extrair_sufixo('Julgamento Virtual: ADC-ED. Incluído na Lista 92-2024') == 'ADC-ED'
    assert extrair_sufixo('Julgamento Virtual: . Incluído na Lista') is None
    assert extrair_sufixo('Julgamento Virtual - Pleno em 04/09/2018 14:44:32 - ADC-AgR-ED') == 'ADC-AgR-ED'
    assert extrair_sufixo(None) is None

    assert extrair_sufixo_fisico('Pauta contém ADI-MC 1234') == 'ADI-MC'
    assert extrair_sufixo_fisico('sem classe aqui') is None

    assert classificar_tipo_questao(None) == 'Não identificado'
    assert classificar_tipo_questao('ADI') == 'PR'
    assert classificar_tipo_questao('ADI-ED') == 'RC'
    assert classificar_tipo_questao('ADI-AgR') == 'RC'
    assert classificar_tipo_questao('ADI-MC') == 'IJ'
    assert classificar_tipo_questao('ADI-MC-Ref-ED') == 'RC'
    assert classificar_tipo_questao('ADI-XYZ') == 'Não identificado'

    assert normalizar_texto('Decisão à Unanimidade') == 'decisao a unanimidade'
    assert normalizar_texto(None) == ''

    assert eh_vista_ministro('Vista', '') is True
    assert eh_vista_ministro('Vista ao(à) Ministro(a)', 'AGU pediu vista') is False
    assert eh_vista_ministro('Suspenso o julgamento', 'pedido de vista do ministro') is True
    assert eh_vista_ministro('Suspenso o julgamento', 'sem relação') is False
    assert eh_vista_ministro('Outro andamento', '') is False

    assert classificar_desfecho_texto('Decisão por unanimidade') == 'Concluído - decisão unânime'
    assert classificar_desfecho_texto(
        'Decisão: Por maioria, vencidos os ministros Fulano (Relator)'
    ) == 'Concluído - decisão maioria, vencido o relator'
    assert classificar_desfecho_texto('Decisão por maioria') == 'Concluído - decisão maioria com o relator'
    assert classificar_desfecho_texto('texto qualquer sem fórmula') is None

    ini, fim = extrair_janela_sessao('Agendado para: 10/03/2023 a 17/03/2023', pd.Timestamp('2023-03-01'), eh_virtual=True)
    assert ini == pd.Timestamp('2023-03-10') and fim == pd.Timestamp('2023-03-24')

    print("inclusao_pauta: selfcheck OK")


if __name__ == "__main__":
    _selfcheck()
