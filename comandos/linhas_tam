cd /home/sant/Área\ de\ trabalho/PROJETOS/openrgb
find . -type f \
  ! -path "*/.git/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/builds/*" \
  ! -path "*/.mypy_cache/*" \
  ! -path "*/.pytest_cache/*" \
  ! -name "*.pyc" \
  ! -name "*.deb" \
  ! -name "*.png" \
  ! -name "*.gif" \
  ! -name "*.svg" \
  -exec sh -c 'stat -c "%s" "$1"; wc -l < "$1"; echo "$1"' _ {} \; \
  | paste - - - \
  | awk '{print $1 " bytes - " $2 " linhas - " $3}'