from collections import defaultdict, Counter
from random import randint, random
from pprint import pprint
from enum import Enum
import statistics

BOTTOM_FLOOR = 1
TOP_FLOOR = 10
PERCENTAGE_BRITT = 1
DEBUG = False

class Direction(Enum):
	UP = 'up'
	DOWN = 'down'
	NONE = None

	@staticmethod
	def opposite_direction(floor: int) -> 'Direction':
		if floor == TOP_FLOOR:
			return Direction.DOWN
		if floor == BOTTOM_FLOOR:
			return Direction.UP
		raise TypeError('Can only Turn Around At Extremes!')

class Person:
	def __init__(self, current_floor: int, desired_floor: int, button_pressed: Direction, turn_created):
		self.current_floor = current_floor
		self.desired_floor = desired_floor
		self.button_pressed = button_pressed
		self.turn_created = turn_created

	def __str__(self) -> str:
		return f'I am on {self.current_floor}, I want to go to {self.desired_floor} (I pressed {self.button_pressed})'

	def __repr__(self) -> str:
		return self.__str__()

	@property
	def true_direction(self) -> Direction:
		if self.desired_floor > self.current_floor:
			return Direction.UP
		else:
			return Direction.DOWN

	def __lt__(self, other: 'Person') -> bool:
		return self.desired_floor < other.desired_floor

	@staticmethod
	def generate_request(elevator_current_floor, turn) -> 'Person':
		current_floor = -1
		desired_floor = -1
		while current_floor == desired_floor:
			current_floor = randint(BOTTOM_FLOOR, TOP_FLOOR)
			desired_floor = randint(BOTTOM_FLOOR, TOP_FLOOR)

		is_britt = random() < PERCENTAGE_BRITT
		if is_britt:
			direction = Direction.DOWN if elevator_current_floor > current_floor else Direction.UP
		else:
			direction = Direction.UP if desired_floor > current_floor else Direction.DOWN
		return Person(current_floor, desired_floor, direction, turn)

class Elevator:
	def __init__(self):
		self.current_floor = BOTTOM_FLOOR
		self.direction_of_next_move = Direction.NONE
		self.request_queue = defaultdict(list) # this will be {floor where a person is waiting: [Person]}
		self.passengers = []
		self.passenger_stats = []

	def print_passenger_metrics(self):
		print(
			f'''
Min Turns: {min(self.passenger_stats)}
Max Turns: {max(self.passenger_stats)}
Mean Turns: {statistics.mean(self.passenger_stats)}
Median Turns: {statistics.median(self.passenger_stats)}
Mode: {Counter(self.passenger_stats).most_common()[0][0]}
{100*PERCENTAGE_BRITT:3.1f}% of People Are Britt
'''
		)

	def more_requests_to_fulfill(self) -> bool:
		return self.passengers or any(v for v in self.request_queue.values())

	def floor_is_in_right_direction(self, prospective_floor: int) -> bool:
		if self.direction_of_next_move == Direction.UP:
			return prospective_floor > self.current_floor
		if self.direction_of_next_move == Direction.DOWN:
			return prospective_floor < self.current_floor
		return False

	def request_is_in_right_direction(self, person: Person) -> bool:
		return (
			self.floor_is_in_right_direction(person.current_floor) and
			self.direction_of_next_move == person.button_pressed
		)

	def initial_direction_guess_if_no_passengers(self) -> None:
		# if you have no passengers and are at the top or bottom, turn around
		# if you aren't and you have a direction, great keep going
		# if you don't have a direction, try and get to ground floor
		if self.current_floor == TOP_FLOOR:
			self.direction_of_next_move = Direction.DOWN
		elif self.current_floor == BOTTOM_FLOOR:
			self.direction_of_next_move = Direction.UP
		elif self.direction_of_next_move == Direction.NONE:
			self.direction_of_next_move = Direction.DOWN

	def move(self) -> None:
		if self.direction_of_next_move == Direction.UP:
			if self.current_floor == TOP_FLOOR:
				raise TypeError('Cant shoot out of the building')
			self.current_floor += 1
		elif self.direction_of_next_move == Direction.DOWN:
			if self.current_floor == BOTTOM_FLOOR:
				raise TypeError('Cant shoot underground')
			self.current_floor -= 1

	def release_passengers(self, turn) -> None:
		to_let_off = [p for p in self.passengers if p.desired_floor == self.current_floor]
		self.passenger_stats += [turn - p.turn_created for p in to_let_off]
		self.passengers = [p for p in self.passengers if p.desired_floor != self.current_floor] # only keep people who did not want this floor

	def accept_passengers(self) -> None:
		prospective_passengers = self.request_queue.pop(elevator.current_floor, [])
		new_passengers = [p for p in prospective_passengers if p.button_pressed == self.direction_of_next_move]
		self.passengers += new_passengers
		self.passengers.sort()
		leave_behinds = [p for p in prospective_passengers if not p in new_passengers]
		self.request_queue[self.current_floor] = leave_behinds

	def receive_request(self, requestor: Person) -> None:
		self.request_queue[requestor.current_floor].append(requestor)

	def show_status(self, side: str, turn: int) -> None:
		if not DEBUG:
			return
		print(f'========{side} of Turn {turn}========')
		print(f'Current Floor: {self.current_floor}, Next Move: {self.direction_of_next_move}')
		print(f'Passengers: {self.passengers}')
		print('Request Queue: ')
		pprint(dict(self.request_queue))

