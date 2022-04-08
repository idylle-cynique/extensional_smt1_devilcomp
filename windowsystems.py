
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import os, subprocess


import devilsfusionsystem as dfs

class DevilResult:
    '''
        合体の組み合わせ結果を表示するためのシステム
        合体結果を表示するウィンドウ・合体結果悪魔の生成に必要な組み合わせ情報をそれぞれのウィンドウから表示する
    '''
    settingLength = 6
    buttonNumber = 0
    gridleft = 0
    gridright = 6
    pushButtons = []
    parent = None
    is_exists = False # 生成されたインスタンスにおいてself.rootが生成されたかどうかをチェック
    result_dict = dict()
    mode = int()      # 2身合体か3身合体か数値で記録
    devilmaterials = list()
    
    def __init__(self,parent=None) -> None:
        self.parent = parent
    
    def gen_widgets(self,num) -> None:
        '''悪魔の数に応じてボタンを動的に生成'''
        if self.is_exists:
            if self.root.winfo_exists(): # 既に一度ウィンドウを生成している場合はまず消去してから処理を行う
                self.del_widgets()
        else:
            self.root = tk.Toplevel(master=self.parent)
            self.root.title("")
            self.frame = ttk.Frame(self.root)
            self.frame.grid()
            self.is_exists = True
            
            # 下部画面の情報
            self.bottoms = MaterialResult(parent=self.root)

        '''左右カーソル用のボタンを生成'''
        self.left = ttk.Button(self.frame, text="<", command=lambda:self.replace_buttons("<"))
        self.right = ttk.Button(self.frame, text=">", command=lambda:self.replace_buttons(">"))
        # 事前に生成済みの左右カーソルボタンを配置
        self.left.grid(row=0,column=0, sticky=tk.N+tk.S)
        self.right.grid(row=0,column=min(self.settingLength,num)+1, sticky=tk.N+tk.S)

        # ボタンの生成・配置
        for i in range(num):                                              # ボタンの生成
            button = ttk.Button(self.frame, text="\n".join(self.devilbuttons[i]),padding=(10,10,10,10),)
            button.bind("<Button-1>",self.gen_materialtable)
            self.pushButtons.append(button)

        for i in range(min(self.settingLength,len(self.pushButtons))):    # ボタンの配置(既定の個数を超える場合は既定個数までのみ表示)
            self.pushButtons[i].grid(row=0, column=i+1)

        # 最左ボタンのインデックス、最右ボタンのインデックスを書き換え
        self.gridleft = 0
        self.gridright = min(self.settingLength, len(self.pushButtons))

        # 生成されたボタン個数を記録
        self.buttonNumber = len(self.pushButtons)

    def get_buttonnames(self) -> None:
        '''ボタンやテーブルに表示するための情報を得る'''
        self.devilnames = []
        self.devilbuttons = []
        self.devilmaterials = []
        for key, val in self.result_dict.items():
            devil = dfs.Devil(key)
            button_string = ["Lv:"+str(devil.info["LV"]),devil.info["名前"],devil.info["種族(漢字)"]]
            self.devilbuttons.append(button_string)
            self.devilnames.append(key)
        return

    def del_widgets(self) -> None:
        '''画面を再構成するために全てのウィジェットを取り除く'''
        for button in self.pushButtons:
            button.grid_forget()
        self.left.grid_forget()
        self.right.grid_forget()
        self.pushButtons = []
        return 
    
    def replace_buttons(self,command) -> None:
        '''カーソルボタンの入力に応じてボタンを再配置する'''
        # まず取り除くボタンの情報と新しく配置するボタンの情報を得る
        preleft, preright = self.gridleft, self.gridright
        if command == "<":
            if self.gridleft == 0:                  # 既に一番左まで来ている場合は何もしない
                return 
            self.gridleft = max(0, self.gridleft-self.settingLength)
            self.gridright = max(self.gridright-self.settingLength,self.settingLength)
        elif command == ">":
            if self.gridright == self.buttonNumber: # 既に一番右まで来ている場合は何もしない
                return 
            self.gridright = min(self.buttonNumber, self.gridright+self.settingLength)
            self.gridleft = self.gridright - self.settingLength
            self.right.grid_forget() # ボタン再配置のために一度取り外す
        print(command,":", self.gridleft, self.gridright, "->", self.buttonNumber)

        for i in range(preleft,preright): # 前に配置していたボタンを取り外す
            self.pushButtons[i].grid_forget()
        
        for i in range(self.gridleft,self.gridright):
            self.pushButtons[i].grid(row=0, column=i+1)
        
        if command == ">": # 左カーソルを押した場合は一度カーソルボタンが消えているので再配置
            self.right.grid(row=0,column=self.gridright+1,sticky=tk.N+tk.S)

    def gen_materialtable(self,event) -> None:
        def gen_tablelist(name) -> list:
            ret_list = []
            for values in self.result_dict[name].materials:
                ret_list.append(values + [name])
            return ret_list
    
        ret = str(event.widget["text"]).split("\n")
        name = ret[1].strip("Lv:")
        self.bottoms.gen_widgets(self.mode)
        tabledata = gen_tablelist(name)
        self.bottoms.insert_materials(tabledata)
        self.bottoms.startup()
        return

    def startup(self):
        self.root.mainloop()

