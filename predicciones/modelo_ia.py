"""Pronóstico mensual: evaluación temporal sin usar entradas futuras reales."""
from functools import lru_cache
from math import pi

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from .models import RegistroMensual

CAMPOS = ('fecha', 'alumnos_inicio', 'consultas', 'clases_prueba', 'inversion_publicidad', 'cuota_mensual', 'promocion', 'alumnos_nuevos', 'bajas')
VARIABLES = ['alumnos_inicio', 'consultas', 'clases_prueba', 'inversion_publicidad', 'cuota_mensual', 'promocion', 'mes_sin', 'mes_cos']


def _preparar(registros):
    df = pd.DataFrame(registros).sort_values('fecha').reset_index(drop=True)
    months = pd.to_datetime(df['fecha']).dt.month
    df['mes_sin'] = np.sin(2 * pi * months / 12)
    df['mes_cos'] = np.cos(2 * pi * months / 12)
    return df


def _modelo():
    return RandomForestRegressor(n_estimators=300, max_depth=4, min_samples_leaf=2, max_features=0.9, random_state=42)


def _promedio_base(historial, mes_objetivo):
    recent = float(historial['alumnos_nuevos'].tail(3).mean())
    same_month = historial.loc[pd.to_datetime(historial['fecha']).dt.month == mes_objetivo, 'alumnos_nuevos']
    seasonal = float(same_month.mean()) if len(same_month) else recent
    weight = 0.5 if len(same_month) >= 2 else 0.3
    return (1 - weight) * recent + weight * seasonal


def _cierre(row):
    return max(0, int(row['alumnos_inicio'] + row['alumnos_nuevos'] - row['bajas']))


def _datos_futuros(ultimo, mes_objetivo, alumnos_actuales, datos_override=None):
    data = {key: float(ultimo[key]) for key in VARIABLES if key not in ('mes_sin', 'mes_cos')}
    data.update(alumnos_inicio=alumnos_actuales, mes_sin=float(np.sin(2*pi*mes_objetivo/12)), mes_cos=float(np.cos(2*pi*mes_objetivo/12)))
    for key, value in (datos_override or {}).items():
        if key in VARIABLES and key not in ('mes_sin', 'mes_cos'):
            data[key] = value
    return pd.DataFrame([data], columns=VARIABLES)


def _evaluar(df):
    comparisons = []
    for index in range(max(12, len(df) - 6), len(df)):
        history = df.iloc[:index]
        last = history.iloc[-1]
        target = pd.to_datetime(df.loc[index, 'fecha'])
        if target != pd.to_datetime(last['fecha']) + pd.offsets.MonthBegin(1):
            continue
        # Se repiten las mismas suposiciones que se usarán al pronosticar un mes nuevo.
        future = _datos_futuros(last, int(target.month), _cierre(last))
        model = _modelo().fit(history[VARIABLES], history['alumnos_nuevos'])
        comparisons.append({
            'fecha': target.date().isoformat(), 'real': float(df.loc[index, 'alumnos_nuevos']),
            'modelo': float(model.predict(future)[0]), 'referencia': _promedio_base(history, int(target.month)),
        })
    # Reservamos los tres meses finales cuando hay seis evaluaciones posibles.
    selection = comparisons[:-3] if len(comparisons) == 6 else comparisons
    validation = comparisons[-3:] if len(comparisons) == 6 else []
    errors = {'modelo': None, 'referencia': None, 'periodos': len(selection), 'comparacion': comparisons, 'validacion': validation, 'mae_validacion': None}
    if selection:
        for method in ('modelo', 'referencia'):
            errors[method] = float(mean_absolute_error([row['real'] for row in selection], [row[method] for row in selection]))
    if validation:
        chosen = 'modelo' if errors['modelo'] <= errors['referencia'] else 'referencia'
        errors['mae_validacion'] = float(mean_absolute_error([row['real'] for row in validation], [row[chosen] for row in validation]))

    return errors


@lru_cache(maxsize=2)
def _entrenamiento(firma):
    # La clave incluye todos los valores: una edición o importación invalida el resultado.
    df = _preparar([dict(zip(CAMPOS, row)) for row in firma])
    evaluation = _evaluar(df)
    model = _modelo().fit(df[VARIABLES], df['alumnos_nuevos'])
    return df, model, evaluation


