
import itertools, collections, random
import os,glob
from pprint import pprint
import sqlite3


class DevilFusionSystem:
    devils = []       # リストにはDevilクラスのオブジェクトが格納される
    devils_set = set(devils)
    combinations = [] # 悪魔合体可能な組み合わせと合体方法を格納したリスト
    results_dict = dict() # 悪魔リストから合体生成が可能な悪魔のリスト
    dbpath = os.path.abspath(r"./devilfusiondb.db") # 悪魔データベースのパスの初期値

    def __init__(self): 
        '''一連のクラス変数を改めて初期化'''
        self.devils = []
        self.devils_set = set()
        self.combinations = []
        self.results_dict = dict()

    def set_devilparty(self,devilsparty):
        '''
            受け取った仲魔リストから合体可能な組み合わせのリストを生成し
            実際の悪魔合体処理の準備を済ませておく
        '''
        def reset_data():
            self.devils = []
            self.devils_set = set()
            self.combinations = []
            self.results_dict = dict()

        if self.devils: # 既に一度データが与えられている場合は初期化処理を行う
            reset_data()

        # 合体結果の重複判断のために悪魔名のリストを確保しておく
        self.devils_set = set(devilsparty)

        # 悪魔リストの各悪魔の文字列からDevilオブジェクトを生成
        self._get_devilobj(devilsparty) 

        # 悪魔リストから合体の組み合わせパターンを全列挙し、さらに各組合せの大まかな合体パターン情報を付加
        self._generate_combinations()
        return

    def _debugresult(self):
        '''
            合体結果から逆算して組み合わせ情報を得られるようにする
            実機のセーブデータと挙動を突き合わせて動作検証を行いたい場合に利用すること
        '''
        for name,devobj in self.results_dict.items():
            print(name,type(devobj))
            for ele in devobj.materials:
                print("  :",ele)
        return

    def _get_devilobj(self,devilsparty):
        '''
            Devilクラスを利用して対象の悪魔の一連の情報にアクセスできるオブジェクトを生成し
            クラス変数に格納して利用できるようにする
        '''
        for devil in devilsparty: 
            obj = Devil(devil)
            #print(obj,obj.info)
            if obj.info == None: # 正しく処理されてこなかった場合はオブジェクトを追加せずに次の処理に移る
                continue
            self.devils.append(obj)
        return

    def _collect_fusionmaterials(self,dev,*materials):
        '''
            可変長引数で受け取った組み合わせ情報を合体結果が共通するものごとに
            各悪魔のインスタンスリストに格納する
        '''
        if dev:   # 返ってきた値がNoneであるものは除く
            temp_list = [dev.info["名前"] for dev in materials]
            if dev not in self.results_dict: # 初めて登録する悪魔については、新規に悪魔オブジェクトを生成する
                # 悪魔名をキーとして、悪魔オブジェクトと対応付ける
                self.results_dict[dev] = Devil(dev)
                print(self.results_dict[dev],":",dev)

                # 辞書内の悪魔オブジェクトに今回の組み合わせ情報を追加
                self.results_dict[dev].collect_materials(temp_list)
            else:   # 既に一度登録済みの悪魔については、そのままその要素に組み合わせ情報だけ追加する
                self.results_dict[dev].collect_materials(temp_list)
    
    def _check_duplication(self,devil_a,devil_b,new_devil):
        '''
            合体結果となる悪魔が合体前の悪魔やそれ以外の仲魔と重複していないかをチェック
            重複状態の有無に応じて合体結果を変更する
        '''
        if new_devil == None: # 合体結果が存在しない場合はそのまま値を返して終了
            return None
            
        for idx in range(len(new_devil)):
            devil_axb = new_devil[idx]
            if devil_axb == devil_a.info["名前"] or devil_axb == devil_b.info["名前"]:
                # 合体結果が合体前の悪魔と同じ場合はスライムに上書き
                print("合体前の悪魔のいずれかと合体結果が同じです")
                new_devil[idx] = "スライム"
            elif devil_axb in self.devils_set:
                # 合体結果が既に仲魔となっている場合は合体をキャンセル
                print("既に同じ仲魔がいます: {}".format(devil_axb))
                new_devil[idx] = None
        return new_devil

    def _check_fusionpattern(self, devil_a, devil_b):
        '''
            ある悪魔と悪魔の組み合わせが合体可能な組み合わせかどうか、
            合体可能な組み合わせなら、大まかにどの種類の合体に対応するのかをデータベースにアクセスしてチェック
        '''
        def exceptional_fusion(a,b):
            # 例外合体となる組み合わせかどうかチェックしてbool値を返す
            
            devil_a = a.info["名前"]
            devil_b = b.info["名前"]
            output_table = []
            with sqlite3.connect(self.dbpath) as conn:
                cur = conn.cursor()
                # 犬・パスカルを用いたかどうかチェック
                if devil_a=="パスカル" or devil_b=="パスカル":
                    return True

                # ランダ×バロンの組み合わせかチェック
                sql = f'''SELECT "合体結果" FROM exceptional_fusion 
                WHERE ("悪魔A"="{devil_a}" AND "悪魔B"="{devil_b}") 
                OR ("悪魔A"="{devil_b}" AND "悪魔B"="{devil_a}")'''
                cur.execute(sql)
                output_table = cur.fetchall()
                #print(sql); print(devil_a, devil_b, cur.fetchall())
            return bool(output_table)

        def human_fusion(a,b):
            # 人間合体となる組み合わせかどうかチェックしてbool値を返す
            devil_a = a.info["種族"]
            devil_b = b.info["種族"]
            human = ["ガイアキョウ", "メシアキョウ"]

            # 二体のうちいずれか一方のみが人間(XOR)ならTrueを返す
            if (devil_a in human)^(devil_b in human):
                return True
            else:
                return False 

        def dark_fusion(a,b):
            # DARK合体となる組み合わせかどうかチェックしてbool値を返す

            devil_a = a.info["属性1"]
            devil_b = b.info["属性1"]
            
            # 各悪魔の属性(LAW, NEUTRAL, DARK)を調べ、いずれか・ないし両方がDARK属性ならTrueを返す
            if (devil_a == "DARK") or (devil_b == "DARK"): 
                return True
            else:
                return False
        
        def normal_fusion(checklist):
            # それまでにチェック済みの合体モードが存在しなければ通常合体だと分かる
            for key,value in checklist.items():
                if value == True:
                    return False
            return True

        def return_value(checklist):
            for k,v in checklist.items():
                if v == True:
                    return k
            return k

        checkdict = {"特殊合体":None, "人間合体":None, "DARK合体":None, "通常合体":None}

        checkdict["特殊合体"] = exceptional_fusion(devil_a,devil_b) # 特殊合体チェック
        checkdict["人間合体"] = human_fusion(devil_a,devil_b)       # 人間合体チェック
        checkdict["DARK合体"] = dark_fusion(devil_a,devil_b)        # DARK合体チェック
        checkdict["通常合体"] = normal_fusion(checkdict)            # 通常合体チェック
        
        #print(f'「{devil_a}」×「{devil_b}」'); print(checkdict)
        return return_value(checkdict)

    def _generate_combinations(self):
        '''
            仲魔リストから組み合わせリストを生成
            さらに大まかな合体パターンに関する情報を付与して探索処理に備える
        '''

        # 全ての組み合わせパターンを列挙
        all_combinations = list(itertools.combinations(self.devils,2))
        #view_basicinfo(all_combinations)

        for idx in range(len(all_combinations)):
            all_combinations[idx] = list(all_combinations[idx])
            a,b = all_combinations[idx]
            mode = self._check_fusionpattern(a,b)
            
            # 三列目を大まかな合体パターンに関する情報を追加で格納しておく
            all_combinations[idx].append(mode) 

        self.combinations = all_combinations
        return

    def search_results(self):
        '''生成した組み合わせ情報と合体様式情報をもとに実際に合体を行い、組み合わせと合体結果とを記録する'''

        # 合体結果の探索に必要な条件を満たしている場合探索を行う
        if len(self.combinations) <= 1:
            print("合体を行えるだけの仲魔が存在しないため、合体を行うことが出来ませんでした")
            return False

        # 組み合わせ要素を順番に取り出してそれぞれに合体処理を行い、結果を悪魔オブジェクト化して記録
        for combi in self.combinations:
            devil_a, devil_b, mode = combi
            multiflag = False
            print(devil_a,"×",devil_b,":",mode)
            if mode == "通常合体": 
                new_devil = self._normalfusion(devil_a,devil_b)
            elif mode == "DARK合体":
                new_devil1 = self._darkfusion(devil_a,devil_b)
                new_devil2 = self._darkfusion(devil_b,devil_a)
                new_devil = [new_devil1, new_devil2]
                new_patterns = [[devil_a,devil_b],[devil_b,devil_a]]
                multiflag = True
            elif mode == "人間合体":
                new_devil = self._humanfusion(devil_a,devil_b)
            else:        # 特殊合体
                new_devil = self._exceptionalfusion(devil_a,devil_b)
            print("結果:",new_devil,"\n----------------------")            

            # 合体結果の重複チェックを行い、変更が必要な場合は合体結果を変更
            if multiflag: # 複数パターン合体結果を試した場合
                new_devil = [self._check_duplication(devil_a,devil_b,new_devil1),
                             self._check_duplication(devil_b,devil_a,new_devil2)]
            else:
                new_devil = self._check_duplication(devil_a,devil_b,new_devil)

            # 合体結果と合体前の悪魔2体の組み合わせ情報を記録
            if multiflag:
                for idx in range(len(new_devil)):
                    devil_a,devil_b = new_patterns[idx]
                    self._collect_fusionmaterials(new_devil[idx],devil_a,devil_b)
            else:
                self._collect_fusionmaterials(new_devil,devil_a,devil_b)

        print("全ての合体結果の算出が完了しました")
        self._debugresult()
        return 

    def _exceptionalfusion(self,devil_a, devil_b):
        ''' 特殊合体を行う'''
        with sqlite3.connect(self.dbpath) as conn:
            cur = conn.cursor()

            # シヴァの生成合体かどうかチェック
            name_a = devil_a.info["名前"]
            name_b = devil_b.info["名前"]
            if name_a!="パスカル" and name_b!="パスカル":
                if name_a == "バロン":
                    name_a,name_b = name_b,name_a

                sql = f'''SELECT "合体結果" FROM exceptional_fusion 
                WHERE "悪魔A"="{name_a}" AND "悪魔B"="{name_b}";'''
                ret = cur.execute(sql).fetchone()
                if bool(ret):
                    answer = ret[0]
                    return answer
            
            # パスカルによる合体かどうかチェック
            if name_a != "パスカル":
                name_a,name_b = name_b,name_a
            
            if name_b == "ケルベロス":
                answer = "スライム"
            else:
                answer = "ケルベロス"

        return answer

    def _humanfusion(self,devil_a, devil_b):
        '''人間合体を行う'''
        mankind = ["メシア教徒", "ガイア教徒"]
        namelist = set([dev.info["名前"] for dev in self.devils]) # 仲魔の名前リストを取得

        if devil_a.info["種族(漢字)"] in mankind:
            human = devil_a
            devil = devil_b
        else:
            devil = devil_a
            human = devil_b
        print(devil,"×",human)
            
        race_a = devil_a.info["種族(漢字)"]
        race_b = devil_b.info["種族(漢字)"]
        name_a = devil_a.info["名前"]
        name_b = devil_b.info["名前"]
        exception = "スライム"
        answer = None

        if not(race_a in mankind and race_b in mankind) and (exception not in [name_a,name_b]): # いずれか一方のみが人間で、合体にスライムが含まれない場合のみ人間合体を行う
            rannum = random.randint(0,31)           # 合体結果選出に用いるランダムなレベル補正値
            base_lv = (devil.info["LV"]+rannum)//2  # 基準となるレベル値
            align = "LAW" if race_a == "メシア教徒" else "CHAOS" # 人間側の信仰に応じて属性を設定
            with sqlite3.connect(self.dbpath) as conn:
                cur = conn.cursor()

                # 人間合体における優先度リストを抜き出す
                sql_pre = '''SELECT "{}" FROM human_fusion'''.format(human.info["種族(漢字)"])
                preemption = cur.execute(sql_pre).fetchall()

                rev_lev = 0 # 対応するレベル基準値に対応する悪魔がいなかった場合に用いる補正値
                cnt = 0     # 補正値計算を行うためのカウンタ

                while(answer == None or answer in namelist): # 条件を十分に満たす合体結果を得られるまで悪魔の探索を繰り返す
                    # 対象となる基準レベル値ちょうどの悪魔から合体結果を抽出
                    sql_dev = '''SELECT "属性2", "種族(漢字)", "名前", "LV" FROM devilsdata
                    WHERE "属性2"="{}" AND "LV"="{}" AND NOT("種族(漢字)"="{}") ORDER BY "LV" ASC
                    '''.format(align,base_lv+rev_lev,human.info["種族(漢字)"])
                    expect = cur.execute(sql_dev).fetchall()

                    print("BASE_LV:",base_lv+rev_lev)
                    for dev in expect:
                        print(dev)
                        dev_race, dev_name = dev[1], dev[2]
                        for race in preemption:
                            if dev_race in race: # 優先度リストに載っている悪魔が見つかった時点で探索処理を終了
                                answer = dev_name

                    # 合体結果が得られなかった場合はレベル基準値の修正
                    if (cnt==0) or (cnt%4==1):
                        rev_lev += 1
                    elif cnt%4 == 3:
                        rev_lev -= 1
                    else:
                        rev_lev *= (-1)
                    
                    # 通常有り得ないが、全探索場合でも永久ループに陥らないようにしておく
                    if -99 <= rev_lev and rev_lev <= 99: # レベル基準値が適正な場合のみループを継続
                        continue
                    break

        else:   # 条件を満たさない場合は合体不可
            answer = None
        #print(answer)
        return answer 
    
    def _darkfusion(self,devil_a,devil_b):
        '''
            DARK合体 (通常DARK合体, スライム合体, DARK2身合体)を行う
        '''
        lv_a = devil_a.info["LV"]
        lv_b = devil_b.info["LV"]

        if not(devil_a.info["属性1"] == devil_b.info["属性1"]): # 通常のDARK合体 (非DARK悪魔×DARK悪魔)
            #print(devil_a.info["属性1"],devil_b.info["属性1"])

            # どちらがDARK悪魔でどちらが非DARK悪魔かをはっきりさせておく
            if devil_a.info["属性1"] == "DARK":
                dark = devil_a
                not_dark = devil_b
            else:
                not_dark = devil_a
                dark = devil_b

            base_lv = lv_a + lv_b
            answer = None
            #print(base_lv,":","3の倍数->",bool(base_lv%3==0),"","7の倍数->",bool(base_lv%7==0))

            if dark.info["名前"] == "スライム": # スライム合体
                answer = not_dark.info["名前"]
            elif (dark.info["LV"] < not_dark.info["LV"]) and ((lv_a+lv_b)%7 == 0): # 非DARK悪魔の種族ランクが1上昇する場合
                #print("非DARK悪魔の種族ランクが+1")
                # データベースを参照して非DARK悪魔の種族の悪魔群のうち、ランクが一つ上の悪魔を取り出す
                with sqlite3.connect(self.dbpath) as conn:
                    cur = conn.cursor()
                    sql = '''SELECT "種族(漢字)", "名前", "LV" FROM devilsdata
                    WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC'''.format(not_dark.info["種族(漢字)"])

                    expect = cur.execute(sql).fetchall()
                    answer = None
                    flag = False
                    for dev in expect: # 合体対象の非DARK悪魔の後に出てくる悪魔が合体結果となる
                        if flag: # 発見次第ループを終了
                            answer = dev[1]
                            break
                        if dev[1] == not_dark.info["名前"]: 
                            flag = True
                            
            elif (dark.info["LV"] >= not_dark.info["LV"]) and ((lv_a+lv_b)%3 == 0): # DARK悪魔の種族ランクが1上昇する場合
                #print("DARK悪魔の種族ランクが+1")
                # データベースを参照してDARK悪魔の種族の悪魔群のうち、ランクが一つ上の悪魔を取り出す
                with sqlite3.connect(self.dbpath) as conn:
                    cur = conn.cursor()
                    sql = '''SELECT "種族(漢字)", "名前", "LV" FROM devilsdata
                    WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC'''.format(dark.info["種族(漢字)"])

                    expect = cur.execute(sql).fetchall()
                    flag = False
                    for dev in expect: # 合体対象のDARK悪魔の後に出てくる悪魔が合体結果となる
                        if flag: # 発見次第ループを終了
                            answer = dev[1]
                            break

                        if dev[1] == dark.info["名前"]: 
                            flag = True
            else:                               # スライム合体
                answer = "スライム"

            return answer

        else:         # DARK2身合体 (DARK悪魔×DARK悪魔)
            race_a = devil_a.info["種族(漢字)"]
            race_b = devil_b.info["種族(漢字)"]
            answer = None
            if race_a != race_b: 
                if lv_a == lv_b: # 異なる種族2体で、レベル値が等しい時
                    # そのまま前者(devil_a)をベース悪魔とする
                    devil = devil_a   
                else:            # 異なる種族2体で、レベル値が異なる時
                    # よりレベルの低い方をベース悪魔とする
                    if lv_a < lv_b:
                        devil = devil_a
                    else:
                        devil = devil_b

                # 対象となる悪魔からランクを1下げた悪魔を取り出す
                with sqlite3.connect(self.dbpath) as conn:
                    cur = conn.cursor()
                    sql = '''SELECT "種族(漢字)", "名前", "LV" FROM devilsdata
                    WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC'''.format(devil_a.info["種族(漢字)"])
                    expect = cur.execute(sql).fetchall()

                    for dev in expect:
                        if dev[1] == devil.info["名前"]:
                            break
                        else:
                            answer = dev[1]
                    
                    if answer == None: # 最低ランクの悪魔のランクをさらに-1下げる場合、最高ランクの悪魔となる
                        answer = expect[-1][1]
                    #print(f"{devil_a}のランクを-1した")
            else:
                if race_a == "邪神":    # 邪神同士によるDARK悪魔同種族合体
                    base_devil = devil_a.info["名前"] if lv_a > lv_b else devil_b.info["名前"]
                    
                    with sqlite3.connect(self.dbpath) as conn:
                        race = "邪神"
                        cur = conn.cursor()
                        sql = f'''SELECT "種族(漢字)","名前", "LV" FROM devilsdata
                        WHERE "種族(漢字)"="{race}" ORDER BY "LV" ASC'''

                        expect = cur.execute(sql).fetchall()
                        answer = None
                        for dev in expect:
                            if base_devil in dev:
                                break
                            else:
                                answer = dev[1]
                else:                  # 邪神以外によるDARK悪魔同種族合体
                    correct = 2 # 合体結果算出に用いる補正値
                    base_lv = (lv_a+lv_b)//2 + correct
                    
                    with sqlite3.connect(self.dbpath) as conn:
                        cur = conn.cursor()

                        # DARK2身合体表から合体後の種族情報を得る
                        sql_race = '''SELECT "合体結果種族" FROM darkdevils_fusion
                        WHERE "合体対象種族"="{}"'''.format(race_a)
                        ret = cur.execute(sql_race).fetchone()
                        race_axb = ret[0]

                        if not(race_axb): # 同種族合体が不可能な場合はNoneを返す
                            answer = None
                            return answer

                        # 合体後の種族の悪魔群の情報をリストで得る
                        sql_axb = '''SELECT "種族(漢字)","名前", "LV" FROM devilsdata
                        WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC'''.format(race_axb)
                        expect = cur.execute(sql_axb).fetchall()

                        abs_lv = 99
                        for dev in expect: # ベースとなるレベル値との差が最も小さくなる悪魔を探す
                            #print(dev,abs_lv,base_lv)
                            lv = dev[2]
                            if abs_lv > abs(base_lv-lv):
                                abs_lv = abs(base_lv-lv)
                                answer = dev[1]
                            else: # レベル差の値が最小を更新できなくなった時点でループを終了
                                break
                    
                    print(answer)

        return answer
    
    def _normalfusion(self,devil_a, devil_b):
        '''
            一般的な属性の悪魔の組み合わせを対象とした合体
            通常合体・大種族合体・同種族(精霊生成)合体・精霊合体・精霊2身合体を行う
        '''

        def normal_fusion(deva,devb):
            # 通常合体を行う
            a = deva.info["種族(漢字)"]
            b = devb.info["種族(漢字)"]
            with sqlite3.connect(self.dbpath) as conn:
                cur = conn.cursor()

                # 合体によって発生する種族の情報を得る
                sql = '''SELECT "合体結果" FROM normal_fusion 
                WHERE "種族A"="{}" AND "種族B"="{}";'''.format(a,b)
                ret = cur.execute(sql).fetchone()
                axb = ret[0] 

                # 合体結果に関するレベル基準値を得る
                base_lv = (deva.info["LV"]+devb.info["LV"])//2 + 2
                
                #print(a,"×",b,"＝",axb,"LV:",level)
                
                # 合体結果となる種族の悪魔群をリストで得る
                sql_axb = '''SELECT "LV","名前" FROM devilsdata
                WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC;'''.format(axb)
                expect = cur.execute(sql_axb).fetchall() 
                answer = None

                # レベル基準値以上の悪魔で、レベル値が最も近い悪魔を取り出す
                for lv,name in expect:
                    #print(lv,name,":",base_lv)
                    if lv >= base_lv : # レベル基準値との差が小さいものを結果として記憶
                        answer = name
                        break

            return answer 
        
        def greater_fusion(deva,devb):
            # 大種族合体
            a = deva.info["種族(漢字)"]
            b = deva.info["種族(漢字)"]

            with sqlite3.connect(self.dbpath) as conn:
                cur = conn.cursor()
                
                # 大種族が同じ種族のリストを取得
                sql_samerace = '''SELECT "種族" FROM racesdata
                WHERE "大種族" IN (SELECT "大種族" FROM racesdata WHERE "種族"="{}");'''.format(a)
                ret_grace = cur.execute(sql_samerace).fetchall()
                ret_grace = ["\"" + ret_grace[i][0] + "\"" for i in range(len(ret_grace))]
                grace = "("+",".join(ret_grace)+")" # IN句による抽出を行うための文字列整形

                # 大種族別に抜き出す
                print(a,ret_grace)
                sql = '''SELECT "LV", "名前","種族(漢字)" FROM devilsdata
                WHERE "種族(漢字)" IN {}
                ORDER BY "LV" ASC;'''.format(grace)
                expect = cur.execute(sql).fetchall()                   
                
                # 合体結果に関するレベル基準値を得る
                level = (deva.info["LV"]+devb.info["LV"])//2 + 3
                answer = expect[0][1]
                abs_lv = 99

                for lv,name,race in expect:
                    #print(lv,name,":", abs_lv, answer)
                    if abs_lv > abs(level-lv):
                        answer = name
                        abs_lv = abs(level-lv)
                
                # 合体後の悪魔の種族と合体前の悪魔2体とで種族が重複している場合は合体不可(None)とする
                if Devil(answer).info["種族(漢字)"] in [a,b]:
                    answer = None

            return answer

        def sameraces_fusion(deva,devb):
            # 同種族合体を行う
            race = deva.info["種族(漢字)"]
            with sqlite3.connect(self.dbpath) as conn:
                cur = conn.cursor()
                
                # 同種族合体表から対象の種族同士を合体した場合の合体結果を得る
                sql = '''SELECT "合体結果" FROM sameraces_fusion 
                WHERE "種族"="{}";'''.format(race)

                ret = cur.execute(sql).fetchone()
                print(deva,devb,ret)

                answer = ret[0] # 同種族合体不可能な種族の場合はNoneが与えられる

            return answer

        def spirit_fusion(deva,devb):
            # 精霊合体を行う
            if deva.info["種族(漢字)"] == "精霊": 
                spi = deva.info["名前"]
                dev = devb.info["種族(漢字)"]
                name = devb.info["名前"]
            else:
                dev = deva.info["種族(漢字)"]
                name = deva.info["名前"]
                spi = devb.info["名前"]

            with sqlite3.connect(self.dbpath) as conn:
                cur = conn.cursor()

                # 精霊合体表からランク変動値を得る
                sql_val = '''SELECT "ランク変動値" FROM spirit_fusion 
                WHERE "種族"="{}" AND "精霊"="{}"'''.format(dev,spi)
                val = cur.execute(sql_val).fetchone()
                
                if val == None: # 何も戻ってこない場合は合体不可
                    answer = None
                    return answer 

                # 合体結果となる種族をレベル昇順でソートされたリストとして得る
                val = val[0] # 値はint型で返されるのでそのまま取り扱い可能
                sql_dev = '''SELECT "LV","名前" FROM devilsdata
                WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC; 
                '''.format(dev)
                expect = cur.execute(sql_dev).fetchall()

                for rank in range(len(expect)):
                    #print(rank,expect[rank],name)
                    if expect[rank][1] == name: # 合体元の悪魔を見つけたら、ランク変動値を加えて合体後ランクを得る
                        rank += val
                        if rank >= len(expect): # ランクが最大を超える場合は最低ランクの悪魔になる
                            answer = expect[0][1]
                        elif rank < 0:          # ランクが最低を下回る場合は最大ランクの悪魔になる
                            answer = expect[-1][1]
                        else:                   # 範囲外参照がなければ、そのまま変動後のランクの悪魔が合体結果
                            answer = expect[rank][1]
                        break
                return answer
        
        def spirits_fusion(deva,devb):
            # 精霊2身合体を行う
            a = deva.info["名前"]
            b = devb.info["名前"]
            with sqlite3.connect(self.dbpath) as conn:
                cur = conn.cursor()

                sql = '''SELECT "合体結果" FROM spirits_fusion
                WHERE "精霊A"="{}" AND "精霊B"="{}";'''.format(a,b)
                ret = cur.execute(sql).fetchone()
                print(ret)
                answer = ret[0]
            return answer

        def detect_type(deva,devb):
            # 通常合体カテゴリのうちどの合体を行うか確認

            race_a = deva.info["種族(漢字)"]
            race_b = devb.info["種族(漢字)"] 

            if race_a == "精霊" or race_b == "精霊": 
                if race_a == "精霊" and race_b == "精霊": # 精霊2身合体
                    return "精霊2身合体"
                else:                                     # 精霊合体
                    return "精霊合体"
            elif race_a == race_b:                        # 同種族合体
                return "同種族合体"
            else:
                a = deva.info["種族"]
                b = devb.info["種族"]
                with sqlite3.connect(self.dbpath) as conn:
                    cur = conn.cursor()
                    
                    # カナ表記の種族名から大種族名を得るためのSQL文
                    base_sql = '''SELECT "大種族" 
                    from (SELECT * FROM racesdata INNER JOIN race_spelling ON racesdata."種族"=race_spelling."種族(漢字)")
                    where "種族(カナ)"="{}";'''
                    sql_a = base_sql.format(a)
                    sql_b = base_sql.format(b)
                    ga = cur.execute(sql_a).fetchone()
                    gb = cur.execute(sql_b).fetchone()
                if ga == gb:
                    return "大種族合体"
                else:
                    return "通常合体"


        combi_type = detect_type(devil_a,devil_b)
        devil_axb = None # 初期化
        #print("---------------\n",devil_a,"×",devil_b,":",combi_type)

        if   combi_type == "通常合体":
            devil_axb = normal_fusion(devil_a, devil_b)
        elif combi_type == "大種族合体":
            devil_axb = greater_fusion(devil_a, devil_b)
        elif combi_type == "同種族合体":
            devil_axb = sameraces_fusion(devil_a,devil_b)
        elif combi_type == "精霊合体":
            devil_axb = spirit_fusion(devil_a, devil_b)
        else:             # 精霊2身合体
            devil_axb = spirits_fusion(devil_a, devil_b)
        #print("\n\n\n",devil_a,"\n",devil_b); print(combi_type); print(devil_axb)

        return devil_axb