class MaterialResult:
    '''合体素材の組み合わせ情報をテーブルに表示する'''
    materials = [] # 悪魔クラスのインスタンス内に格納された合体素材リストを格納
    colnames = []  # 合体モードに応じた列情報を記録
    buttons = []   # ボタンウィジェット群を格納
    parent = None
    is_exists = False # 生成されたインスタンスにおいてself.rootが生成されたかどうかをチェック
    output_table = list()

    def __init__(self,parent=None):
        '''親ウィンドウに関する情報(存在しない場合はNoneでも可)を先だって記録'''
        self.parent = parent
        
    def gen_widgets(self,num):
        '''ウィンドウを生成'''
        if self.is_exists: 
            if self.root.winfo_exists(): # 既に一度ウィンドウを生成している場合はまず消去してから処理を行う
                self.del_widgets()
        else:
            self.root = tk.Toplevel(master=self.parent)
            self.root.title("")
            self.is_exists = True
            self.set_frames()

        if num == 2:        # 合体モードに応じて列数を決定
            self.colnames = ("悪魔A", "悪魔B","合体結果")
        elif num == 3:
            self.colnames = ("悪魔A", "悪魔B", "悪魔C", "合体結果")

        self.set_table()
        self.gen_buttons()

    def set_frames(self) -> None:
        '''フレームの生成・配置'''
        # テーブル部分のフレーム
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0, column=0)

        # ボタン部分のフレーム
        self.buttonFrame = ttk.Frame(self.root)
        self.buttonFrame.grid(row=1, column=0)

    def set_table(self) -> None:
        '''テーブルウィジェットを生成・配置する'''
        self.materialTable = ttk.Treeview(
            self.frame, columns=self.colnames, selectmode=tk.BROWSE)
        self.materialTable.grid()

        self.materialTable.column('#0',width=0, stretch='no')
        for cn in self.colnames:
            self.materialTable.column(cn, anchor=tk.CENTER)
            self.materialTable.heading(cn, text=cn)

    def gen_buttons(self) -> None:
        '''合体モードに応じてボタンを生成'''
        ''''''
        return
        for i in range(len(self.colnames)):
            if self.colnames[i] == "合体結果":
                self.button = ttk.Button(self.buttonFrame, text=self.colnames[i]+"を閲覧する",
                                    command=None)
            else:
                self.button = ttk.Button(self.buttonFrame, text=self.colnames[i]+"を閲覧する",
                                    command=lambda:self.chk_material(self.materialTable.selection(),i))
            self.buttons.append(self.button)
        
        for i in range(len(self.colnames)):
            if self.colnames[i] == "合体結果":
                self.buttons[i].grid(row=0, column=i, sticky=tk.W+tk.E,)
            else:           # それ以外
                self.buttons[i].grid(row=0, column=i, sticky=tk.W+tk.E,)
    
    def del_widgets(self) -> None:
        '''再配置のため一度配置したボタン・テーブルを消去する'''
        self.materialTable.grid_forget()
        return
        for button in self.buttons:
            button.grid_forget()
        self.buttons = []

    def chk_material(self,record,idx) -> None:
        if not(record):
            return
        print(idx,record)

    def insert_materials(self,tabledata):
        '''悪魔オブジェクトから合体素材情報を取得し、テーブルに表示する'''
        for record in tabledata:
            self.materialTable.insert(parent="",index="end", values=record)
        return
    
    def startup(self):
        self.root.mainloop()

