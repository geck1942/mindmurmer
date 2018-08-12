from mq import mq_messages, fr0stlevel, heartrate, heartrate_history
from status import status_fr0st, status_eeg, status_dmx, status_heartsensor


def get_context():
    return {
        'statuses': statuses(),
        'fr0stlevel': fr0stlevel(),
        'fr0stlevels': fr0stlevels(),
        'heartrate': heartrate(),
        'heartrate_history': heartrate_history(),
        'mqmessages': mq_messages(),
    }


def fr0stlevels():
    return [
        {'id': "default", 'name': "Default"},
        {'id': "0", 'name': "0"},
        {'id': "1", 'name': "1"},
        {'id': "2", 'name': "2"},
        {'id': "3", 'name': "3"},
        {'id': "4", 'name': "4"},
        {'id': "5", 'name': "5"},
    ]


def statuses():
    return [
        status_fr0st(),
        status_eeg(),
        status_dmx(),
        status_heartsensor(),
    ]
