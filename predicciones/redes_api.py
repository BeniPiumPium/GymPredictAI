"""Lectura de Meta. Los secretos solo se leen del entorno del servidor."""
import json
import os
import re
from datetime import datetime, time, timedelta
from time import monotonic
from zoneinfo import ZoneInfo
from django.conf import settings
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

class ErrorRedes(Exception): pass
class SinRedireccion(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

def configuracion(fuente):
    prefix = {'anuncios': 'META_AD', 'instagram': 'META_IG', 'facebook': 'META_PAGE'}[fuente]
    account = os.environ.get(prefix + '_ID', '').strip()
    token = os.environ.get(prefix + '_TOKEN', '').strip()
    version = os.environ.get('META_API_VERSION', '').strip()
    if not re.fullmatch(r'v\d+\.0', version) or not re.fullmatch(r'\d+', account) or not token:
        raise ErrorRedes('Falta configurar la cuenta, su token y META_API_VERSION en el servidor. Consultá CONECTAR_REDES.md.')
    return account, token, version

class Meta:
    def __init__(self, token, version):
        self.token, self.version = token, version
        self.deadline = monotonic() + 50
        self.opener = build_opener(SinRedireccion())
    def get(self, path, params):
        if not re.fullmatch(r'[A-Za-z0-9_/]+', path): raise ErrorRedes('Identificador de Meta inválido.')
        url = 'https://graph.facebook.com/' + self.version + '/' + path + '?' + urlencode(params)
        remaining = self.deadline - monotonic()
        if remaining <= 0: raise ErrorRedes('La consulta tardó demasiado. Acortá el período; no se guardó un informe parcial.')
        req = Request(url, headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/json'})
        try:
            with self.opener.open(req, timeout=min(20, remaining)) as response:
                raw = response.read(5_000_001)
            if len(raw) > 5_000_000: raise ErrorRedes('Respuesta demasiado grande. Elegí un período más corto.')
            result = json.loads(raw)
            if not isinstance(result, dict) or 'error' in result: raise ErrorRedes('Meta rechazó la consulta. Revisá permisos, versión y vigencia del token.')
            return result
        except HTTPError as error:
            # No exponemos URLs, tokens ni cuerpos de errores del proveedor.
            if error.code in (401, 403): raise ErrorRedes('Meta denegó el acceso. Revisá permisos y vigencia del token.') from None
            if error.code == 429: raise ErrorRedes('Meta limitó las consultas. Intentá nuevamente más tarde.') from None
            raise ErrorRedes('Meta rechazó la consulta. Revisá versión de API, permisos, métricas y período.') from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise ErrorRedes('No se pudo consultar Meta. No se reemplazó el informe anterior.') from None
    def listar(self, path, params):
        rows, seen = [], set()
        params = dict(params, limit=100)
        for _ in range(20):
            result = self.get(path, params)
            data = result.get('data')
            if not isinstance(data, list): raise ErrorRedes('Meta devolvió un formato inesperado.')
            rows.extend(data)
            paging = result.get('paging', {})
            if not paging.get('next'): return rows
            cursor = paging.get('cursors', {}).get('after')
            if not cursor or cursor in seen: raise ErrorRedes('No se pudo completar la paginación. Acortá el período.')
            seen.add(cursor); params['after'] = cursor
        raise ErrorRedes('El informe supera 2000 elementos. Acortá el período; no se guardaron datos parciales.')

def _consultar(fuente, desde, hasta):
    account, token, version = configuracion(fuente)
    api = Meta(token, version)
    if fuente == 'anuncios':
        rows = api.listar('act_' + account + '/insights', {
            'level':'campaign', 'time_increment':'all_days',
            'time_range':json.dumps({'since':desde.isoformat(),'until':hasta.isoformat()}),
            'fields':'campaign_id,campaign_name,date_start,date_stop,spend,account_currency,impressions,reach,clicks,ctr,cpc,actions'})
        return account, [{'id': x['campaign_id'], 'nombre': x.get('campaign_name',''), 'gasto': x.get('spend'), 'moneda':x.get('account_currency'), 'impresiones':x.get('impressions'), 'alcance':x.get('reach'), 'clics':x.get('clicks'), 'ctr':x.get('ctr'), 'cpc':x.get('cpc'), 'acciones':x.get('actions',[])} for x in rows]
    if fuente == 'instagram':
        rows = api.listar(account + '/media', {'fields':'id,caption,timestamp,like_count,comments_count,media_type,permalink'})
    else:
        rows = api.listar(account + '/published_posts', {'fields':'id,message,created_time,permalink_url,reactions.limit(0).summary(true),comments.limit(0).summary(true),shares', 'since':int(datetime.combine(desde,time.min,ZoneInfo(settings.TIME_ZONE)).timestamp()), 'until':int(datetime.combine(hasta+timedelta(days=1),time.min,ZoneInfo(settings.TIME_ZONE)).timestamp())})
    selected = []
    for x in rows:
        stamp = x.get('timestamp') or x.get('created_time')
        if not stamp: continue
        # El calendario de publicaciones se interpreta en la zona horaria del gimnasio.
        day = datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(ZoneInfo(settings.TIME_ZONE)).date()
        if not desde <= day <= hasta: continue
        selected.append({'id':x['id'], 'nombre':(x.get('caption') or x.get('message') or 'Publicación sin texto')[:500], 'fecha':day.isoformat(), 'likes':x.get('like_count') if fuente=='instagram' else x.get('reactions',{}).get('summary',{}).get('total_count'), 'comentarios':x.get('comments_count') if fuente=='instagram' else x.get('comments',{}).get('summary',{}).get('total_count'), 'compartidos':x.get('shares',{}).get('count'), 'alcance':None})
        if fuente == 'instagram':
            # Fallar explícitamente evita presentar un informe completo si faltó consultar insights.
            insights = api.get(x['id']+'/insights', {'metric':'reach'})
            for metric in insights.get('data',[]):
                if metric.get('name')=='reach':
                    values=metric.get('values',[])
                    selected[-1]['alcance']=values[0].get('value') if values else metric.get('total_value',{}).get('value')
        if len(selected)>100: raise ErrorRedes('Más de 100 publicaciones en el período. Acortalo para completar la consulta.')
    return account, selected


def consultar(fuente, desde, hasta):
    try:
        return _consultar(fuente, desde, hasta)
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ErrorRedes('Meta devolvió datos con un formato inesperado. Se conserva el informe anterior.') from None
