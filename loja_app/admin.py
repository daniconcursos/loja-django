from django.contrib import admin
from .models import Cliente, Produto, Orcamento, OrcamentoItem, OrdemServico

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    search_fields = ('nome',)

    class Media:
        js = ('js/viacep.js',)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    search_fields = ('nome',)

class OrcamentoItemInline(admin.TabularInline):
    model = OrcamentoItem
    extra = 1

@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    inlines = [OrcamentoItemInline]

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    search_fields = ('status',)