docker exec -it mensis-python python main.py --run manual_backup_postgres

docker logs mensis-python

docker exec -it mensis-python bash




git clone git@github.com:yuugao-kaori/mensis.git
cd mensis
git checkout -b development
git add .
git commit -m "test"
git push -u origin development

git add ./
git commit -m "レポートの文章を修正"
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