class DevilPartyEdit:
    '''仲魔リストを作成・編集するためのGUI'''
    filepath = "./devilparty.txt"
    devil_list = []

    def __init__(self):
        self.root = tk.Toplevel()        
        self.root.title("仲魔リスト(COMP)の編集")
        self.root.resizable(width=False, height=False)
        self.root.protocol("WM_DELETE_WINDOW", lambda:None)

        self.__generate_frame()
        self.__generate_widget()

        self.input_file()
        self.__setDevilParty(self.devil_list)

    def __generate_frame(self):
        self.frame = ttk.Frame(self.root)
        self.frame.grid(
            rowspan=2, row=0, column=0,
            padx=10, pady=10, sticky=tk.N+tk.S)
        self.frame.propagate(False)

        self.editframe = ttk.Frame(self.root)
        self.editframe.grid(row=0,column=1)

        self.okcancel = ttk.Frame(self.root)
        self.okcancel.grid(row=1, column=1)

    def __generate_widget(self):
        # 仲魔リストを閲覧・編集するためのリストボックスを生成
        self.listbox = tk.Listbox(
            self.frame, selectmode="Single", 
            listvariable=self.devil_list,
            width=20, height=16, justify=tk.CENTER,)
        self.listbox.grid(padx=10, pady=5, ipadx=0, ipady=0)

        # 追加する仲魔を指定するためのラベルを生成
        self.devilname = tk.StringVar()
        self.editName = ttk.Entry(self.editframe, textvariable=self.devilname)
        self.editName.grid(padx=10, pady=5, sticky=tk.W+tk.E)

        # 編集処理を行うためのボタンを生成
        self.addButton = ttk.Button(
            self.editframe, text="追加", 
            command=lambda:self.__addDevil())     # 仲魔の追加ボタン
        self.addButton.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W+tk.E)

        self.removeButton = ttk.Button(  # 仲魔の削除ボタン
            self.editframe, text="削除",
            command=lambda:self.__removeDevil())
        self.removeButton.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W+tk.E)
        
        # キャンセル・OKボタン
        okButton = ttk.Button(self.okcancel, text="編集内容を反映", command=lambda:self.exit(save=True))
        cancelButton = ttk.Button(self.okcancel, text="編集内容を破棄", command=lambda:self.exit(save=False))
        okButton.grid    (row=0, column=0, padx=5,pady=5)
        cancelButton.grid(row=0, column=1, padx=5,pady=5)

        txtButton = ttk.Button(self.okcancel, text=".txtを開く", command=lambda:subprocess.Popen(["start",os.path.abspath(self.filepath)], shell=True))
        txtButton.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)

    def __setDevilParty(self, devils=[]):
        if not(devils): # 引数が与えられていない場合はクラス変数の仲魔リストを参照
            devils = self.devil_list
        self.listbox.delete(0, tk.END) # 一度初期化

        for dev in devils:             # 再度仲魔リストを挿入
            self.listbox.insert(tk.END, dev)

    def __addDevil(self):    # 追加ボタンを押した時の処理
        name = self.devilname.get()
        if name not in self.devil_list: # 既に追加済みの悪魔は挿入しない
            self.listbox.insert(tk.END, name)
            self.devil_list.append(name)

    def __removeDevil(self): # 削除ボタンを押した時の処理
        idx = self.listbox.curselection()
        if idx:     # curselection()を用いて選択位置のインデックスを得る
            name = self.devil_list[idx[0]]
        else:       # 何も選択されていない場合は末尾を削除
            name = self.devil_list[-1]

        self.devil_list.remove(name)
        self.__setDevilParty(self.devil_list) # 削除後のリストを用いて再配置

    def startup(self):          # 起動
        self.root.mainloop()
    
    def exit(self,save=False):  # 終了
        def save_list(flag):    # セーブフラグが立っている場合は仲魔リストの保存処理を行う
            if not(flag):
                self.input_file()
                self.__setDevilParty()
            with open(os.path.abspath(self.filepath), 'w', encoding='UTF-8') as f:
                for dev in self.devil_list:
                    f.write(dev+"\n")
            return
        save_list(save)
    
    def input_file(self,path = None): # テキストファイルからデータを読み出す
        if not(path):   # ファイルパスが与えられなかった場合は標準で設定されているファイルを読む
            path = self.filepath
        else:           # ファイルパスが与えられた場合はパスの設定を変更
            self.filepath = path
        self.devil_list = []
        with open(os.path.abspath(path), 'r', encoding='UTF-8') as f:
            listbox = f.readlines()
            for line in listbox:
                devil = line.strip("\n")
                self.devil_list.append(devil)

        
