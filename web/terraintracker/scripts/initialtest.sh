echo "# create user1"
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d \
  '{
  "phone":"3475563921", 
  "lat":"40.7273949017785", 
  "lon":"-73.98767802526797",
  "password": "Test1234",
  "apns_token": "ebc54afa581eb0098c05cbffe5ed6b01c861ef47b27a266cb6acc649f3e27a11"}' http://localhost:5000/users

echo "# create user2"
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d \
  '{
  "phone":"5555555552", 
  "lat":"40.72", 
  "lon":"-73.98",
  "password": "Test45678",
  "apns_token": "28bc9df3164ca01af6d226370ebcd0071c20bcf1135b5342b2dcf227d62daa4d"}' http://localhost:5000/users

echo "# login user1"
curl -u "3475563921:Test45678" -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d \
  '{
  "lat":"40.72", 
  "lon":"-73.98",
  "apns_token": "28bc9df3164ca01af6d226370ebcd0071c20bcf1135b5342b2dcf227d62daa4d"}' http://localhost:5000/login
echo "# login user2"
curl -u "5555555552:Test45678" -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d \
  '{
  "lat":"40.72", 
  "lon":"-73.98",
  "apns_token": "28bc9df3164ca01af6d226370ebcd0071c20bcf1135b5342b2dcf227d62daa4d"}' http://localhost:5000/login


echo "# user1 request tow"
curl -u "3475563921:Test1234" -X POST http://localhost:5000/tow_request 

echo "# user2 accept"
curl -u "5555555552:Test45678" -i -H "Accept: application/json" -H "Content-Type: application/json" -X PUT -d \
  '{"action": "accept"}' http://localhost:5000/tow_request

echo "# user1 get status"
curl -u "3475563921:Test1234" -i -H "Accept: application/json" -H "Content-Type: application/json" http://localhost:5000/tow_event

echo "# user2 get status"
curl -u "5555555552:Test45678" -i -H "Accept: application/json" -H "Content-Type: application/json" http://localhost:5000/tow_event