class DevilFusionSystemBy3(DevilFusionSystem):
    '''
        3身合体を行うためのクラス
        一部の合体において2身合体システムを用いるため、2身合体システムを備えたクラスを継承し、
        3身合体システム内で別途記述することなく2身合体を利用できるようにしている
        また、オーバーライドを利用して一部の親クラスのメソッドを独自に再定義してある     
    '''
    def __init__(self):
        return
        
    def _access_database(self, sql):
        '''
            悪魔合体データベースへのアクセスを行う
            データベースへのアクセス処理は概ねどれも同じなので、個別に記述せずに同一のメソッドを経由してデータを参照する
        '''
        with sqlite3.connect(self.dbpath) as conn:
            cur = conn.cursor()
            #print(sql)
            ret = cur.execute(sql).fetchall()
        return ret

    def _check_3dfusionpattern(self, devil_a, devil_b, devil_c):
        def chk_unfusionability(a,b,c) -> bool:
            # 3身合体不能な特殊悪魔が含まれていないかチェックする
            unfusionables = ["ウリエル", "ラファエル", "ガブリエル", "シヴァ", "ヴィシュヌ"]
            for dev in [a,b,c]:
                dark = dev.info["名前"]
                if dark in unfusionables:
                    return True
            return False
        
        def chk_exceptional_fusion(a,b,c) -> bool:
            # 屍鬼コープスの生成パターンかどうかチェックする
            race_a = a.info["種族(漢字)"]; deva = a.info["名前"]
            race_b = b.info["種族(漢字)"]; devb = b.info["名前"]
            race_c = c.info["種族(漢字)"]; devc = c.info["名前"]
            races = {race_a, race_b, race_c}
            names = {deva, devb, devc}

            if ("屍鬼" in races) and ("コープス" not in names) and (len(races) == 1):
                return True
            
            # セラフ・ウリエルの生成パターンかどうかチェックする
            base_sql = '''SELECT "合体結果" FROM exceptional_3dfusion
            WHERE "悪魔A"="{}" AND "悪魔B"="{}" AND "悪魔C"="{}"'''
            
            # 無意味なループやデータベースアクセスは避けたいので、合体悪魔が全て天使である場合以外は先にFalseを返す
            if (len(races) > 1) or ("天使" not in races):
                return False
            
            # 合体悪魔が全て天使であるような場合はデータベースの参照を行う
            perms = list(itertools.permutations(list(names)))   # 並びが複数有り得るので、順列を生成してすべて試す
            for perm in perms:
                x,y,z = perm
                sql = base_sql.format(x,y,z)
                ret_table = self._access_database(sql)
                if ret_table: 
                    return True
            
            # Trueとなる参照結果が得られなかった場合はFalseを返す
            return False

        def chk_greater_fusion(a,b,c) -> bool:
            # レベルの低い悪魔2体の大種族が同じかどうか判定
            race_a = a.info["種族(漢字)"]
            race_b = b.info["種族(漢字)"]  

            # 大種族表を参照して、悪魔B,悪魔Cの大種族が同一であるかチェックする
            sql = '''SELECT "大種族" FROM racesdata WHERE "種族"="{}"'''
            sql_a = sql.format(race_a)
            sql_b = sql.format(race_b)

            # メソッドを経由してデータベースにアクセスし、抽出リストを得る
            ret_a = self._access_database(sql_a); ret_a = ret_a[0]
            ret_b = self._access_database(sql_b); ret_b = ret_b[0]
            if ret_a == ret_b:
                return True
            else:
                return False
        
        def chk_slime_fusion(a,b,c) -> bool:
            races = [a.info["種族(漢字)"], b.info["種族(漢字)"], c.info["種族(漢字)"]]
            graces = set()

            if "犬" in races:   # 犬・パスカルの場合もスライム合体とする
                return True

            # 各悪魔の大種族情報を得る
            for race in races:
                sql = '''SELECT "大種族" FROM racesdata WHERE "種族"="{}"'''.format(race)
                grace = self._access_database(sql); grace = grace[0][0]
                graces.add(grace)

            # 大種族が｛邪霊、外道、人｝のいずれかである悪魔が含まれている場合スライム合体と判定
            slimeset = {"邪霊", "外道", "人"}
            if graces & slimeset:
                return True
            return False
        
        def chk_dark_fusion(a,b,c) -> bool:
            # 3体のうちにDARK悪魔が含まれかどうかで判定を行う
            race_a = a.info["属性1"]
            race_b = b.info["属性1"]
            race_c = c.info["属性1"]
            attributes = [race_a, race_b, race_c]
            if "DARK" in attributes:
                return True
            else:
                return False
        
        if chk_unfusionability(devil_a,devil_b,devil_c):
            return "合体不可"
        elif chk_exceptional_fusion(devil_a,devil_b,devil_c):
            return "特殊合体"
        elif chk_greater_fusion(devil_a,devil_b,devil_c):
            return "大種族合体"
        elif chk_slime_fusion(devil_a,devil_b,devil_c):
            return "スライム合体"
        elif chk_dark_fusion(devil_a,devil_b,devil_c):
            return "DARK合体"
        else:       # いずれにも該当しなければ通常合体と判定できる
            return "通常合体"

    def __sort_devils(self,x,y,z):
        '''
            合体候補となる組み合わせをレベル順に並び替えて3身合体処理に備える
        '''
        devilobjs = [x,y,z]
        devillvs = sorted([x.info["LV"],y.info["LV"],z.info["LV"]]) # レベル降順にソート
        devilset = set() # 整列済みリストを生成するためのインデックス管理セット
        sorted_devil = [-1,-1,-1] # ひとまず整数値で初期化

        # レベル順にソートした悪魔オブジェクトのリストを作成
        for i in range(len(devilobjs)):
            for j in range(len(devillvs)): 
                #print(devilobjs[i].info["LV"],devillvs[j],devilset)
                if devilobjs[i].info["LV"] == devillvs[j] and (j not in devilset):
                    sorted_devil[j] = devilobjs[i]
                    #print(j,devilobjs[i])
                    devilset.add(j)
                    break
        #print(sorted_devil)
        
        # 最もレベルが高い悪魔が2体いる場合もあるので、その場合は可能な限り通常合体が行える形に直す
        '''具体的にこの場合の仕様がどのようになっているのか不明だが、
        2身+2身合体ベースの算出とすると、実際の結果と食い違う場合があるのでこのようにしておく'''
        if sorted_devil[1].info["LV"] == sorted_devil[2].info["LV"]:
            devilgrs = []
            sql = '''SELECT "大種族" FROM racesdata WHERE "種族"="{}"'''
            for i in range(len(sorted_devil)):
                grace = self._access_database(sql.format(sorted_devil[i].info["種族(漢字)"])); grace = grace[0][0]
                devilgrs.append(grace)

            if devilgrs[0] == devilgrs[1]:
                sorted_devil[1],sorted_devil[2] = sorted_devil[2],sorted_devil[1]

        return sorted_devil  

    def _generate_combinations(self):
        # 全ての組み合わせパターンを列挙
        all_combinations = list(itertools.combinations(self.devils,3))
        
        for idx in range(len(all_combinations)):
            # 組み合わせで得られた悪魔をレベル順に並び替え
            a,b,c = all_combinations[idx]
            a,b,c = self.__sort_devils(a,b,c)
            all_combinations[idx] = a,b,c
            all_combinations[idx] = list(all_combinations[idx])
            mode = self._check_3dfusionpattern(a,b,c)
            #print(a,"×",b,"×",c,":",mode)

            # 三列目を大まかな合体パターンに関する情報を追加で格納しておく
            all_combinations[idx].append(mode) 

        self.combinations = all_combinations
        return
    
    def search_results(self):
        ''' 組み合わせリストを用いて有り得る3身合体結果を全て求める '''
        def __debugprint(axbxc,mode,a,b,c) -> None:
            print("-"*64)
            print("{}: {}×{}×{}".format(mode,a,b,c))
            print("合体結果: {}".format(axbxc))
            #print("-"*64)

        if len(self.devils) <= 2: # 合体生成に必要な最低仲魔数よりも仲魔が少ない場合
            return False
        
        for combi in self.combinations:
            devil_a,devil_b,devil_c,mode = combi

            if mode == "特殊合体":
                devilAxBxC = self._exceptional3dfusion(devil_a,devil_b,devil_c)
            elif mode == "通常合体":
                devilAxBxC = self._normal3dfusion(devil_a,devil_b,devil_c)
            elif mode == "大種族合体":
                devilAxBxC = self._greater3dfusion(devil_a,devil_b,devil_c)
            elif mode == "スライム合体":
                devilAxBxC = self._slime3fusion(devil_a,devil_b,devil_c)
            elif mode == "DARK合体":
                devilAxBxC = self._dark3dfusion(devil_a,devil_b,devil_c)
            else:        # 合体不可
                devilAxBxC = None
            
            devilAxBxC = self._check_3dduplication(devil_a,devil_b,devil_c,devilAxBxC)

            __debugprint(devilAxBxC,mode,devil_a,devil_b,devil_c)
            self._collect_fusionmaterials(devilAxBxC,devil_a,devil_b,devil_c)
        
        self._debugresult()
        return True

    def _check_3dduplication(self,a,b,c,axbxc):
        '''合体結果として導かれた悪魔が既に存在している場合、外道スライムに合体結果が変更となる'''
        a = a.info["名前"]
        b = b.info["名前"]
        c = c.info["名前"]
        if axbxc in [a,b,c]:
            print(a,b,c,axbxc,":","これはまずい")
            return "スライム"
        else:
            return axbxc # 問題がなければそのまま返す

    def _normal3dfusion(self,deva,devb,devc,rev_val=0):
        '''
            通常の3身合体プロセスによって合体結果を求める
            ただし、合体結果が『？』となった場合は、別途ランダム合体用の処理を追加
        '''
        def random_fusion() -> str:
            # 属性1がNEUTRALの悪魔群からランダムに一体を選ぶ
            '''処理回数が多いと感じた場合には、別途NEUTRAL悪魔だけ抜き出したビューを作成して、それを参照にした方がよいかもしれない'''
            sql_rand = '''SELECT "名前" FROM devilsdata WHERE "属性1"="NEUTRAL"'''
            expect = self._access_database(sql_rand)
            randidx = random.randint(0,len(expect)-1) # 得られるデータ数の範囲内でランダムにインデックスを取得
            return expect[randidx][0]

        def normal3dfusion_a() -> str: # 3身合体表Aを参照して結果を得る
            ## レベルのより低い2体(悪魔Aと悪罵B)の大種族情報を取りだす
            race_a = deva.info["種族(漢字)"]
            race_b = devb.info["種族(漢字)"]
            sql_grace = '''SELECT "大種族" FROM racesdata WHERE "種族"="{}"'''

            grace_a = self._access_database(sql_grace.format(race_a)); grace_a = grace_a[0][0]
            grace_b = self._access_database(sql_grace.format(race_b)); grace_b = grace_b[0][0]

            ## 取り出した大種族情報を用いて3身合体表Aの結果を得る
            sql_3da = '''SELECT "合体結果" FROM normal_3dfusionA
            WHERE "大種族A"="{}" AND "大種族B"="{}"'''.format(grace_a, grace_b)
            ret_axb = self._access_database(sql_3da); ret_axb = ret_axb[0][0]
            
            return ret_axb
        
        def normal3dfusion_b() -> str: # 3身合体表Bを用いて合体結果を得る
            # 悪魔Cの大種族情報を得る
            race_c = devc.info["種族(漢字)"]
            sql_grace = '''SELECT "大種族" FROM racesdata WHERE "種族"="{}"'''.format(race_c)
            grace_c = self._access_database(sql_grace); grace_c = grace_c[0][0]

            # 3身合体表Aの結果と悪魔Cの大種族情報を用いて3身合体表Bから合体結果種族を求める
            sql_axbxc = '''SELECT "合体結果" FROM normal_3dfusionB
            WHERE "大種族"="{}" AND "グループ"="{}"'''.format(grace_c, axb)

            ret_axbxc = self._access_database(sql_axbxc); ret_axbxc = ret_axbxc[0][0]
            return ret_axbxc
        
        answer = None

        # 最終的な合体結果の導出に必要なレベル基準値を求める
        correction = 8 # 基準レベル値算出に用いる補正値
        base_lv = (deva.info["LV"]+devb.info["LV"]+devc.info["LV"])//3 + correction + rev_val
        
        # 3身合体表Aから合体結果を得る
        axb = normal3dfusion_a()

        # 3身合体表Aの結果と3体目の悪魔の大種族情報を用いて合体結果を得る
        axbxc = normal3dfusion_b()

        # 合体結果がランダム合体(「?」)となった場合は別途処理を行い、それを最終結果とする
        if axbxc == "?":
            return random_fusion()
        
        # ランダム合体でない場合は、得られた種族情報とレベル基準値から最終結果を求める
        sql_race = '''SELECT "LV","名前","種族(漢字)" FROM devilsdata
        WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC'''.format(axbxc)
        expect = sorted(self._access_database(sql_race))
        for lv,devil,race in expect:
            #print(base_lv,":",lv,devil,race)
            if base_lv <= lv: # レベル基準値を超える悪魔を合体結果とする
                answer = devil
                break
        if not(answer):
            # 基準値以上の悪魔が見つからなかった場合は同種族中の最上位悪魔が合体結果となる
            answer = expect[-1][1]
        #print(axb,"×",axbxc,"=",answer)
        return answer       
        
    def _greater3dfusion(self,deva,devb,devc):

        # まずレベルの低い悪魔2体に大種族合体を施す
        mode = self._check_fusionpattern(deva,devb)
        if mode == "DARK合体":
            dev_axb = self._darkfusion(deva,devb)
        else:
            dev_axb = self._normalfusion(deva,devb)

        # 2身合体不可の組み合わせだった場合はそのまま合体不可(None)として終了
        if not(dev_axb): 
            return None

        # 2身合体(親クラス)のメソッドを用い重複をチェック、合体結果を悪魔オブジェクト化
        dev_axb = self._check_duplication(deva,devb,dev_axb)

        # 重複検証の結果合体不可と判定された場合はやはりNoneを返す
        if not(dev_axb):
            return None
        
        # 2身合体(親クラス)のメソッドを用いて残りの2体の合体方式を確認
        dev_axb = Devil(dev_axb)
        mode = self._check_fusionpattern(dev_axb,devc)
        
        # 更に悪魔AxBと悪魔Cの合体を行う
        if mode == "通常合体":
            new_devil = self._normalfusion(dev_axb, devc)
        elif mode == "大種族合体":
            new_devil = self._normalfusion(dev_axb, devc)
        elif mode == "DARK合体":
            new_devil = self._darkfusion(dev_axb,devc)
        else:
            pass

        # 最後に出来上がった悪魔を1ランクアップさせる
        new_devil = Devil(new_devil) # 種族情報の参照のため再度悪魔オブジェクト化

        sql = '''SELECT "LV","名前","種族(漢字)" FROM devilsdata 
            WHERE "種族(漢字)"="{}" ORDER BY "LV" ASC'''.format(new_devil.info["種族(漢字)"])
        expect = self._access_database(sql)
        answer = None
        for lv,devil,race in expect:
            #print(new_devil.info["LV"], answer)
            if new_devil.info["LV"] < lv: # 該当する悪魔が見つかり次第ループ脱出
                answer = devil
                break
        else:                             # そのままループを終えた場合は最下位悪魔が合体結果となる
            '''
                検証したところだと、最高ランクの悪魔が最初の合体（A×B)の時点で出来上がっている場合、
                最低ランクの悪魔にはならず、合体そのものが行われない(Noneとなる)ようになっているらしい
                A×Bの2身合体だけで事が済むのだからわざわざ損をすることがないように、ということかもしれない
                実際の動作が確かにこうなっているため、これも仕様として盛り込んでおく
            '''
            if expect[-1][1] == dev_axb.info["名前"]:
                answer = None
            else:
                answer = expect[0][1]
        return answer
    
    def _slime3fusion(self,devil_a, devil_b, devil_c):
        '''
            合体結果がスライムとなる3身合体
            合体パターン判別メソッドを通した時点で合体結果は分かっているのでそのまま即座に結果を返す
        '''
        return "スライム"

    def _dark3dfusion(self,devil_a,devil_b,devil_c):
        '''
            DARK悪魔を含む3身合体。レベル基準値の三種値に別途修正値を与える以外は通常の3身合体と同じなので
            組み合わせに含まれるDARK悪魔の数 * (-4) だけの修正値を追加で用意したあと、そのまま通常合体に渡す
        '''
        devils = [devil_a,devil_b,devil_c]
        revise_value = 0
        for i in range(len(devils)):
            if devils[i].info["属性1"] == "DARK":
                revise_value += (-4)
        print("DARK合体につきレベル基準値を次の分だけ修正:",revise_value)
        return self._normal3dfusion(devil_a,devil_b,devil_c,rev_val=revise_value)
    
    def _exceptional3dfusion(self, devil_a, devil_b, devil_c):
        abc_pattern = list(itertools.permutations([devil_a,devil_b,devil_c],3))
        answer = None

        for combi in abc_pattern:
            a,b,c = combi
            sql = '''SELECT "合体結果" FROM exceptional_3dfusion
            WHERE "悪魔A"="{}" AND "悪魔B"="{}" AND "悪魔C"="{}"
            '''.format(a.info["名前"],b.info["名前"],c.info["名前"])
            ret = self._access_database(sql)

            if ret:
                print(a,b,c,":",ret)
                answer = ret[0][0]
        print(answer)
        return answer

