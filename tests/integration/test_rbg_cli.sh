#!/bin/bash
set -e

# Mock openrgb and sudo
mkdir -p /tmp/mock_bin
echo '#!/bin/bash' > /tmp/mock_bin/openrgb
echo 'exit 0' >> /tmp/mock_bin/openrgb
chmod +x /tmp/mock_bin/openrgb

echo '#!/bin/bash' > /tmp/mock_bin/sudo
echo '"$@"' >> /tmp/mock_bin/sudo
chmod +x /tmp/mock_bin/sudo

export PATH="/tmp/mock_bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && cd ../.. && pwd)"
RBG="$SCRIPT_DIR/rbg.sh"

echo "🧪 Running integration tests for rbg.sh CLI wrapper..."

# Test valid targets
for col in "Branca" "Desligar" "Desligado" "Branco" "off"; do
    output=$(bash "$RBG" "$col" 2>&1)
    if [[ "$output" != *"✅"* ]]; then
        echo "❌ Fail: Expected success for '$col', got '$output'"
        exit 1
    fi
done
echo "✅ Passed: Valid keywords"

# Test invalid target
output=$(bash "$RBG" "Invalido" 2>&1 || true)
if [[ "$output" != *"❌ Erro"* ]]; then
    echo "❌ Fail: Expected error for 'Invalido', got '$output'"
    exit 1
fi
echo "✅ Passed: Invalid keywords error"

echo "🎯 All bash CLI tests passed."
