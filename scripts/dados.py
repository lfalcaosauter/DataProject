"""
Gerador de dados fake para o projeto de Pipeline de Transacoes Bancarias.

O script respeita a ordem de dependencia das tabelas (quem tem FK precisa
que a tabela "pai" ja exista), senao o banco recusa a insercao:

    Agencias, Clientes  ->  Contas  ->  Cartoes, Transacoes, Emprestimos

Saida:
    - bancosim.db          (SQLite simulando o OLTP)
    - bronze/*.csv          (uma copia fiel de cada tabela, pronta pra
                              servir de camada Bronze do pipeline)
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta
 
from faker import Faker

random.seed(42)
Faker.seed(42)
fake = Faker("pt_BR")
 
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "oltp.db")
 
N_AGENCIAS = 10
N_CLIENTES = 500
N_TRANSACOES = 5000
PCT_CLIENTES_COM_EMPRESTIMO = 0.3
 
TIPOS_TRANSACAO = ["PIX", "TED", "DOC", "Saque", "Depósito"]
TIPOS_CARTAO = ["Crédito", "Débito", "Múltiplo"]
 

def criar_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS Transacoes;
        DROP TABLE IF EXISTS Emprestimos;
        DROP TABLE IF EXISTS Cartao;
        DROP TABLE IF EXISTS Contas;
        DROP TABLE IF EXISTS Transacao_Tipo;
        DROP TABLE IF EXISTS Cliente;
        DROP TABLE IF EXISTS Agencia;
 
        CREATE TABLE Agencia (
            Agencia_ID INTEGER PRIMARY KEY,
            Nome_Agencia TEXT NOT NULL,
            Cidade TEXT NOT NULL
        );
 
        CREATE TABLE Cliente (
            Cliente_ID INTEGER PRIMARY KEY,
            Nome TEXT NOT NULL,
            CPF TEXT NOT NULL,
            Data_Nascimento TEXT NOT NULL
        );
 
        CREATE TABLE Contas (
            Conta_ID INTEGER PRIMARY KEY,
            Cliente_ID INTEGER NOT NULL,
            Agencia_ID INTEGER NOT NULL,
            Saldo REAL NOT NULL,
            FOREIGN KEY (Cliente_ID) REFERENCES Cliente(Cliente_ID),
            FOREIGN KEY (Agencia_ID) REFERENCES Agencia(Agencia_ID)
        );
 
        CREATE TABLE Cartao (
            Cartao_ID INTEGER PRIMARY KEY,
            Conta_ID INTEGER NOT NULL,
            Numero_Cartao_Mascarado TEXT NOT NULL,
            Tipo_Cartao TEXT NOT NULL,
            FOREIGN KEY (Conta_ID) REFERENCES Contas(Conta_ID)
        );
 
        CREATE TABLE Emprestimos (
            Emprestimo_ID INTEGER PRIMARY KEY,
            Cliente_ID INTEGER NOT NULL,
            Valor_Contratado REAL NOT NULL,
            Parcelas INTEGER NOT NULL,
            Data_Contrato TEXT NOT NULL,
            FOREIGN KEY (Cliente_ID) REFERENCES Cliente(Cliente_ID)
        );
 
        CREATE TABLE Transacao_Tipo (
            Tipo_ID INTEGER PRIMARY KEY,
            Descricao TEXT NOT NULL
        );
 
        CREATE TABLE Transacoes (
            Transacao_ID INTEGER PRIMARY KEY,
            Conta_Origem_ID INTEGER NOT NULL,
            Conta_Destino_ID INTEGER,
            Tipo_Transacao_ID INTEGER NOT NULL,
            Valor REAL,
            Data_Hora TEXT NOT NULL,
            FOREIGN KEY (Conta_Origem_ID) REFERENCES Contas(Conta_ID),
            FOREIGN KEY (Conta_Destino_ID) REFERENCES Contas(Conta_ID),
            FOREIGN KEY (Tipo_Transacao_ID) REFERENCES Transacao_Tipo(Tipo_ID)
        );
        """
    )
    conn.commit()
 
