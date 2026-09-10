from django.contrib import admin
from .models import Cliente, Produto, OrdemServico, Orcamento, OrcamentoItem

class OrcamentoItemInline(admin.TabularInline):
    model = OrcamentoItem
    extra = 1
    
    # Adicionamos um script rápido para injetar o valor automaticamente (opcional avançado)
    # Mas uma alternativa mais simples e nativa do Django é usar uma propriedade ou override no save.

# 2. Configura o Orçamento para usar esse bloco de itens
@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    inlines = [OrcamentoItemInline]
    list_display = ('id', 'cliente', 'status', 'data_criacao')

# Registra os outros modelos normalmente
admin.site.register(Cliente)
admin.site.register(Produto)
admin.site.register(OrdemServico)