import re
from pathlib import Path

import pandas as pd

RE_VOTO_DIRETO = re.compile(
    r'vot\w*[\s,]+(?:ora\s+)?reajustad\w*'
    r'|vot\w*[\s,]+(?:ora\s+)?alterad\w*'
    r'|vot\w*[\s,]+(?:ora\s+)?reformulad\w*'
    r'|vot\w*[\s,]+(?:ora\s+)?aditad\w*'
    r'|reajust\w*\s+.{0,20}?vot'
    r'|altera[çc]\w*\s+d[eo]\s+vot'
    r'|reformul\w*\s+.{0,20}?vot'
    r'|adit\w*\s+(?:\w+\s+){0,2}?vot(?:o|os)\b'
    r'|ajust\w*\s+.{0,20}?vot'
    r'|alteraram\s+(?:os\s+|seus\s+)?vot'
    r'|reajustad\w*\s+.{0,30}?vot'
    r'|(?:relator|ministr\w*)[^.]{0,40}?(?:agora|ora)\s+reajustad\w*'
    r'|vot\w*[\s,]+(?:ora\s+)?retificad\w*'
    r'|retific\w*\s+.{0,20}?vot'
    r'|retificad\w*\s+.{0,30}?vot',
    re.IGNORECASE
)

RE_MINISTRO = re.compile(r'ministr[oa]|relator[a]?', re.IGNORECASE)

RE_SUSTENTACAO = re.compile(r'sustenta[çc]\w*\s+or', re.IGNORECASE)
RE_SUST_NEGADA = re.compile(
    r'(?:indefer\w*|rejeit\w*|neg\w*|cancel\w*)\s+.{0,30}?sustenta[çc]\w*\s+or'
    r'|sustenta[çc]\w*\s+or\w*\s+.{0,30}?(?:indefer\w*|rejeit\w*|negad\w*|cancelad\w*)',
    re.IGNORECASE
)

PERIODO_INICIO = '2020-01-01'
PERIODO_FIM = '2026-01-31'


def tem_reajuste_voto(texto):
    if not isinstance(texto, str):
        return False
    return bool(RE_VOTO_DIRETO.search(texto)) and bool(RE_MINISTRO.search(texto))


def eh_sustentacao(and_nome, and_complemento):
    nome = str(and_nome or '')
    comp = str(and_complemento or '')
    tem_sustentacao = (nome == 'Sustentação Oral') or bool(RE_SUSTENTACAO.search(comp))
    if not tem_sustentacao:
        return False
    if nome == 'Arquivo de sustentação oral rejeitado':
        return False
    return not bool(RE_SUST_NEGADA.search(comp))


def detectar_reajuste_de_voto(dim_andamentos):
    df = dim_andamentos.copy()
    df['and_data_dt'] = pd.to_datetime(df['and_data'], dayfirst=True, errors='coerce')
    mask_periodo = df['and_data_dt'].between(PERIODO_INICIO, PERIODO_FIM)
    df['tem_reajuste'] = False
    df.loc[mask_periodo, 'tem_reajuste'] = (
        df.loc[mask_periodo, 'and_complemento'].apply(tem_reajuste_voto)
    )
    return df[df['tem_reajuste']].copy()


def verificar_sustentacao_oral(dim_andamentos):
    df = dim_andamentos.copy()
    df['eh_sustentacao'] = df.apply(
        lambda row: eh_sustentacao(row['and_nome'], row['and_complemento']), axis=1
    )
    df['and_data_dt'] = pd.to_datetime(df['and_data'], dayfirst=True, errors='coerce')
    return df[df['eh_sustentacao']].copy()


def _teve_evento_na_janela(inclusoes, eventos, dias_antes, dias_depois):
    incidentes_com_evento = set(eventos['incidente'].unique())

    def teve_evento(row):
        inc = row['incidente']
        if inc not in incidentes_com_evento:
            return False
        inicio = row['data_inclusao_dt']
        janela_ini = inicio - pd.Timedelta(days=dias_antes)
        janela_fim = inicio + pd.Timedelta(days=dias_depois)
        eventos_processo = eventos[
            (eventos['incidente'] == inc)
            & (eventos['and_data_dt'] >= janela_ini)
            & (eventos['and_data_dt'] < janela_fim)
        ]
        return not eventos_processo.empty

    return inclusoes.apply(teve_evento, axis=1)


def vincular_reajuste_a_inclusoes(inclusoes, reajustes):
    df = inclusoes.copy()
    df['teve_reajuste'] = _teve_evento_na_janela(df, reajustes, dias_antes=0, dias_depois=30)
    return df


def vincular_sustentacao_a_inclusoes(inclusoes, sustentacoes):
    df = inclusoes.copy()
    df['teve_sustentacao'] = _teve_evento_na_janela(df, sustentacoes, dias_antes=15, dias_depois=30)
    return df


def tramitacao_dois_ambientes(inclusoes):
    df = inclusoes.copy()
    tramitacao_processo = (
        df.groupby('incidente')['ambiente']
        .agg(lambda x: set(x))
        .apply(
            lambda amb:
            'Ambos os ambientes' if {'Plenário Virtual', 'Plenário Físico'} <= amb
            else ('Só Virtual' if 'Plenário Virtual' in amb else 'Só Físico')
        )
        .reset_index(name='tramitacao')
    )
    df = df.drop(columns=[
        col for col in df.columns
        if col.startswith('tramitacao') or col == 'tramitou_ambos'
    ], errors='ignore')
    df = df.merge(tramitacao_processo, on='incidente', how='left')
    df['tramitou_ambos'] = df['tramitacao'] == 'Ambos os ambientes'
    return df