class StartMenu:
    tryflag = False # 一回以上合体探索ボタンを押したかどうかチェック

    def __init__(self):
        self.root = tk.Tk()        
        self.root.title("邪教の館")
        self.root.resizable(width=False, height=False)

        self.menu = ttk.Frame(self.root)
        self.menu.grid(row=0, column=0)

        # テキストラベル
        self.entry = ttk.Label(self.menu, text="悪魔が集いし邪教の館へようこそ……\n何の用かな？")
        self.entry.grid(padx=10, pady=5)

        # 合体モード選択
        fusionby2d = ttk.Button(self.menu, text="2身合体を行う", command=lambda:self.start_fusion(2))
        fusionby3d = ttk.Button(self.menu, text="3身合体を行う", command=lambda:self.start_fusion(3))
        fusionby2d.grid(padx=10, pady=5, sticky=tk.W+tk.E)
        fusionby3d.grid(padx=10, pady=5, sticky=tk.W+tk.E)

        check_status = ttk.Button(self.menu, text="仲魔リストを編集する", command=lambda:self.open_editer())
        exit_button = ttk.Button(self.menu, text="外に出る", command=lambda:self.quit(flag=True))
        check_status.grid(padx=10, pady=5, sticky=tk.W+tk.E)
        exit_button.grid(padx=10, pady=5, sticky=tk.W+tk.E)

        # 合体に用いるバックエンド処理を備えたインスタンスを用意
        self.fusionsystemby2 = dfs.DevilFusionSystem()
        self.fusionsystemby3 = dfs.DevilFusionSystemBy3()
        self.devilparty = dfs.DevilParty()
        self.devilediter = []

    def start_fusion(self,num):
        '''ボタンを押し次第合体を開始し、バックエンド処理の結果をウィンドウに表示する'''
        print(f"{num}身合体を行います")
        if num == 2:
            self.devilparty.set_devilsdata()
            self.fusionsystemby2.set_devilparty(self.devilparty.devils_list)
            self.fusionsystemby2.search_results()
            result_length = len(self.fusionsystemby2.results_dict)
        else:
            self.devilparty.set_devilsdata()
            self.fusionsystemby3.set_devilparty(self.devilparty.devils_list)
            self.fusionsystemby3.search_results()
            result_length= len(self.fusionsystemby3.results_dict)

        # 動的に生成・除去するウィンドウ部分を用意
        if not(self.tryflag):   # GUI部品の新規生成は最初のみ
            self.fusionresult = DevilResult(parent=self.root)
            self.tryflag = True

        # 合体結果(辞書)を各画面部品に出力データとして与える
        if num == 2:
            self.fusionresult.result_dict = self.fusionsystemby2.results_dict
            self.fusionresult.get_buttonnames()
        else:
            self.fusionresult.result_dict = self.fusionsystemby3.results_dict
            self.fusionresult.get_buttonnames()

        # 合体結果を表示するためのウィンドウを用意
        self.fusionresult.mode = num
        self.fusionresult.gen_widgets(result_length)

        # 合体結果を得るための合体素材を閲覧するためのテーブルを表示
        self.fusionresult.startup()

    def open_editer(self):
        if not(self.devilediter):
            self.devilediter = DevilPartyEdit()
            self.devilediter.startup()
        else:
            self.devilediter.root.destroy()
            self.devilediter = DevilPartyEdit()
            self.devilediter.startup()



    def startup(self):   # 起動
        self.root.mainloop()

    def quit(self,flag): # 終了
        if flag:
            messagebox.showinfo("館の主","仲魔が増えたらまた来るがよい……")
        self.root.destroy()








class WINDOW:
    def __init__(self):
        self.root = tk.Tk()

        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0,column=0)

        self.input_num = tk.StringVar()
        self.entry = ttk.Entry(self.frame, textvariable=self.input_num, justify="center")
        self.entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        self.entry.insert(0,0)

        self.startButton = ttk.Button(self.frame, command=lambda:self.generate_buttons(self.input_num.get()), text="GENERATE")
        self.startButton.grid(row=1, column=0, sticky=tk.W+tk.E)

    def generate_buttons(self,num):
        num = int(num)
        self.but_win = DevilResult()
        self.but_win.startup()

    def startup(self):
        self.root.mainloop()

def main():
    root = WINDOW()
    root.startup()

if __name__ == "__main__":
    main()