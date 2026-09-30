import csv,io,json,zipfile,pathlib,datetime
root=pathlib.Path(__file__).resolve().parents[1]/'public/data'
for year in [2026,2024]:
 z=zipfile.ZipFile(f'/tmp/tse-{year}.zip'); rows=list(csv.DictReader(io.StringIO(z.read(f'pesquisa_eleitoral_{year}_BRASIL.csv').decode('cp1252',errors='replace')),delimiter=';')); records=[];seen=set();details={};chunk=0
 target=root/str(year);target.mkdir(parents=True,exist_ok=True)
 for r in rows:
  id=r['NR_PROTOCOLO_REGISTRO']
  if id in seen:continue
  seen.add(id)
  rec=dict(id=id,year=int(r['AA_ELEICAO']),uf=r['SG_UF'],ue=r['SG_UE'],city=r['NM_UE'] if len(r['SG_UE'])>2 else '',election=r['NM_ELEICAO'],institute=r['NM_EMPRESA_FANTASIA'] if r['NM_EMPRESA_FANTASIA'] not in ['','#NULO#'] else r['NM_EMPRESA'],company=r['NM_EMPRESA'],cnpj=r['NR_CNPJ_EMPRESA'],offices=[x.strip() for x in r['DS_CARGO'].split(',')],registered=r['DT_REGISTRO'][:10],start=r['DT_INICIO_PESQUISA'][:10],end=r['DT_FIM_PESQUISA'][:10],release=r['DT_DIVULGACAO'][:10],sample=int(r['QT_ENTREVISTADO']),cost=float(r['VR_PESQUISA'].replace(',','.')),own=r['ST_PESQUISA_PROPRIA']=='S',statistician=r['NM_ESTATISTICO_RESP'],conre=r['CD_CONRE'],detailFile=f'/data/{year}/details-{chunk}.json')
  records.append(rec);details[id]=r
  if len(details)==100:
   (target/f'details-{chunk}.json').write_text(json.dumps(details,ensure_ascii=False));details={};chunk+=1
 if details:(target/f'details-{chunk}.json').write_text(json.dumps(details,ensure_ascii=False))
 (root/f'{year}.json').write_text(json.dumps(dict(records=records,generated=f'{rows[0]["DT_GERACAO"]} {rows[0]["HH_GERACAO"]}',fetchedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=f'https://cdn.tse.jus.br/estatistica/sead/odsele/pesquisa_eleitoral/pesquisa_eleitoral_{year}.zip',mode='snapshot'),ensure_ascii=False))
 print(year,len(records),'registros',len(set(r['city'] for r in records if r['city'])),'cidades')
