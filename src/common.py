"""Utilidades próprias para artefatos locais. Nenhum dado externo é obtido."""
from pathlib import Path
import json, html, platform, sys
import numpy as np
import pandas as pd
SEED=20261111
BASE=Path(__file__).resolve().parents[1]
def outdir():
    p=BASE/'reports';p.mkdir(exist_ok=True);return p
def save_json(name, obj):
    def conv(x):
        if isinstance(x, np.generic):return x.item()
        if isinstance(x, np.ndarray):return x.tolist()
        if isinstance(x, Path):return str(x)
        raise TypeError(type(x).__name__)
    (outdir()/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=conv,allow_nan=False)+'\n',encoding='utf8')
def save_csv(name, df):df.to_csv(outdir()/name,index=False)
def environment():
    import matplotlib
    return dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__,seed=SEED)
def mae(y,p):return float(np.mean(np.abs(np.asarray(y)-np.asarray(p))))
def wape(y,p):
    den=float(np.abs(y).sum());return float(np.abs(np.asarray(y)-p).sum()/den) if den else None
def dashboard(title, intro, metrics, tables, images=()):
    esc=lambda x:html.escape(str(x))
    cards=''.join('<article><small>'+esc(k)+'</small><strong>'+esc(v)+'</strong></article>' for k,v in metrics.items())
    def table_html(df):
        heads=''.join('<th>'+esc(c)+'</th>' for c in df.columns)
        rows=''.join('<tr>'+''.join('<td data-label="'+esc(c)+'">'+esc('não se aplica' if pd.isna(v) else v)+'</td>' for c,v in zip(df.columns,row))+'</tr>' for row in df.itertuples(index=False,name=None))
        return '<table><thead><tr>'+heads+'</tr></thead><tbody>'+rows+'</tbody></table>'
    sections=''.join('<section><h2>'+esc(k)+'</h2><div class="scroll">'+table_html(df)+'</div></section>' for k,df in tables.items())
    pics=''.join('<figure><img src="'+esc(x)+'" alt="'+esc(label)+'"><figcaption>'+esc(label)+'</figcaption></figure>' for x,label in images)
    page="""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>@font-face{{font-family:Inter;src:url('../assets/Inter.ttf')}}@font-face{{font-family:Inter;font-weight:700 900;src:url('../assets/Inter-Bold.ttf')}}:root{{--accent:#3f3cd8;--soft:#eef0ff;--ink:#161514;--muted:#5c5955;--line:#e9e8e4}}*{{box-sizing:border-box}}body{{margin:0;background:#fbfbfa;color:var(--ink);font:16px/1.6 Inter,Arial,sans-serif}}main{{max-width:1100px;margin:auto;padding:40px 24px}}header{{border-bottom:1px solid var(--line);padding-bottom:30px}}.brand{{font-size:24px;font-weight:800;color:var(--accent);letter-spacing:-.02em}}h1{{font-size:clamp(30px,5vw,52px);line-height:1.08;letter-spacing:-.02em;max-width:20ch}}h2{{font-size:25px;line-height:1.2}}p{{max-width:75ch}}.note{{background:var(--soft);padding:20px;border-radius:14px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:30px 0}}article{{padding:20px;background:white;border:1px solid var(--line);border-radius:18px}}small{{display:block;color:var(--muted)}}strong{{font-size:24px;overflow-wrap:anywhere}}section{{margin:48px 0}}.scroll{{overflow:auto;border:1px solid var(--line);border-radius:14px}}table{{border-collapse:collapse;width:100%;background:white;white-space:nowrap;font-size:14px}}td,th{{padding:12px 16px;text-align:left;border-bottom:1px solid var(--line)}}th{{background:var(--soft)}}img{{max-width:100%;height:auto}}figure{{margin:24px 0}}figcaption,footer{{font-size:14px;color:var(--muted)}}details{{border:1px solid var(--line);padding:16px;border-radius:14px}}a{{color:var(--accent)}}@media(max-width:400px){{main{{padding:24px 16px}}.cards{{grid-template-columns:1fr 1fr}}strong{{font-size:20px}}}}@media(max-width:600px){{.scroll{{border:0;overflow:visible}}table,tbody,tr,td{{display:block;white-space:normal}}thead{{display:none}}tr{{padding:12px 16px;margin:14px 0;border:1px solid var(--line);border-radius:14px}}td{{display:flex;justify-content:space-between;gap:16px;padding:9px 0;overflow-wrap:anywhere}}td::before{{content:attr(data-label);font-weight:600;max-width:55%;flex-shrink:0}}td:last-child{{border:0}}}}@media print{{main{{max-width:none}}.scroll{{overflow:visible}}table{{white-space:normal}}}}</style><main><header><div class="brand">data with natan</div><p>ESTUDO INDEPENDENTE · DADOS SINTÉTICOS</p><h1>{title}</h1><p>{intro}</p></header><p class="note">Simulação didática, sem clientes reais. Os resultados não demonstram ganho comercial, satisfação ou risco real. Leia as hipóteses e os testes no documento explicativo.</p><div class="cards">{cards}</div>{pics}{sections}<details><summary>Como reproduzir / Reproduce</summary><p>Na raiz: <code>python -m src.pipeline</code>. Para testes: <code>python -m unittest discover -s tests -v</code>. Os dados são gerados localmente com seed fixa; não há acesso a rede.</p><p>Independent study with synthetic data. Run the same commands to regenerate outputs. No real restaurant, customer or operational gain is represented.</p></details><footer><p>Implementação original com assistência de IA. Conteúdo preparado para revisão; nenhuma autoria individual não assistida é alegada.</p></footer></main></html>"""
    (outdir()/'dashboard.html').write_text(page.format(title=esc(title),intro=esc(intro),cards=cards,sections=sections,pics=pics),encoding='utf8')
def setup_plot():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'figure.dpi':130,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.prop_cycle':plt.cycler(color=['#3f3cd8','#161514','#8a877f']),'axes.facecolor':'#ffffff','figure.facecolor':'#fbfbfa'})
    return plt
