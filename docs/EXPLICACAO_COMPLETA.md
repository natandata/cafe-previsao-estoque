# Previsão e estoque perecível do café

Documento de implementação e estudo, versão privada de 11/11/2026. Projeto 8 do guia. Código independente com assistência de IA, dados próprios e sintéticos. Não é uma reprodução dos resultados do autor de referência nem uma implantação num café real. O projeto 10, plataforma de operações, é separado deste pacote.

## 1. O problema que foi implementado

Uma previsão de vendas só vira uma decisão operacional quando é ligada a uma unidade comprável e a uma regra de reposição. O projeto começa com duas bebidas, prevê suas quantidades e as converte em mililitros de leite. Depois compara uma compra fixa com uma política de ponto de reposição, incluindo prazo de chegada, validade, estoque em trânsito e demanda perdida.

A pergunta não é 'qual modelo é mais sofisticado?', mas 'qual método simples prevê melhor e o que acontece quando eu uso essa previsão numa política com hipóteses explícitas?'. Não há rede neural, otimização financeira ou promessa de redução de desperdício. O método sazonal simples vence os outros dois na base construída, e isso é um resultado aceitável, não algo a esconder.

O histórico tem 600 dias de calendário, de 01/01/2024 a 22/08/2025, dois itens e 1.200 registros dia/item. O calendário termina no passado porque é uma simulação histórica, não um retrato do café em novembro de 2026. Os primeiros 460 dias são o histórico inicial, os 84 seguintes servem para comparar métodos e os últimos 56 são o teste final. A execução usa seed 20261111.

## 2. Resultado medido, sem marketing

Na validação, o MAE do café com leite é 5,02 unidades para sazonal semanal, 19,54 para média móvel e 19,16 para suavização. Para cappuccino, é 4,67, 12,72 e 12,59 unidades, respectivamente. O vencedor foi escolhido nessa etapa, separadamente por item, e ficou congelado antes de avaliar o teste.

No teste final, o café com leite tem MAE de 5,18 unidades e WAPE de 8,05%; o cappuccino tem MAE de 4,43 unidades e WAPE de 11,41%. Esses são erros numa demanda fictícia criada com sazonalidade semanal, ruído e tendência leve. Não demonstram desempenho num restaurante real ou superioridade universal do método semanal.

A simulação usa 200 trajetórias por cenário, 90 dias por trajetória, dois prazos (2 e 5 dias), dois serviços nominais (90% e 97,5%) e duas políticas. São oito cenários e 1.600 execuções de estoque. Todos recebem as mesmas trajetórias para que a comparação não confunda política com um sorteio diferente de demanda.

Para prazo de 2 dias e serviço nominal 97,5%, a política de reposição atende em média 98,05% da demanda, com estoque médio de 13,26 litros. A compra fixa atende 99,64%, com 18,92 litros. A política de reposição reduz o estoque médio no exemplo, mas também perde mais demanda. Não é correto dizer que ela dominou a compra fixa em todas as métricas.

Com prazo de 5 dias e serviço 97,5%, a reposição atende 96,55%, abaixo do parâmetro nominal, e mantém cerca de 17,71 litros. Isso mostra por que o parâmetro da fórmula não deve ser vendido como garantia de atendimento. As diferenças entre serviço de ciclo, fill rate, sazonalidade e revisão discreta importam.

## 3. Mapa dos módulos

`src.pipeline.generate()` cria os dados. `validate_daily()` verifica o contrato e recusa lacunas sem evidência. `forecast()` implementa os três métodos. `backtest()` materializa previsões por origem temporal. `Policy` valida parâmetros de estoque, `levels()` calcula níveis e `simulate()` executa uma trajetória. `run()` organiza seleção, teste, previsão seguinte, cenários e artefatos.

`src/common.py` concentra gravação de CSV/JSON, gráficos e HTML. `app.py` oferece exploração local, com idioma, bebida, método, prazo, validade, nível nominal e seed. O notebook reusa as funções do código e expõe as contas. `tests/test_pipeline.py` tem 38 casos automatizados, com exemplos manuais, invariantes e casos extremos.

