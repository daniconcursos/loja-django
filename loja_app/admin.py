from django.contrib import admin
from .models import Cliente, Produto, OrdemServico, Orcamento

admin.site.register(Cliente)
admin.site.register(Produto)
admin.site.register(OrdemServico)
admin.site.register(Orcamento)