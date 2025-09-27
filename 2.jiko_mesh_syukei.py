#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
当事者Bの年齢階層別 事故件数をメッシュごとに集計し、
メッシュポリゴンを GeoJSON / GeoParquet で出力。

入力: honhyo_2019-2024_convert_add_mesh.csv
必須列: mesh_3/4/5/6, 年齢（当事者B）
出力:
  - GeoJSON: mesh_ageB_counts_*.geojson
  - GeoParquet: mesh_ageB_counts_*.parquet

年齢階層（当事者B）を次の8区分に正規化:
  0～24歳, 25～34歳, 35～44歳, 45～54歳, 55～64歳, 65～74歳, 75歳以上, 不明
"""

import json
import re
import sys
import numpy as np
import pandas as pd
import jismesh.utils as ju

# ====== 設定 ======
INPUT_CSV = "honhyo_2019-2024_convert_add_mesh.csv"
MESH_COL  = "mesh_6"   # "mesh_3" / "mesh_4" / "mesh_5" / "mesh_6" に変更可 mesh_3: 1km mesh_4: 500m mesh_5: 250m mesh_6: 125m
AGE_COL   = "年齢（当事者B）"
OUTPUT_FORMAT = "geoparquet"  # "geojson" / "geoparquet" / "both"

AGE_BUCKETS = [
    "0～24歳","25～34歳","35～44歳","45～54歳",
    "55～64歳","65～74歳","75歳以上","不明"
]

OUTNAME_PREFIX = {
    "mesh_3": "mesh_ageB_counts_1km",
    "mesh_4": "mesh_ageB_counts_500m",
    "mesh_5": "mesh_ageB_counts_250m",
    "mesh_6": "mesh_ageB_counts_125m",
}[MESH_COL]

OUTPUT_GEOJSON  = f"{OUTNAME_PREFIX}.geojson"
OUTPUT_PARQUET  = f"{OUTNAME_PREFIX}.parquet"

# ====== ユーティリティ: 年齢正規化 ======
import re
_rx_num = re.compile(r"\d+")
def normalize_age_bucket(x) -> str:
    if pd.isna(x):
        return "不明"
    s = str(x).strip()
    if s in AGE_BUCKETS:
        return s
    nums = _rx_num.findall(s)
    if not nums:
        return "不明"
    try:
        if "～" in s:
            n = int(nums[0])  # 下限で判定
        else:
            n = int(nums[0])
        if n <= 24:   return "0～24歳"
        if n <= 34:   return "25～34歳"
        if n <= 44:   return "35～44歳"
        if n <= 54:   return "45～54歳"
        if n <= 64:   return "55～64歳"
        if n <= 74:   return "65～74歳"
        return "75歳以上"
    except Exception:
        return "不明"

# ====== 読み込み & 前処理 ======
print(f"[INFO] reading: {INPUT_CSV}")
df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig", low_memory=False)

df[MESH_COL] = pd.to_numeric(df[MESH_COL], errors="coerce").astype("Int64")
valid_mesh = df[MESH_COL].notna() & (df[MESH_COL] != 9999)

df.loc[:, AGE_COL] = df[AGE_COL].apply(normalize_age_bucket)

# ====== 集計（メッシュ×年齢階層） ======
g = (
    df.loc[valid_mesh, [MESH_COL, AGE_COL]]
      .groupby([MESH_COL, AGE_COL], dropna=False)
      .size()
      .unstack(AGE_COL, fill_value=0)
)
g = g.reindex(columns=AGE_BUCKETS, fill_value=0)
g["総計"] = g.sum(axis=1)

print(f"[INFO] meshes: {len(g):,}  total accidents counted: {int(g['総計'].sum()):,}")

# ====== メッシュ → ポリゴン座標 ======
codes = g.index.to_numpy(dtype=np.int64)
lat_sw, lon_sw = ju.to_meshpoint(codes, 0, 0)  # 南西
lat_ne, lon_ne = ju.to_meshpoint(codes, 1, 1)  # 北東

# ====== GeoJSON 出力 ======
def write_geojson():
    features = []
    for i, code in enumerate(codes):
        ring = [
            [float(lon_sw[i]), float(lat_sw[i])],
            [float(lon_ne[i]), float(lat_sw[i])],
            [float(lon_ne[i]), float(lat_ne[i])],
            [float(lon_sw[i]), float(lat_ne[i])],
            [float(lon_sw[i]), float(lat_sw[i])],
        ]
        props = {"mesh_code": int(code)}
        for col in AGE_BUCKETS + ["総計"]:
            props[col] = int(g.loc[code, col])
        features.append({"type": "Feature",
                         "geometry": {"type": "Polygon", "coordinates": [ring]},
                         "properties": props})
    geojson = {"type": "FeatureCollection", "features": features}
    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    print(f"[INFO] wrote: {OUTPUT_GEOJSON}  (features={len(features):,})")

# ====== GeoParquet 出力（EPSG:4326） ======
def write_geoparquet():
    try:
        import geopandas as gpd
        from shapely.geometry import Polygon
    except Exception as e:
        print("[ERROR] GeoParquet 出力には 'geopandas', 'shapely', 'pyarrow' が必要です。")
        print("        例: pip install geopandas shapely pyarrow")
        raise

    # DataFrame -> GeoDataFrame
    records = []
    for i, code in enumerate(codes):
        ring = [
            (float(lon_sw[i]), float(lat_sw[i])),
            (float(lon_ne[i]), float(lat_sw[i])),
            (float(lon_ne[i]), float(lat_ne[i])),
            (float(lon_sw[i]), float(lat_ne[i])),
            (float(lon_sw[i]), float(lat_sw[i])),
        ]
        row = {"mesh_code": int(code)}
        for col in AGE_BUCKETS + ["総計"]:
            row[col] = int(g.loc[code, col])
        row["geometry"] = Polygon(ring)
        records.append(row)

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    # GeoParquet（GeoMetadata付き）
    gdf.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"[INFO] wrote: {OUTPUT_PARQUET}  (features={len(gdf):,})")

# ====== 実行 ======
if OUTPUT_FORMAT in ("geojson", "both"):
    write_geojson()
if OUTPUT_FORMAT in ("geoparquet", "both"):
    write_geoparquet()