Esses limites de módulo evitam misturar treinamento, avaliação e apresentação. A política pode ser testada com uma sequência de demanda escrita à mão, sem depender de todo o gerador. Uma previsão pode ser testada com sete números, sem abrir Streamlit. Essa separação reduz o trabalho necessário para localizar um erro.

## 4. O contrato da base

Cada linha contém `date`, `item`, `quantity`, `is_open` e `observed`. A chave é data/item, não só data. `quantity` representa unidades de bebida demandadas e atendidas no histórico sintético. O gerador assume ausência de censura por ruptura: venda observada coincide com demanda. Em dados reais, vendas baixas podem refletir falta de estoque, não demanda baixa; esse problema precisaria de outra modelagem.

`observed=True` informa que a coleta aconteceu. `is_open=False` informa um fechamento conhecido. O café fecha aos domingos na simulação e por isso a quantidade é zero. Um registro ausente não recebe zero automaticamente. A função rejeita uma data/item ausente, um registro não observado, duplicata, item sem ficha técnica, valor negativo, fracionário, infinito ou venda positiva num fechamento.

A validação exige o calendário completo entre a menor e a maior data presentes para os dois itens. Ela não adivinha que todo o primeiro mês deveria existir se ambos os itens foram cortados juntos antes da menor data: esse limite externo precisaria vir de um contrato de extração. Essa distinção evita confundir validação interna com conhecimento de uma fonte que não foi fornecida.

Não há clientes, endereços, entregadores, reviews ou dados de caixa de terceiros. Os nomes dos itens são rótulos da simulação. A base Cafe Sales Dataset e os CSVs do repositório de referência não foram baixados nem redistribuídos. O código e os dados próprios podem ser avaliados sem depender da licença de uma operação alheia.

## 5. Como os dados foram gerados

O gerador usa `numpy.random.default_rng(seed)`. A demanda tem um nível por bebida, um fator semanal, uma tendência pequena, um ciclo suave de 90 dias e ruído normal arredondado. Sexta e sábado têm maior fator; domingo fecha. Quantidades negativas são cortadas em zero. O objetivo é construir um cenário auditável em que os métodos tenham comportamentos diferentes.

Esse desenho favorece explicitamente um baseline semanal. É uma escolha didática, e não evidência de que todos os cafés têm essa forma. Uma avaliação real precisaria de feriados, promoções, mudanças de preço, clima disponível antes da previsão, capacidade e períodos de ruptura. A seed repete os sorteios dentro do ambiente declarado; não transforma as hipóteses em fatos.

O ambiente foi testado em Python 3.10.12 e 3.12.15, com NumPy 2.2.6, pandas 2.3.3 e matplotlib 3.10.9. Fixar versões diminui divergências. Não há requisição de rede quando o pipeline roda; a rede só é necessária para instalar dependências que ainda não estejam disponíveis.

## 6. Três métodos e suas contas

O sazonal semanal, `seasonal7`, repete os últimos sete valores na mesma ordem. Se o histórico termina com `[10, 20, 30, 40, 50, 60, 0]`, a próxima semana prevista é essa mesma sequência. Para dez dias, ele repete os três primeiros valores depois da semana. Isso é recursão sazonal simples, não uso de valores reais futuros.

A média móvel, `moving7`, calcula a média dos últimos sete valores conhecidos e repete essa média em todo o horizonte. Ela suaviza ruído, mas apaga a diferença entre sábado e domingo. Por isso erra bastante neste gerador. Ela não recalcula a média com a venda real de amanhã durante uma previsão emitida hoje.

A suavização exponencial, `ses025`, começa no primeiro valor do histórico e atualiza o nível por `nivel = 0.25 * observado + 0.75 * nivel_anterior`. A previsão é constante em todo o horizonte. O alfa 0,25 foi fixado como parte do experimento, não ajustado no teste final. O método acompanha nível, mas não representa a sazonalidade semanal de forma explícita.

