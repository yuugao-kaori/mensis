docker exec -it mensis-python python main.py --run test

docker logs mensis-python

docker exec -it mensis-python bash




git clone git@github.com:yuugao-kaori/mensis.git
cd mensis
git checkout -b development
git add .
git commit -m "test"
git push -u origin development

git add ./
git commit -m "レポート機能の定期実行化"
git push


ログローテ


SELECT
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    indexname = 'idx_note_text_with_pgroonga'
    AND schemaname = 'public';





