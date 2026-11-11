"""Evalúa la base actual con el mismo procedimiento que utiliza la página."""
import os


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        import django
        django.setup()
        from predicciones.modelo_ia import predecir_proximo_mes
        from predicciones.models import RegistroMensual
    except ModuleNotFoundError as error:
        raise SystemExit(f'Falta {error.name}. Primero ejecutá python iniciar.py --solo-preparar y después ejecutá este archivo con el Python de .venv.') from None
    resultado = predecir_proximo_mes()
    if resultado is None:
        raise SystemExit('Se necesitan al menos 12 meses en la base. Cargalos desde Registros → Importar CSV.')
    print('EVALUACIÓN CRONOLÓGICA DE LA BASE ACTUAL')
    print(f'Meses disponibles: {RegistroMensual.objects.count()}')
    print(f'Meses para seleccionar método: {resultado["periodos_evaluados"]}')
    print('Cada pronóstico utiliza solo datos anteriores y el mes del calendario.')
    for label, key in [('Random Forest', 'error_modelo'), ('Referencia reciente y estacional', 'error_referencia')]:
        value = resultado[key]
        print(f'{label}: MAE {value:.2f} altas' if value is not None else f'{label}: todavía no hay meses reservados para evaluación.')
    print(f'Método elegido: {resultado["modelo_usado"]}')
    print(f'Próximo período: {resultado["mes_objetivo"]:%Y-%m}')
    print(f'Altas estimadas: {resultado["alumnos_estimados"]}')
    print(f'MAE informado para el pronóstico: {resultado["error_medio"]} · {resultado["error_descripcion"]}')
    print('El error histórico no garantiza la precisión futura.')


if __name__ == '__main__':
    main()
