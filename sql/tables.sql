-- DDL do banco transacional (OLTP) do Pipeline de Transações Bancárias
-- Chaves primárias garantem unicidade; chaves estrangeiras implementam o DER.

CREATE TABLE Clientes (
    Cliente_ID INT PRIMARY KEY,
    Nome VARCHAR(100),
    CPF VARCHAR(11) UNIQUE,
    Data_Nascimento DATE
);

CREATE TABLE Agencias (
    Agencia_ID INT PRIMARY KEY,
    Nome_Agencia VARCHAR(50),
    Cidade VARCHAR(50)
);

CREATE TABLE Contas (
    Conta_ID INT PRIMARY KEY,
    Cliente_ID INT,
    Agencia_ID INT,
    Saldo DECIMAL(15, 2),
    FOREIGN KEY (Cliente_ID) REFERENCES Clientes(Cliente_ID),
    FOREIGN KEY (Agencia_ID) REFERENCES Agencias(Agencia_ID)
);

-- Nunca armazenamos o número completo do cartão (boa prática de segurança / PCI-DSS).
CREATE TABLE Cartoes (
    Cartao_ID INT PRIMARY KEY,
    Conta_ID INT,
    Numero_Cartao_Mascarado VARCHAR(20),
    Tipo_Cartao VARCHAR(20),
    FOREIGN KEY (Conta_ID) REFERENCES Contas(Conta_ID)
);

CREATE TABLE Tipos_Transacao (
    Tipo_Transacao_ID INT PRIMARY KEY,
    Descricao VARCHAR(50)
);

CREATE TABLE Transacoes (
    Transacao_ID INT PRIMARY KEY,
    Conta_Origem_ID INT,
    Conta_Destino_ID INT,
    Tipo_Transacao_ID INT,
    Valor DECIMAL(15, 2),
    Data_Hora TIMESTAMP,
    FOREIGN KEY (Conta_Origem_ID) REFERENCES Contas(Conta_ID),
    FOREIGN KEY (Conta_Destino_ID) REFERENCES Contas(Conta_ID),
    FOREIGN KEY (Tipo_Transacao_ID) REFERENCES Tipos_Transacao(Tipo_Transacao_ID)
);

CREATE TABLE Emprestimos (
    Emprestimo_ID INT PRIMARY KEY,
    Cliente_ID INT,
    Valor_Contratado DECIMAL(15, 2),
    Parcelas INT,
    Data_Contrato DATE,
    FOREIGN KEY (Cliente_ID) REFERENCES Clientes(Cliente_ID)
);

-- Índices nas FKs: aceleram os JOINs/GROUP BY usados nas análises (seção 6 do projeto)
CREATE INDEX idx_contas_cliente ON Contas(Cliente_ID);
CREATE INDEX idx_contas_agencia ON Contas(Agencia_ID);
CREATE INDEX idx_transacoes_origem ON Transacoes(Conta_Origem_ID);
CREATE INDEX idx_transacoes_destino ON Transacoes(Conta_Destino_ID);
CREATE INDEX idx_emprestimos_cliente ON Emprestimos(Cliente_ID);
