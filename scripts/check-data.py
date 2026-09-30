import json,pathlib,datetime
root=pathlib.Path(__file__).resolve().parents[1]/'public/data'
total=0
for year in [2026,2024,2022,2020,2018,2016,2014,2012]:
 d=json.loads((root/f'{year}.json').read_text());records=d['records'];assert len({r['id'] for r in records})==len(records)
 for r in records:
  assert r['year']==year
  for key in ['registered','start','end','release']:
   if r[key]:datetime.date.fromisoformat(r[key])
  assert (root.parent/r['detailFile'].lstrip('/')).is_file()
 for r in [records[0],records[-1]]:
  details=json.loads((root.parent/r['detailFile'].lstrip('/')).read_text());assert r['id'] in details
 total+=len(records)
 print(year,len(records),'OK')
print('Total validado:',total)
