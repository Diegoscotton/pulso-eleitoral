"""Import only public election-facing candidate fields; exclude CPF, email, birth dates."""
import sys,json,zipfile,io,csv,pathlib,importlib,datetime
fetch=importlib.import_module('sync-tse').download
root=pathlib.Path(__file__).resolve().parents[1]/'public/data'
for year in (list(map(int,sys.argv[1:])) or [2026,2022,2018,2014]):
 meta=json.loads(fetch(f'https://dadosabertos.tse.jus.br/api/3/action/package_show?id=candidatos-{year}'))['result']
 url=next(r['url'] for r in meta['resources'] if r['name'].lower()=='candidatos')
 local=pathlib.Path(f'/tmp/candidates-{year}.zip')
 blob=local.read_bytes() if local.exists() else fetch(url)
 z=zipfile.ZipFile(io.BytesIO(blob));names=[n for n in z.namelist() if n.endswith('_BRASIL.csv')] or [n for n in z.namelist() if n.endswith('.csv')];records={};generated=''
 for name in names:
  for r in csv.DictReader(io.TextIOWrapper(z.open(name),encoding='cp1252',errors='replace',newline=''),delimiter=';'):
   if r['DS_CARGO'] not in ['PRESIDENTE','GOVERNADOR']:continue
   generated=f'{r["DT_GERACAO"]} {r["HH_GERACAO"]}'
   id=f'{r["CD_ELEICAO"]}-{r["NR_TURNO"]}-{r["SQ_CANDIDATO"]}'
   records[id]=dict(id=id,name=r['NM_URNA_CANDIDATO'],fullName=r['NM_CANDIDATO'],number=r['NR_CANDIDATO'],party=r['SG_PARTIDO'],partyName=r['NM_PARTIDO'],uf=r['SG_UF'],office=r['DS_CARGO'].title(),turn=r['NR_TURNO'],election=r['DS_ELEICAO'],status=r['DS_SITUACAO_CANDIDATURA'],coalition=r['NM_COLIGACAO'],composition=r['DS_COMPOSICAO_COLIGACAO'])
 assert records
 (root/f'candidates-{year}.json').write_text(json.dumps(dict(records=list(records.values()),generated=generated,source=url),ensure_ascii=False))
 print(year,len(records),'candidaturas de Presidente e Governador',flush=True)
