# Pending master additions (staged, not loaded)

Nothing in system.yaml or gen.py reads this directory. Each CSV has the target table's headers (plus new columns noted below)
and holds only the rows to APPEND. To apply: copy to seed/<table>.csv (seed overlay appends by key) and make the two edits below.

## New column / table (need system.yaml + gen.py edits)
- suppliers.csv: extra LAST column `supplier_type` (enum product|indirect). In system.yaml add it after account_manager_id;
  in gen.py set `s["supplier_type"] = "product"` for every generated supplier (no RNG use), just before `out["suppliers"]=...`.
- airports.csv: NEW table `airports` (key iata_code; cols iata_code, name, city, country, region); add to system.yaml tables.

## Rows
- legal_entities: LE-PL Harbour & Vale Polska (PLN).
- sites: DC6 Corby 3PL overflow DC (GB), DC7 Lodz DC (PL, LE-PL), DC8 Frankfurt DC (DE); stores ST256-ST259 (Lodz, Warsaw, Krakow, Wroclaw; PL, LE-PL). Update sites.site_id desc for the new id ranges.
- ports: USLAX, ESVLC, GRPIR, VNCMT, SGSIN, VNHPH.
- airports: DAC, SGN, IST, LHR, DXB, HKG, PVG, CDG.
- suppliers: SUP-0081..SUP-0090 indirect (packaging x2, energy x2, facilities x2, MRO x2, temporary labour, racking); spend 0, GB.
- factories: FAC-0152..0155 (KH x2, ID x2) on SUP-0001/0002/0003; no POs.
- partners: PTN-024 Mexico franchise.
- products: SKU-106307..106384 (12 SKUs, styles STY-9501..9510), status new, launch 2027, no sales/stock/POs.

## Reasoning / cautions
- Backpacks use new category "Backpacks" (not "Bags"): adding to Bags moved pricing's category median/percentile (SKU-103423 story: 0.74, 38.99).
  Other categories reused (Drinkware, Outerwear, Shirts, Trousers, Bedding, Smart Home); new categories Kitchenware (lunch box) and Toys (Kids). Toiletries not added (no named product).
- Not added: Czech entity (network does not imply it), southern DC / second Midlands DC (DC6 Corby covers Midlands overflow).
- Appending to sites/products/suppliers/factories shifts any generator that loops those tables with its RNG; re-generate and re-validate all systems together.
- mk_seed.py.txt is the script that produced these CSVs (reads data/ for supplier/factory picks).
