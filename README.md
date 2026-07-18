# rgb-control — Controle de LEDs OpenRGB para GNOME 🎨🐧

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Quality Gate](https://img.shields.io/badge/quality--gate-passed-brightgreen)


```bash
sudo apt install --reinstall ./builds/rgb-control_3.0.0-1_all.deb
```

Solução focada (v3.0.0) para controlar a iluminação de gabinetes **ASUS TUF Gaming**
e periféricos no Linux via **OpenRGB**.

---

## ✨ Componentes

| Componente | Responsabilidade |
|---|---|
| **Extensão GNOME Shell** | Menu de acesso rápido no painel superior (Shell 45–48) |
| **`rgb` CLI** | Aplicação de cores via terminal (`rgb azul`, `rgb off`, `rgb FF5500`) |
| **`rgb_config`** | Módulo Python puro — leitura/escrita do `config.json` |
| **`assets/default_config.json`** | SSOT das 8 cores padrão de atalho |

---

## 🖥️ Extensão GNOME Shell

O ícone 💡 no painel superior abre um menu com:
- **8 botões de cor** rápida configuráveis
- **Botão liga/desliga** LEDs (off)
- **Configurar Cores** → abre painel de Preferências nativo do GNOME

### Configurar as cores de atalho

```bash
gnome-extensions prefs rgb-control@sant.github.com
```

Ou clique no ícone de engrenagem ⚙️ dentro do menu da extensão.

---

## 💻 CLI (`rgb`)

```bash
rgb azul          # Aplica azul
rgb vermelho      # Aplica vermelho
rgb FF5500        # Aplica cor hex diretamente
rgb off           # Desliga LEDs
rgb on            # Liga com última cor usada
rgb               # Menu interativo (gum)
rgb --help        # Ajuda completa
```

Cores predefinidas: `branco`, `preto/off`, `vermelho`, `verde`, `azul`,
`amarelo`, `laranja`, `ambar`, `roxo`, `ciano` (e variantes em inglês).

---

## 🚀 Instalação

### Dependências
```bash
sudo apt install openrgb
```

### Instalação via .deb
```bash
sudo apt install ./builds/rgb-control_3.0.0-1_all.deb
```

---

## 🛠️ Desenvolvimento

### Setup
```bash
git clone https://github.com/Gerson-Santiago/rgb-control.git
pip install -e .[dev]
./scripts/setup_dev.sh
```

### Pipeline de Qualidade
```bash
./run_tests.sh
```

Gates: arquivos não rastreados → Pyright → Mypy → CLI bash → Pytest+coverage → Ratchet → Versão

### Build do pacote
```bash
./build_deb.sh
```

---

## 🏗️ Estrutura

```
rgb-control/
├── gnome-extension/          # Extensão GNOME Shell (extension.js + prefs.js)
├── src/rgb_config/           # Módulo Python puro — gerência de config.json
├── packaging/rgb.sh          # Script CLI principal
├── assets/default_config.json # SSOT das cores padrão
└── tests/                   # Suite de testes automatizados
```

---
**Status: ESTÁVEL 🛡️**
