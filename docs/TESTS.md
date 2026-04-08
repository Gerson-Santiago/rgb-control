# Arquitetura de QA Gold Standard (v1.0.22)

Este documento detalha o sistema de blindagem de qualidade implementado no projeto `openrbg`. O objetivo é garantir que o software seja resiliente, livre de vazamentos de memória e protegido contra mudanças que quebrem o comportamento esperado.

## 🛡️ Os 12 Eixos de Defesa

O projeto utiliza uma estratégia de defesa em profundidade, dividida em quatro categorias principais:

### 1. Fidelidade de Ambiente (Realism)
*   **Headless Real (No Mocks)**: Diferente do sistema anterior (baseado em `MagicMock`), o Gold Standard utiliza objetos GObject/Adw reais via `gi.repository`. As janelas e aplicações são instanciadas genuinamente, mas em um ambiente sem display físico (usando flags de isolamento do DBus). Isso captura erros de tipos nativos e sinais disparados na ordem errada.
*   **Isolamento GObject**: A fixture `app_instance` no `conftest.py` garante que cada teste execute em um contexto de aplicação isolado para evitar poluição de barramento.

### 2. Resiliência de Lógica (Property-Based)
*   **Lógica Atômica (`utils.py`)**: A lógica de manipulação de cores foi extraída para um utilitário puro e independente.
*   **Hypothesis Testing**: Implementado em `tests/unit/test_color_logic_hypothesis.py`. Este sistema gera milhares de casos de borda (inputs aleatórios, curtos, maiúsculos/minúsculos, corrompidos) para provar matematicamente que o conversor de cores nunca causará um crash no software.

### 3. Monitoramento de Recursos (Memory & Async)
*   **Stress de Memória (`tracemalloc`)**: O teste `tests/unit/test_memory_efficiency.py` monitora o consumo de RAM em ciclos stressantes de atualização de UI (100+ ciclos), capturando snapshots para detectar vazamentos (leaks).
*   **Async Integrity**: O daemon é validado para garantir que não existam corrotinas órfãs ("never awaited") e que ciclos de scan de barramento sejam limpos.

### 4. Sincronização e Porta de Qualidade (Contract & Gate)
*   **Contrato Daemon ↔ GUI**: Validado em `tests/integration/test_daemon_gui_contract.py`. Garante que as mudanças de estado no disco (status files) e sinais de sistema (SIGUSR1) sejam corretamente interpretados entre os dois processos independentes.
*   **Coverage Ratchet**: Implementado via `scripts/coverage_ratchet.py`. O sistema "trava" o threshold de cobertura; qualquer novo código que diminua a cobertura global (atualmente 73.19%) bloqueará automaticamente o commit.
*   **Mypy Strict & Pyright**: Todos os arquivos devem passar na checagem estática de tipos rigorosa.

---

## 🚀 Como Rodar os Testes

O gate central de qualidade é o script `run_tests.sh`.

### Pré-requisitos
Certifique-se de ter as ferramentas de QA instaladas:
```bash
pip install pytest-cov pytest-asyncio hypothesis pyfakefs mypy pyright
```

### Execução Completa (Quality Gate)
Para validar o projeto antes de um commit ou release:
```bash
./run_tests.sh
```
Este script executa:
1.  **Linter**: Tipagem estrita com Mypy.
2.  **Pytest**: Execução de toda a suite com cobertura.
3.  **Ratchet**: Verificação de regressão de cobertura.

### Execução Manual
Se desejar rodar apenas um nicho:
```bash
PYTHONPATH=src pytest tests/unit/        # Apenas tests unitários
PYTHONPATH=src pytest tests/gui/         # Apenas testes de interface
PYTHONPATH=src pytest -m integration     # Apenas testes de integração/contrato
```

---

## 📊 Métricas de Referência
(Registradas no commit `93e0b9a`)
- **Cobertura Alvo**: > 70% (Protegida pelo Ratchet em 73.19%).
- **Tipo de Ambiente**: GTK4 / Adw 1.0 funcional.
- **Async Pattern**: Pytest-asyncio (mode=auto).