Todos exigem um histórico unidimensional de pelo menos sete valores finitos, não negativos, e horizonte inteiro positivo. A saída é não negativa. Se houver item novo com menos de sete dias, a função falha de forma clara em vez de inventar um histórico; um fallback para item novo seria uma extensão a desenhar com o negócio.

## 7. Avaliação temporal sem vazamento

`backtest(values, start, stop, method, horizon=7)` cria origens não sobrepostas. Em cada origem, passa ao modelo apenas `values[:origin]`. A previsão de sete dias é emitida de uma vez. Só na origem seguinte os sete valores que já se tornaram passado podem entrar no histórico. Cada linha de resultado guarda origem, índice alvo, observado, previsão e método.

Há 12 semanas de validação e 8 semanas de teste. As janelas do teste podem usar observações de semanas anteriores do próprio teste quando elas já estariam disponíveis no tempo operacional. Isso é uma avaliação de atualizações semanais, não uma previsão de 56 dias emitida no primeiro dia do teste. O rótulo do gráfico e o documento mantêm essa distinção.

Um teste altera brutalmente os valores futuros e verifica que as previsões da origem anterior não mudam. Outro confere que o índice alvo nunca fica antes da origem e que nenhum alvo atravessa o fim da janela. Essas verificações são mais úteis contra vazamento do que apenas declarar que o código é 'temporal'.

A validação escolhe o método pelo menor MAE; um desempate usa o nome de forma determinística. O teste final mede apenas o método escolhido. Não é usado para selecionar o vencedor. Depois de concluir a avaliação, o método já escolhido é atualizado com todo o histórico para demonstrar a previsão dos sete dias seguintes. Essa previsão atualizada não é apresentada como um novo teste com resultado conhecido.

## 8. O significado de MAE e WAPE

MAE é a média de `abs(observado - previsto)`. Ele continua na unidade da bebida: MAE 5,18 significa erro absoluto médio de cerca de cinco unidades por dia, não 5,18% e não um limite máximo. Alguns dias podem errar mais e outros menos.

WAPE é `soma(abs(erros)) / soma(abs(observados))`. O projeto não usa MAPE porque existem domingos com quantidade zero. O WAPE divide pelo volume total do período e não explode em cada dia de fechamento. Se todo o período observado for zero, a função retorna ausência de percentual em vez de dividir por zero; o JSON não aceita NaN silencioso.

Essas métricas não incorporam o custo assimétrico de faltar e sobrar leite. Duas previsões com o mesmo MAE podem gerar estoques diferentes se uma erra sempre para baixo em dias de pico. Por isso o projeto não termina na tabela de previsão: ele simula a decisão, mas ainda sob hipóteses simplificadas.

## 9. Da bebida para o ingrediente

A ficha técnica declara 80 ml por café com leite e 180 ml por cappuccino. A demanda prevista de leite de um dia é `80 * cafes + 180 * cappuccinos`. Não foi assumido que uma unidade de bebida é uma unidade de ingrediente comprado. Também não há conversão implícita entre litro e mililitro: o simulador usa ml inteiros e a apresentação divide por 1000 para litros.

Exemplo manual: 10 cafés com leite e 5 cappuccinos consomem 10 × 80 + 5 × 180 = 1700 ml, ou 1,7 L. Se a receita mudar para 100 ml no café, a previsão de unidades da bebida pode continuar igual, mas a compra de leite muda. Por isso a ficha é separada do modelo de demanda.

Só um ingrediente foi modelado. Não há grãos, açúcar, embalagens, múltiplos fornecedores ou capacidade de geladeira. A validade usada é fixa a partir da chegada e não distingue leite fechado de aberto. Essas simplificações precisam aparecer antes que alguém confunda o estudo com um sistema de compras pronto.

## 10. Ponto de reposição e estoque-alvo

A média diária de leite vem da previsão agregada da próxima semana. O desvio padrão vem dos erros agregados da validação, preservando a combinação das bebidas. Com `L` dias de prazo e `z` quantil normal do serviço nominal, o estoque de segurança é `z * desvio * sqrt(L)`. O ponto de reposição é `media * L + seguranca`. Os níveis são arredondados para cima em ml.

