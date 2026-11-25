# Diagrama de pressões junto ao perfil do muro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar o segundo perfil de resultados e as pressões laterais num único quadro sem cobrir o muro ou as camadas.

**Architecture:** Estender `_montar_esquema_referencia` com uma opção para criar um painel de pressão à direita. O painel terá eixo horizontal próprio em kPa e compartilhará o eixo de cotas do perfil. O croqui do topo usa a opção desligada.

**Tech Stack:** Python, Streamlit e Plotly já usados em `pages/01_Muro_de_Arrimo.py`; nenhuma dependência nova.

**Spec:** `docs/superpowers/specs/2026-11-25-diagrama-pressao-no-perfil-muro-design.md`

## Global Constraints

- Alterar somente o segundo desenho de resultados; manter o croqui compacto do topo.
- Reservar domínio próprio para as pressões e não desenhá-las sobre as camadas.
- Alinhar a vertical do painel com a cota do perfil e usar escala horizontal em kPa.
- Manter as quatro séries atuais: solo, sobrecarga, água e total.
- Não alterar cálculos, CAD, relatório, controles ou dependências.

## Review Focus

- **Aterro inclinado (β > 0):** o painel continua alinhado à cota H do muro mesmo com a superfície inclinada.
- **Várias camadas:** as mudanças de pressão nas interfaces permanecem visíveis sem passar sobre os rótulos.
- **N.A. dentro de uma camada:** a curva da água e as parcelas totais mantêm os saltos e níveis calculados.
- **Sem N.A.:** a série de água permanece nula e não distorce a escala.
- **Pressão total nula:** o painel mostra uma indicação legível em vez de escala inválida ou erro.

---

### Task 1: Compor o perfil e as pressões na mesma figura

**Files:**
- Modify: `pages/01_Muro_de_Arrimo.py`

**Interfaces:**
- Consumes: `_montar_esquema_referencia(resultado_muro, entradas_muro, camadas_solo)` e `resultado_muro["diagramas_pressao"]`, já usados na página.
- Produces: `_montar_esquema_referencia(..., incluir_diagrama_pressao: bool = False) -> go.Figure`; quando ativado, cria `xaxis2` para as pressões e mantém o eixo vertical de cotas do perfil.

- [x] **Step 1: Add the optional pressure panel**

  Add the optional boolean parameter to `_montar_esquema_referencia`. When true, reserve separate Plotly x-axis domains for profile and pressure, plot the four existing pressure series against `cota = H - profundidade`, show a compact legend/hover labels, and use a safe `[0, 1]` fallback plus a note when the maximum total pressure is zero. Leave the current single-panel layout unchanged when false.

- [x] **Step 2: Use the composite only in the results drawing**

  Call `_montar_esquema_referencia(..., incluir_diagrama_pressao=True)` from `_mostrar_graficos`. Remove the standalone pressure plot so the same four series are not repeated below. Keep the top croqui call using the default false value.

- [ ] **Step 3: Compile and inspect the rendered layout**

  Run `python -m py_compile pages/01_Muro_de_Arrimo.py`. Open the retaining-wall page with the planilha example, then inspect the second drawing for shared cota alignment, a distinct kPa scale, legible layer callouts, and no overlap. Also inspect a multi-layer profile with inclined β and one with N.A. inside a layer; confirm the top croqui remains unchanged.

  **Execution note:** Python compilation and `git diff --check` passed. The local visual render could not start because the system Python lacks Plotly and the offline `uv` cache is inaccessible; the code change itself does not add dependencies. This visual check remains pending.

- [ ] **Step 4: Commit and publish the scoped change**

  Stage only the muro page and the approved design/plan documents; leave unrelated working-tree changes untouched. Commit and push to `main`, as previously authorized.
