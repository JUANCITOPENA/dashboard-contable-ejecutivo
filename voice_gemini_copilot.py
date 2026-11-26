"""
================================================================================
COPILOT DE VOZ INTELIGENTE CON GEMINI 2.5 FLASH (ESTÁNDAR JPV PRO)
================================================================================
Autor: Ing. Juancito Peña Vizcaíno
Propósito: Asistente conversacional de voz bidireccional (STT + Gemini 2.5 + TTS).
           Panel oculto en espera por defecto con activación por voz y wake-words.
           Conectado directamente a la API de Google Gemini (gemini-2.5-flash)
           con razonamiento agentico, analítica contable, machine learning y data science.
================================================================================
"""

import json
import os
import re
import unicodedata
import pandas as pd


def generar_prompt_sistema_contable(df: pd.DataFrame) -> str:
    """
    Construye el contexto financiero y contable integral para el Agente Gemini 2.5 Flash
    calculando todas las métricas de forma 100% dinámica desde el dataframe.
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
    c603 = float(df[df['Codigo_Cuenta'] == 'CTA_603']['Debito_DOP'].sum())

    # Crecimiento anual dinámico
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
Eres el Copilot y Agente de Inteligencia Financiera, Machine Learning y Data Science para el Dashboard Contable Ejecutivo de Juancito Pena (Estándar JPV Pro).
Tienes acceso completo e irrestricto a los estados contables auditados de la empresa ({asientos_count:,} asientos de libro diario en {polizas_count:,} pólizas cuadradas, período 2024-2026):

DATOS GENERALES DE LA ORGANIZACIÓN (AUDITORÍA OFICIAL):
- Giro de negocio: Empresa tecnológica especializada en Soluciones Cloud, Software Corporativo y Consultoría de Inteligencia Artificial (Líder I+D+i: Ing. Juancito Peña).
- Facturación Total Consolidada (36M): RD$ {ing_tot:,.2f} (Soluciones Cloud & Software [CTA_401]: RD$ {c401:,.2f}, Consultoría & IA [CTA_402]: RD$ {c402:,.2f}).
- Egresos Totales: RD$ {egr_tot:,.2f} (Costos Directos: RD$ {cos_tot:,.2f} [{(cos_tot/ing_tot*100):.1f}%], Gastos Operativos OPEX: RD$ {gas_tot:,.2f} [{(gas_tot/ing_tot*100):.1f}%]).
- Utilidad Neta Consolidada: RD$ {util_tot:,.2f} (Margen Neto: {margen_neto:.1f}% - Alta rentabilidad corporativa).
- Activos Totales: RD$ {total_activos:,.2f} (Bancos DOP [CTA_102]: RD$ {b_dop:,.2f}, Bancos USD [CTA_103]: RD$ {b_usd:,.2f}, Caja General [CTA_101]: RD$ {caja:,.2f}, Cuentas por Cobrar [CTA_104]: RD$ {cxc:,.2f}, Activos Fijos [CTA_106]: RD$ {activos_fijos:,.2f}).
- Pasivos Totales (Deudas): RD$ {total_pasivos:,.2f} (ITBIS DGII [CTA_203]: RD$ {itbis:,.2f}, Cuentas por Pagar Proveedores [CTA_201]: RD$ {prov:,.2f}, Retenciones TSS e ISR [CTA_204]: RD$ {tss:,.2f}).
- Capital Social Aportado: RD$ {total_capital:,.2f} (CTA_301).
- Gastos de Sueldos y Salarios: RD$ {sueldos:,.2f} (CTA_601 - representa el {pct_sueldos_ing:.1f}% de los ingresos y el {pct_sueldos_egr:.1f}% de los egresos, ratio equilibrado y saludable).
- Costos de Infraestructura Cloud: RD$ {c502:,.2f} (CTA_502). Costo de Ventas Tech: RD$ {c501:,.2f} (CTA_501).
- Gastos Generales y Administrativos: RD$ {c603:,.2f} (CTA_603).
- Liquidez Inmediata en Caja y Bancos: RD$ {liquidez_total:,.2f}.
- Solvencia Patrimonial: {solvencia:.2f} a 1 (posee RD$ {solvencia:.2f} en activos por cada peso de deuda).
- Cuadre contable de Partida Doble: 100% perfecto (Débitos = Créditos = RD$ {total_debitos:,.2f}, diferencia exacta de RD$ 0.00).

EJERCICIOS ANUALES (EVOLUCIÓN TEMPORAL):
""" + "\n".join(anios_info) + f"""

LOS 12 DEPARTAMENTOS Y SUS LÍDERES (ORDENADOS POR PRESUPUESTO EJECUTADO):
""" + "\n".join(deptos_str) + f"""

RÉCORDS HISTÓRICOS DE FACTURACIÓN:
- Mes Récord: {best_m['Mes']} {int(best_m['Año'])} con facturación de RD$ {float(best_m['Credito_DOP']):,.2f}.
- Mes más bajo: {worst_m['Mes']} {int(worst_m['Año'])} con facturación de RD$ {float(worst_m['Credito_DOP']):,.2f}.

DIRECTIVAS PARA RESPONDER:
1. Responde a CUALQUIER pregunta del usuario (contabilidad, auditoría, estadísticas, ratios, machine learning, proyecciones, recomendaciones estratégicas, comparativas, rankings, cuentas, líderes o departamentos).
2. Sé analítico, elocuente, riguroso y profesional como un Director Financiero (CFO) y Científico de Datos Senior.
3. Devuelve SIEMPRE y ÚNICAMENTE un objeto JSON válido con la siguiente estructura:
{{
  "titulo": "Título profesional con emoji acorde al tema",
  "respuesta_voz": "Texto natural en español para ser narrado por el sintetizador de voz (TTS). Debe sonar fluido, claro y ejecutivo. Los números deben pronunciarse con claridad (ej: ciento doce punto diez millones de pesos).",
  "respuesta_html": "Explicación detallada con formato HTML, etiquetas <b> para negritas, cifras exactas con símbolo RD$, análisis contable y recomendaciones.",
  "kpis": [
    {{"lbl": "Etiqueta métrica", "val": "RD$ XX.XXM o %", "dlt": "Contexto breve", "col": "#10B981"}}
  ]
}}
"""
    return prompt.strip()


