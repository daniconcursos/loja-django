from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from .models import Cliente, Produto, OrdemServico, Orcamento, OrcamentoItem


def owner_required(view_func):
    @wraps(view_func)
    @login_required(login_url="login")
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Esta área é exclusiva do proprietário.")
            return redirect("index")
        return view_func(request, *args, **kwargs)

    return wrapped_view


@login_required(login_url="login")
def index(request):
    clientes = Cliente.objects.all()
    produtos = Produto.objects.all()
    servicos = OrdemServico.objects.all()
    orcamentos = Orcamento.objects.all()

    return render(request, "loja_app/index.html", {
        "clientes": clientes,
        "produtos": produtos,
        "servicos": servicos,
        "orcamentos": orcamentos,
    })


@login_required(login_url="login")
def cadastrar_cliente(request, cliente_id=None):
    cliente = None
    if cliente_id is not None:
        cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == "POST":
        nome = request.POST.get("nome")
        telefone = request.POST.get("telefone")
        cep = request.POST.get("cep")
        rua = request.POST.get("rua")
        numero = request.POST.get("numero")
        bairro = request.POST.get("bairro")
        cidade = request.POST.get("cidade")
        estado = request.POST.get("estado")

        if cliente is None:
            Cliente.objects.create(
                nome=nome,
                telefone=telefone,
                cep=cep,
                rua=rua,
                numero=numero,
                bairro=bairro,
                cidade=cidade,
                estado=estado
            )
        else:
            cliente.nome = nome
            cliente.telefone = telefone
            cliente.cep = cep
            cliente.rua = rua
            cliente.numero = numero
            cliente.bairro = bairro
            cliente.cidade = cidade
            cliente.estado = estado
            cliente.save()

        return redirect("clientes")

    clientes = Cliente.objects.all().order_by("nome")
    return render(request, "loja_app/clientes.html", {
        "clientes": clientes,
        "cliente": cliente,
    })


@login_required(login_url="login")
def cadastrar_produto(request, produto_id=None):
    produto = None
    if produto_id is not None:
        produto = get_object_or_404(Produto, id=produto_id)

    if request.method == "POST":
        nome = request.POST.get("nome")
        quantidade = request.POST.get("quantidade")
        preco = request.POST.get("preco")

        if produto is None:
            Produto.objects.create(
                nome=nome,
                quantidade=quantidade,
                preco=preco
            )
        else:
            produto.nome = nome
            produto.quantidade = quantidade
            produto.preco = preco
            produto.save()

        return redirect("produtos")

    produtos = Produto.objects.all().order_by("nome")
    return render(request, "loja_app/produtos.html", {
        "produtos": produtos,
        "produto": produto,
    })


@login_required(login_url="login")
def cadastrar_servico(request, servico_id=None):
    servico = None
    if servico_id is not None:
        servico = get_object_or_404(OrdemServico, id=servico_id)

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        descricao = request.POST.get("descricao")
        valor = request.POST.get("valor")
        status = request.POST.get("status")

        cliente = get_object_or_404(Cliente, id=cliente_id)

        if servico is None:
            OrdemServico.objects.create(
                cliente=cliente,
                descricao=descricao,
                valor=valor,
                status=status
            )
        else:
            servico.cliente = cliente
            servico.descricao = descricao
            servico.valor = valor
            servico.status = status
            servico.save()

        return redirect("servicos")

    clientes = Cliente.objects.all()
    servicos = OrdemServico.objects.select_related("cliente").order_by("-data_criacao")
    return render(request, "loja_app/servicos.html", {
        "clientes": clientes,
        "servicos": servicos,
        "servico": servico,
    })


@login_required(login_url="login")
def listar_orcamentos(request):
    orcamentos = Orcamento.objects.select_related("cliente").order_by("-data_criacao")
    return render(request, "loja_app/orcamentos.html", {"orcamentos": orcamentos})


@login_required(login_url="login")
@require_POST
def finalizar_orcamento(request, orcamento_id):
    orcamento = get_object_or_404(Orcamento, id=orcamento_id)
    if orcamento.status not in ("Rejeitado", "Finalizado"):
        orcamento.status = "Finalizado"
        orcamento.data_finalizacao = timezone.now()
        orcamento.save(update_fields=["status", "data_finalizacao"])

    return redirect("orcamentos")


