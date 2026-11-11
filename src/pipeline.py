"""Previsão temporal e reposição perecível. Dados e políticas originais."""
from dataclasses import dataclass
from datetime import date,timedelta
from statistics import NormalDist
import math
import numpy as np
import pandas as pd
from .common import *
RECIPES_ML={'Cafe com leite':80,'Cappuccino':180}
METHODS=('seasonal7','moving7','ses025')
def generate(seed=SEED,days=600):
    """Cada registro é dia/item observado. Zero só aparece por fechamento conhecido."""
    rng=np.random.default_rng(seed);rows=[]
    for t in range(days):
        d=date(2024,1,1)+timedelta(days=t);is_open=d.weekday()!=6
        for item,base in [('Cafe com leite',54),('Cappuccino',32)]:
            weekly=[1.03,.98,1.02,1.12,1.35,1.5,0][d.weekday()]
            level=base*weekly*(1+.0003*t)+4*np.sin(t*2*np.pi/90)
            q=max(0,int(round(level+rng.normal(0,5)))) if is_open else 0
            rows.append(dict(date=d.isoformat(),item=item,quantity=q,is_open=is_open,observed=True))
    return pd.DataFrame(rows)
def validate_daily(raw):
    required={'date','item','quantity','is_open','observed'}
    if not required<=set(raw):raise ValueError('Colunas diarias ausentes')
    x=raw.copy();x['date']=pd.to_datetime(x.date,format='%Y-%m-%d',errors='raise')
    if x.empty:raise ValueError('Serie vazia')
    if x.duplicated(['date','item']).any():raise ValueError('Dia/item duplicado')
    if not x.item.isin(RECIPES_ML).all():raise ValueError('Ficha tecnica ausente')
    if not x.observed.eq(True).all():raise ValueError('Coleta ausente nao e zero')
    if not x.is_open.isin([True,False]).all():raise ValueError('Fechamento invalido')
    q=pd.to_numeric(x.quantity,errors='raise')
    if q.isna().any() or (~np.isfinite(q)).any() or (q<0).any() or (q%1!=0).any():raise ValueError('Quantidade deve ser inteiro nao negativo')
    if ((~x.is_open.astype(bool))&(q!=0)).any():raise ValueError('Venda em fechamento contraditorio')
    full=pd.date_range(x.date.min(),x.date.max(),freq='D')
    for item in RECIPES_ML:
        dates=x.loc[x.item==item,'date'].sort_values()
        if len(dates)!=len(full) or not np.array_equal(dates.values,full.values):raise ValueError('Dia ausente: recuperar coleta, nao preencher zero')
    x['quantity']=q.astype(int);return x.sort_values(['date','item']).reset_index(drop=True)
def forecast(history,horizon,method):
    h=np.asarray(history,dtype=float)
    if h.ndim!=1 or len(h)<7 or not isinstance(horizon,(int,np.integer)) or isinstance(horizon,bool) or horizon<1 or np.any(~np.isfinite(h)) or np.any(h<0):raise ValueError('Historico unidimensional >=7, finito e nao negativo; horizonte inteiro positivo')
    if method=='seasonal7':p=np.resize(h[-7:],horizon)
    elif method=='moving7':p=np.repeat(h[-7:].mean(),horizon)
    elif method=='ses025':
        level=h[0]
        for v in h[1:]:level=.25*v+.75*level
        p=np.repeat(level,horizon)
    else:raise ValueError('Metodo desconhecido')
    return np.maximum(0,p)
def backtest(values,start,stop,method,horizon=7):
    """Origens não sobrepostas, sem revelar o futuro dentro dos 7 dias."""
    y=np.asarray(values,float);rows=[]
    if start<7 or stop>len(y) or start>=stop:raise ValueError('Janela invalida')
    for origin in range(start,stop,horizon):
        end=min(origin+horizon,stop);pred=forecast(y[:origin],end-origin,method)
        for t,p in zip(range(origin,end),pred):rows.append(dict(origin=origin,index=t,actual=float(y[t]),prediction=float(p),method=method))
    return pd.DataFrame(rows)
@dataclass(frozen=True)
class Policy:
    lead_days:int=2
    service:float=.95
    shelf_days:int=7
    review_days:int=1
    def __post_init__(self):
        if any(not isinstance(v,(int,np.integer)) or isinstance(v,bool) or v<1 for v in [self.lead_days,self.shelf_days,self.review_days]):raise ValueError('Prazos inteiros positivos')
        if not np.isfinite(self.service) or not .5<self.service<1:raise ValueError('Servico entre .5 e 1')
def levels(mean_ml,std_ml,policy):
    if not np.isfinite(mean_ml) or not np.isfinite(std_ml) or mean_ml<0 or std_ml<0:raise ValueError('Demanda finita e nao negativa')
    z=NormalDist().inv_cdf(policy.service)
    safety=z*std_ml*math.sqrt(policy.lead_days)
    rop=math.ceil(mean_ml*policy.lead_days+safety)
    target=math.ceil(mean_ml*(policy.lead_days+policy.review_days)+z*std_ml*math.sqrt(policy.lead_days+policy.review_days))
    return dict(rop_ml=rop,target_ml=target,safety_ml=math.ceil(safety))
