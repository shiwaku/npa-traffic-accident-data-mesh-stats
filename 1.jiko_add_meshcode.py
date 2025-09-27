#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
1.add_meshcode.py
- honhyo_2019-2024_convert.csv を読み込み、
  3～6次メッシュコード列（mesh_3, mesh_4, mesh_5, mesh_6）を追加して
  honhyo_2019-2024_convert_add_mesh.csv に一括書き出しします。
- 範囲外（経度が100≦lon<180でない、または緯度が-90～90でない）は
  メッシュコードに 9999 を代入します。
- 依存: pandas, numpy, jismesh (pip install pandas numpy jismesh)
"""

import os
import sys
from typing import Tuple

import numpy as np
import pandas as pd
import jismesh.utils as ju

INPUT_CANDIDATES = ["honhyo_2019-2024_convert.csv"]
OUTPUT_PATH = "honhyo_2019-2024_convert_add_mesh.csv"

LAT_CANDIDATES = ["地点_緯度（北緯）_10進数","緯度","lat","Latitude","LAT"]
LON_CANDIDATES = ["地点_経度（東経）_10進数","経度","lon","Longitude","LON"]

OUT_COLS = {3: "mesh_3", 4: "mesh_4", 5: "mesh_5", 6: "mesh_6"}

def find_input_file() -> str:
    for p in INPUT_CANDIDATES:
        if os.path.exists(p):
            return p
    sys.exit("[ERROR] csv が見つかりません。")

def sniff_latlon_columns(df: pd.DataFrame) -> Tuple[str,str]:
    def pick(cands):
        for c in cands:
            if c in df.columns:
                return c
        return None
    lat_col = pick(LAT_CANDIDATES)
    lon_col = pick(LON_CANDIDATES)
    if lat_col is None or lon_col is None:
        lowered = {c.lower().strip(): c for c in df.columns}
        for k in ["緯度","latitude","lat"]:
            if lat_col is None and k in lowered:
                lat_col = lowered[k]; break
        for k in ["経度","longitude","lon"]:
            if lon_col is None and k in lowered:
                lon_col = lowered[k]; break
    if lat_col is None or lon_col is None:
        sys.exit("[ERROR] 緯度/経度の列が見つかりませんでした。")
    return lat_col, lon_col

def read_dataframe(path: str) -> pd.DataFrame:
    try:
        import pyarrow  # noqa
        return pd.read_csv(path, encoding="utf-8-sig", engine="pyarrow")
    except Exception:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)

def compute_mesh(df: pd.DataFrame, lat_col: str, lon_col: str, levels=(3,4,5,6)) -> pd.DataFrame:
    for lv in levels:
        df[OUT_COLS[lv]] = pd.Series(pd.NA, dtype="Int64", index=df.index)

    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")

    mask_num = lat.notna() & lon.notna()
    mask_bounds = (lat >= -90) & (lat <= 90) & (lon >= 100) & (lon < 180)
    valid = mask_num & mask_bounds
    invalid = mask_num & ~mask_bounds

    print(f"[INFO] 有効座標: {int(valid.sum()):,} / {len(df):,}")
    if invalid.any():
        print(f"[WARN] 範囲外座標: {int(invalid.sum()):,} → 9999 に設定")

    if valid.any():
        lat_v = np.round(lat[valid].to_numpy(float, copy=False), 12)
        lon_v = np.round(lon[valid].to_numpy(float, copy=False), 12)
        for lv in levels:
            codes = ju.to_meshcode(lat_v, lon_v, lv)
            df.loc[valid, OUT_COLS[lv]] = pd.Series(codes, index=df.index[valid], dtype="Int64")

    # 範囲外は9999で埋める
    for lv in levels:
        df.loc[invalid, OUT_COLS[lv]] = 9999

    return df

def main():
    in_path = find_input_file()
    print(f"[INFO] Reading: {in_path}")
    df = read_dataframe(in_path)
    lat_col, lon_col = sniff_latlon_columns(df)
    print(f"[INFO] Using columns -> lat:'{lat_col}', lon:'{lon_col}'")
    df = compute_mesh(df, lat_col, lon_col, levels=(3,4,5,6))
    print(f"[INFO] Writing: {OUTPUT_PATH}")
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print("[INFO] Done.")

if __name__ == "__main__":
    main()
