import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import yfinance as yf
from pathlib import Path
from scipy import stats
from scipy.stats import norm

import mi_portafolio as mp   # <- tu ficha: activos, pesos, textos

# =====================================================================
# 0. CONFIGURACIÓN DE LA PÁGINA
# =====================================================================
st.set_page_config(page_title=mp.nombre_portafolio, page_icon="📊", layout="wide")
sns.set_theme(style="whitegrid")
DIAS_ANIO = 252

activos = mp.activos
benchmark = mp.benchmark
pesos = pd.Series(mp.pesos, index=activos, name="Peso")

st.title(f"📊 {mp.nombre_portafolio}")
st.caption(f"Dashboard para inversionistas · {mp.integrantes}")
BG_COLOR = "#121417"     # Ajusta si cambias el backgroundColor de .streamlit/config.toml
TEXT_COLOR = "#EAECEF"
GRID_COLOR = "#2C313A"

plt.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": BG_COLOR,
    "savefig.facecolor": BG_COLOR,
    "text.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "axes.edgecolor": GRID_COLOR,
    "grid.color": GRID_COLOR,
})

# =====================================================================
# 1. DATOS: Yahoo Finance (con archivo de respaldo)
# =====================================================================
@st.cache_data(ttl=3600, show_spinner="Descargando precios de Yahoo Finance...")
def descargar_precios(tickers, inicio, fin):
    datos = yf.download(list(tickers), start=inicio, end=fin,
                        auto_adjust=True, progress=False)
    cierre = datos["Close"][list(tickers)].dropna()
    if len(cierre) < 30:
        raise ValueError("Yahoo Finance devolvió muy pocos datos")
    return cierre

tickers = activos + [benchmark]
try:
    cierre_total = descargar_precios(tuple(tickers), mp.fecha_inicio, mp.fecha_fin)
    fuente = "Yahoo Finance"
except Exception:
    if Path("precios_respaldo.csv").exists():
        cierre_total = pd.read_csv("precios_respaldo.csv", index_col=0, parse_dates=True)
        cierre_total = cierre_total[tickers].dropna()
        fuente = "archivo precios_respaldo.csv (Yahoo Finance no respondió)"
    else:
        st.error("No fue posible descargar los precios y no existe precios_respaldo.csv.")
        st.stop()

# =====================================================================
# 2. BARRA LATERAL: controles del usuario
# =====================================================================
st.sidebar.header("⚙️ Ajusta el análisis")

umbral = st.sidebar.slider("Umbral de pérdida diaria", -0.05, -0.01, -0.02, step=0.005, format="%.3f")
primera = cierre_total.index[0].date()
ultima = cierre_total.index[-1].date()
inicio, fin = st.sidebar.slider("Período analizado", min_value=primera, max_value=ultima,
                                value=(primera, ultima), format="YYYY-MM-DD")
monto_inicial = st.sidebar.number_input("Monto inicial (USD)", min_value=1_000,
                                        value=int(mp.monto_inicial), step=1_000)
confianza = st.sidebar.selectbox("Nivel de confianza del VaR", [0.95, 0.99],
                                 format_func=lambda x: f"{x:.0%}")

st.sidebar.divider()
st.sidebar.subheader("🧺 Composición")
st.sidebar.dataframe(pesos.map("{:.0%}".format))
st.sidebar.caption(f"Benchmark: **{benchmark}** · Fuente: {fuente}")

cierre_periodo = cierre_total.loc[str(inicio):str(fin)]
if len(cierre_periodo) < 60:
    st.warning("Elige un período más largo (al menos 60 días de negociación).")
    st.stop()

cierre = cierre_periodo[activos]
cierre_bench = cierre_periodo[benchmark]

# =====================================================================
# 3. CÁLCULOS (los mismos del taller)
# =====================================================================
# Rendimientos de los activos
rend_simple = cierre.pct_change().dropna()
rendimientos = np.log(cierre / cierre.shift(1)).dropna()

# Portafolio (rebalanceo diario) y benchmark
rend_port = np.log(1 + (rend_simple * pesos).sum(axis=1))
rend_port.name = "Portafolio"
rend_bench = np.log(cierre_bench / cierre_bench.shift(1)).dropna()
rend_bench.name = benchmark
rend_todos = pd.concat([rendimientos, rend_port, rend_bench], axis=1)

