import pandas as pd
import sqlite3
import os, glob

def main():
    '''
        pandasライブラリを利用し取得した各種CSVデータファイルをデータベース化して
        SQL文によって合体結果の検索を行えるようにする
    '''
    csv_path = os.path.join(os.path.abspath(".")) #
    db_path = os.path.join(csv_path, "devilfusiondb.db")

    csv_datas = glob.glob(os.path.join(csv_path,"*.csv")) # ディレクトリ内のCSVデータを取得
    print(csv_path); print(db_path)
    print(csv_datas)
    for f in csv_datas:
        #print(f)
        filename = os.path.basename(f) # ファイル名だけを得る
        print(filename)
        dataframe = pd.read_csv(filename, dtype=object)
        filename = filename.rstrip(".csv") # 拡張子は削除
        print("f",filename)
        with sqlite3.connect(db_path) as conn:
            dataframe.to_sql(filename, con=conn)
        
    print("COMPLETED.")




if __name__ == "__main__":
    main()