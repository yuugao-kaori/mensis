docker exec -it mensis-python python main.py test

docker logs mensis-python

docker exec -it mensis-python bash


git clone git@github.com:yuugao-kaori/mensis.git
cd mensis
git checkout -b development
git add .
git commit -m "test"
git push -u origin development