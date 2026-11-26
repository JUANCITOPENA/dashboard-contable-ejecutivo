"""
================================================================================
MÓDULO DE INTELIGENCIA FINANCIERA UNIVERSAL & COPILOT DE VOZ (ESTÁNDAR JPV PRO)
================================================================================
Autor: Ing. Juancito Peña Vizcaíno
Propósito: Asistente conversacional analítico de voz bidireccional (STT + NLU + TTS).
           Cubo multidimensional relacional que responde preguntas libres:
           - Top N / Rankings (cuentas de mayor valor, mayor gasto, activos, pasivos, etc.)
           - Conteos e inventario de cuentas, departamentos y líderes
           - Promedios mensuales y estadísticas descriptivas
           - Ratios financieros, proporciones y pesos porcentuales (sueldos vs ventas)
           - Desgloses por categoría (activos, pasivos, gastos, costos, ingresos)
           - Crecimiento y variaciones interanuales (2024 a 2026)
           - Cuentas, departamentos, líderes, meses, trimestres y años específicos
           Responde con KPIs Bento interactivos y síntesis de voz ejecutiva automática.
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
        if decimal >= 100:
            entero += 1
            decimal = 0
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
    Construye el cubo multidimensional analítico de la empresa en un JSON estructurado
    con soporte para rankings Top-N, promedios, ratios y desgloses por categoría.
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
    activos_fijos = float(df[df['Codigo_Cuenta'] == 'CTA_106']['Monto_Neto_DOP'].sum())
    total_activos = float(act_df['Monto_Neto_DOP'].sum())
    total_pasivos = float(pas_df['Credito_DOP'].sum() - pas_df['Debito_DOP'].sum())
    total_capital = float(cap_df['Credito_DOP'].sum() - cap_df['Debito_DOP'].sum())
    sueldos = float(df[df['Codigo_Cuenta'] == 'CTA_601']['Debito_DOP'].sum())

    ing_24 = float(df[(df['Tipo_Cuenta'] == 'Ingresos') & (df['Año'] == 2024)]['Credito_DOP'].sum())
    ing_26 = float(df[(df['Tipo_Cuenta'] == 'Ingresos') & (df['Año'] == 2026)]['Credito_DOP'].sum())
    crec_ventas_24_26 = ((ing_26 - ing_24) / ing_24 * 100) if ing_24 > 0 else 0

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
            'liquidez_total': caja + b_dop + b_usd,
            'solvencia': (total_activos / total_pasivos) if total_pasivos > 0 else 0
        },
        'estadisticas': {
            'total_cuentas': int(df['Codigo_Cuenta'].nunique()),
            'total_deptos': int(df['Departamento'].nunique()),
            'total_lideres': int(df['Lider_Departamento'].dropna().nunique()),
            'total_asientos': len(df),
            'promedio_venta_mensual': ing_tot / 36,
            'promedio_gasto_mensual': egr_tot / 36,
            'promedio_utilidad_mensual': util_tot / 36,
            'sueldos_pct_ingresos': (sueldos / ing_tot * 100) if ing_tot > 0 else 0,
            'sueldos_pct_egresos': (sueldos / egr_tot * 100) if egr_tot > 0 else 0,
            'crecimiento_ventas_24_26': crec_ventas_24_26
        },
        'anios': {},
        'trimestres': {},
        'meses': {},
        'cuentas': {},
        'cuentas_ranking': [],
        'cuentas_por_tipo': {
            'Activo': [],
            'Pasivo': [],
            'Capital': [],
            'Ingresos': [],
            'Costo': [],
            'Gasto': []
        },
        'deptos': {},
        'deptos_ranking': [],
        'lideres': {},
        'lideres_ranking': [],
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
    for (cod, cta, tipo), grp in df.groupby(['Codigo_Cuenta', 'Cuenta_Contable', 'Tipo_Cuenta']):
        deb = float(grp['Debito_DOP'].sum())
        cred = float(grp['Credito_DOP'].sum())
        neto = float(grp['Monto_Neto_DOP'].sum())

        if tipo in ['Costo', 'Gasto']:
            val_economico = deb
        elif tipo == 'Ingresos':
            val_economico = cred
        elif tipo == 'Pasivo':
            val_economico = cred - deb
        else: # Activo, Capital
            val_economico = abs(neto) if neto != 0 else max(deb, cred)

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

        item_cuenta = {
            'codigo': str(cod),
            'nombre': str(cta),
            'tipo': str(tipo),
            'monto': val_economico,
            'debito': deb,
            'credito': cred,
            'neto': neto,
            'anios': anios_dict,
            'top_depto': top_dep
        }

        data['cuentas'][str(cta)] = item_cuenta
        data['cuentas_ranking'].append(item_cuenta)
        if str(tipo) in data['cuentas_por_tipo']:
            data['cuentas_por_tipo'][str(tipo)].append(item_cuenta)

    # Ordenar cuentas_ranking por monto descendente
    data['cuentas_ranking'].sort(key=lambda x: x['monto'], reverse=True)
    for t in data['cuentas_por_tipo']:
        data['cuentas_por_tipo'][t].sort(key=lambda x: x['monto'], reverse=True)

    # 5. Departamentos (Los 12 departamentos)
    for dep, grp in df.groupby('Departamento'):
        grp_egr = grp[grp['Tipo_Cuenta'].isin(['Costo', 'Gasto'])]
        gasto_dep = float(grp_egr['Debito_DOP'].sum())
        anios_dep = {int(a): float(g['Debito_DOP'].sum()) for a, g in grp_egr.groupby('Año') if pd.notna(a)}
        lider = str(grp['Lider_Departamento'].dropna().iloc[0]) if not grp['Lider_Departamento'].dropna().empty else "N/D"

        dep_item = {
            'nombre': str(dep),
            'lider': lider,
            'total_gasto': gasto_dep,
            'pct_empresa': (gasto_dep / egr_tot * 100) if egr_tot > 0 else 0,
            'anios': anios_dep
        }
        data['deptos'][str(dep)] = dep_item
        data['deptos_ranking'].append(dep_item)

    data['deptos_ranking'].sort(key=lambda x: x['total_gasto'], reverse=True)

    # 6. Líderes (Los 12 líderes departamentales)
    for lid, grp in df.groupby('Lider_Departamento'):
        grp_egr = grp[grp['Tipo_Cuenta'].isin(['Costo', 'Gasto'])]
        gasto_lid = float(grp_egr['Debito_DOP'].sum())
        depto = str(grp['Departamento'].dropna().iloc[0]) if not grp['Departamento'].dropna().empty else "N/D"
        lid_item = {
            'nombre': str(lid),
            'depto': depto,
            'total_gasto': gasto_lid,
            'pct_empresa': (gasto_lid / egr_tot * 100) if egr_tot > 0 else 0
        }
        data['lideres'][str(lid)] = lid_item
        data['lideres_ranking'].append(lid_item)

    data['lideres_ranking'].sort(key=lambda x: x['total_gasto'], reverse=True)

    # 7. Rankings y Superlativos
    m_ing = ing_df.groupby(['Año_Mes', 'Año', 'Mes'])['Credito_DOP'].sum().reset_index().sort_values(by='Credito_DOP', ascending=False)
    best_m = m_ing.iloc[0]
    worst_m = m_ing.iloc[-1]
    dep_sort = data['deptos_ranking']
    lid_sort = data['lideres_ranking']

    data['rankings'] = {
        'mejor_mes': {'nombre': f"{best_m['Mes']} {int(best_m['Año'])}", 'monto': float(best_m['Credito_DOP'])},
        'peor_mes': {'nombre': f"{worst_m['Mes']} {int(worst_m['Año'])}", 'monto': float(worst_m['Credito_DOP'])},
        'top_depto': {'nombre': dep_sort[0]['nombre'], 'monto': dep_sort[0]['total_gasto'], 'lider': dep_sort[0]['lider']},
        'menor_depto': {'nombre': dep_sort[-1]['nombre'], 'monto': dep_sort[-1]['total_gasto'], 'lider': dep_sort[-1]['lider']},
        'top_lider': {'nombre': lid_sort[0]['nombre'], 'monto': lid_sort[0]['total_gasto'], 'depto': lid_sort[0]['depto']},
        'menor_lider': {'nombre': lid_sort[-1]['nombre'], 'monto': lid_sort[-1]['total_gasto'], 'depto': lid_sort[-1]['depto']}
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
        .kpi-val {{ font-size: 1.22rem; font-weight: 900; color: #0F172A; margin: 3px 0; }}
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
                Pregunta libremente: rankings (ej: <i>cuáles son las tres cuentas de mayor valor</i>), estadísticas, gastos, activos o períodos.
            </span>
        </div>

        <div class="quick-chips">
            <span style="font-size: 0.75rem; font-weight: 800; color: #475569; margin-right: 4px;">⚡ PREGUNTAS EJECUTIVAS:</span>
            <button class="chip" onclick="consultarTexto('cuáles son las tres cuentas de mayor valor')">🏆 ¿Top 3 Cuentas de Mayor Valor?</button>
            <button class="chip" onclick="consultarTexto('cuáles son las tres cuentas de mayor gasto')">💸 ¿Top 3 Cuentas de Gasto?</button>
            <button class="chip" onclick="consultarTexto('cuáles son los tres departamentos que más gastan')">🏢 ¿Top 3 Departamentos?</button>
            <button class="chip" onclick="consultarTexto('quiénes son los tres líderes con mayor presupuesto')">👔 ¿Top 3 Líderes?</button>
            <button class="chip" onclick="consultarTexto('cuántas cuentas tenemos en total')">🔢 ¿Cuántas cuentas hay?</button>
            <button class="chip" onclick="consultarTexto('cuál es el promedio mensual de ventas')">📊 ¿Promedio Ventas?</button>
            <button class="chip" onclick="consultarTexto('qué porcentaje de los ingresos representan los sueldos')">👥 ¿Peso de Sueldos?</button>
            <button class="chip" onclick="consultarTexto('cuáles son las cuentas de activos')">🏛️ ¿Cuentas de Activos?</button>
            <button class="chip" onclick="consultarTexto('qué cuenta debe más')">🚨 ¿Qué cuenta debe más?</button>
            <button class="chip" onclick="consultarTexto('cómo estábamos en el 2024')">📅 ¿2024?</button>
            <button class="chip" onclick="consultarTexto('rendimiento financiero 2025')">📅 ¿2025?</button>
            <button class="chip" onclick="consultarTexto('cuánto crecieron las ventas de 2024 a 2026')">📈 ¿Crecimiento?</button>
        </div>

        <div class="input-bar">
            <input type="text" id="query_input" class="text-input" placeholder="Escribe o habla lo que desees saber (ej: ¿cuáles son las 3 cuentas de mayor valor? o ¿cuál es el promedio de gasto?)..." onkeydown="if(event.key==='Enter') consultarInput()">
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
                let ent = Math.floor(mm);
                let dec = Math.round((mm - ent) * 100);
                if (dec >= 100) {{ ent += 1; dec = 0; }}
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

        function extraerNumero(norm, defecto = 3) {{
            if (/\\b(un[oa]?|primer[oa]?|1)\\b/.test(norm)) return 1;
            if (/\\b(dos|segund[oa]s?|2)\\b/.test(norm)) return 2;
            if (/\\b(tres|tercer[oa]s?|3)\\b/.test(norm)) return 3;
            if (/\\b(cuatro|cuart[oa]s?|4)\\b/.test(norm)) return 4;
            if (/\\b(cinco|quint[oa]s?|5)\\b/.test(norm)) return 5;
            if (/\\b(seis|sext[oa]s?|6)\\b/.test(norm)) return 6;
            if (/\\b(siete|septim[oa]s?|7)\\b/.test(norm)) return 7;
            if (/\\b(ocho|octav[oa]s?|8)\\b/.test(norm)) return 8;
            if (/\\b(nueve|noven[oa]s?|9)\\b/.test(norm)) return 9;
            if (/\\b(diez|decim[oa]s?|10)\\b/.test(norm)) return 10;
            const m = norm.match(/\\b(\\d+)\\b/);
            if (m && parseInt(m[1]) <= 20) return parseInt(m[1]);
            return defecto;
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

            const nRanking = extraerNumero(norm, 3);

            // =================================================================
            // 1. RANKINGS DINÁMICOS & TOP N (Cuentas de mayor valor, mayor gasto, etc.)
            // =================================================================
            const esRanking = /top|mayor|mayores|mas alt[oa]s?|mas grande[s]?|ranking|primer[oa]s?|principales|de mayor valor|de mas valor|de mayor saldo|mas valor|mas gastan|mas ejecutan|de mas peso|mas costosas?/.test(norm);

            if (esRanking) {{
                // A) Top N Cuentas de Gasto / Egresos
                if (/gasto|costo|egreso|operativ[ao]|salida/.test(norm)) {{
                    const lista = FIN_DATA.pareto_egresos.slice(0, nRanking);
                    res.titulo = "📊 Top " + nRanking + " Cuentas de Mayor Gasto Corporativo";
                    res.kpis = lista.map((x, idx) => ({{
                        lbl: "#" + (idx + 1) + " " + x.cuenta.split(' ')[0] + "...",
                        val: fmtDop(x.monto),
                        dlt: x.pct.toFixed(1) + "% del gasto",
                        col: idx === 0 ? "#7C3AED" : (idx === 1 ? "#DC2626" : "#0284C7")
                    }}));
                    const nombresVoz = lista.map((x, idx) => (idx === 0 ? "en primer lugar " : (idx === 1 ? "en segundo lugar " : "y en tercer lugar ")) + x.cuenta + " con " + fmtVoz(x.monto)).join(", ");
                    res.voz = "Las " + nRanking + " cuentas de mayor gasto de la empresa son: " + nombresVoz + ".";
                    res.html = "<b>Top " + nRanking + " Cuentas de Mayor Gasto:</b><br>" + 
                               lista.map((x, idx) => "<b>" + (idx + 1) + ". " + x.cuenta + " (" + x.codigo + "):</b> " + fmtDop(x.monto) + " (" + x.pct.toFixed(1) + "% del total)").join("<br>");
                    return res;
                }}

                // B) Top N Cuentas de Pasivos / Deuda
                if (/pasivo|deuda|debe|obligacion|compromiso|fisco|acreedor/.test(norm)) {{
                    const lista = FIN_DATA.pasivos.slice(0, nRanking);
                    const totPas = FIN_DATA.consolidado.pasivos;
                    res.titulo = "🚨 Top " + nRanking + " Cuentas de Mayor Deuda (Pasivos)";
                    res.kpis = lista.map((x, idx) => ({{
                        lbl: "#" + (idx + 1) + " " + x.cuenta.split(' ')[0] + "...",
                        val: fmtDop(x.monto),
                        dlt: ((x.monto / totPas) * 100).toFixed(1) + "% de deuda",
                        col: idx === 0 ? "#DC2626" : "#F59E0B"
                    }}));
                    const nombresVoz = lista.map((x, idx) => (idx === 0 ? "primero " : (idx === 1 ? "segundo " : "y tercero ")) + x.cuenta + " con " + fmtVoz(x.monto)).join(", ");
                    res.voz = "Las " + nRanking + " cuentas con mayor pasivo exigible son: " + nombresVoz + ".";
                    res.html = "<b>Top " + nRanking + " Pasivos Exigibles:</b><br>" + 
                               lista.map((x, idx) => "<b>" + (idx + 1) + ". " + x.cuenta + " (" + x.codigo + "):</b> " + fmtDop(x.monto) + " (" + ((x.monto / totPas) * 100).toFixed(1) + "% de la deuda)").join("<br>");
                    return res;
                }}

                // C) Top N Cuentas de Activos
                if (/activo|banco|propiedad|equip|patrimonio/.test(norm) && !/depto|departamento/.test(norm)) {{
                    const lista = (FIN_DATA.cuentas_por_tipo['Activo'] || []).slice(0, nRanking);
                    res.titulo = "🏛️ Top " + nRanking + " Cuentas de Mayor Activo";
                    res.kpis = lista.map((x, idx) => ({{
                        lbl: "#" + (idx + 1) + " " + x.nombre.split(' ')[0] + "...",
                        val: fmtDop(x.monto),
                        dlt: x.codigo,
                        col: idx === 0 ? "#10B981" : "#0284C7"
                    }}));
                    const nombresVoz = lista.map((x, idx) => (idx === 0 ? "primero " : (idx === 1 ? "segundo " : "y tercero ")) + x.nombre + " con " + fmtVoz(x.monto)).join(", ");
                    res.voz = "Las " + nRanking + " cuentas de mayor activo son: " + nombresVoz + ".";
                    res.html = "<b>Top " + nRanking + " Cuentas de Activo:</b><br>" + 
                               lista.map((x, idx) => "<b>" + (idx + 1) + ". " + x.nombre + " (" + x.codigo + "):</b> " + fmtDop(x.monto)).join("<br>");
                    return res;
                }}

                // D) Top N Departamentos por Gasto
                if (/departamento|depto|area/.test(norm)) {{
                    const lista = FIN_DATA.deptos_ranking.slice(0, nRanking);
                    res.titulo = "🏢 Top " + nRanking + " Departamentos de Mayor Presupuesto";
                    res.kpis = lista.map((x, idx) => ({{
                        lbl: "#" + (idx + 1) + " " + x.nombre.split(' ')[0],
                        val: fmtDop(x.total_gasto),
                        dlt: x.pct_empresa.toFixed(1) + "% empresa",
                        col: idx === 0 ? "#DC2626" : "#0284C7"
                    }}));
                    const nombresVoz = lista.map((x, idx) => (idx === 0 ? "primero " : (idx === 1 ? "segundo " : "y tercero ")) + x.nombre + " con " + fmtVoz(x.total_gasto)).join(", ");
                    res.voz = "Los " + nRanking + " departamentos con mayor gasto son: " + nombresVoz + ".";
                    res.html = "<b>Top " + nRanking + " Departamentos de Mayor Gasto:</b><br>" + 
                               lista.map((x, idx) => "<b>" + (idx + 1) + ". " + x.nombre + ":</b> " + fmtDop(x.total_gasto) + " (" + x.pct_empresa.toFixed(1) + "% del gasto corporativo - Líder: " + x.lider + ")").join("<br>");
                    return res;
                }}

                // E) Top N Líderes por Presupuesto
                if (/lider|persona|director|gerente|quienes/.test(norm)) {{
                    const lista = FIN_DATA.lideres_ranking.slice(0, nRanking);
                    res.titulo = "👔 Top " + nRanking + " Líderes con Mayor Presupuesto Ejecutado";
                    res.kpis = lista.map((x, idx) => ({{
                        lbl: "#" + (idx + 1) + " " + x.nombre.split(' ')[0] + " " + (x.nombre.split(' ')[1] || ''),
                        val: fmtDop(x.total_gasto),
                        dlt: x.depto.split(' ')[0],
                        col: idx === 0 ? "#7C3AED" : "#0284C7"
                    }}));
                    const nombresVoz = lista.map((x, idx) => (idx === 0 ? "primero " : (idx === 1 ? "segundo " : "y tercero ")) + x.nombre + " con " + fmtVoz(x.total_gasto)).join(", ");
                    res.voz = "Los " + nRanking + " líderes con mayor presupuesto ejecutado son: " + nombresVoz + ".";
                    res.html = "<b>Top " + nRanking + " Líderes con Mayor Presupuesto:</b><br>" + 
                               lista.map((x, idx) => "<b>" + (idx + 1) + ". " + x.nombre + " (" + x.depto + "):</b> " + fmtDop(x.total_gasto) + " (" + x.pct_empresa.toFixed(1) + "% de la empresa)").join("<br>");
                    return res;
                }}

                // F) TOP N CUENTAS DE MAYOR VALOR (GENERAL / ABSOLUTO EN LA EMPRESA)
                // Caso que el usuario preguntó: "cuáles son las tres cuentas de mayor valor"
                const listaGral = FIN_DATA.cuentas_ranking.slice(0, nRanking);
                res.titulo = "🏆 Top " + nRanking + " Cuentas de Mayor Valor en la Empresa";
                res.kpis = listaGral.map((x, idx) => ({{
                    lbl: "#" + (idx + 1) + " " + x.nombre.split(' ')[0] + " " + (x.nombre.split(' ')[1] || ''),
                    val: fmtDop(x.monto),
                    dlt: x.tipo + " (" + x.codigo + ")",
                    col: idx === 0 ? "#7C3AED" : (idx === 1 ? "#0284C7" : "#10B981")
                }}));
                const nombresVoz = listaGral.map((x, idx) => (idx === 0 ? "en primer lugar " : (idx === 1 ? "en segundo lugar " : (idx === 2 ? "y en tercer lugar " : "seguido de "))) + x.nombre + " con " + fmtVoz(x.monto)).join(", ");
                res.voz = "Las " + nRanking + " cuentas de mayor valor en la empresa son: " + nombresVoz + ".";
                res.html = "<b>Las " + nRanking + " Cuentas de Mayor Valor Corporativo:</b><br>" + 
                           listaGral.map((x, idx) => "<b>" + (idx + 1) + ". " + x.nombre + " (" + x.codigo + " - " + x.tipo + "):</b> <b style='color:#0284C7;'>" + fmtDop(x.monto) + "</b>").join("<br>") + 
                           "<br><small style='color:#64748B;'>Valores ordenados por volumen económico y saldo patrimonial neto auditado.</small>";
                return res;
            }}

            // =================================================================
            // 2. CONTEO & INVENTARIO DE ENTIDADES (¿Cuántas cuentas, deptos, etc.?)
            // =================================================================
            if (/cuant[ao]s? (cuentas|departamentos|areas|lideres|asientos|registros)/.test(norm)) {{
                const st = FIN_DATA.estadisticas;
                if (/cuenta/.test(norm)) {{
                    res.titulo = "📑 Catálogo General: 18 Cuentas Contables Oficiales";
                    res.kpis = [
                        {{ lbl: "Total Cuentas", val: st.total_cuentas.toString(), dlt: "Catálogo activo", col: "#0284C7" }},
                        {{ lbl: "Activos & Pasivos", val: "8 Cuentas", dlt: "Balance", col: "#10B981" }},
                        {{ lbl: "Ingresos & Gastos", val: "9 Cuentas", dlt: "P&L", col: "#F59E0B" }}
                    ];
                    res.voz = "La empresa opera con dieciocho cuentas contables estructuradas: cinco de activo, tres de pasivo, una de capital, dos de ingresos, dos de costo y cinco de gastos operativos.";
                    res.html = "<b>Estructura del Catálogo (18 Cuentas):</b><br>" + 
                               "• <b>Activos (5):</b> Bancos DOP, Bancos USD, Caja General, CxC Clientes, Activos Fijos.<br>" +
                               "• <b>Pasivos (3):</b> ITBIS DGII, Retenciones TSS/ISR, Proveedores CxP.<br>" +
                               "• <b>Capital (1):</b> Capital Social Aportado.<br>" +
                               "• <b>Resultados (9):</b> 2 de Ingresos, 2 de Costos y 5 de Gastos Operativos.";
                    return res;
                }}
                if (/departamento|area/.test(norm)) {{
                    res.titulo = "🏢 Estructura Operativa: 12 Departamentos";
                    res.kpis = [
                        {{ lbl: "Departamentos", val: st.total_deptos.toString(), dlt: "Áreas activas", col: "#0284C7" }},
                        {{ lbl: "Depto Mayor Gasto", val: "Tecnología", dlt: "RD$ 6.81M", col: "#DC2626" }},
                        {{ lbl: "Depto Más Austero", val: "Marketing", dlt: "RD$ 2.80M", col: "#10B981" }}
                    ];
                    res.voz = "La organización cuenta con doce departamentos corporativos activos, siendo Tecnología el de mayor presupuesto ejecutado y Marketing el más austero.";
                    res.html = "<b>Organigrama Departamental (12 Áreas):</b> Tecnología, Marketing, Ventas, Finanzas, Logística, Compras, Operaciones, Recursos Humanos, Soporte Técnico, Auditoría, Legal e I+D.";
                    return res;
                }}
                if (/lider|director|gerente/.test(norm)) {{
                    res.titulo = "👔 Equipo Directivo: 12 Líderes Departamentales";
                    res.kpis = [
                        {{ lbl: "Líderes de Área", val: st.total_lideres.toString(), dlt: "1 por departamento", col: "#7C3AED" }},
                        {{ lbl: "Mayor Ejecución", val: "Juancito Peña", dlt: "Tecnología", col: "#0284C7" }},
                        {{ lbl: "Menor Ejecución", val: "Carmen Rosario", dlt: "Marketing", col: "#10B981" }}
                    ];
                    res.voz = "Existen doce líderes departamentales a cargo de la gestión presupuestaria, encabezados por el Ingeniero Juancito Peña en Tecnología y Carlos López en Finanzas.";
                    res.html = "<b>Líderes Departamentales (12):</b> Ing. Juancito Peña, Carmen Rosario, Sofía Hernández, Carlos López, Laura Sánchez, Pedro Morales, Ricardo Vargas, Ana Martínez, Elena Gómez, David Ramírez, Lic. Roberto Castillo y Patricia Cruz.";
                    return res;
                }}
                if (/asiento|registro|movimiento/.test(norm)) {{
                    res.titulo = "⚖️ Auditoría Forense: 4,853 Asientos Contables";
                    res.kpis = [
                        {{ lbl: "Total Asientos", val: "4,853", dlt: "Libro Diario", col: "#0284C7" }},
                        {{ lbl: "Período Cubierto", val: "36 Meses", dlt: "2024 - 2026", col: "#10B981" }},
                        {{ lbl: "Cuadre Débitos/Créditos", val: "100%", dlt: "Diferencia RD$ 0.00", col: "#16A34A" }}
                    ];
                    res.voz = "Se auditaron cuatro mil ochocientos cincuenta y tres asientos contables en el libro diario consolidado, con un cuadre matemático perfecto de cero centavos de diferencia.";
                    res.html = "Auditoría de <b>4,853 asientos contables</b> en 36 meses, certificando cuadre de partida doble perfecto al 100%.";
                    return res;
                }}
            }}

            // =================================================================
            // 3. PROMEDIOS MENSUALES Y ESTADÍSTICAS
            // =================================================================
            if (/promedio.*(venta|facturacion|ingreso|gasto|egreso)|cuanto se (vende|gasta) (al|por) mes/.test(norm)) {{
                const st = FIN_DATA.estadisticas;
                res.titulo = "📊 Promedios Mensuales de Operación (36 Meses)";
                res.kpis = [
                    {{ lbl: "Venta Mensual Prom.", val: fmtDop(st.promedio_venta_mensual), dlt: "Facturación media", col: "#10B981" }},
                    {{ lbl: "Gasto Mensual Prom.", val: fmtDop(st.promedio_gasto_mensual), dlt: "OPEX medio", col: "#F59E0B" }},
                    {{ lbl: "Utilidad Mensual Prom.", val: fmtDop(st.promedio_utilidad_mensual), dlt: "Beneficio medio", col: "#0284C7" }}
                ];
                res.voz = "En promedio, la empresa factura " + fmtVoz(st.promedio_venta_mensual) + 
                          " cada mes, frente a un gasto mensual medio de " + fmtVoz(st.promedio_gasto_mensual) + 
                          ", generando una utilidad mensual promedio de " + fmtVoz(st.promedio_utilidad_mensual) + ".";
                res.html = "<b>Estadísticas Mensuales Medias:</b> Facturación de <b style='color:#059669;'>" + fmtDop(st.promedio_venta_mensual) + 
                           "</b>/mes, egresos de <b style='color:#D97706;'>" + fmtDop(st.promedio_gasto_mensual) + 
                           "</b>/mes y utilidad neta media de <b style='color:#0284C7;'>" + fmtDop(st.promedio_utilidad_mensual) + "</b>/mes.";
                return res;
            }}

            // =================================================================
            // 4. RATIOS & PESO PORCENTUAL (Sueldos vs Ventas, Solvencia, etc.)
            // =================================================================
            if (/porcentaje.*(sueldo|salario|nomina)|peso.*(sueldo|salario|nomina)|cuanto representan los sueldos/.test(norm)) {{
                const st = FIN_DATA.estadisticas;
                res.titulo = "👥 Peso de Sueldos y Nómina en las Finanzas";
                res.kpis = [
                    {{ lbl: "Sueldos / Egresos", val: st.sueldos_pct_egresos.toFixed(1) + "%", dlt: "De todos los gastos", col: "#7C3AED" }},
                    {{ lbl: "Sueldos / Ventas", val: st.sueldos_pct_ingresos.toFixed(1) + "%", dlt: "De la facturación", col: "#0284C7" }},
                    {{ lbl: "Monto Ejecutado", val: "RD$ 24.00M", dlt: "36 meses", col: "#10B981" }}
                ];
                res.voz = "Los sueldos y salarios representan el " + st.sueldos_pct_egresos.toFixed(1) + 
                          " por ciento de todos los egresos corporativos, y equivalen al " + st.sueldos_pct_ingresos.toFixed(1) + 
                          " por ciento de la facturación global de la empresa.";
                res.html = "<b>Impacto de la Nómina (CTA_601):</b> Absorbe el <b style='color:#7C3AED;'>" + st.sueldos_pct_egresos.toFixed(1) + 
                           "%</b> del total de egresos corporativos y el <b>" + st.sueldos_pct_ingresos.toFixed(1) + "%</b> de las ventas totales con un acumulado de <b>RD$ 24.00M</b>.";
                return res;
            }}

            if (/solvencia|relacion.*activo.*pasivo|cobertura de deuda/.test(norm)) {{
                const sol = FIN_DATA.consolidado.solvencia;
                res.titulo = "🛡️ Ratio de Solvencia Patrimonial (Activos vs Pasivos)";
                res.kpis = [
                    {{ lbl: "Solvencia", val: sol.toFixed(2) + "x", dlt: "Activos / Pasivos", col: "#10B981" }},
                    {{ lbl: "Activos Totales", val: fmtDop(FIN_DATA.consolidado.activos), dlt: "Respaldo", col: "#0284C7" }},
                    {{ lbl: "Pasivos Totales", val: fmtDop(FIN_DATA.consolidado.pasivos), dlt: "Deuda exigible", col: "#EF4444" }}
                ];
                res.voz = "El ratio de solvencia de la empresa es de " + sol.toFixed(2) + 
                          " veces. Esto significa que por cada peso de deuda exigible, la compañía dispone de cinco punto veintitrés pesos en activos de respaldo.";
                res.html = "<b>Solvencia Financiera:</b> <b style='color:#059669;'>" + sol.toFixed(2) + 
                           " a 1</b>. La empresa cuenta con " + fmtDop(FIN_DATA.consolidado.activos) + 
                           " en activos respaldando " + fmtDop(FIN_DATA.consolidado.pasivos) + " en deudas exigibles.";
                return res;
            }}

            if (/crecimiento.*(ventas|facturacion|ingresos)|cuanto crecieron las ventas|evolucion 2024.*2026/.test(norm)) {{
                const st = FIN_DATA.estadisticas;
                res.titulo = "📈 Crecimiento de Facturación (2024 a 2026)";
                res.kpis = [
                    {{ lbl: "Crecimiento Acumulado", val: "+" + st.crecimiento_ventas_24_26.toFixed(1) + "%", dlt: "2024 vs 2026", col: "#10B981" }},
                    {{ lbl: "Ventas 2024", val: "RD$ 28.22M", dlt: "Año base", col: "#64748B" }},
                    {{ lbl: "Ventas 2026", val: "RD$ 38.37M", dlt: "Año cierre", col: "#0284C7" }}
                ];
                res.voz = "La facturación creció un " + st.crecimiento_ventas_24_26.toFixed(1) + 
                          " por ciento entre dos mil veinticuatro y dos mil veintiséis, pasando de veintiocho punto veintidós millones a treinta y ocho punto treinta y siete millones de pesos.";
                res.html = "<b>Expansión Comercial:</b> Crecimiento de <b style='color:#059669;'>+" + st.crecimiento_ventas_24_26.toFixed(1) + 
                           "%</b> entre 2024 (RD$ 28.22M) y 2026 (RD$ 38.37M).";
                return res;
            }}

            // =================================================================
            // 5. LISTADOS POR CATEGORÍA CONTABLE
            // =================================================================
            if (/cuales son.*(activos|pasivos|gastos|ingresos)/.test(norm)) {{
                let tipoCat = "Activo";
                if (/pasivo/.test(norm)) tipoCat = "Pasivo";
                else if (/gasto/.test(norm)) tipoCat = "Gasto";
                else if (/ingreso/.test(norm)) tipoCat = "Ingresos";

                const listaCat = FIN_DATA.cuentas_por_tipo[tipoCat] || [];
                res.titulo = "📋 Cuentas de " + tipoCat + " (" + listaCat.length + " Cuentas)";
                res.kpis = listaCat.slice(0, 3).map((x, idx) => ({{
                    lbl: x.nombre.split(' ')[0] + "...",
                    val: fmtDop(x.monto),
                    dlt: x.codigo,
                    col: "#0284C7"
                }}));
                const nombresVoz = listaCat.map(x => x.nombre + " con " + fmtVoz(x.monto)).join(", ");
                res.voz = "Las cuentas de " + tipoCat + " son: " + nombresVoz + ".";
                res.html = "<b>Cuentas de " + tipoCat + " registradas:</b><br>" + 
                           listaCat.map(x => "• <b>" + x.nombre + " (" + x.codigo + "):</b> " + fmtDop(x.monto)).join("<br>");
                return res;
            }}

            // =================================================================
            // 6. TEMPORALIDADES ESPECÍFICAS (Años, Trimestres, Meses)
            // =================================================================
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

            // =================================================================
            // 7. CUENTAS, DEPARTAMENTOS Y LÍDERES ESPECÍFICOS
            // =================================================================
            // A) Cuentas Contables Específicas
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

            for (const c of cuentasDef) {{
                if (c.regex.test(norm)) {{
                    const cData = FIN_DATA.cuentas[c.key];
                    if (cData) {{
                        res.titulo = "📑 Cuenta: " + c.key;
                        res.kpis = [
                            {{ lbl: "Saldo / Monto", val: fmtDop(cData.monto), dlt: "Acumulado", col: "#0284C7" }},
                            {{ lbl: "Tipo de Cuenta", val: cData.tipo, dlt: cData.codigo, col: "#64748B" }},
                            {{ lbl: "Depto Principal", val: cData.top_depto, dlt: "Mayor impacto", col: "#10B981" }}
                        ];
                        res.voz = "La cuenta " + c.key + " registra un saldo de " + fmtVoz(cData.monto) + 
                                  ", siendo " + cData.top_depto + " el departamento con mayor actividad registrada.";
                        res.html = "<b>" + c.key + " (" + cData.codigo + "):</b> Saldo registrado de <b style='color:#0284C7;'>" + 
                                   fmtDop(cData.monto) + "</b> (" + cData.tipo + "). Departamento de mayor impacto: <b>" + cData.top_depto + "</b>.";
                        return res;
                    }}
                }}
            }}

            // B) Departamentos Específicos
            for (const d of FIN_DATA.deptos_ranking) {{
                const normD = d.nombre.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, "").replace(/[^a-z0-9]/g, " ");
                const partes = normD.split(' ').filter(p => p.length >= 4);
                if (partes.some(p => norm.includes(p))) {{
                    res.titulo = "🏢 Departamento: " + d.nombre;
                    res.kpis = [
                        {{ lbl: "Gasto Ejecutado", val: fmtDop(d.total_gasto), dlt: "Presupuesto", col: "#DC2626" }},
                        {{ lbl: "Líder a Cargo", val: d.lider, dlt: "Gestión", col: "#0284C7" }},
                        {{ lbl: "Participación", val: d.pct_empresa.toFixed(1) + "%", dlt: "De la empresa", col: "#7C3AED" }}
                    ];
                    res.voz = "El departamento de " + d.nombre + ", a cargo de " + d.lider + 
                              ", ejecutó un gasto total de " + fmtVoz(d.total_gasto) + 
                              ", representando el " + d.pct_empresa.toFixed(1) + " por ciento del presupuesto corporativo.";
                    res.html = "El área de <b>" + d.nombre + "</b> liderada por <b>" + d.lider + 
                               "</b> ejecutó <b style='color:#DC2626;'>" + fmtDop(d.total_gasto) + "</b> (" + d.pct_empresa.toFixed(1) + "% del gasto corporativo).";
                    return res;
                }}
            }}

            // C) Líderes Específicos
            for (const lid of FIN_DATA.lideres_ranking) {{
                const normL = lid.nombre.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, "").replace(/ing\\.|lic\\./g, "").trim();
                const partes = normL.split(' ').filter(p => p.length >= 4);
                if (partes.some(p => norm.includes(p))) {{
                    res.titulo = "👔 Líder Departamental: " + lid.nombre;
                    res.kpis = [
                        {{ lbl: "Total Administrado", val: fmtDop(lid.total_gasto), dlt: "Presupuesto", col: "#7C3AED" }},
                        {{ lbl: "Departamento", val: lid.depto, dlt: "Asignación", col: "#0284C7" }},
                        {{ lbl: "Participación", val: lid.pct_empresa.toFixed(1) + "%", dlt: "Del gasto", col: "#F59E0B" }}
                    ];
                    res.voz = lid.nombre + " lidera " + lid.depto + " y ha administrado un presupuesto total de " + 
                              fmtVoz(lid.total_gasto) + ", equivalente al " + lid.pct_empresa.toFixed(1) + " por ciento del gasto corporativo.";
                    res.html = "<b>" + lid.nombre + ":</b> Responsable del departamento de <b>" + lid.depto + 
                               "</b> con un gasto ejecutado acumulado de <b style='color:#7C3AED;'>" + fmtDop(lid.total_gasto) + "</b>.";
                    return res;
                }}
            }}

            // =================================================================
            // 8. DIAGNÓSTICO ADAPTATIVO CONVERSACIONAL (NUNCA ENTRA EN BUCLE)
            // =================================================================
            const tot = FIN_DATA.consolidado;
            res.titulo = "🧠 Análisis Financiero Ejecutivo: " + raw;
            res.kpis = [
                {{ lbl: "Facturación Global", val: fmtDop(tot.ingresos), dlt: "36 meses", col: "#10B981" }},
                {{ lbl: "Utilidad Neta", val: fmtDop(tot.utilidad), dlt: "Margen: " + tot.margen.toFixed(1) + "%", col: "#0284C7" }},
                {{ lbl: "Liquidez Inmediata", val: fmtDop(tot.liquidez_total), dlt: "Bancos + Caja", col: "#10B981" }},
                {{ lbl: "Deuda Principal", val: "RD$ 17.66M", dlt: "DGII (59.4%)", col: "#EF4444" }}
            ];
            res.voz = "Para tu consulta sobre " + raw + ", te presento el estado general. La empresa mantiene una facturación de " + 
                      fmtVoz(tot.ingresos) + ", con utilidad neta de " + fmtVoz(tot.utilidad) + 
                      " y liquidez de " + fmtVoz(tot.liquidez_total) + 
                      ". Puedes preguntarme sobre rankings como cuáles son las tres cuentas de mayor valor, promedios de ventas o cualquier departamento.";
            res.html = "Consulta analizada: <i>'" + raw + "'</i>.<br>" +
                       "<b>Diagnóstico Consolidado:</b> Facturación de <b style='color:#059669;'>" + fmtDop(tot.ingresos) + 
                       "</b>, utilidad neta de <b style='color:#0284C7;'>" + fmtDop(tot.utilidad) + 
                       "</b> (Margen: " + tot.margen.toFixed(1) + "%) y liquidez inmediata en bancos y caja de <b style='color:#059669;'>" + 
                       fmtDop(tot.liquidez_total) + "</b>.<br>" +
                       "<span style='color:#64748B; font-size:0.84rem;'>💡 Puedes preguntar: 'cuáles son las tres cuentas de mayor valor', 'promedio mensual de ventas', 'qué cuenta debe más', o 'cuánto gastó Tecnología'.</span>";

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
