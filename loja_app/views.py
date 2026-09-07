from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente, Produto, OrdemServico, Orcamento, OrcamentoItem


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


def cadastrar_cliente(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        telefone = request.POST.get("telefone")
        cep = request.POST.get("cep")
        rua = request.POST.get("rua")
        bairro = request.POST.get("bairro")
        cidade = request.POST.get("cidade")
        estado = request.POST.get("estado")

        Cliente.objects.create(
            nome=nome,
            telefone=telefone,
            cep=cep,
            rua=rua,
            bairro=bairro,
            cidade=cidade,
            estado=estado
        )

        return redirect("index")

    return render(request, "loja_app/clientes.html")


def cadastrar_produto(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        quantidade = request.POST.get("quantidade")
        preco = request.POST.get("preco")

        Produto.objects.create(
            nome=nome,
            quantidade=quantidade,
            preco=preco
        )

        return redirect("index")

    return render(request, "loja_app/produtos.html")


def cadastrar_servico(request):
    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        descricao = request.POST.get("descricao")
        valor = request.POST.get("valor")
        status = request.POST.get("status")

        cliente = get_object_or_404(Cliente, id=cliente_id)

        OrdemServico.objects.create(
            cliente=cliente,
            descricao=descricao,
            valor=valor,
            status=status
        )

        return redirect("index")

    clientes = Cliente.objects.all()
    return render(request, "loja_app/servicos.html", {"clientes": clientes})


def listar_orcamentos(request):
    orcamentos = Orcamento.objects.all()
    return render(request, "loja_app/orcamentos.html", {"orcamentos": orcamentos})


def novo_orcamento(request):
    clientes = Cliente.objects.all()
    produtos = Produto.objects.all()

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        cliente = get_object_or_404(Cliente, id=cliente_id)

        orcamento = Orcamento.objects.create(
            cliente=cliente,
            descricao=request.POST.get("descricao", ""),
            status="Rascunho"
        )

        produtos_ids = request.POST.getlist("produto")
        quantidades = request.POST.getlist("quantidade")
        precos = request.POST.getlist("preco")

        for i, produto_id in enumerate(produtos_ids):
            produto = get_object_or_404(Produto, id=produto_id)
            quantidade = int(quantidades[i])
            preco = float(precos[i])

            OrcamentoItem.objects.create(
                orcamento=orcamento,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco
            )

        return redirect("orcamentos")

    return render(request, "loja_app/novo_orcamento.html", {
        "clientes": clientes,
        "produtos": produtos
    })