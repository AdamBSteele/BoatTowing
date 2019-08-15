import json
import logging
import requests

from haversine import haversine

from terraintracker.config import ONE_SIGNAL_API_KEY, ONE_SIGNAL_APP_ID

logger = logging.getLogger(__name__)


class OneSignalNotificationSender():

    @property
    def headers(self):
        if not ONE_SIGNAL_API_KEY or not ONE_SIGNAL_APP_ID:
            logger.warning("You need to add your ONE_SIGNAL_API_KEY and ONE_SIGNAL_APP_ID to your .ini file")
        return {"Content-Type": "application/json; charset=utf-8", "Authorization": "Basic " + ONE_SIGNAL_API_KEY}

    def buildTowRequestContents(sefl, requestee, requestor):
        start = (float(requestee.last_lat_seen), float(requestee.last_long_seen))
        end = (float(requestor.last_lat_seen), float(requestor.last_long_seen))
        distance = haversine(start, end)
        return "{} ({:.2f}mi away) needs your help! Click here to help tow them.".format(requestor.first_name,
                                                                                         distance)

    def sendTowRequest(self, requestee, requestor, tow_request_id):
        tow_request_text = self.buildTowRequestContents(requestee, requestor)
        if requestee.one_signal_player_id is None or requestor.one_signal_player_id is None:
            logger.error("cant send tow request because someones missing a onesignal {}->{}".format(requestee,
                                                                                                    requestor))
            return
        logger.debug("One signal sending tow request")

        payload = {"app_id": ONE_SIGNAL_APP_ID,
                   "template_id": "54ddc503-21aa-4813-aa0e-4eda27479b00",
                   "contents": {"en": tow_request_text},
                   "include_player_ids": [requestee.one_signal_player_id, ],
                   "data": {"tow_request_id": tow_request_id,
                            "message_type": "incoming_tow_request"}}

        logging.debug("sending tow request to " + requestee.one_signal_player_id)
        req = requests.post("https://onesignal.com/api/v1/notifications",
                            headers=self.headers,
                            data=json.dumps(payload))

        print(req.status_code, req.reason, req.text)

    def sentTowRequestAccepted(self, requestor, requestee, tow_event_id):
        payload = {"app_id": ONE_SIGNAL_APP_ID,
                   "include_player_ids": [requestor.one_signal_player_id, ],
                   "headings": {"en": "A boater has offered to help!"},
                   "contents": {"en": "{} will call you shortly.".format(requestee.name)},
                   "data": {"message_type": "requestee_accept",
                            "user_id": requestee.id,
                            "tower_name": requestee.name,
                            "tow_event_id": tow_event_id}}

        logging.debug("Sending tow request accepted\n{}".format(payload))
        req = requests.post("https://onesignal.com/api/v1/notifications",
                            headers=self.headers,
                            data=json.dumps(payload))

        print(req.status_code, req.reason)

    def sendNoDriftTowersInYourArea(self, requestee_one_signal_player_id):

        payload = {"app_id": ONE_SIGNAL_APP_ID,
                   "include_player_ids": [requestee_one_signal_player_id, ],
                   "headings": {"en": "Sorry!"},
                   "contents": {"en": "No Drift towers are in your area"}}

        logging.debug("sending no drifters in your area to " + requestee_one_signal_player_id)
        req = requests.post("https://onesignal.com/api/v1/notifications",
                            headers=self.headers,
                            data=json.dumps(payload))

        print(req.status_code, req.reason)

    def sendNoOneIsComingBecauseYouGotRejected(self, requestee_one_signal_player_id):

        payload = {"app_id": ONE_SIGNAL_APP_ID,
                   "include_player_ids": [requestee_one_signal_player_id, ],
                   "headings": {"en": "Sorry!"},
                   "contents": {"en": "No one is available to tow you at this time"}}

        logging.debug("sending tow request to " + requestee_one_signal_player_id)
        req = requests.post("https://onesignal.com/api/v1/notifications",
                            headers=self.headers,
                            data=json.dumps(payload))

        print(req.status_code, req.reason)

    def sendTowEventCompleted(self, user_sending_message, user_receiving_message):
        payload = {"app_id": ONE_SIGNAL_APP_ID,
                   "include_player_ids": [user_receiving_message.one_signal_player_id, ],
                   "headings": {"en": "Tow Complete!"},
                   "contents": {"en": "{} has marked the tow complete. Thank you for using Drift!".format(user_sending_message.id)}}

        logging.debug("sending tow event complete to {}".format(user_receiving_message))
        req = requests.post("https://onesignal.com/api/v1/notifications",
                            headers=self.headers,
                            data=json.dumps(payload))

    def sendTowEventCancelled(self, user_sending_message, user_receiving_message):
        payload = {"app_id": ONE_SIGNAL_APP_ID,
                   "include_player_ids": [user_receiving_message.one_signal_player_id, ],
                   "headings": {"en": "Tow Complete!"},
                   "contents": {"en": "{} has marked the tow cancelled. Thank you for using Drift!".format(user_sending_message.id, 'XXX-XXX-XXXX')}}

        logging.debug("sending tow event cancelled to ".format(user_receiving_message))
        req = requests.post("https://onesignal.com/api/v1/notifications",
                            headers=self.headers,
                            data=json.dumps(payload))

        print(req.status_code, req.reason)


one_signal_notification_sender = OneSignalNotificationSender()
