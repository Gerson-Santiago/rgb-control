---
trigger: always_on
---

A comunidade Python adota abordagens arquiteturais flexíveis, focadas na
organização por responsabilidade (componentes), modularidade e, para projetos mais complexos, princípios de Clean Architecture (Arquitetura Limpa). Não existe uma regra única, mas sim um conjunto de práticas recomendadas para manter o código testável, escalável e de fácil manutenção. 
Aqui estão os principais padrões arquiteturais adotados:
1. Estrutura Modular e Funcional (Base)
A prática mais comum, especialmente para scripts e aplicações de pequeno/médio porte, é separar o código fonte (src) da documentação, testes e configurações. 

    src/ layout: Pasta principal contendo o código-fonte.
    tests/: Pasta separada para testes automatizados.
    requirements.txt / pyproject.toml: Gestão de dependências. 

2. Clean Architecture (Arquitetura Limpa)
Muito utilizada em grandes aplicações (com Django ou Flask) para garantir que a lógica de negócio seja independente de frameworks e bancos de dados. Ela organiza o projeto em camadas: 

    Entidades: Regras de negócio de alto nível.
    Casos de Uso: Lógica específica da aplicação.
    Interfaces/Adapters: Converte dados entre casos de uso e agentes externos (DB, Web).
    Frameworks & Drivers: Banco de dados, frameworks web (ex: Django, Flask).