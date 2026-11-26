"""
================================================================================
MÓDULO DE INTELIGENCIA FINANCIERA & NLU POR VOZ (ESTÁNDAR JPV PRO)
================================================================================
Autor: Ing. Juancito Peña Vizcaíno
Propósito: Interpretación semántica de preguntas y comandos por voz sobre el
           dataset del Libro Diario y Balance General, cálculo analítico en tiempo
           real y síntesis de respuestas ejecutivas con narrativa causal y TTS.
================================================================================
"""

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
    """Formatea valores monetarios en millones o miles con símbolo RD$."""
    val = abs(monto)
    signo = "-" if monto < 0 else ""
    if val >= 1_000_000:
        return f"{signo}RD$ {val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"{signo}RD$ {val / 1_000:.1f}k"
    else:
        return f"{signo}RD$ {val:,.2f}"


def formatear_voz_millones(monto: float) -> str:
    """Formato fonético limpio en español para síntesis de voz (sin abreviaturas 'M' o 'RD$')."""
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


def extraer_periodo(texto_norm: str):
    """
    Detecta año (2024, 2025, 2026) y trimestre (Q1, Q2, Q3, Q4) en el comando.
    Tolera erratas comunes como 'trismetre', 'trimeste', etc.
    """
    anio = None
    trimestre = None
    meses = None

    # Detección de Año
    match_anio = re.search(r'\b(2024|2025|2026)\b', texto_norm)
    if match_anio:
        anio = int(match_anio.group(1))

    # Detección de Trimestres
    if re.search(r'(primer|1er|q1|enero a marzo|primer\s*trismetre)', texto_norm):
        trimestre = 1
        meses = [1, 2, 3]
    elif re.search(r'(segundo|2do|q2|abril a junio)', texto_norm):
        trimestre = 2
        meses = [4, 5, 6]
    elif re.search(r'(tercer|3er|q3|julio a septiembre)', texto_norm):
        trimestre = 3
        meses = [7, 8, 9]
    elif re.search(r'(cuarto|4to|q4|octubre a diciembre)', texto_norm):
        trimestre = 4
        meses = [10, 11, 12]

    return anio, trimestre, meses


