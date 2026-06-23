---
trigger: always_on
---

## 🏁 Automatização e Pipeline (Git/CI)

Para garantir que o histórico do projeto permaneça limpo e funcional:

1. **Uso Obrigatório do Workflow**:
   - Toda entrega segue a árvore de decisões descrita em [.agents/workflows/pipeline.md](file:///home/sant/Área de trabalho/PROJETOS/openrgb/.agents/workflows/pipeline.md), validando tipos, testes, integridade de documentação e build local.

2. **Mensagens de Commit**:
   - Seguir o padrão [Conventional Commits](https://www.conventionalcommits.org/).
   - Ex: `feat:`, `fix:`, `refactor:`, `chore:`.

3. **Automação de Push**:
   - O push deve ser executado pelo desenvolvedor após a validação manual do build do pacote Debian, conforme a árvore de decisões.