def simulate(demand_ml,mean_ml,std_ml,policy,baseline=False):
    """Recebe > expira > atende FEFO > repõe. Falta perdida, sem backlog.
    Lote vence no início do dia arrival+shelf_days. Reposição não chega no dia.
    O estoque inicial é comprado e tem validade, não é estoque gratuito.
    """
    demand=np.asarray(demand_ml)
    if demand.ndim!=1 or np.any(~np.isfinite(demand)) or np.any(demand<0) or np.any(demand%1):raise ValueError('Demanda em ml inteiros nao negativos')
    lev=levels(mean_ml,std_ml,policy);initial=lev['target_ml'];lots=[[policy.shelf_days,initial]];pipeline=[];rows=[];purchased=initial
    for day,d in enumerate(demand.astype(int)):
        arrived=sum(q for arrival,q in pipeline if arrival==day)
        if arrived:lots.append([day+policy.shelf_days,arrived])
        pipeline=[p for p in pipeline if p[0]>day]
        expired=sum(q for expiry,q in lots if expiry<=day);lots=[lot for lot in lots if lot[0]>day]
        before=sum(q for _,q in lots);need=int(d);served=0;lots.sort()
        for lot in lots:
            used=min(lot[1],need);lot[1]-=used;need-=used;served+=used
        lots=[lot for lot in lots if lot[1]>0];onhand=sum(q for _,q in lots);position=onhand+sum(q for _,q in pipeline)
        order=0
        if day%policy.review_days==0:
            # Base: pedido fixo igual à demanda média de um dia, sem proteção.
            if baseline:order=math.ceil(mean_ml*policy.review_days)
            elif position<=lev['rop_ml']:order=max(0,lev['target_ml']-position)
        if order:pipeline.append((day+policy.lead_days,order));purchased+=order
        rows.append(dict(day=day,demand_ml=int(d),arrival_ml=arrived,expired_ml=expired,before_demand_ml=before,served_ml=served,lost_ml=need,onhand_ml=onhand,pipeline_ml=sum(q for _,q in pipeline),order_ml=order))
    trace=pd.DataFrame(rows,columns=['day','demand_ml','arrival_ml','expired_ml','before_demand_ml','served_ml','lost_ml','onhand_ml','pipeline_ml','order_ml']);lost=int(trace.lost_ml.sum());total=int(trace.demand_ml.sum());waste=int(trace.expired_ml.sum());end=int(trace.onhand_ml.iloc[-1]) if len(trace) else initial;transit=sum(q for _,q in pipeline)
    assert purchased==int(trace.served_ml.sum())+waste+end+transit
    return dict(fill_rate=1-lost/total if total else 1,stockout_days=int((trace.lost_ml>0).sum()),lost_ml=lost,waste_ml=waste,average_stock_ml=float(trace.onhand_ml.mean()) if len(trace) else 0,purchased_ml=purchased,end_onhand_ml=end,end_pipeline_ml=transit,simulated_purchase_cents=purchased,simulated_lost_margin_cents=lost*2),trace

