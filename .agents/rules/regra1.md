---
trigger: always_on
---

## 🏗️ Clean Architecture (Padrão OpenRGB)

A arquitetura do projeto deve seguir rigorosamente a separação em camadas para garantir independência de hardware e testabilidade:

1. **Domain (`src/rgb_daemon/domain.py`)**: 
   - Contém entidades puras e regras de negócio estáveis.
   - **Proibido**: Imports de `evdev`, `subprocess` ou qualquer dependência externa.

2. **Application (`src/rgb_daemon/application.py`)**: 
   - Define os Casos de Uso (ex: `ToggleMode`, `NextColor`).
   - Orquestra Dominio e Interfaces.
   - **Injeção de Dependências**: Deve receber interfaces (Abstract Base Classes) em vez de classes concretas.

3. **Infrastructure (`src/rgb_daemon/infrastructure.py`)**: 
   - Implementa os Adaptadores (Adapters) para o SO e Hardware.
   - Ex: `NotifyOSD`, `ShellColorApplicator`, `EvdevHardware`.

4. **Composition Root (`src/rgb_daemon/main.py`)**: 
   - Onde todas as peças são montadas.