# benzene-data

Data pipeline behind the GB grid connection queue figures on www.benzene-group.com.

## Inputs (all public)
- `inputs/tec-register-*.csv`: NESO Transmission Entry Capacity register (published Tuesdays and Fridays, api.neso.energy)
- `inputs/REPD_Publication_*.csv`: DESNZ Renewable Energy Planning Database
- `inputs/cfd_contract_portfolio_status.csv`: Low Carbon Contracts Company CfD portfolio
- `reference/pypsa-gb`: substation locations (MIT licence, Andrew Lyden)

## Run
```
mkdir -p out
python3 -I scripts/build.py inputs/tec-register-13-november-2026.csv inputs/REPD_Publication_Q3_2026.csv inputs/cfd_contract_portfolio_status.csv out reference/pypsa-gb
python3 -I scripts/make_page.py out
python3 -I scripts/update_home.py out site
```
`build.py` writes `out/platform.json`; `make_page.py` builds the queue map; `update_home.py` refreshes the marked figures in `site/index.html` and `site/llms.txt` and prints what changed.

## Rules
- Figures come only from the opened primary sources above.
- If any headline figure moves by more than 10%, the refresh holds and asks for a human check before publishing.
- No em or en dashes in public text (the updater refuses to write them).