def gerar_agencias(conn: sqlite3.Connection) -> list[int]:
    rows = [
        (i, f"Agência {fake.city()}", fake.city())
        for i in range(1, N_AGENCIAS + 1)
    ]
    conn.executemany(
        "INSERT INTO Agencia (Agencia_ID, Nome_Agencia, Cidade) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return [r[0] for r in rows]
 
 
def gerar_clientes(conn: sqlite3.Connection) -> list[int]:
    rows = []
    for i in range(1, N_CLIENTES + 1):
        nome = fake.name()
        # CPF propositalmente "sujo" (com pontos e traço) para a Silver limpar
        cpf = fake.cpf()
        nascimento = fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()
        rows.append((i, nome, cpf, nascimento))
    conn.executemany(
        "INSERT INTO Cliente (Cliente_ID, Nome, CPF, Data_Nascimento) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return [r[0] for r in rows]
 
 
def gerar_contas(conn: sqlite3.Connection, clientes: list[int], agencias: list[int]) -> list[int]:
    rows = []
    conta_id = 1
    for cliente_id in clientes:
        for _ in range(random.randint(1, 2)):
            saldo = round(random.uniform(-500, 50000), 2)
            agencia_id = random.choice(agencias)
            rows.append((conta_id, cliente_id, agencia_id, saldo))
            conta_id += 1
    conn.executemany(
        "INSERT INTO Contas (Conta_ID, Cliente_ID, Agencia_ID, Saldo) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return [r[0] for r in rows]
 
 
def gerar_cartoes(conn: sqlite3.Connection, contas: list[int]) -> None:
    rows = []
    cartao_id = 1
    for conta_id in contas:
        for _ in range(random.randint(0, 2)):
            numero_mascarado = f"**** **** **** {fake.credit_card_number()[-4:]}"
            tipo = random.choice(TIPOS_CARTAO)
            rows.append((cartao_id, conta_id, numero_mascarado, tipo))
            cartao_id += 1
    conn.executemany(
        """INSERT INTO Cartao
           (Cartao_ID, Conta_ID, Numero_Cartao_Mascarado, Tipo_Cartao)
           VALUES (?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
 
 
def gerar_emprestimos(conn: sqlite3.Connection, clientes: list[int]) -> None:
    rows = []
    emprestimo_id = 1
    qtd_com_emprestimo = int(len(clientes) * PCT_CLIENTES_COM_EMPRESTIMO)
    clientes_selecionados = random.sample(clientes, qtd_com_emprestimo)
    for cliente_id in clientes_selecionados:
        for _ in range(random.randint(1, 2)):
            valor = round(random.uniform(1000, 80000), 2)
            parcelas = random.choice([12, 24, 36, 48, 60])
            data_contrato = fake.date_between(start_date="-3y", end_date="today").isoformat()
            rows.append((emprestimo_id, cliente_id, valor, parcelas, data_contrato))
            emprestimo_id += 1
    conn.executemany(
        """INSERT INTO Emprestimos
           (Emprestimo_ID, Cliente_ID, Valor_Contratado, Parcelas, Data_Contrato)
           VALUES (?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
 
 
def gerar_tipos_transacao(conn: sqlite3.Connection) -> list[int]:
    rows = [(i + 1, tipo) for i, tipo in enumerate(TIPOS_TRANSACAO)]
    conn.executemany(
        "INSERT INTO Transacao_Tipo (Tipo_ID, Descricao) VALUES (?, ?)", rows
    )
    conn.commit()
    return [r[0] for r in rows]
 
 
def gerar_transacoes(conn: sqlite3.Connection, contas: list[int], tipos: list[int]) -> None:
    rows = []
    for transacao_id in range(1, N_TRANSACOES + 1):
        conta_origem = random.choice(contas)
        conta_destino = random.choice([c for c in contas if c != conta_origem])
        tipo_id = random.choice(tipos)
        valor = round(random.uniform(5, 15000), 2)
 
        if random.random() < 0.01:
            valor = None
 
        data_hora_naive = fake.date_time_between(start_date="-90d", end_date="now")
 
        # Fusos horários misturados de propósito: metade em horário de
        # Brasília (-03:00), metade em UTC (+00:00). A Silver padroniza isso.
        offset = "-03:00" if random.random() < 0.5 else "+00:00"
        data_hora = f"{data_hora_naive.isoformat()}{offset}"
 
        rows.append((transacao_id, conta_origem, conta_destino, tipo_id, valor, data_hora))
 
    conn.executemany(
        """INSERT INTO Transacoes
           (Transacao_ID, Conta_Origem_ID, Conta_Destino_ID, Tipo_Transacao_ID, Valor, Data_Hora)
           VALUES (?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
 

def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
 
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
 
    conn = sqlite3.connect(DB_PATH)
    try:
        criar_schema(conn)
 
        agencias = gerar_agencias(conn)
        clientes = gerar_clientes(conn)
        contas = gerar_contas(conn, clientes, agencias)
        gerar_cartoes(conn, contas)
        gerar_emprestimos(conn, clientes)
        tipos = gerar_tipos_transacao(conn)
        gerar_transacoes(conn, contas, tipos)
 
        print(f"[dados.py] Banco OLTP gerado em '{DB_PATH}'")
        print(f"[dados.py] Agencias={len(agencias)} | Clientes={len(clientes)} | "
              f"Contas={len(contas)} | Transacoes>={N_TRANSACOES}")
    finally:
        conn.close()
 
 
if __name__ == "__main__":
    main()
 