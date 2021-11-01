from statemachine import StateMachine, State


class TrafficLightMachine(StateMachine):
    green = State('Green', initial=True)
    yellow = State('Yellow')
    red = State('Red')

    slowdown = green.to(yellow)
    stop = yellow.to(red)
    go = red.to(green)

    def on_slowdown(self):
        print('transition on_slowdown')


class MyModel(object):
    def __init__(self, state):
        self.state = state
    


obj = MyModel(state='green')
traffic_light = TrafficLightMachine(obj)
print(traffic_light.is_red)

traffic_light.slowdown()
