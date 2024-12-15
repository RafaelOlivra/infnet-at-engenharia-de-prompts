# AT: Engenharia de Prompts para Ciência de Dados [24E4_4]

**Rafael Soares de Oliveira**

Infnet - Ciência de Dados | Dezembro 2024

https://lms.infnet.edu.br/moodle/mod/assign/view.php?id=413838

---

## Como iniciar o projeto

### 1. Configurar o ambiente virtual

Execute os comandos abaixo no terminal para criar e ativar um ambiente virtual e instalar as dependências necessárias:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Inicializar o Streamlit

```console
streamlit run src/dashboard.py
```

Acesse o projeto no navegador no endereço http://localhost:8501 (ou no endereço exibido no console).

#### Dica para usuários do VSCode

Após instalar as dependências, você pode executar o projeto diretamente no VSCode usando o atalho Ctrl+F5 (ou um comando equivalente no seu sistema operacional).
