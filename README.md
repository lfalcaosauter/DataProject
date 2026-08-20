# Pipeline Analítico de Transações Bancárias

Projeto prático de engenharia de dados: simulação de um ambiente bancário
(OLTP) e construção de um pipeline analítico seguindo a Arquitetura
Medallion (Bronze, Silver, Gold).

## Estrutura do projeto

```
DataProject/
├── data/              
│   └── bronze/
├── scripts/            
├── sql/               
└── docs/              
```

## Como rodar

```bash
pip install -r requirements.txt
python3 scripts/dados_fake.py     
python3 scripts/bronze.py      
```
