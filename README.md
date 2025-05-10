# Mensis ｰ Misskey自動メンテナンスシステム

## これはなに？
Misskeyのメンテナンスをちょっと高度にやってくれるDockerComposeです。

## できること
- Postgresのバックアップ
- PGroonga用インデックスの再構築
- PG_repackによるVACUUM処理
- ディスク使用状況の把握
- メンテナンス結果をターゲットアカウントにDMで送る
- メンテナンス実行状況などをノートする

## （まだ）できないこと
- Minioのバックアップ取得
- MisskeyのfilesからMinioへの移行を支援する機能
- Redisのバックアップ取得

## ご注意
- たぶんバグがあります。
- .envでコメントアウトされている機能の多くが未実装です。
- オーバーヘッドが大きいです（性能がギリギリのサーバでは運用しないほうが吉）

## 使い方
1. backup,penetrationディレクトリを/mensisの中に作ってください
2. `mv example.env .env`を実行して.envファイルを作ります。
3. 環境変数を設定します。（MisskeyのTOKENなど）
4. `docker compose up -d`してください。※Dockerが動く環境であるのが前提です
5. 正常に動いていれば成功です。
6. `./scripts/python.log`にログが出力されているので、気になったことがあればご覧ください。
   
## Q＆A
- Q：Mensisの意味は？
- A：MisskeyのバックエンドシステムをTerra（テルラ）と呼んでいるので、その補佐をするMensis（月の意味）です。
- Q：問い合わせ先は？
- A：https://misskey.seitendan.com/@takumin3211 です。が、多くの場合、ご期待には添えません。