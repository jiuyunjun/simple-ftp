# Simple FTP

## English
Simple web-based file sharing built with Flask.

### Features
- Upload single or multiple files with progress display
- Drag-and-drop area for quick upload
- Upload folders as ZIP archives
- Download and delete uploaded files
- Batch download selected files by clicking rows to select
- Comment board with colored messages
- Server logs record what each IP does

### Usage
1. Install Flask if needed: `pip install flask`
2. Run `python ftp.py`
3. Open `http://localhost:5000/<username>/` in your browser to start uploading

## 中文
基于 Flask 的简单文件分享工具。

### 功能
- 支持单文件和多文件上传并显示进度
- 提供拖拽区域快速上传
- 文件夹上传会自动压缩成 ZIP
- 可下载或删除已上传的文件
- 支持点击行选择并批量下载
- 内置留言板并为不同 IP 分配颜色
- 记录各个 IP 的操作日志

### 使用方法
1. 如有需要安装 Flask：`pip install flask`
2. 运行 `python ftp.py`
3. 在浏览器打开 `http://localhost:5000/<用户名>/` 开始上传

## 日本語
Flask で作られたシンプルなファイル共有ツールです。

### 機能
- 進捗表示付きでファイルを1つまたは複数アップロード
- ドラッグ&ドロップ用エリア
- フォルダを ZIP としてアップロード
- アップロードしたファイルのダウンロードと削除
- 行をクリックして複数のファイルをまとめてダウンロード
- IP ごとに色が変わる掲示板
- 各 IP の操作履歴を記録

### 使い方
1. Flask が入っていない場合 `pip install flask`
2. `python ftp.py` を実行
3. ブラウザで `http://localhost:5000/<ユーザー名>/` を開いてアップロード開始
