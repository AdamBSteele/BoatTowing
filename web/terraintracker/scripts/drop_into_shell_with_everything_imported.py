# pylint: skip-file

# You can run this to open a Python shell with all this stuff already imported

if __name__ == "__main__":
    import code

    from terraintracker.app_init import db
    from terraintracker.models.live_configuration import live_config, LiveConfiguration
    from terraintracker.models.location import Location
    from terraintracker.models.location_history import LocationHistory
    from terraintracker.models.request_log import RequestLog
    from terraintracker.models.tow_request import TowRequest, TowRequestBatch
    from terraintracker.models.user import User
    from terraintracker.models.tow_event import TowEvent
    import datetime

    users = User.query.all()
    print("If you're gonna mess with live_config, make sure you run:")
    print("live_config.modification_time=datetime.now()")
    code.interact(local=dict(globals(), **locals()))
