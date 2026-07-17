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
RBG="$SCRIPT_DIR/packaging/rgb.sh"

echo "🧪 Running integration tests for rgb.sh CLI wrapper..."

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

# Test version flag
output=$(bash "$RBG" "-v" 2>&1)
if [[ "$output" != *"RGB Controller v"* ]]; then
    echo "❌ Fail: Expected version output for '-v', got '$output'"
    exit 1
fi
output=$(bash "$RBG" "--version" 2>&1)
if [[ "$output" != *"RGB Controller v"* ]]; then
    echo "❌ Fail: Expected version output for '--version', got '$output'"
    exit 1
fi
echo "✅ Passed: Version flags"

# Test help flag
output=$(bash "$RBG" "-h" 2>&1)
if [[ "$output" != *"Uso: rgb"* || "$output" != *"Cores predefinidas"* ]]; then
    echo "❌ Fail: Expected help menu for '-h', got '$output'"
    exit 1
fi
output=$(bash "$RBG" "--help" 2>&1)
if [[ "$output" != *"Uso: rgb"* || "$output" != *"Cores predefinidas"* ]]; then
    echo "❌ Fail: Expected help menu for '--help', got '$output'"
    exit 1
fi
echo "✅ Passed: Help flags"

# Test "on" command
rm -f /tmp/.controle_led.color
output=$(bash "$RBG" "on" 2>&1)
if [[ "$output" != *"✅ on"* ]]; then
    echo "❌ Fail: Expected success for 'on' without history, got '$output'"
    exit 1
fi

echo "#00FF00" > /tmp/.controle_led.color
output=$(bash "$RBG" "on" 2>&1)
if [[ "$output" != *"✅ on"* ]]; then
    echo "❌ Fail: Expected success for 'on' with green history, got '$output'"
    exit 1
fi
val=$(cat /tmp/.controle_led.color)
if [[ "$val" != "#00FF00" ]]; then
    echo "❌ Fail: Expected color to remain green, got '$val'"
    exit 1
fi
echo "✅ Passed: 'on' command with and without history"

echo "🎯 All bash CLI tests passed."
