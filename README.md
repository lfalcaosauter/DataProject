# Pipeline Analítico de Transações Bancárias

Projeto prático de engenharia de dados: simulação de um ambiente bancário
(OLTP) e construção de um pipeline analítico seguindo a Arquitetura
Medallion (Bronze, Silver, Gold).

## Estrutura do projeto

```
DataProject/
├── data/               # dados gerados (não versionado, ver .gitignore)
│   └── bronze/
├── scripts/            # pipeline em Python, em ordem de execução
├── sql/                # DDL e queries analíticas
└── docs/               # documentação do projeto
```

## Como rodar

```bash
pip install -r requirements.txt
python3 scripts/01_gerar_dados_fake.py     # cria o OLTP simulado (Faker)
python3 scripts/02_extracao_bronze.py       # extrai OLTP -> camada Bronze
```

## Status

- [x] Modelagem do banco (OLTP)
- [x] Geração de dados sintéticos (Faker)
- [x] Extração para camada Bronze
- [ ] Transformação para camada Silver
- [ ] Agregações para camada Gold
- [ ] Escolha e configuração da hospedagem em nuvem
