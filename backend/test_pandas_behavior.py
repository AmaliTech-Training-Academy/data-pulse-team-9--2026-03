from io import StringIO

import pandas as pd

csv_data = "col1,col2\nval1,val2\nval3,val4,bad\nval5,val6"
try:
    df = pd.read_csv(StringIO(csv_data), engine="python", on_bad_lines="skip", sep=",")
    print(df)
    print("row count:", len(df))
except Exception as e:
    print("Exception:", e)