def exportar_reajustes_de_voto(inclusoes, reajustes):
    reaj_export = reajustes.merge(
        inclusoes[['incidente', 'nome_processo', 'relator']].drop_duplicates('incidente'),
        on='incidente', how='left'
    )
    return (
        reaj_export[[
            'incidente', 'nome_processo', 'classe', 'relator',
            'and_data', 'and_nome', 'and_complemento'
        ]]
        .sort_values(['classe', 'nome_processo', 'and_data'])
        .reset_index(drop=True)
    )


def run_pipeline(processed_dir, interim_dir):
    processed_dir = Path(processed_dir)
    interim_dir = Path(interim_dir)

    dim_andamentos = pd.read_parquet(interim_dir / 'dim_andamentos.parquet')
    inclusoes = pd.read_parquet(processed_dir / 'inclusoes_em_pauta.parquet')

    reajustes = detectar_reajuste_de_voto(dim_andamentos)
    reajustes_export = exportar_reajustes_de_voto(inclusoes, reajustes)
    interim_dir.mkdir(parents=True, exist_ok=True)
    reajustes_export.to_parquet(interim_dir / 'reajustes_de_voto.parquet', index=False)

    inclusoes = vincular_reajuste_a_inclusoes(inclusoes, reajustes)

    inclusoes = tramitacao_dois_ambientes(inclusoes)
    inclusoes.to_parquet(processed_dir / 'tramitacoes.parquet', index=False)

    sustentacoes = verificar_sustentacao_oral(dim_andamentos)
    inclusoes = vincular_sustentacao_a_inclusoes(inclusoes, sustentacoes)
    inclusoes.to_parquet(processed_dir / 'sustentacao_oral.parquet', index=False)

    return reajustes_export, inclusoes


def _selfcheck():
    dim_andamentos = pd.DataFrame([
        {'incidente': 1, 'classe': 'ADI', 'and_index': 0, 'and_data': '01/02/2021',
         'and_nome': 'Decisão', 'and_complemento': 'O Relator, Ministro Fulano, teve seu voto ora reajustado.'},
        {'incidente': 1, 'classe': 'ADI', 'and_index': 1, 'and_data': '02/02/2021',
         'and_nome': 'Sustentação Oral', 'and_complemento': 'Realizada sustentação oral pelo advogado.'},
        {'incidente': 2, 'classe': 'ADPF', 'and_index': 0, 'and_data': '03/02/2021',
         'and_nome': 'Decisão', 'and_complemento': 'Ministro Fulano solicitou reajuste de vencimentos dos servidores.'},
        {'incidente': 2, 'classe': 'ADPF', 'and_index': 1, 'and_data': '04/02/2021',
         'and_nome': 'Decisão', 'and_complemento': 'Indeferida a sustentação oral requerida.'},
    ])

    reajustes = detectar_reajuste_de_voto(dim_andamentos)
    assert set(reajustes['incidente']) == {1}, 'falso positivo/negativo em detecção de reajuste'

    sustentacoes = verificar_sustentacao_oral(dim_andamentos)
    assert set(sustentacoes['incidente']) == {1}, 'sustentação negada não deveria contar'

    inclusoes = pd.DataFrame([
        {'incidente': 1, 'nome_processo': 'ADI 1', 'classe': 'ADI', 'relator': 'Fulano',
         'ambiente': 'Plenário Virtual', 'data_inclusao_dt': pd.Timestamp('2021-01-25')},
        {'incidente': 1, 'nome_processo': 'ADI 1', 'classe': 'ADI', 'relator': 'Fulano',
         'ambiente': 'Plenário Físico', 'data_inclusao_dt': pd.Timestamp('2021-01-25')},
        {'incidente': 2, 'nome_processo': 'ADPF 1', 'classe': 'ADPF', 'relator': 'Fulano',
         'ambiente': 'Plenário Virtual', 'data_inclusao_dt': pd.Timestamp('2021-01-25')},
    ])

    inclusoes = vincular_reajuste_a_inclusoes(inclusoes, reajustes)
    assert inclusoes.loc[inclusoes['incidente'] == 1, 'teve_reajuste'].all()
    assert not inclusoes.loc[inclusoes['incidente'] == 2, 'teve_reajuste'].any()

    inclusoes = tramitacao_dois_ambientes(inclusoes)
    assert (inclusoes.loc[inclusoes['incidente'] == 1, 'tramitacao'] == 'Ambos os ambientes').all()
    assert (inclusoes.loc[inclusoes['incidente'] == 2, 'tramitacao'] == 'Só Virtual').all()
    assert inclusoes.loc[inclusoes['incidente'] == 1, 'tramitou_ambos'].all()

    inclusoes = vincular_sustentacao_a_inclusoes(inclusoes, sustentacoes)
    assert inclusoes.loc[inclusoes['incidente'] == 1, 'teve_sustentacao'].all()
    assert not inclusoes.loc[inclusoes['incidente'] == 2, 'teve_sustentacao'].any()

    print('reajustes.py selfcheck: OK')


if __name__ == '__main__':
    _selfcheck()
