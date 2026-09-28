# 🎣 Slayer2 Fish — AutoFish Macro

Macro de pesca automática para Windows, feita em Python. Ela detecta o minijogo de pesca na tela (via visão computacional com OpenCV) e controla o mouse automaticamente para manter a barra no lugar certo. Vem com uma interface gráfica (CustomTkinter) para configurar tudo sem mexer no código.

> ⚠️ **Aviso:** automatizar ações em jogos online pode violar os Termos de Serviço do jogo e resultar em punições. Use por sua conta e risco.

## ✨ Funcionalidades

- Ciclo automático: arremessar → acompanhar o minijogo → coletar → repetir
- Detecção da barra do minijogo por cor (HSV) com predição de inércia
- Interface gráfica com abas **Principal** e **Avançado**
- Área de leitura do minijogo ajustável na tela (caixa arrastável e redimensionável)
- Todos os tempos e parâmetros editáveis e salvos em `config.json`
- Atalhos globais e botão de emergência

## ⌨️ Atalhos

| Tecla | Ação                                              |
| ----- | ------------------------------------------------- |
| `F1`  | Liga / pausa a macro                              |
| `F2`  | Ajusta a área de leitura do minijogo              |
| `ESC` | Encerramento de emergência (solta mouse e teclas) |

Os atalhos `F1` e `F2` podem ser trocados na aba **Avançado**.

## 📁 Estrutura do projeto

```
fish_teste/
├── gui.py            # Interface gráfica (ponto de entrada)
├── Slayer2_Fish.py   # Lógica da macro e seletor de área
├── gui.spec          # Configuração do PyInstaller
├── config.json       # Configurações salvas
├── requirements.txt  # Dependências Python
└── README.md
```

## 🚀 Como usar

### Opção 1 — Executável pronto (sem instalar Python)

1. Baixe o `Slayer2Fish.exe` na aba **Releases** deste repositório.
2. Coloque o `.exe` em uma pasta e execute (o `config.json` será criado ao lado dele).

### Opção 2 — Rodando pelo código-fonte

Requisitos: **Windows** e **Python 3.10+**.

```bash
# 1. Clone o repositório
git clone https://github.com/RicardoViniciusMachadoMartins/Slayer2Fish.git
cd Slayer2Fish

# 2. (Opcional) Crie um ambiente virtual
python -m venv venv
venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a interface
python gui.py
```

> Execute como **Administrador** se o jogo não estiver reagindo aos cliques e teclas simulados.

## 🎮 Passo a passo

1. Abra o jogo e deixe-o na tela principal (modo janela sem bordas costuma funcionar melhor).
2. Abra o AutoFish e clique em **DEFINIR ÁREA DO MINIJOGO (F2)**.
3. Posicione e redimensione a caixa verde sobre a barra do minijogo e clique em **[ SAVE ]**.
4. Pressione **F1** para iniciar. Pressione **F1** de novo para pausar.
5. Em caso de problema, aperte **ESC**.

## ⚙️ Configurações (`config.json`)

| Chave                                | Descrição                                                            |
| ------------------------------------ | -------------------------------------------------------------------- |
| `hotkeys.hotkey_1` / `hotkey_2`      | Teclas de iniciar/pausar e de selecionar área                        |
| `scan_area`                          | Posição e tamanho da área lida (proporção da tela, de 0 a 1)         |
| `task_fps`                           | Quantas leituras por segundo                                         |
| `timings.cast_settle_sec`            | Tempo segurando o clique ao arremessar                               |
| `timings.cast_after_sec`             | Pausa após o arremesso                                               |
| `timings.wait_minigame_start_sec`    | Tempo máximo esperando o minijogo aparecer                           |
| `timings.after_collect_sec`          | Pausa após coletar                                                   |
| `advanced.inertia_prediction_factor` | Força da predição de movimento da barra                              |
| `advanced.white_gone_frames`         | Quadros sem detectar o marcador para considerar o minijogo encerrado |
| `advanced.wait_before_t_sec`         | Espera antes de segurar `T` para coletar                             |

## 🛠️ Gerando o executável

```bash
pip install pyinstaller
pyinstaller gui.spec
```

O `.exe` será gerado na pasta `dist/`.

## 🧰 Tecnologias

Python · OpenCV · NumPy · mss · pydirectinput · keyboard · CustomTkinter
