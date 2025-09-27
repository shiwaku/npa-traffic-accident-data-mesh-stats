# npa-traffic-accident-data-mesh-stats

警察庁（NPA）の交通事故統計情情報のオープンデータを地域メッシュ単位で加工・集計し、GeoJSON / GeoParquet 形式で出力するツール群です。  

---

## 機能概要

### 1. メッシュコード付与 (`1.jiko_add_meshcode.py`)
- 入力: [honhyo_2019-2024_convert.csv, 1.4GB](https://xs489works.xsrv.jp/pmtiles-data/traffic-accident/honhyo_2019-2024_convert.csv)
- 緯度・経度から地域メッシュコード（3次, 4次, 5次, 6次）を算出  
- 範囲外の座標は `9999` を代入  
- 出力: [honhyo_2019-2024_convert_add_mesh.csv, 1.4GB](https://xs489works.xsrv.jp/pmtiles-data/traffic-accident/honhyo_2019-2024_convert_add_mesh.csv)

### 2. メッシュ別集計 (`2.jiko_mesh_syukei.py`)
- 入力: `honhyo_2019-2024_convert_add_mesh.csv`  
- 当事者Bの年齢を次の 8 区分に正規化して集計  
  - 0～24歳, 25～34歳, 35～44歳, 45～54歳,  
    55～64歳, 65～74歳, 75歳以上, 不明  
- メッシュ（3次～6次）ごとの事故件数を集計し、ポリゴン化  
- 各種設定
  - INPUT_CSV = "honhyo_2019-2024_convert_add_mesh.csv"
  - MESH_COL  = "mesh_6"
    - mesh_3: 1km mesh_4: 500m mesh_5: 250m mesh_6: 125mの指定が可能 
  - AGE_COL   = "年齢（当事者B）"
  - OUTPUT_FORMAT = "geoparquet"  # "geojson" / "geoparquet" / "both"
- 出力形式:  
  - GeoJSON: `mesh_ageB_counts_*.geojson`  
  - GeoParquet: `mesh_ageB_counts_*.parquet`
- 出力: 
  - [mesh_ageB_counts_1km.parquet, 2.9MB](https://xs489works.xsrv.jp/pmtiles-data/traffic-accident/mesh_ageB_counts_1km.parquet)
  - [mesh_ageB_counts_500m.parquet, 6.0MB](https://xs489works.xsrv.jp/pmtiles-data/traffic-accident/mesh_ageB_counts_500m.parquet)
  - [mesh_ageB_counts_250m.parquet, 12.0MB](https://xs489works.xsrv.jp/pmtiles-data/traffic-accident/mesh_ageB_counts_250m.parquet)
  - [mesh_ageB_counts_125m.parquet, 20.1MB](https://xs489works.xsrv.jp/pmtiles-data/traffic-accident/mesh_ageB_counts_125m.parquet)
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
