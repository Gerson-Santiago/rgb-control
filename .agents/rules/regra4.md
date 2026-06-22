---
trigger: always_on
---

## 🏷️ Versionamento e Empacotamento Debian (OpenRGB)

Para garantir integridade nas instalações e atualizações do sistema Debian/Ubuntu, seguimos regras rígidas de versionamento semântico e empacotamento.

### 1. O Formato de Pacote `X.Y.Z-R_ARCH.deb`
Cada compilação gera um arquivo com a nomenclatura `rgb-control_X.Y.Z-R_ARCH.deb`, onde:
*   **`X.Y.Z` (Versão Semântica)**: A versão da aplicação definida no `pyproject.toml` (Major.Minor.Patch). Deve ser incrementada a cada nova funcionalidade, correção ou refatoração.
*   **`R` (Revisão Debian)**: O número de revisão do empacotamento (ex: `1`). Deve ser incrementado se apenas arquivos de controle do Debian (como `build_deb.sh`, `postinst`, `postrm` ou arquivos de serviço systemd) forem alterados, sem mudança no código-fonte Python.
*   **`ARCH` (Arquitetura)**: Definido como `all`, pois a aplicação é escrita em Python puro (independente de arquitetura física de processador).

### 2. Sincronização Obrigatória de Versão
Sempre que a versão for incrementada no `pyproject.toml` (fonte única de verdade), ela deve ser atualizada de forma correspondente nos seguintes locais:
1.  **`pyproject.toml`**: campo `version = "X.Y.Z"`.
2.  **`src/rgb_control/main.py`**: flag de CLI `--version` imprimindo `RGB Control vX.Y.Z`.
3.  **`rgb.sh`**: CLI wrapper imprimindo `RGB Controller vX.Y.Z`.
4.  **`README.md`**: badges e links das instruções de instalação apontando para a nova build.
5.  **`docs/stack.md`**: cabeçalho do documento `(vX.Y.Z)`.
6.  **`docs/TESTS.md`**: cabeçalho do documento `(vX.Y.Z)`.
7.  **`comandos/atualizar.sh`**: comando de reinstalação com o novo nome de pacote deb.

### 3. Trava de Segurança no Pipeline
*   O script `run_tests.sh` executa automaticamente a auditoria de versão via `python3 scripts/docs_sync_check.py`.
*   Qualquer descompasso ou esquecimento causará a falha do pipeline local de qualidade, impedindo que o script `build_deb.sh` gere o pacote obsoleto ou inconsistente.

### 4. Script de Automação de Versão (Recomendado para Agentes)
Para evitar erros manuais de sincronização ao alterar a versão:
*   **Ação**: Execute o script de automação passando a nova versão como parâmetro.
*   **Comando**: `python3 scripts/bump_version.py X.Y.Z` (onde `X.Y.Z` é a nova versão pretendida).
*   **Comportamento**: O script atualiza todos os 7 locais identificados acima e roda a auditoria `docs_sync_check.py` automaticamente para garantir a conformidade dos documentos.

