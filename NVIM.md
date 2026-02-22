# Nvim help

## Python virtualenv with direnv

- Install direnv    
    - macOS: brew install direnv
    - Arch: sudo pacman -S direnv
- Add to your zshrc
    - eval "$(direnv hook zsh)"
- In each Python project, create .envrc
    - source .venv/bin/activate
- Allow it once per project
    - direnv allow
