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

import sqlite3
import random
import csv
import os
from datetime import datetime, timedelta

from faker import Faker

fake = Faker("pt_BR")
random.seed(42)        
Faker.seed(42)

N_AGENCIAS = 5
N_CLIENTES = 200
N_CONTAS = 300          
N_CARTOES = 250
N_TRANSACOES = 8000
N_EMPRESTIMOS = 60

OUTPUT_DB = "bancosim.db"
OUTPUT_DIR = "bronze"


def criar_schema(conn: sqlite3.Connection) -> None:
    """Cria as tabelas seguindo o DDL do projeto (com Conta_Origem/Destino)."""
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS Transacoes;
        DROP TABLE IF EXISTS Emprestimos;
        DROP TABLE IF EXISTS Cartoes;
        DROP TABLE IF EXISTS Contas;
        DROP TABLE IF EXISTS Tipos_Transacao;
        DROP TABLE IF EXISTS Agencias;
        DROP TABLE IF EXISTS Clientes;

        CREATE TABLE Clientes (
            Cliente_ID INTEGER PRIMARY KEY,
            Nome TEXT,
            CPF TEXT UNIQUE,
            Data_Nascimento TEXT
        );

        CREATE TABLE Agencias (
            Agencia_ID INTEGER PRIMARY KEY,
            Nome_Agencia TEXT,
            Cidade TEXT
        );

        CREATE TABLE Contas (
            Conta_ID INTEGER PRIMARY KEY,
            Cliente_ID INTEGER,
            Agencia_ID INTEGER,
            Saldo REAL,
            FOREIGN KEY (Cliente_ID) REFERENCES Clientes(Cliente_ID),
            FOREIGN KEY (Agencia_ID) REFERENCES Agencias(Agencia_ID)
        );

        CREATE TABLE Cartoes (
            Cartao_ID INTEGER PRIMARY KEY,
            Conta_ID INTEGER,
            Numero_Cartao_Mascarado TEXT,  -- só os 4 últimos dígitos ficam visíveis
            Tipo_Cartao TEXT,
            FOREIGN KEY (Conta_ID) REFERENCES Contas(Conta_ID)
        );

        CREATE TABLE Tipos_Transacao (
            Tipo_Transacao_ID INTEGER PRIMARY KEY,
            Descricao TEXT
        );

        CREATE TABLE Transacoes (
            Transacao_ID INTEGER PRIMARY KEY,
            Conta_Origem_ID INTEGER,
            Conta_Destino_ID INTEGER,
            Tipo_Transacao_ID INTEGER,
            Valor REAL,
            Data_Hora TEXT,
            FOREIGN KEY (Conta_Origem_ID) REFERENCES Contas(Conta_ID),
            FOREIGN KEY (Conta_Destino_ID) REFERENCES Contas(Conta_ID),
            FOREIGN KEY (Tipo_Transacao_ID) REFERENCES Tipos_Transacao(Tipo_Transacao_ID)
        );

        CREATE TABLE Emprestimos (
            Emprestimo_ID INTEGER PRIMARY KEY,
            Cliente_ID INTEGER,
            Valor_Contratado REAL,
            Parcelas INTEGER,
            Data_Contrato TEXT,
            FOREIGN KEY (Cliente_ID) REFERENCES Clientes(Cliente_ID)
        );

        CREATE INDEX idx_contas_cliente ON Contas(Cliente_ID);
        CREATE INDEX idx_contas_agencia ON Contas(Agencia_ID);
        CREATE INDEX idx_transacoes_origem ON Transacoes(Conta_Origem_ID);
        CREATE INDEX idx_transacoes_destino ON Transacoes(Conta_Destino_ID);
        CREATE INDEX idx_emprestimos_cliente ON Emprestimos(Cliente_ID);
        """
    )
    conn.commit()


def gerar_agencias(conn):
    cur = conn.cursor()
    dados = []
    for i in range(1, N_AGENCIAS + 1):
        dados.append((i, f"Agência {fake.city()}", fake.city()))
    cur.executemany("INSERT INTO Agencias VALUES (?, ?, ?)", dados)
    conn.commit()
    return [d[0] for d in dados]


def gerar_clientes(conn):
    cur = conn.cursor()
    dados = []
    cpfs_usados = set()
    for i in range(1, N_CLIENTES + 1):
        # evita colisão de CPF (Faker às vezes repete em volumes grandes)
        cpf = fake.cpf().replace(".", "").replace("-", "")
        while cpf in cpfs_usados:
            cpf = fake.cpf().replace(".", "").replace("-", "")
        cpfs_usados.add(cpf)

        nascimento = fake.date_of_birth(minimum_age=18, maximum_age=85)
        dados.append((i, fake.name(), cpf, nascimento.isoformat()))
    cur.executemany("INSERT INTO Clientes VALUES (?, ?, ?, ?)", dados)
    conn.commit()
    return [d[0] for d in dados]


def gerar_contas(conn, ids_clientes, ids_agencias):
    cur = conn.cursor()
    dados = []
    for i in range(1, N_CONTAS + 1):
        cliente_id = random.choice(ids_clientes)
        agencia_id = random.choice(ids_agencias)
        saldo = round(random.uniform(0, 50000), 2)
        dados.append((i, cliente_id, agencia_id, saldo))
    cur.executemany("INSERT INTO Contas VALUES (?, ?, ?, ?)", dados)
    conn.commit()
    return [d[0] for d in dados]


def gerar_cartoes(conn, ids_contas):
    cur = conn.cursor()
    dados = []
    tipos = ["Débito", "Crédito", "Múltiplo"]
    for i in range(1, N_CARTOES + 1):
        conta_id = random.choice(ids_contas)
        numero_completo = fake.credit_card_number()
        mascarado = "**** **** **** " + numero_completo[-4:]  # nunca guardamos o número cheio
        dados.append((i, conta_id, mascarado, random.choice(tipos)))
    cur.executemany("INSERT INTO Cartoes VALUES (?, ?, ?, ?)", dados)
    conn.commit()


def gerar_tipos_transacao(conn):
    cur = conn.cursor()
    tipos = [(1, "PIX"), (2, "TED"), (3, "DOC"), (4, "Boleto")]
    cur.executemany("INSERT INTO Tipos_Transacao VALUES (?, ?)", tipos)
    conn.commit()
    return [t[0] for t in tipos]


def gerar_transacoes(conn, ids_contas, ids_tipos):
    cur = conn.cursor()
    dados = []
    inicio = datetime(2025, 1, 1)
    for i in range(1, N_TRANSACOES + 1):
        origem, destino = random.sample(ids_contas, 2)  # nunca origem == destino
        tipo_id = random.choice(ids_tipos)
        valor = round(random.uniform(5, 5000), 2)
        data_hora = inicio + timedelta(
            days=random.randint(0, 300),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        dados.append((i, origem, destino, tipo_id, valor, data_hora.isoformat()))
    cur.executemany("INSERT INTO Transacoes VALUES (?, ?, ?, ?, ?, ?)", dados)
    conn.commit()


def gerar_emprestimos(conn, ids_clientes):
    cur = conn.cursor()
    dados = []
    for i in range(1, N_EMPRESTIMOS + 1):
        cliente_id = random.choice(ids_clientes)
        valor = round(random.uniform(1000, 30000), 2)
        parcelas = random.choice([12, 24, 36, 48, 60])
        data_contrato = fake.date_between(start_date="-2y", end_date="today")
        dados.append((i, cliente_id, valor, parcelas, data_contrato.isoformat()))
    cur.executemany("INSERT INTO Emprestimos VALUES (?, ?, ?, ?, ?)", dados)
    conn.commit()


def exportar_csvs(conn):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tabelas = [
        "Clientes", "Agencias", "Contas", "Cartoes",
        "Tipos_Transacao", "Transacoes", "Emprestimos",
    ]
    cur = conn.cursor()
    for tabela in tabelas:
        cur.execute(f"SELECT * FROM {tabela}")
        colunas = [desc[0] for desc in cur.description]
        linhas = cur.fetchall()
        caminho = os.path.join(OUTPUT_DIR, f"{tabela.lower()}_raw.csv")
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(colunas)
            writer.writerows(linhas)
        print(f"  -> {caminho} ({len(linhas)} linhas)")


def validar(conn):
    """Checagens simples de sanidade antes de seguir pro pipeline."""
    cur = conn.cursor()
    print("\nValidação:")
    for tabela in ["Clientes", "Agencias", "Contas", "Cartoes", "Transacoes", "Emprestimos"]:
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        print(f"  {tabela}: {cur.fetchone()[0]} linhas")

    cur.execute("SELECT COUNT(*) FROM Transacoes WHERE Conta_Origem_ID = Conta_Destino_ID")
    print(f"  Transações com origem == destino (deve ser 0): {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM Contas WHERE Saldo < 0")
    print(f"  Contas com saldo negativo (deve ser 0): {cur.fetchone()[0]}")


def main():
    conn = sqlite3.connect(OUTPUT_DB)
    print(f"Criando schema em {OUTPUT_DB}...")
    criar_schema(conn)

    print("Gerando dados (respeitando a ordem de dependência das FKs)...")
    ids_agencias = gerar_agencias(conn)
    ids_clientes = gerar_clientes(conn)
    ids_contas = gerar_contas(conn, ids_clientes, ids_agencias)
    gerar_cartoes(conn, ids_contas)
    ids_tipos = gerar_tipos_transacao(conn)
    gerar_transacoes(conn, ids_contas, ids_tipos)
    gerar_emprestimos(conn, ids_clientes)

    validar(conn)

    print(f"\nExportando CSVs para a pasta '{OUTPUT_DIR}/' (camada Bronze)...")
    exportar_csvs(conn)

    conn.close()
    print("\nConcluído.")


if __name__ == "__main__":
    main()
