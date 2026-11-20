# 📘 Manual Maestro Paso a Paso: Suite Ejecutiva de Inteligencia Financiera & Control Contable
> **Plataforma Integral de Analítica Avanzada, Auditoría Forense y Narración por Voz (Estándar JPV Pro)**  
> **Autor:** Ing. Juancito Peña Vizcaíno | Arquitecto Digital, Consultor de Inteligencia Artificial & Datos  
> **Versión:** 3.5 Enterprise Production Ready | **Fecha:** Noviembre 2026  
> **Repositorio Oficial:** `https://github.com/JUANCITOPENA/dashboard-contable-ejecutivo`

---

## 📑 Tabla de Contenidos

1. [🏛️ Ficha Técnica y Presentación Institucional](#1-🏛️-ficha-técnica-y-presentación-institucional)
2. [📊 El Dataset Contable: Estructura del Libro Diario General](#2-📊-el-dataset-contable-estructura-del-libro-diario-general)
3. [⚙️ Preparación del Entorno Virtual y Dependencias (Paso a Paso)](#3-⚙️-preparación-del-entorno-virtual-y-dependencias-paso-a-paso)
4. [🔄 Pipeline ETL y Análisis Exploratorio de Datos (EDA)](#4-🔄-pipeline-etl-y-análisis-exploratorio-de-datos-eda)
5. [📐 Diccionario Matemático y Fórmulas Financieras](#5-📐-diccionario-matemático-y-fórmulas-financieras)
6. [🧠 Arquitectura del Código Fuente (Desglose por Secciones)](#6-🧠-arquitectura-del-código-fuente-desglose-por-secciones)
7. [🎙️ Motor Maestro de Audio TTS y Storytelling Dinámico](#7-🎙️-motor-maestro-de-audio-tts-y-storytelling-dinámico)
8. [🎨 Sistema de Nivelación Geométrica, UI Responsiva y Motor Dual](#8-🎨-sistema-de-nivelación-geométrica-ui-responsiva-y-motor-dual-de-temas)
9. [🖼️ Recorrido Visual por las 7 Pestañas Analíticas (Mockups de Interfaz)](#9-🖼️-recorrido-visual-por-las-7-pestañas-analíticas-mockups-de-interfaz)
10. [🎯 Dictamen de Auditoría y Hoja de Ruta Estratégica a 90 Días](#10-🎯-dictamen-de-auditoría-y-hoja-de-ruta-estratégica-a-90-días)
11. [🚀 Despliegue en Streamlit Community Cloud (Guía Paso a Paso)](#11-🚀-despliegue-en-streamlit-community-cloud-guía-paso-a-paso)
12. [🏛️ Autor y Créditos Oficiales](#12-🏛️-autor-y-créditos-oficiales)

---

## 1. 🏛️ Ficha Técnica y Presentación Institucional

La **Suite Ejecutiva de Inteligencia Financiera & Control Contable** es una aplicación analítica web de clase empresarial diseñada para proporcionar visibilidad financiera integral en 360 grados a directores generales (CEO), directores financieros (CFO), comités de auditoría interna y consejos de administración.

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
│                   - Informe Gerencial (Tab 5)                                          │
│                   - Libro Mayor (Tab 6)                                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Atributos Clave
- **Horizonte Temporal:** 36 meses completos (Ejercicios Fiscales 2024, 2025 y 2026).
- **Masa Transaccional Auditada:** 4,853 asientos contables consolidados en 1,871 pólizas.
- **Cuadre de Partida Doble:** `RD$ 250,369,637.28` en Débitos = `RD$ 250,369,637.28` en Créditos (Varianza: `RD$ 0.00`).
- **Narración Auditada por Voz:** Integración nativa de la **Web Speech API** en cada panel y visual con ecualizador animado, control de volumen táctil y pronunciación perfecta de cifras en español sin pausas ni distorsiones.
- **Arquitectura de Interfaz:** Sistema responsivo adaptable a pantallas de escritorio UltraWide, laptops, tablets y móviles con contenedores geométricamente nivelados (`st.container(border=True)`).

---

## 2. 📊 El Dataset Contable: Estructura del Libro Diario General

El motor analítico se alimenta del archivo contable oficial:
`Contabilidad_Libro_Diario_Consolidado_Limpio.xlsx` (Hoja: `Libro_Diario_General`).

### Diccionario de Datos del Dataset

| Campo | Tipo | Ejemplo | Descripción Contable |
| :--- | :--- | :--- | :--- |
| `Fecha` | Datetime | `2024-01-15` | Fecha de emisión y registro contable de la transacción. |
| `Numero_Poliza` | String | `POL-2024-0012` | Identificador único de la póliza de diario, ingreso o egreso. |
| `Codigo_Departamento` | String | `DEP_01` | Código del centro de costo o departamento responsable. |
| `Departamento` | String | `Tecnología & I+D+i` | Nombre formal de la unidad organizativa. |
| `Lider_Departamento` | String | `Ing. Juancito Peña` | Responsable titular del ejercicio del gasto. |
| `Codigo_Cuenta` | String | `CTA_101` | Código del catálogo maestro de cuentas contables. |
| `Cuenta_Contable` | String | `Caja General` | Descripción formal de la cuenta contable. |
| `Tipo_Cuenta` | String | `Activo` | Naturaleza contable: `Activo`, `Pasivo`, `Capital`, `Ingresos`, `Costo`, `Gasto`. |
| `Estado_Financiero` | String | `Balance General` | Clasificación de destino: `Balance General` o `Estado de Resultados`. |
| `Moneda` | String | `DOP` / `USD` | Moneda original de la factura o transacción. |
| `Monto_Original` | Float | `1,500.00` | Valor en la moneda original de transacción. |
| `Tasa_Cambio` | Float | `58.50` | Tipo de cambio spot aplicado para la conversión a DOP. |
| `Debito_DOP` | Float | `87,750.00` | Cargo contable en Pesos Dominicanos (aumento activo/gasto). |
| `Credito_DOP` | Float | `0.00` | Abono contable en Pesos Dominicanos (aumento pasivo/ingreso). |
| `Monto_Neto_DOP` | Float | `87,750.00` | Saldo neto del asiento (`Debito_DOP - Credito_DOP`). |
| `Referencia_Concepto` | String | `Servicios Cloud AWS` | Glosa o detalle justificativo de la póliza contable. |

---

## 3. ⚙️ Preparación del Entorno Virtual y Dependencias (Paso a Paso)

Para garantizar un entorno aislado, reproducible y libre de conflictos con librerías globales del sistema operativo, siga esta secuencia rigurosa:

### Paso 3.1: Clonar o Situarse en la Carpeta del Proyecto
Abra PowerShell o Terminal y sitúese en el directorio de trabajo:
```powershell
Set-Location "C:\Users\User\Desktop\dashboard_contable_ejecutivo"
```

### Paso 3.2: Crear el Entorno Virtual de Python
Cree un entorno virtual aislado con Python 3.10, 3.11, 3.12, 3.13 o 3.14:
```powershell
# En Windows (PowerShell)
python -m venv venv
```

### Paso 3.3: Activar el Entorno Virtual
```powershell
# En Windows PowerShell
.\venv\Scripts\Activate.ps1

# Si PowerShell restringe la ejecución de scripts, autorice la sesión:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

# En CMD tradicional
.\venv\Scripts\activate.bat

# En macOS / Linux
source venv/bin/activate
```
*(Al activarse, verá el prefijo `(venv)` al inicio de su línea de comandos).*

### Paso 3.4: Crear y Verificar el Archivo `requirements.txt`
El archivo `requirements.txt` especifica las versiones mínimas estables:
```txt
streamlit>=1.39.0
pandas>=2.2.0
numpy>=1.26.0
plotly>=5.24.0
openpyxl>=3.1.5
tabulate>=0.9.0
matplotlib>=3.8.0
jinja2>=3.1.0
```

### Paso 3.5: Instalar las Dependencias
Con el entorno virtual activo, actualice `pip` e instale la suite de paquetes:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 3.6: Verificar la Instalación
Compruebe que los paquetes esenciales están listos:
```powershell
python -c "import streamlit, pandas, numpy, plotly, openpyxl, matplotlib, jinja2; print('✅ Todas las librerías cargadas exitosamente.')"
```

### Paso 3.7: Configurar `.streamlit/config.toml` (Servidor, Seguridad y Toolbar)
Cree la carpeta `.streamlit` en la raíz del proyecto y configure el archivo `config.toml` para optimizar el despliegue local y en Streamlit Cloud:
```toml
[theme]
primaryColor = "#0284C7"
font = "sans serif"

[server]
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[client]
showErrorDetails = true
toolbarMode = "viewer"
```
*(Nota: `toolbarMode = "viewer"` garantiza que la barra superior nativa de Streamlit esté visible y permita a los usuarios acceder al menú de opciones y ajustes del visor).*

---

## 4. 🔄 Pipeline ETL y Análisis Exploratorio de Datos (EDA)

El pipeline de ingesta implementa la función `@st.cache_data` para garantizar tiempos de respuesta inferiores a **200 milisegundos** tras la primera carga:

```python
@st.cache_data
def cargar_datos(ruta_archivo) -> pd.DataFrame:
    # 1. Lectura de la hoja principal
    df = pd.read_excel(ruta_archivo, sheet_name='Libro_Diario_General')
    
    # 2. Sanitización de registros sin póliza o residuales
    df = df.dropna(subset=['Numero_Poliza']).copy()
    
    # 3. Conversión de fechas y construcción de dimensiones cronológicas
    df['Año'] = df['Año'].astype(int)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Mes'] = pd.Categorical(df['Mes'], categories=MESES_ORDEN, ordered=True)
    df['Mes_Num'] = df['Fecha'].dt.month
    df['Trimestre'] = 'Q' + df['Fecha'].dt.quarter.astype(str)
    df['Año_Mes'] = df['Fecha'].dt.to_period('M').astype(str)
    df['Per_Tri'] = df['Año'].astype(str) + ' ' + df['Trimestre']
    
    return df
```

### Hallazgos del Análisis Exploratorio (EDA)
1. **Volumen de Transacciones:** Distribución uniforme a lo largo de los 36 meses, con 1,871 pólizas y un promedio de 2.6 asientos por póliza.
2. **Moneda Extranjera:** 748 asientos corresponden a facturación en moneda extranjera (`USD`), representando el 29.8% de los ingresos totales convertidos a DOP.
3. **Inconsistencias Forenses Identificadas:**
   - La cuenta `CTA_101` (Caja General) registra un saldo acumulado acreedor negativo de **-RD$ 3,846,803.82**, producto de salidas de efectivo no compensadas con remesas bancarias.
   - La cuenta `CTA_104` (Cuentas por Cobrar) evidencia una tasa de cobranza de apenas **21.3%**, inmovilizando **RD$ 45.37M** en clientes.
   - Existen **RD$ 29.74M** acumulados en pasivos fiscales (`ITBIS por Pagar DGII`, `Retenciones TSS & ISR`) y proveedores estratégicos.

---

## 5. 📐 Diccionario Matemático y Fórmulas Financieras

Toda la lógica de cálculo está formalizada según los principios universales de contabilidad financiera:

### 5.1 Fórmulas de Rentabilidad y Desempeño (P&L)

$$\text{Ingresos Totales} = \sum \text{Crédito DOP}_{(\text{Tipo} = \text{'Ingresos'})}$$

$$\text{Costos Directos} = \sum \text{Débito DOP}_{(\text{Tipo} = \text{'Costo'})}$$

$$\text{Gastos Operativos (OPEX)} = \sum \text{Débito DOP}_{(\text{Tipo} = \text{'Gasto'})}$$

$$\text{Utilidad Bruta} = \text{Ingresos Totales} - \text{Costos Directos}$$

$$\text{Margen Bruto (\%)} = \left(\frac{\text{Utilidad Bruta}}{\text{Ingresos Totales}}\right) \times 100$$

$$\text{Utilidad Neta} = \text{Utilidad Bruta} - \text{Gastos Operativos}$$

$$\text{Margen Neto (\%)} = \left(\frac{\text{Utilidad Neta}}{\text{Ingresos Totales}}\right) \times 100$$

### 5.2 Fórmulas de Auditoría de Tesorería, Cobranza y Solvencia

$$\text{Tesorería Disponible} = \text{Saldo}(\text{CTA\_101}) + \text{Saldo}(\text{CTA\_102}) + \text{Saldo}(\text{CTA\_103})$$

$$\text{Tasa de Cobranza (\%)} = \left(\frac{\sum \text{Créditos (Abonos) CTA\_104}}{\sum \text{Débitos (Cargos) CTA\_104}}\right) \times 100$$

$$\text{Cobertura de Liquidez sobre Pasivos} = \frac{\text{Tesorería Disponible}}{\text{Pasivos Totales Exigibles}}$$

$$\text{Cartera CxC Inmovilizada} = \sum \text{Débito DOP}_{\text{CTA\_104}} - \sum \text{Crédito DOP}_{\text{CTA\_104}}$$

### 5.3 Ecuación Contable Fundamental y Partida Doble

$$\sum \text{Débitos DOP} = \sum \text{Créditos DOP} \quad \implies \quad \text{Diferencia} = \text{RD\$ 0.00}$$

$$\text{Activos Totales} = \text{Pasivos Exigibles} + \text{Capital Social} + \text{Utilidad Neta Retenida}$$

$$\text{Activo} = \text{Pasivo} + \text{Patrimonio Neto} \quad (\text{Identidad 100\% Verificada})$$

---

## 6. 🧠 Arquitectura del Código Fuente (Desglose por Secciones)

El archivo maestro `app.py` está estructurado en 8 bloques de gobernanza:

### Bloque 1: Configuración de Streamlit y Parche Robusto Markdown
Configura el viewport en pantalla ancha (`layout="wide"`), favicon oficial y aplica un parche preventivo a `DataFrame.to_markdown` para garantizar exportaciones limpias aun si la librería `tabulate` no estuviese presente.

### Bloque 2: Capa CSS y Nivelación de Altura
Inyecta reglas CSS especializadas:
- **Nivelación Geométrica:** `div[data-testid="stHorizontalBlock"] { align-items: stretch; }` garantiza que todas las columnas en la misma fila tengan idéntica altura visual.
- **Títulos Uniformes:** `h3 { min-height: 2.85rem; }` alinea la línea de inicio de los gráficos.
- **Paleta de Resaltado:** Clases `.hl-green`, `.hl-blue`, `.hl-amber`, `.hl-red`, `.hl-purple` para storytelling de datos.

### Bloque 3: Motor TTS de Audio (Web Speech API)
Implementa el componente HTML/JS dinámico con sintetizador nativo del navegador, controles táctiles y slider sincronizado de volumen.

### Bloque 4: Pipeline ETL y Slicers Multidimensionales
Define los segmentadores colapsables en la barra lateral (Ejercicio, Trimestre, Mes, Departamento, Líder, Tipo de Cuenta, Cuenta y Moneda) con botones de selección masiva (*"✅ Todos"* / *"🧹 Limpiar"*).

### Bloque 5: Pestañas Analíticas (Tabs 0 al 6)
- **Tab 0: 🏁 Resumen Ejecutivo:** KPI Cards Bento, Índice de Salud Corporativa (0 a 100), Gráfico de Ingresos vs Egresos y Cascada P&L.
- **Tab 1: 📊 Rentabilidad & P&L:** Dinámica mensual de ingresos, mezcla de facturación por línea de negocio, estacionalidad y análisis Pareto de gastos.
- **Tab 2: 🏢 Eficiencia Departamental:** Treemap presupuestario, matriz de costos por unidad, dispersión de nómina vs erogaciones y tabla de eficiencia.
- **Tab 3: 🚨 Auditoría & Riesgos:** Gráfico forense integrado de los 3 hallazgos críticos (Caja General negativa, Cartera CxC inmovilizada, Pasivos acumulados vs Tasa de Cobranza), Dial de Eficacia, Pasivos por pagar y Matriz de Riesgos.
- **Tab 4: 🔮 Tendencias & Proyección:** Modelo de regresión predictiva a 6 meses (`Runway`), intervalos de confianza a $\pm 1\sigma$ y matriz de dolarización de cartera.
- **Tab 5: 📑 Informe Gerencial:** Memorándum completo de Alta Dirección, **Gráfico de Macromagnitudes 360°**, **Gráfico de Hoja de Ruta a 90 Días** (doble eje impacto DOP vs plazos en días), tabla estratégica y descarga en Markdown.
- **Tab 6: 🔍 Libro Mayor:** KPI Grid de partida doble, **Matriz Forense de Débitos vs Créditos**, **Ecuación Patrimonial del Balance General**, explorador de 500 asientos con formato condicional y exportador multi-hoja a Excel.

---

## 7. 🎙️ Motor Maestro de Audio TTS y Storytelling Dinámico

La suite erradica las tradicionales interfaces silenciosas mediante un sistema de voz interactivo:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎙️ CONSOLA DE NARRACIÓN POR VOZ (WEB SPEECH API)                            │
│                                                                             │
│ [▶️ Escuchar]  [⏸️ Pausar]  [⏯️ Reanudar]  [⏹️ Detener]   ● Narrando análisis...│
│                                                                             │
│ 🔊 Volumen: [-] ────[========o====]──── [+]  85%                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Características Técnicas del Motor de Voz
1. **Zero Cost & Zero Lag:** Utiliza la API nativa `window.speechSynthesis` del navegador, funcionando 100% offline sin consumir tokens ni APIs de terceros.
2. **Normalizador Fonético de Cifras:** La función `_a_voz()` expande abreviaturas (`RD$ 50.82M` $\rightarrow$ *"cincuenta millones ochocientos veinte mil pesos dominicanos"*), eliminando pausas raras o lecturas truncadas.
3. **Control de Volumen Sincronizado:** Slider continuo de 0% a 100% con sincronización en tiempo real sobre la propiedad `utterance.volume`.
4. **Detención Automática:** Al pausar, detener o interactuar con un nuevo módulo, el sintetizador cancela la locución previa para evitar ecos o solapamientos.

---

## 8. 🎨 Sistema de Nivelación Geométrica, UI Responsiva y Motor Dual de Temas

### 8.1 Protocolo de Nivelación Geométrica
Para erradicar el problema común en Streamlit donde una columna queda más alta que su vecina, la suite implementa el **Protocolo de Nivelación Geométrica**:

1. **Contenedores con Borde:** Todo gráfico o tarjeta se aloja dentro de `with st.container(border=True):`.
2. **Alturas Fijas en Plotly:** Cada gráfico se invoca mediante `plot(estilo(fig, 410))` o `320`, estandarizando la altura en píxeles.
3. **Flexbox Stretch en CSS:**
   ```css
   div[data-testid="stHorizontalBlock"] {
       align-items: stretch !important;
   }
   div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
       display: flex !important;
       flex-direction: column !important;
   }
   div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"] {
       height: 100% !important;
   }
   ```
4. **Comportamiento Responsivo:** En pantallas de escritorio se distribuyen en 2 o 3 columnas simétricas; en tablets y teléfonos inteligentes se apilan verticalmente de forma automática conservando su legibilidad completa.

### 8.2 Motor Dual de Temas (Claro ☀️ / Oscuro 🌙)
La aplicación cuenta con un diccionario centralizado de tokens de diseño (`THEME`) gobernado por `st.session_state["app_theme"]` que permite conmutar la visualización en caliente:
* **☀️ Modo Claro:** Fondo `#F4F7FB`, tarjetas Bento `#FFFFFF`, bordes `#CBD5E1`, textos `#0F172A` y gráficos Plotly sobre lienzo blanco.
* **🌙 Modo Oscuro:** Fondo `#0B0F17`, tarjetas Bento `#111827`, bordes `#334155`, textos `#F8FAFC` y gráficos Plotly sobre lienzo oscuro medianoche.
* **Badges Semánticos:** Mantiene activos los estilos de alto contraste para Storytelling de Datos:
  - `.hl-green`: Verde `#059669` (valores positivos, utilidades y superación de meta).
  - `.hl-blue`: Azul `#0284C7` (ingresos, transacciones y referencias estándar).
  - `.hl-amber`: Ámbar `#D97706` (atención requerida, márgenes moderados).
  - `.hl-red`: Rojo `#DC2626` (alertas críticas, déficits de caja y mora).
  - `.hl-purple`: Púrpura `#6366F1` (erogaciones, OPEX y proyecciones).

---

## 9. 🖼️ Recorrido Visual por las 7 Pestañas Analíticas (Mockups de Interfaz)

### Tab 0: Resumen Ejecutivo
Muestra los 5 KPI Cards principales (Ingresos, Margen Bruto, Utilidad Neta, Tesorería, Dolarización), el Índice de Salud Corporativa (65/100 SÓLIDA 🟡) y la cascada P&L.

### Tab 3: Auditoría & Riesgos (Gráfico Forense Integrado)
```
  [DOP]                                               [% Cobranza]
  RD$ 50M ┤                        [■] Pasivos 29.74M        100%
  RD$ 40M ┤        [■] Cartera CxC 45.37M              Meta   80% 
  RD$ 20M ┤                                                   60%
    RD$ 0 ┼──────────────────────────────────── ⋯⋯ Tasa 21.3% 40%
 -RD$ 4M ┤ ◆ Caja General -RD$ 3.85M                         20%
```

### Tab 5: Informe Gerencial (Consolidación 360° & Plan 90 Días)
```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│ 📊 Macromagnitudes & Conversión 360°  │ 🎯 Hoja de Ruta 90 Días: Metas        │
│                                       │                                       │
│ 🟢 Facturación ─────────── RD$ 98.12M │  RD$ 35M ┤       [■] Saneamiento      │
│ 🟣 Margen Bruto ────────── RD$ 86.44M │  RD$ 30M ┤       [■] Divisas  ◆ D90   │
│ 🟢 Tesorería   ─────────── RD$ 85.19M │  RD$ 25M ┤ [■]CxC        ◆ D60        │
│ 🔵 Utilidad    ─────────── RD$ 50.82M │  RD$ 20M ┤              ◆ D45 [■]Exp  │
│ 🟠 Cartera CxC ─────────── RD$ 45.37M │  RD$ 15M ┤       ◆ D30                │
│ 🔴 Pasivos     ─────────── RD$ 29.74M │    RD$ 0 ┴─────────────────────────── │
│ 🔴 Caja Gen ◄─ -RD$ 3.85M | Cero      │          Cobranza Saneam Divisas Exp  │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

### Tab 6: Libro Mayor & Balance General Completo
```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│ ⚖️ Matriz Forense de Partida Doble    │ 🏛️ Ecuación Patrimonial del Balance   │
│                                       │                                       │
│ [■ Débitos] [■ Créditos] ◆ Saldo Neto │ [■ Activos] ─────────── [■ Pasivo+Pat]│
│  RD$ 250.37M = RD$ 250.37M (Cuadra)   │  RD$ 111.08M  =  RD$ 111.08M (Cuadra) │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 10. 🎯 Dictamen de Auditoría y Hoja de Ruta Estratégica a 90 Días

| Prioridad | Iniciativa Estratégica | Responsable | Meta Cuantificable | Plazo |
| :--- | :--- | :--- | :--- | :---: |
| **P1 - Urgente** | Campaña de Recuperación de Cartera CxC | Finanzas & Ventas | Recuperar $\ge 55\%$ de CxC (`RD$ 24.95M`) | 60 Días |
| **P1 - Urgente** | Arqueo de Caja y Conciliación Fiscal DGII/TSS | Contraloría | Saneamiento al 100% de `CTA_101` y pasivos | 45 Días |
| **P2 - Alta** | Integración API Tasa Diaria Banco Central en ERP | Tecnología & I+D+i | Eliminar tasa estática en asientos USD | 30 Días |
| **P3 - Media** | Rebalanceo Presupuestario & Escalamiento | Dirección / Marketing | Consolidar expansión de ingresos (`RD$ 20.33M`) | 90 Días |

---

## 11. 🚀 Despliegue en Streamlit Community Cloud (Guía Paso a Paso)

El despliegue en la nube oficial de Streamlit es gratuito y se realiza en 5 minutos:

### Paso 11.1: Subir el Proyecto a GitHub
Asegúrese de haber empujado los cambios a su repositorio:
```powershell
git add .
git commit -m "feat: Suite Contable Ejecutiva v3.5 Lista para Producción"
git push -u origin main
```

### Paso 11.2: Acceder a Streamlit Community Cloud
1. Ingrese a [https://share.streamlit.io](https://share.streamlit.io) e inicie sesión con su cuenta de GitHub (**JUANCITOPENA**).
2. Haga clic en el botón superior derecho: **"Create app"** o **"New app"**.

### Paso 11.3: Configurar los Parámetros de Despliegue
En el formulario de configuración, complete:
- **Repository:** `JUANCITOPENA/dashboard-contable-ejecutivo`
- **Branch:** `main`
- **Main file path:** `app.py`
- **App URL (opcional):** `dashboard-contable-ejecutivo-jpv`

### Paso 11.4: Desplegar y Monitorear
1. Presione el botón **"Deploy!"**.
2. Streamlit Cloud leerá automáticamente `requirements.txt`, instalará las dependencias en un contenedor Linux y levantará la aplicación en menos de 90 segundos.
3. ¡Listo! Su suite estará disponible con certificado SSL HTTPS activo en:
   `https://dashboard-contable-ejecutivo.streamlit.app`

---

## 12. 🏛️ Autor y Créditos Oficiales

**Ing. Juancito Peña Vizcaíno**  
*Arquitecto Digital, Consultor Senior en Inteligencia Artificial, Analítica de Datos y Desarrollo Full Stack.*  
- **LinkedIn:** [Juancito Peña Vizcaíno](https://www.linkedin.com/in/juancitope%C3%B1a/)  
- **Canal Educativo:** [@JuancitoDevV](https://www.youtube.com/@JuancitoDevV)  
- **GitHub:** [@JUANCITOPENA](https://github.com/JUANCITOPENA)  
- **Twitter / X:** [@JuancitoPenaV](https://x.com/JuancitoPenaV)  
- **Correo Institucional:** juancito.pena.v@hotmail.com  

---
*Desarrollado bajo los más rigurosos estándares de Gobernanza Empresarial, Calidad Total (ISO 25010) y Accesibilidad WCAG 2.2 AAA.*
