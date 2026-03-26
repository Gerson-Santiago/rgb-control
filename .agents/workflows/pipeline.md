---
description: Pipeline completo de Verificação, Teste e Versionamento (CI/CD Local)
---

Este workflow executa a sequência obrigatória de qualidade antes de qualquer entrega.

// turbo-all
1. **Análise Estática (Linter/Tipagem)**
   Executa o Pyright para garantir que não há erros de importação ou tipos.
   ```bash
   python3 -m pyright src/ tests/
   ```

2. **Testes Unitários e de Integração**
   Executa a suíte de testes com o PYTHONPATH configurado.
   ```bash
   export PYTHONPATH=src:$PYTHONPATH; pytest tests/test_daemon_* tests/test_gui_backend_clean.py -v
   ```

3. **Relatório de Cobertura**
   Garante que a cobertura mínima de 80-90% seja mantida.
   ```bash
   export PYTHONPATH=src:$PYTHONPATH; pytest --cov=src/rgb_daemon --cov=src/rgb_control --cov-report=term-missing
   ```

4. **Versionamento Automático (Git)**
   Se os testes passarem, realiza o commit e o push das alterações.
   ```bash
   git add -A
   git commit -m "chore: pipeline pass - auto-commit"
   git push origin $(git branch --show-current)
   ```
