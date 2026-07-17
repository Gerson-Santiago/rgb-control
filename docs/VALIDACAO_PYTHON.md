# Validação de Qualidade e Sintaxe em Python

No desenvolvimento e manutenção do projeto, a validação de sintaxe e qualidade do código Python é executada automaticamente pelo pipeline. No entanto, durante o desenvolvimento diário, várias ferramentas podem ser utilizadas isoladamente pelo desenvolvedor para garantir a conformidade rápida das alterações.

Abaixo está o manual de referência rápida para validação em Python.

---

### 1. Verificar apenas erros de sintaxe (nativo do Python)

Para validar a sintaxe de um arquivo de forma rápida sem executá-lo:

```bash
python3 -m py_compile arquivo.py
```

Se o interpretador não retornar nenhuma saída, significa que o arquivo não possui erros de sintaxe.

---

### 2. Verificar toda uma pasta recursivamente

Para analisar a sintaxe de todos os arquivos de um diretório recursivamente:

```bash
python3 -m compileall .
```

Isso tentará compilar todos os arquivos `.py` no escopo do projeto, acusando falhas se houver problemas de sintaxe em códigos obsoletos ou novos.

---

### 3. Executar o arquivo diretamente

Para validar o fluxo lógico e expor problemas que ocorrem exclusivamente em tempo de execução:

```bash
python3 arquivo.py
```

---

### 4. Verificar problemas de qualidade do código (Linter)

O projeto utiliza e recomenda o **Ruff** para análise estática de qualidade (limpeza de imports não utilizados, formatação, complexidade de código, etc.).

Para instalar localmente:

```bash
pip install ruff
```

Para analisar um arquivo específico:

```bash
ruff check arquivo.py
```

Para validar a pasta inteira do projeto:

```bash
ruff check .
```

---

### 5. Verificar Tipagem Estática (Type Checking)

Como o projeto segue tipagem rigorosa (`mypy --strict`), você pode rodar a verificação de tipos localmente:

Para instalar o MyPy:

```bash
pip install mypy
```

Para validar um arquivo individualmente:

```bash
mypy arquivo.py
```

---

### Equivalência com JavaScript

Se você estiver habituado ao comando do ecossistema Node.js **`node --check arquivo.js`**, a equivalência direta no Python é:

```bash
python3 -m py_compile arquivo.py
```

Ele valida a árvore de sintaxe (AST) do arquivo sem invocar sua execução real.
