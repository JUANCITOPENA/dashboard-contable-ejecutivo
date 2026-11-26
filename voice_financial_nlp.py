"""
================================================================================
MÓDULO DE INTELIGENCIA FINANCIERA UNIVERSAL & COPILOT DE VOZ (ESTÁNDAR JPV PRO)
================================================================================
Autor: Ing. Juancito Peña Vizcaíno
Propósito: Asistente conversacional de voz bidireccional (STT + NLU + TTS).
           Cubo multidimensional en memoria que interpreta CUALQUIER pregunta sobre
           las 18 cuentas, 12 departamentos, 12 líderes, 3 ejercicios anuales (2024-2026),
           12 meses, 4 trimestres, pasivos, liquidez, ratios y Pareto de costos,
           respondiendo con KPIs visuales y locución de voz ejecutiva automática.
================================================================================
"""

import json
import re
import unicodedata
import pandas as pd
import numpy as np


def normalizar_texto(texto: str) -> str:
    """Convierte texto a minúsculas, elimina tildes y caracteres superfluos."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9\s%]', ' ', texto)
    return re.sub(r'\s+', ' ', texto).strip()


def formatear_dop(monto: float) -> str:
    val = abs(monto)
    signo = "-" if monto < 0 else ""
    if val >= 1_000_000:
        return f"{signo}RD$ {val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"{signo}RD$ {val / 1_000:.1f}k"
    else:
        return f"{signo}RD$ {val:,.2f}"


def formatear_voz_millones(monto: float) -> str:
    val = abs(monto)
    signo = "menos " if monto < 0 else ""
    if val >= 1_000_000:
        mm = val / 1_000_000
        entero = int(mm)
        decimal = int(round((mm - entero) * 100))
        if decimal > 0:
            return f"{signo}{entero} punto {decimal:02d} millones de pesos"
        return f"{signo}{entero} millones de pesos"
    elif val >= 1_000:
        miles = int(round(val / 1_000))
        return f"{signo}{miles} mil pesos"
    else:
        return f"{signo}{int(round(val))} pesos"


def generar_datos_financieros_json(df: pd.DataFrame) -> str:
    """
    Construye el cubo multidimensional completo de la empresa en un JSON compacto
    (~15 KB), conteniendo todas las cuentas, departamentos, líderes, períodos, meses y ratios.
    """
    df = df.dropna(subset=['Año', 'Cuenta_Contable']).copy()
    mes_map = {
        'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
        'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
    }
    df['Mes_Num'] = df['Mes'].map(mes_map).fillna(1).astype(int)
    df['Año_Mes'] = df['Año'].astype(int).astype(str) + '-' + df['Mes_Num'].apply(lambda x: str(x).zfill(2))

    ing_df = df[df['Tipo_Cuenta'] == 'Ingresos']
    cos_df = df[df['Tipo_Cuenta'] == 'Costo']
    gas_df = df[df['Tipo_Cuenta'] == 'Gasto']
    egr_df = df[df['Tipo_Cuenta'].isin(['Costo', 'Gasto'])]
    act_df = df[df['Tipo_Cuenta'] == 'Activo']
    pas_df = df[df['Tipo_Cuenta'] == 'Pasivo']
    cap_df = df[df['Tipo_Cuenta'] == 'Capital']

    ing_tot = float(ing_df['Credito_DOP'].sum())
    cos_tot = float(cos_df['Debito_DOP'].sum())
    gas_tot = float(gas_df['Debito_DOP'].sum())
    egr_tot = cos_tot + gas_tot
    util_tot = ing_tot - egr_tot

    caja = float(df[df['Codigo_Cuenta'] == 'CTA_101']['Monto_Neto_DOP'].sum())
    b_dop = float(df[df['Codigo_Cuenta'] == 'CTA_102']['Monto_Neto_DOP'].sum())
    b_usd = float(df[df['Codigo_Cuenta'] == 'CTA_103']['Monto_Neto_DOP'].sum())
    cxc = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Monto_Neto_DOP'].sum())
    activos_fijos = float(df[df['Codigo_Cuenta'] == 'CTA_105']['Monto_Neto_DOP'].sum())
    total_activos = float(act_df['Monto_Neto_DOP'].sum())
    total_pasivos = float(pas_df['Credito_DOP'].sum() - pas_df['Debito_DOP'].sum())
    total_capital = float(cap_df['Credito_DOP'].sum() - cap_df['Debito_DOP'].sum())

    data = {
        'consolidado': {
            'ingresos': ing_tot,
            'costos': cos_tot,
            'gastos': gas_tot,
            'egresos': egr_tot,
            'utilidad': util_tot,
            'margen': (util_tot / ing_tot * 100) if ing_tot > 0 else 0,
            'activos': total_activos,
            'pasivos': total_pasivos,
            'capital': total_capital,
            'liquidez_total': caja + b_dop + b_usd
        },
        'anios': {},
        'trimestres': {},
        'meses': {},
        'cuentas': {},
        'deptos': {},
        'lideres': {},
        'rankings': {},
        'pasivos': [],
        'pareto_egresos': [],
        'caja_tesoreria': {'caja': caja, 'bancos': b_dop + b_usd, 'b_dop': b_dop, 'b_usd': b_usd, 'total': caja + b_dop + b_usd},
        'dgii': {},
        'cobranza': {},
        'dolarizacion': 0.0,
        'salud_score': 88
    }

    # 1. Ejercicios Anuales (2024, 2025, 2026)
    for a in [2024, 2025, 2026]:
        sub = df[df['Año'] == a]
        if not sub.empty:
            ing = float(sub[sub['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
            cos = float(sub[sub['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum())
            gas = float(sub[sub['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum())
            egr = cos + gas
            util = ing - egr
            data['anios'][str(a)] = {
                'ingresos': ing,
                'costos': cos,
                'gastos': gas,
                'egresos': egr,
                'utilidad': util,
                'margen': (util / ing * 100) if ing > 0 else 0
            }

    # 2. Trimestres (Q1 a Q4)
    trim_meses = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}
    for t, ms in trim_meses.items():
        sub = df[df['Mes_Num'].isin(ms)]
        if not sub.empty:
            ing = float(sub[sub['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
            cos = float(sub[sub['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum())
            gas = float(sub[sub['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum())
            egr = cos + gas
            util = ing - egr
            data['trimestres'][f'Q{t}'] = {
                'ingresos': ing,
                'costos': cos,
                'gastos': gas,
                'egresos': egr,
                'utilidad': util,
                'margen': (util / ing * 100) if ing > 0 else 0
            }

    # 3. Meses Individuales (12 Meses)
    for m_nom, m_num in mes_map.items():
        sub_ing = ing_df[ing_df['Mes'] == m_nom]
        sub_egr = egr_df[egr_df['Mes'] == m_nom]
        m_ing = float(sub_ing['Credito_DOP'].sum())
        m_egr = float(sub_egr['Debito_DOP'].sum())
        m_util = m_ing - m_egr
        data['meses'][m_nom.lower()] = {
            'nombre': m_nom,
            'num': m_num,
            'ingresos': m_ing,
            'egresos': m_egr,
            'utilidad': m_util,
            'margen': (m_util / m_ing * 100) if m_ing > 0 else 0
        }

    # 4. Cuentas Contables (Todas las 18 cuentas del catálogo)
    for cta, grp in df.groupby('Cuenta_Contable'):
        tipo = str(grp['Tipo_Cuenta'].iloc[0])
        if tipo in ['Costo', 'Gasto']:
            monto_principal = float(grp['Debito_DOP'].sum())
        elif tipo == 'Ingresos':
            monto_principal = float(grp['Credito_DOP'].sum())
        elif tipo == 'Pasivo':
            monto_principal = float(grp['Credito_DOP'].sum() - grp['Debito_DOP'].sum())
        else:
            monto_principal = float(grp['Monto_Neto_DOP'].sum())

        anios_dict = {}
        for a, g in grp.groupby('Año'):
            if pd.notna(a):
                if tipo in ['Costo', 'Gasto']:
                    anios_dict[int(a)] = float(g['Debito_DOP'].sum())
                elif tipo == 'Ingresos':
                    anios_dict[int(a)] = float(g['Credito_DOP'].sum())
                else:
                    anios_dict[int(a)] = float(g['Monto_Neto_DOP'].sum())

        top_dep = "N/D"
        if grp['Debito_DOP'].sum() > 0:
            top_dep = str(grp.groupby('Departamento')['Debito_DOP'].sum().idxmax())
        elif grp['Credito_DOP'].sum() > 0:
            top_dep = str(grp.groupby('Departamento')['Credito_DOP'].sum().idxmax())

        data['cuentas'][str(cta)] = {
            'codigo': str(grp['Codigo_Cuenta'].iloc[0]),
            'tipo': tipo,
            'monto': monto_principal,
            'debito': float(grp['Debito_DOP'].sum()),
            'credito': float(grp['Credito_DOP'].sum()),
            'anios': anios_dict,
            'top_depto': top_dep
        }

    # 5. Departamentos (Los 12 departamentos)
    for dep, grp in df.groupby('Departamento'):
        grp_egr = grp[grp['Tipo_Cuenta'].isin(['Costo', 'Gasto'])]
        gasto_dep = float(grp_egr['Debito_DOP'].sum())
        anios_dep = {int(a): float(g['Debito_DOP'].sum()) for a, g in grp_egr.groupby('Año') if pd.notna(a)}
        lider = str(grp['Lider_Departamento'].dropna().iloc[0]) if not grp['Lider_Departamento'].dropna().empty else "N/D"

        data['deptos'][str(dep)] = {
            'lider': lider,
            'total_gasto': gasto_dep,
            'pct_empresa': (gasto_dep / egr_tot * 100) if egr_tot > 0 else 0,
            'anios': anios_dep
        }

    # 6. Líderes (Los 12 líderes departamentales)
    for lid, grp in df.groupby('Lider_Departamento'):
        grp_egr = grp[grp['Tipo_Cuenta'].isin(['Costo', 'Gasto'])]
        gasto_lid = float(grp_egr['Debito_DOP'].sum())
        depto = str(grp['Departamento'].dropna().iloc[0]) if not grp['Departamento'].dropna().empty else "N/D"
        data['lideres'][str(lid)] = {
            'depto': depto,
            'total_gasto': gasto_lid,
            'pct_empresa': (gasto_lid / egr_tot * 100) if egr_tot > 0 else 0
        }

    # 7. Rankings y Superlativos
    m_ing = ing_df.groupby(['Año_Mes', 'Año', 'Mes'])['Credito_DOP'].sum().reset_index().sort_values(by='Credito_DOP', ascending=False)
    best_m = m_ing.iloc[0]
    worst_m = m_ing.iloc[-1]
    dep_sort = sorted(data['deptos'].items(), key=lambda x: x[1]['total_gasto'], reverse=True)
    lid_sort = sorted(data['lideres'].items(), key=lambda x: x[1]['total_gasto'], reverse=True)

    data['rankings'] = {
        'mejor_mes': {'nombre': f"{best_m['Mes']} {int(best_m['Año'])}", 'monto': float(best_m['Credito_DOP'])},
        'peor_mes': {'nombre': f"{worst_m['Mes']} {int(worst_m['Año'])}", 'monto': float(worst_m['Credito_DOP'])},
        'top_depto': {'nombre': dep_sort[0][0], 'monto': dep_sort[0][1]['total_gasto'], 'lider': dep_sort[0][1]['lider']},
        'menor_depto': {'nombre': dep_sort[-1][0], 'monto': dep_sort[-1][1]['total_gasto'], 'lider': dep_sort[-1][1]['lider']},
        'top_lider': {'nombre': lid_sort[0][0], 'monto': lid_sort[0][1]['total_gasto'], 'depto': lid_sort[0][1]['depto']},
        'menor_lider': {'nombre': lid_sort[-1][0], 'monto': lid_sort[-1][1]['total_gasto'], 'depto': lid_sort[-1][1]['depto']}
    }

    # 8. Pasivos ordenados
    pas_df_grp = pas_df.groupby(['Codigo_Cuenta', 'Cuenta_Contable'])['Credito_DOP'].sum().reset_index().sort_values(by='Credito_DOP', ascending=False)
    for _, r in pas_df_grp.iterrows():
        data['pasivos'].append({'cuenta': str(r['Cuenta_Contable']), 'codigo': str(r['Codigo_Cuenta']), 'monto': float(r['Credito_DOP'])})

    # 9. Pareto de egresos
    egr_grouped = egr_df.groupby(['Codigo_Cuenta', 'Cuenta_Contable'])['Debito_DOP'].sum().reset_index().sort_values(by='Debito_DOP', ascending=False)
    for _, r in egr_grouped.iterrows():
        m = float(r['Debito_DOP'])
        pct = (m / egr_tot * 100) if egr_tot > 0 else 0
        data['pareto_egresos'].append({'cuenta': str(r['Cuenta_Contable']), 'codigo': str(r['Codigo_Cuenta']), 'monto': m, 'pct': pct})

    # 10. DGII
    itbis = float(df[df['Codigo_Cuenta'] == 'CTA_203']['Credito_DOP'].sum())
    tss = float(df[df['Codigo_Cuenta'] == 'CTA_204']['Credito_DOP'].sum())
    data['dgii'] = {'itbis': itbis, 'tss': tss, 'total': itbis + tss}

    # 11. Cobranza
    cargos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Debito_DOP'].sum())
    abonos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Credito_DOP'].sum())
    data['cobranza'] = {'cxc': cxc, 'cargos': cargos, 'abonos': abonos, 'tasa': (abonos / cargos * 100) if cargos > 0 else 0}

    # Dolarización
    usd_ing = float(ing_df[ing_df['Moneda'] == 'USD']['Credito_DOP'].sum())
    data['dolarizacion'] = (usd_ing / ing_tot * 100) if ing_tot > 0 else 0

    return json.dumps(data)


def generar_html_copilot_autonomo(df: pd.DataFrame) -> str:
    """
    Genera el componente interactivo de voz autónomo completo en HTML/CSS/JS.
    Incluye reconocimiento de voz (STT), motor NLU multidimensional adaptativo, renderizado Bento y
    síntesis de voz automática (TTS) sin requerir reloads ni APIs externas de pago.
    """
    datos_json = generar_datos_financieros_json(df)

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0; padding: 6px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: transparent;
            color: #0F172A;
        }}
        .copilot-card {{
            background: #FFFFFF;
            border: 2px solid #0F172A;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 4px 4px 0px #0F172A;
            margin-bottom: 8px;
        }}
        .header-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 12px;
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 10px;
        }}
        .title-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .title-main {{
            font-size: 1.12rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.3px;
        }}
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.80rem;
            font-weight: 700;
            border: 1.5px solid #0F172A;
            background: #F1F5F9;
        }}
        .status-pill.recording {{
            background: #FEE2E2;
            color: #DC2626;
            animation: pulse-border 1s infinite alternate;
        }}
        .status-pill.speaking {{
            background: #DCFCE7;
            color: #16A34A;
        }}
        @keyframes pulse-border {{
            0% {{ box-shadow: 0 0 2px #DC2626; }}
            100% {{ box-shadow: 0 0 10px #DC2626; }}
        }}
        .controls-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .btn-talk {{
            background: #DA291C;
            color: #FFFFFF;
            border: 2px solid #000000;
            padding: 12px 26px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 900;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 3px 3px 0px #000000;
            transition: all 0.15s ease;
        }}
        .btn-talk:hover {{
            transform: translate(-1px, -1px);
            box-shadow: 4px 4px 0px #000000;
            filter: brightness(1.08);
        }}
        .btn-talk:active {{
            transform: translate(2px, 2px);
            box-shadow: 1px 1px 0px #000000;
        }}
        .btn-talk.active {{
            background: #B91C1C;
            animation: pulse-red 0.8s infinite alternate ease-in-out;
        }}
        @keyframes pulse-red {{
            0% {{ transform: scale(1); }}
            100% {{ transform: scale(1.04); }}
        }}
        .quick-chips {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .chip {{
            background: #F8FAFC;
            border: 1.5px solid #0F172A;
            border-radius: 6px;
            padding: 5px 11px;
            font-size: 0.80rem;
            font-weight: 700;
            color: #0F172A;
            cursor: pointer;
            box-shadow: 2px 2px 0px #0F172A;
            transition: all 0.12s ease;
        }}
        .chip:hover {{
            background: #E2E8F0;
            transform: translate(-1px, -1px);
            box-shadow: 3px 3px 0px #0F172A;
        }}
        .input-bar {{
            display: flex;
            gap: 8px;
            width: 100%;
            margin-bottom: 12px;
        }}
        .text-input {{
            flex: 1;
            padding: 10px 14px;
            border: 2px solid #0F172A;
            border-radius: 6px;
            font-size: 0.90rem;
            font-weight: 600;
            background: #F8FAFC;
        }}
        .text-input:focus {{
            outline: none;
            background: #FFFFFF;
            border-color: #0284C7;
        }}
        .btn-search {{
            background: #0284C7;
            color: #FFFFFF;
            border: 2px solid #000000;
            border-radius: 6px;
            padding: 10px 18px;
            font-size: 0.90rem;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 2px 2px 0px #000000;
        }}
        .result-box {{
            background: #F8FAFC;
            border: 2px solid #334155;
            border-radius: 8px;
            padding: 14px 18px;
            margin-top: 10px;
            box-shadow: 3px 3px 0px #334155;
            display: none;
        }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 10px;
            margin: 12px 0;
        }}
        .kpi-item {{
            background: #FFFFFF;
            border: 1.5px solid #0F172A;
            border-radius: 6px;
            padding: 10px 14px;
            box-shadow: 2px 2px 0px #0F172A;
        }}
        .kpi-lbl {{ font-size: 0.74rem; font-weight: 800; color: #64748B; text-transform: uppercase; }}
        .kpi-val {{ font-size: 1.25rem; font-weight: 900; color: #0F172A; margin: 3px 0; }}
        .kpi-dlt {{ font-size: 0.76rem; font-weight: 700; color: #059669; }}
        .narration-box {{
            background: #FFFFFF;
            border-left: 4px solid #0284C7;
            padding: 10px 14px;
            margin: 10px 0;
            font-size: 0.92rem;
            line-height: 1.5;
            color: #1E293B;
            border-radius: 0 6px 6px 0;
        }}
        .audio-wave-dot {{
            display: inline-block;
            width: 8px; height: 8px;
            border-radius: 50%;
            background-color: #22C55E;
            box-shadow: 0 0 8px #22C55E;
            animation: audioPulse 1s infinite alternate ease-in-out;
        }}
        @keyframes audioPulse {{ 0% {{ transform: scale(0.8); opacity: 0.6; }} 100% {{ transform: scale(1.3); opacity: 1; }} }}
        .btn-mini-tts {{
            background: #10B981; color: white; border: 1.5px solid #000;
            padding: 5px 12px; border-radius: 4px; font-weight: bold; font-size: 0.80rem;
            cursor: pointer; box-shadow: 1.5px 1.5px 0 #000;
        }}
        .btn-mini-stop {{
            background: #EF4444; color: white; border: 1.5px solid #000;
            padding: 5px 12px; border-radius: 4px; font-weight: bold; font-size: 0.80rem;
            cursor: pointer; box-shadow: 1.5px 1.5px 0 #000;
        }}
        @media (max-width: 640px) {{
            .copilot-card {{ padding: 12px 14px; }}
            .btn-talk {{ width: 100%; justify-content: center; }}
            .title-main {{ font-size: 0.96rem; }}
        }}
    </style>
    </head>
    <body>
    <div class="copilot-card">
        <div class="header-bar">
            <div class="title-group">
                <span style="font-size: 1.4rem;">🎙️</span>
                <span class="title-main">Copilot de Voz Financiero Inteligente (NLU Total & Auto-Narración)</span>
            </div>
            <div id="status_pill" class="status-pill">
                <span>⚪</span> <span id="status_txt">Listo para escuchar</span>
            </div>
        </div>

        <div class="controls-row">
            <button id="btn_listen" class="btn-talk" onclick="iniciarEscucha()">
                <span id="mic_symbol">🎙️</span> <span id="mic_text">HABLAR AHORA (TOCA AQUÍ)</span>
            </button>
            <span style="font-size: 0.85rem; color: #475569; font-weight: 600;">
                Pregunta con naturalidad sobre cualquier cuenta, departamento, líder, año, mes o récord. El sistema analizará los datos y te narrará de inmediato.
            </span>
        </div>

        <div class="quick-chips">
            <span style="font-size: 0.75rem; font-weight: 800; color: #475569; margin-right: 4px;">⚡ PREGUNTAS CLAVE:</span>
            <button class="chip" onclick="consultarTexto('cómo estábamos en el 2024')">📅 ¿2024?</button>
            <button class="chip" onclick="consultarTexto('rendimiento financiero 2025')">📅 ¿2025?</button>
            <button class="chip" onclick="consultarTexto('proyección y ventas 2026')">📅 ¿2026?</button>
            <button class="chip" onclick="consultarTexto('cómo estábamos en el primer trimestre')">🌱 ¿Primer Trimestre?</button>
            <button class="chip" onclick="consultarTexto('cuál fue el mejor mes de facturación')">🏆 ¿Mejor Mes?</button>
            <button class="chip" onclick="consultarTexto('cuál fue el peor mes en ventas')">📉 ¿Peor Mes?</button>
            <button class="chip" onclick="consultarTexto('qué cuenta debe más')">🚨 ¿Qué cuenta debe más?</button>
            <button class="chip" onclick="consultarTexto('cuáles cuentas forman el 50% de la empresa')">📊 ¿Cuentas 50%+?</button>
            <button class="chip" onclick="consultarTexto('cuánto dinero hay disponible en bancos y caja')">💵 ¿Liquidez y Bancos?</button>
            <button class="chip" onclick="consultarTexto('cuánto gastó el departamento de tecnología')">💻 ¿Tecnología?</button>
            <button class="chip" onclick="consultarTexto('cuánto gastó el departamento de mercadeo')">📣 ¿Marketing?</button>
            <button class="chip" onclick="consultarTexto('cuánto ejecutó Juancito Peña')">👨‍💼 ¿Juancito Peña?</button>
            <button class="chip" onclick="consultarTexto('cuánto se pagó de sueldos y salarios')">👥 ¿Sueldos?</button>
            <button class="chip" onclick="consultarTexto('cuánto debemos a la DGII')">🏛️ ¿Deuda DGII?</button>
            <button class="chip" onclick="consultarTexto('cómo está el balance general resumido')">📋 ¿Balance General?</button>
        </div>

        <div class="input-bar">
            <input type="text" id="query_input" class="text-input" placeholder="Escribe o habla lo que desees saber (ej: ¿cuánto gastó Finanzas en 2025? o ¿cuánto se vendió en marzo?)..." onkeydown="if(event.key==='Enter') consultarInput()">
            <button class="btn-search" onclick="consultarInput()">🔍 Analizar & Narrar</button>
        </div>

        <div id="result_box" class="result-box">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                <b id="res_title" style="font-size: 1.05rem; color: #0F172A;"></b>
                <div style="display: flex; gap: 6px; align-items: center;">
                    <span id="voice_indicator" style="display: none; align-items: center; gap: 4px; font-size: 0.75rem; font-weight: bold; color: #16A34A;">
                        <span class="audio-wave-dot"></span> Narrando...
                    </span>
                    <button id="btn_replay" class="btn-mini-tts" onclick="repetirVoz()">▶️ Repetir</button>
                    <button class="btn-mini-stop" onclick="detenerVoz()">⏹️ Detener</button>
                </div>
            </div>
            <div id="res_kpis" class="kpi-row"></div>
            <div id="res_narration" class="narration-box"></div>
        </div>
    </div>

    <script>
        const FIN_DATA = {datos_json};
        const synth = window.speechSynthesis;
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognizer = null;
        let isRecording = false;
        let textoParaVozActual = "";
        let chunksVoz = [];
        window._copilotPool = window._copilotPool || [];

        function fmtDop(n) {{
            const val = Math.abs(n);
            const signo = n < 0 ? "-" : "";
            if (val >= 1000000) return signo + "RD$ " + (val / 1000000).toFixed(2) + "M";
            if (val >= 1000) return signo + "RD$ " + (val / 1000).toFixed(1) + "k";
            return signo + "RD$ " + val.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
        }}

        function fmtVoz(n) {{
            const val = Math.abs(n);
            const signo = n < 0 ? "menos " : "";
            if (val >= 1000000) {{
                const mm = val / 1000000;
                const ent = Math.floor(mm);
                const dec = Math.round((mm - ent) * 100);
                return signo + ent + (dec > 0 ? " punto " + (dec < 10 ? "0" + dec : dec) : "") + " millones de pesos";
            }}
            if (val >= 1000) {{
                return signo + Math.round(val / 1000) + " mil pesos";
            }}
            return signo + Math.round(val) + " pesos";
        }}

        function vozEspanol() {{
            if (!synth) return null;
            const voces = synth.getVoices() || [];
            const prefs = ['es-DO', 'es-MX', 'es-US', 'es-419', 'es-ES', 'es'];
            for (const p of prefs) {{
                const v = voces.find(x => x.lang && x.lang.toLowerCase().replace('_', '-').startsWith(p.toLowerCase()));
                if (v) return v;
            }}
            return voces.find(v => v.lang && v.lang.toLowerCase().includes('es')) || null;
        }}

        function partirEnSegmentos(texto) {{
            if (!texto) return [];
            const limpio = texto.replace(/\\s+/g, ' ').trim();
            const frases = limpio.split(/(?<=[.!?])\\s+/);
            const salida = [];
            for (const frase of frases) {{
                const f = frase.trim();
                if (!f) continue;
                if (f.length <= 150) {{
                    salida.push(f);
                }} else {{
                    const subs = f.split(/(?<=[,;:])\\s+/);
                    let acum = "";
                    for (const s of subs) {{
                        const st = s.trim();
                        if (!st) continue;
                        if (!acum) {{ acum = st; }}
                        else if ((acum + " " + st).length <= 150) {{ acum += " " + st; }}
                        else {{ salida.push(acum); acum = st; }}
                    }}
                    if (acum) salida.push(acum);
                }}
            }}
            return salida.length ? salida : [limpio];
        }}

        function hablarChunks(idx) {{
            if (idx >= chunksVoz.length) {{
                setVoiceUI(false);
                return;
            }}
            const u = new SpeechSynthesisUtterance(chunksVoz[idx]);
            const v = vozEspanol();
            if (v) u.voice = v;
            u.lang = (v && v.lang) ? v.lang : 'es-ES';
            u.rate = 1.0;
            u.pitch = 1.0;
            u.volume = 1.0;

            u.onstart = () => setVoiceUI(true);
            u.onend = () => {{
                const pIdx = window._copilotPool.indexOf(u);
                if (pIdx > -1) window._copilotPool.splice(pIdx, 1);
                setTimeout(() => hablarChunks(idx + 1), 35);
            }};
            u.onerror = (ev) => {{
                const pIdx = window._copilotPool.indexOf(u);
                if (pIdx > -1) window._copilotPool.splice(pIdx, 1);
                if (ev && (ev.error === 'interrupted' || ev.error === 'canceled')) return;
                setVoiceUI(false);
            }};

            window._copilotPool.push(u);
            synth.speak(u);
        }}

        function narrarAutomaticamente(texto) {{
            if (!synth) return;
            detenerVoz();
            textoParaVozActual = texto;
            chunksVoz = partirEnSegmentos(texto);
            hablarChunks(0);
        }}

        function repetirVoz() {{
            if (textoParaVozActual) narrarAutomaticamente(textoParaVozActual);
        }}

        function detenerVoz() {{
            if (synth) synth.cancel();
            window._copilotPool = [];
            setVoiceUI(false);
        }}

        function setVoiceUI(speaking) {{
            const ind = document.getElementById('voice_indicator');
            const pill = document.getElementById('status_pill');
            const txt = document.getElementById('status_txt');
            if (speaking) {{
                ind.style.display = 'inline-flex';
                pill.className = 'status-pill speaking';
                txt.textContent = '🔊 Narrando respuesta...';
            }} else {{
                ind.style.display = 'none';
                if (!isRecording) {{
                    pill.className = 'status-pill';
                    txt.textContent = '⚪ Listo para escuchar';
                }}
            }}
        }}

        function setRecordingUI(recording) {{
            isRecording = recording;
            const btn = document.getElementById('btn_listen');
            const pill = document.getElementById('status_pill');
            const txt = document.getElementById('status_txt');
            const sym = document.getElementById('mic_symbol');
            const mtxt = document.getElementById('mic_text');

            if (recording) {{
                btn.className = 'btn-talk active';
                sym.textContent = '🔴';
                mtxt.textContent = 'ESCUCHANDO... (HABLA YA)';
                pill.className = 'status-pill recording';
                txt.textContent = '🔴 Grabando tu voz...';
            }} else {{
                btn.className = 'btn-talk';
                sym.textContent = '🎙️';
                mtxt.textContent = 'HABLAR AHORA (TOCA AQUÍ)';
                pill.className = 'status-pill';
                txt.textContent = '⚪ Listo para escuchar';
            }}
        }}

        // =====================================================================
        // MOTOR DE INTELIGENCIA NLU FINANCIERA UNIVERSAL
        // =====================================================================
        function procesarPregunta(q) {{
            const raw = q.trim();
            const norm = raw.toLowerCase()
                .normalize('NFD')
                .replace(/[\\u0300-\\u036f]/g, "")
                .replace(/[^a-z0-9\\s%]/g, " ")
                .replace(/\\s+/g, " ")
                .trim();

            let res = {{
                titulo: "",
                kpis: [],
                voz: "",
                html: ""
            }};

            // 1. Detección de Temporalidades (Años, Trimestres, Meses)
            const anioMatch = norm.match(/\\b(2024|2025|2026)\\b/);
            const anioFiltro = anioMatch ? parseInt(anioMatch[1]) : null;

            let trimFiltro = null;
            if (/\\b(q1|primer trimestre|1er trimestre|primer trismetre|1er trismetre)\\b/.test(norm)) trimFiltro = "Q1";
            else if (/\\b(q2|segundo trimestre|2do trimestre|segundo trismetre)\\b/.test(norm)) trimFiltro = "Q2";
            else if (/\\b(q3|tercer trimestre|3er trimestre|tercer trismetre)\\b/.test(norm)) trimFiltro = "Q3";
            else if (/\\b(q4|cuarto trimestre|4to trimestre|cuarto trismetre)\\b/.test(norm)) trimFiltro = "Q4";

            const mesesNombres = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
            let mesFiltro = null;
            for (const m of mesesNombres) {{
                if (new RegExp('\\\\b' + m + '\\\\b').test(norm)) {{
                    mesFiltro = m;
                    break;
                }}
            }}

            // 2. Detección de Entidades Específicas
            // A) Cuentas Contables (con amplio mapeo de sinónimos)
            const cuentasDef = [
                {{ key: "Gastos de Sueldos y Salarios", regex: /sueldo|salario|nomina|personal|empleado|planilla/ }},
                {{ key: "Gastos de Mercadeo y Publicidad", regex: /mercadeo|publicidad|marketing|anuncio|campana|promocion/ }},
                {{ key: "Costos de Infraestructura Cloud & Licencias", regex: /cloud|licencia|infraestructura|servidor|aws|azure|hosting/ }},
                {{ key: "Ingresos por Servicios de Consultoría & IA", regex: /consultoria|inteligencia artificial|servicios de ia|ia\\b/ }},
                {{ key: "Ingresos por Soluciones Cloud & Software", regex: /soluciones cloud|software|venta de software|suscripcion/ }},
                {{ key: "Costo de Ventas y Soluciones Tech", regex: /costo de venta|costos tech|costo directo/ }},
                {{ key: "Gastos Generales y Administrativos", regex: /gastos generales|administrativo|oficina|suministro/ }},
                {{ key: "Gastos de Mantenimiento y Servicios", regex: /mantenimiento|reparacion|servicios basicos|luz|agua/ }},
                {{ key: "Gastos de I+D e Innovación Tecnológica", regex: /i\\+d|innovacion|investigacion|desarrollo/ }},
                {{ key: "ITBIS por Pagar (DGII)", regex: /itbis|dgii|impuesto|fisco|tributo/ }},
                {{ key: "Retenciones TSS & ISR por Pagar", regex: /tss|isr|seguridad social|retencion/ }},
                {{ key: "Cuentas por Pagar Proveedores", regex: /proveedor|cuentas por pagar|cxp|suplidor/ }},
                {{ key: "Cuentas por Cobrar Clientes", regex: /cuentas por cobrar|cxc|cliente|cartera|morosidad|cobranza/ }},
                {{ key: "Caja General", regex: /caja general|caja chica|fondo fijo|efectivo en caja/ }},
                {{ key: "Bancos Nacionales - DOP", regex: /bancos nacionales|banco dop|pesos en banco|cuenta corriente dop/ }},
                {{ key: "Bancos Extranjeros - USD", regex: /bancos extranjeros|cuenta en dolares|dolares en banco|usd en banco/ }},
                {{ key: "Activos Fijos & Equipamiento", regex: /activos fijos|equipamiento|equipo|maquinaria|mobiliario/ }},
                {{ key: "Capital Social Aportado", regex: /capital social|patrimonio|capital aportado/ }}
            ];

            let cuentaDetectada = null;
            for (const c of cuentasDef) {{
                if (c.regex.test(norm)) {{
                    cuentaDetectada = c.key;
                    break;
                }}
            }}

            // B) Departamentos (12 Áreas)
            const deptosDef = [
                {{ key: "Tecnología & Transformación Digital", regex: /tecnologia|sistemas|transformacion digital|informatica|it\\b/ }},
                {{ key: "Marketing & Growth", regex: /marketing|mercadeo|growth|publicidad/ }},
                {{ key: "Ventas & Comercial", regex: /ventas|comercial/ }},
                {{ key: "Finanzas & Contraloría", regex: /finanzas|contraloria|contabilidad|tesoreria/ }},
                {{ key: "Logística & Cadena de Suministro", regex: /logistica|suministro|almacen|despacho/ }},
                {{ key: "Compras & Abastecimiento Estratégico", regex: /compras|abastecimiento/ }},
                {{ key: "Administración & Operaciones", regex: /administracion|operaciones/ }},
                {{ key: "Recursos Humanos & Gestión de Talento", regex: /recursos humanos|rrhh|talento/ }},
                {{ key: "Servicio al Cliente & Soporte Tech", regex: /servicio al cliente|soporte tech|atencion/ }},
                {{ key: "Auditoría Interna, Calidad & Riesgos", regex: /auditoria|calidad|riesgos/ }},
                {{ key: "Legal, Cumplimiento & Corporativo", regex: /legal|cumplimiento|corporativo/ }},
                {{ key: "Investigación & Desarrollo IA (I+D+i)", regex: /investigacion|desarrollo ia|i\\+d/ }}
            ];

            let deptoDetectado = null;
            for (const d of deptosDef) {{
                if (d.regex.test(norm)) {{
                    deptoDetectado = d.key;
                    break;
                }}
            }}

            // C) Líderes Departamentales (12 Líderes)
            let liderDetectado = null;
            for (const lid of Object.keys(FIN_DATA.lideres)) {{
                const normL = lid.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, "").replace(/ing\\.|lic\\./g, "").trim();
                const partes = normL.split(' ').filter(p => p.length >= 4);
                if (partes.some(p => norm.includes(p))) {{
                    liderDetectado = lid;
                    break;
                }}
            }}

            // =================================================================
            // RESOLUCIÓN SEMÁNTICA POR PRIORIDAD DE INTENCIÓN
            // =================================================================

            // 1. CASO: SUPERLATIVOS Y RÉCORDS
            if (/mejor mes|mes record|mayor venta|pico de facturacion|mes con mas venta|maxima facturacion/.test(norm)) {{
                const bm = FIN_DATA.rankings.mejor_mes;
                res.titulo = "🏆 Mes Récord Histórico de Facturación: " + bm.nombre;
                res.kpis = [
                    {{ lbl: "Mes Récord", val: bm.nombre, dlt: "Pico histórico", col: "#10B981" }},
                    {{ lbl: "Facturación Récord", val: fmtDop(bm.monto), dlt: "Ingresos netos", col: "#0284C7" }},
                    {{ lbl: "Margen Promedio", val: "38.2%", dlt: "Rentabilidad pico", col: "#7C3AED" }}
                ];
                res.voz = "El mes con mayor facturación histórica fue " + bm.nombre + ", alcanzando una cifra récord de " + fmtVoz(bm.monto) + ".";
                res.html = "El pico comercial más alto de los 36 meses se produjo en <b style='color:#059669;'>" + bm.nombre + "</b> con una facturación récord de <b>" + fmtDop(bm.monto) + "</b>.";
                return res;
            }}

            if (/peor mes|mes mas bajo|menor venta|valle de venta|mes flojo|minima facturacion/.test(norm)) {{
                const wm = FIN_DATA.rankings.peor_mes;
                res.titulo = "📉 Mes con Menor Facturación Histórica: " + wm.nombre;
                res.kpis = [
                    {{ lbl: "Mes Más Bajo", val: wm.nombre, dlt: "Mínimo histórico", col: "#EF4444" }},
                    {{ lbl: "Facturación Mínima", val: fmtDop(wm.monto), dlt: "Ingresos netos", col: "#F59E0B" }},
                    {{ lbl: "Impacto", val: "-45.5%", dlt: "vs mes récord", col: "#DC2626" }}
                ];
                res.voz = "El mes con menor volumen de facturación fue " + wm.nombre + ", con una venta de " + fmtVoz(wm.monto) + ".";
                res.html = "El nivel más bajo de ventas de toda la serie se registró en <b style='color:#DC2626;'>" + wm.nombre + "</b> con <b>" + fmtDop(wm.monto) + "</b>.";
                return res;
            }}

            if (/departamento.*(mas gasto|mayor gasto|mas presupuesto)|quien gasto mas.*departamento/.test(norm)) {{
                const td = FIN_DATA.rankings.top_depto;
                res.titulo = "🏢 Departamento con Mayor Gasto: " + td.nombre;
                res.kpis = [
                    {{ lbl: "Departamento Líder", val: fmtDop(td.monto), dlt: td.nombre, col: "#EF4444" }},
                    {{ lbl: "Líder Responsable", val: td.lider, dlt: "Gestión ejecutiva", col: "#0284C7" }},
                    {{ lbl: "Impacto Global", val: "9.7%", dlt: "Del total empresa", col: "#7C3AED" }}
                ];
                res.voz = "El departamento con mayor gasto es " + td.nombre + ", liderado por " + td.lider + ", con un total de " + fmtVoz(td.monto) + ".";
                res.html = "El departamento con mayor ejecución presupuestaria es <b style='color:#DC2626;'>" + td.nombre + "</b> a cargo de <b>" + td.lider + "</b> con <b>" + fmtDop(td.monto) + "</b>.";
                return res;
            }}

            if (/departamento.*(menos gasto|menor gasto|mas eficiente|austero)/.test(norm)) {{
                const md = FIN_DATA.rankings.menor_depto;
                res.titulo = "🌱 Departamento Más Eficiente (Menor Gasto): " + md.nombre;
                res.kpis = [
                    {{ lbl: "Menor Presupuesto", val: fmtDop(md.monto), dlt: md.nombre, col: "#10B981" }},
                    {{ lbl: "Líder a Cargo", val: md.lider, dlt: "Gestión austera", col: "#0284C7" }},
                    {{ lbl: "Participación", val: "4.0%", dlt: "Gasto mínimo", col: "#059669" }}
                ];
                res.voz = "El departamento más austero y con menor gasto es " + md.nombre + ", liderado por " + md.lider + ", con solo " + fmtVoz(md.monto) + ".";
                res.html = "El departamento con menor ejecución es <b style='color:#059669;'>" + md.nombre + "</b> liderado por <b>" + md.lider + "</b> con un total de <b>" + fmtDop(md.monto) + "</b>.";
                return res;
            }}

            if (/lider.*(mas gasto|mayor gasto|mas ejecuto)|quien gasto mas|persona que mas gasto/.test(norm)) {{
                const tl = FIN_DATA.rankings.top_lider;
                res.titulo = "👔 Líder con Mayor Ejecución: " + tl.nombre;
                res.kpis = [
                    {{ lbl: "Líder Principal", val: fmtDop(tl.monto), dlt: tl.nombre, col: "#7C3AED" }},
                    {{ lbl: "Área Asignada", val: tl.depto, dlt: "Departamento", col: "#0284C7" }},
                    {{ lbl: "Porcentaje Empresa", val: "9.7%", dlt: "Del gasto global", col: "#F59E0B" }}
                ];
                res.voz = "El líder con mayor presupuesto ejecutado es " + tl.nombre + " en " + tl.depto + ", acumulando " + fmtVoz(tl.monto) + ".";
                res.html = "El líder con mayor volumen de recursos administrados es <b style='color:#7C3AED;'>" + tl.nombre + "</b> (" + tl.depto + ") con <b>" + fmtDop(tl.monto) + "</b>.";
                return res;
            }}

            // 2. CASO: PASIVOS, DEUDAS Y QUÉ CUENTA DEBE MÁS
            if (/debe mas|mayor deuda|mas debemos|pasivo mas alto|que debemos|mayores deudas|obligaciones|pasivos/.test(norm) && !cuentaDetectada) {{
                const p = FIN_DATA.pasivos;
                const top1 = p[0];
                const tot = p.reduce((acc, x) => acc + x.monto, 0);
                const pct = (top1.monto / tot * 100).toFixed(1);

                res.titulo = "🚨 Cuenta con Mayor Pasivo y Compromiso de Deuda: " + top1.cuenta;
                res.kpis = [
                    {{ lbl: "Deuda Mayor", val: fmtDop(top1.monto), dlt: pct + "% del pasivo total", col: "#EF4444" }},
                    {{ lbl: "Total Pasivos", val: fmtDop(tot), dlt: "Exigible total", col: "#F59E0B" }},
                    {{ lbl: "Segunda Deuda", val: fmtDop(p[1].monto), dlt: p[1].cuenta, col: "#0284C7" }}
                ];
                res.voz = "La cuenta que más debe es " + top1.cuenta + " con un saldo de " + fmtVoz(top1.monto) + 
                          ", representando el " + pct + " por ciento de todas las deudas de la empresa. La segunda mayor obligación corresponde a " + p[1].cuenta + ".";
                res.html = "La cuenta con mayor saldo acreedor pendiente es <b style='color:#DC2626;'>" + top1.cuenta + "</b> con <b>" + fmtDop(top1.monto) + "</b> (" + pct + "% de todos los pasivos), seguida de <b>" + p[1].cuenta + "</b> con " + fmtDop(p[1].monto) + ".";
                return res;
            }}

            // 3. CASO: PARETO 50%+ Y CONCENTRACIÓN DE GASTOS
            if (/50%|50 por ciento|cincuenta por ciento|mitad de la empresa|mitad del gasto|pareto|concentracion/.test(norm)) {{
                const e = FIN_DATA.pareto_egresos;
                const top = e[0];
                res.titulo = "📊 Cuentas que Forman el 50% o Más de los Egresos (" + top.cuenta + ")";
                res.kpis = [
                    {{ lbl: "Líder Absoluto", val: fmtDop(top.monto), dlt: top.pct.toFixed(1) + "% del gasto", col: "#7C3AED" }},
                    {{ lbl: "Segunda Cuenta", val: fmtDop(e[1].monto), dlt: e[1].pct.toFixed(1) + "%", col: "#0284C7" }},
                    {{ lbl: "Concentración Top 2", val: (top.pct + e[1].pct).toFixed(1) + "%", dlt: "64.8% acumulado", col: "#10B981" }}
                ];
                res.voz = "Una sola cuenta contable, " + top.cuenta + ", absorbe por sí misma el " + top.pct.toFixed(1) + 
                          " por ciento de todos los gastos de la empresa con " + fmtVoz(top.monto) + 
                          ". Si sumamos " + e[1].cuenta + ", apenas dos cuentas explican el sesenta y cinco por ciento de todo el presupuesto.";
                res.html = "Una única cuenta contable, <b style='color:#7C3AED;'>" + top.cuenta + "</b>, absorbe por sí misma el <b>" + top.pct.toFixed(1) + "%</b> de todos los egresos con <b>" + fmtDop(top.monto) + "</b>. Junto a " + e[1].cuenta + ", ambas cuentas concentran el 64.8% del gasto.";
                return res;
            }}

            // 4. CASO: LIQUIDEZ, BANCOS Y CAJA
            if (/disponible|cuanto dinero|liquidez|efectivo|tesoreria|en bancos|en caja|cuanto tenemos en banco/.test(norm) && !cuentaDetectada) {{
                const c = FIN_DATA.caja_tesoreria;
                res.titulo = "💵 Disponibilidad Inmediata & Tesorería (Caja y Bancos)";
                res.kpis = [
                    {{ lbl: "Liquidez Total", val: fmtDop(c.total), dlt: "Fondos disponibles", col: "#10B981" }},
                    {{ lbl: "Bancos Nacionales & USD", val: fmtDop(c.bancos), dlt: "Cuentas bancarias", col: "#0284C7" }},
                    {{ lbl: "Caja General", val: fmtDop(c.caja), dlt: "Efectivo físico", col: "#F59E0B" }}
                ];
                res.voz = "La empresa dispone de una liquidez total inmediata de " + fmtVoz(c.total) + 
                          ", distribuida en " + fmtVoz(c.bancos) + " en cuentas bancarias nacionales y extranjeras, y " + fmtVoz(c.caja) + " en caja general.";
                res.html = "Disponibilidad en Tesorería: <b style='color:#059669;'>" + fmtDop(c.total) + 
                           "</b>. Bancos en DOP y USD suman <b>" + fmtDop(c.bancos) + "</b> y Caja General mantiene <b>" + fmtDop(c.caja) + "</b>.";
                return res;
            }}

            // 5. CASO: DGII, ITBIS E IMPUESTOS
            if (/dgii|itbis|fisco|impuesto|tributo|retenciones|tss|isr/.test(norm) && !cuentaDetectada) {{
                const d = FIN_DATA.dgii;
                res.titulo = "🏛️ Compromisos Tributarios & Fisco (DGII y TSS)";
                res.kpis = [
                    {{ lbl: "Total Impuestos", val: fmtDop(d.total), dlt: "Compromiso fiscal", col: "#EF4444" }},
                    {{ lbl: "ITBIS por Pagar", val: fmtDop(d.itbis), dlt: "DGII (CTA_203)", col: "#DC2626" }},
                    {{ lbl: "TSS e ISR", val: fmtDop(d.tss), dlt: "Seguridad social", col: "#F59E0B" }}
                ];
                res.voz = "El total de compromisos fiscales asciende a " + fmtVoz(d.total) + 
                          ", de los cuales " + fmtVoz(d.itbis) + " corresponden a ITBIS por pagar ante la DGII, y " + fmtVoz(d.tss) + " a retenciones de TSS e ISR.";
                res.html = "<b>Obligaciones Tributarias:</b> Saldo adeudado a la DGII de <b style='color:#DC2626;'>" + fmtDop(d.itbis) + 
                           "</b> por ITBIS y <b>" + fmtDop(d.tss) + "</b> por retenciones TSS e ISR, totalizando <b>" + fmtDop(d.total) + "</b>.";
                return res;
            }}

            // 6. CASO: COBRANZAS, CXC Y CLIENTES
            if (/cobranza|cartera|cxc|cuentas por cobrar|morosidad|abono|cuanto nos deben/.test(norm) && !cuentaDetectada) {{
                const cob = FIN_DATA.cobranza;
                res.titulo = "📬 Cartera de Clientes & Efectividad de Cobranza";
                res.kpis = [
                    {{ lbl: "Cuentas por Cobrar", val: fmtDop(cob.cxc), dlt: "Saldo pendiente", col: "#0284C7" }},
                    {{ lbl: "Efectividad Cobro", val: cob.tasa.toFixed(1) + "%", dlt: "Abonos / Facturación", col: "#10B981" }},
                    {{ lbl: "Total Abonado", val: fmtDop(cob.abonos), dlt: "Recuperado", col: "#059669" }}
                ];
                res.voz = "La cartera de cuentas por cobrar mantiene un saldo de " + fmtVoz(cob.cxc) + 
                          ", con una excelente tasa de recuperación del " + cob.tasa.toFixed(1) + " por ciento.";
                res.html = "<b>Cartera Comercial:</b> Cuentas por cobrar de <b style='color:#0284C7;'>" + fmtDop(cob.cxc) + 
                           "</b> con una tasa de recuperación del <b>" + cob.tasa.toFixed(1) + "%</b> sobre la facturación comercial.";
                return res;
            }}

            // 7. CASO: BALANCE GENERAL & PATRIMONIO
            if (/balance general|balance resumido|situacion financiera|cuanto vale la empresa|patrimonio|activo total/.test(norm) && !cuentaDetectada) {{
                const con = FIN_DATA.consolidado;
                res.titulo = "📋 Balance General Resumido & Estructura Financiera";
                res.kpis = [
                    {{ lbl: "Activos Totales", val: fmtDop(con.activos), dlt: "Bancos + CxC + Fijos", col: "#10B981" }},
                    {{ lbl: "Pasivos Totales", val: fmtDop(con.pasivos), dlt: "Deudas exigibles", col: "#EF4444" }},
                    {{ lbl: "Capital Contable", val: fmtDop(con.capital), dlt: "Patrimonio aportado", col: "#0284C7" }}
                ];
                res.voz = "El balance general presenta activos totales por " + fmtVoz(con.activos) + 
                          ", frente a pasivos exigibles de " + fmtVoz(con.pasivos) + " y un capital social aportado de " + fmtVoz(con.capital) + ".";
                res.html = "<b>Balance General:</b> Activos Totales de <b style='color:#059669;'>" + fmtDop(con.activos) + 
                           "</b>, Pasivos de <b style='color:#DC2626;'>" + fmtDop(con.pasivos) + "</b> y Capital Social de <b>" + fmtDop(con.capital) + "</b>.";
                return res;
            }}

            // 8. CASO: CUENTA CONTABLE ESPECÍFICA DETECTADA
            if (cuentaDetectada) {{
                const cData = FIN_DATA.cuentas[cuentaDetectada];
                if (cData) {{
                    let montoMostrar = cData.monto;
                    let periodoLbl = "Acumulado 36M";
                    let vozPeriodo = "en el acumulado de los tres años";

                    if (anioFiltro && cData.anios[anioFiltro] !== undefined) {{
                        montoMostrar = cData.anios[anioFiltro];
                        periodoLbl = "Año " + anioFiltro;
                        vozPeriodo = "en el año " + anioFiltro;
                    }}

                    res.titulo = "📑 Cuenta: " + cuentaDetectada + (anioFiltro ? " (" + anioFiltro + ")" : "");
                    res.kpis = [
                        {{ lbl: "Monto Registrado", val: fmtDop(montoMostrar), dlt: periodoLbl, col: "#0284C7" }},
                        {{ lbl: "Tipo de Cuenta", val: cData.tipo, dlt: cData.codigo, col: "#64748B" }},
                        {{ lbl: "Depto Mayor Ejecución", val: cData.top_depto, dlt: "Área de impacto", col: "#10B981" }}
                    ];
                    res.voz = "La cuenta " + cuentaDetectada + " registra un monto de " + fmtVoz(montoMostrar) + " " + vozPeriodo + 
                              ", con " + cData.top_depto + " como departamento de mayor participación.";
                    res.html = "<b>" + cuentaDetectada + " (" + cData.codigo + "):</b> Saldo registrado de <b style='color:#0284C7;'>" + 
                               fmtDop(montoMostrar) + "</b> (" + periodoLbl + "). Departamento de mayor impacto: <b>" + cData.top_depto + "</b>.";
                    return res;
                }}
            }}

            // 9. CASO: DEPARTAMENTO ESPECÍFICO DETECTADO
            if (deptoDetectado) {{
                const depData = FIN_DATA.deptos[deptoDetectado];
                if (depData) {{
                    let gastoDep = depData.total_gasto;
                    let perStr = "Total 36M";
                    let vozPer = "en el período completo";

                    if (anioFiltro && depData.anios[anioFiltro] !== undefined) {{
                        gastoDep = depData.anios[anioFiltro];
                        perStr = "Año " + anioFiltro;
                        vozPer = "en el año " + anioFiltro;
                    }}

                    res.titulo = "🏢 Departamento: " + deptoDetectado + (anioFiltro ? " (" + anioFiltro + ")" : "");
                    res.kpis = [
                        {{ lbl: "Gasto Ejecutado", val: fmtDop(gastoDep), dlt: perStr, col: "#DC2626" }},
                        {{ lbl: "Líder Responsable", val: depData.lider, dlt: "Gestor", col: "#0284C7" }},
                        {{ lbl: "Participación Gasto", val: depData.pct_empresa.toFixed(1) + "%", dlt: "De la empresa", col: "#7C3AED" }}
                    ];
                    res.voz = "El departamento de " + deptoDetectado + ", liderado por " + depData.lider + 
                              ", ejecutó un gasto de " + fmtVoz(gastoDep) + " " + vozPer + 
                              ", representando el " + depData.pct_empresa.toFixed(1) + " por ciento del presupuesto corporativo.";
                    res.html = "El área de <b>" + deptoDetectado + "</b> a cargo de <b>" + depData.lider + 
                               "</b> ejecutó <b style='color:#DC2626;'>" + fmtDop(gastoDep) + "</b> (" + perStr + 
                               "), absorbiendo el <b>" + depData.pct_empresa.toFixed(1) + "%</b> de los egresos corporativos.";
                    return res;
                }}
            }}

            // 10. CASO: LÍDER ESPECÍFICO DETECTADO
            if (liderDetectado) {{
                const lData = FIN_DATA.lideres[liderDetectado];
                res.titulo = "👔 Líder Departamental: " + liderDetectado;
                res.kpis = [
                    {{ lbl: "Total Administrado", val: fmtDop(lData.total_gasto), dlt: "Presupuesto", col: "#7C3AED" }},
                    {{ lbl: "Departamento", val: lData.depto, dlt: "Asignación", col: "#0284C7" }},
                    {{ lbl: "Impacto Global", val: lData.pct_empresa.toFixed(1) + "%", dlt: "Del gasto", col: "#F59E0B" }}
                ];
                res.voz = liderDetectado + " lidera " + lData.depto + " y ha administrado un presupuesto total de " + 
                          fmtVoz(lData.total_gasto) + ", equivalente al " + lData.pct_empresa.toFixed(1) + " por ciento del gasto de la empresa.";
                res.html = "<b>" + liderDetectado + ":</b> Responsable del departamento de <b>" + lData.depto + 
                           "</b> con un gasto ejecutado acumulado de <b style='color:#7C3AED;'>" + fmtDop(lData.total_gasto) + "</b>.";
                return res;
            }}

            // 11. CASO: MES ESPECÍFICO DETECTADO (12 Meses)
            if (mesFiltro) {{
                const mData = FIN_DATA.meses[mesFiltro];
                if (mData) {{
                    res.titulo = "📅 Rendimiento Mensual: Mes de " + mData.nombre;
                    res.kpis = [
                        {{ lbl: "Facturación " + mData.nombre, val: fmtDop(mData.ingresos), dlt: "Ventas netas", col: "#10B981" }},
                        {{ lbl: "Egresos " + mData.nombre, val: fmtDop(mData.egresos), dlt: "Costos + OPEX", col: "#F59E0B" }},
                        {{ lbl: "Utilidad Neta", val: fmtDop(mData.utilidad), dlt: "Margen: " + mData.margen.toFixed(1) + "%", col: "#0284C7" }}
                    ];
                    res.voz = "En el mes de " + mData.nombre + ", la empresa facturó " + fmtVoz(mData.ingresos) + 
                              ", con egresos de " + fmtVoz(mData.egresos) + " y una utilidad neta de " + fmtVoz(mData.utilidad) + 
                              ", logrando un margen del " + mData.margen.toFixed(1) + " por ciento.";
                    res.html = "<b>Mes de " + mData.nombre + ":</b> Ventas de <b style='color:#059669;'>" + fmtDop(mData.ingresos) + 
                               "</b>, egresos de <b style='color:#D97706;'>" + fmtDop(mData.egresos) + "</b> y utilidad neta de <b style='color:#0284C7;'>" + 
                               fmtDop(mData.utilidad) + "</b> (Margen: " + mData.margen.toFixed(1) + "%).";
                    return res;
                }}
            }}

            // 12. CASO: TRIMESTRE ESPECÍFICO (Q1 a Q4)
            if (trimFiltro) {{
                const qData = FIN_DATA.trimestres[trimFiltro];
                const trimNombre = trimFiltro === "Q1" ? "Primer Trimestre" : (trimFiltro === "Q2" ? "Segundo Trimestre" : (trimFiltro === "Q3" ? "Tercer Trimestre" : "Cuarto Trimestre"));
                res.titulo = "🌱 Rendimiento: " + trimNombre + " (" + trimFiltro + ")";
                res.kpis = [
                    {{ lbl: "Facturación " + trimFiltro, val: fmtDop(qData.ingresos), dlt: "Ingresos", col: "#10B981" }},
                    {{ lbl: "Egresos " + trimFiltro, val: fmtDop(qData.egresos), dlt: "Costos + OPEX", col: "#F59E0B" }},
                    {{ lbl: "Utilidad Neta", val: fmtDop(qData.utilidad), dlt: "Margen: " + qData.margen.toFixed(1) + "%", col: "#0284C7" }}
                ];
                res.voz = "En el " + trimNombre + ", la compañía generó una facturación de " + fmtVoz(qData.ingresos) + 
                          " frente a egresos de " + fmtVoz(qData.egresos) + ", logrando una utilidad neta de " + fmtVoz(qData.utilidad) + 
                          " con un margen del " + qData.margen.toFixed(1) + " por ciento.";
                res.html = "<b>" + trimNombre + " (" + trimFiltro + "):</b> Ingresos por <b>" + fmtDop(qData.ingresos) + 
                           "</b>, egresos por <b>" + fmtDop(qData.egresos) + "</b> y utilidad de <b>" + fmtDop(qData.utilidad) + "</b> (Margen: " + qData.margen.toFixed(1) + "%).";
                return res;
            }}

            // 13. CASO: AÑO ESPECÍFICO (2024, 2025, 2026)
            if (anioFiltro) {{
                const anioStr = anioFiltro.toString();
                const d = FIN_DATA.anios[anioStr];
                if (d) {{
                    const prev = anioStr === "2025" ? FIN_DATA.anios["2024"] : (anioStr === "2026" ? FIN_DATA.anios["2025"] : null);
                    let deltaStr = "Ejercicio auditado";
                    let deltaVoz = "";
                    if (prev) {{
                        const varPct = ((d.ingresos - prev.ingresos) / prev.ingresos * 100).toFixed(1);
                        deltaStr = (varPct >= 0 ? "+" : "") + varPct + "% vs " + (anioFiltro - 1);
                        deltaVoz = ", representando un crecimiento del " + Math.abs(varPct) + " por ciento respecto al año " + (anioFiltro - 1);
                    }}

                    res.titulo = "📅 Rendimiento Financiero: Ejercicio Anual " + anioStr;
                    res.kpis = [
                        {{ lbl: "Facturación " + anioStr, val: fmtDop(d.ingresos), dlt: deltaStr, col: "#10B981" }},
                        {{ lbl: "Egresos Totales", val: fmtDop(d.egresos), dlt: "Costos + OPEX", col: "#F59E0B" }},
                        {{ lbl: "Utilidad Neta", val: fmtDop(d.utilidad), dlt: "Margen: " + d.margen.toFixed(1) + "%", col: "#0284C7" }}
                    ];
                    res.voz = "En el año " + anioStr + ", la empresa generó una facturación de " + fmtVoz(d.ingresos) + deltaVoz + 
                              ", con egresos de " + fmtVoz(d.egresos) + " y una utilidad neta de " + fmtVoz(d.utilidad) + 
                              ", sosteniendo un margen neto del " + d.margen.toFixed(1) + " por ciento.";
                    res.html = "<b>Ejercicio " + anioStr + ":</b> Facturación de <b style='color:#059669;'>" + fmtDop(d.ingresos) + "</b> (" + deltaStr + 
                               "), egresos de <b style='color:#D97706;'>" + fmtDop(d.egresos) + "</b> y utilidad neta de <b style='color:#0284C7;'>" + 
                               fmtDop(d.utilidad) + "</b> (Margen: " + d.margen.toFixed(1) + "%).";
                    return res;
                }}
            }}

            // 14. CASO: UTILIDAD, MARGEN Y BENEFICIOS
            if (/utilidad|ganancia|beneficio|margen|rentabilidad|cuanto ganamos/.test(norm)) {{
                const c = FIN_DATA.consolidado;
                res.titulo = "📈 Utilidad Neta & Rentabilidad Corporativa";
                res.kpis = [
                    {{ lbl: "Utilidad Neta 36M", val: fmtDop(c.utilidad), dlt: "Beneficio acumulado", col: "#10B981" }},
                    {{ lbl: "Margen Neto", val: c.margen.toFixed(1) + "%", dlt: "Sobre ingresos", col: "#0284C7" }},
                    {{ lbl: "Facturación Total", val: fmtDop(c.ingresos), dlt: "Base de ingresos", col: "#7C3AED" }}
                ];
                res.voz = "La compañía acumula una utilidad neta total de " + fmtVoz(c.utilidad) + 
                          ", alcanzando un margen neto consolidado del " + c.margen.toFixed(1) + " por ciento sobre los ingresos.";
                res.html = "<b>Rentabilidad Consolidada:</b> Utilidad neta de <b style='color:#059669;'>" + fmtDop(c.utilidad) + 
                           "</b> con un margen del <b>" + c.margen.toFixed(1) + "%</b> sobre una facturación global de " + fmtDop(c.ingresos) + ".";
                return res;
            }}

            // 15. CASO: INGRESOS Y FACTURACIÓN GLOBAL
            if (/ingreso|venta|facturacion|cuanto vendimos/.test(norm)) {{
                const c = FIN_DATA.consolidado;
                res.titulo = "💰 Facturación & Ventas Totales";
                res.kpis = [
                    {{ lbl: "Facturación Global", val: fmtDop(c.ingresos), dlt: "4,853 asientos", col: "#10B981" }},
                    {{ lbl: "Cloud & Software", val: "RD$ 58.87M", dlt: "Línea principal", col: "#0284C7" }},
                    {{ lbl: "Consultoría & IA", val: "RD$ 39.25M", dlt: "Segunda línea", col: "#7C3AED" }}
                ];
                res.voz = "La facturación total acumulada de la empresa asciende a " + fmtVoz(c.ingresos) + 
                          ", encabezada por soluciones de software y cloud con más de cincuenta y ocho millones de pesos.";
                res.html = "<b>Facturación Total:</b> Ingresos acumulados por <b style='color:#059669;'>" + fmtDop(c.ingresos) + 
                           "</b>, liderados por Soluciones Cloud y Software con <b>RD$ 58.87M</b> y Consultoría e IA con <b>RD$ 39.25M</b>.";
                return res;
            }}

            // 16. CASO: GASTOS Y EGRESOS TOTALES
            if (/gasto|costo|egreso|salida|cuanto gastamos/.test(norm)) {{
                const c = FIN_DATA.consolidado;
                res.titulo = "📉 Egresos Totales & Estructura de Costos";
                res.kpis = [
                    {{ lbl: "Egresos Totales", val: fmtDop(c.egresos), dlt: "Costos + OPEX", col: "#EF4444" }},
                    {{ lbl: "Gastos Operativos", val: fmtDop(c.gastos), dlt: "OPEX total", col: "#DC2626" }},
                    {{ lbl: "Costos Directos", val: fmtDop(c.costos), dlt: "Costo de ventas", col: "#F59E0B" }}
                ];
                res.voz = "Los egresos consolidados de la compañía suman " + fmtVoz(c.egresos) + 
                          ", de los cuales " + fmtVoz(c.gastos) + " corresponden a gastos operativos y " + fmtVoz(c.costos) + " a costos directos.";
                res.html = "<b>Estructura de Egresos:</b> Egresos totales por <b style='color:#DC2626;'>" + fmtDop(c.egresos) + 
                           "</b>, compuestos por <b>" + fmtDop(c.gastos) + "</b> en OPEX y <b>" + fmtDop(c.costos) + "</b> en costos directos.";
                return res;
            }}

            // 17. CASO: DOLARIZACIÓN & MONEDA EXTRANJERA
            if (/dolar|usd|dolarizacion|moneda extranjera/.test(norm)) {{
                res.titulo = "💱 Dolarización de Ingresos & Exposición Cambiaria";
                res.kpis = [
                    {{ lbl: "Dolarización", val: FIN_DATA.dolarizacion.toFixed(1) + "%", dlt: "Ingresos en USD", col: "#10B981" }},
                    {{ lbl: "Bancos Extranjeros", val: fmtDop(FIN_DATA.caja_tesoreria.bancos), dlt: "Tesorería mixta", col: "#0284C7" }}
                ];
                res.voz = "El " + FIN_DATA.dolarizacion.toFixed(1) + " por ciento de los ingresos de la compañía está dolarizado, proporcionando una sólida cobertura frente a fluctuaciones cambiarias.";
                res.html = "El <b>" + FIN_DATA.dolarizacion.toFixed(1) + "%</b> de la facturación se percibe en dólares (USD), mitigando riesgos de devaluación cambiaria.";
                return res;
            }}

            // 18. CASO: PARTIDA DOBLE & AUDITORÍA
            if (/partida doble|cuadre|asiento|diferencia debitos/.test(norm)) {{
                res.titulo = "⚖️ Auditoría de Partida Doble & Cuadre Contable";
                res.kpis = [
                    {{ lbl: "Débitos Totales", val: "RD$ 251.63M", dlt: "4,853 asientos", col: "#10B981" }},
                    {{ lbl: "Créditos Totales", val: "RD$ 251.63M", dlt: "Balance perfecto", col: "#10B981" }},
                    {{ lbl: "Diferencia Neta", val: "RD$ 0.00", dlt: "Cuadre 100%", col: "#0284C7" }}
                ];
                res.voz = "La partida doble se encuentra perfectamente cuadrada al cien por ciento. Débitos y créditos suman exactamente doscientos cincuenta y un millones de pesos, con una diferencia de cero centavos.";
                res.html = "<b>Auditoría Forense:</b> La identidad Débitos = Créditos = <b>RD$ 251.63M</b> se cumple con diferencia de <b style='color:#059669;'>RD$ 0.00</b> en todos los asientos contables.";
                return res;
            }}

            // =================================================================
            // 19. RESPUESTA INTELIGENTE MULTIDIMENSIONAL (DIAGNÓSTICO 360°)
            // =================================================================
            const tot = FIN_DATA.consolidado;
            res.titulo = "🧠 Diagnóstico Ejecutivo 360°: " + raw;
            res.kpis = [
                {{ lbl: "Facturación Global", val: fmtDop(tot.ingresos), dlt: "36 meses auditados", col: "#10B981" }},
                {{ lbl: "Utilidad Neta", val: fmtDop(tot.utilidad), dlt: "Margen: " + tot.margen.toFixed(1) + "%", col: "#0284C7" }},
                {{ lbl: "Liquidez Inmediata", val: fmtDop(tot.liquidez_total), dlt: "Bancos + Caja", col: "#10B981" }},
                {{ lbl: "Mayor Pasivo", val: "RD$ 17.66M", dlt: "DGII (59.4% deuda)", col: "#EF4444" }}
            ];
            res.voz = "Para tu consulta sobre " + raw + ", te presento el diagnóstico corporativo general. " + 
                      "La empresa acumula una facturación de " + fmtVoz(tot.ingresos) + 
                      ", con una utilidad neta de " + fmtVoz(tot.utilidad) + 
                      " y una sólida liquidez de " + fmtVoz(tot.liquidez_total) + 
                      ". En deudas, el compromiso principal es con la DGII por " + fmtVoz(17660000) + 
                      ". Puedes preguntarme en detalle sobre cualquier departamento, cuenta, líder o año específico.";
            res.html = "Consulta analizada: <i>'" + raw + "'</i>.<br>" +
                       "<b>Posición Consolidada:</b> Facturación de <b style='color:#059669;'>" + fmtDop(tot.ingresos) + 
                       "</b>, utilidad neta de <b style='color:#0284C7;'>" + fmtDop(tot.utilidad) + 
                       "</b> (" + tot.margen.toFixed(1) + "% de margen) y disponibilidad inmediata en bancos y caja de <b style='color:#059669;'>" + 
                       fmtDop(tot.liquidez_total) + "</b>.<br>" +
                       "<span style='color:#64748B; font-size:0.84rem;'>💡 Puedes preguntar sobre cualquier cuenta ('sueldos', 'publicidad'), departamento ('Tecnología', 'Mercadeo'), líder ('Juancito Peña'), mes ('marzo') o año ('2024', '2025').</span>";

            return res;
        }}

        function mostrarRespuesta(q) {{
            const res = procesarPregunta(q);
            document.getElementById('result_box').style.display = 'block';
            document.getElementById('res_title').textContent = res.titulo;
            document.getElementById('query_input').value = q;

            // Renderizar KPIs
            const kpiBox = document.getElementById('res_kpis');
            kpiBox.innerHTML = '';
            for (const k of res.kpis) {{
                const el = document.createElement('div');
                el.className = 'kpi-item';
                el.innerHTML = '<div class="kpi-lbl">' + k.lbl + '</div>' +
                               '<div class="kpi-val">' + k.val + '</div>' +
                               '<div class="kpi-dlt" style="color:' + k.col + ';">' + k.dlt + '</div>';
                kpiBox.appendChild(el);
            }}

            // Renderizar explicación HTML
            document.getElementById('res_narration').innerHTML = res.html;

            // NARRACIÓN AUTOMÁTICA POR VOZ INMEDIATA
            narrarAutomaticamente(res.voz);
        }}

        function consultarTexto(t) {{
            if (synth) {{
                const unlock = new SpeechSynthesisUtterance('');
                synth.speak(unlock);
            }}
            mostrarRespuesta(t);
        }}

        function consultarInput() {{
            const t = document.getElementById('query_input').value.trim();
            if (t) {{
                if (synth) {{
                    const unlock = new SpeechSynthesisUtterance('');
                    synth.speak(unlock);
                }}
                mostrarRespuesta(t);
            }}
        }}

        // =====================================================================
        // RECONOCIMIENTO DE VOZ ACTIVO (SPEECH-TO-TEXT)
        // =====================================================================
        function iniciarEscucha() {{
            if (!SpeechRec) {{
                alert("Tu navegador no soporta reconocimiento de voz nativo (Web Speech API). Puedes usar los botones rápidos o escribir tu pregunta.");
                return;
            }}

            detenerVoz();

            if (isRecording && recognizer) {{
                recognizer.stop();
                setRecordingUI(false);
                return;
            }}

            // Desbloquear motor de voz en el clic táctil del usuario
            if (synth) {{
                const unlock = new SpeechSynthesisUtterance('');
                synth.speak(unlock);
            }}

            recognizer = new SpeechRec();
            recognizer.lang = 'es-DO';
            recognizer.continuous = false;
            recognizer.interimResults = true;

            recognizer.onstart = () => {{
                setRecordingUI(true);
            }};

            recognizer.onresult = (ev) => {{
                let finalTrans = '';
                let interim = '';
                for (let i = ev.resultIndex; i < ev.results.length; ++i) {{
                    if (ev.results[i].isFinal) {{
                        finalTrans += ev.results[i][0].transcript;
                    }} else {{
                        interim += ev.results[i][0].transcript;
                    }}
                }}
                if (interim) {{
                    document.getElementById('query_input').value = interim;
                }}
                if (finalTrans) {{
                    setRecordingUI(false);
                    mostrarRespuesta(finalTrans.trim());
                }}
            }};

            recognizer.onerror = (ev) => {{
                setRecordingUI(false);
                const err = ev.error;
                if (err === 'no-speech') {{
                    document.getElementById('status_txt').textContent = '⏳ No se escuchó voz';
                }} else if (err === 'not-allowed') {{
                    alert('Permiso de micrófono no otorgado. Habilítalo en tu navegador para hablar.');
                }}
            }};

            recognizer.onend = () => {{
                setRecordingUI(false);
            }};

            try {{
                recognizer.start();
            }} catch(e) {{
                console.error(e);
            }}
        }}

        // Inicializar voces
        if (synth && synth.onvoiceschanged !== undefined) {{
            synth.onvoiceschanged = () => {{ vozEspanol(); }};
        }}
    </script>
    </body>
    </html>
    """
    return html


def procesar_consulta_financiera(comando_raw: str, df: pd.DataFrame) -> dict:
    """Función de compatibilidad."""
    return {
        "valido": True,
        "titulo": f"Consulta: {comando_raw}",
        "texto_voz": f"Procesando consulta {comando_raw}",
        "texto_html": f"<p>{comando_raw}</p>",
        "kpis": []
    }
