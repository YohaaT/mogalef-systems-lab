import os
import re
import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, WEEKLY, FR

def get_rollover_date(contract_str):
    """
    Calcula la fecha de rollover para un contrato en formato 'MM-YY'.
    Asume que el rollover se realiza el jueves previo a la semana del vencimiento,
    el cual es el tercer viernes del mes de vencimiento. Esto equivale a 8 días
    antes del 3er viernes.
    """
    month = int(contract_str[:2])
    year = 2000 + int(contract_str[3:])
    
    first_day = datetime.date(year, month, 1)
    # Obtener todos los viernes del mes
    fridays = list(rrule(WEEKLY, byweekday=FR, dtstart=first_day, count=3))
    third_friday = fridays[2]
    
    # Rollover date: 8 días antes del 3er viernes (que es un jueves)
    rollover_date = third_friday.date() - datetime.timedelta(days=8)
    return datetime.datetime.combine(rollover_date, datetime.time(0, 0))

def main():
    directory = '.'
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    
    # Regex para parsear "ES 03-17.Last.txt"
    pattern = re.compile(r'^([A-Z]+)\s+(\d{2}-\d{2})\.Last\.txt$')
    
    instruments = {}
    
    for f in files:
        match = pattern.match(f)
        if match:
            inst = match.group(1)
            contract = match.group(2)
            if inst not in instruments:
                instruments[inst] = []
            instruments[inst].append({
                'filename': f,
                'contract_str': contract,
                'year': 2000 + int(contract[3:]),
                'month': int(contract[:2])
            })
            
    ohlcv_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    for inst, contracts in instruments.items():
        print(f"Procesando instrumento: {inst}")
        # Ordenar cronológicamente
        contracts.sort(key=lambda x: x['year'] * 100 + x['month'])
        
        dfs = []
        prev_rollover = None
        
        for i, c in enumerate(contracts):
            filepath = os.path.join(directory, c['filename'])
            print(f"  Leyendo {c['filename']}...")
            try:
                df = pd.read_csv(filepath, sep=';', header=None, names=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                # Formato datetime: 20170101 201100
                df['datetime'] = pd.to_datetime(df['datetime'].astype(str), format='%Y%m%d %H%M%S', errors='coerce')
                df = df.dropna(subset=['datetime'])
                
                current_rollover = get_rollover_date(c['contract_str'])
                
                # Filtrar con el rollover previo
                if prev_rollover is not None:
                    df = df[df['datetime'] >= prev_rollover]
                    
                # Filtrar con el rollover actual si no es el último contrato
                if i < len(contracts) - 1:
                    df = df[df['datetime'] < current_rollover]
                
                dfs.append(df)
                prev_rollover = current_rollover
            except Exception as e:
                print(f"  Error leyendo {c['filename']}: {e}")
                
        if not dfs:
            continue
            
        print(f"  Concatenando contratos para {inst}...")
        continuous_df = pd.concat(dfs)
        
        # Filtro de fines de semana: Eliminar datos de los sábados (donde no hay sesión)
        # weekday() devuelve 5 para el sábado.
        continuous_df = continuous_df[continuous_df['datetime'].dt.weekday != 5]
        
        # Filtro específico solicitado para el bad tick del 20 de Enero de 2024
        continuous_df = continuous_df[continuous_df['datetime'].dt.date != pd.to_datetime('2024-01-20').date()]
        
        continuous_df.set_index('datetime', inplace=True)
        continuous_df.sort_index(inplace=True)
        
        timeframes = {'5min': '5m', '10min': '10m', '15min': '15m'}
        
        for tf_pd, tf_str in timeframes.items():
            print(f"  Haciendo resample a {tf_str} para {inst}...")
            resampled_df = continuous_df.resample(tf_pd).agg(ohlcv_dict)
            resampled_df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
            
            # Exportar
            out_filename = f"{inst}_Continuous_{tf_str}.txt"
            out_filepath = os.path.join(directory, out_filename)
            
            # Formatear el índice de nuevo a YYYYMMDD HHMMSS
            resampled_df.index = resampled_df.index.strftime('%Y%m%d %H%M%S')
            
            # Asegurarse de que el volumen sea entero
            if 'volume' in resampled_df.columns:
                resampled_df['volume'] = resampled_df['volume'].astype(int)
                
            resampled_df.to_csv(out_filepath, sep=';', header=False)
            print(f"  Guardado: {out_filename}")

if __name__ == "__main__":
    main()
