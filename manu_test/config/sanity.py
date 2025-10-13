import manufacturers as manu

# if you change the CSV later, clear the cache and re-load
manu.load.cache_clear()

# load your CSV (relative to your current folder)
df = manu.load(r"C:\Users\kened\Downloads\OriginDetective\OriginDetective\config\manufacuturers.csv")
print(df.columns.tolist())
print(len(df), "rows")


print(df.head(3).to_dict(orient="records"))