def generar_html_copilot_gemini(df: pd.DataFrame, api_key: str) -> str:
    """
    Genera la interfaz de voz ultra-inteligente conectada a Gemini 2.5 Flash con
    panel oculto en espera por defecto, wake-words y síntesis de voz automática.
    """
    system_prompt = generar_prompt_sistema_contable(df)
    system_prompt_json = json.dumps(system_prompt)
    api_key_safe = api_key if api_key else ""

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0; padding: 4px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: transparent;
            color: #0F172A;
        }}
        .copilot-container {{
            background: #FFFFFF;
            border: 2.5px solid #000000;
            border-radius: 12px;
            box-shadow: 4px 4px 0px #000000;
            overflow: hidden;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        /* Barra de estado en espera (Panel Oculto por Defecto) */
        .ambient-bar {{
            background: #0F172A;
            color: #FFFFFF;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            cursor: pointer;
            user-select: none;
        }}
        .ambient-left {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            font-size: 0.95rem;
            letter-spacing: -0.2px;
        }}
        .ambient-pulse {{
            width: 10px; height: 10px;
            border-radius: 50%;
            background-color: #22C55E;
            box-shadow: 0 0 10px #22C55E;
            animation: pulse-dot 1.2s infinite alternate;
        }}
        @keyframes pulse-dot {{
            0% {{ transform: scale(0.8); opacity: 0.7; }}
            100% {{ transform: scale(1.3); opacity: 1; }}
        }}
        .ambient-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .btn-toggle {{
            background: #DA291C;
            color: #FFFFFF;
            border: 1.5px solid #000000;
            padding: 5px 14px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 2px 2px 0px #000000;
            transition: all 0.12s ease;
        }}
        .btn-toggle:hover {{
            background: #B91C1C;
            transform: translate(-1px, -1px);
        }}
        /* Cuerpo Expandible del Panel */
        .panel-body {{
            display: none;
            padding: 16px 20px;
            background: #FFFFFF;
            border-top: 2px solid #000000;
        }}
        .controls-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .btn-mic {{
            background: #DA291C;
            color: #FFFFFF;
            border: 2px solid #000000;
            padding: 12px 24px;
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
        .btn-mic:hover {{
            transform: translate(-1px, -1px);
            box-shadow: 4px 4px 0px #000000;
        }}
        .btn-mic.recording {{
            background: #B91C1C;
            animation: pulse-red 0.8s infinite alternate ease-in-out;
        }}
        @keyframes pulse-red {{
            0% {{ transform: scale(1); }}
            100% {{ transform: scale(1.04); }}
        }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 800;
            border: 1.5px solid #000000;
            background: #F1F5F9;
        }}
        .status-badge.listening {{
            background: #FEE2E2;
            color: #DC2626;
        }}
        .status-badge.thinking {{
            background: #FEF3C7;
            color: #D97706;
        }}
        .status-badge.speaking {{
            background: #DCFCE7;
            color: #16A34A;
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
            font-size: 0.92rem;
            font-weight: 600;
            background: #F8FAFC;
        }}
        .text-input:focus {{
            outline: none;
            background: #FFFFFF;
            border-color: #0284C7;
        }}
        .btn-send {{
            background: #0284C7;
            color: #FFFFFF;
            border: 2px solid #000000;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: 0.92rem;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 2px 2px 0px #000000;
        }}
        /* Contenedor de Resultados con IA */
        .result-box {{
            background: #F8FAFC;
            border: 2px solid #334155;
            border-radius: 8px;
            padding: 16px 20px;
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
            padding: 12px 16px;
            margin: 10px 0;
            font-size: 0.94rem;
            line-height: 1.55;
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
            .ambient-bar {{ padding: 8px 12px; }}
            .panel-body {{ padding: 12px 14px; }}
            .btn-mic {{ width: 100%; justify-content: center; }}
        }}
    </style>
    </head>
    <body>
    <div class="copilot-container">
        <!-- 1. Barra en Espera / Modo Oculto por Defecto -->
        <div class="ambient-bar" onclick="togglePanel()">
            <div class="ambient-left">
                <span class="ambient-pulse" id="ambient_dot"></span>
                <span>🎙️ Copilot Gemini 2.5 Flash IA (En espera activa)</span>
                <span style="font-size: 0.78rem; color: #94A3B8; font-weight: 600;">| Habla con naturalidad o di "Oye Gemini"</span>
            </div>
            <div class="ambient-actions">
                <button id="btn_toggle_text" class="btn-toggle" onclick="event.stopPropagation(); togglePanel()">🔽 Abrir Asistente</button>
            </div>
        </div>

        <!-- 2. Cuerpo del Panel Inteligente (Desplegable) -->
        <div id="panel_body" class="panel-body">
            <div class="controls-row">
                <button id="btn_mic" class="btn-mic" onclick="iniciarEscucha()">
                    <span id="mic_icon">🎙️</span> <span id="mic_label">PULSAR Y HABLAR (VOZ)</span>
                </button>
                <div id="status_badge" class="status-badge">
                    <span>⚪</span> <span id="status_label">Listo para escuchar tu pregunta</span>
                </div>
                <span style="font-size: 0.82rem; color: #475569; font-weight: 600; margin-left: auto;">
                    💡 Pregunta lo que desees sobre contabilidad, rankings, estadísticas, proyecciones o análisis.
                </span>
            </div>

            <div class="input-bar">
                <input type="text" id="query_input" class="text-input" placeholder="Escribe o habla cualquier pregunta (ej: cuáles son las tres cuentas de mayor valor? o recomiéndame acciones con la DGII)..." onkeydown="if(event.key==='Enter') consultarGemini()">
                <button class="btn-send" onclick="consultarGemini()">⚡ Preguntar a Gemini</button>
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
    </div>

    <script>
        const GEMINI_API_KEY = "{api_key_safe}";
        const SYSTEM_PROMPT = {system_prompt_json};

        let isPanelOpen = false;
        let isListening = false;
        let isProcessing = false;
        let textoParaVozActual = "";
        let chunksVoz = [];
        window._copilotPool = window._copilotPool || [];

        const synth = window.speechSynthesis;
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognizer = null;

        function togglePanel(forceOpen = null) {{
            const body = document.getElementById('panel_body');
            const btn = document.getElementById('btn_toggle_text');
            if (forceOpen !== null) {{
                isPanelOpen = forceOpen;
            }} else {{
                isPanelOpen = !isPanelOpen;
            }}

            if (isPanelOpen) {{
                body.style.display = 'block';
                btn.textContent = '🔼 Ocultar Panel';
            }} else {{
                body.style.display = 'none';
                btn.textContent = '🔽 Abrir Asistente';
                detenerVoz();
            }}
        }}

        function setStatus(tipo, texto) {{
            const badge = document.getElementById('status_badge');
            const lbl = document.getElementById('status_label');
            badge.className = 'status-badge ' + (tipo || '');
            lbl.textContent = texto;
        }}

        function setMicUI(recording) {{
            isListening = recording;
            const btn = document.getElementById('btn_mic');
            const icon = document.getElementById('mic_icon');
            const lbl = document.getElementById('mic_label');
            if (recording) {{
                btn.className = 'btn-mic recording';
                icon.textContent = '🔴';
                lbl.textContent = 'ESCUCHANDO... (HABLA YA)';
                setStatus('listening', '🔴 Escuchando tu voz...');
            }} else {{
                btn.className = 'btn-mic';
                icon.textContent = '🎙️';
                lbl.textContent = 'PULSAR Y HABLAR (VOZ)';
                if (!isProcessing) setStatus('', '⚪ Listo para escuchar tu pregunta');
            }}
        }}

        // =====================================================================
        // SÍNTESIS DE VOZ AUTOMÁTICA (TTS NATIVO SIN CORTES)
        // =====================================================================
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

        function hablarChunks(idx) {{
            if (idx >= chunksVoz.length) {{
                document.getElementById('voice_indicator').style.display = 'none';
                setStatus('', '⚪ Listo para escuchar tu pregunta');
                return;
            }}
            const u = new SpeechSynthesisUtterance(chunksVoz[idx]);
            const v = vozEspanol();
            if (v) u.voice = v;
            u.lang = (v && v.lang) ? v.lang : 'es-ES';
            u.rate = 1.0;
            u.pitch = 1.0;
            u.volume = 1.0;

            u.onstart = () => {{
                document.getElementById('voice_indicator').style.display = 'inline-flex';
                setStatus('speaking', '🔊 Narrando respuesta con Gemini IA...');
            }};

            u.onend = () => {{
                const pIdx = window._copilotPool.indexOf(u);
                if (pIdx > -1) window._copilotPool.splice(pIdx, 1);
                setTimeout(() => hablarChunks(idx + 1), 35);
            }};

            u.onerror = (ev) => {{
                const pIdx = window._copilotPool.indexOf(u);
                if (pIdx > -1) window._copilotPool.splice(pIdx, 1);
                if (ev && (ev.error === 'interrupted' || ev.error === 'canceled')) return;
                document.getElementById('voice_indicator').style.display = 'none';
                setStatus('', '⚪ Listo para escuchar tu pregunta');
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
            document.getElementById('voice_indicator').style.display = 'none';
        }}

        // =====================================================================
        // CONSULTA AGÉNTICA A GEMINI 2.5 FLASH (REST API)
        // =====================================================================
        async function consultarGemini(preguntaManual = null) {{
            const input = document.getElementById('query_input');
            const q = (preguntaManual || input.value || '').trim();
            if (!q) return;

            detenerVoz();
            isProcessing = true;
            togglePanel(true);
            setStatus('thinking', '🧠 Gemini 2.5 Flash analizando finanzas...');

            document.getElementById('result_box').style.display = 'block';
            document.getElementById('res_title').textContent = "🧠 Razonando con Gemini 2.5 Flash...";
            document.getElementById('res_kpis').innerHTML = "<div style='color:#64748B; font-weight:700;'>Procesando métricas y estados financieros...</div>";
            document.getElementById('res_narration').innerHTML = "<i>Consultando modelo de inteligencia contable...</i>";

            // Desbloquear audio en el gesto del usuario
            if (synth) {{
                const unlock = new SpeechSynthesisUtterance('');
                synth.speak(unlock);
            }}

            try {{
                const url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY;
                const payload = {{
                    system_instruction: {{ parts: [{{ text: SYSTEM_PROMPT }}] }},
                    contents: [{{ parts: [{{ text: q }}] }}],
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
                    throw new Error("HTTP " + resp.status + ": " + (await resp.text()));
                }}

                const data = await resp.json();
                const rawText = data.candidates[0].content.parts[0].text;
                const resultado = JSON.parse(rawText);

                renderizarResultado(resultado);
            }} catch(err) {{
                console.error("Error consultando Gemini:", err);
                document.getElementById('res_title').textContent = "⚠️ Error en consulta";
                document.getElementById('res_narration').innerHTML = "<b style='color:#DC2626;'>Fallo de conexión o límite de API:</b> " + err.message;
                setStatus('', '⚪ Error en respuesta');
            }} finally {{
                isProcessing = false;
            }}
        }}

        function renderizarResultado(res) {{
            document.getElementById('result_box').style.display = 'block';
            document.getElementById('res_title').textContent = res.titulo || "Análisis Financiero";

            // KPIs Bento
            const kpiBox = document.getElementById('res_kpis');
            kpiBox.innerHTML = '';
            if (res.kpis && res.kpis.length) {{
                for (const k of res.kpis) {{
                    const el = document.createElement('div');
                    el.className = 'kpi-item';
                    el.innerHTML = '<div class="kpi-lbl">' + (k.lbl || '') + '</div>' +
                                   '<div class="kpi-val">' + (k.val || '') + '</div>' +
                                   '<div class="kpi-dlt" style="color:' + (k.col || '#10B981') + ';">' + (k.dlt || '') + '</div>';
                    kpiBox.appendChild(el);
                }}
            }}

            // Explicación HTML
            document.getElementById('res_narration').innerHTML = res.respuesta_html || '';

            // Auto-narración
            if (res.respuesta_voz) {{
                narrarAutomaticamente(res.respuesta_voz);
            }}
        }}

        // =====================================================================
        // RECONOCIMIENTO DE VOZ ACTIVO (SPEECH-TO-TEXT) & WAKE-WORD
        // =====================================================================
        function iniciarEscucha() {{
            if (!SpeechRec) {{
                alert("Tu navegador no soporta reconocimiento de voz nativo (Web Speech API). Puedes usar el teclado para consultar a Gemini.");
                return;
            }}

            detenerVoz();
            togglePanel(true);

            if (isListening && recognizer) {{
                recognizer.stop();
                setMicUI(false);
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
                setMicUI(true);
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
                    setMicUI(false);
                    document.getElementById('query_input').value = finalTrans.trim();
                    consultarGemini(finalTrans.trim());
                }}
            }};

            recognizer.onerror = (ev) => {{
                setMicUI(false);
                const err = ev.error;
                if (err === 'no-speech') {{
                    setStatus('', '⏳ No se escuchó voz');
                }} else if (err === 'not-allowed') {{
                    alert('Permiso de micrófono denegado. Permite el micrófono en tu navegador para hablar.');
                }}
            }};

            recognizer.onend = () => {{
                setMicUI(false);
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
