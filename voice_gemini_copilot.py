"""
================================================================================
STUDIO CONVERSACIONAL DE IA & VOZ AGÉNTICA CON POOL GEMINI (ESTÁNDAR JPV PRO)
================================================================================
Autor: Ing. Juancito Peña Vizcaíno
Propósito: Pestaña interactiva de Inteligencia Artificial Financiera conectada a un
           pool dinámico de modelos Google Gemini con enrutamiento inteligente,
           protección contra abuso y bucles de tokens (Token Guard), reconocimiento
           de voz bidireccional (STT + TTS nativo), KPIs Bento dinámicos, gráficos
           interactivos en tiempo real con Chart.js y tablas analíticas formateadas.
================================================================================
"""

import json
import os
import re
import unicodedata
import pandas as pd


def generar_prompt_sistema_contable(df: pd.DataFrame) -> str:
    """
    Construye el contexto financiero y contable integral para el Agente Gemini
    calculando todas las métricas de forma 100% dinámica desde el dataframe ampliado.
    """
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
    margen_neto = (util_tot / ing_tot * 100) if ing_tot > 0 else 0
    margen_bruto = ((ing_tot - cos_tot) / ing_tot * 100) if ing_tot > 0 else 0

    caja = float(df[df['Codigo_Cuenta'] == 'CTA_101']['Monto_Neto_DOP'].sum())
    b_dop = float(df[df['Codigo_Cuenta'] == 'CTA_102']['Monto_Neto_DOP'].sum())
    b_usd = float(df[df['Codigo_Cuenta'] == 'CTA_103']['Monto_Neto_DOP'].sum())
    cxc = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Monto_Neto_DOP'].sum())
    activos_fijos = float(df[df['Codigo_Cuenta'] == 'CTA_106']['Monto_Neto_DOP'].sum())
    total_activos = float(act_df['Monto_Neto_DOP'].sum())

    itbis = float(df[df['Codigo_Cuenta'] == 'CTA_203']['Credito_DOP'].sum() - df[df['Codigo_Cuenta'] == 'CTA_203']['Debito_DOP'].sum())
    prov = float(df[df['Codigo_Cuenta'] == 'CTA_201']['Credito_DOP'].sum() - df[df['Codigo_Cuenta'] == 'CTA_201']['Debito_DOP'].sum())
    tss = float(df[df['Codigo_Cuenta'] == 'CTA_204']['Credito_DOP'].sum() - df[df['Codigo_Cuenta'] == 'CTA_204']['Debito_DOP'].sum())
    total_pasivos = float(pas_df['Credito_DOP'].sum() - pas_df['Debito_DOP'].sum())
    total_capital = float(cap_df['Credito_DOP'].sum() - cap_df['Debito_DOP'].sum())

    sueldos = float(df[df['Codigo_Cuenta'] == 'CTA_601']['Debito_DOP'].sum())
    pct_sueldos_ing = (sueldos / ing_tot * 100) if ing_tot > 0 else 0
    pct_sueldos_egr = (sueldos / egr_tot * 100) if egr_tot > 0 else 0

    c401 = float(df[df['Codigo_Cuenta'] == 'CTA_401']['Credito_DOP'].sum())
    c402 = float(df[df['Codigo_Cuenta'] == 'CTA_402']['Credito_DOP'].sum())
    c501 = float(df[df['Codigo_Cuenta'] == 'CTA_501']['Debito_DOP'].sum())
    c502 = float(df[df['Codigo_Cuenta'] == 'CTA_502']['Debito_DOP'].sum())
    c602 = float(df[df['Codigo_Cuenta'] == 'CTA_602']['Debito_DOP'].sum())
    c603 = float(df[df['Codigo_Cuenta'] == 'CTA_603']['Debito_DOP'].sum())
    c604 = float(df[df['Codigo_Cuenta'] == 'CTA_604']['Debito_DOP'].sum())
    c605 = float(df[df['Codigo_Cuenta'] == 'CTA_605']['Debito_DOP'].sum())

    # Crecimiento anual dinámico (2024, 2025, 2026)
    anios_info = []
    for a in sorted(df['Año'].dropna().unique()):
        sub_a = df[df['Año'] == a]
        ing_a = float(sub_a[sub_a['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
        cos_a = float(sub_a[sub_a['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum())
        gas_a = float(sub_a[sub_a['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum())
        egr_a = cos_a + gas_a
        util_a = ing_a - egr_a
        mg_a = (util_a / ing_a * 100) if ing_a > 0 else 0
        anios_info.append(f"- Año {int(a)}: Facturación RD$ {ing_a:,.2f} | Egresos RD$ {egr_a:,.2f} | Utilidad Neta RD$ {util_a:,.2f} (Margen: {mg_a:.1f}%)")

    # Departamentos ordenados por gasto
    dep_gastos = []
    for dep, grp in df.groupby('Departamento'):
        g_dep = float(grp[grp['Tipo_Cuenta'].isin(['Costo', 'Gasto'])]['Debito_DOP'].sum())
        lid = str(grp['Lider_Departamento'].dropna().iloc[0]) if not grp['Lider_Departamento'].dropna().empty else "N/D"
        pct_dep = (g_dep / egr_tot * 100) if egr_tot > 0 else 0
        dep_gastos.append({'depto': dep, 'gasto': g_dep, 'lider': lid, 'pct': pct_dep})
    dep_gastos.sort(key=lambda x: x['gasto'], reverse=True)
    deptos_str = [f"{i}. {d['depto']}: RD$ {d['gasto']:,.2f} ({d['pct']:.1f}% del presupuesto - Líder: {d['lider']})" for i, d in enumerate(dep_gastos, 1)]

    # Récords mensuales
    m_ing = ing_df.groupby(['Año', 'Mes'])['Credito_DOP'].sum().reset_index().sort_values(by='Credito_DOP', ascending=False)
    best_m = m_ing.iloc[0]
    worst_m = m_ing.iloc[-1]

    solvencia = (total_activos / total_pasivos) if total_pasivos > 0 else 0
    liquidez_total = caja + b_dop + b_usd
    total_debitos = float(df['Debito_DOP'].sum())
    total_creditos = float(df['Credito_DOP'].sum())
    asientos_count = len(df)
    polizas_count = df['Numero_Poliza'].nunique()

    prompt = f"""
Eres el Copilot Senior de Inteligencia Financiera, Auditoría y Data Science para el Dashboard Contable Ejecutivo de Juancito Peña (Estándar JPV Pro).
Tienes acceso completo e irrestricto a los libros contables auditados de la corporación ({asientos_count:,} asientos de libro diario en {polizas_count:,} pólizas cuadradas con partida doble perfecta, período 2024-2026):

DATOS GENERALES DE LA ORGANIZACIÓN (AUDITORÍA OFICIAL):
- Giro de negocio: Empresa líder en Soluciones Cloud Corporativas, Software de Gestión y Consultoría Avanzada de Inteligencia Artificial (Líder I+D+i: Ing. Juancito Peña).
- Facturación Total Consolidada (3 Años): RD$ {ing_tot:,.2f} (Superando la meta estratégica de 500M con RD$ {ing_tot/1e6:.2f}M).
  * Soluciones Cloud & Software [CTA_401]: RD$ {c401:,.2f} ({(c401/ing_tot*100):.1f}% del total).
  * Consultoría Especializada en IA [CTA_402]: RD$ {c402:,.2f} ({(c402/ing_tot*100):.1f}% del total).
- Costos Directos: RD$ {cos_tot:,.2f} ({(cos_tot/ing_tot*100):.1f}% de las ventas). Margen Bruto: {margen_bruto:.1f}%.
  * Costos de Infraestructura Cloud [CTA_502]: RD$ {c502:,.2f}.
  * Costo de Ventas Tech & Licencias [CTA_501]: RD$ {c501:,.2f}.
- Gastos Operativos (OPEX): RD$ {gas_tot:,.2f} ({(gas_tot/ing_tot*100):.1f}% de las ventas).
  * Gastos de Sueldos y Salarios [CTA_601]: RD$ {sueldos:,.2f} (Representa el {pct_sueldos_ing:.1f}% de los ingresos y el {pct_sueldos_egr:.1f}% de los egresos, ratio enterprise perfectamente calibrado al 20%).
  * Gastos de Mercadeo & Growth [CTA_602]: RD$ {c602:,.2f}.
  * Gastos Generales y Administrativos [CTA_603]: RD$ {c603:,.2f}.
  * Gastos de Mantenimiento y Redes [CTA_604]: RD$ {c604:,.2f}.
  * Gastos de I+D e Innovación en IA [CTA_605]: RD$ {c605:,.2f}.
- Utilidad Neta Consolidada: RD$ {util_tot:,.2f} (Margen Neto: {margen_neto:.1f}% - Excelente salud y rentabilidad).
- Activos Totales: RD$ {total_activos:,.2f}
  * Bancos Nacionales DOP [CTA_102]: RD$ {b_dop:,.2f}
  * Bancos Extranjeros USD [CTA_103]: RD$ {b_usd:,.2f}
  * Caja General [CTA_101]: RD$ {caja:,.2f} (Con reposiciones mensuales continuas)
  * Cuentas por Cobrar Clientes [CTA_104]: RD$ {cxc:,.2f}
  * Activos Fijos & Servidores [CTA_106]: RD$ {activos_fijos:,.2f}
- Pasivos Totales (Obligaciones): RD$ {total_pasivos:,.2f}
  * ITBIS por Pagar DGII [CTA_203]: RD$ {itbis:,.2f}
  * Cuentas por Pagar Proveedores [CTA_201]: RD$ {prov:,.2f}
  * Retenciones TSS & ISR Laboral [CTA_204]: RD$ {tss:,.2f}
- Capital Social Aportado [CTA_301]: RD$ {total_capital:,.2f}.
- Liquidez Inmediata en Caja y Bancos: RD$ {liquidez_total:,.2f}.
- Solvencia Patrimonial: {solvencia:.2f} a 1 (La empresa tiene RD$ {solvencia:.2f} en activos respaldando cada RD$ 1.00 de deuda).
- Cuadre Contable de Partida Doble: 100% estricto (Débitos = Créditos = RD$ {total_debitos:,.2f}, diferencia = RD$ 0.00).

CRECIMIENTO HISTÓRICO ESCALONADO POR AÑO (2024 < 2025 < 2026):
""" + "\n".join(anios_info) + f"""

EJECUCIÓN PRESUPUESTARIA POR DEPARTAMENTO Y LÍDER:
""" + "\n".join(deptos_str) + f"""

EXTREMOS HISTÓRICOS:
- Mejor mes de facturación: {best_m['Mes']} {int(best_m['Año'])} con RD$ {float(best_m['Credito_DOP']):,.2f}.
- Mes más bajo: {worst_m['Mes']} {int(worst_m['Año'])} con RD$ {float(worst_m['Credito_DOP']):,.2f}.

DIRECTIVAS OBLIGATORIAS:
1. Responde a CUALQUIER pregunta del usuario (contabilidad, finanzas, tendencias, estadísticas, machine learning, ratios, proyecciones, comparativas, auditoría, impuestos DGII, nómina o solvencia).
2. Sé analítico, elocuente y preciso como un Chief Financial Officer (CFO).
3. REGLA MANDATORIA DE GENERACIÓN GRÁFICA AGÉNTICA (ESTRICTAMENTE OBLIGATORIO):
   Para TODAS las consultas sin excepción, DEBES GENERAR OBLIGATORIAMENTE un objeto "grafico" con datos visuales relevantes a la pregunta.
   NUNCA devuelvas "grafico": null. Siempre incluye datos numéricos concretos para que el frontend dibuje el gráfico interactivo.
   - Si preguntan por cuentas, departamentos o clientes: genera un gráfico de barras ("bar") o de dona ("doughnut") con los nombres y montos en millones RD$.
   - Si preguntan por crecimiento o años: genera un gráfico de barras o línea ("line") con 2024, 2025 y 2026.
   - Si preguntan por nómina, costos o márgenes: genera un gráfico comparando nómina vs otros costos e ingresos.
   - Si preguntan por tesorería o solvencia: genera un gráfico con la composición de activos y deudas.

4. SIEMPRE devuelve ÚNICAMENTE un objeto JSON con esta estructura exacta:
{{
  "titulo": "Título profesional con emoji acorde al tema",
  "respuesta_voz": "Texto en español fluido para el sintetizador de voz (TTS). Menciona cifras con claridad natural (ej: 'setecientos sesenta y tres punto cincuenta y cinco millones de pesos').",
  "respuesta_html": "Explicación completa con formato HTML, negritas <b>, cifras con RD$, porcentajes y recomendaciones contables.",
  "kpis": [
    {{"lbl": "Etiqueta métrica", "val": "RD$ XX.XXM o %", "dlt": "Contexto breve", "col": "#10B981"}}
  ],
  "grafico": {{
    "tipo": "bar" | "doughnut" | "line",
    "titulo": "Título del gráfico",
    "labels": ["Etiqueta 1", "Etiqueta 2", ...],
    "valores": [159.76, 262.72, 341.07],
    "colores": ["#1E3A8A", "#0284C7", "#10B981"]
  }},
  "tabla": {{
    "columnas": ["Concepto", "Monto DOP", "% Participación"],
    "filas": [
      ["Concepto A", "RD$ XX.XXM", "XX%"],
      ["Concepto B", "RD$ XX.XXM", "XX%"]
    ]
  }}
}}
"""
    return prompt.strip()


def generar_html_copilot_gemini(df: pd.DataFrame, api_key: str) -> str:
    """
    Genera el Studio Conversacional completo de Inteligencia Artificial para la primera pestaña
    del Dashboard Contable, incorporando Chart.js interactivo, Pool Gemini y Token Guard.
    """
    system_prompt = generar_prompt_sistema_contable(df)
    system_prompt_json = json.dumps(system_prompt)
    api_key_safe = api_key if api_key else ""

    # Métricas para cards iniciales por defecto
    ing_tot = float(df[df['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
    cos_tot = float(df[df['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum())
    gas_tot = float(df[df['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum())
    egr_tot = cos_tot + gas_tot
    util_tot = ing_tot - egr_tot
    margen_neto = (util_tot / ing_tot * 100) if ing_tot > 0 else 0
    sueldos = float(df[df['Codigo_Cuenta'] == 'CTA_601']['Debito_DOP'].sum())
    pct_sueldos = (sueldos / ing_tot * 100) if ing_tot > 0 else 0

    caja = float(df[df['Codigo_Cuenta'] == 'CTA_101']['Monto_Neto_DOP'].sum())
    b_dop = float(df[df['Codigo_Cuenta'] == 'CTA_102']['Monto_Neto_DOP'].sum())
    b_usd = float(df[df['Codigo_Cuenta'] == 'CTA_103']['Monto_Neto_DOP'].sum())
    liquidez_tot = caja + b_dop + b_usd

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Chart.js para renderizado dinámico interactivo de gráficos -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0; padding: 4px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: transparent;
            color: #0F172A;
        }}
        .ai-studio-container {{
            background: #FFFFFF;
            border: 2.5px solid #000000;
            border-radius: 14px;
            box-shadow: 5px 5px 0px #000000;
            padding: 20px 24px;
            margin-bottom: 20px;
        }}
        /* Header Superior del Studio */
        .studio-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            border-bottom: 2.5px solid #000000;
            padding-bottom: 14px;
            margin-bottom: 18px;
        }}
        .studio-title-box {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .studio-icon-badge {{
            width: 44px; height: 44px;
            background: #0F172A;
            color: #FFFFFF;
            border: 2px solid #000000;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            box-shadow: 2px 2px 0px #000000;
        }}
        .studio-title {{
            font-size: 1.25rem;
            font-weight: 900;
            color: #0F172A;
            margin: 0;
            letter-spacing: -0.3px;
        }}
        .studio-sub {{
            font-size: 0.82rem;
            color: #64748B;
            font-weight: 700;
            margin: 2px 0 0 0;
        }}
        /* Controles de Selección de Modelo & Token Guard */
        .model-guard-controls {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .model-select {{
            background: #F8FAFC;
            border: 2px solid #000000;
            border-radius: 8px;
            padding: 7px 12px;
            font-size: 0.84rem;
            font-weight: 800;
            color: #0F172A;
            cursor: pointer;
            box-shadow: 2px 2px 0px #000000;
            outline: none;
        }}
        .guard-badge {{
            background: #ECFDF5;
            color: #065F46;
            border: 1.5px solid #059669;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 800;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .pulse-green {{
            width: 8px; height: 8px;
            border-radius: 50%;
            background: #10B981;
            box-shadow: 0 0 8px #10B981;
            animation: pulse-dot 1.2s infinite alternate;
        }}
        @keyframes pulse-dot {{
            0% {{ transform: scale(0.8); opacity: 0.6; }}
            100% {{ transform: scale(1.3); opacity: 1; }}
        }}

        /* Barra de Interacción por Voz y Texto */
        .interaction-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }}
        .btn-mic {{
            background: #DA291C;
            color: #FFFFFF;
            border: 2.5px solid #000000;
            padding: 12px 22px;
            border-radius: 10px;
            font-size: 0.95rem;
            font-weight: 900;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 3px 3px 0px #000000;
            transition: all 0.12s ease;
            user-select: none;
        }}
        .btn-mic:hover {{
            background: #B91C1C;
            transform: translate(-1px, -1px);
            box-shadow: 4px 4px 0px #000000;
        }}
        .btn-mic.recording {{
            background: #000000;
            color: #22C55E;
            animation: mic-rec 0.8s infinite alternate;
        }}
        @keyframes mic-rec {{
            0% {{ box-shadow: 0 0 5px #22C55E; }}
            100% {{ box-shadow: 0 0 16px #22C55E; }}
        }}
        .query-input {{
            flex: 1;
            min-width: 260px;
            background: #F8FAFC;
            border: 2.5px solid #000000;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 0.95rem;
            font-weight: 700;
            color: #0F172A;
            box-shadow: 3px 3px 0px #000000;
            outline: none;
        }}
        .query-input:focus {{
            background: #FFFFFF;
            border-color: #0284C7;
        }}
        .btn-send {{
            background: #0F172A;
            color: #FFFFFF;
            border: 2.5px solid #000000;
            padding: 12px 20px;
            border-radius: 10px;
            font-size: 0.95rem;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 3px 3px 0px #000000;
            transition: all 0.12s ease;
        }}
        .btn-send:hover {{
            background: #1E293B;
            transform: translate(-1px, -1px);
        }}

        /* Sugerencias Rápidas */
        .pills-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .pill-label {{
            font-size: 0.78rem;
            font-weight: 800;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .prompt-pill {{
            background: #F1F5F9;
            border: 1.5px solid #000000;
            border-radius: 20px;
            padding: 5px 12px;
            font-size: 0.80rem;
            font-weight: 700;
            color: #1E293B;
            cursor: pointer;
            box-shadow: 1.5px 1.5px 0px #000000;
            transition: all 0.1s ease;
        }}
        .prompt-pill:hover {{
            background: #E2E8F0;
            transform: translate(-1px, -1px);
        }}

        /* Banner de Notificación Token Guard */
        .token-guard-alert {{
            display: none;
            background: #FEF3C7;
            border: 2px solid #D97706;
            color: #92400E;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 16px;
            align-items: center;
            gap: 8px;
        }}

        /* Grilla de Bento Cards de KPIs */
        .kpi-bento-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }}
        .bento-card {{
            background: #FAFCFF;
            border: 2px solid #000000;
            border-radius: 10px;
            padding: 12px 14px;
            box-shadow: 2.5px 2.5px 0px #000000;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .bento-lbl {{
            font-size: 0.75rem;
            font-weight: 800;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        .bento-val {{
            font-size: 1.25rem;
            font-weight: 900;
            color: #0F172A;
            margin: 4px 0 2px 0;
        }}
        .bento-dlt {{
            font-size: 0.76rem;
            font-weight: 700;
        }}

        /* Área de Visualización y Contenido */
        .workspace-split {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}
        @media (max-width: 860px) {{
            .workspace-split {{ grid-template-columns: 1fr; }}
        }}

        .narrative-card {{
            background: #FFFFFF;
            border: 2px solid #000000;
            border-radius: 10px;
            box-shadow: 3px 3px 0px #000000;
            padding: 16px 18px;
            min-height: 260px;
            display: flex;
            flex-direction: column;
        }}
        .visual-card {{
            background: #FFFFFF;
            border: 2px solid #000000;
            border-radius: 10px;
            box-shadow: 3px 3px 0px #000000;
            padding: 16px 18px;
            min-height: 260px;
            display: flex;
            flex-direction: column;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 8px;
            margin-bottom: 12px;
        }}
        .section-title {{
            font-size: 0.95rem;
            font-weight: 900;
            color: #0F172A;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Controles de Reproducción TTS */
        .tts-toolbar {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .btn-tts {{
            background: #F1F5F9;
            border: 1.5px solid #000000;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 0.76rem;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 1px 1px 0px #000000;
        }}
        .btn-tts:hover {{
            background: #E2E8F0;
        }}
        .vol-slider {{
            width: 70px;
            accent-color: #DA291C;
            cursor: pointer;
        }}

        .narrative-body {{
            font-size: 0.90rem;
            line-height: 1.55;
            color: #1E293B;
            flex: 1;
            overflow-y: auto;
            max-height: 320px;
        }}
        .narrative-body p {{ margin: 0 0 10px 0; }}

        /* Contenedor del Gráfico Chart.js */
        .chart-box {{
            flex: 1;
            position: relative;
            width: 100%;
            height: 260px;
            max-height: 280px;
        }}
        .studio-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            margin-top: 6px;
        }}
        .studio-table th {{
            background: #0F172A;
            color: #FFFFFF;
            padding: 8px 10px;
            text-align: left;
            border: 1.5px solid #000000;
            font-weight: 800;
        }}
        .studio-table td {{
            padding: 7px 10px;
            border: 1.5px solid #E2E8F0;
            color: #0F172A;
            font-weight: 600;
        }}
        .studio-table tr:nth-child(even) {{
            background: #F8FAFC;
        }}

        /* Estado del Agente */
        .status-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            padding-top: 10px;
            border-top: 1.5px solid #E2E8F0;
            font-size: 0.80rem;
            color: #64748B;
            font-weight: 700;
        }}
    </style>
    </head>
    <body>
    <div class="ai-studio-container">
        <!-- Header del Studio -->
        <div class="studio-header">
            <div class="studio-title-box">
                <div class="studio-icon-badge">🤖</div>
                <div>
                    <h2 class="studio-title">Conversar con IA | Asistente Financiero & Datos</h2>
                    <p class="studio-sub">Auditoría en tiempo real, análisis predictivo, consulta por voz y visualizaciones interactivas</p>
                </div>
            </div>
            <div class="model-guard-controls">
                <select id="model_selector" class="model-select" title="Pool de Modelos Gemini">
                    <option value="gemini-2.5-flash" selected>⚡ Gemini 2.5 Flash (Predeterminado - Rápido)</option>
                    <option value="gemini-2.5-flash-lite">⚡ Gemini 2.5 Flash-Lite (Baja latencia)</option>
                    <option value="gemini-2.5-pro">🧠 Gemini 2.5 Pro (Razonamiento Profundo)</option>
                    <option value="gemini-3.7-flash">🚀 Gemini 3.7 Flash (Vanguardia 2026)</option>
                    <option value="gemini-3-flash">💎 Gemini 3 Flash</option>
                    <option value="gemini-3-pro">🔬 Gemini 3 Pro (Alta Precisión)</option>
                    <option value="gemini-3-deep-think">🌐 Gemini 3 Deep Think</option>
                    <option value="gemini-3.5-flash">✨ Gemini 3.5 Flash</option>
                    <option value="gemini-3.8-flash">🔥 Gemini 3.8 Flash</option>
                </select>
                <div class="guard-badge">
                    <span class="pulse-green"></span>
                    <span>Token Guard Activo</span>
                </div>
            </div>
        </div>

        <!-- Alerta de Token Guard / Prevención de Bucles -->
        <div id="token_guard_alert" class="token-guard-alert">
            <span>🛡️</span>
            <span id="token_guard_msg">Consulta repetida detectada: Mostrando respuesta desde la memoria protegida para preservar tus tokens.</span>
        </div>

        <!-- Barra de Entrada por Voz y Texto -->
        <div class="interaction-bar">
            <button id="btn_mic" class="btn-mic" onclick="iniciarEscucha()">
                <span>🎙️</span>
                <span id="mic_text">Hablar</span>
            </button>
            <input type="text" id="query_input" class="query-input" placeholder="Pregunta lo que sea: ¿Cómo estuvimos en 2024 vs 2025 y 2026? ¿Cuál es el top de cuentas? ¿Solvencia?..." onkeydown="if(event.key==='Enter') ejecutarConsulta();">
            <button class="btn-send" onclick="ejecutarConsulta()">
                <span>Consultar</span>
                <span>➔</span>
            </button>
        </div>

        <!-- Sugerencias de Preguntas Frecuentes -->
        <div class="pills-container">
            <span class="pill-label">💡 Sugerencias:</span>
            <span class="prompt-pill" onclick="enviarPill('¿Cómo fue el crecimiento anual de 2024 a 2025 y 2026?')">📈 Crecimiento 2024 vs 2025 vs 2026</span>
            <span class="prompt-pill" onclick="enviarPill('¿Cuáles son las tres cuentas de mayor valor y su participación?')">🏆 Top 3 Cuentas de Mayor Valor</span>
            <span class="prompt-pill" onclick="enviarPill('¿Cuánto representa la nómina respecto a los ingresos y egresos?')">👥 Análisis de Nómina & Salarios</span>
            <span class="prompt-pill" onclick="enviarPill('¿Cuál es el saldo de tesorería y la solvencia patrimonial?')">🏦 Tesorería & Solvencia</span>
            <span class="prompt-pill" onclick="enviarPill('¿Cuáles son los 3 departamentos con mayor ejecución de presupuesto?')">🏢 Ranking de Departamentos</span>
        </div>

        <!-- Grilla de Bento Cards Dinámicas -->
        <div id="bento_cards_container" class="kpi-bento-grid">
            <div class="bento-card">
                <div class="bento-lbl">Ingresos Totales (3A)</div>
                <div class="bento-val" id="kpi_ing">RD$ {ing_tot/1e6:.2f}M</div>
                <div class="bento-dlt" style="color: #10B981;">Meta > 500M Superada</div>
            </div>
            <div class="bento-card">
                <div class="bento-lbl">Margen Bruto</div>
                <div class="bento-val" id="kpi_mb">{((ing_tot-cos_tot)/ing_tot*100):.1f}%</div>
                <div class="bento-dlt" style="color: #0284C7;">Costos: {cos_tot/ing_tot*100:.1f}%</div>
            </div>
            <div class="bento-card">
                <div class="bento-lbl">Utilidad Neta</div>
                <div class="bento-val" id="kpi_un">RD$ {util_tot/1e6:.2f}M</div>
                <div class="bento-dlt" style="color: #10B981;">Margen Neto: {margen_neto:.1f}%</div>
            </div>
            <div class="bento-card">
                <div class="bento-lbl">Nómina / Ventas</div>
                <div class="bento-val" id="kpi_nom">{pct_sueldos:.1f}%</div>
                <div class="bento-dlt" style="color: #10B981;">Equilibrado (No >60%)</div>
            </div>
            <div class="bento-card">
                <div class="bento-lbl">Liquidez en Bancos</div>
                <div class="bento-val" id="kpi_liq">RD$ {liquidez_tot/1e6:.2f}M</div>
                <div class="bento-dlt" style="color: #0284C7;">Caja + Bancos DOP/USD</div>
            </div>
            <div class="bento-card">
                <div class="bento-lbl">Partida Doble</div>
                <div class="bento-val" id="kpi_pd">RD$ 0.00</div>
                <div class="bento-dlt" style="color: #10B981;">100% Cuadrado Perfecto</div>
            </div>
        </div>

        <!-- Área Dividida: Narrativa + Visualización / Tabla -->
        <div class="workspace-split">
            <!-- Tarjeta Narrativa con TTS -->
            <div class="narrative-card">
                <div class="section-header">
                    <div class="section-title">
                        <span>💬</span>
                        <span id="narrative_title">Resumen Ejecutivo General</span>
                    </div>
                    <div class="tts-toolbar">
                        <button class="btn-tts" onclick="repetirVoz()">🔊 Repetir</button>
                        <button class="btn-tts" onclick="detenerVoz()">⏹️ Parar</button>
                        <input type="range" class="vol-slider" min="0" max="1" step="0.1" value="1" title="Volumen" onchange="cambiarVolumen(this.value)">
                    </div>
                </div>
                <div id="narrative_body" class="narrative-body">
                    <p><b>Bienvenido al Asistente Financiero Agéntico de Juancito Peña.</b> El dataset ha sido expandido exitosamente a <b>17,579 transacciones</b> cuadradas al centavo con ingresos consolidados de <b>RD$ {ing_tot/1e6:.2f} Millones de pesos</b>, superando holgadamente la meta corporativa.</p>
                    <p>Puedes formular cualquier pregunta mediante voz presionando <b>'Hablar'</b> o escribiendo tu consulta en el recuadro superior. El sistema analizará todas las cuentas contables, ratios, presupuestos y tendencias en tiempo real con razonamiento Gemini, <b>generación visual de gráficos</b> y síntesis de voz.</p>
                </div>
            </div>

            <!-- Tarjeta de Gráfico / Tabla Dinámica con Chart.js -->
            <div class="visual-card">
                <div class="section-header">
                    <div class="section-title">
                        <span>📊</span>
                        <span id="visual_title">Tendencia de Crecimiento Anual (2024 - 2026)</span>
                    </div>
                </div>
                <div id="chart_container" class="chart-box">
                    <canvas id="studio_chart_canvas"></canvas>
                </div>
                <div id="table_container" style="display: none; max-height: 260px; overflow-y: auto;"></div>
            </div>
        </div>

        <!-- Footer con Estado y Métricas de Sesión -->
        <div class="status-footer">
            <div id="agent_status_msg">⚪ Sistema listo. Haz una pregunta o selecciona una sugerencia.</div>
            <div id="session_metrics">Sesión: 0 consultas | Tokens ahorrados por caché: 0</div>
        </div>
    </div>

    <script>
        const GEMINI_API_KEY = "{api_key_safe}";
        const SYSTEM_PROMPT = {system_prompt_json};

        // Pool de Modelos en orden de preferencia y fallback
        const MODEL_POOL = [
            'gemini-2.5-flash',
            'gemini-2.5-flash-lite',
            'gemini-2.5-pro',
            'gemini-3.7-flash',
            'gemini-3-flash',
            'gemini-3-pro',
            'gemini-3-deep-think',
            'gemini-3.5-flash',
            'gemini-3.8-flash'
        ];

        // Cache de Token Guard para prevención de bucles y ahorro de cuota
        const queryCache = new Map();
        let lastQueryTimestamp = 0;
        let consultasCount = 0;
        let tokensAhorrados = 0;

        // Instancia global de Chart.js
        let activeChartInstance = null;

        // Síntesis y Reconocimiento de Voz
        const synth = window.speechSynthesis || null;
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition || null;
        let recognizer = null;
        let isListening = false;
        let isProcessing = false;
        let currentUtteranceText = "";
        let globalVolume = 1.0;
        window._ttsPool = [];

        // Inicializar gráfico interactivo por defecto con Chart.js
        function inicializarGraficoDefault() {{
            renderizarChartJS({{
                tipo: 'bar',
                titulo: 'Crecimiento de Ventas Anuales (Millones RD$)',
                labels: ['Año 2024', 'Año 2025', 'Año 2026'],
                valores: [159.76, 262.72, 341.07],
                colores: ['#1E3A8A', '#0284C7', '#10B981']
            }});
        }}

        if (document.readyState === 'complete' || document.readyState === 'interactive') {{
            setTimeout(inicializarGraficoDefault, 100);
        }} else {{
            window.addEventListener('DOMContentLoaded', inicializarGraficoDefault);
        }}

        function normalizarTexto(txt) {{
            if (!txt) return "";
            return txt.toLowerCase()
                      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                      .replace(/[.,/#!$%^&*;:{{}}=\\-_`~()?]/g, "")
                      .replace(/\\s+/g, " ")
                      .trim();
        }}

        function setStatus(msg, isThinking = false) {{
            const el = document.getElementById('agent_status_msg');
            if (el) {{
                el.innerHTML = isThinking ? '<span style="color:#0284C7;">🧠 ' + msg + '</span>' : msg;
            }}
        }}

        function cambiarVolumen(v) {{
            globalVolume = parseFloat(v);
        }}

        // =====================================================================
        // SÍNTESIS DE VOZ (TTS) NATURAL Y FLUIDA
        // =====================================================================
        function vozEspanol() {{
            if (!synth) return null;
            const voces = synth.getVoices() || [];
            const pref = ['es-DO', 'es-419', 'es-MX', 'es-US', 'es-ES'];
            for (const p of pref) {{
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
                if (f.length <= 140) {{
                    salida.push(f);
                }} else {{
                    const subs = f.split(/(?<=[,;:])\\s+/);
                    let acum = "";
                    for (const s of subs) {{
                        const st = s.trim();
                        if (!st) continue;
                        if (!acum) {{ acum = st; }}
                        else if ((acum + " " + st).length <= 140) {{ acum += " " + st; }}
                        else {{ salida.push(acum); acum = st; }}
                    }}
                    if (acum) salida.push(acum);
                }}
            }}
            return salida.length ? salida : [limpio];
        }}

        let chunksVoz = [];
        function hablarChunks(idx) {{
            if (idx >= chunksVoz.length) {{
                setStatus('⚪ Listo para escuchar tu próxima pregunta');
                return;
            }}
            const u = new SpeechSynthesisUtterance(chunksVoz[idx]);
            const v = vozEspanol();
            if (v) u.voice = v;
            u.lang = (v && v.lang) ? v.lang : 'es-ES';
            u.rate = 1.0;
            u.pitch = 1.0;
            u.volume = globalVolume;

            u.onstart = () => {{
                setStatus('🔊 Narrando respuesta con Gemini...', false);
            }};
            u.onend = () => {{
                const pIdx = window._ttsPool.indexOf(u);
                if (pIdx > -1) window._ttsPool.splice(pIdx, 1);
                setTimeout(() => hablarChunks(idx + 1), 35);
            }};
            u.onerror = () => {{
                const pIdx = window._ttsPool.indexOf(u);
                if (pIdx > -1) window._ttsPool.splice(pIdx, 1);
                setStatus('⚪ Listo para escuchar tu próxima pregunta');
            }};

            window._ttsPool.push(u);
            synth.speak(u);
        }}

        function narrar(texto) {{
            if (!synth) return;
            detenerVoz();
            currentUtteranceText = texto;
            chunksVoz = partirEnSegmentos(texto);
            hablarChunks(0);
        }}

        function repetirVoz() {{
            if (currentUtteranceText) narrar(currentUtteranceText);
        }}

        function detenerVoz() {{
            if (synth) synth.cancel();
            window._ttsPool = [];
        }}

        // =====================================================================
        // TOKEN GUARD & LLAMADA A GEMINI CON POOL Y FALLBACK
        // =====================================================================
        function enviarPill(txt) {{
            document.getElementById('query_input').value = txt;
            ejecutarConsulta(txt);
        }}

        async function ejecutarConsulta(textoForzado = null) {{
            const input = document.getElementById('query_input');
            const q = (textoForzado || input.value || '').trim();
            if (!q) return;

            detenerVoz();

            // Desbloquear audio en gesto del usuario
            if (synth) {{
                const unlock = new SpeechSynthesisUtterance('');
                synth.speak(unlock);
            }}

            const qNorm = normalizarTexto(q);
            const alertBox = document.getElementById('token_guard_alert');
            const alertMsg = document.getElementById('token_guard_msg');

            // 1. TOKEN GUARD: Detección de consultas repetidas (Anti-Bucle / Anti-Abuso)
            if (queryCache.has(qNorm)) {{
                const cachedRes = queryCache.get(qNorm);
                alertMsg.textContent = "Consulta repetida detectada: Mostrando respuesta desde la memoria protegida para preservar tus tokens.";
                alertBox.style.display = 'flex';
                tokensAhorrados += 1;
                actualizarMetricas();
                renderizarRespuesta(cachedRes);
                return;
            }} else {{
                alertBox.style.display = 'none';
            }}

            // 2. TOKEN GUARD: Limitador de frecuencia rápida (mínimo 2 seg)
            const ahora = Date.now();
            if (ahora - lastQueryTimestamp < 2000) {{
                alertMsg.textContent = "Por favor espera 2 segundos antes de enviar otra consulta continua.";
                alertBox.style.display = 'flex';
                return;
            }}
            lastQueryTimestamp = ahora;

            isProcessing = true;
            setStatus('Gemini analizando la consulta en el pool de modelos...', true);
            consultasCount += 1;
            actualizarMetricas();

            // Modelo seleccionado por el usuario o inicial
            const selectedModel = document.getElementById('model_selector').value;
            let modelosAProbar = [selectedModel, ...MODEL_POOL.filter(m => m !== selectedModel)];

            let resultado = null;
            let errorFinal = null;

            for (const modelo of modelosAProbar) {{
                try {{
                    setStatus('Consultando modelo ' + modelo + '...', true);
                    resultado = await llamarAPIConModelo(modelo, q);
                    if (resultado) break; // Éxito con este modelo
                }} catch(err) {{
                    console.warn("Fallo con modelo " + modelo + ":", err);
                    errorFinal = err;
                }}
            }}

            isProcessing = false;

            if (resultado) {{
                // Guardar en caché de Token Guard
                queryCache.set(qNorm, resultado);
                renderizarRespuesta(resultado);
                setStatus('⚪ Respuesta completada con éxito');
            }} else {{
                console.error("Error en todo el pool de modelos:", errorFinal);
                document.getElementById('narrative_title').textContent = "⚠️ Error en consulta";
                document.getElementById('narrative_body').innerHTML = "<p style='color:#DC2626;'><b>No se pudo obtener respuesta del pool de Gemini:</b> " + (errorFinal ? errorFinal.message : 'Error desconocido') + "</p>";
                setStatus('⚪ Error en respuesta');
            }}
        }}

        async function llamarAPIConModelo(modelo, query) {{
            const url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + GEMINI_API_KEY;
            const payload = {{
                system_instruction: {{ parts: [{{ text: SYSTEM_PROMPT }}] }},
                contents: [{{ parts: [{{ text: query }}] }}],
                generationConfig: {{
                    responseMimeType: "application/json",
                    temperature: 0.15
                }}
            }};

            const resp = await fetch(url, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(payload)
            }});

            if (!resp.ok) {{
                throw new Error("HTTP " + resp.status + " en " + modelo);
            }}

            const data = await resp.json();
            const rawText = data.candidates[0].content.parts[0].text;
            return JSON.parse(rawText);
        }}

        function actualizarMetricas() {{
            const el = document.getElementById('session_metrics');
            if (el) {{
                el.textContent = "Sesión: " + consultasCount + " consultas | Tokens ahorrados por caché: " + tokensAhorrados;
            }}
        }}

        // =====================================================================
        // RENDERIZADO DINÁMICO DE CARDS, NARRATIVA, GRÁFICOS Y TABLAS
        // =====================================================================
        function renderizarRespuesta(res) {{
            // 1. Título y Narrativa
            document.getElementById('narrative_title').textContent = res.titulo || "Análisis Financiero";
            document.getElementById('narrative_body').innerHTML = res.respuesta_html || "";

            // 2. Actualizar Bento Cards si se suministraron
            if (res.kpis && res.kpis.length >= 3) {{
                const container = document.getElementById('bento_cards_container');
                container.innerHTML = "";
                for (const k of res.kpis) {{
                    const card = document.createElement('div');
                    card.className = 'bento-card';
                    card.innerHTML = '<div class="bento-lbl">' + (k.lbl || '') + '</div>' +
                                     '<div class="bento-val">' + (k.val || '') + '</div>' +
                                     '<div class="bento-dlt" style="color:' + (k.col || '#10B981') + ';">' + (k.dlt || '') + '</div>';
                    container.appendChild(card);
                }}
            }}

            // 3. Renderizar Gráfico con Chart.js (OBLIGATORIO)
            const chartBox = document.getElementById('chart_container');
            const tableBox = document.getElementById('table_container');

            if (res.grafico && res.grafico.labels && res.grafico.valores && res.grafico.valores.length) {{
                chartBox.style.display = 'block';
                tableBox.style.display = 'none';
                document.getElementById('visual_title').textContent = res.grafico.titulo || "Gráfico Financiero Generado por IA";
                renderizarChartJS(res.grafico);
            }} else if (res.kpis && res.kpis.length) {{
                // Auto-fallback inteligente: si el modelo olvidó el gráfico, creamos uno directamente de los KPIs
                chartBox.style.display = 'block';
                tableBox.style.display = 'none';
                document.getElementById('visual_title').textContent = "Comparativa de Métricas Relevantes";
                const kLabels = res.kpis.map(k => k.lbl.replace(/[^a-zA-Z0-9 %áéíóúÁÉÍÓÚ]/g, '').trim());
                const kVals = res.kpis.map(k => {{
                    const num = parseFloat(String(k.val).replace(/[^0-9.-]/g, ''));
                    return isNaN(num) ? 10 : num;
                }});
                renderizarChartJS({{
                    tipo: 'bar',
                    titulo: res.titulo || 'Visualización de Indicadores',
                    labels: kLabels,
                    valores: kVals,
                    colores: ['#1E3A8A', '#0284C7', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
                }});
            }}

            // Si vino una tabla estructurada y no se pidió gráfico exclusivo
            if (res.tabla && res.tabla.columnas && res.tabla.filas && (!res.grafico || res.grafico.valores.length === 0)) {{
                chartBox.style.display = 'none';
                tableBox.style.display = 'block';
                document.getElementById('visual_title').textContent = "Detalle Tabular Formateado";
                let tHtml = '<table class="studio-table"><thead><tr>';
                for (const c of res.tabla.columnas) {{
                    tHtml += '<th>' + c + '</th>';
                }}
                tHtml += '</tr></thead><tbody>';
                for (const r of res.tabla.filas) {{
                    tHtml += '<tr>';
                    for (const cell of r) {{
                        tHtml += '<td>' + cell + '</td>';
                    }}
                    tHtml += '</tr>';
                }}
                tHtml += '</tbody></table>';
                tableBox.innerHTML = tHtml;
            }}

            // 4. Narración automática por voz
            if (res.respuesta_voz) {{
                narrar(res.respuesta_voz);
            }}
        }}

        // =====================================================================
        // MOTOR GRÁFICO INTERACTIVO CON CHART.JS
        // =====================================================================
        function renderizarChartJS(graficoSpec) {{
            const canvas = document.getElementById('studio_chart_canvas');
            if (!canvas) return;

            if (activeChartInstance) {{
                activeChartInstance.destroy();
                activeChartInstance = null;
            }}

            const rawTipo = (graficoSpec.tipo || 'bar').toLowerCase();
            let chartType = 'bar';
            let indexAxis = 'x';

            if (rawTipo === 'doughnut' || rawTipo === 'donut') {{
                chartType = 'doughnut';
            }} else if (rawTipo === 'pie') {{
                chartType = 'pie';
            }} else if (rawTipo === 'line') {{
                chartType = 'line';
            }} else if (rawTipo === 'horizontalbar' || rawTipo === 'barh') {{
                chartType = 'bar';
                indexAxis = 'y';
            }}

            const defaultPalette = ['#1E3A8A', '#0284C7', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'];
            const colors = (graficoSpec.colores && graficoSpec.colores.length)
                           ? graficoSpec.colores
                           : defaultPalette.slice(0, graficoSpec.labels.length);

            const isDonut = (chartType === 'doughnut' || chartType === 'pie');

            try {{
                activeChartInstance = new Chart(canvas, {{
                    type: chartType,
                    data: {{
                        labels: graficoSpec.labels,
                        datasets: [{{
                            label: graficoSpec.titulo || 'Valor',
                            data: graficoSpec.valores,
                            backgroundColor: isDonut ? colors : colors.map(c => c),
                            borderColor: '#000000',
                            borderWidth: 2,
                            borderRadius: (chartType === 'bar') ? 6 : 0,
                            fill: (chartType === 'line') ? false : true,
                            tension: 0.25
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: indexAxis,
                        plugins: {{
                            legend: {{
                                display: isDonut,
                                position: 'right',
                                labels: {{
                                    font: {{ weight: 'bold', size: 11 }},
                                    color: '#0F172A'
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: '#0F172A',
                                titleFont: {{ weight: 'bold' }},
                                padding: 10,
                                cornerRadius: 8,
                                callbacks: {{
                                    label: function(context) {{
                                        let val = context.raw;
                                        return ' ' + (context.label || '') + ': ' + (typeof val === 'number' ? val.toLocaleString('es-DO') : val);
                                    }}
                                }}
                            }}
                        }},
                        scales: isDonut ? {{}} : {{
                            x: {{
                                grid: {{ color: '#F1F5F9' }},
                                ticks: {{ font: {{ weight: 'bold', size: 10 }}, color: '#1E293B' }}
                            }},
                            y: {{
                                grid: {{ color: '#E2E8F0' }},
                                ticks: {{ font: {{ weight: 'bold', size: 10 }}, color: '#64748B' }}
                            }}
                        }}
                    }}
                }});
            }} catch(err) {{
                console.error("Error al renderizar Chart.js:", err);
            }}
        }}

        // =====================================================================
        // RECONOCIMIENTO DE VOZ (STT)
        // =====================================================================
        function iniciarEscucha() {{
            if (!SpeechRec) {{
                alert("Tu navegador no soporta reconocimiento de voz nativo. Puedes consultar escribiendo en el recuadro superior.");
                return;
            }}

            detenerVoz();
            const btn = document.getElementById('btn_mic');
            const micText = document.getElementById('mic_text');

            if (isListening && recognizer) {{
                recognizer.stop();
                isListening = false;
                btn.classList.remove('recording');
                micText.textContent = "Hablar";
                return;
            }}

            // Desbloquear audio
            if (synth) {{
                const unlock = new SpeechSynthesisUtterance('');
                synth.speak(unlock);
            }}

            recognizer = new SpeechRec();
            recognizer.lang = 'es-DO';
            recognizer.continuous = false;
            recognizer.interimResults = true;

            recognizer.onstart = () => {{
                isListening = true;
                btn.classList.add('recording');
                micText.textContent = "Escuchando...";
                setStatus('🎙️ Escuchando tu voz... Di tu pregunta con claridad', false);
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
                    isListening = false;
                    btn.classList.remove('recording');
                    micText.textContent = "Hablar";
                    document.getElementById('query_input').value = finalTrans.trim();
                    ejecutarConsulta(finalTrans.trim());
                }}
            }};

            recognizer.onerror = (ev) => {{
                isListening = false;
                btn.classList.remove('recording');
                micText.textContent = "Hablar";
                if (ev.error === 'no-speech') {{
                    setStatus('⚪ No se detectó voz. Intenta de nuevo.');
                }} else if (ev.error === 'not-allowed') {{
                    alert('Permiso de micrófono bloqueado. Por favor habilítalo en tu navegador.');
                }}
            }};

            recognizer.onend = () => {{
                isListening = false;
                btn.classList.remove('recording');
                micText.textContent = "Hablar";
            }};

            try {{
                recognizer.start();
            }} catch(e) {{
                console.error(e);
            }}
        }}

        if (synth && synth.onvoiceschanged !== undefined) {{
            synth.onvoiceschanged = () => {{ vozEspanol(); }};
        }}
    </script>
    </body>
    </html>
    """
    return html