# Valor de la inversión (arranca en el monto inicial)
fecha0 = cierre.index[0]
valor_port = pd.concat([pd.Series([monto_inicial], index=[fecha0]),
                        monto_inicial * np.exp(rend_port.cumsum())])
valor_bench = pd.concat([pd.Series([monto_inicial], index=[fecha0]),
                         monto_inicial * np.exp(rend_bench.cumsum())])

# Resumen anualizado de cada serie
resumen = pd.DataFrame({
    "Rend. anualizado": rend_todos.mean() * DIAS_ANIO,
    "Volatilidad anualizada": rend_todos.std() * np.sqrt(DIAS_ANIO),
})

def max_drawdown(valor):
    return (valor / valor.cummax() - 1).min()

def var_dinero(cuantil_log, valor):
    return valor * (1 - np.exp(cuantil_log))

def ficha(r, valor):
    mu_a = r.mean() * DIAS_ANIO
    sigma_a = r.std() * np.sqrt(DIAS_ANIO)
    return {
        "Rendimiento total": valor.iloc[-1] / valor.iloc[0] - 1,
        "Rendimiento anualizado": mu_a,
        "Volatilidad anualizada": sigma_a,
        "Sharpe": (mu_a - mp.tasa_libre_riesgo) / sigma_a,
        "Máxima caída": max_drawdown(valor),
        "VaR diario (histórico)": r.quantile(1 - confianza),
        "Peor día": r.min(),
        "Mejor día": r.max(),
        "Asimetría": stats.skew(r),
        "Exceso de curtosis": stats.kurtosis(r),
    }

ficha_tecnica = pd.DataFrame({"Portafolio": ficha(rend_port, valor_port),
                              benchmark: ficha(rend_bench, valor_bench)})
fp, fb = ficha_tecnica["Portafolio"], ficha_tecnica[benchmark]

# Parámetros de la normal y VaR en dinero
mu_p, sigma_p = rend_port.mean(), rend_port.std()
q_hist = rend_port.quantile(1 - confianza)
q_norm = norm.ppf(1 - confianza, loc=mu_p, scale=sigma_p)
valor_actual = valor_port.iloc[-1]

# =====================================================================
# 4. INDICADORES CLAVE (st.metric)
# =====================================================================
st.subheader("Indicadores clave del período")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Valor final", f"USD {valor_actual:,.0f}",
          f"{valor_actual - valor_bench.iloc[-1]:+,.0f} vs {benchmark}")
c2.metric("Rendimiento anualizado", f"{fp['Rendimiento anualizado']:.1%}",
          f"{(fp['Rendimiento anualizado'] - fb['Rendimiento anualizado']) * 100:+.1f} pp vs {benchmark}")
c3.metric("Volatilidad anualizada", f"{fp['Volatilidad anualizada']:.1%}",
          f"{(fp['Volatilidad anualizada'] - fb['Volatilidad anualizada']) * 100:+.1f} pp vs {benchmark}",
          delta_color="inverse")
c4.metric("Sharpe", f"{fp['Sharpe']:.2f}", f"{fp['Sharpe'] - fb['Sharpe']:+.2f} vs {benchmark}")
c5.metric(f"VaR diario {confianza:.0%}", f"USD {var_dinero(q_hist, valor_actual):,.0f}",
          f"{q_hist:.2%} del valor", delta_color="off")
st.caption("Más volatilidad aparece en rojo porque significa más riesgo. "
           "Portafolio con pesos fijos y rebalanceo diario; sin costos de transacción.")

# =====================================================================
# 5. PESTAÑAS: una pregunta del inversionista por pestaña
# =====================================================================
t1, t2, t3, t4, t5, t6 = st.tabs(["🧺 ¿Qué tengo?", "💰 ¿Cuánto he ganado?",
                                  "⚖️ ¿Cuánto riesgo?", "🔗 ¿Estoy diversificado?",
                                  "📉 ¿Cuánto puedo perder?", "📝 Nuestro mensaje"])