def _historial():
    signature = tuple(RegistroMensual.objects.order_by('fecha').values_list(*CAMPOS))
    if len(signature) < 12: return None
    return _entrenamiento(signature)


def predecir_proximo_mes():
    analysis = _historial()
    if analysis is None: return None
    df, model, evaluation = analysis
    last = df.iloc[-1]
    target = pd.to_datetime(last['fecha']) + pd.offsets.MonthBegin(1)
    active = _cierre(last)
    future = _datos_futuros(last, int(target.month), active)
    use_model = evaluation['modelo'] is not None and evaluation['modelo'] <= evaluation['referencia']
    estimate = float(model.predict(future)[0]) if use_model else _promedio_base(df, int(target.month))
    recent = df.tail(6)
    churn_rate = float(recent['bajas'].sum()) / float(recent['alumnos_inicio'].sum()) if recent['alumnos_inicio'].sum() else 0
    arrivals = max(0, round(estimate))
    departures = min(active, max(0, round(active * churn_rate)))
    mean = float(df['alumnos_nuevos'].mean())
    seasonal = df.loc[pd.to_datetime(df['fecha']).dt.month == target.month, 'alumnos_nuevos']
    seasonal_mean = float(seasonal.mean()) if len(seasonal) else mean
    error = evaluation['mae_validacion'] if evaluation['mae_validacion'] is not None else evaluation['modelo'] if use_model else evaluation['referencia']
    return {
        'alumnos_estimados': arrivals, 'bajas_estimadas': departures,
        'alumnos_cierre_estimado': max(0, active + arrivals - departures),
        'crecimiento': round((arrivals-departures)/active*100, 2) if active else 0,
        'error_medio': round(error, 2) if error is not None else None,
        'error_descripcion': '3 meses posteriores de validación' if evaluation['mae_validacion'] is not None else 'Error exploratorio; sin validación independiente',
        'error_modelo': round(evaluation['modelo'], 2) if evaluation['modelo'] is not None else None,
        'error_referencia': round(evaluation['referencia'], 2) if evaluation['referencia'] is not None else None,
        'periodos_evaluados': evaluation['periodos'], 'comparacion': evaluation['comparacion'],
        'modelo_usado': 'Random Forest' if use_model else 'Promedio reciente y estacional',
        'mes_objetivo': target.date(), 'mes_factor_estacional': round((seasonal_mean/mean-1)*100, 1) if mean else 0,
        'alumnos_actuales': active, 'confianza': f'{len(df)} meses de historial',
    }


def simular_prediccion(datos_usuario):
    analysis = _historial()
    if analysis is None: return None
    df, model, evaluation = analysis
    last = df.iloc[-1]
    month = int(datos_usuario['mes_objetivo'])
    if not 1 <= month <= 12: raise ValueError('Mes inválido.')
    future = _datos_futuros(last, month, datos_usuario['alumnos_inicio'], datos_usuario)
    if not np.isfinite(future.to_numpy(dtype=float)).all(): raise ValueError('Ingresá solamente números finitos.')
    baseline = float(model.predict(_datos_futuros(last, month, _cierre(last)))[0])
    estimate = max(0, round(float(model.predict(future)[0])))
    labels = {'alumnos_inicio': 'socios iniciales', 'consultas': 'consultas', 'clases_prueba': 'clases de prueba', 'inversion_publicidad': 'inversión', 'cuota_mensual': 'cuota'}
    outside = [label for key, label in labels.items() if float(future.iloc[0][key]) < float(df[key].min()) or float(future.iloc[0][key]) > float(df[key].max())]
    validation = evaluation.get('validacion', [])
    scenario_error = float(mean_absolute_error([x['real'] for x in validation], [x['modelo'] for x in validation])) if validation else evaluation['modelo']
    return {
        'altas': estimate, 'metodo': 'Random Forest · escenario con tus datos',
        'error': round(scenario_error, 2) if scenario_error is not None else None,
        'mes_objetivo': month, 'base_altas': max(0, round(baseline)), 'diferencia': estimate-max(0, round(baseline)),
        'fuera_de_rango': ', '.join(outside),
    }
