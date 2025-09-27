# npa-traffic-accident-data-mesh-stats

警察庁（NPA）の交通事故統計情情報のオープンデータを地域メッシュ単位で加工・集計し、GeoJSON / GeoParquet 形式で出力するツール群です。  

---

## 機能概要

### 1. メッシュコード付与 (`1.jiko_add_meshcode.py`)
- 入力: [honhyo_2019-2024_convert.csv ,1.4GB](https://xs489works.xsrv.jp/pmtiles-data/traffic-accident/honhyo_2019-2024_convert.csv)
- 緯度・経度から地域メッシュコード（3次, 4次, 5次, 6次）を算出  
- 範囲外の座標は `9999` を代入  
- 出力: `honhyo_2019-2024_convert_add_mesh.csv`

### 2. メッシュ別集計 (`2.jiko_mesh_syukei.py`)
- 入力: `honhyo_2019-2024_convert_add_mesh.csv`  
- 当事者Bの年齢を次の 8 区分に正規化して集計  
  - 0～24歳, 25～34歳, 35～44歳, 45～54歳,  
    55～64歳, 65～74歳, 75歳以上, 不明  
- メッシュ（3次～6次）ごとの事故件数を集計し、ポリゴン化  
- 出力形式:  
  - GeoJSON: `mesh_ageB_counts_*.geojson`  
  - GeoParquet: `mesh_ageB_counts_*.parquet`

---

## 必要なライブラリ

- Python 3.12.4
- [pandas](https://pandas.pydata.org/)  
- [numpy](https://numpy.org/)  
- [jismesh](https://pypi.org/project/jismesh/)  
- （GeoParquet 出力時）`geopandas`, `shapely`, `pyarrow`

インストール例：

```bash
pip install pandas numpy jismesh geopandas shapely pyarrow
