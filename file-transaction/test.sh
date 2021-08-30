python file_transaction.py -c BeginTrans $1
python file_transaction.py -f example.json -t ACTIONS1 $1
python file_transaction.py -f example.json -t ACTIONS2 -p 'test|append' $1
python file_transaction.py -c Commit $1


