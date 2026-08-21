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


import os
import random
import sqlite3
 
import pandas as pd
 
DB_PATH = os.path.join("data", "oltp.db")
BRONZE_DIR = os.path.join("data", "bronze")
 
TABELAS = [
    "Agencia",
    "Cliente",
    "Contas",
    "Cartao",
    "Emprestimos",
    "Transacao_Tipo",
    "Transacoes",
]
 
NOME_ARQUIVO_BRONZE = {
    "Agencia": "agencias_raw",
    "Cliente": "clientes_raw",
    "Contas": "contas_raw",
    "Cartao": "cartoes_raw",
    "Emprestimos": "emprestimos_raw",
    "Transacao_Tipo": "tipos_transacao_raw",
    "Transacoes": "transacoes_raw",
}
 
 
def extrair_tabela(conn: sqlite3.Connection, tabela: str) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
 
 
def main() -> None:
    os.makedirs(BRONZE_DIR, exist_ok=True)
 
    conn = sqlite3.connect(DB_PATH)
    try:
        for tabela in TABELAS:
            df = extrair_tabela(conn, tabela)
 
            if tabela == "Transacoes":
                random.seed(42)
                n_duplicatas = max(1, int(len(df) * 0.01))
                duplicatas = df.sample(n=n_duplicatas, random_state=42)
                df = pd.concat([df, duplicatas], ignore_index=True)
 
            nome_arquivo = NOME_ARQUIVO_BRONZE[tabela]
            caminho = os.path.join(BRONZE_DIR, f"{nome_arquivo}.parquet")
            df.to_parquet(caminho, index=False, engine="pyarrow")
 
            print(f"[bronze.py] {tabela} -> {caminho} ({len(df)} linhas)")
    finally:
        conn.close()
 
 
if __name__ == "__main__":
    main()
 