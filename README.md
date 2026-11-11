# Previsão e estoque perecível do café

Estudo independente com dados sintéticos e assistência de IA. Liga previsão de duas bebidas a consumo de leite e reposição perecível. Não é um café real, uma ordem de compra ou uma reprodução literal do projeto de referência.

**Estado:** implementado e executado localmente, em revisão privada. Nenhum repositório foi criado/publicado. Audiência pública escolhida; nome e conteúdo aguardam revisão. Sem licença de reutilização adicionada ao código próprio. Inter tem sua própria SIL OFL em `assets/`.

## O que foi implementado

- 600 dias,2 bebidas,1.200 linhas dia/item e ficha de leite em ml.
- Contrato diário que rejeita lacunas, duplicatas, falta de coleta e quantidades inválidas. Domingo fechado é zero conhecido, não imputação de registro ausente.
- Sazonal semanal, média móvel 7 e suavização exponencial alfa 0,25.
- Seleção em84 dias de validação após460 dias iniciais;56 dias finais separados. Previsões emitidas em blocos semanais, sem revelar o futuro dentro da semana.
- Reposição por ponto/alvo versus compra fixa; trânsito, FEFO, validade, falta perdida e conservação de massa.
- 200 trajetórias de90 dias por cenário,8 cenários pareados, seed 20261119. Bootstrap de erros semanais da validação sobre a previsão seguinte.
- Notebook executado, relatório offline, CSVs auditáveis e app Streamlit PT/EN com controles e50 trajetórias por exploração.

## Resultado de referência

O sazonal semanal venceu na validação para os dois itens. No teste: café com leite MAE**5,18 unidades**, WAPE**8,05%**; cappuccino MAE**4,43 unidades**, WAPE**11,41%**.

Prazo 2 dias/serviço nominal 97,5%: reposição atende 98,05% com estoque médio 13,26 L; compra fixa atende 99,64% com 18,92 L. Há troca entre estoque e atendimento, não vitória em tudo. Esses resultados são sintéticos; não demonstram redução real de desperdício ou lucro. Serviço nominal não é garantia de fill rate.

38 testes passam em Python 3.10.12 e 3.12.15, incluindo caso manual, fronteira temporal, saldo, trânsito, validade e balanço. Interface exercitada em PT/EN, prazo 5/validade 3 e troca de método; layout inspecionado em 320/390/1280 px. Não instalado/testado no Dell, em Windows nativo ou com dados reais. GitHub Actions ainda não executado.

## Rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.pipeline
# Interface opcional
python -m pip install -r requirements-app.txt
python -m streamlit run app.py
# Teste de interface
python -m unittest discover -s tests_ui -v
# Notebook opcional
python -m pip install -r requirements-notebook.txt
python scripts/execute_notebook.py
```

No PowerShell, use `.venv\Scripts\python.exe` se não ativar o ambiente; não altere política global do Windows. Windows nativo não foi testado. O app usa localhost e estatísticas de uso desativadas. Não exponha sua porta publicamente sem revisão.

## Entender e alterar

- [Explicação aprofundada](docs/EXPLICACAO_COMPLETA.md): decisões, fórmulas, código, resultados, testes e mudanças.
- [Estado verificado](docs/STATUS.md)
- [Notebook executado](notebooks/01_implementacao_explicada.ipynb)
- [Créditos](THIRD_PARTY_NOTICES.md)
- `src/pipeline.py`: gerador, contrato, previsões, avaliação, política e simulação.
- `reports/`: dados gerados, validação/teste, próximos 7 dias, cenários, rastros, métricas, figuras e HTML.

A data da previsão seguinte é 23 a 29/08/2025, depois do histórico fictício, não a semana atual. A simulação repete o perfil de uma semana por 90 dias. Só leite, prazo/validade fixos, sem capacidade de geladeira, custo de pedido ou validade pós-abertura. Compra ilustrativa de R$ 10/L e margem perdida fictícia de R$ 20/L não significam ótimo financeiro. Demanda histórica igual à venda é uma hipótese que pode falhar em ruptura real.

## Referência

https://github.com/AmirhosseinHonardoust/Cafe-Demand-Forecasting-Reorder-Simulator . Nenhum código, base ou resultado do autor foi copiado. Os dados são próprios e sintéticos. Licenças de dependências são separadas; o manual privado não integra o pacote.

---

# Café forecasting and perishable stock

Independent study with synthetic data and AI assistance. It connects forecasts for two drinks to milk consumption and perishable replenishment. It is not a real café, a purchase instruction or a literal reproduction of the reference project.

**Status:** implemented and executed locally, under private review. No repository has been created or published. Public audience selected; name and content await review. No original-code reuse license has been added. Inter retains its separate SIL OFL in `assets/`.

## Implementation

- 600 days,2 drinks,1,200 day/item rows and a milk recipe in ml.
- Daily contract rejects gaps, duplicates, missing collection and invalid quantities. Closed Sundays are known zeros, not imputed missing records.
- Weekly seasonal naive,7-day moving mean and exponential smoothing with alpha 0.25.
- Selection on84 validation days after460 initial days;56 separate final test days. Forecasts are issued in weekly blocks without future observations inside a block.
- Reorder-point/order-up-to versus fixed purchases; in-transit stock, FEFO, expiry, lost sales and mass balance.
- 200 paired 90-day paths per scenario,8 scenarios, seed 20261119. Validation weekly errors are bootstrapped over the next forecast.
- Executed notebook, offline report, auditable CSVs and PT/EN Streamlit app with controls and50 paths per interactive scenario.

## Reference result

Weekly seasonal naive won validation for both drinks. Final test: café com leite MAE**5.18 units**, WAPE**8.05%**; cappuccino MAE**4.43 units**, WAPE**11.41%**.

At 2-day lead time and 97.5% nominal service, replenishment serves 98.05% with 13.26 L average stock; fixed purchasing serves 99.64% with 18.92 L. There is a stock/service trade-off, not a universal winner. Figures are synthetic and do not demonstrate real waste reduction or profit. Nominal service does not guarantee fill rate.

38 tests pass on Python 3.10.12 and 3.12.15, including manual cases, temporal boundaries, balances, transit, expiry and conservation. UI exercised in PT/EN, lead 5/shelf 3 and different methods; layout inspected at 320/390/1280 px. Not installed or tested on the owner's Dell, native Windows or real data. GitHub Actions has not run.

## Run and read

Use the commands above from the project root: minimal dependencies and tests first, then optional app/UI tests or notebook requirements. On PowerShell, use `.venv\Scripts\python.exe` if activation is unavailable; do not change global execution policy. Native Windows is untested. The app binds to localhost and disables usage statistics; do not expose the port without review.

The full explanation is `docs/EXPLICACAO_COMPLETA.md` and its English counterpart `docs/EXPLANATION.md`. Verified status is in `docs/STATUS.md`, executed notebook in `notebooks/`, credits in `THIRD_PARTY_NOTICES.md`. `src/pipeline.py` contains the generator, contract, forecasts, evaluation, policy and simulation. `reports/` contains generated data, validation/test forecasts, next 7 days, scenarios, traces, metrics, figures and HTML.

The next forecast is 23 to 29 August 2025, after the fictional history, not the current week. Simulation repeats one week's profile for 90 days. Only milk, fixed lead/shelf life, no fridge capacity, order cost or post-opening shelf life. Illustrative BRL 10/L purchasing and BRL 20/L lost margin do not establish a financial optimum. Historical sales equaling demand is an assumption that can fail during real stockouts.

## Reference

https://github.com/AmirhosseinHonardoust/Cafe-Demand-Forecasting-Reorder-Simulator . No reference code, dataset or results were copied. Data are original and synthetic. Dependency licenses remain separate; the private brand manual is not bundled.
