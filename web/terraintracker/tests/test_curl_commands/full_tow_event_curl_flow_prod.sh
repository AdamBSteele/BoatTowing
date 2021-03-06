# APNS tokens
# Mark: ebc54afa581eb0098c05cbffe5ed6b01c861ef47b27a266cb6acc649f3e27a11
# Adam: 28bc9df3164ca01af6d226370ebcd0071c20bcf1135b5342b2dcf227d62daa4d
# Harmeet: a446520bd57a50e5e69dcd06810c3b35ea3fb37e778230d8023f1421950af2cb


echo "# create user1"
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d \
  '{
  "phone":"5555555551", 
  "lat":"40.7273949017785", 
  "lon":"-73.98767802526797",
  "password": "Test1234",
  "apns_token": "ebc54afa581eb0098c05cbffe5ed6b01c861ef47b27a266cb6acc649f3e27a11"}' localhost:5000/users

echo "# create user2"
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d \
  '{
  "phone":"5555555552", 
  "lat":"40.72", 
  "lon":"-73.98",
  "password": "Test1234",
  "apns_token": "a446520bd57a50e5e69dcd06810c3b35ea3fb37e778230d8023f1421950af2cb"}' localhost:5000/users

echo "# user1 request tow"
curl -u "5555555551:Test1234" -X POST localhost:5000/tow_request 

echo "# user2 accept"
curl -u "5555555552:Test1234" -i -H "Accept: application/json" -H "Content-Type: application/json" -X PUT -d \
  '{"action": "accept"}' localhost:5000/tow_request

echo "# user1 confirm"
curl -u "5555555551:Test1234" -i -H "Accept: application/json" -H "Content-Type: application/json" -X PUT -d \
  '{"action": "confirm"}' localhost:5000/tow_event

echo "# user1 get status"
curl -u "5555555552:Test1234" -i -H "Accept: application/json" -H "Content-Type: application/json" localhost:5000/tow_event

echo "# user2 get status"
curl -u "5555555551:Test1234" -i -H "Accept: application/json" -H "Content-Type: application/json" localhost:5000/tow_event