# ---------- Pestaña 1: composición -----------------------------------
with t1:
    izq, der = st.columns(2)
    with izq:
        tabla = pd.DataFrame(mp.info_activos, index=["Nombre", "Sector"]).T
        tabla["Peso"] = pesos.map("{:.0%}".format)
        st.dataframe(tabla)
        st.markdown(f"**¿Por qué este portafolio?** {mp.justificacion}")
    with der:
        por_sector = tabla.assign(Peso=pesos).groupby("Sector")["Peso"].sum().sort_values()
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.barh(por_sector.index, por_sector.values, color="steelblue", edgecolor="black")
        for i, v in enumerate(por_sector.values):
            ax.text(v + 0.005, i, f"{v:.0%}", va="center")
        ax.set_title("Peso por sector", fontweight="bold")
        ax.set_xlabel("Peso")
        st.pyplot(fig)
        plt.close(fig)

# ---------- Pestaña 2: rendimiento -----------------------------------
with t2:
    st.markdown(f"**Valor de una inversión de USD {monto_inicial:,.0f}**")
    st.line_chart(pd.DataFrame({mp.nombre_portafolio: valor_port, benchmark: valor_bench}))
    st.info(f"Una inversión de USD {monto_inicial:,.0f} el {inicio} se habría convertido en "
            f"USD {valor_actual:,.0f} el {cierre.index[-1].date()}, frente a "
            f"USD {valor_bench.iloc[-1]:,.0f} en {benchmark}.")

    st.markdown("**Evolución de cada activo (inicio = 100)**")
    elegidos = st.multiselect("Activos a mostrar", activos, default=activos)
    base_100 = cierre[elegidos] / cierre[elegidos].iloc[0] * 100
    base_100[f"{benchmark} (benchmark)"] = cierre_bench / cierre_bench.iloc[0] * 100
    st.line_chart(base_100)

# ---------- Pestaña 3: riesgo-rendimiento ----------------------------
with t3:
    izq, der = st.columns([3, 2])
    with izq:
        fig, ax = plt.subplots(figsize=(8, 5.5))
        for nombre in resumen.index:
            x = resumen.loc[nombre, "Volatilidad anualizada"]
            y = resumen.loc[nombre, "Rend. anualizado"]
            if nombre == "Portafolio":
                ax.scatter(x, y, s=300, color="navy", marker="*", zorder=3)
            elif nombre == benchmark:
                ax.scatter(x, y, s=200, color="black", marker="D", zorder=3)
            else:
                ax.scatter(x, y, s=120, color="steelblue", edgecolor="black", zorder=3)
            ax.annotate(nombre, (x, y), xytext=(8, 5), textcoords="offset points", fontweight="bold")
        ax.axhline(0, color="black", linewidth=1)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        ax.set_title("Mapa riesgo–rendimiento (anualizado)", fontweight="bold")
        ax.set_xlabel("Volatilidad anualizada (riesgo)")
        ax.set_ylabel("Rendimiento anualizado")
        st.pyplot(fig)
        plt.close(fig)
    with der:
        st.dataframe(resumen.style.format("{:.2%}"))
        st.caption("Arriba y a la izquierda = más rendimiento con menos riesgo.")

# ---------- Pestaña 4: diversificación -------------------------------
with t4:
    correlacion = rendimientos.corr()
    corr_promedio = correlacion.values[np.triu_indices_from(correlacion, k=1)].mean()
    vol_activos = rendimientos.std() * np.sqrt(DIAS_ANIO)
    vol_sin_div = (pesos * vol_activos).sum()
    vol_port = fp["Volatilidad anualizada"]

    izq, der = st.columns([3, 2])
    with izq:
        fig, ax = plt.subplots(figsize=(7, 5.5))
        sns.heatmap(correlacion, annot=True, fmt=".2f", cmap="coolwarm",
                    center=0, vmin=-1, vmax=1, square=True, ax=ax)
        ax.set_title("Correlación entre los rendimientos", fontweight="bold")
        st.pyplot(fig)
        plt.close(fig)
    with der:
        st.metric("Correlación promedio", f"{corr_promedio:.2f}")
        st.metric("Volatilidad si ρ = 1", f"{vol_sin_div:.1%}")
        st.metric("Volatilidad real del portafolio", f"{vol_port:.1%}",
                  f"{(vol_port - vol_sin_div) * 100:+.1f} pp por diversificar", delta_color="inverse")
        st.success(f"La diversificación reduce el riesgo en un "
                   f"{(vol_sin_div - vol_port) / vol_sin_div:.0%} frente a un portafolio "
                   f"con activos perfectamente correlacionados.")

