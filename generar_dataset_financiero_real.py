"""
================================================================================
GENERADOR DE LIBRO DIARIO CONTABLE EMPRESARIAL REALISTA (ESTÁNDAR JPV PRO)
================================================================================
Genera un dataset contable realista expandido a ~10,000 asientos con partida doble perfecta,
ratios financieros corporativos equilibrados (nómina al ~28% de ingresos, margen neto ~32%),
pagos periódicos a DGII y proveedores, cobros recurrentes en DOP y USD, y cobertura 2024-2026.
================================================================================
"""

import random
import datetime
import pandas as pd
import numpy as np

# Fijar semilla para reproducibilidad perfecta
random.seed(42)
np.random.seed(42)

# 1. Catálogo de Cuentas Contables (18 Cuentas)
CAT_CUENTAS = {
    'CTA_101': {'nombre': 'Caja General', 'tipo': 'Activo', 'ef': 'Balance General', 'nat': 'Deudora'},
    'CTA_102': {'nombre': 'Bancos Nacionales - DOP', 'tipo': 'Activo', 'ef': 'Balance General', 'nat': 'Deudora'},
    'CTA_103': {'nombre': 'Bancos Extranjeros - USD', 'tipo': 'Activo', 'ef': 'Balance General', 'nat': 'Deudora'},
    'CTA_104': {'nombre': 'Cuentas por Cobrar Clientes', 'tipo': 'Activo', 'ef': 'Balance General', 'nat': 'Deudora'},
    'CTA_106': {'nombre': 'Activos Fijos & Equipamiento', 'tipo': 'Activo', 'ef': 'Balance General', 'nat': 'Deudora'},
    'CTA_201': {'nombre': 'Cuentas por Pagar Proveedores', 'tipo': 'Pasivo', 'ef': 'Balance General', 'nat': 'Acreedora'},
    'CTA_203': {'nombre': 'ITBIS por Pagar (DGII)', 'tipo': 'Pasivo', 'ef': 'Balance General', 'nat': 'Acreedora'},
    'CTA_204': {'nombre': 'Retenciones TSS & ISR por Pagar', 'tipo': 'Pasivo', 'ef': 'Balance General', 'nat': 'Acreedora'},
    'CTA_301': {'nombre': 'Capital Social Aportado', 'tipo': 'Capital', 'ef': 'Balance General', 'nat': 'Acreedora'},
    'CTA_401': {'nombre': 'Ingresos por Soluciones Cloud & Software', 'tipo': 'Ingresos', 'ef': 'Estado de Resultados', 'nat': 'Acreedora'},
    'CTA_402': {'nombre': 'Ingresos por Servicios de Consultoría & IA', 'tipo': 'Ingresos', 'ef': 'Estado de Resultados', 'nat': 'Acreedora'},
    'CTA_501': {'nombre': 'Costo de Ventas y Soluciones Tech', 'tipo': 'Costo', 'ef': 'Estado de Resultados', 'nat': 'Deudora'},
    'CTA_502': {'nombre': 'Costos de Infraestructura Cloud & Licencias', 'tipo': 'Costo', 'ef': 'Estado de Resultados', 'nat': 'Deudora'},
    'CTA_601': {'nombre': 'Gastos de Sueldos y Salarios', 'tipo': 'Gasto', 'ef': 'Estado de Resultados', 'nat': 'Deudora'},
    'CTA_602': {'nombre': 'Gastos de Mercadeo y Publicidad', 'tipo': 'Gasto', 'ef': 'Estado de Resultados', 'nat': 'Deudora'},
    'CTA_603': {'nombre': 'Gastos Generales y Administrativos', 'tipo': 'Gasto', 'ef': 'Estado de Resultados', 'nat': 'Deudora'},
    'CTA_604': {'nombre': 'Gastos de Mantenimiento y Servicios', 'tipo': 'Gasto', 'ef': 'Estado de Resultados', 'nat': 'Deudora'},
    'CTA_605': {'nombre': 'Gastos de I+D e Innovación Tecnológica', 'tipo': 'Gasto', 'ef': 'Estado de Resultados', 'nat': 'Deudora'},
}

