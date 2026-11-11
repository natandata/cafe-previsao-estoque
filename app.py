"""Cenários locais de previsão e reposição com dados sintéticos."""
from pathlib import Path
import base64,numpy as np,pandas as pd,streamlit as st
from src.pipeline import generate,validate_daily,forecast,backtest,Policy,levels,simulate,RECIPES_ML,METHODS
from src.common import SEED
st.set_page_config(page_title='Previsão e estoque',layout='wide')
_font=base64.b64encode((Path(__file__).parent/'assets/Inter.ttf').read_bytes()).decode()
st.markdown('<style>@font-face{font-family:Inter;src:url(data:font/ttf;base64,'+_font+')} html,body,h1,h2,h3,p,button,input,select,[data-testid=stApp]{font-family:Inter,Arial,sans-serif}h1,h2{letter-spacing:-.02em}.brand{color:#3f3cd8;font-size:24px;font-weight:800}</style>',unsafe_allow_html=True)
lang=st.sidebar.radio('Idioma' if st.session_state.get('language','PT')=='PT' else 'Language',['PT','EN'],key='language');en=lang=='EN'
def t(pt,eng):return eng if en else pt
def num(v,digits=0):
 s=f'{v:,.{digits}f}';return s if en else s.translate(str.maketrans(',.','.,'))
def pct(v):return num(v*100,1)+'%'
st.markdown('<div class="brand">data with natan</div>',unsafe_allow_html=True)
st.title(t('Previsão e estoque perecível','Forecasting and perishable stock'))
st.info(t('Demanda sintética. Isto é um cenário, não uma ordem de compra.','Synthetic demand. This is a scenario, not a purchase instruction.'))
@st.cache_data
def daily():return validate_daily(generate())
x=daily();names={'Cafe com leite':t('Café com leite','Coffee with milk'),'Cappuccino':'Cappuccino'}
item=st.sidebar.selectbox(t('Bebida','Drink'),list(RECIPES_ML),format_func=lambda v:names[v])
method_labels={'seasonal7':t('Sazonal semanal','Weekly seasonal naive'),'moving7':t('Média móvel de 7 dias','7-day moving mean'),'ses025':t('Suavização exponencial','Exponential smoothing')}
method=st.sidebar.selectbox(t('Método de previsão','Forecast method'),list(METHODS),format_func=lambda v:method_labels[v])
lead=st.sidebar.slider(t('Prazo do fornecedor (dias)','Lead time (days)'),1,7,2)
shelf=st.sidebar.slider(t('Validade (dias)','Shelf life (days)'),1,14,7)
service=st.sidebar.select_slider(t('Serviço nominal de ciclo','Nominal cycle service'),options=[.80,.90,.95,.975,.99],value=.95,format_func=pct)
seed=st.sidebar.number_input(t('Seed da simulação','Simulation seed'),min_value=0,max_value=2**31-1,value=SEED+8)
st.subheader(t('Previsão','Forecast'))
y=x[x.item==item].quantity.to_numpy(float);st.line_chart(pd.DataFrame({t('Unidades','Units'):y[-56:]}),color='#3f3cd8');st.caption(t('Unidades sintéticas por dia nos últimos 56 dias.','Synthetic units per day over the last 56 days.'))
f=forecast(y,7,method)
st.dataframe(pd.DataFrame({t('Dia do horizonte','Horizon day'):range(1,8),t('Unidades previstas','Predicted units'):[num(v,2) for v in f],t('Leite (ml)','Milk (ml)'):[num(v*RECIPES_ML[item],0) for v in f]}),hide_index=True)
st.caption(t('Horizonte semanal: a previsão não recebe observações futuras dentro da semana.','Weekly horizon: no future observations enter a forecast already issued.'))
st.subheader(t('Cenário de estoque','Inventory scenario'))
st.caption(t('Ficha: 80 ml por café com leite e 180 ml por cappuccino. Semanas de erro da validação são reamostradas em conjunto.','Recipes use 80 ml per coffee with milk and 180 ml per cappuccino. Validation-error weeks are jointly resampled.'))
if st.button(t('Simular 50 trajetórias','Simulate 50 paths'),type='primary'):
 pred=np.zeros(7);res=[]
 for name,milk in RECIPES_ML.items():
  yy=x[x.item==name].quantity.to_numpy(float);pred+=forecast(yy,7,method)*milk;b=backtest(yy,len(yy)-140,len(yy)-56,method);b['error_ml']=(b.actual-b.prediction)*milk;res.append(b[['index','error_ml']])
 errors=pd.concat(res).groupby('index').error_ml.sum().to_numpy();weeks=errors.reshape(-1,7);rng=np.random.default_rng(int(seed));pol=Policy(int(lead),float(service),int(shelf),1);mean=pred.mean();std=errors.std(ddof=1);rows=[]
 for i in range(50):
  noise=np.concatenate([weeks[int(rng.integers(len(weeks)))] for _ in range(13)])[:90];d=np.maximum(0,np.rint(np.resize(pred,90)+noise)).astype(int);result,trace=simulate(d,mean,std,pol);rows.append(result)
 r=pd.DataFrame(rows);a,b,c=st.columns(3);a.metric(t('Demanda atendida','Fill rate'),pct(r.fill_rate.mean()));b.metric(t('Descarte (L)','Waste (L)'),num(r.waste_ml.mean()/1000,2));c.metric(t('Estoque médio (L)','Average stock (L)'),num(r.average_stock_ml.mean()/1000,2))
 lev=levels(mean,std,pol);st.subheader(t('Parâmetros da política','Policy levels'))
 st.dataframe(pd.DataFrame({t('Parâmetro','Parameter'):[t('Ponto de reposição (ml)','Reorder point (ml)'),t('Estoque-alvo (ml)','Target stock (ml)'),t('Segurança (ml)','Safety stock (ml)')],t('Valor','Value'):[num(lev[k]) for k in ['rop_ml','target_ml','safety_ml']]}),hide_index=True)
 st.subheader(t('Rastro da última trajetória','Last path trace'))
 labels={'day':t('Dia','Day'),'demand_ml':t('Demanda (ml)','Demand (ml)'),'arrival_ml':t('Chegada (ml)','Arrival (ml)'),'expired_ml':t('Vencido (ml)','Expired (ml)'),'before_demand_ml':t('Antes do consumo (ml)','Before demand (ml)'),'served_ml':t('Atendido (ml)','Served (ml)'),'lost_ml':t('Perdido (ml)','Lost (ml)'),'onhand_ml':t('Em mãos (ml)','On hand (ml)'),'pipeline_ml':t('Em trânsito (ml)','In transit (ml)'),'order_ml':t('Compra (ml)','Order (ml)')}
 st.dataframe(trace.map(lambda v:num(v)).rename(columns=labels),hide_index=True)
 st.download_button(t('Baixar trajetórias','Download paths'),r.to_csv(index=False).encode(),file_name='scenarios.csv',mime='text/csv')
 st.caption(t('O CSV preserva os nomes técnicos, números sem formatação e unidades documentadas.','CSV retains technical names, unformatted numbers and documented units.'))
 st.warning(t('Serviço nominal é entrada da aproximação normal, não garantia de demanda atendida. Demanda, validade e prazo mudam o resultado.','Nominal service is a normal-approximation input, not a fill-rate guarantee. Demand, expiry and lead assumptions matter.'))
st.caption(t('O seletor explora métodos. O relatório versionado escolhe pela validação, nunca pelo teste final.','The selector explores methods. The versioned report selects on validation, never on final test.'))