class Devil:
    '''
        データベースにアクセスして対象悪魔に関する一連の情報を取得
        辞書型で格納して楽に取り扱えるようにしておく
    '''
    info = dict()
    filepath = os.path.abspath(r"./devilparty.txt")
    dbpath = os.path.abspath(r"./devilfusiondb.db")
    materials = list()

    def __init__(self,devil):
        '''
            リストなどのクラス変数は別途コンストラクタ等のメソッドで初期化しないと
            同じクラスから生成された別のインスタンスからの処理を行った際にその処理結果が共有されてしまう
            コンストラクタなどを用いて必ず別途初期化処理をすること
        '''
        self.info = dict()
        self.materials = list() 

        # データベースの悪魔データテーブルから情報を取得
        conn = sqlite3.connect(os.path.abspath(self.dbpath))
        cur = conn.cursor()
        sql = 'SELECT * FROM devilsdata WHERE "名前" = "{}"'.format(devil)

        outcome = cur.execute(sql)
        record = outcome.fetchone() # 対象のレコードの情報をタプルで得る
        colnames = list(map(lambda row: row[0], cur.description)) # データベースの列名を得る
        #print(devil,colnames,record)

        if record == None: # データベースに悪魔が存在しなかった場合は何もせずに処理を終える
            self.info = None
            return

        for i in range(len(colnames)): # 辞書型でクラス変数に格納
            col = colnames[i]
            rec = record[i]
            #print(col, rec)
            self.info[col] = rec
        
        #print(self.info)
        conn.close()

    def collect_materials(self,devils):
        self.materials.append(devils)
        return 

    def __repr__(self) -> str: 
        # print出力である程度中身が分かるようにしておく
        if self.info == None:
            return f'存在しない悪魔'
        else:
            return f'{self.info["種族(漢字)"]} {self.info["名前"]}'

