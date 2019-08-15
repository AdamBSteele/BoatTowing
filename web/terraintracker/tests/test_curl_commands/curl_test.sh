
# Add Marks notification ID and location
curl -u "Mark:Test1234"  -i -H "Accept: application/json" -H "Content-Type: application/json"  -X PUT -d \
  '{"lat":"40.7273949017785", 
    "lon":"-73.98767802526797",
    "one_signal_player_id": "0fab97c0-6ce8-490e-9b8b-1f53606848a2"}' \
    localhost:5000/users 

# Add Adams notification ID and location
curl -u '10155279163912326:Test!234'  -i -H "Accept: application/json" -H "Content-Type: application/json"  -X PUT -d \
  '{"lat":"40.7273949017785", 
    "lon":"-73.98767802526797",
    "one_signal_player_id": "546b9067-e9b4-4709-bf44-36c1bef6ad26"}' \
localhost:5000/users 

# Adam requests
curl -u "Adam:Test45678"  -i -H "Accept: application/json" -H "Content-Type: application/json"  -X POST -d \
  '{"lat":"40.7273949017785", 
    "lon":"-73.98767802526797"}' \
localhost:5000/tow_request 

# Mark requests
curl -u "Mark:Test1234"  -i -H "Accept: application/json" -H "Content-Type: application/json"  -X POST -d \
  '{"lat":"40.7273949017785", 
    "lon":"-73.98767802526797"}' \
localhost:5000/tow_request 

# Mark rejects
curl -u "Mark:Test1234" -i -H "Accept: application/json" -H "Content-Type: application/json" -X PUT -d \
  '{"action": "reject", "trash": "garbage"}' http://localhost:5000/tow_request

# Mark accepts
curl -u "Mark:Test1234" -i -H "Accept: application/json" -H "Content-Type: application/json" -X PUT -d \
  '{"action": "accept", "trash": "garbage"}' http://localhost:5000/tow_request


# Adam rejects
curl -u "Adam:Test45678" -i -H "Accept: application/json" -H "Content-Type: application/json" -X PUT -d \
  '{"action": "reject", "trash": "garbage"}' http://localhost:5000/tow_request

# Adam accepts
curl -u "Adam:Test45678" -i -H "Accept: application/json" -H "Content-Type: application/json" -X PUT -d \
  '{"action": "accept", "trash": "garbage"}' http://localhost:5000/tow_request
