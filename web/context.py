def available_states():
    return [{'id': str(level+1), 'name': str(level+1)} for level in xrange(5)]


class Context():

    def __init__(self, bus, status):
        self.bus = bus
        self.status = status

    def fetch(self):
        return {
            'statuses': self.status.get_statuses(),
            'state': self.bus.get_state(),
            'states': available_states(),
            'state_history': self.bus.get_state_history(),
            'heart_rate': self.bus.get_heart_rate(),
            'heart_rate_history': self.bus.get_heart_rate_history(),
        }