O estoque-alvo cobre prazo mais intervalo de revisão: `media * (L + R) + z * desvio * sqrt(L + R)`. A revisão é diária no experimento (`R=1`). Se a posição de estoque for menor ou igual ao ponto de reposição, a compra preenche até esse alvo. A posição inclui estoque em mãos e compras em trânsito. Ignorar o trânsito faria o programa comprar várias vezes a mesma necessidade.

Exemplo sem incerteza: média 100 ml/dia, desvio zero, prazo 2 dias e revisão de 1 dia produzem ponto 200 ml e alvo 300 ml. O teste manual verifica exatamente esses números. Aumentar serviço ou prazo deve elevar a proteção; outros testes verificam essa direção.

A aproximação normal supõe uma forma simples para a incerteza acumulada. Ela não representa perfeitamente fechamento semanal, autocorrelação ou revisão discreta, e serviço de ciclo não é o mesmo que a fração da demanda atendida. O simulador mede o comportamento que resulta da regra em vez de assumir que o percentual solicitado foi alcançado.

## 11. A simulação, na ordem certa

Cada dia segue esta ordem: recebe compras com chegada marcada para aquele dia; expira lotes cujo vencimento chegou; atende demanda consumindo primeiro o que vence antes; calcula posição; decide uma nova compra. A compra feita hoje chega somente após o prazo. Não há recebimento instantâneo nem quantidade negativa de estoque.

Um lote que chega no dia `a` expira no início do dia `a + shelf_days`. Assim, validade de um dia permite uso no dia da chegada e expira no começo do seguinte. Essa convenção é explícita e testada. Trocar a convenção muda o desperdício, especialmente para validade curta.

O consumo usa FEFO: first expired, first out, ou primeiro a vencer, primeiro a sair. Lotes são ordenados por vencimento antes do consumo. Quantidade que falta vira venda perdida e não fica aguardando como backlog. O programa não promete entregar amanhã uma bebida que o cliente deixou de comprar hoje.

O estoque inicial é igual ao alvo, tem validade e entra na quantidade comprada. Ele não é um presente gratuito para favorecer uma política. Ao fim da trajetória, o estoque em mãos e o que ainda está em trânsito também são contados. O invariante é: comprado = consumido + expirado + estoque final + trânsito final. A simulação exige que essa identidade seja exata.

## 12. Como as trajetórias são construídas

Depois da escolha do modelo, os erros de validação das bebidas são multiplicados por suas fichas e somados por índice. Isso preserva a combinação observada de erros entre bebidas. Os 84 erros agregados formam 12 blocos semanais. Cada trajetória sorteia blocos inteiros de erro e os soma à repetição da previsão da próxima semana; valores são arredondados e cortados em zero.

Sorteio de blocos, ou bootstrap em blocos, preserva parte da dependência dentro da semana. Não preserva todos os padrões possíveis entre semanas nem inventa eventos extremos nunca vistos. O horizonte de 90 dias repete a previsão de uma semana; não há tendência futura de 90 dias modelada. Os quantis de resultados refletem essas 200 trajetórias sintéticas, não intervalos de confiança garantidos para um café real.

O gerador de caminhos usa seed 20261119. As trajetórias são criadas uma vez e reaproveitadas para todas as políticas. A comparação pareada diminui ruído de Monte Carlo. Não usa erros do teste final para calibrar incerteza: os resíduos vêm só da validação, enquanto a previsão para implantação pode usar o histórico que já terminou.

## 13. A política fixa e a comparação justa

A política fixa compra a média prevista a cada revisão, sem proteção adicional na quantidade comprada. Para cada cenário, começa com o mesmo estoque-alvo da política de reposição e tem o mesmo prazo, validade e demanda. O estoque inicial muda quando muda o parâmetro de serviço porque o cenário mudou; não compare linhas com serviços diferentes como se apenas a política tivesse mudado.

As métricas incluem fill rate, dias com falta, ml perdidos, descarte, estoque médio ao fim do dia, quantidade comprada, estoque e trânsito finais. Fill rate é `1 - perdido / demandado`. Num caminho sem demanda, o programa retorna 1 por convenção e não divide por zero. Dias com falta contam dias, não pessoas nem bebidas perdidas.

