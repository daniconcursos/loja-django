from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.index, name="index"),
    path("clientes/", views.cadastrar_cliente, name="clientes"),
    path("clientes/<int:cliente_id>/editar/", views.cadastrar_cliente, name="editar_cliente"),
    path("produtos/", views.cadastrar_produto, name="produtos"),
    path("produtos/<int:produto_id>/editar/", views.cadastrar_produto, name="editar_produto"),
    path("servicos/", views.cadastrar_servico, name="servicos"),
    path("servicos/<int:servico_id>/editar/", views.cadastrar_servico, name="editar_servico"),
    path("orcamentos/", views.listar_orcamentos, name="orcamentos"),
    path("orcamentos/<int:orcamento_id>/editar/", views.novo_orcamento, name="editar_orcamento"),
    path("orcamentos/<int:orcamento_id>/finalizar/", views.finalizar_orcamento, name="finalizar_orcamento"),
    path("novo-orcamento/", views.novo_orcamento, name="novo_orcamento"),
    path("relatorio-recebimentos/", views.relatorio_recebimentos, name="relatorio_recebimentos"),
]