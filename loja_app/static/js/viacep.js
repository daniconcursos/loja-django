document.addEventListener('DOMContentLoaded', function () {
    const cepInput = document.getElementById('id_cep');
    if (!cepInput) return;

    cepInput.addEventListener('blur', function () {
        const cep = this.value.replace(/\D/g, '');
        
        if (cep.length === 8) {
            fetch(`https://viacep.com.br/ws/${cep}/json/`)
                .then(response => response.json())
                .then(data => {
                    if (!data.erro) {
                        const rua = document.getElementById('id_rua');
                        const bairro = document.getElementById('id_bairro');
                        const cidade = document.getElementById('id_cidade');
                        const estado = document.getElementById('id_estado');

                        if (rua) rua.value = data.logradouro;
                        if (bairro) bairro.value = data.bairro;
                        if (cidade) cidade.value = data.localidade;
                        if (estado) estado.value = data.uf;

                        const numero = document.getElementById('id_numero');
                        if (numero) numero.focus();
                    } else {
                        alert('CEP não encontrado pelo ViaCEP.');
                    }
                })
                .catch(() => {
                    alert('Erro ao buscar o CEP.');
                });
        }
    });
});