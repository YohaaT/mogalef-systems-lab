import pandas as pd
import numpy as np
from pathlib import Path
import os

def verify_data_for_backtest(file_path):
    print(f"\n--- Verificando {file_path.name} ---")
    
    # Cargar datos
    try:
        df = pd.read_csv(file_path, sep=';', header=None, 
                         names=['datetime', 'Open', 'High', 'Low', 'Close', 'Volume'],
                         parse_dates=['datetime'])
        print(f"Total de barras: {len(df)}")
    except Exception as e:
        print(f"Error al cargar: {e}")
        return False
        
    # 1. Orden cronológico
    if not df['datetime'].is_monotonic_increasing:
        print("ERROR: Los datos NO estan en orden cronologico.")
        return False
    else:
        print("OK: Orden cronologico correcto.")
        
    # 2. Duplicados
    duplicates = df.duplicated(subset=['datetime'])
    if duplicates.any():
        print(f"ERROR: Hay {duplicates.sum()} fechas/horas duplicadas.")
        print(df[duplicates].head())
        return False
    else:
        print("OK: No hay fechas/horas duplicadas.")
        
    # 3. Coherencia OHLC
    # High debe ser el máximo, Low el mínimo
    ohlc_errors = ((df['High'] < df['Open']) | (df['High'] < df['Close']) | 
                   (df['Low'] > df['Open']) | (df['Low'] > df['Close']))
    if ohlc_errors.any():
        print(f"ERROR: Hay {ohlc_errors.sum()} barras con incoherencias OHLC (ej. Low > Open).")
        return False
    else:
        print("OK: Coherencia de barras OHLC (High >= Open/Close, Low <= Open/Close) correcta.")
        
    # 4. Análisis de Gaps (Saltos de precio entre barras)
    # Calculamos la diferencia porcentual entre el Close anterior y el Open actual
    df['prev_close'] = df['Close'].shift(1)
    df['gap_pct'] = abs(df['Open'] - df['prev_close']) / df['prev_close'] * 100
    
    # Gaps anormales (> 1% en temporalidades pequeñas puede ser inusual, pero aceptable de un día a otro)
    # Vamos a revisar los 5 mayores gaps
    print("\nTop 5 mayores gaps (Open vs Close anterior):")
    top_gaps = df.nlargest(5, 'gap_pct')
    for _, row in top_gaps.iterrows():
        print(f"  {row['datetime']}: Diferencia {row['gap_pct']:.2f}% (Close prev: {row['prev_close']}, Open: {row['Open']})")
        
    # 5. Gaps temporales (detectar datos faltantes)
    # Diferencia entre timestamps
    df['time_diff'] = df['datetime'].diff()
    print("\nEstadisticas de intervalos de tiempo:")
    print(df['time_diff'].value_counts().head(5))
    
    print("Verificacion completada.\n")
    return True

if __name__ == "__main__":
    data_dir = Path(r"c:\Users\Yohanny Tambo\Desktop\Bo_Oracle\mogalef-systems-lab\new_data")
    
    # Verificar los archivos de 15 minutos como muestra
    files_to_check = list(data_dir.glob("*_Continuous_15m.txt"))
    
    if not files_to_check:
        print("No se encontraron archivos de prueba.")
    
    for f in files_to_check:
        verify_data_for_backtest(f)
