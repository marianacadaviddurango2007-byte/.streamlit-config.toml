# =====================================================================
#  mi_portafolio.py  ·  LA FICHA DE MI PORTAFOLIO
# =====================================================================

# ---------- 1. Identificación ----------------------------------------
nombre_portafolio = "mi_portafolio"
integrantes = "Mariana Cadavid Durango"

# ---------- 2. Composición (igual que en el taller) -------------------
activos = ["CIB", "EC", "NU", "ITUB", "MELI"]

info_activos = {
    "CIB": ("Bancolombia", "Financiero"),
    "EC": ("Ecopetrol", "Energético"),
    "NU": ("Nu", "Financiero"),
    "ITUB": ("ITAU", "Financiero"),
    "MELI": ("Mercado libre", "Tecnología")
}

# Pesos en el MISMO orden de `activos`. Deben sumar 1.
pesos = [0.30, 0.20, 0.20, 0.15, 0.15]

benchmark = "SPY"
fecha_inicio = "2024-01-01"
fecha_fin = "2027-01-01"
monto_inicial = 1500000
tasa_libre_riesgo = 0.04      # anual

# ---------- 3. Mensaje para el inversionista (sección 13 del taller) --
justificacion = ("Se seleccionaron estos 5 activos para equilibrar la estabilidad"
 "de la renta variable local y los flujos de dividendos (banca, energía y"
" tecnológica) con una palanca de alto crecimiento en tecnología financiera"
"regional, diversificando el riesgo sistémico del portafolio."
)

resumen_ejecutivo = (
    "Portafolio multiactivo regional compuesto por 5 referentes de alta liquidez"
    "(CIB, EC, NU, ITUB, MELI), combinando la estabilidad de la banca tradicional"
    "andina y brasileña con el dinamismo del comercio electrónico y la tecnología"
    "financiera en América Latina. El portafolio muestra un perfil de riesgo"
    "moderado-agresivo orientado al crecimiento patrimonial de largo plazo."

    "Frente al benchmark: Superó a los índices regionales tradicionales gracias al "
    "fuerte impulso de los sectores de tecnología y comercio digital (MELI, NU), "
    "lo que compensó la debilidad y volatilidad cíclica del sector energético (EC)."

    "Perfil de riesgo: Moderado-agresivo. Combina la estabilidad de flujos de la banca"
     "tradicional andina y brasileña con la alta beta de activos de crecimiento tecnológico,"
      "presentando una volatilidad acorde a portafolios de renta variable en mercados emergentes."
)

hallazgos = [
    "Rendimiento: Los activos de tecnología y comercio digital (MELI y NU) impulsaron"
    "la rentabilidad acumulada del portafolio, compensando la ciclicidad del sector energético (EC).",

    "Riesgo y diversificación: La inclusión de instituciones financieras diversificadas"
    "(CIB e ITUB) amortiguó la volatilidad sectorial gracias a correlaciones moderadas con los activos tecnológicos.",

    "Eventos extremos:Las volatilidades anualizadas se mantuvieron dentro de los rangos "
    "esperados para mercados emergentes y de crecimiento, sin quiebres sistémicos atípicos en la ventana temporal analizada.",
]

riesgos = (
   "Exposición sectorial acentuada en servicios financieros y tecnología "
    "de consumo, altamente sensibles a cambios en tasas de interés macroeconómicas."
    "Tendencia de los activos regionales a converger hacia una"
    "correlación elevada durante choques de liquidez global o salidas de capital de economías emergentes."
    " Probabilidad de movimientos extremos de precios impulsados por"
     "la volatilidad de materias primas (EC) y la sensibilidad de valuación en valores de crecimiento (NU, MELI)."

)
limitaciones = (
    "Asume que los retornos siguen una distribución normal,subestimando la"
     "probabilidad de pérdidas extremas. Supone ajustes constantes de ponderación ignorando las "
     "fricciones operativas reales del mercado. Omite comisiones de corretaje, impuestos, tarifas"
     "de custodia y el impacto por deslizamiento de precios (slippage)."
)

perfil_inversionista = "Moderado a agresivo"   # Conservador, Moderado o Agresivo
