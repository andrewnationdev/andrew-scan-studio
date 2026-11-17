# Andrew ScanStudio — Guia Rápido de Uso
Interface de recorte de documentos e imagens projetada para extrair, alinhar e exportar múltiplas regiões de imagens e arquivos PDF.

## Dependências

```bash
pip install PyQt5 opencv-python PyMuPDF pillow numpy
```

## Uso

```bash
python3 app.py
```

## 1. Abrindo Documentos
* **Abrir Arquivo (`Ctrl + O`):** Carregue imagens (`PNG`, `JPG`, `JPEG`, `BMP`, `TIFF`) ou documentos `PDF` multipáginas pelo menu **Arquivo > Abrir Imagem ou PDF...** ou pelo botão na aba superior.
* **Navegação entre Páginas:** Utilize o seletor de páginas ou os botões `◀` e `▶` na barra superior para alternar entre as páginas de um PDF.

## 2. Navegação e Zoom na Área de Trabalho
* **Zoom:** Gire a **roda do mouse** sobre qualquer ponto da imagem para ampliar ou reduzir mantendo o cursor como referência (ou use `Ctrl +` / `Ctrl -`).
* **Mover a Imagem (Pan):** Clique e segure o **botão direito do mouse** (ou o botão do meio / `Espaço + Clique Esquerdo`) e arraste para navegar pela página sem usar as barras de rolagem.
* **Atalhos de Visualização:**
  * `Ctrl + 0`: Ajusta a página inteira à tela.
  * `Ctrl + 1`: Restaura o zoom para `100%`.

## 3. Ferramentas de Seleção (Barra Lateral Esquerda)
* **Seleção Retangular (`M`):**
  1. Clique e arraste sobre a imagem para criar uma área de recorte.
  2. Clique sobre uma região existente para movê-la.
  3. Arraste os **quadrados brancos** nos cantos para redimensionar ou a **bolinha superior** para rotacionar livremente.
* **Marcar 4 Cantos (`P`):**
  1. Ideal para documentos inclinados ou fotografados em ângulo.
  2. Clique nos **4 vértices** do documento; o sistema calcula automaticamente a largura, altura e o ângulo de alinhamento.
  3. Um **clique rápido com o botão direito** desfaz o último ponto marcado (`Esc` limpa todos os pontos pendentes).

## 4. Edição, Camadas e Renomeação em Lote (Painel Direito)
* **Propriedades:** Ajuste manualmente o nome de saída, ângulo de inclinação (`°`), largura (`L`) e altura (`A`) em pixels da região selecionada.
* **Regiões / Camadas:** Visualize todas as seleções criadas no documento. Clique em um item para selecioná-lo (e ir automaticamente para a página correspondente) ou pressione `Delete` para excluir.
* **Renomear em Lote (`Ctrl + B`):** Clique em **Renomear Lote** para nomear sequencialmente todas as regiões (ex.: `DOC_0001_frente`, `DOC_0002_frente`), escolhendo prefixo, número inicial, quantidade de dígitos, sufixo e escopo (todas as páginas ou página atual).
* **Rotação de Página:** Use os botões `↺` e `↻` na barra lateral ou superior para girar a página atual em `90°` (as regiões marcadas acompanham a rotação).

## 5. Projetos e Exportação
* **Salvar / Carregar Projeto (`Ctrl + S` / `Ctrl + L`):** Salva todas as marcações, nomes e rotações em um arquivo `.json` para retomar o trabalho posteriormente.
* **Exportar Recortes (`Ctrl + E`):** No painel **Exportação**, escolha o formato desejado (`JPG`, `PNG` ou `WEBP`) e clique em **Exportar Todos os Recortes** para salvar todas as regiões já alinhadas na pasta de destino.
