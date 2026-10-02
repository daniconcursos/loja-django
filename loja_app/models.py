from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20)
    cep = models.CharField(max_length=9)
    rua = models.CharField(max_length=200)
    bairro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20, blank=True, null=True)
    cidade = models.CharField(max_length=200)
    estado = models.CharField(max_length=2)
    
    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=200)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nome


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ("Pendente", "Pendente"),
        ("Concluido", "Concluído"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    descricao = models.TextField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pendente")
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OS {self.id} - {self.cliente.nome}"


class Orcamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    descricao = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Rascunho", "Rascunho"),
            ("Enviado", "Enviado"),
            ("Aprovado", "Aprovado"),
            ("Rejeitado", "Rejeitado"),
            ("Finalizado", "Finalizado"),
        ],
        default="Rascunho"
    )
    data_finalizacao = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Orçamento {self.id} - {self.cliente.nome}"

    @property
    def valor_total(self):
        total = 0
        for item in self.itens.all():
            total += item.quantidade * item.preco_unitario
        return total


class OrcamentoItem(models.Model):
    orcamento = models.ForeignKey(Orcamento, related_name="itens", on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.produto.nome} ({self.quantidade})"