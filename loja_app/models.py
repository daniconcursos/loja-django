from django.db import models
from decimal import Decimal # Importante para fazer cálculos exatos com dinheiro

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
    # Opções de margem de lucro disponíveis no sistema
    MARGEM_CHOICES = [
        (Decimal('1.30'), '30%'),
        (Decimal('1.35'), '35% (Padrão)'),
        (Decimal('1.40'), '40%'),
        (Decimal('1.50'), '50%'),
        (Decimal('2.00'), '100% (Dobro)'),
    ]

    nome = models.CharField(max_length=150)
    valor_custo = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campo de margem com 35% (1.35) definido como o padrão automático
    margem_lucro = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        choices=MARGEM_CHOICES, 
        default=Decimal('1.35')
    )

    @property
    def valor_venda(self):
        # Multiplica o custo pelo valor da margem selecionada
        preco_final = self.valor_custo * self.margem_lucro
        return round(preco_final, 2)

    def __str__(self):
        # Pega a porcentagem visual para exibir bonito no painel
        margem_porcentagem = int((self.margem_lucro - 1) * 100)
        return f"{self.nome} - Custo: R${self.valor_custo} | Venda ({margem_porcentagem}%): R${self.valor_venda}"
    
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
    status = models.CharField(max_length=20,
        choices=[
            ("Rascunho", "Rascunho"),
            ("Enviado", "Enviado"),
            ("Aprovado", "Aprovado"),
            ("Rejeitado", "Rejeitado"),
        ],
        default="Rascunho"
    )

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
    preço_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *kwargs):
        # Se o preço unitário não foi preenchido, puxa automaticamente o valor de venda calculado do produto
        if not self.preço_unitario:
            self.preço_unitario = self.produto.valor_venda
        super().save(*kwargs)

    @property
    def subtotal(self):
        return self.quantidade * self.preço_unitario