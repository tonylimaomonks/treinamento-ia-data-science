# Relatório-gabarito DS-101

É o veredito pronto, montado com o mesmo pipeline que o time vai usar no Ato 2. Serve como referência do facilitador e como material pós-treino.

```bash
bash gabarito/relatorio/rodar_queries.sh     # queries/r01–r09.sql → results/*.csv (dry run antes de cada uma)
python3 gabarito/relatorio/gen_data.py       # CSV → data.json → const D em relatorio_DS-101.html (valida o parse)
open gabarito/relatorio/relatorio_DS-101.html
```

- `template.html` é a fonte. O `relatorio_DS-101.html` é gerado: não edite à mão.
- Rodou o setup de novo (outro `DATA_REF`)? Rode os dois comandos acima: todos os números se atualizam.
- `r08` lê a cascata do `trama_gabarito`, que usa a verdade oculta do setup. O relatório diz isso nos caveats.