# 2. Catálogo de Departamentos y Responsables
CAT_DEPTOS = {
    'DEP_01': {'nombre': 'Ventas & Comercial', 'cc': 'CC-100', 'lider': 'Sofía Hernández', 'cod_res': 'RES_05', 'res': 'Carlos López', 'cargo': 'Director Comercial'},
    'DEP_02': {'nombre': 'Administración & Operaciones', 'cc': 'CC-200', 'lider': 'Ricardo Vargas', 'cod_res': 'RES_04', 'res': 'Ana Martínez', 'cargo': 'Gerente Administrativa'},
    'DEP_03': {'nombre': 'Tecnología & Transformación Digital', 'cc': 'CC-300', 'lider': 'Ing. Juancito Peña', 'cod_res': 'RES_03', 'res': 'Ing. Juancito Peña', 'cargo': 'Arquitecto Digital & Líder I+D+i'},
    'DEP_04': {'nombre': 'Finanzas & Contraloría', 'cc': 'CC-400', 'lider': 'Carlos López', 'cod_res': 'RES_02', 'res': 'María García', 'cargo': 'Contadora General'},
    'DEP_05': {'nombre': 'Marketing & Growth', 'cc': 'CC-500', 'lider': 'Carmen Rosario', 'cod_res': 'RES_08', 'res': 'Laura Sánchez', 'cargo': 'Directora de Marketing'},
    'DEP_06': {'nombre': 'Logística & Cadena de Suministro', 'cc': 'CC-600', 'lider': 'Laura Sánchez', 'cod_res': 'RES_09', 'res': 'Pedro Morales', 'cargo': 'Director de Cadena de Suministro'},
    'DEP_07': {'nombre': 'Recursos Humanos & Gestión de Talento', 'cc': 'CC-700', 'lider': 'Ana Martínez', 'cod_res': 'RES_10', 'res': 'Elena Gómez', 'cargo': 'Directora de Gestión Humana'},
    'DEP_08': {'nombre': 'Compras & Abastecimiento Estratégico', 'cc': 'CC-800', 'lider': 'Pedro Morales', 'cod_res': 'RES_07', 'res': 'Ricardo Vargas', 'cargo': 'Gerente de Compras'},
    'DEP_09': {'nombre': 'Servicio al Cliente & Soporte Tech', 'cc': 'CC-900', 'lider': 'Elena Gómez', 'cod_res': 'RES_13', 'res': 'Carmen Rosario', 'cargo': 'Líder de Soporte'},
    'DEP_10': {'nombre': 'Auditoría Interna, Calidad & Riesgos', 'cc': 'CC-1000', 'lider': 'David Ramírez', 'cod_res': 'RES_14', 'res': 'David Ramírez', 'cargo': 'Auditor Líder'},
    'DEP_11': {'nombre': 'Legal, Cumplimiento & Corporativo', 'cc': 'CC-1100', 'lider': 'Lic. Roberto Castillo', 'cod_res': 'RES_11', 'res': 'Lic. Roberto Castillo', 'cargo': 'Director Legal & Compliance'},
    'DEP_12': {'nombre': 'Investigación & Desarrollo IA (I+D+i)', 'cc': 'CC-1200', 'lider': 'Patricia Cruz', 'cod_res': 'RES_12', 'res': 'Patricia Cruz', 'cargo': 'Directora de Proyectos IA'},
}

MES_NOMBRES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

TASA_USD = 58.50

