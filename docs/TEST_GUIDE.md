# 🧪 Guia de Testes Premium: openrgb (v1.0.23)

Este documento define a arquitetura de testes e as políticas de qualidade para manter a estabilidade do sistema.

## 🏗️ Estrutura de Testes
O projeto segue uma estrutura em camadas para garantir isolamento e velocidade:

- `tests/unit/`: Testes de funções puras e lógica de domínio (Ex: conversão de cores, cálculos de estado). **Rápidos e sem efeitos colaterais.**
- `tests/gui/`: Testes de interface Libadwaita. Verificam se os widgets estão instanciados e se os sinais (callbacks) estão conectados. **Mockam o Backend.**
- `tests/integration/`: Testes de contrato entre componentes. Verificam se a GUI e o Daemon se comunicam corretamente via arquivos de status e sinais de processo. **Mockam o Subprocesso (Popen/Run) para evitar prompts de sistema.**

---

## 🥇 Políticas de Qualidade "Test First" (TDD)

1.  **Isolamento Total**: Nenhum teste unitário ou de integração deve acessar o hardware real ou exigir privilégios de root (`sudo`/`pkexec`). Use os patches do `unittest.mock`.
    ```python
    with patch('rgb_control.backend.subprocess.run'): # Blindagem total
        backend.apply_color("#00FF00", "Verde")
    ```
2.  **Cobertura Incremental (Ratchet)**: Cada nova funcionalidade deve vir acompanhada de testes que mantenham a cobertura acima do threshold atual (v1.0.23: **82%**).
3.  **Nomes Descritivos**: Use o padrão `test_<funcionalidade>_<comportamento_esperado>`.
4.  **Cenários de Borda**: Sempre inclua testes para inputs `None`, vazios ou malformados na camada de `utils`.

---

## 🚀 Como Executar os Testes
Use o pipeline automatizado que já configura o `PYTHONPATH` e valida o `Mypy` e `Pyright`:
```bash
./run_tests.sh
```

## 🛠️ Frameworks Utilizados
- **Pytest**: Executor de testes e fixtures.
- **Unittest Mock**: Isolamento de sistema.
- **Pyfakefs**: Simulação de sistema de arquivos (Status/PID files).
- **Coverage**: Garantia de visibilidade de execução.