class DevilParty:
    '''
        仲魔にした悪魔の情報を適切な様式で格納、保管し、
        悪魔合体で利用できるようにするためのクラス
    '''
    devils_list = []
    filepath = os.path.abspath(r"./devilparty.txt")
    dbpath = os.path.abspath(r"./devilfusiondb.db")

    def __init__(self,file="",database=""): 
        '''
            パスからファイルを参照してパーティ情報を得る
            カレントディレクトリがプログラムファイルのあるパスなら引数なしでも機能するように
            事前に初期値も設定してある
        '''
        # 引数が存在するならクラス変数の値を変更
        if file:
            self.filepath = file
        if database:
            self.dbpath = database
        self.set_devilsdata()
    
    def set_devilsdata(self,):
        # 仲魔データの存在チェック
        if not(os.path.exists(self.filepath)):
            print("THE FILE YOU ASSINGNED IS NOT FOUND...")
            return None
        
        self.devils_list = []
        # 仲魔リストの生成
        with open(self.filepath, 'r', encoding='UTF-8') as f:
            for d in f:
                d = d.strip('\n')
                self.devils_list.append(d)
        
        # 悪魔データベースの存在チェック
        if not(os.path.exists(self.dbpath)):
            print("THE DATABASE FILEPATH MAY NOT BE EXIST....")
            return None

        self.inspect_party() # 仲魔リストの整合性を確保
        print(self.devils_list)
    
    def inspect_party(self):
        '''
            同じ悪魔が複数存在したり、存在しない悪魔が格納されていないか検査する
        '''

        # 重複チェック
        temp_list = set()
        for devil in self.devils_list:
            if devil in temp_list:
                self.devils_list.remove(devil) # 重複する悪魔は削除し一つだけ残す
            else:
                temp_list.add(devil)
        
        # 存在チェック, 利用後は速やかにclose()すること
        conn = sqlite3.connect(self.dbpath)
        cur = conn.cursor()

        for devil in self.devils_list:
            sql = '''SELECT * FROM devilsdata WHERE "名前" = "{}"'''.format(devil)
            outcome = cur.execute(sql)
            #print(devil)
            if not(outcome): #存在しなかった場合はリストから取り除く
                self.devils_list.remove(devil)
            
        conn.close()


def main():
    def exe_dfs3():
        dp = DevilParty()
        dfs3 = DevilFusionSystemBy3()
        dp.set_devilsdata()
        dfs3.set_devilparty(dp.devils_list)
        dfs3.search_results()
        return
    def exe_dfs2():
        dp = DevilParty()
        dfs2 = DevilFusionSystem()
        dp.set_devilsdata()
        dfs2.set_devilparty(dp.devils_list)
        dfs2.search_results()
    if input("3身合体を行う場合は[1]を、2身合体はそれ以外の値を入力してください: ")=="1":
        exe_dfs3()
    else:
        exe_dfs2()
    return

if __name__ == "__main__":
    main()