@owner_required
def relatorio_recebimentos(request):
    hoje = timezone.localdate()
    inicio_padrao = date(hoje.year, hoje.month, 1)
    inicio_param = request.GET.get("inicio", "")
    fim_param = request.GET.get("fim", "")
    inicio = parse_date(inicio_param) if inicio_param else inicio_padrao
    fim = parse_date(fim_param) if fim_param else hoje
    erro = ""

    if inicio is None or fim is None:
        erro = "Informe as datas no formato válido."
        inicio = inicio or inicio_padrao
        fim = fim or hoje
    elif inicio > fim:
        erro = "A data inicial deve ser anterior ou igual à data final."

    orcamentos = Orcamento.objects.none()
    total_recebido = Decimal("0.00")
    chart_labels = []
    chart_values = []
    agrupamento = "dia"

    if not erro:
        orcamentos = Orcamento.objects.filter(
            status="Finalizado",
            data_finalizacao__date__gte=inicio,
            data_finalizacao__date__lte=fim,
        ).select_related("cliente").prefetch_related("itens").order_by("-data_finalizacao")

        dias_no_periodo = (fim - inicio).days
        if dias_no_periodo <= 31:
            dias = [inicio + timedelta(days=offset) for offset in range(dias_no_periodo + 1)]
            valores_por_periodo = {dia: Decimal("0.00") for dia in dias}
            for orcamento in orcamentos:
                dia = timezone.localtime(orcamento.data_finalizacao).date()
                valores_por_periodo[dia] += orcamento.valor_total
            chart_labels = [dia.strftime("%d/%m") for dia in dias]
            chart_values = [float(valores_por_periodo[dia]) for dia in dias]
        else:
            agrupamento = "mês"
            meses = []
            cursor = date(inicio.year, inicio.month, 1)
            while cursor <= fim:
                meses.append((cursor.year, cursor.month))
                if cursor.month == 12:
                    cursor = date(cursor.year + 1, 1, 1)
                else:
                    cursor = date(cursor.year, cursor.month + 1, 1)

            valores_por_periodo = {mes: Decimal("0.00") for mes in meses}
            for orcamento in orcamentos:
                finalizado_em = timezone.localtime(orcamento.data_finalizacao)
                chave_mes = (finalizado_em.year, finalizado_em.month)
                valores_por_periodo[chave_mes] += orcamento.valor_total
            chart_labels = [f"{mes:02d}/{ano}" for ano, mes in meses]
            chart_values = [float(valores_por_periodo[mes]) for mes in meses]

        for orcamento in orcamentos:
            total_recebido += orcamento.valor_total

    return render(request, "loja_app/relatorio_recebimentos.html", {
        "orcamentos": orcamentos,
        "total_recebido": total_recebido,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "inicio": inicio,
        "fim": fim,
        "erro": erro,
        "agrupamento": agrupamento,
    })


@login_required(login_url="login")
def novo_orcamento(request, orcamento_id=None):
    orcamento = None
    if orcamento_id is not None:
        orcamento = get_object_or_404(Orcamento, id=orcamento_id)
        if orcamento.status == "Finalizado":
            messages.error(request, "Orçamentos finalizados não podem ser alterados.")
            return redirect("orcamentos")

    clientes = Cliente.objects.all()
    produtos = Produto.objects.all()

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        cliente = get_object_or_404(Cliente, id=cliente_id)
        produtos_ids = request.POST.getlist("produto")
        quantidades = request.POST.getlist("quantidade")
        precos = request.POST.getlist("preco")
        destino = "editar_orcamento" if orcamento else "novo_orcamento"
        argumentos_destino = [orcamento.id] if orcamento else []

        if (
            not produtos_ids
            or len(produtos_ids) != len(quantidades)
            or len(produtos_ids) != len(precos)
            or any(not produto_id for produto_id in produtos_ids)
        ):
            messages.error(request, "Adicione pelo menos um produto com quantidade e preço.")
            return redirect(destino, *argumentos_destino)

        itens = []
        for produto_id, quantidade_enviada, preco_enviado in zip(produtos_ids, quantidades, precos):
            produto = get_object_or_404(Produto, id=produto_id)
            try:
                quantidade = int(quantidade_enviada)
                preco = Decimal(preco_enviado)
            except (InvalidOperation, ValueError):
                messages.error(request, "Confira a quantidade e o preço de cada produto.")
                return redirect(destino, *argumentos_destino)

            if quantidade < 1 or preco < 0:
                messages.error(request, "A quantidade deve ser maior que zero e o preço não pode ser negativo.")
                return redirect(destino, *argumentos_destino)

            itens.append((produto, quantidade, preco))

        with transaction.atomic():
            if orcamento:
                orcamento.cliente = cliente
                orcamento.descricao = request.POST.get("descricao", "")
                orcamento.status = "Rascunho"
                orcamento.save(update_fields=["cliente", "descricao", "status"])
                orcamento.itens.all().delete()
            else:
                orcamento = Orcamento.objects.create(
                    cliente=cliente,
                    descricao=request.POST.get("descricao", ""),
                    status="Rascunho"
                )

            OrcamentoItem.objects.bulk_create([
                OrcamentoItem(
                    orcamento=orcamento,
                    produto=produto,
                    quantidade=quantidade,
                    preco_unitario=preco,
                )
                for produto, quantidade, preco in itens
            ])

        if orcamento_id is not None:
            messages.success(request, "Orçamento alterado. O status voltou para Rascunho.")

        return redirect("orcamentos")

    linhas = []
    if orcamento:
        linhas = [
            {
                "produto_id": item.produto_id,
                "quantidade": item.quantidade,
                "preco": item.preco_unitario,
            }
            for item in orcamento.itens.all()
        ]
    if not linhas:
        linhas = [{"produto_id": "", "quantidade": 1, "preco": ""}]

    return render(request, "loja_app/novo_orcamento.html", {
        "clientes": clientes,
        "produtos": produtos,
        "orcamento": orcamento,
        "linhas": linhas,
    })