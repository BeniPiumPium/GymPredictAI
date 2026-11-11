from datetime import timedelta
from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import InformeSocial
from .redes_api import consultar, configuracion, ErrorRedes

class PeriodoForm(forms.Form):
    fuente = forms.ChoiceField(choices=[('anuncios','Campañas pagas de Meta'),('instagram','Publicaciones de Instagram'),('facebook','Publicaciones de Facebook')])
    desde = forms.DateField(widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d'))
    hasta = forms.DateField(widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d'))
    def clean(self):
        d=super().clean()
        if d.get('desde') and d.get('hasta'):
            if not 0 <= (d['hasta']-d['desde']).days <= 90: raise forms.ValidationError('Elegí un período de hasta 91 días, con inicio anterior al final.')
            if d['hasta'] >= timezone.localdate(): raise forms.ValidationError('Elegí como máximo ayer para evitar días incompletos.')
        return d

@require_http_methods(['GET','POST'])
def redes(request):
    today=timezone.localdate()
    form=PeriodoForm(request.POST if request.method=='POST' else request.GET or None, initial={'desde':today-timedelta(days=30),'hasta':today-timedelta(days=1)})
    report=None
    if request.method=='POST':
        if not request.user.is_superuser: raise PermissionDenied
        if form.is_valid():
            d=form.cleaned_data
            try:
                account,rows=consultar(d['fuente'],d['desde'],d['hasta'])
                report,_=InformeSocial.objects.update_or_create(fuente=d['fuente'],cuenta=account,desde=d['desde'],hasta=d['hasta'],defaults={'filas':rows,'usuario':request.user})
                messages.success(request,'Estadísticas consultadas y guardadas. No se modificó ninguna publicación ni campaña.')
                return redirect('/redes/?informe='+str(report.pk))
            except ErrorRedes as error: form.add_error(None,str(error))
    elif request.GET.get('informe','').isdigit():
        report=InformeSocial.objects.filter(pk=request.GET['informe']).first()
    status=[]
    for source,label in PeriodoForm.base_fields['fuente'].choices:
        try: configuracion(source); ready=True
        except ErrorRedes: ready=False
        status.append({'nombre':label,'lista':ready})
    return render(request,'predicciones/redes.html',{'formulario':form,'informe':report,'informes':InformeSocial.objects.all()[:30],'estados':status})
