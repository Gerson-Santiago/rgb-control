---
trigger: always_on
---

## 🧪 Test-Driven Development & Qualidade (OpenRGB)

O projeto exige alta confiabilidade devido à interação direta com hardware.

1. **Test-First (TDD)**:
   - Escrever testes unitários ANTES da implementação da lógica no `Application` ou `Domain`.
   - Garantir que o teste falhe apropriadamente antes de fazer passar.

2. **Metas de Cobertura**:
   - **Mínimo Absoluto**: 80% de cobertura geral.
   - **Alvo Ideal**: 90%+ para as camadas de `Domain` e `Application`.

3. **Ferramental**:
   - Usar `pytest` com `pytest-cov`.
   - Mockar rigorosamente toda a infraestrutura (`Infrastructure`) para evitar efeitos colaterais no hardware durante os testes.

4. **Pipeline de Qualidade**:
   - Nenhum commit deve ser feito sem passar pelo workflow `/pipeline`.