turn = 1
elevator = Elevator()
more_passengers = True
while more_passengers or elevator.more_requests_to_fulfill():



	elevator.show_status('Start', turn)

	elevator.release_passengers(turn)
	elevator.accept_passengers()

	more_passengers = turn < 1000
	if more_passengers:
		new_requests = randint(0, 3)
		for _ in range(new_requests):
			elevator.receive_request(Person.generate_request(elevator.current_floor, turn))

	# decide which way to go
	if not elevator.passengers:
		elevator.initial_direction_guess_if_no_passengers()
		# if you have no passengers, see if there is an obvious direction
		# then, check your request queue
		# first see if there are people who want to go in the direction you want to go - fulfill the closest one
		# if there aren't any, pick the closest request [in the 'wrong' direction]



		requests_to_fulfill = {
			k: [p for p in v if elevator.request_is_in_right_direction(p)] for k, v in elevator.request_queue.items() if v
		}
		if not any(v for v in requests_to_fulfill.values()):
			requests_to_fulfill = {
				k: [p for p in v if not elevator.request_is_in_right_direction(p)] for k, v in elevator.request_queue.items() if v
			}
		if not any(v for v in requests_to_fulfill.values()):
			# there was no one waiting to go in the direction i am going, or the opposite, so don't move!
			elevator.direction_of_next_move = Direction.NONE
		else:
			floors_sorted_by_distance = sorted(requests_to_fulfill.keys(), key = lambda floor: floor - elevator.current_floor) # not absolute value in order to bias it to going up (to break ties where it bounces between 5 and 6 to fulfill people on 1 and 10)
			floor_to_move_to = floors_sorted_by_distance[0]
			if floor_to_move_to == elevator.current_floor and floor_to_move_to in [TOP_FLOOR, BOTTOM_FLOOR]:
				elevator.direction_of_next_move = Direction.opposite_direction(floor_to_move_to)
			else:
				elevator.direction_of_next_move = Direction.DOWN if floor_to_move_to < elevator.current_floor else Direction.UP
	else:
		# if you do have passengers
			# if you have people who want to go in the direction you are going, keep going
			# if you don't, change direction
			# if you don't have a direction, ask the first passenger
		if elevator.direction_of_next_move == Direction.NONE:
			elevator.direction_of_next_move = elevator.passengers[0].true_direction
		
		if not any(p.true_direction == elevator.direction_of_next_move for p in elevator.passengers):
			elevator.direction_of_next_move = Direction.UP if elevator.direction_of_next_move == Direction.DOWN else Direction.DOWN



	elevator.accept_passengers()
	elevator.show_status('End', turn)
	try:
		elevator.move()
	except TypeError:
		print('Elevator Crash!')
		import pdb
		pdb.set_trace()
		break
	turn += 1

elevator.print_passenger_metrics()


