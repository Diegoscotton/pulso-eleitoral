# Pulso Eleitoral
Dashboard em português com dados reais do TSE / PesqEle. Registros deduplicados por protocolo, filtros por UF, município eleitoral, cargo, instituto, eleição, datas, amostra, valor, pesquisa própria e estatístico. Exportação CSV e metodologia completa.

## Hospedagem gratuita no GitHub Pages
1. Publicar este projeto em um repositório público (compatível com GitHub Free).
2. Em Settings → Pages, selecionar **GitHub Actions** como origem.
3. Executar o workflow **Atualizar TSE e publicar painel**.
O workflow consulta a API CKAN oficial, baixa os CSVs de 2012 a 2026 e publica o site. A rotina diária está configurada para 10:17 UTC (07:17 Brasília), sujeita aos atrasos e políticas de inatividade do GitHub. Não requer chave de API nem servidor pago. Falhas de importação interrompem a nova publicação, preservando o site anteriormente publicado. Os dados não são enviados ao Git e não há token pessoal no workflow.

## Executar localmente
Requer Node 22 e Python 3.12+.
```
npm ci
npm run sync:tse
npm run dev:pages
```
Build estático: `npm run build:pages`. Para subdiretório: `PAGES_BASE=/nome-do-repositorio/ npm run build:pages`.

## Integração
- API: `https://dadosabertos.tse.jus.br/api/3/action/package_show?id=pesquisas-eleitorais-2026`
- Catálogo: `https://dadosabertos.tse.jus.br/group/pesquisas-eleitorais`
- Recursos ZIP oficiais são descobertos pela API, não por scraping de resultados.
- O parser respeita encoding Windows-1252, campos entre aspas, ponto e vírgula e textos multilinha.
- O arquivo BRASIL inclui todas as UFs; não somar os arquivos estaduais.
- A versão com servidor disponibiliza `/api/pesquisas?year=2026`, `/api/pesquisas?year=2026&id=...` e `/api/catalogo?year=2026`. Cache de 15 minutos e limite de download de 48 MiB. A versão Pages usa importação prévia em CI e não depende dessas rotas.

## Limitações verificadas
A base CSV não contém percentuais de voto, rejeição, nomes de candidatos nem cenários. O PesqEle rejeitou o acesso automatizado aos relatórios completos. A aba Candidatos informa essa ausência explicitamente; nenhuma série eleitoral é inventada. Para incorporar resultados será necessário acesso aos relatórios e extração verificável, mantendo cenário, cargo, turno, universo, período e fonte.
Município significa unidade eleitoral registrada, não cada cidade visitada em uma pesquisa estadual. Margem de erro e confiança permanecem no texto original da metodologia. Datas de divulgação são previstas e não confirmam publicação; amostras são declaradas. Os nomes de institutos são os registrados, sem deduplicação corporativa adicional.
