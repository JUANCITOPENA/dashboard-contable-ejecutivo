# 🏛️ Suite Ejecutiva de Inteligencia Financiera & Control Contable
> **Plataforma Integral de Analítica Avanzada, Auditoría Forense, Motor Dual de Temas y Narración por Voz (Estándar JPV Pro)**  
> **Autor:** Ing. Juancito Peña Vizcaíno | Arquitecto Digital & Consultor de Inteligencia Artificial y Datos  
> **Repositorio Oficial:** [https://github.com/JUANCITOPENA/dashboard-contable-ejecutivo](https://github.com/JUANCITOPENA/dashboard-contable-ejecutivo)  
> **Despliegue en Streamlit Cloud:** [https://dashboard-contable-ejecutivo.streamlit.app](https://dashboard-contable-ejecutivo.streamlit.app)  
> **Estado:** 100% Estable, Auditado y en Producción (Noviembre 2026)

---

## 📌 1. Visión General del Proyecto

La **Suite Ejecutiva de Inteligencia Financiera & Control Contable** es una aplicación analítica de alto nivel desarrollada en **Python + Streamlit + Plotly**, concebida específicamente para Comités Ejecutivos, Consejos de Administración, Directores Financieros (CFO) y Auditores Forenses.

A diferencia de los tableros analíticos convencionales que muestran métricas aisladas y estáticas, esta suite integra:
1. **Motor Dual de Temas Dinámico:** Conmutación instantánea entre `☀️ Modo Claro` (blanco corporativo de alto impacto) y `🌙 Modo Oscuro` (medianoche slate de alta fidelidad) mediante control táctil en barra lateral.
2. **Sistema Narrativo de Voz Contextual (Web Speech API - Estándar JPV Pro):** Distribuido en cada panel y sección analítica. Actúa como un **Auditor & Analista Financiero Senior**, explicando las visualizaciones, la composición cromática y, fundamentalmente, **los "Porqués" detrás de los números y riesgos**.
3. **Auditoría Forense en Tiempo Real:** Validación matemática de partida doble y emulación completa de la identidad contable del Balance General (`Activo = Pasivo + Capital + Utilidad Neta`).
4. **Nivelación Geométrica Estricta:** Cuadrículas Bento Grid simétricas donde todos los gráficos que comparten fila mantienen exactamente la misma altura en pantallas de escritorio y se adaptan de forma elástica en dispositivos móviles.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SUITE DE INTELIGENCIA FINANCIERA & CONTROL                      │
│                                                                                        │
│  [Dataset: 4,853 Asientos] ──► [Pipeline ETL & Caché] ──► [Métricas & Ecuación Balance] │
│                                                                   │                    │
│                                ┌──────────────────────────────────┴─────────────────┐  │
│                                ▼                                                    ▼  │
│                   [7 Pestañas Ejecutivas]                             [Motor TTS Voz]   │
│                   - Resumen Ejecutivo (Tab 0)                         - Web Speech API │
│                   - Rentabilidad P&L (Tab 1)                          - Control Slider │
│                   - Eficiencia Depto (Tab 2)                          - Wave-Dots      │
│                   - Auditoría Riesgos (Tab 3)                         - Blindaje Num   │
│                   - Tendencias & Run (Tab 4)                                           │
│                   - Informe Gerencial (Tab 5)                         [Motor Dual UI]  │
│                   - Libro Mayor (Tab 6)                               - Modo Claro ☀️  │
│                                                                       - Modo Oscuro 🌙 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 2. Motor Dual de Temas y Experiencia Visual (Light / Dark Mode)

La suite cuenta con un motor de tokens de diseño centralizado (`THEME`) sincronizado en tiempo real a través de `st.session_state`:

* **☀️ Modo Claro (Corporate Executive):**
  - Fondo de aplicación: `#F4F7FB` (Gris hielo suave de descanso visual).
  - Tarjetas Bento: `#FFFFFF` con sutil borde `#CBD5E1` y elevación suave.
  - Tipografía: Azul medianoche oscuro `#0F172A` de máximo contraste (WCAG 2.2 AAA).
  - Lienzo Plotly: Fondo blanco puro con grillas `#E2E8F0`.
* **🌙 Modo Oscuro (High-End Midnight):**
  - Fondo de aplicación: `#0B0F17` (Negro slate aeroespacial).
  - Tarjetas Bento: `#111827` con borde `#334155`.
  - Tipografía: Blanco puro `#F8FAFC` con textos secundarios `#94A3B8`.
  - Lienzo Plotly: Fondo medianoche `#111827` con grillas `#1E293B`.
* **Badges Semánticos Vibrantes:**
  - Preservación íntegra de resaltados cromáticos en ambos modos: `.hl-green` (verde esmeralda), `.hl-blue` (azul cian), `.hl-amber` (ámbar dorado), `.hl-red` (rojo carmesí) y `.hl-purple` (púrpura real).
* **Barra de Opciones de Streamlit Habilitada:**
  - Configuración `toolbarMode = "viewer"` en `.streamlit/config.toml` con encabezado transparente que permite acceder al menú nativo superior de tres puntos y ajustes sin interferencias.

---

## 🎯 3. Métricas Macroeconómicas y Resultados Clave (Horizonte 36 Meses)

| Métrica Financiera | Valor Consolidado | Contexto e Interpretación Contable |
| :--- | :---: | :--- |
| **Facturación Acumulada** | `RD$ 98.12M` | Ritmo comercial sostenido con crecimiento del 21.7% interanual en 2026. |
| **Costos Directos** | `RD$ 11.68M` | Modelo de software y consultoría con costos directos de apenas el **11.9%**. |
| **Utilidad Bruta** | `RD$ 86.44M` | Margen bruto de excelencia del **88.1%**, habilitando alto margen de contribución. |
| **Gastos Operativos (OPEX)** | `RD$ 35.62M` | Absorbe el **36.3%** de las ventas; nómina de ingeniería concentra el **50.7%**. |
| **Utilidad Neta Final** | `RD$ 50.82M` | Margen neto sobresaliente del **51.8%** retenido por la operación corporativa. |
| **Índice de Salud Corporativa** | `65/100 🟡` | Categoría **SÓLIDA**, penalizada por mora en cobranza y descuadre de caja menor. |
| **Tesorería Disponible** | `RD$ 85.19M` | Cobertura de **2.86x** sobre pasivos exigibles acumulados. |
| **Cartera CxC Inmovilizada** | `RD$ 45.37M` | Tasa de cobranza deprimida en **21.3%**; foco primario del plan a 90 días. |
| **Pasivos Acumulados** | `RD$ 29.74M` | Concentrado en `ITBIS DGII` (17.66M), Proveedores (9.20M) y Retenciones TSS (2.88M). |
| **Déficit en Caja General** | `-RD$ 3.85M` | Saldo acreedor por salidas en efectivo sin previa reposición bancaria. |
| **Partida Doble Auditada** | `RD$ 250.37M` | Débitos = Créditos con varianza exacta de **RD$ 0.00** en 4,853 asientos. |

---

## 🧭 4. Arquitectura de las 7 Pestañas Analíticas

### 🏁 Tab 0: Resumen Ejecutivo
- **5 Bento KPI Cards:** Facturación, Margen Bruto, Utilidad Neta, Tesorería y Dolarización.
- **Índice Compuesto de Salud Corporativa:** Algoritmo ponderado (Rentabilidad 30%, Cobranza 25%, Liquidez 20%, Control Interno 15%, Crecimiento 10%).
- **Gráfico Comparativo de Ingresos vs. Egresos:** Dinámica mensual y margen neto temporal.
- **Cascada de Rentabilidad P&L:** Descomposición paso a paso desde ingresos hasta beneficio neto.

### 📊 Tab 1: Rentabilidad & P&L
- **Ingresos Mensuales por Línea de Negocio:** Soluciones Cloud & Software (`55.5%`) vs Servicios de Consultoría & IA (`44.5%`).
- **Ciclo Estacional y Picos de Demanda:** Detección de meses pico (Septiembre, Marzo, Enero) y valles comerciales.
- **Análisis de Pareto de Gastos:** Concentración del 80% del gasto en apenas 4 cuentas contables.

### 🏢 Tab 2: Eficiencia Departamental
- **Treemap Presupuestario Jerárquico:** Erogaciones por departamento y centros de costo.
- **Matriz de Dispersión:** Proporción de nómina frente a gastos operativos generales.
- **Tabla Maestra de Centros de Costo:** Ranking con porcentaje de participación presupuestaria y mapas de calor protegidos.

### 🚨 Tab 3: Auditoría & Riesgos
- **Gráfico Forense Integrado de los 3 Hallazgos Críticos (Doble Eje):**
  - *Línea Roja con Diamantes:* Trayectoria descendente de Caja General por debajo de la línea cero (`-RD$ 3.85M`).
  - *Barras Ámbar:* Cartera CxC inmovilizada en clientes (`RD$ 45.37M`).
  - *Barras Violetas:* Pasivos acumulados sin liquidar (`RD$ 29.74M`).
  - *Línea Punteada Celeste (Eje Derecho):* Tasa de cobranza deprimida (`21.3%`) frente a la meta óptima verde (`80%`).
- **Dial de Eficacia de Cobranza:** Medidor semafórico con zonas roja, amarilla y verde.
- **Gráfico Donut de Pasivos:** Concentración de deuda con la DGII, TSS y suplidores.
- **Matriz de Riesgos:** Cuantificación de impacto, probabilidad y asignación de responsables.

### 🔮 Tab 4: Tendencias & Proyección
- **Modelo de Regresión Lineal Predictivo (Runway 6 Meses):** Proyección de ingresos con bandas de dispersión estadística ($\pm 1\sigma$).
- **Matriz de Dolarización Cambiaria:** Análisis de facturación bimoneda (DOP vs USD) y cobertura ante tipo de cambio.

### 📑 Tab 5: Informe Gerencial
- **Memorándum de Alta Dirección:** Diagnóstico estructurado y dictamen de contraloría con texto formateado en acordeones interactivos.
- **📊 Macromagnitudes & Conversión Patrimonial 360°:** Gráfico de barras horizontales con eje cero explícito que evalúa facturación (`RD$ 98.12M`), margen bruto (`RD$ 86.44M`), tesorería (`RD$ 85.19M`), utilidad neta (`RD$ 50.82M`), cartera CxC (`RD$ 45.37M`), nómina (`RD$ 24.00M`), pasivos (`RD$ 29.74M`) y el déficit de caja general extendiéndose hacia la izquierda en rojo (`-RD$ 3.85M`).
- **🎯 Hoja de Ruta 90 Días (Doble Eje):** Barras de impacto financiero en DOP (Cobranza: `RD$ 24.95M`, Saneamiento: `RD$ 33.59M`, Cobertura: `RD$ 29.23M`, Expansión: `RD$ 20.33M`) contrastadas con la línea escalonada de plazos (Día 30, 45, 60 y 90).
- **Descarga de Informe:** Exportación del memorándum completo en formato Markdown (`.md`) nativo sin requerir librerías externas complejas.

### 🔍 Tab 6: Libro Mayor & Balance General
- **KPI Grid de Partida Doble:** Asientos en vista, Total Débitos, Total Créditos, Diferencia y Asientos USD.
- **⚖️ Matriz Forense de Partida Doble:** Barras dobles agrupadas que comparan Débitos (cargos) en azul vs Créditos (abonos) en verde para las 6 naturalezas contables, con línea de saldo neto y validación de varianza cero (`RD$ 250.37M = RD$ 250.37M`).
- **🏛️ Ecuación Patrimonial del Balance General:** Emulación gráfica de la identidad contable `Activo = Pasivo + Capital + Utilidad Neta`, con línea de equilibrio horizontal a nivel de Activos Totales (`RD$ 111.08M`).
- **Explorador con Mapa de Calor:** Tabla interactiva de asientos con búsqueda en tiempo real.
- **💱 Barómetro de Divisas en Vivo & Revaluación Spot (Top 5 vs DOP):** Conexión API en tiempo real (ExchangeRate-API + CDN jsDelivr con fallback de resguardo) que cotiza USD, EUR, CAD, GBP y CHF frente al Peso Dominicano, gráfico de paridades relativas y comparativa de saldos.
- **📑 Matriz de Cuentas Contables en Divisa y Diferencial Cambiario:** Revaluación automática de cuentas en moneda extranjera (`CTA_103`, cartera, ingresos USD), calculando el saldo contable histórico vs saldo revaluado spot y el efecto neto de ganancia o pérdida cambiaria (*Forex Gain/Loss*) conforme a la norma NIC 21.
- **Exportador a Excel Enriquecido:** Generación de libro multi-hoja (`.xlsx`) en 6 hojas estructuradas incluyendo `Revaluacion_Divisas_Spot` y `Tasas_Spot_Top5`.

---

## 🎙️ 5. Motor Maestro de Audio TTS (Web Speech API)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎙️ CONSOLA DE NARRACIÓN POR VOZ (ESTÁNDAR JPV PRO)                          │
│                                                                             │
│ [▶️ Escuchar]  [⏸️ Pausar]  [⏯️ Reanudar]  [⏹️ Detener]   ● Narrando análisis...│
│                                                                             │
│ 🔊 Volumen: [-] ────[========o====]──── [+]  85%                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Web Speech API Nativa:** Cero dependencias externas, cero latencia de red y funcionamiento garantizado offline.
2. **Ecualizador Visual:** Animación en verde pulsante (`.audio-wave-dot`) que indica si la voz está activa o en pausa.
3. **Control Deslizante de Volumen:** Ajuste continuo de 0% a 100% sincronizado en vivo con `utterance.volume`.
4. **Normalización Fonética Avanzada:** Lectura impecable de cantidades monetarias en español (millones, miles, centavos), porcentajes y abreviaturas contables sin pausas artificiales ni tropiezos.

---

## 🚀 6. Instalación y Ejecución Local

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/JUANCITOPENA/dashboard-contable-ejecutivo.git
cd dashboard-contable-ejecutivo
```

### Paso 2: Crear y Activar Entorno Virtual
```bash
# En Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# En Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Iniciar la Aplicación
```bash
streamlit run app.py
```
*La plataforma se abrirá automáticamente en su navegador en `http://localhost:8501`.*

---

## ☁️ 7. Despliegue en Streamlit Community Cloud

1. Ingrese a [Streamlit Community Cloud](https://share.streamlit.io/) e inicie sesión con su cuenta de GitHub (**JUANCITOPENA**).
2. Haga clic en **"New app"**.
3. Seleccione el repositorio: `JUANCITOPENA/dashboard-contable-ejecutivo`.
4. Rama: `main`.
5. Archivo principal: `app.py`.
6. Presione **"Deploy!"** y su suite estará operativa en vivo en minutos con conexión segura HTTPS.

---

## 📂 8. Estructura del Repositorio

```
dashboard-contable-ejecutivo/
├── .gitignore                                         # Reglas de exclusión para entornos y temporales
├── .streamlit/
│   └── config.toml                                    # Configuración de servidor, CORS y toolbar mode
├── app.py                                            # Aplicación principal de la Suite Ejecutiva (con Motor Dual)
├── Contabilidad_Libro_Diario_Consolidado_Limpio.xlsx # Dataset oficial del Libro Diario General (4,853 asientos)
├── MANUAL_PASO_A_PASO_SUITE_CONTABLE_STREAMLIT.md    # Manual exhaustivo paso a paso de la plataforma
├── README.md                                         # Documentación ejecutiva del proyecto
├── requirements.txt                                  # Dependencias de producción para Python y Cloud
└── STATUS.md                                         # Bitácora de calidad, auditoría y control de versiones
```

---

## 🏛️ 9. Autor y Contacto Institucional

**Ing. Juancito Peña Vizcaíno**  
*Arquitecto Digital, Consultor Senior en Inteligencia Artificial, Analítica de Datos y Desarrollo Full Stack.*  
- **LinkedIn:** [Juancito Peña Vizcaíno](https://www.linkedin.com/in/juancitope%C3%B1a/)  
- **YouTube:** [@JuancitoDevV](https://www.youtube.com/@JuancitoDevV)  
- **GitHub:** [@JUANCITOPENA](https://github.com/JUANCITOPENA)  
- **Twitter / X:** [@JuancitoPenaV](https://x.com/JuancitoPenaV)  
- **Email:** juancito.pena.v@hotmail.com  

---
*Desarrollado bajo los más rigurosos estándares de Gobernanza Empresarial, Calidad Total (ISO 25010) y Accesibilidad WCAG 2.2 AAA.*
