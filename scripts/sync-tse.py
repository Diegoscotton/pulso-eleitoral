"""Fetch official CKAN resources and export static, deduplicated dashboard data."""
import csv,io,json,zipfile,pathlib,datetime,urllib.request,sys,time,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]/'public/data'
YEARS=[2026,2024,2022,2020,2018,2016,2014,2012]
def download(url):
 from urllib.parse import urlparse
 assert urlparse(url).hostname in ['dadosabertos.tse.jus.br','cdn.tse.jus.br'] and url.startswith('https://')
 for attempt in range(3):
  try:
   with urllib.request.urlopen(url,timeout=120) as r:return r.read()
  except Exception:
   if attempt==2:raise
   time.sleep(3*(attempt+1))
def iso(value):
 value=(value or '')[:10]
 if '/' in value:
  try:return datetime.datetime.strptime(value,'%d/%m/%Y').date().isoformat()
  except ValueError:return ''
 return value if len(value)==10 and value[4]=='-' else ''
def sync(year):
 meta=json.loads(download(f'https://dadosabertos.tse.jus.br/api/3/action/package_show?id=pesquisas-eleitorais-{year}'))['result']
 resources=[dict(name=r['name'],url=r['url'],format=r['format']) for r in meta['resources']]
 url=next(r['url'] for r in resources if r['name'].lower()=='pesquisas eleitorais')
 archive=zipfile.ZipFile(io.BytesIO(download(url)));names=[n for n in archive.namelist() if n.lower().endswith('_brasil.csv')] or [n for n in archive.namelist() if n.lower().endswith('.csv')]
 target=ROOT/str(year);target.mkdir(parents=True,exist_ok=True)
 records=[];details={};seen=set();chunk=0;generated=''
 for name in names:
  with archive.open(name) as f:
   for r in csv.DictReader(io.TextIOWrapper(f,encoding='cp1252',errors='replace',newline=''),delimiter=';'):
    r['DS_CARGO']=r.get('DS_CARGO',r.get('DS_CARGOS',''))
    r['QT_ENTREVISTADO']=r.get('QT_ENTREVISTADO',r.get('QT_ENTREVISTADOS','0'))
    id=r['NR_PROTOCOLO_REGISTRO']
    if id in seen:continue
    seen.add(id);generated=f'{r["DT_GERACAO"]} {r["HH_GERACAO"]}'
    def num(key):
     try:return float(r.get(key,'0').replace(',','.'))
     except ValueError:return 0
    rec=dict(id=id,year=int(r['AA_ELEICAO']),uf=r['SG_UF'],ue=r['SG_UE'],city=r['NM_UE'] if len(r['SG_UE'])>2 else '',election=r['NM_ELEICAO'],institute=r['NM_EMPRESA_FANTASIA'] if r['NM_EMPRESA_FANTASIA'] not in ['','#NULO#'] else r['NM_EMPRESA'],company=r['NM_EMPRESA'],cnpj=r['NR_CNPJ_EMPRESA'],offices=[x.strip() for x in r['DS_CARGO'].split(',') if x.strip() and x.strip()!='#NULO#'],registered=iso(r.get('DT_REGISTRO')),start=iso(r.get('DT_INICIO_PESQUISA')),end=iso(r.get('DT_FIM_PESQUISA')),release=iso(r.get('DT_DIVULGACAO')),sample=num('QT_ENTREVISTADO'),cost=num('VR_PESQUISA'),own=(r.get('ST_PESQUISA_PROPRIA')=='S') if r.get('ST_PESQUISA_PROPRIA') in ['S','N'] else None,statistician=r['NM_ESTATISTICO_RESP'],conre=r['CD_CONRE'],detailFile=f'/data/{year}/details-{chunk}.json')
    records.append(rec);details[id]=r
    if len(details)==100:
     (target/f'details-{chunk}.json').write_text(json.dumps(details,ensure_ascii=False));details={};chunk+=1
 if details:(target/f'details-{chunk}.json').write_text(json.dumps(details,ensure_ascii=False))
 assert records, 'Empty official dataset'
 payload=dict(records=records,generated=generated,fetchedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=url,mode='snapshot')
 (ROOT/f'{year}.json').write_text(json.dumps(payload,ensure_ascii=False))
 (ROOT/f'catalog-{year}.json').write_text(json.dumps(dict(resources=resources),ensure_ascii=False))
 print(f'{year}: {len(records)} registros',flush=True)
if __name__=='__main__':
 ROOT.mkdir(parents=True,exist_ok=True)
 for year in (list(map(int,sys.argv[1:])) or YEARS):sync(year)
