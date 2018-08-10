def mq_start():
    pass


def mq_messages():
    return [
        '-00:00:01.000 abc',
        '-00:00:02.000 def',
        '-00:00:03.000 ghi',
        '-00:00:05.000 jkl',
    ]


def fr0stlevel():
    return 'No Level Seen On MQ Bus, Has The Webserver Just Started?'


def heartrate():
    return 'No Heart Rate Seen On MQ Bus, Has The Webserver Just Started?'


def heartrate_history():
    return [
        '-00:00:01.000 67',
        '-00:00:02.000 68',
        '-00:00:05.000 70',
        '-00:00:06.000 71',
    ]
