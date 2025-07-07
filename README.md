# Simple FTP

## English
Simple web-based file sharing built with Flask.

### Features
- Upload single or multiple files with progress display
- Drag-and-drop area for quick upload
- Upload folders as ZIP archives
- Download and delete uploaded files
- Delete entire spaces from the index page
- Batch download selected files by clicking rows to select
- Comment board with colored messages
- Copy comment text exactly as written, preserving spaces and line breaks
- Server logs record what each IP does

### Usage
1. Install Flask if needed: `pip install flask`
2. Run `python ftp.py`
3. Open `http://localhost:5000/<space>/` in your browser to start uploading
   (`<space>` represents a task space or purpose, not necessarily a personal name)
4. Visiting `http://localhost:5000/` shows an index of all spaces

## 中文
基于 Flask 的简单文件分享工具。

### 功能
- 支持单文件和多文件上传并显示进度
- 提供拖拽区域快速上传
- 文件夹上传会自动压缩成 ZIP
- 可下载或删除已上传的文件
- 可在索引页删除整个空间
- 支持点击行选择并批量下载
- 内置留言板并为不同 IP 分配颜色
- 留言复制时完全保留空格和换行
- 记录各个 IP 的操作日志

### 使用方法
1. 如有需要安装 Flask：`pip install flask`
2. 运行 `python ftp.py`
3. 在浏览器打开 `http://localhost:5000/<空间名>/` 开始上传
   （此处的 `<空间名>` 指一个任务空间或目的地，并非必须是个人名称）
4. 访问 `http://localhost:5000/` 可查看全部空间索引

## 日本語
Flask で作られたシンプルなファイル共有ツールです。

### 機能
- 進捗表示付きでファイルを1つまたは複数アップロード
- ドラッグ&ドロップ用エリア
- フォルダを ZIP としてアップロード
- アップロードしたファイルのダウンロードと削除
- インデックスページからスペースを丸ごと削除
- 行をクリックして複数のファイルをまとめてダウンロード
- IP ごとに色が変わる掲示板
- コメントをコピーするとき、空白と改行をそのまま維持
- 各 IP の操作履歴を記録

### 使い方
1. Flask が入っていない場合 `pip install flask`
2. `python ftp.py` を実行
3. ブラウザで `http://localhost:5000/<スペース>/` を開いてアップロード開始
   （`<スペース>` は作業用や目的別のスペース名で、必ずしも個人名ではありません）
4. `http://localhost:5000/` にアクセスするとスペース一覧が表示されます