# ---------- Pestaña 5: pérdidas --------------------------------------
with t5:
    izq, der = st.columns(2)
    with izq:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.hist(rend_port, bins=60, density=True, color="steelblue", alpha=0.5, edgecolor="black")
        xs = np.linspace(rend_port.min(), rend_port.max(), 400)
        ax.plot(xs, norm.pdf(xs, mu_p, sigma_p), color="red", linewidth=2, label="Normal ajustada")
        ax.axvline(q_hist, color="darkred", linestyle="--", linewidth=2,
                   label=f"VaR {confianza:.0%} histórico: {q_hist:.2%}")
        ax.set_title("Rendimientos diarios del portafolio", fontweight="bold")
        ax.set_xlabel("Rendimiento diario")
        ax.legend(fontsize=9)
        st.pyplot(fig)
        plt.close(fig)
    with der:
        var_tabla = pd.DataFrame({
            "Rendimiento (%)": [q_norm, q_hist],
            "Pérdida (USD)": [var_dinero(q_norm, valor_actual), var_dinero(q_hist, valor_actual)],
        }, index=["VaR normal", "VaR histórico"])
        st.dataframe(var_tabla.style.format({"Rendimiento (%)": "{:.2%}", "Pérdida (USD)": "{:,.2f}"}))
        st.info(f"Con un {confianza:.0%} de confianza, la pérdida del portafolio en un día "
                f"no debería superar USD {var_dinero(q_hist, valor_actual):,.0f} "
                f"({-q_hist:.2%} de su valor), según la historia del período.")

    st.markdown("**Caída desde el máximo previo (drawdown)**")
    dd = pd.DataFrame({"Portafolio": valor_port / valor_port.cummax() - 1,
                       benchmark: valor_bench / valor_bench.cummax() - 1}) * 100
    st.area_chart(dd, y_label="Drawdown (%)", stack=False)
    st.caption(f"Máxima caída del portafolio: {fp['Máxima caída']:.1%} "
               f"(benchmark: {fb['Máxima caída']:.1%}).")
    prob = (rend_port <= umbral).mean()
st.metric(f"Días con pérdida mayor a {-umbral:.1%}", f"{prob:.2%}", f"≈ {prob * DIAS_ANIO:.0f} días al año", delta_color="off")

# ---------- Pestaña 6: mensaje ---------------------------------------
with t6:
    st.subheader("Resumen ejecutivo")
    st.write(mp.resumen_ejecutivo)
    st.subheader("Tres hallazgos clave")
    for h in mp.hallazgos:
        st.markdown(f"- {h}")
    izq, der = st.columns(2)
    izq.warning(mp.riesgos)
    der.info(mp.limitaciones)
    st.markdown(f"**Perfil de inversionista sugerido:** {mp.perfil_inversionista}")

    st.subheader("Ficha técnica")
    formatos = {k: "{:.2%}" for k in ficha_tecnica.index}
    formatos.update({"Sharpe": "{:.2f}", "Asimetría": "{:.2f}", "Exceso de curtosis": "{:.2f}"})
    st.dataframe(ficha_tecnica.apply(lambda fila: fila.map(formatos[fila.name].format), axis=1))

# =====================================================================
# 6. DATOS Y NOTA LEGAL
# =====================================================================
with st.expander("🔎 Ver y descargar los precios"):
    st.dataframe(cierre_periodo.tail(20))
    st.download_button("Descargar precios (CSV)", cierre_periodo.to_csv().encode("utf-8"),
                       "precios_portafolio.csv", "text/csv")

st.caption("⚠️ Rendimientos pasados no garantizan rendimientos futuros. Este análisis tiene "
           "fines académicos y no constituye una recomendación de inversión.")
