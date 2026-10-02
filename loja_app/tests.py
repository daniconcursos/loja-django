from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Cliente, OrdemServico, Orcamento, OrcamentoItem, Produto


class OrdemServicoTests(TestCase):
	def setUp(self):
		self.owner = get_user_model().objects.create_user(
			username="owner",
			password="Test-password-456",
			is_staff=True,
			is_superuser=True,
		)
		self.client.force_login(self.owner)
		self.cliente = Cliente.objects.create(
			nome="Joana Silva",
			telefone="11999999999",
			cep="01000-000",
			rua="Rua Central",
			numero="10",
			bairro="Centro",
			cidade="São Paulo",
			estado="SP",
		)

	def test_visitante_e_redirecionado_para_login(self):
		self.client.logout()

		response = self.client.get(reverse("index"))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, f"{reverse('login')}?next={reverse('index')}")

	def test_proprietario_consegue_entrar_e_sair(self):
		self.client.logout()

		response = self.client.post(
			reverse("login"),
			{"username": "owner", "password": "Test-password-456"},
		)

		self.assertRedirects(response, reverse("index"))
		self.assertEqual(self.client.get(reverse("index")).status_code, 200)

		response = self.client.post(reverse("logout"))
		self.assertRedirects(response, reverse("login"))
		self.assertEqual(self.client.get(reverse("index")).status_code, 302)

	def test_funcionario_acessa_orcamentos_mas_nao_relatorio_financeiro(self):
		usuario = get_user_model().objects.create_user(
			username="usuario",
			password="Test-password-456",
		)
		self.client.force_login(usuario)

		for nome_rota in ("index", "clientes", "produtos", "servicos", "orcamentos", "novo_orcamento"):
			with self.subTest(rota=nome_rota):
				response = self.client.get(reverse(nome_rota))
				self.assertEqual(response.status_code, 200)

		self.assertContains(response, "Orçamentos")
		self.assertNotContains(response, "Recebimentos")
		self.assertRedirects(
			self.client.get(reverse("relatorio_recebimentos")),
			reverse("index"),
		)

	def test_funcionario_pode_cadastrar_orcamento(self):
		produto = Produto.objects.create(nome="Cabo", quantidade=5, preco="12.50")
		produto_adicional = Produto.objects.create(nome="Conector", quantidade=10, preco="3.00")
		usuario = get_user_model().objects.create_user(
			username="funcionario",
			password="Test-password-456",
		)
		self.client.force_login(usuario)

		response = self.client.post(
			reverse("novo_orcamento"),
			{
				"cliente": self.cliente.id,
				"descricao": "Orçamento cadastrado por funcionário",
				"produto": [produto.id, produto_adicional.id],
				"quantidade": ["2", "3"],
				"preco": ["20.00", "4.25"],
			},
		)

		self.assertRedirects(response, reverse("orcamentos"))
		orcamento = Orcamento.objects.get(descricao="Orçamento cadastrado por funcionário")
		self.assertEqual(orcamento.itens.count(), 2)
		self.assertEqual(orcamento.valor_total, Decimal("52.75"))

	def test_lista_de_orcamentos_exibe_acao_alterar(self):
		Orcamento.objects.create(cliente=self.cliente, descricao="Orçamento aberto")

		response = self.client.get(reverse("orcamentos"))

		self.assertContains(response, "Alterar")

	def test_editar_orcamento_atualiza_itens_e_reabre_como_rascunho(self):
		produto = Produto.objects.create(nome="Cabo", quantidade=5, preco="12.50")
		produto_adicional = Produto.objects.create(nome="Conector", quantidade=10, preco="3.00")
		orcamento = Orcamento.objects.create(
			cliente=self.cliente,
			descricao="Descrição antiga",
			status="Aprovado",
		)
		OrcamentoItem.objects.create(
			orcamento=orcamento,
			produto=produto,
			quantidade=1,
			preco_unitario="12.50",
		)

		response = self.client.post(
			reverse("editar_orcamento", args=[orcamento.id]),
			{
				"cliente": self.cliente.id,
				"descricao": "Descrição atualizada",
				"produto": [produto.id, produto_adicional.id],
				"quantidade": ["2", "3"],
				"preco": ["20.00", "4.25"],
			},
		)

		orcamento.refresh_from_db()
		self.assertRedirects(response, reverse("orcamentos"))
		self.assertEqual(Orcamento.objects.count(), 1)
		self.assertEqual(orcamento.descricao, "Descrição atualizada")
		self.assertEqual(orcamento.status, "Rascunho")
		self.assertEqual(orcamento.itens.count(), 2)
		self.assertEqual(orcamento.valor_total, Decimal("52.75"))

	def test_orcamento_finalizado_nao_pode_ser_alterado(self):
		produto = Produto.objects.create(nome="Cabo", quantidade=5, preco="12.50")
		orcamento = Orcamento.objects.create(
			cliente=self.cliente,
			descricao="Finalizado",
			status="Finalizado",
			data_finalizacao=timezone.now(),
		)
		OrcamentoItem.objects.create(
			orcamento=orcamento,
			produto=produto,
			quantidade=1,
			preco_unitario="12.50",
		)

		response = self.client.post(
			reverse("editar_orcamento", args=[orcamento.id]),
			{
				"cliente": self.cliente.id,
				"descricao": "Tentativa de alteração",
				"produto": [produto.id],
				"quantidade": ["10"],
				"preco": ["1.00"],
			},
		)

		orcamento.refresh_from_db()
		self.assertRedirects(response, reverse("orcamentos"))
		self.assertEqual(orcamento.descricao, "Finalizado")
		self.assertEqual(orcamento.status, "Finalizado")
		self.assertEqual(orcamento.valor_total, Decimal("12.50"))

	def test_tela_de_servicos_exibe_formulario_e_ordens(self):
		response = self.client.get(reverse("servicos"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Nova Ordem de Serviço")
		self.assertContains(response, "Cancelar")
		self.assertContains(response, "Ordens de Serviço cadastradas")

	def test_editar_ordem_atualiza_registro_existente(self):
		servico = OrdemServico.objects.create(
			cliente=self.cliente,
			descricao="Instalação",
			valor="50.00",
			status="Pendente",
		)

		response = self.client.post(
			reverse("editar_servico", args=[servico.id]),
			{
				"cliente": self.cliente.id,
				"descricao": "Instalação e manutenção",
				"valor": "80.00",
				"status": "Concluido",
			},
		)

		servico.refresh_from_db()
		self.assertRedirects(response, reverse("servicos"))
		self.assertEqual(OrdemServico.objects.count(), 1)
		self.assertEqual(servico.descricao, "Instalação e manutenção")
		self.assertEqual(str(servico.valor), "80.00")
		self.assertEqual(servico.status, "Concluido")

	def test_editar_cliente_atualiza_registro_existente(self):
		response = self.client.post(
			reverse("editar_cliente", args=[self.cliente.id]),
			{
				"nome": "Joana Silva",
				"telefone": "11888888888",
				"cep": "01000-000",
				"rua": "Rua Nova",
				"numero": "20",
				"bairro": "Centro",
				"cidade": "São Paulo",
				"estado": "SP",
			},
		)

		self.cliente.refresh_from_db()
		self.assertRedirects(response, reverse("clientes"))
		self.assertEqual(Cliente.objects.count(), 1)
		self.assertEqual(self.cliente.telefone, "11888888888")
		self.assertEqual(self.cliente.rua, "Rua Nova")

	def test_editar_produto_atualiza_registro_existente(self):
		produto = Produto.objects.create(nome="Cabo", quantidade=5, preco="12.50")

		response = self.client.post(
			reverse("editar_produto", args=[produto.id]),
			{"nome": "Cabo reforçado", "quantidade": 8, "preco": "15.00"},
		)

		produto.refresh_from_db()
		self.assertRedirects(response, reverse("produtos"))
		self.assertEqual(Produto.objects.count(), 1)
		self.assertEqual(produto.nome, "Cabo reforçado")
		self.assertEqual(produto.quantidade, 8)
		self.assertEqual(str(produto.preco), "15.00")

	def test_telas_de_orcamento_renderizam_com_layout(self):
		Produto.objects.create(nome="Cabo", quantidade=5, preco="12.50")

		for nome_rota in ("orcamentos", "novo_orcamento", "index"):
			with self.subTest(rota=nome_rota):
				response = self.client.get(reverse(nome_rota))
				self.assertEqual(response.status_code, 200)
				self.assertContains(response, "Sistema de Loja")
				if nome_rota == "novo_orcamento":
					self.assertContains(response, "Adicionar produto")

	def test_finalizar_orcamento_registra_status_e_data(self):
		orcamento = Orcamento.objects.create(
			cliente=self.cliente,
			descricao="Instalação",
			status="Aprovado",
		)

		response = self.client.post(reverse("finalizar_orcamento", args=[orcamento.id]))

		orcamento.refresh_from_db()
		self.assertRedirects(response, reverse("orcamentos"))
		self.assertEqual(orcamento.status, "Finalizado")
		self.assertIsNotNone(orcamento.data_finalizacao)

	def test_relatorio_soma_apenas_orcamentos_finalizados_no_periodo(self):
		produto = Produto.objects.create(nome="Cabo", quantidade=10, preco="10.00")
		data_finalizacao = timezone.now()
		finalizado = Orcamento.objects.create(
			cliente=self.cliente,
			status="Finalizado",
			data_finalizacao=data_finalizacao,
		)
		aprovado = Orcamento.objects.create(
			cliente=self.cliente,
			status="Aprovado",
		)
		OrcamentoItem.objects.create(
			orcamento=finalizado,
			produto=produto,
			quantidade=2,
			preco_unitario="10.00",
		)
		OrcamentoItem.objects.create(
			orcamento=aprovado,
			produto=produto,
			quantidade=4,
			preco_unitario="10.00",
		)
		dia = timezone.localtime(data_finalizacao).date().isoformat()

		response = self.client.get(
			reverse("relatorio_recebimentos"),
			{"inicio": dia, "fim": dia},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context["total_recebido"], Decimal("20.00"))
		self.assertEqual(list(response.context["orcamentos"]), [finalizado])
		self.assertContains(response, "Recebimentos por dia")