A tabela também mostra percentis 5 e 95 do fill rate entre trajetórias. Esses percentis descrevem a dispersão da simulação. Não são a mesma coisa que serviço nominal nem um intervalo probabilístico validado externamente. Para uma decisão real, seria necessário testar estabilidade com mais sementes, mudanças de distribuição e dados recentes.

O custo ilustrativo é 1 centavo por ml comprado, equivalente a R$ 10,00 por litro, e margem perdida ilustrativa de 2 centavos por ml não atendido. Não há custo de armazenagem, custo fixo de pedido, impostos, valor residual ou perecibilidade pós-abertura. Não somamos desperdício novamente ao custo de compra, pois isso contaria duas vezes o mesmo leite comprado. Não afirmamos lucro ou ótimo econômico.

## 14. O que o painel deixa explorar

O HTML abre offline e mostra os relatórios congelados. A aplicação Streamlit permite escolher bebida e método para ver a semana prevista; depois simula 50 trajetórias com prazo, validade, serviço e seed configuráveis. O cenário interativo é separado da avaliação versionada de 200 trajetórias. Mudar o seletor de modelo não reescreve qual método venceu a validação no relatório.

As unidades aparecem nos rótulos: bebidas em unidades, leite em ml nos rastros e litros nos resumos, prazo e validade em dias. Um resultado de 97,7% na interface padrão com 50 trajetórias não deve ser citado como se fosse o resultado exato da tabela de 200 trajetórias e serviço 97,5%; são cenários diferentes. Reproduza os parâmetros e a seed ao comparar telas.

A aplicação oferece download dos resultados locais e não emite pedido a fornecedor. Não usa contas, não cobra, não publica GitHub nem envia dados a um serviço de previsão. O servidor fica em localhost por padrão, com estatísticas de uso do Streamlit desativadas. Compartilhar a porta na internet exigiria uma revisão de segurança e privacidade que não faz parte desta entrega.

## 15. Os 38 testes como explicação

A primeira família verifica geração repetível e contrato diário: calendário, duplicata, coleta, valor negativo/fracionário, fechamento e ficha ausente. A segunda verifica fórmulas de previsão com números pequenos, histórico insuficiente, método inválido, independência do futuro, origens, janela parcial e limite temporal.

A terceira cobre níveis manuais, crescimento de segurança com serviço/prazo e políticas inválidas. A quarta cobre demanda zero, saldo não negativo, conservação de massa, falta perdida, chegada só após prazo, validade, demanda = consumo + perda, repetição, ml inválido, FEFO, caminho vazio, demanda igual entre políticas, trânsito e custo de compra.

Um teste encontrou um erro real na primeira versão: uma trajetória vazia criava DataFrame sem colunas e quebrava antes de reportar o estoque inicial. O código foi corrigido para declarar as colunas mesmo sem linhas e o teste passou. Esse é um exemplo de revisão do código por evidência, não um motivo para omitir casos extremos.

Os testes foram executados em Python 3.10.12 e 3.12.15. A aplicação foi exercitada em PT/EN, prazo 5/validade 3 e troca de método. Houve inspeção visual em 320, 390 e 1280 pixels. Não houve instalação ou execução deste projeto no Dell, validação clínica/sanitária, teste de carga ou uso com dados de cliente.

## 16. Como reproduzir

