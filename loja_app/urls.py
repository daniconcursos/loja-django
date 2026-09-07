from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("clientes/", views.cadastrar_cliente, name="clientes"),
    path("produtos/", views.cadastrar_produto, name="produtos"),
    path("servicos/", views.cadastrar_servico, name="servicos"),
    path("orcamentos/", views.listar_orcamentos, name="orcamentos"),
    path("novo-orcamento/", views.novo_orcamento, name="novo_orcamento"),
]