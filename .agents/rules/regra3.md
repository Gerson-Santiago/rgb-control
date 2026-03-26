---
trigger: always_on
---

## 🏁 Automatização e Pipeline (Git/CI)

Para garantir que o histórico do projeto permaneça limpo e funcional:

1. **Uso Obrigatório do Workflow**:
   - Todo commit deve ser precedido pela execução do comando `/pipeline`.
   - O pipeline valida: Tipagem (Pyright) -> Testes (Pytest) -> Versionamento (Git).

2. **Mensagens de Commit**:
   - Seguir o padrão [Conventional Commits](https://www.conventionalcommits.org/).
   - Ex: `feat:`, `fix:`, `refactor:`, `chore:`.

3. **Automação de Push**:
   - O workflow `/pipeline` está configurado para realizar o `git push` automaticamente após o sucesso dos testes.