Crie um ambiente separado na raiz deste projeto. No Ubuntu/WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.pipeline
```

No PowerShell, use os executáveis de `.venv\Scripts\` se a ativação de scripts estiver bloqueada. Não é necessário mudar a política global do Windows. O caminho de Windows nativo não foi testado nesta entrega; Linux Python 3.10 e 3.12 foi.

Para interface, instale `requirements-app.txt` e execute `python -m streamlit run app.py`. Para notebook, instale `requirements-notebook.txt` e execute as células em ordem numa sessão nova. O notebook importa `src.pipeline`, não carrega modelos binários de terceiros. A execução principal gera todas as saídas em `reports/`, inclusive dados sintéticos, previsões de validação/teste, cenários por trajetória, métricas, gráficos e HTML.

`forecast_next7.csv` é uma previsão demonstrativa de 23 a 29/08/2025 depois do histórico simulado. Não é uma recomendação de compra para a data atual. `simulation_trace_path0.csv` guarda o primeiro caminho de cada cenário; os arquivos de simulação guardam os resumos dos 200 caminhos. O código e a seed permitem gerar os demais rastros se necessário.

## 17. Como mudar e o que verificar

Para alterar uma ficha, mude `RECIPES_ML`, confira a conta de conversão e rode testes e pipeline. Para acrescentar uma bebida, gere uma série completa, acrescente a receita e confirme que todos os erros são alinhados por data. Se uma bebida não usar leite, decida se deve entrar no conjunto modelado ou ficar fora deste ingrediente; não invente consumo só para preencher uma coluna.

Para mudar o horizonte, reveja a origem temporal e a unidade de avaliação. O experimento está desenhado para emissão semanal. Uma previsão diária com revelação diária de observado pode ter erro diferente e não deve ser comparada sem explicar o protocolo. Para mudar alfa da suavização, ajuste-o apenas no treino/validação e mantenha o teste final fora da busca.

Para prazo variável, modele a chegada de cada compra explicitamente e verifique se a política usa uma estimativa conhecida na decisão. Para limite de geladeira, adicione capacidade e rejeição/adiamento de compra; não corte estoque sem registrar descarte. Para embalagens, arredonde pedido para múltiplos da embalagem e recalcule o balanço.

Para múltiplos ingredientes, cada bebida consome um vetor de fichas; cada ingrediente tem unidade, validade, custo e fornecedor. A disponibilidade de uma bebida passa a depender de todos os ingredientes. Esse problema é maior que somar litros e está reservado à evolução do sistema, não escondido como funcionalidade pronta aqui.

## 18. Como explicar numa entrevista FDE

Comece pela decisão: garantir matéria-prima sem exagerar em perecíveis. Em seguida mostre por que previsão de venda precisa de ficha técnica, por que dia sem coleta não é zero e por que a ordem dos eventos do estoque muda o resultado. Abra um teste manual, um rastro de três dias e a identidade de conservação de massa.

Mostre que o baseline venceu e que a política mais econômica em estoque não venceu em atendimento. Reconhecer um trade-off medido comunica mais cuidado que escolher uma métrica conveniente. Explique o que seria necessário para um piloto: contratos de dados, observação de ruptura, custos reais, prazo real, validade, responsáveis e limites de decisão automática.

Não diga que reduziu desperdício num café ou entregou um sistema de compra em produção. Diga que implementou, com assistência, um estudo reproduzível, examinou limitações e consegue explicar onde ele deixa de representar uma operação. A documentação foi feita para apoiar esse entendimento, não para substituir sua leitura do código.

## 19. Créditos e publicação

Inspiração temática: https://github.com/AmirhosseinHonardoust/Cafe-Demand-Forecasting-Reorder-Simulator . Nenhum arquivo, base ou implementação do autor foi copiado. Os nomes dos métodos descrevem conceitos, não uma reprodução literal do software de referência. Dependências mantêm suas próprias licenças; a fonte Inter tem SIL OFL incluída no pacote.

Nome proposto: `cafe-previsao-estoque`. O conteúdo e README estão preparados para revisão privada. Ainda não houve criação/publicação no GitHub e a escolha de licença do código autoral continua com o titular. O manual privado não integra o pacote e este trabalho não alterou o computador do titular.

Fontes técnicas e contexto: NumPy Generator, https://numpy.org/doc/stable/reference/random/generator.html ; pandas date_range, https://pandas.pydata.org/docs/reference/api/pandas.date_range.html ; Python NormalDist, https://docs.python.org/3/library/statistics.html#statistics.NormalDist . A prevenção de vazamento segue também https://scikit-learn.org/stable/common_pitfalls.html , embora esta implementação não precise de scikit-learn para seus três baselines.
