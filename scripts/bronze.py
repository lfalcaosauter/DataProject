"""
Extracao: OLTP (bancosim.db) -> Camada Bronze

Este script simula o processo real de extracao de um pipeline de dados:
ele NAO sabe como os dados foram criados (poderiam vir de um app bancario
de verdade), apenas se conecta ao banco transacional e copia o conteudo
"as is" para a camada Bronze, com colunas de auditoria adicionadas.

Estrategia usada aqui: FULL LOAD (recarrega tudo a cada execucao).
Isso e adequado pra um projeto pequeno/simulado. Em um cenario com volume
maior, o proximo passo natural seria uma extracao INCREMENTAL, usando uma
coluna de watermark (ex: MAX(Transacao_ID) ou Data_Hora ja processada) pra
extrair so o que e novo desde a ultima execucao.
"""

import sqlite3
import os
import uuid
from datetime import datetime

import pandas as pd

DB_PATH = "bancosim.db"
BRONZE_DIR = "bronze"

TABELAS = [
    "Clientes",
    "Agencias",
    "Contas",
    "Cartoes",
    "Tipos_Transacao",
    "Transacoes",
    "Emprestimos",
]


def extrair_tabela(conn: sqlite3.Connection, tabela: str, lote_id: str, data_carga: str) -> pd.DataFrame:
    """Le uma tabela inteira do OLTP e adiciona colunas de auditoria."""
    df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)

    # Colunas de auditoria: de onde veio e quando entrou na Bronze.
    # Isso e o que permite, mais tarde, rastrear qualquer linha ate sua origem.
    df["arquivo_origem"] = f"{DB_PATH}::{tabela}"
    df["lote_id"] = lote_id
    df["data_carga"] = data_carga

    return df


def salvar_bronze(df: pd.DataFrame, tabela: str) -> None:
    """Salva em CSV e Parquet (Parquet é o formato preferido em produção:
    mais compacto e guarda o tipo de cada coluna)."""
    os.makedirs(BRONZE_DIR, exist_ok=True)

    caminho_csv = os.path.join(BRONZE_DIR, f"{tabela.lower()}_raw.csv")
    caminho_parquet = os.path.join(BRONZE_DIR, f"{tabela.lower()}_raw.parquet")

    df.to_csv(caminho_csv, index=False)
    df.to_parquet(caminho_parquet, index=False)

    print(f"  -> {tabela}: {len(df)} linhas ({caminho_csv} e {caminho_parquet})")


def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"'{DB_PATH}' não encontrado. Rode antes o gerar_dados_fake.py "
            "pra criar o banco OLTP."
        )

    lote_id = str(uuid.uuid4())         
    data_carga = datetime.now().isoformat()

    print(f"Iniciando extração (lote {lote_id})...")
    conn = sqlite3.connect(DB_PATH)

    for tabela in TABELAS:
        df = extrair_tabela(conn, tabela, lote_id, data_carga)
        salvar_bronze(df, tabela)

    conn.close()
    print("\nExtração concluída. Dados disponíveis em ./bronze/")


if __name__ == "__main__":
    main()
