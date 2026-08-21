"""
Camada Silver: limpeza e padronização. 

Lê os arquivos brutos gerados pela extração (bronze/*_raw.parquet) e aplica
os tratamentos descritos na documentação do projeto:
    - remover linhas duplicadas (pela chave primária de negócio);
    - tratar valores nulos em campos essenciais;
    - padronizar o CPF (somente dígitos);
    - padronizar a data/hora das transações para um único fuso horário
      (America/Sao_Paulo).

"""      
import os
import pandas as pd

BRONZE_DIR = "bronze"
SILVER_DIR = "silver"

def ler_bronze(tabela: str) -> pd.DataFrame:
    caminho = os.path.join(BRONZE_DIR, f"{tabela}_raw.parquet")
    return pd.read_parquet(caminho)

def salvar_silver(df: pd.DataFrame, nome_arquivo: str) -> None:
    os.makedirs(SILVER_DIR, exist_ok=True)
    caminho = os.path.join(SILVER_DIR, f"{nome_arquivo}.parquet")
    df.to_parquet(caminho, index=False)
    print(f" -> {nome_arquivo} salvo com sucesso.")

def main() -> None:
    print("Lendo e limpando dados da camada Bronze...")

    clientes = ler_bronze("clientes").drop_duplicates().dropna(subset=["Cliente_ID"])
    clientes["CPF"] = clientes["CPF"].astype(str).str.replace(r"\D", "", regex=True)

    agencias = ler_bronze("agencias").drop_duplicates()
    
    contas = ler_bronze("contas").drop_duplicates()
    contas["Saldo"] = contas["Saldo"].fillna(0.0)

    cartoes = ler_bronze("cartoes").drop_duplicates()
    tipos_transacao = ler_bronze("tipos_transacao").drop_duplicates()
    
    transacoes = ler_bronze("transacoes").drop_duplicates().dropna(subset=["Valor"])
    emprestimos = ler_bronze("emprestimos").drop_duplicates()

    print("\nSalvando tabelas base na camada Silver...")
    salvar_silver(clientes, "clientes_cleaned")
    salvar_silver(agencias, "agencias_cleaned")
    salvar_silver(contas, "contas_cleaned")
    salvar_silver(cartoes, "cartoes_cleaned")
    salvar_silver(tipos_transacao, "tipos_transacao_cleaned")
    salvar_silver(transacoes, "transacoes_cleaned")
    salvar_silver(emprestimos, "emprestimos_cleaned")

    print("\nMontando tabelas enriquecidas (Joins)...")
    
    cols_auditoria = ["arquivo_origem", "lote_id", "data_carga"]
    clientes_slim = clientes.drop(columns=cols_auditoria, errors="ignore")
    agencias_slim = agencias.drop(columns=cols_auditoria, errors="ignore")
    tipos_slim = tipos_transacao.drop(columns=cols_auditoria, errors="ignore")

    contas_enriquecidas = contas.merge(clientes_slim, on="Cliente_ID", how="left")
    contas_enriquecidas = contas_enriquecidas.merge(agencias_slim, on="Agencia_ID", how="left")
    salvar_silver(contas_enriquecidas, "contas_enriquecidas")

    transacoes_detalhadas = transacoes.merge(tipos_slim, on="Tipo_Transacao_ID", how="left")
    salvar_silver(transacoes_detalhadas, "transacoes_detalhadas")

    print("\nConcluído!")

if __name__ == "__main__":
    main()