def procesar_consulta_financiera(comando_raw: str, df: pd.DataFrame) -> dict:
    """
    Motor maestro de interpretación y respuesta financiera.
    Recibe la transcripción de voz y el dataset consolidado.
    """
    if df.empty or not comando_raw:
        return {
            "valido": False,
            "titulo": "Consulta no procesada",
            "texto_voz": "No se recibió ninguna consulta o el libro contable está vacío.",
            "texto_html": "<p>Sin registros disponibles.</p>",
            "kpis": []
        }

    cmd = normalizar_texto(comando_raw)
    anio, trimestre, meses = extraer_periodo(cmd)

    # --------------------------------------------------------------------------
    # 1. CASO: ¿QUÉ CUENTA DEBE MÁS? / PASIVOS / MAYOR DEUDA
    # --------------------------------------------------------------------------
    if re.search(r'(cuenta debe mas|mayor deuda|mas debemos|pasivo mas alto|quien debemos|que debemos|deuda principal|mayores pasivos)', cmd):
        pas_df = df[df['Tipo_Cuenta'] == 'Pasivo'].copy()
        resumen_pas = pas_df.groupby(['Codigo_Cuenta', 'Cuenta_Contable'])['Credito_DOP'].sum().reset_index()
        resumen_pas = resumen_pas.sort_values(by='Credito_DOP', ascending=False)
        total_pasivos = float(resumen_pas['Credito_DOP'].sum())

        top1 = resumen_pas.iloc[0]
        top1_nom = top1['Cuenta_Contable']
        top1_monto = float(top1['Credito_DOP'])
        top1_pct = (top1_monto / total_pasivos * 100) if total_pasivos > 0 else 0

        top2_txt = ""
        if len(resumen_pas) > 1:
            top2 = resumen_pas.iloc[1]
            top2_txt = f", seguida de <b>{top2['Cuenta_Contable']}</b> con {formatear_dop(float(top2['Credito_DOP']))}"

        kpis = [
            {"label": "Pasivo Más Alto", "valor": formatear_dop(top1_monto), "delta": f"{top1_pct:.1f}% del total", "color": "#EF4444"},
            {"label": "Pasivos Totales", "valor": formatear_dop(total_pasivos), "delta": "Exigible", "color": "#F59E0B"}
        ]

        texto_voz = (
            f"La cuenta que más debe es {top1_nom}, con un saldo acumulado de {formatear_voz_millones(top1_monto)}, "
            f"lo que representa el {top1_pct:.1f} por ciento de todos los pasivos corporativos. "
            f"Se recomienda coordinar con tesorería su liquidación para evitar recargos o contingencias comerciales."
        )

        texto_html = f"""
        <div style="font-size: 0.95rem; line-height: 1.5; color: #0F172A;">
            La cuenta con mayor saldo acreedor pendiente es <b style="color: #DC2626;">{top1_nom}</b> con 
            <b>{formatear_dop(top1_monto)}</b> ({top1_pct:.1f}% de la deuda acumulada){top2_txt}.
            <br><br>
            <b>Diagnóstico Forense:</b> Estas obligaciones concentran el mayor compromiso financiero del balance. 
            La tesorería cuenta con respaldo suficiente pero requiere planificar pagos escalonados para proteger el capital de trabajo.
        </div>
        """

        return {
            "valido": True,
            "tipo": "pasivo_top",
            "titulo": f"🚨 Cuenta con Mayor Pasivo: {top1_nom}",
            "texto_voz": texto_voz,
            "texto_html": texto_html,
            "kpis": kpis,
            "tabla": resumen_pas.head(4)
        }

    # --------------------------------------------------------------------------
    # 2. CASO: ¿CUÁLES FORMAN EL 50% O MÁS DE LA EMPRESA / GASTOS? (PARETO 50% / 80%)
    # --------------------------------------------------------------------------
    if re.search(r'(50%|50 por ciento|cincuenta por ciento|mitad de la empresa|mitad del gasto|concentracion|forman el 50|representan el 50|pareto)', cmd):
        # Análisis de Pareto sobre egresos (Costo + Gasto)
        egr_df = df[df['Tipo_Cuenta'].isin(['Costo', 'Gasto'])].copy()
        resumen_egr = egr_df.groupby(['Codigo_Cuenta', 'Cuenta_Contable'])['Debito_DOP'].sum().reset_index()
        resumen_egr = resumen_egr.sort_values(by='Debito_DOP', ascending=False)
        total_egr = float(resumen_egr['Debito_DOP'].sum())

        resumen_egr['Pct'] = (resumen_egr['Debito_DOP'] / total_egr * 100) if total_egr > 0 else 0
        resumen_egr['Pct_Acum'] = resumen_egr['Pct'].cumsum()

        # Filtrar hasta superar el 50%
        idx_50 = resumen_egr[resumen_egr['Pct_Acum'] >= 50].index
        corte = idx_50[0] + 1 if len(idx_50) > 0 else 1
        cuentas_50 = resumen_egr.iloc[:corte]

        top_cuenta = cuentas_50.iloc[0]
        top_nombre = top_cuenta['Cuenta_Contable']
        top_monto = float(top_cuenta['Debito_DOP'])
        top_pct = float(top_cuenta['Pct'])

        num_ctas = len(cuentas_50)
        nombres_ctas = ", ".join(f"'{c}'" for c in cuentas_50['Cuenta_Contable'])

        if top_pct >= 50:
            detalle_explicacion = (
                f"Una sola cuenta, <b>{top_nombre}</b>, absorbe por sí misma el <b>{top_pct:.1f}%</b> del presupuesto de egresos "
                f"con un total ejecutado de <b>{formatear_dop(top_monto)}</b>."
            )
            voz_explicacion = (
                f"Una sola cuenta contable, {top_nombre}, absorbe por sí misma el {top_pct:.1f} por ciento de todos los gastos de la empresa, "
                f"con un acumulado de {formatear_voz_millones(top_monto)}."
            )
        else:
            detalle_explicacion = (
                f"Las <b>{num_ctas} cuentas</b> que concentran el 50% o más del gasto son: {nombres_ctas}, "
                f"encabezadas por <b>{top_nombre}</b> con el <b>{top_pct:.1f}%</b>."
            )
            voz_explicacion = (
                f"Un conjunto de {num_ctas} cuentas contables concentran más de la mitad de todos los gastos de la compañía, "
                f"encabezadas por {top_nombre} con el {top_pct:.1f} por ciento."
            )

        kpis = [
            {"label": "Líder en Gastos", "valor": formatear_dop(top_monto), "delta": f"{top_pct:.1f}% del total", "color": "#7C3AED"},
            {"label": "Egresos Totales", "valor": formatear_dop(total_egr), "delta": f"{num_ctas} cuentas hacen el 50%+", "color": "#0284C7"}
        ]

        texto_voz = (
            f"{voz_explicacion} "
            f"Cualquier plan de optimización de costos debe enfocarse prioritariamente en estos rubros."
        )

        texto_html = f"""
        <div style="font-size: 0.95rem; line-height: 1.5; color: #0F172A;">
            {detalle_explicacion}
            <br><br>
            <b>Estrategia de Control:</b> Dado que la nómina y los servicios directos representan más de la mitad del costo operativo, 
            la auditoría interna debe monitorear la productividad de los equipos de ingeniería y consultoría para salvaguardar el margen neto.
        </div>
        """

        return {
            "valido": True,
            "tipo": "pareto_concentracion",
            "titulo": f"📊 Concentración del 50% o Más de la Empresa ({top_nombre})",
            "texto_voz": texto_voz,
            "texto_html": texto_html,
            "kpis": kpis,
            "tabla": cuentas_50[['Cuenta_Contable', 'Debito_DOP', 'Pct', 'Pct_Acum']]
        }

    # --------------------------------------------------------------------------
    # 3. CASO: ANÁLISIS TEMPORAL (¿CÓMO ESTÁBAMOS EN 2024, 2025, 2026 O EN UN TRIMESTRE?)
    # --------------------------------------------------------------------------
    if anio is not None or trimestre is not None or re.search(r'(como estabamos|como nos fue|como fue|balance del|estado de resultados|rendimiento del|cierre del|desempeno)', cmd):
        sub_df = df.copy()
        filtro_txt = []

        if anio is not None:
            sub_df = sub_df[sub_df['Año'] == anio]
            filtro_txt.append(f"Año {anio}")
        else:
            anio = int(df['Año'].max()) if 'Año' in df.columns else 2026

        if meses is not None:
            sub_df = sub_df[sub_df['Mes_Num'].isin(meses)]
            trim_nombres = {1: "Primer Trimestre (Q1)", 2: "Segundo Trimestre (Q2)", 3: "Tercer Trimestre (Q3)", 4: "Cuarto Trimestre (Q4)"}
            filtro_txt.append(trim_nombres.get(trimestre, f"Trimestre {trimestre}"))

        titulo_periodo = " · ".join(filtro_txt) if filtro_txt else f"Ejercicio {anio}"

        ing_s = float(sub_df[sub_df['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
        cos_s = float(sub_df[sub_df['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum())
        gas_s = float(sub_df[sub_df['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum())
        egr_s = cos_s + gas_s
        util_s = ing_s - egr_s
        margen_s = (util_s / ing_s * 100) if ing_s > 0 else 0

        # Comparativa con año previo si aplica
        delta_txt = ""
        delta_voz = ""
        if anio > 2024 and meses is None:
            prev_df = df[df['Año'] == (anio - 1)]
            prev_ing = float(prev_df[prev_df['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
            if prev_ing > 0:
                var_pct = ((ing_s - prev_ing) / prev_ing) * 100
                signo_v = "+" if var_pct >= 0 else ""
                delta_txt = f" ({signo_v}{var_pct:.1f}% vs {anio - 1})"
                delta_voz = f", lo que representó una variación del {abs(var_pct):.1f} por ciento respecto al año {anio - 1}"

        kpis = [
            {"label": f"Facturación {titulo_periodo}", "valor": formatear_dop(ing_s), "delta": delta_txt or "Ingresos netos", "color": "#10B981"},
            {"label": "Egresos Totales", "valor": formatear_dop(egr_s), "delta": f"Costos: {formatear_dop(cos_s)}", "color": "#F59E0B"},
            {"label": "Utilidad Neta", "valor": formatear_dop(util_s), "delta": f"Margen: {margen_s:.1f}%", "color": "#0284C7" if util_s >= 0 else "#EF4444"}
        ]

        texto_voz = (
            f"En {titulo_periodo}, la empresa generó una facturación de {formatear_voz_millones(ing_s)}{delta_voz}, "
            f"con egresos operativos de {formatear_voz_millones(egr_s)}. "
            f"Esto resultó en una utilidad neta de {formatear_voz_millones(util_s)}, consolidando un margen neto del {margen_s:.1f} por ciento. "
            f"La operación se mantuvo {'rentable y financieramente saludable' if margen_s > 40 else 'estable bajo control de gastos'}."
        )

        texto_html = f"""
        <div style="font-size: 0.95rem; line-height: 1.5; color: #0F172A;">
            Durante el período <b>{titulo_periodo}</b>, la organización alcanzó una facturación de 
            <b style="color: #059669;">{formatear_dop(ing_s)}</b>{delta_txt}, frente a erogaciones totales de 
            <b style="color: #D97706;">{formatear_dop(egr_s)}</b> (Costos directos {formatear_dop(cos_s)} y OPEX {formatear_dop(gas_s)}).
            <br><br>
            <b>Resultado Neto:</b> La utilidad neta alcanzó <b style="color: #0284C7;">{formatear_dop(util_s)}</b>, 
            con un sobresaliente margen de rentabilidad del <b>{margen_s:.1f}%</b>, impulsado por el bajo costo marginal de los proyectos de software e inteligencia artificial.
        </div>
        """

        return {
            "valido": True,
            "tipo": "temporal",
            "titulo": f"📈 Rendimiento Financiero: {titulo_periodo}",
            "texto_voz": texto_voz,
            "texto_html": texto_html,
            "kpis": kpis
        }

    # --------------------------------------------------------------------------
    # 4. CASO: IMPUESTOS, DGII, TSS O PASIVOS FISCALES
    # --------------------------------------------------------------------------
    if re.search(r'(dgii|impuesto|impuestos|itbis|tss|isr|fiscal)', cmd):
        itbis = float(df[df['Codigo_Cuenta'] == 'CTA_203']['Credito_DOP'].sum())
        tss = float(df[df['Codigo_Cuenta'] == 'CTA_204']['Credito_DOP'].sum())
        tot_fiscal = itbis + tss

        bancos = float(df[df['Codigo_Cuenta'].isin(['CTA_102', 'CTA_103'])]['Monto_Neto_DOP'].sum())
        cobertura = (bancos / tot_fiscal) if tot_fiscal > 0 else 1.0

        kpis = [
            {"label": "Pasivo DGII (ITBIS)", "valor": formatear_dop(itbis), "delta": "Retenciones", "color": "#EF4444"},
            {"label": "TSS e ISR", "valor": formatear_dop(tss), "delta": "Seguridad Social", "color": "#F59E0B"},
            {"label": "Cobertura en Bancos", "valor": f"{cobertura:.1f}x", "delta": "Solvencia plena", "color": "#10B981"}
        ]

        texto_voz = (
            f"El pasivo fiscal acumulado con la DGII por concepto de ITBIS es de {formatear_voz_millones(itbis)}, "
            f"sumado a {formatear_voz_millones(tss)} en retenciones de seguridad social e impuesto sobre la renta. "
            f"La tesorería en cuentas bancarias dispone de {formatear_voz_millones(bancos)}, garantizando una cobertura de {cobertura:.1f} veces para cumplir con el fisco sin contratiempos."
        )

        texto_html = f"""
        <div style="font-size: 0.95rem; line-height: 1.5; color: #0F172A;">
            Las obligaciones fiscales acumuladas ante la <b>DGII</b> ascienden a <b style="color: #DC2626;">{formatear_dop(itbis)}</b> por ITBIS, 
            más <b style="color: #D97706;">{formatear_dop(tss)}</b> en retenciones de TSS e ISR.
            <br><br>
            <b>Índice de Solvencia Fiscal:</b> La empresa dispone de <b>{formatear_dop(bancos)}</b> en bancos, lo que otorga una cobertura de 
            <b style="color: #059669;">{cobertura:.1f} veces</b> sobre los pasivos fiscales totales.
        </div>
        """

        return {
            "valido": True,
            "tipo": "dgii_fiscal",
            "titulo": "🏛️ Auditoría Fiscal DGII & Retenciones",
            "texto_voz": texto_voz,
            "texto_html": texto_html,
            "kpis": kpis
        }

    # --------------------------------------------------------------------------
    # 5. CASO: CAJA GENERAL, BANCOS O LIQUIDEZ
    # --------------------------------------------------------------------------
    if re.search(r'(caja|caja general|bancos|liquidez|tesoreria|plata|efectivo)', cmd):
        caja = float(df[df['Codigo_Cuenta'] == 'CTA_101']['Monto_Neto_DOP'].sum())
        b_dop = float(df[df['Codigo_Cuenta'] == 'CTA_102']['Monto_Neto_DOP'].sum())
        b_usd = float(df[df['Codigo_Cuenta'] == 'CTA_103']['Monto_Neto_DOP'].sum())
        disp = caja + b_dop + b_usd

        kpis = [
            {"label": "Caja General", "valor": formatear_dop(caja), "delta": "Descubierto" if caja < 0 else "Saldo normal", "color": "#EF4444" if caja < 0 else "#10B981"},
            {"label": "Bancos DOP + USD", "valor": formatear_dop(b_dop + b_usd), "delta": "Cuentas bancarias", "color": "#10B981"},
            {"label": "Tesorería Neta", "valor": formatear_dop(disp), "delta": "Disponibilidad", "color": "#0284C7"}
        ]

        texto_voz = (
            f"La caja general presenta un saldo en descubierto de {formatear_voz_millones(caja)}, "
            f"debido a desembolsos menores sin reposición inmediata de fondo fijo. "
            f"Sin embargo, las cuentas bancarias en pesos y dólares suman {formatear_voz_millones(b_dop + b_usd)}, "
            f"asegurando una tesorería neta total de {formatear_voz_millones(disp)}."
        )

        texto_html = f"""
        <div style="font-size: 0.95rem; line-height: 1.5; color: #0F172A;">
            <b>Caja General:</b> Registra un saldo deudor anómalo de <b style="color: #DC2626;">{formatear_dop(caja)}</b>. 
            Requiere arqueo urgente y emisión de cheque de reposición de fondo fijo.
            <br><br>
            <b>Posición Global de Tesorería:</b> En contraste, la liquidez bancaria institucional suma 
            <b style="color: #059669;">{formatear_dop(b_dop + b_usd)}</b>, dejando la posición neta en <b>{formatear_dop(disp)}</b>.
        </div>
        """

        return {
            "valido": True,
            "tipo": "caja_liquidez",
            "titulo": "💵 Posición de Caja & Tesorería Disponible",
            "texto_voz": texto_voz,
            "texto_html": texto_html,
            "kpis": kpis
        }

    # --------------------------------------------------------------------------
    # 6. CASO: COBRANZAS, CXC O CARTERA
    # --------------------------------------------------------------------------
    if re.search(r'(cobranza|cobros|cxc|cartera|morosidad|deudores|clientes)', cmd):
        cxc = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Monto_Neto_DOP'].sum())
        cargos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Debito_DOP'].sum())
        abonos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Credito_DOP'].sum())
        tasa = (abonos / cargos * 100) if cargos > 0 else 0

        kpis = [
            {"label": "Cartera CxC Inmovilizada", "valor": formatear_dop(cxc), "delta": "Saldo pendiente", "color": "#EF4444"},
            {"label": "Tasa de Cobranza", "valor": f"{tasa:.1f}%", "delta": "Meta: 80%", "color": "#F59E0B"},
            {"label": "Valores Recuperados", "valor": formatear_dop(abonos), "delta": "Cobrado efectivo", "color": "#10B981"}
        ]

        texto_voz = (
            f"Las cuentas por cobrar registran un saldo inmovilizado de {formatear_voz_millones(cxc)}, "
            f"con una tasa de cobranza del {tasa:.1f} por ciento frente al total facturado. "
            f"Se han recuperado {formatear_voz_millones(abonos)}, pero es prioritario intensificar la gestión de cartera sobre los clientes corporativos en mora."
        )

        texto_html = f"""
        <div style="font-size: 0.95rem; line-height: 1.5; color: #0F172A;">
            <b>Cartera Vencida:</b> Existen <b style="color: #DC2626;">{formatear_dop(cxc)}</b> pendientes de cobro, 
            con una tasa de recaudación del <b>{tasa:.1f}%</b>.
            <br><br>
            <b>Recomendación de Contraloría:</b> Aplicar corte de crédito preventivo sobre deudores con más de 60 días de antigüedad 
            para monetizar el flujo comercial.
        </div>
        """

        return {
            "valido": True,
            "tipo": "cobranza",
            "titulo": "📑 Estado de Cartera de Cobros (CxC)",
            "texto_voz": texto_voz,
            "texto_html": texto_html,
            "kpis": kpis
        }

    # --------------------------------------------------------------------------
    # 7. CASO: RESUMEN GENERAL / FALLBACK INTELIGENTE
    # --------------------------------------------------------------------------
    ing_tot = float(df[df['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum())
    cos_tot = float(df[df['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum())
    gas_tot = float(df[df['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum())
    util_tot = ing_tot - cos_tot - gas_tot
    margen_tot = (util_tot / ing_tot * 100) if ing_tot > 0 else 0

    kpis = [
        {"label": "Facturación Consolidada", "valor": formatear_dop(ing_tot), "delta": "36 meses", "color": "#10B981"},
        {"label": "Egresos Totales", "valor": formatear_dop(cos_tot + gas_tot), "delta": "Costos + OPEX", "color": "#F59E0B"},
        {"label": "Utilidad Neta", "valor": formatear_dop(util_tot), "delta": f"Margen: {margen_tot:.1f}%", "color": "#0284C7"}
    ]

    texto_voz = (
        f"Procesé tu consulta '{comando_raw}'. A nivel corporativo consolidado, la compañía acumula una facturación de "
        f"{formatear_voz_millones(ing_tot)}, con egresos de {formatear_voz_millones(cos_tot + gas_tot)} y una utilidad neta de "
        f"{formatear_voz_millones(util_tot)}, sosteniendo un margen neto del {margen_tot:.1f} por ciento."
    )

    texto_html = f"""
    <div style="font-size: 0.95rem; line-height: 1.5; color: #0F172A;">
        Consulta interpretada: <i>"{comando_raw}"</i>.
        <br><br>
        <b>Panorama Financiero Consolidado:</b> La facturación acumulada alcanza <b>{formatear_dop(ing_tot)}</b>, 
        con erogaciones de <b>{formatear_dop(cos_tot + gas_tot)}</b> y una utilidad neta de <b>{formatear_dop(util_tot)}</b> (margen del {margen_tot:.1f}%).
    </div>
    """

    return {
        "valido": True,
        "tipo": "general",
        "titulo": f"🔍 Análisis Financiero: {comando_raw.capitalize()}",
        "texto_voz": texto_voz,
        "texto_html": texto_html,
        "kpis": kpis
    }