def run():
    x=validate_daily(generate());save_csv('daily_synthetic.csv',x)
    validation=[];final=[];selections={};future=[];total_ml=None;train_ml=None;validation_ml=None
    for item,milk in RECIPES_ML.items():
        y=x.loc[x.item==item,'quantity'].to_numpy(float);n=len(y);train_end=n-140;test_start=n-56
        scores={}
        for method in METHODS:
            v=backtest(y,train_end,test_start,method);v['item']=item;validation.append(v);scores[method]=mae(v.actual,v.prediction)
        selected=min(scores,key=lambda k:(scores[k],k));selections[item]=dict(method=selected,validation_mae=scores,train_days=train_end,validation_days=test_start-train_end,test_days=n-test_start)
        f=backtest(y,test_start,n,selected);f['item']=item;final.append(f)
        # Última previsão demonstrativa após fechar todo o histórico, não métrica de teste.
        p=forecast(y,7,selected)
        for h,value in enumerate(p):future.append(dict(date=(x.date.max()+pd.Timedelta(days=h+1)).date().isoformat(),item=item,predicted_units=float(value),milk_ml=float(value*milk)))
        total_ml=y*milk if total_ml is None else total_ml+y*milk
        train_ml=y[:train_end]*milk if train_ml is None else train_ml+y[:train_end]*milk
    v=pd.concat(validation,ignore_index=True);f=pd.concat(final,ignore_index=True)
    save_csv('validation_predictions.csv',v);save_csv('test_predictions.csv',f);save_csv('forecast_next7.csv',pd.DataFrame(future))
    performance=f.groupby('item').apply(lambda g:pd.Series({'mae_units':mae(g.actual,g.prediction),'wape':wape(g.actual.to_numpy(),g.prediction.to_numpy())}),include_groups=False).reset_index()
    save_csv('forecast_metrics.csv',performance)
    # Decisão para a semana seguinte ao histórico: previsão já atualizada com
    # dados conhecidos. Não altera a seleção nem as métricas do teste final.
    future_milk=pd.DataFrame(future).groupby('date').milk_ml.sum().to_numpy()
    residual=[]
    for item,milk in RECIPES_ML.items():
        chosen=v[(v.item==item)&(v.method==selections[item]['method'])].copy()
        chosen['error_ml']=(chosen.actual-chosen.prediction)*milk
        residual.append(chosen[['index','error_ml']])
    errors=pd.concat(residual).groupby('index').error_ml.sum().to_numpy()
    mean=float(np.mean(future_milk));std=float(np.std(errors,ddof=1))
    # Bootstrap emparelhado de semanas de erro da validação. Preserva a
    # dependência entre bebidas e dias na mesma semana; não usa erros do teste.
    complete=errors[:len(errors)//7*7].reshape(-1,7);rng=np.random.default_rng(SEED+8)
    paths=[np.maximum(0,np.rint(np.resize(future_milk,90)+np.concatenate([complete[int(rng.integers(len(complete)))] for _ in range(13)])[:90])).astype(int) for _ in range(200)]
    summary=[];traces=[]
    for lead in [2,5]:
        for service in [.90,.975]:
            for baseline in [True,False]:
                pol=Policy(lead,service,7,1);runs=[]
                for path_id,d in enumerate(paths):
                    res,trace=simulate(d,mean,std,pol,baseline);res['path_id']=path_id;runs.append(res)
                    if path_id==0:trace['policy']='fixed' if baseline else 'rop';trace['lead_days']=lead;trace['service']=service;traces.append(trace)
                r=pd.DataFrame(runs);label='fixed' if baseline else 'rop'
                save_csv(f'simulation_{label}_lead{lead}_s{service}.csv',r)
                summary.append(dict(policy=label,lead_days=lead,service=service,fill_rate_mean=float(r.fill_rate.mean()),fill_rate_p05=float(r.fill_rate.quantile(.05)),fill_rate_p95=float(r.fill_rate.quantile(.95)),waste_liters_mean=float(r.waste_ml.mean()/1000),stock_liters_mean=float(r.average_stock_ml.mean()/1000),stockout_days_mean=float(r.stockout_days.mean()),purchase_reais_mean=float(r.simulated_purchase_cents.mean()/100),**levels(mean,std,pol)))
    sim=pd.DataFrame(summary);save_csv('simulation_summary.csv',sim);save_csv('simulation_trace_path0.csv',pd.concat(traces,ignore_index=True))
    stats=dict(environment=environment(),selections=selections,performance=performance.to_dict('records'),inventory_parameters=dict(mean_forecast_ml=mean,std_validation_error_ml=std,recipes_ml=RECIPES_ML,shelf_days=7,bootstrap_paths=200,path_days=90,demand_model='previsao proxima semana + bootstrap de semanas de erro da validacao',purchase_cents_per_ml=1,lost_margin_cents_per_ml=2),simulations=summary,scope='Demanda de bebidas convertida em um ingrediente: leite; nao sistema completo de ingredientes')
    save_json('metrics.json',stats)
    plt=setup_plot();fig,axs=plt.subplots(2,1,figsize=(9,7))
    for ax,(item,g) in zip(axs,f.groupby('item')):
        ax.plot(g['index'],g.actual,label='Observado sintético');ax.plot(g['index'],g.prediction,label='Previsão 7 dias');ax.set(title=item,ylabel='Unidades');ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(outdir()/'forecast.png');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4));plot=sim[(sim.service==.975)];labels=plot.policy+' L'+plot.lead_days.astype(str);ax.bar(labels,plot.fill_rate_mean);ax.set(ylim=(0,1.05),ylabel='Fração de demanda atendida',title='Reposição: média em 200 trajetórias por cenário');fig.tight_layout();fig.savefig(outdir()/'inventory.png');plt.close(fig)
    dashboard('Quando repor o estoque do café?','Você compara três previsões e simula reposição com prazo de fornecedor, validade e falta perdida.',{'Dias observados':len(x)//2,'Itens vendidos':2,'Trajetórias por cenário':200,'Validade do leite':'7 dias'},{'Teste final intocado na seleção':performance.round(4),'Cenários de reposição':sim.round(3),'Previsão seguinte (não avaliada)':pd.DataFrame(future).round(2)},[('forecast.png','Últimos 56 dias em previsões de sete dias'),('inventory.png','Serviço simulado não é garantia real')]);print(performance.to_string(index=False));print(sim.to_string(index=False));return stats
if __name__=='__main__':run()