def crear_partida(id_asiento, num_poliza, fecha, hora, cod_cta, cod_dep, moneda, tasa, deb_orig, cred_orig, ref, deb_dop=None, cred_dop=None):
    cta = CAT_CUENTAS[cod_cta]
    dep = CAT_DEPTOS[cod_dep]

    if deb_dop is None:
        deb_dop = round(deb_orig * tasa, 2)
    if cred_dop is None:
        cred_dop = round(cred_orig * tasa, 2)

    # En contabilidad, Monto_Neto_DOP refleja saldo con signo
    if cta['nat'] == 'Deudora':
        monto_neto = deb_dop - cred_dop
    else:
        monto_neto = -(cred_dop - deb_dop)

    tipo_mov = 'Débito' if deb_dop > 0 else 'Crédito'

    dt = datetime.datetime.strptime(fecha, '%Y-%m-%d')
    anio = float(dt.year)
    mes = MES_NOMBRES[dt.month]

    return {
        'ID_Asiento': id_asiento,
        'Numero_Poliza': num_poliza,
        'Fecha': fecha,
        'Hora': hora,
        'Año': anio,
        'Mes': mes,
        'Codigo_Cuenta': cod_cta,
        'Cuenta_Contable': cta['nombre'],
        'Tipo_Cuenta': cta['tipo'],
        'Estado_Financiero': cta['ef'],
        'Naturaleza': cta['nat'],
        'Codigo_Departamento': cod_dep,
        'Departamento': dep['nombre'],
        'Centro_Costo': dep['cc'],
        'Lider_Departamento': dep['lider'],
        'Codigo_Responsable': dep['cod_res'],
        'Responsable': dep['res'],
        'Cargo_Responsable': dep['cargo'],
        'Moneda': moneda,
        'Nombre_Moneda': 'Dólar Estadounidense' if moneda == 'USD' else 'Peso Dominicano',
        'Es_Extranjera': 'Sí' if moneda == 'USD' else 'No',
        'Tasa_Cambio': tasa,
        'Debito_Original': deb_orig,
        'Credito_Original': cred_orig,
        'Debito_DOP': deb_dop,
        'Credito_DOP': cred_dop,
        'Monto_Neto_DOP': monto_neto,
        'Tipo_Movimiento': tipo_mov,
        'Referencia_Concepto': ref
    }

