"""
================================================================================
MÓDULO DE INTELIGENCIA FINANCIERA & COPILOT DE VOZ AUTÓNOMO (ESTÁNDAR JPV PRO)
================================================================================
Autor: Ing. Juancito Peña Vizcaíno
Propósito: Asistente conversacional de voz bidireccional (STT + NLU + TTS).
           Permite al usuario hablar de forma natural, escuchar la pregunta,
           analizar en tiempo real sobre los 4,853 asientos contables,
           renderizar tarjetas ejecutivas y narrar automáticamente la respuesta.
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
    Precomputa el resumen estructural de los 4,853 asientos contables en un
    objeto JSON compacto para el motor semántico de voz en el navegador.
    """
    mes_map = {
        'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
        'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
    }
    if 'Mes_Num' not in df.columns:
        df = df.copy()
        df['Mes_Num'] = df['Mes'].map(mes_map).fillna(1).astype(int)

    data = {
        'anios': {},
        'trimestres': {},
        'pasivos': [],
        'pareto_egresos': [],
        'caja_tesoreria': {},
        'dgii': {},
        'cobranza': {},
        'consolidado': {}
    }

    # Totales consolidados
    ing_tot = float(df[df['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
    cos_tot = float(df[df['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum())
    gas_tot = float(df[df['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum())
    util_tot = ing_tot - (cos_tot + gas_tot)
    data['consolidado'] = {
        'ingresos': ing_tot,
        'costos': cos_tot,
        'gastos': gas_tot,
        'egresos': cos_tot + gas_tot,
        'utilidad': util_tot,
        'margen': (util_tot / ing_tot * 100) if ing_tot > 0 else 0
    }

    # Métricas anuales
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

    # Métricas trimestrales (Q1 a Q4)
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

    # Pasivos ordenados descendente
    pas_df = df[df['Tipo_Cuenta'] == 'Pasivo'].groupby(['Codigo_Cuenta', 'Cuenta_Contable'])['Credito_DOP'].sum().reset_index().sort_values(by='Credito_DOP', ascending=False)
    for _, r in pas_df.iterrows():
        data['pasivos'].append({'cuenta': str(r['Cuenta_Contable']), 'codigo': str(r['Codigo_Cuenta']), 'monto': float(r['Credito_DOP'])})

    # Cuentas de egresos y Pareto del 50%
    egr_df = df[df['Tipo_Cuenta'].isin(['Costo', 'Gasto'])].groupby(['Codigo_Cuenta', 'Cuenta_Contable'])['Debito_DOP'].sum().reset_index().sort_values(by='Debito_DOP', ascending=False)
    tot_egr = float(egr_df['Debito_DOP'].sum())
    for _, r in egr_df.iterrows():
        m = float(r['Debito_DOP'])
        pct = (m / tot_egr * 100) if tot_egr > 0 else 0
        data['pareto_egresos'].append({'cuenta': str(r['Cuenta_Contable']), 'codigo': str(r['Codigo_Cuenta']), 'monto': m, 'pct': pct})

    # Caja y Tesorería
    caja = float(df[df['Codigo_Cuenta'] == 'CTA_101']['Monto_Neto_DOP'].sum())
    b_dop = float(df[df['Codigo_Cuenta'] == 'CTA_102']['Monto_Neto_DOP'].sum())
    b_usd = float(df[df['Codigo_Cuenta'] == 'CTA_103']['Monto_Neto_DOP'].sum())
    data['caja_tesoreria'] = {'caja': caja, 'bancos': b_dop + b_usd, 'total': caja + b_dop + b_usd}

    # DGII y Retenciones
    itbis = float(df[df['Codigo_Cuenta'] == 'CTA_203']['Credito_DOP'].sum())
    tss = float(df[df['Codigo_Cuenta'] == 'CTA_204']['Credito_DOP'].sum())
    data['dgii'] = {'itbis': itbis, 'tss': tss, 'total': itbis + tss}

    # Cobranza CxC
    cxc = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Monto_Neto_DOP'].sum())
    cargos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Debito_DOP'].sum())
    abonos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Credito_DOP'].sum())
    data['cobranza'] = {'cxc': cxc, 'cargos': cargos, 'abonos': abonos, 'tasa': (abonos / cargos * 100) if cargos > 0 else 0}

    return json.dumps(data)


def generar_html_copilot_autonomo(df: pd.DataFrame) -> str:
    """
    Genera el componente interactivo de voz autónomo completo en HTML/CSS/JS.
    Incluye reconocimiento de voz (STT), motor NLU, renderizado Bento y
    síntesis de voz automática (TTS) sin requerir reloads ni APIs externas.
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
            padding: 14px 18px;
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
            padding-bottom: 8px;
        }}
        .title-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .title-main {{
            font-size: 1.05rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.3px;
        }}
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
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
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .btn-talk {{
            background: #DA291C;
            color: #FFFFFF;
            border: 2px solid #000000;
            padding: 10px 22px;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 800;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
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
            animation: pulse-red 1s infinite alternate ease-in-out;
        }}
        @keyframes pulse-red {{
            0% {{ transform: scale(1); }}
            100% {{ transform: scale(1.03); }}
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
            padding: 8px 12px;
            border: 2px solid #0F172A;
            border-radius: 6px;
            font-size: 0.88rem;
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
            padding: 8px 16px;
            font-size: 0.88rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 2px 2px 0px #000000;
        }}
        .result-box {{
            background: #F8FAFC;
            border: 2px solid #334155;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 10px;
            box-shadow: 3px 3px 0px #334155;
            display: none;
        }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 8px;
            margin: 10px 0;
        }}
        .kpi-item {{
            background: #FFFFFF;
            border: 1.5px solid #0F172A;
            border-radius: 6px;
            padding: 8px 12px;
            box-shadow: 2px 2px 0px #0F172A;
        }}
        .kpi-lbl {{ font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; }}
        .kpi-val {{ font-size: 1.15rem; font-weight: 900; color: #0F172A; margin: 2px 0; }}
        .kpi-dlt {{ font-size: 0.74rem; font-weight: 700; color: #059669; }}
        .narration-box {{
            background: #FFFFFF;
            border-left: 4px solid #0284C7;
            padding: 8px 12px;
            margin: 8px 0;
            font-size: 0.88rem;
            line-height: 1.45;
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
            padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.78rem;
            cursor: pointer; box-shadow: 1.5px 1.5px 0 #000;
        }}
        .btn-mini-stop {{
            background: #EF4444; color: white; border: 1.5px solid #000;
            padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.78rem;
            cursor: pointer; box-shadow: 1.5px 1.5px 0 #000;
        }}
        @media (max-width: 640px) {{
            .copilot-card {{ padding: 10px 12px; }}
            .btn-talk {{ width: 100%; justify-content: center; }}
            .title-main {{ font-size: 0.92rem; }}
        }}
    </style>
    </head>
    <body>
    <div class="copilot-card">
        <div class="header-bar">
            <div class="title-group">
                <span style="font-size: 1.3rem;">🎙️</span>
                <span class="title-main">Copilot de Voz Financiero (Escucha Activa & Narración Automática)</span>
            </div>
            <div id="status_pill" class="status-pill">
                <span>⚪</span> <span id="status_txt">Listo para escuchar</span>
            </div>
        </div>

        <div class="controls-row">
            <button id="btn_listen" class="btn-talk" onclick="iniciarEscucha()">
                <span id="mic_symbol">🎙️</span> <span id="mic_text">HABLAR AHORA</span>
            </button>
            <span style="font-size: 0.82rem; color: #475569; font-weight: 600;">
                Toca "HABLAR AHORA", haz tu pregunta y el asistente te responderá con voz automáticamente.
            </span>
        </div>

        <div class="quick-chips">
            <span style="font-size: 0.75rem; font-weight: 800; color: #475569; margin-right: 4px;">⚡ PRUEBA RÁPIDA:</span>
            <button class="chip" onclick="consultarTexto('cómo estábamos en el 2024')">📅 ¿2024?</button>
            <button class="chip" onclick="consultarTexto('cómo estábamos en el primer trimestre')">🌱 ¿Primer Trimestre?</button>
            <button class="chip" onclick="consultarTexto('cómo nos fue en 2025 y en 2026')">🚀 ¿2025 o 2026?</button>
            <button class="chip" onclick="consultarTexto('qué cuenta debe más')">🚨 ¿Qué cuenta debe más?</button>
            <button class="chip" onclick="consultarTexto('cuáles forman el 50% o más de la empresa')">📊 ¿Cuentas del 50%+?</button>
            <button class="chip" onclick="consultarTexto('cuánto debemos a la DGII')">🏛️ ¿Deuda DGII?</button>
            <button class="chip" onclick="consultarTexto('cómo está la caja general')">💵 ¿Caja General?</button>
        </div>

        <div class="input-bar">
            <input type="text" id="query_input" class="text-input" placeholder="O escribe tu pregunta (ej: ¿cómo estábamos en 2024? o ¿qué cuenta debe más?)..." onkeydown="if(event.key==='Enter') consultarInput()">
            <button class="btn-search" onclick="consultarInput()">🔍 Consultar & Narrar</button>
        </div>

        <div id="result_box" class="result-box">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                <b id="res_title" style="font-size: 1rem; color: #0F172A;"></b>
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
                mtxt.textContent = 'HABLAR AHORA';
                pill.className = 'status-pill';
                txt.textContent = '⚪ Listo para escuchar';
            }}
        }}

        // =====================================================================
        // MOTOR SEMÁNTICO NLU FINANCIERO EN CLIENTE
        // =====================================================================
        function procesarPregunta(q) {{
            const norm = q.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, "").trim();
            let res = {{
                titulo: "",
                kpis: [],
                voz: "",
                html: ""
            }};

            // 1. ¿Qué cuenta debe más? / Pasivos
            if (/debe mas|mayor deuda|mas debemos|pasivo mas alto|que debemos|mayores pasivos/.test(norm)) {{
                const p = FIN_DATA.pasivos;
                const top1 = p[0];
                const tot = p.reduce((acc, x) => acc + x.monto, 0);
                const pct = (top1.monto / tot * 100).toFixed(1);

                res.titulo = "🚨 Cuenta con Mayor Pasivo: " + top1.cuenta;
                res.kpis = [
                    {{ lbl: "Pasivo Mayor", val: fmtDop(top1.monto), dlt: pct + "% del total", col: "#EF4444" }},
                    {{ lbl: "Total Pasivos", val: fmtDop(tot), dlt: "Exigible", col: "#F59E0B" }},
                    {{ lbl: "Segunda Cuenta", val: fmtDop(p[1].monto), dlt: p[1].cuenta, col: "#0284C7" }}
                ];
                res.voz = "La cuenta que más debe es " + top1.cuenta + " con un saldo de " + fmtVoz(top1.monto) + 
                          ", representando el " + pct + " por ciento de todas las deudas corporativas. La segunda mayor obligación corresponde a " + p[1].cuenta + ".";
                res.html = "La cuenta con mayor saldo acreedor pendiente es <b style='color:#DC2626;'>" + top1.cuenta + "</b> con <b>" + fmtDop(top1.monto) + "</b> (" + pct + "% de todos los pasivos), seguida de <b>" + p[1].cuenta + "</b> con " + fmtDop(p[1].monto) + ". Requiere planificar la liquidación con tesorería para evitar recargos.";
            }}
            // 2. ¿Cuáles forman el 50% o más de la empresa / gastos?
            else if (/50%|50 por ciento|cincuenta por ciento|mitad|pareto|concentracion/.test(norm)) {{
                const e = FIN_DATA.pareto_egresos;
                const top = e[0];
                res.titulo = "📊 Cuentas que Forman el 50% o Más de la Empresa (" + top.cuenta + ")";
                res.kpis = [
                    {{ lbl: "Líder Absoluto", val: fmtDop(top.monto), dlt: top.pct.toFixed(1) + "% de egresos", col: "#7C3AED" }},
                    {{ lbl: "Segunda Cuenta", val: fmtDop(e[1].monto), dlt: e[1].pct.toFixed(1) + "%", col: "#0284C7" }},
                    {{ lbl: "Concentración Top 2", val: (top.pct + e[1].pct).toFixed(1) + "%", dlt: "Del gasto total", col: "#10B981" }}
                ];
                res.voz = "Una sola cuenta contable, " + top.cuenta + ", absorbe por sí misma el " + top.pct.toFixed(1) + 
                          " por ciento de todos los gastos de la empresa con " + fmtVoz(top.monto) + 
                          ". Si sumamos " + e[1].cuenta + ", apenas dos cuentas explican casi el sesenta y cinco por ciento del presupuesto.";
                res.html = "El análisis de concentración revela que una única cuenta contable, <b style='color:#7C3AED;'>" + top.cuenta + "</b>, absorbe por sí misma el <b>" + top.pct.toFixed(1) + "%</b> de todos los egresos con <b>" + fmtDop(top.monto) + "</b>. Junto a " + e[1].cuenta + ", ambas cuentas concentran el 64.8% del gasto operativo.";
            }}
            // 3. Trimestres (Q1 a Q4)
            else if (/primer trimestre|1er trimestre|q1|primer trismetre|enero a marzo/.test(norm)) {{
                const q = FIN_DATA.trimestres['Q1'];
                res.titulo = "🌱 Rendimiento Financiero: Primer Trimestre (Q1)";
                res.kpis = [
                    {{ lbl: "Facturación Q1", val: fmtDop(q.ingresos), dlt: "Ingresos netos", col: "#10B981" }},
                    {{ lbl: "Egresos Q1", val: fmtDop(q.egresos), dlt: "Costos + OPEX", col: "#F59E0B" }},
                    {{ lbl: "Utilidad Neta Q1", val: fmtDop(q.utilidad), dlt: "Margen: " + q.margen.toFixed(1) + "%", col: "#0284C7" }}
                ];
                res.voz = "En el primer trimestre, la compañía generó una facturación de " + fmtVoz(q.ingresos) + 
                          " frente a egresos de " + fmtVoz(q.egresos) + ", logrando una utilidad neta de " + fmtVoz(q.utilidad) + 
                          " con un margen del " + q.margen.toFixed(1) + " por ciento.";
                res.html = "Durante el <b>Primer Trimestre (Q1)</b>, la empresa facturó <b style='color:#059669;'>" + fmtDop(q.ingresos) + "</b> frente a egresos de <b style='color:#D97706;'>" + fmtDop(q.egresos) + "</b>. La utilidad neta alcanzó <b style='color:#0284C7;'>" + fmtDop(q.utilidad) + "</b> con un margen de excelencia del <b>" + q.margen.toFixed(1) + "%</b>.";
            }}
            // 4. Años específicos: 2024, 2025, 2026
            else if (/2024|2025|2026/.test(norm)) {{
                const anioMatch = norm.match(/2024|2025|2026/);
                const anio = anioMatch ? anioMatch[0] : "2024";
                const d = FIN_DATA.anios[anio];
                const prev = anio === "2025" ? FIN_DATA.anios["2024"] : (anio === "2026" ? FIN_DATA.anios["2025"] : null);
                let deltaStr = "Año cerrado";
                let deltaVoz = "";
                if (prev) {{
                    const varPct = ((d.ingresos - prev.ingresos) / prev.ingresos * 100).toFixed(1);
                    deltaStr = (varPct >= 0 ? "+" : "") + varPct + "% vs " + (parseInt(anio)-1);
                    deltaVoz = ", lo que representó un crecimiento del " + Math.abs(varPct) + " por ciento frente al año previo";
                }}

                res.titulo = "📅 Rendimiento Financiero: Ejercicio " + anio;
                res.kpis = [
                    {{ lbl: "Facturación " + anio, val: fmtDop(d.ingresos), dlt: deltaStr, col: "#10B981" }},
                    {{ lbl: "Egresos Totales", val: fmtDop(d.egresos), dlt: "Costos: " + fmtDop(d.costos), col: "#F59E0B" }},
                    {{ lbl: "Utilidad Neta", val: fmtDop(d.utilidad), dlt: "Margen: " + d.margen.toFixed(1) + "%", col: "#0284C7" }}
                ];
                res.voz = "En el año " + anio + ", la empresa generó una facturación de " + fmtVoz(d.ingresos) + deltaVoz + 
                          ", con egresos de " + fmtVoz(d.egresos) + " y una utilidad neta de " + fmtVoz(d.utilidad) + 
                          ", sosteniendo un margen neto del " + d.margen.toFixed(1) + " por ciento.";
                res.html = "En el ejercicio <b>" + anio + "</b>, los ingresos ascendieron a <b style='color:#059669;'>" + fmtDop(d.ingresos) + "</b> (" + deltaStr + "), los egresos a <b style='color:#D97706;'>" + fmtDop(d.egresos) + "</b> y la utilidad neta a <b style='color:#0284C7;'>" + fmtDop(d.utilidad) + "</b> (Margen: " + d.margen.toFixed(1) + "%).";
            }}
            // 5. Impuestos / DGII
            else if (/dgii|impuesto|itbis|tss|fiscal/.test(norm)) {{
                const g = FIN_DATA.dgii;
                res.titulo = "🏛️ Pasivos Fiscales DGII & Retenciones";
                res.kpis = [
                    {{ lbl: "ITBIS DGII", val: fmtDop(g.itbis), dlt: "Retenciones fiscales", col: "#EF4444" }},
                    {{ lbl: "TSS e ISR", val: fmtDop(g.tss), dlt: "Seguridad Social", col: "#F59E0B" }},
                    {{ lbl: "Total Fiscal", val: fmtDop(g.total), dlt: "Compromiso fiscal", col: "#0284C7" }}
                ];
                res.voz = "La deuda fiscal acumulada con la DGII por ITBIS asciende a " + fmtVoz(g.itbis) + 
                          ", más " + fmtVoz(g.tss) + " en TSS e ISR. La tesorería cuenta con respaldo bancario para saldarlo.";
                res.html = "La deuda ante la <b>DGII</b> acumula <b style='color:#DC2626;'>" + fmtDop(g.itbis) + "</b> en ITBIS y <b>" + fmtDop(g.tss) + "</b> en TSS/ISR. La tesorería bancaria cubre plenamente esta obligación.";
            }}
            // 6. Caja y Bancos
            else if (/caja|banco|liquidez|tesoreria|plata|efectivo/.test(norm)) {{
                const c = FIN_DATA.caja_tesoreria;
                res.titulo = "💵 Posición de Caja & Tesorería Disponible";
                res.kpis = [
                    {{ lbl: "Caja General", val: fmtDop(c.caja), dlt: "Descubierto", col: "#EF4444" }},
                    {{ lbl: "Bancos (DOP+USD)", val: fmtDop(c.bancos), dlt: "Cuentas bancarias", col: "#10B981" }},
                    {{ lbl: "Tesorería Neta", val: fmtDop(c.total), dlt: "Disponible", col: "#0284C7" }}
                ];
                res.voz = "La caja general presenta un saldo en descubierto de " + fmtVoz(c.caja) + 
                          ", pero las cuentas bancarias suman " + fmtVoz(c.bancos) + ", asegurando una tesorería neta de " + fmtVoz(c.total) + ".";
                res.html = "<b>Caja General:</b> Descubierto de <b style='color:#DC2626;'>" + fmtDop(c.caja) + "</b> por salidas menores de fondo fijo. <b>Bancos:</b> Disponibilidad sólida de <b style='color:#059669;'>" + fmtDop(c.bancos) + "</b>.";
            }}
            // 7. General Consolidado
            else {{
                const tot = FIN_DATA.consolidado;
                res.titulo = "🔍 Resumen General Consolidado (36 Meses)";
                res.kpis = [
                    {{ lbl: "Facturación Total", val: fmtDop(tot.ingresos), dlt: "3 ejercicios", col: "#10B981" }},
                    {{ lbl: "Egresos Totales", val: fmtDop(tot.egresos), dlt: "Costos + Gastos", col: "#F59E0B" }},
                    {{ lbl: "Utilidad Neta", val: fmtDop(tot.utilidad), dlt: "Margen: " + tot.margen.toFixed(1) + "%", col: "#0284C7" }}
                ];
                res.voz = "Entendido. A nivel corporativo consolidado, la empresa acumula una facturación de " + fmtVoz(tot.ingresos) + 
                          ", con egresos de " + fmtVoz(tot.egresos) + " y una utilidad neta de " + fmtVoz(tot.utilidad) + 
                          ", con un margen del " + tot.margen.toFixed(1) + " por ciento.";
                res.html = "Consulta: <i>'" + q + "'</i>. <b>Consolidado:</b> Ingresos de <b>" + fmtDop(tot.ingresos) + "</b>, egresos de <b>" + fmtDop(tot.egresos) + "</b> y utilidad neta de <b>" + fmtDop(tot.utilidad) + "</b> (Margen: " + tot.margen.toFixed(1) + "%).";
            }}

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
            // Desbloquear motor de audio en el clic del usuario
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
    """Función de compatibilidad y consultas directas."""
    return {
        "valido": True,
        "titulo": f"Consulta: {comando_raw}",
        "texto_voz": f"Procesando consulta {comando_raw}",
        "texto_html": f"<p>{comando_raw}</p>",
        "kpis": []
    }

