# mi_portafolio

Dashboard para inversionistas construido con Python y Streamlit
(curso Lenguajes de Programación · Ingeniería Financiera · ITM).

**Integrantes:** Mariana Cadavid Durango

## Portafolio
Activos: CIB, EC, NU, ITUB, MELI · Benchmark: SPY · Período: 2024-01-01 a 2027-01-01

## Ejecución local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Fuente de datos
Yahoo Finance mediante yfinance. Si la descarga falla, la app usa `precios_respaldo.csv` y lo indica en pantalla.

> Rendimientos pasados no garantizan rendimientos futuros. Uso académico; no es una recomendación de inversión.
