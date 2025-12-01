#!/bin/bash
# Environment setup script for LLM Chat
# Creates an isolated Python 3.11 environment with CUDA support

set -e

# Configuration
ENV_NAME="${ENV_NAME:-llm-chat-env}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
CUDA_VERSION="${CUDA_VERSION:-12.1}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.llm_chat}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LLM Chat Environment Setup ===${NC}"
echo ""

# Check for Python 3.11
check_python() {
    echo -e "${YELLOW}Checking for Python ${PYTHON_VERSION}...${NC}"
    
    if command -v python${PYTHON_VERSION} &> /dev/null; then
        PYTHON_CMD="python${PYTHON_VERSION}"
        echo -e "${GREEN}Found: $(${PYTHON_CMD} --version)${NC}"
    elif command -v python3 &> /dev/null; then
        PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ "$PY_VER" == "$PYTHON_VERSION" ]]; then
            PYTHON_CMD="python3"
            echo -e "${GREEN}Found: $(${PYTHON_CMD} --version)${NC}"
        else
            echo -e "${RED}Python ${PYTHON_VERSION} not found. Found Python ${PY_VER} instead.${NC}"
            echo -e "${YELLOW}Please install Python ${PYTHON_VERSION} or set PYTHON_VERSION environment variable.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Python not found. Please install Python ${PYTHON_VERSION}.${NC}"
        exit 1
    fi
}

# Check for CUDA
check_cuda() {
    echo -e "${YELLOW}Checking for CUDA...${NC}"
    
    if command -v nvidia-smi &> /dev/null; then
        NVIDIA_OUTPUT=$(nvidia-smi --query-gpu=driver_version,cuda_version --format=csv,noheader 2>/dev/null || true)
        if [[ -n "$NVIDIA_OUTPUT" ]]; then
            echo -e "${GREEN}NVIDIA GPU detected: ${NVIDIA_OUTPUT}${NC}"
            CUDA_AVAILABLE=true
        else
            echo -e "${YELLOW}NVIDIA driver found but no GPU detected${NC}"
            CUDA_AVAILABLE=false
        fi
    else
        echo -e "${YELLOW}NVIDIA driver not found. CUDA acceleration will not be available.${NC}"
        CUDA_AVAILABLE=false
    fi
}

# Create virtual environment
create_venv() {
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    
    VENV_PATH="${INSTALL_DIR}/venv"
    
    if [[ -d "$VENV_PATH" ]]; then
        echo -e "${YELLOW}Virtual environment already exists at ${VENV_PATH}${NC}"
        read -p "Do you want to recreate it? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_PATH"
        else
            echo -e "${GREEN}Using existing environment${NC}"
            return
        fi
    fi
    
    mkdir -p "$INSTALL_DIR"
    ${PYTHON_CMD} -m venv "$VENV_PATH"
    
    echo -e "${GREEN}Virtual environment created at ${VENV_PATH}${NC}"
}

# Install dependencies
install_deps() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    VENV_PATH="${INSTALL_DIR}/venv"
    source "${VENV_PATH}/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install base requirements
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "${SCRIPT_DIR}/requirements.txt" ]]; then
        pip install -r "${SCRIPT_DIR}/requirements.txt"
    else
        pip install aiohttp PyQt5
    fi
    
    # Install PyTorch with CUDA support if available
    if [[ "$CUDA_AVAILABLE" == "true" ]]; then
        echo -e "${YELLOW}Installing PyTorch with CUDA ${CUDA_VERSION} support...${NC}"
        
        case "$CUDA_VERSION" in
            "12.1")
                pip install torch --index-url https://download.pytorch.org/whl/cu121
                ;;
            "12.8")
                pip install torch --index-url https://download.pytorch.org/whl/cu128
                ;;
            "11.8")
                pip install torch --index-url https://download.pytorch.org/whl/cu118
                ;;
            *)
                echo -e "${YELLOW}Unknown CUDA version ${CUDA_VERSION}, installing CPU-only PyTorch${NC}"
                pip install torch
                ;;
        esac
    else
        echo -e "${YELLOW}Installing CPU-only PyTorch...${NC}"
        pip install torch --index-url https://download.pytorch.org/whl/cpu
    fi
    
    deactivate
    
    echo -e "${GREEN}Dependencies installed${NC}"
}

# Create launcher script
create_launcher() {
    echo -e "${YELLOW}Creating launcher script...${NC}"
    
    VENV_PATH="${INSTALL_DIR}/venv"
    LAUNCHER_PATH="${INSTALL_DIR}/run.sh"
    
    cat > "$LAUNCHER_PATH" << EOF
#!/bin/bash
# LLM Chat Launcher
source "${VENV_PATH}/bin/activate"
python -m llm_chat "\$@"
EOF
    
    chmod +x "$LAUNCHER_PATH"
    
    echo -e "${GREEN}Launcher created at ${LAUNCHER_PATH}${NC}"
}

# Create desktop entry (Linux)
create_desktop_entry() {
    if [[ "$(uname)" == "Linux" ]]; then
        echo -e "${YELLOW}Creating desktop entry...${NC}"
        
        DESKTOP_FILE="$HOME/.local/share/applications/llm-chat.desktop"
        mkdir -p "$(dirname "$DESKTOP_FILE")"
        
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=LLM Chat
Comment=Local LLM Chat Interface
Exec=${INSTALL_DIR}/run.sh
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;Development;
EOF
        
        echo -e "${GREEN}Desktop entry created${NC}"
    fi
}

# Main setup
main() {
    check_python
    check_cuda
    create_venv
    install_deps
    create_launcher
    create_desktop_entry
    
    echo ""
    echo -e "${GREEN}=== Setup Complete ===${NC}"
    echo ""
    echo "To run LLM Chat:"
    echo "  ${INSTALL_DIR}/run.sh"
    echo ""
    echo "Or activate the virtual environment manually:"
    echo "  source ${INSTALL_DIR}/venv/bin/activate"
    echo "  python -m llm_chat"
    echo ""
    
    if [[ "$CUDA_AVAILABLE" == "true" ]]; then
        echo -e "${GREEN}CUDA support is enabled.${NC}"
    else
        echo -e "${YELLOW}Running in CPU mode.${NC}"
    fi
}

main
