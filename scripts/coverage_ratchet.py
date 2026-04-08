#!/usr/bin/env python3
import json
import os
import sys

THRESHOLD_FILE = ".coverage_ratchet_threshold"
COVERAGE_FILE = "coverage.json"

def main():
    if not os.path.exists(COVERAGE_FILE):
        print(f"❌ Falha: Arquivo {COVERAGE_FILE} não encontrado. Execute pytest --cov-report=json.")
        sys.exit(1)

    with open(COVERAGE_FILE, "r") as f:
        data = json.load(f)
    
    current_coverage = data.get("totals", {}).get("percent_covered", 0.0)
    current_coverage = round(current_coverage, 2)

    threshold = 70.0 # Floor Absoluto de Qualidade do Projeto
    if os.path.exists(THRESHOLD_FILE):
        try:
            with open(THRESHOLD_FILE, "r") as f:
                threshold = float(f.read().strip())
        except ValueError:
            pass

    print(f"📊 Coverage Atual: {current_coverage}% (Threshold: {threshold}%)")

    if current_coverage < threshold:
        print(f"❌ REGRESSÃO NO COVERAGE DETECTADA! O limite anterior era {threshold}%.")
        print("Adicione testes paritários aos seus novos branches ou lógicas antes de commitar.")
        sys.exit(1)

    if current_coverage > threshold:
        print(f"🟢 Novo pico de cobertura alcançado! O Ratchet foi atualizado de {threshold}% para {current_coverage}%!")
        with open(THRESHOLD_FILE, "w") as f:
            f.write(f"{current_coverage}\n")
    else:
        print("✅ Cobertura mantida de forma satisfatória.")

if __name__ == "__main__":
    main()
