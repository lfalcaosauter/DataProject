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

## Modelagem do banco (OLTP)

O banco transacional simula o dia a dia de um banco digital: abertura de
contas, cartões, empréstimos e transações entre contas. Os dados são gerados
de forma sintética via Python (Faker).

O DER completo e o script de criação (DDL) estão em `sql/`.

### Dicionário de dados

| Tabela | Campos-chave | Descrição resumida |
|---|---|---|
| Agencia | Agencia_ID (PK) | Agências bancárias |
| Cliente | Cliente_ID (PK) | Titulares das contas |
| Contas | Conta_ID (PK), Cliente_ID (FK), Agencia_ID (FK) | Contas bancárias, vinculadas a cliente e agência |
| Cartão | Cartão_ID (PK), Conta_ID (FK) | Cartões emitidos por conta |
| Empréstimos | Emprestimo_ID (PK), Cliente_ID (FK) | Empréstimos contratados por cliente |
| Transação_Tipo | Tipo_ID (PK) | Tipos de operação (PIX, TED, Saque, Depósito) |
| Transações | Transação_ID (PK), Conta_Origem_ID (FK), Conta_Destino_ID (FK), Tipo_Transacao_ID (FK) | Movimentações entre contas |



## Arquitetura de dados (Medallion)

- **Bronze**: cópia fiel dos dados extraídos do OLTP, sem tratamento.
- **Silver**: dados limpos e padronizados (deduplicação, tratamento de nulos,
  padronização de CPF e fuso horário).
- **Gold**: tabelas agregadas para consumo em BI (saldo por agência,
  movimentação PIX diária, perfil de risco de inadimplência).

