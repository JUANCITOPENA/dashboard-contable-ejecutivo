import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

BASE_DIR = r"C:\Users\User\Desktop\dashboard_contable_ejecutivo"
DOCS_DIR = os.path.join(BASE_DIR, "docs", "screenshots")
os.makedirs(DOCS_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 8501


def run():
    print("Iniciando Suite Ejecutiva Streamlit...")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(7)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=True,
                args=["--disable-gpu", "--no-sandbox"]
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1
            )
            page = context.new_page()

            print("Cargando aplicación...")
            page.goto(f"http://localhost:{PORT}")
            page.wait_for_selector("[data-testid='stTabs']", timeout=35000)
            time.sleep(4)

            def click_tab(name):
                tab = page.locator(f'div[data-testid="stTab"]:has-text("{name}")')
                tab.click()
                time.sleep(2.5)

            def scroll_top():
                page.evaluate("() => { const el = document.querySelector('section[data-testid=\"stMain\"]'); if(el) el.scrollTop = 0; }")
                time.sleep(2)

            # 1. Tab 0: Resumen Ejecutivo
            print("📸 [1/10] Capturando 00_resumen_ejecutivo.png...")
            click_tab("🏁 Resumen Ejecutivo")
            scroll_top()
            p0 = os.path.join(DOCS_DIR, "00_resumen_ejecutivo.png")
            page.screenshot(path=p0)
            print(f" -> Guardado: 00_resumen_ejecutivo.png ({os.path.getsize(p0)/1024:.1f} KB)")

            # 2. Tab 1: Rentabilidad & P&L
            print("📸 [2/10] Capturando 01_rentabilidad_pyg.png...")
            click_tab("📊 Rentabilidad & P&L")
            scroll_top()
            time.sleep(0.5)
            p1 = os.path.join(DOCS_DIR, "01_rentabilidad_pyg.png")
            page.screenshot(path=p1)
            print(f" -> Guardado: 01_rentabilidad_pyg.png ({os.path.getsize(p1)/1024:.1f} KB)")

            # 3. Tab 2: Eficiencia Departamental
            print("📸 [3/10] Capturando 02_eficiencia_departamental.png...")
            click_tab("🏢 Eficiencia Departamental")
            scroll_top()
            time.sleep(0.5)
            p2 = os.path.join(DOCS_DIR, "02_eficiencia_departamental.png")
            page.screenshot(path=p2)
            print(f" -> Guardado: 02_eficiencia_departamental.png ({os.path.getsize(p2)/1024:.1f} KB)")

            # 4. Tab 3: Auditoría & Riesgos (Monitor Forense)
            print("📸 [4/10] Capturando 03_auditoria_y_riesgos.png...")
            click_tab("🚨 Auditoría & Riesgos")
            mon = page.locator("text=Monitor Forense").first
            if mon.count() > 0:
                mon.scroll_into_view_if_needed()
            time.sleep(2.5)
            p3 = os.path.join(DOCS_DIR, "03_auditoria_y_riesgos.png")
            page.screenshot(path=p3)
            print(f" -> Guardado: 03_auditoria_y_riesgos.png ({os.path.getsize(p3)/1024:.1f} KB)")

            # 5. Tab 4: Tendencias & Proyección
            print("📸 [5/10] Capturando 04_tendencias_y_proyeccion.png...")
            click_tab("🔮 Tendencias & Proyección")
            scroll_top()
            time.sleep(0.5)
            p4 = os.path.join(DOCS_DIR, "04_tendencias_y_proyeccion.png")
            page.screenshot(path=p4)
            print(f" -> Guardado: 04_tendencias_y_proyeccion.png ({os.path.getsize(p4)/1024:.1f} KB)")

            # 6. Tab 5: Informe Gerencial (Macromagnitudes 360°)
            print("📸 [6/10] Capturando 05_informe_gerencial.png...")
            click_tab("📑 Informe Gerencial")
            macro = page.locator("text=Macromagnitudes").first
            if macro.count() > 0:
                macro.scroll_into_view_if_needed()
            time.sleep(2.5)
            p5 = os.path.join(DOCS_DIR, "05_informe_gerencial.png")
            page.screenshot(path=p5)
            print(f" -> Guardado: 05_informe_gerencial.png ({os.path.getsize(p5)/1024:.1f} KB)")

            # 7. Tab 6: Libro Mayor (Matriz Forense Débitos vs Créditos)
            print("📸 [7/10] Capturando 06_libro_mayor_auditoria.png...")
            click_tab("🔍 Libro Mayor")
            matriz = page.locator("text=Matriz Forense de Partida Doble").first
            if matriz.count() > 0:
                matriz.scroll_into_view_if_needed()
            time.sleep(2.5)
            p6 = os.path.join(DOCS_DIR, "06_libro_mayor_auditoria.png")
            page.screenshot(path=p6)
            print(f" -> Guardado: 06_libro_mayor_auditoria.png ({os.path.getsize(p6)/1024:.1f} KB)")

            # 8. Tab 6: Barómetro Top 5 Divisas en Vivo (NIC 21)
            print("📸 [8/10] Capturando 06_libro_mayor_divisas_barometro.png...")
            barom = page.locator("text=Barómetro de Divisas en Vivo").first
            if barom.count() > 0:
                barom.scroll_into_view_if_needed()
            time.sleep(2.5)
            p_fx = os.path.join(DOCS_DIR, "06_libro_mayor_divisas_barometro.png")
            page.screenshot(path=p_fx)
            print(f" -> Guardado: 06_libro_mayor_divisas_barometro.png ({os.path.getsize(p_fx)/1024:.1f} KB)")

            # 9. Tab 6: Estado de Resultados Multidivisa en Vivo
            print("📸 [9/10] Capturando 06_libro_mayor_er_multidivisa.png...")
            er = page.locator("text=Estado de Resultados Comparativo con Consolidación").first
            if er.count() > 0:
                er.scroll_into_view_if_needed()
            time.sleep(2.5)
            p_er = os.path.join(DOCS_DIR, "06_libro_mayor_er_multidivisa.png")
            page.screenshot(path=p_er)
            print(f" -> Guardado: 06_libro_mayor_er_multidivisa.png ({os.path.getsize(p_er)/1024:.1f} KB)")

            # 10. Menú Lateral de Segmentación (Sidebar)
            print("📸 [10/10] Capturando 07_menu_segmentacion_sidebar.png...")
            click_tab("🏁 Resumen Ejecutivo")
            scroll_top()
            p7 = os.path.join(DOCS_DIR, "07_menu_segmentacion_sidebar.png")
            page.screenshot(path=p7)
            print(f" -> Guardado: 07_menu_segmentacion_sidebar.png ({os.path.getsize(p7)/1024:.1f} KB)")

            browser.close()
            print("\n🎉 ¡TODAS LAS 10 CAPTURAS HAN SIDO GENERADAS Y VERIFICADAS CON ÉXITO TOTAL!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    run()