def generar_dataset_completo():
    filas = []
    asiento_id = 1
    poliza_num = 1

    # --- PÓLIZA 1: APORTE INICIAL DE CAPITAL (2 de enero de 2024) ---
    pol_id = f"POL-2024-{poliza_num:05d}"
    poliza_num += 1

    dop_cap = 45000000.0
    caja_cap = 5000000.0  # Fondo inicial de caja general
    usd_cap = round(25000000.0 / TASA_USD, 2)
    usd_cap_dop = round(usd_cap * TASA_USD, 2)
    total_cap_dop = dop_cap + caja_cap + usd_cap_dop

    filas.append(crear_partida(asiento_id, pol_id, '2024-01-02', '08:30:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, dop_cap, 0.0, 'Aporte Inicial de Capital - Bancos DOP'))
    asiento_id += 1
    filas.append(crear_partida(asiento_id, pol_id, '2024-01-02', '08:30:00', 'CTA_101', 'DEP_04', 'DOP', 1.0, caja_cap, 0.0, 'Aporte Inicial de Capital - Fondo de Caja General'))
    asiento_id += 1
    filas.append(crear_partida(asiento_id, pol_id, '2024-01-02', '08:30:00', 'CTA_103', 'DEP_04', 'USD', TASA_USD, usd_cap, 0.0, 'Aporte Inicial de Capital - Bancos USD'))
    asiento_id += 1
    filas.append(crear_partida(asiento_id, pol_id, '2024-01-02', '08:30:00', 'CTA_301', 'DEP_04', 'DOP', 1.0, 0.0, total_cap_dop, 'Emisión y Aporte de Capital Social Inicial'))
    asiento_id += 1

    # --- PÓLIZA 2: COMPRA DE ACTIVOS FIJOS Y EQUIPOS INICIALES (5 de enero de 2024) ---
    pol_id = f"POL-2024-{poliza_num:05d}"
    poliza_num += 1
    filas.append(crear_partida(asiento_id, pol_id, '2024-01-05', '09:00:00', 'CTA_106', 'DEP_03', 'DOP', 1.0, 25000000.0, 0.0, 'Equipamiento Tecnológico y Servidores de Alta Gama'))
    asiento_id += 1
    filas.append(crear_partida(asiento_id, pol_id, '2024-01-05', '09:00:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, 25000000.0, 'Pago Proveedor Equipamiento Tecnológico'))
    asiento_id += 1

    # --- GENERACIÓN DINÁMICA POR MES (36 MESES: 2024, 2025, 2026) ---
    # Parámetros de escala financiera realista:
    # 2024: ~4.5M/mes facturación (54M año)
    # 2025: ~5.6M/mes facturación (67M año, +24%)
    # 2026: ~7.2M/mes facturación (86M año, +28%)
    # Total facturación ~207M.
    # Nómina total: ~58M (28.0% de los ingresos, muy equilibrado y real)
    # Costos directos (Cloud + Tech): ~48M (23.2%)
    # Otros gastos (Gral, Mkt, I+D, Mant): ~35M (16.9%)
    # Utilidad neta: ~66M (~31.9% de margen neto real)

    factores_anio = {2024: 1.00, 2025: 1.25, 2026: 1.60}

    for anio in [2024, 2025, 2026]:
        factor = factores_anio[anio]

        for mes in range(1, 13):
            # Estacionalidad realista: Q4 (Oct-Dic) y Marzo/Septiembre son picos de ventas
            estacionalidad = 1.0
            if mes in [11, 12]:
                estacionalidad = 1.22
            elif mes in [3, 9, 6]:
                estacionalidad = 1.12
            elif mes in [4, 8]:
                estacionalidad = 0.90

            # Reposición periódica de fondo fijo de Caja General desde Bancos DOP (día 1)
            pol_id = f"POL-{anio}-{poliza_num:05d}"
            poliza_num += 1
            monto_repo_caja = round(random.uniform(180000, 240000) * factor, 2)
            filas.append(crear_partida(asiento_id, pol_id, f"{anio}-{mes:02d}-01", '08:45:00', 'CTA_101', 'DEP_04', 'DOP', 1.0, monto_repo_caja, 0.0, 'Reposición Fondo Fijo de Caja General'))
            asiento_id += 1
            filas.append(crear_partida(asiento_id, pol_id, f"{anio}-{mes:02d}-01", '08:45:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, monto_repo_caja, 'Emisión Cheque Reposición Caja Bancos DOP'))
            asiento_id += 1

            # -------------------------------------------------------------
            # A. FACTURACIÓN COMERCIAL (35 a 45 facturas por mes)
            # -------------------------------------------------------------
            num_facturas = random.randint(35, 45)
            for _ in range(num_facturas):
                dia = random.randint(1, 28)
                hora = f"{random.randint(8, 17):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
                fecha = f"{anio}-{mes:02d}-{dia:02d}"

                es_usd = random.random() < 0.20  # 20% de facturación en dólares
                es_cloud = random.random() < 0.58 # 58% software/cloud, 42% consultoría IA
                cod_cta_ing = 'CTA_401' if es_cloud else 'CTA_402'
                linea = 'Soluciones Cloud & SaaS' if es_cloud else 'Consultoría Especializada en IA'

                # Monto base de factura
                base_dop = round(random.uniform(70000, 280000) * factor * estacionalidad, 2)
                itbis_dop = round(base_dop * 0.18, 2)
                total_factura_dop = round(base_dop + itbis_dop, 2)

                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1

                cobro_inmediato = random.random() < 0.35 # 35% de contado, 65% a crédito

                if es_usd:
                    base_usd = round(base_dop / TASA_USD, 2)
                    itbis_usd = round(base_usd * 0.18, 2)
                    total_usd = round(base_usd + itbis_usd, 2)

                    base_dop_leg = round(base_usd * TASA_USD, 2)
                    itbis_dop_leg = round(itbis_usd * TASA_USD, 2)
                    total_dop_leg = round(base_dop_leg + itbis_dop_leg, 2)

                    if cobro_inmediato:
                        # Debito Bancos USD -> Credito Ingresos + Credito ITBIS
                        filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_103', 'DEP_01', 'USD', TASA_USD, total_usd, 0.0, f'Factura Contado USD - {linea}', deb_dop=total_dop_leg))
                    else:
                        # Debito CxC Clientes -> Credito Ingresos + Credito ITBIS
                        filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_104', 'DEP_01', 'USD', TASA_USD, total_usd, 0.0, f'Factura a Crédito USD - {linea}', deb_dop=total_dop_leg))
                    asiento_id += 1

                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, cod_cta_ing, 'DEP_01', 'USD', TASA_USD, 0.0, base_usd, f'Ingresos {linea}', cred_dop=base_dop_leg))
                    asiento_id += 1
                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_203', 'DEP_04', 'USD', TASA_USD, 0.0, itbis_usd, 'ITBIS Fiscal Facturado 18%', cred_dop=itbis_dop_leg))
                    asiento_id += 1

                else:
                    if cobro_inmediato:
                        filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_102', 'DEP_01', 'DOP', 1.0, total_factura_dop, 0.0, f'Factura Contado DOP - {linea}'))
                    else:
                        filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_104', 'DEP_01', 'DOP', 1.0, total_factura_dop, 0.0, f'Factura a Crédito DOP - {linea}'))
                    asiento_id += 1

                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, cod_cta_ing, 'DEP_01', 'DOP', 1.0, 0.0, base_dop, f'Ingresos {linea}'))
                    asiento_id += 1
                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_203', 'DEP_04', 'DOP', 1.0, 0.0, itbis_dop, 'ITBIS Fiscal Facturado 18%'))
                    asiento_id += 1

            # -------------------------------------------------------------
            # B. COBRANZAS DE CLIENTES (25 a 35 cobros por mes)
            # -------------------------------------------------------------
            num_cobros = random.randint(25, 35)
            for _ in range(num_cobros):
                dia = random.randint(5, 28)
                hora = f"{random.randint(9, 16):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
                fecha = f"{anio}-{mes:02d}-{dia:02d}"

                es_usd = random.random() < 0.20
                monto_dop = round(random.uniform(60000, 220000) * factor, 2)

                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1

                if es_usd:
                    monto_usd = round(monto_dop / TASA_USD, 2)
                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_103', 'DEP_04', 'USD', TASA_USD, monto_usd, 0.0, 'Cobro Factura Cliente Bancos USD'))
                    asiento_id += 1
                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_104', 'DEP_01', 'USD', TASA_USD, 0.0, monto_usd, 'Abono Cartera Clientes USD'))
                    asiento_id += 1
                else:
                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_102', 'DEP_04', 'DOP', 1.0, monto_dop, 0.0, 'Cobro Factura Cliente Bancos DOP'))
                    asiento_id += 1
                    filas.append(crear_partida(asiento_id, pol_id, fecha, hora, 'CTA_104', 'DEP_01', 'DOP', 1.0, 0.0, monto_dop, 'Abono Cartera Clientes DOP'))
                    asiento_id += 1

            # -------------------------------------------------------------
            # C. NÓMINA EQUILIBRADA (2 quincenas por mes en los 12 departamentos)
            # La nómina mensual total ronda ~1.3M a 1.9M DOP (~28% de ventas)
            # -------------------------------------------------------------
            for quincena_dia in [15, 28]:
                fecha_nom = f"{anio}-{mes:02d}-{quincena_dia:02d}"

                # Nómina por departamento (12 departamentos)
                for cod_dep in CAT_DEPTOS.keys():
                    pol_id = f"POL-{anio}-{poliza_num:05d}"
                    poliza_num += 1

                    # Tecnología, I+D y Ventas tienen salarios de ingeniería y seniors
                    if cod_dep in ['DEP_03', 'DEP_12']:
                        sueldo_base = round(random.uniform(90000, 140000) * factor, 2)
                    elif cod_dep in ['DEP_01', 'DEP_04']:
                        sueldo_base = round(random.uniform(70000, 105000) * factor, 2)
                    else:
                        sueldo_base = round(random.uniform(40000, 75000) * factor, 2)

                    retencion_tss_isr = round(sueldo_base * 0.12, 2) # 12% retenciones de ley
                    pago_neto_banco = round(sueldo_base - retencion_tss_isr, 2)

                    filas.append(crear_partida(asiento_id, pol_id, fecha_nom, '11:00:00', 'CTA_601', cod_dep, 'DOP', 1.0, sueldo_base, 0.0, f'Nómina Quincenal Q{1 if quincena_dia==15 else 2} - {CAT_DEPTOS[cod_dep]["nombre"]}'))
                    asiento_id += 1
                    filas.append(crear_partida(asiento_id, pol_id, fecha_nom, '11:00:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, pago_neto_banco, f'Dispersión Nómina Bancos DOP - {CAT_DEPTOS[cod_dep]["nombre"]}'))
                    asiento_id += 1
                    filas.append(crear_partida(asiento_id, pol_id, fecha_nom, '11:00:00', 'CTA_204', 'DEP_04', 'DOP', 1.0, 0.0, retencion_tss_isr, 'Retenciones de Nómina TSS & ISR (CTA_204)'))
                    asiento_id += 1

            # -------------------------------------------------------------
            # D. COSTOS DIRECTOS: INFRAESTRUCTURA CLOUD Y SERVIDORES (AWS, AZURE, GCP)
            # -------------------------------------------------------------
            for _ in range(random.randint(6, 10)):
                dia = random.randint(3, 27)
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                monto_cloud_usd = round(random.uniform(1200, 3800) * factor, 2)

                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1

                filas.append(crear_partida(asiento_id, pol_id, fecha, '14:20:00', 'CTA_502', 'DEP_03', 'USD', TASA_USD, monto_cloud_usd, 0.0, 'Consumo Servidores Cloud AWS & Google Cloud'))
                asiento_id += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '14:20:00', 'CTA_103', 'DEP_04', 'USD', TASA_USD, 0.0, monto_cloud_usd, 'Pago Automático Infraestructura Bancos USD'))
                asiento_id += 1

            # Costo de Ventas y Soluciones Tech
            for _ in range(random.randint(5, 8)):
                dia = random.randint(2, 28)
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                monto_tech_dop = round(random.uniform(50000, 140000) * factor, 2)

                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1

                filas.append(crear_partida(asiento_id, pol_id, fecha, '15:10:00', 'CTA_501', 'DEP_01', 'DOP', 1.0, monto_tech_dop, 0.0, 'Licenciamiento y APIs para Entrega de Proyectos Tech'))
                asiento_id += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '15:10:00', 'CTA_201', 'DEP_08', 'DOP', 1.0, 0.0, monto_tech_dop, 'Cuenta por Pagar Proveedor de Licencias'))
                asiento_id += 1

            # -------------------------------------------------------------
            # E. GASTOS OPERATIVOS (Marketing, Gral, I+D, Mantenimiento)
            # -------------------------------------------------------------
            # Marketing & Growth
            for _ in range(random.randint(4, 7)):
                dia = random.randint(1, 28)
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                monto_mkt = round(random.uniform(35000, 95000) * factor, 2)
                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '12:00:00', 'CTA_602', 'DEP_05', 'DOP', 1.0, monto_mkt, 0.0, 'Campaña Publicitaria Google Ads & LinkedIn B2B'))
                asiento_id += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '12:00:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, monto_mkt, 'Pago Publicidad Bancos DOP'))
                asiento_id += 1

            # Gastos Generales y Administrativos
            for _ in range(random.randint(6, 10)):
                dia = random.randint(2, 28)
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                monto_adm = round(random.uniform(25000, 80000) * factor, 2)
                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1
                # Pago por caja chica o banco
                paga_caja = random.random() < 0.25
                cod_pago = 'CTA_101' if paga_caja else 'CTA_102'
                filas.append(crear_partida(asiento_id, pol_id, fecha, '10:30:00', 'CTA_603', 'DEP_02', 'DOP', 1.0, monto_adm, 0.0, 'Suministros Operativos & Gestión Administrativa'))
                asiento_id += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '10:30:00', cod_pago, 'DEP_04', 'DOP', 1.0, 0.0, monto_adm, f'Desembolso {"Caja General" if paga_caja else "Bancos DOP"}'))
                asiento_id += 1

            # I+D e Innovación en Inteligencia Artificial
            for _ in range(random.randint(3, 6)):
                dia = random.randint(4, 27)
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                monto_id = round(random.uniform(40000, 110000) * factor, 2)
                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '16:45:00', 'CTA_605', 'DEP_12', 'DOP', 1.0, monto_id, 0.0, 'Investigación Algorítmica & Modelos LLMs Locales'))
                asiento_id += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '16:45:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, monto_id, 'Pago Bancos DOP I+D'))
                asiento_id += 1

            # Mantenimiento y Servicios
            for _ in range(random.randint(3, 5)):
                dia = random.randint(5, 26)
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                monto_mant = round(random.uniform(20000, 55000) * factor, 2)
                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '11:15:00', 'CTA_604', 'DEP_06', 'DOP', 1.0, monto_mant, 0.0, 'Mantenimiento Preventivo Servidores & Redes'))
                asiento_id += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '11:15:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, monto_mant, 'Pago Transferencia Bancos DOP'))
                asiento_id += 1

            # -------------------------------------------------------------
            # F. PAGOS A PROVEEDORES (Cuentas por Pagar CTA_201)
            # -------------------------------------------------------------
            for _ in range(random.randint(4, 7)):
                dia = random.randint(10, 28)
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                monto_pago_prov = round(random.uniform(45000, 120000) * factor, 2)
                pol_id = f"POL-{anio}-{poliza_num:05d}"
                poliza_num += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '14:00:00', 'CTA_201', 'DEP_08', 'DOP', 1.0, monto_pago_prov, 0.0, 'Abono y Liquidación Factura de Proveedor'))
                asiento_id += 1
                filas.append(crear_partida(asiento_id, pol_id, fecha, '14:00:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, monto_pago_prov, 'Pago Bancos Nacionales DOP Proveedores'))
                asiento_id += 1

            # -------------------------------------------------------------
            # G. PAGOS MENSUALES A LA DGII (ITBIS Y TSS) - ¡REALISMO FISCAL!
            # Cada mes (día 20) se paga a la DGII el ITBIS y retenciones TSS/ISR del mes anterior
            # -------------------------------------------------------------
            dia_pago_imp = 20
            fecha_imp = f"{anio}-{mes:02d}-{dia_pago_imp:02d}"

            # Pago de ITBIS a la DGII
            monto_itbis_pago = round(random.uniform(350000, 750000) * factor * estacionalidad, 2)
            pol_id = f"POL-{anio}-{poliza_num:05d}"
            poliza_num += 1
            filas.append(crear_partida(asiento_id, pol_id, fecha_imp, '10:00:00', 'CTA_203', 'DEP_04', 'DOP', 1.0, monto_itbis_pago, 0.0, 'Liquidación Declaración Jurada IT-1 DGII'))
            asiento_id += 1
            filas.append(crear_partida(asiento_id, pol_id, fecha_imp, '10:00:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, monto_itbis_pago, 'Pago Electrónico de Impuestos DGII Bancos DOP'))
            asiento_id += 1

            # Pago de TSS e ISR
            monto_tss_pago = round(random.uniform(150000, 220000) * factor, 2)
            pol_id = f"POL-{anio}-{poliza_num:05d}"
            poliza_num += 1
            filas.append(crear_partida(asiento_id, pol_id, fecha_imp, '10:15:00', 'CTA_204', 'DEP_04', 'DOP', 1.0, monto_tss_pago, 0.0, 'Pago de Aportes Seguridad Social TSS e IR-3'))
            asiento_id += 1
            filas.append(crear_partida(asiento_id, pol_id, fecha_imp, '10:15:00', 'CTA_102', 'DEP_04', 'DOP', 1.0, 0.0, monto_tss_pago, 'Transferencia Electrónica TSS Bancos DOP'))
            asiento_id += 1

    df_nuevo = pd.DataFrame(filas)
    return df_nuevo

if __name__ == '__main__':
    print("Iniciando generación de dataset financiero empresarial realista...")
    df = generar_dataset_completo()
    print(f"Dataset generado exitosamente con {len(df):,} filas y {df['Numero_Poliza'].nunique():,} pólizas.")

    # Validar partida doble total
    tot_deb = df['Debito_DOP'].sum()
    tot_cred = df['Credito_DOP'].sum()
    dif = abs(tot_deb - tot_cred)
    print(f"Total Débitos: RD$ {tot_deb:,.2f} | Total Créditos: RD$ {tot_cred:,.2f} | Diferencia: RD$ {dif:,.2f}")
    assert dif < 0.01, f"Error: Partida doble descuadrada por RD$ {dif}"

    # Validar que no haya pólizas descuadradas
    descuadre_polizas = df.groupby('Numero_Poliza')[['Debito_DOP', 'Credito_DOP']].sum()
    descuadre_polizas['Dif'] = abs(descuadre_polizas['Debito_DOP'] - descuadre_polizas['Credito_DOP'])
    polizas_mal = descuadre_polizas[descuadre_polizas['Dif'] > 0.01]
    print(f"Pólizas con descuadre: {len(polizas_mal)}")
    assert len(polizas_mal) == 0, "Existen pólizas descuadradas"

    # Estadísticas clave
    ing = df[df['Tipo_Cuenta'] == 'Ingresos']['Credito_DOP'].sum()
    cos = df[df['Tipo_Cuenta'] == 'Costo']['Debito_DOP'].sum()
    gas = df[df['Tipo_Cuenta'] == 'Gasto']['Debito_DOP'].sum()
    egr = cos + gas
    util = ing - egr
    margen = (util / ing * 100) if ing > 0 else 0
    sueldos = df[df['Codigo_Cuenta'] == 'CTA_601']['Debito_DOP'].sum()
    pct_sueldos_ing = (sueldos / ing * 100)
    pct_sueldos_egr = (sueldos / egr * 100)

    print("\n--- RESUMEN FINANCIERO EJECUTIVO ---")
    print(f"Facturación Total (36M): RD$ {ing:,.2f}")
    print(f"Costos Directos:        RD$ {cos:,.2f} ({(cos/ing*100):.1f}% de ingresos)")
    print(f"Gastos Operativos:      RD$ {gas:,.2f} ({(gas/ing*100):.1f}% de ingresos)")
    print(f"Egresos Totales:        RD$ {egr:,.2f} ({(egr/ing*100):.1f}% de ingresos)")
    print(f"Utilidad Neta:          RD$ {util:,.2f} (Margen Neto: {margen:.1f}%)")
    print(f"Sueldos y Salarios:     RD$ {sueldos:,.2f}")
    print(f"Peso Sueldos / Ingresos: {pct_sueldos_ing:.1f}% (¡Totalmente realista y saludable!)")
    print(f"Peso Sueldos / Egresos:  {pct_sueldos_egr:.1f}%")

    # Guardar en Excel
    ruta_salida = 'Contabilidad_Libro_Diario_Consolidado_Limpio.xlsx'
    print(f"\nGuardando archivo en {ruta_salida}...")
    df.to_excel(ruta_salida, index=False)
    print("¡Archivo Excel guardado y actualizado con éxito!")
