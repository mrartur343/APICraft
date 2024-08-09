import asyncio
import random
import sys
import threading
import time
import typing

import schedule
from flask import Flask, jsonify, request

app = Flask(__name__)


class Player:
	def __init__(self, ip: str, x: int, y: int, health: float, hungry: float, inventory: dict):
		self.inventory: typing.Dict[str,int] = inventory
		self.hungry = hungry
		self.health = health
		self.y = y
		self.x = x
		self.ip = ip


class FloorBlock:
	def __init__(self, block_type: str):
		self.block_type = block_type


class Block:
	def __init__(self, block_type: str, loot: dict):
		self.loot = loot
		self.block_type = block_type


class MapFloorBlock:
	def __init__(self, block: FloorBlock, x: int, y: int):
		self.block = block
		self.y = y
		self.x = x


class MapBlock:
	def __init__(self, block: Block, x: int, y: int):
		self.block = block
		self.y = y
		self.x = x


class Map:
	def __init__(self):
		self.floor: typing.List[MapFloorBlock] = []
		self.blocks: typing.List[MapBlock] = []

	def get_floor(self, x: int, y: int) -> MapFloorBlock | None:
		for floor_block in self.floor:
			if floor_block.x == x and floor_block.y == y:
				return floor_block

		return None

	def get_block(self, x: int, y: int) -> MapBlock | None:
		for block in self.blocks:
			if block.x == x and block.y == y:
				return block

		return None

	def __str__(self):
		map_listed: typing.List[typing.List[str]] = []
		for i in range(20):
			line = []
			for j in range(20):
				x = i - 10
				y = j - 10
				floor = self.get_floor(x, y)
				if floor is None:
					line.append('n')
				else:
					line.append(floor.block.block_type[0])
			map_listed.append(line)

		map_str: str = ''
		for line in map_listed:
			for s in line:
				map_str += s + ' '
			map_str += '\n'
		return map_str


def generate_map() -> Map:
	map = Map()

	for i in range(20):
		for j in range(20):
			x = i - 10
			y = j - 10
			if (x ** 2) + (y ** 2) < 100:
				map.floor.append(MapFloorBlock(all_floor['stone_floor'], x - 10, y))
	for i in range(20):
		for j in range(20):
			x = i - 10
			y = j - 10
			if (x ** 2) + (y ** 2) < 100:
				map.floor.append(MapFloorBlock(all_floor['grass_floor'], x + 10, y))

	map.floor.append(MapFloorBlock(all_floor['stone_floor'], 0, 0))

	for i in range(20):
		for j in range(20):
			x = i - 10
			y = j - 10
			random.seed(f"{x}_{y}")
			if random.random() < 0.2:
				if map.get_floor(x, y) is not None:
					if map.get_floor(x, y).block == all_floor['grass_floor']:
						map.blocks.append(MapBlock(all_block['three'], x, y))
	for i in range(20):
		for j in range(20):
			x = i - 10
			y = j - 10
			random.seed(f"{x}_{y}")
			if random.random() < 0.2:
				if map.get_floor(x, y) is not None:
					if map.get_floor(x, y).block == all_floor['stone_floor']:
						map.blocks.append(MapBlock(all_block['stone'], x, y))

	map.floor.append(MapFloorBlock(all_floor['diamond_floor'], -5, 0))
	map.floor.append(MapFloorBlock(all_floor['diamond_floor'], 5, 0))
	map.blocks.append(MapBlock(all_block['diamond_block'], -5, 0))

	return map


class Item:
	def __init__(self, item_type: str, name: str, block: Block):
		self.block = block
		self.name = name
		self.item_type = item_type


class FuelItem(Item):
	def __init__(self, name: str, block: Block):
		super().__init__("fuel", name, block)


class EnvItem(Item):
	def __init__(self, name: str, block: Block):
		super().__init__("env", name, block)


all_floor = {
	'stone_floor': FloorBlock('stone_floor'),
	'grass_floor': FloorBlock('grass_floor'),
	'diamond_floor': FloorBlock('diamond_floor')
}
all_block = {
	'three': Block('three', {'wood': 5}),
	'wood': Block('wood', {'wood': 1}),
	'plank': Block('plank', {'plank': 1}),
	'cobblestone': Block('cobblestone', {'cobblestone': 1}),
	'stone': Block('stone', {'cobblestone': 1}),
	'stick': Block('stick', {'stick': 1}),
	'pickaxe': Block('pickaxe', {'pickaxe': 1}),
	'diamond_block': Block('diamond_block', {'diamond_block': 1}),
}

all_items: typing.Dict[str,Item | EnvItem | FuelItem] = {
	'three': EnvItem('three', all_block['three']),
	'stone': EnvItem('stone', all_block['stone']),
	'wood': FuelItem('wood', all_block['wood']),
	'plank': FuelItem('plank', all_block['plank']),
	'cobblestone': FuelItem('cobblestone', all_block['cobblestone']),
	'stick': FuelItem('stick', all_block['stick']),
	'pickaxe': Item("other",'pickaxe', all_block['pickaxe']),
	'diamond_block': EnvItem('diamond_block', all_block['diamond_block']),
}
all_crafts = [
	({'wood':1},{'plank':4}),
	({'plank':2},{'stick':4}),
	({'stick':2,'cobblestone':3},{'pickaxe':1}),
]


class Game:
	def __init__(self):
		self.map = generate_map()
		self.players: typing.List[Player] = []

	def get_xy_player(self, x, y) -> int | None:
		player_index = 0
		for player in self.players:
			if player.x == x and player.y == y:
				return player_index
			player_index += 1

		return None

	def get_xy_floor(self, x, y) -> MapFloorBlock | None:
		for floor_block in self.map.floor:
			if floor_block.x == x and floor_block.y == y:
				return floor_block

		return None

	def get_xy_block(self, x, y) -> MapBlock | None:
		for block in self.map.blocks:
			if block.x == x and block.y == y:
				return block

		return None

	def collision_check(self, x, y):
		player_col = self.get_xy_player(x, y)
		floor_col = self.get_xy_floor(x, y)
		block_col = self.get_xy_block(x, y)
		return player_col is None and not (floor_col is None) and block_col is None

	def get_player_info(self, ip) -> Player | None:


		player_info = None

		for p in self.players:
			if p.ip == ip:
				player_info = p

		return player_info
	def get_player_index(self, ip) -> int | None:


		player_index = 0

		for p in self.players:
			if p.ip == ip:
				return player_index
			player_index+=1


	def get_block_index(self, x, y) -> int | None:


		b_index = 0

		for b in self.map.blocks:
			if b.x==x and b.y==y:
				return b_index
			b_index += 1

		return None

	def player_tick(self, ip):
		ip_exst = False

		player_index = 0

		for p in self.players:
			if p.ip == ip:
				ip_exst = True
				break
			player_index += 1

		if not ip_exst:
			player_index = len(self.players)
			self.players.append(Player(ip, 5 - random.randint(0, 10), 5 - random.randint(0, 10), 1.0, 1.0, {}))

		self.players[player_index].hungry = round(self.players[player_index].hungry, 2)
		self.players[player_index].health = round(self.players[player_index].health, 2)
		return player_index

	def player_mine(self, ip: str, direct: int) -> bool:
		player_index = self.player_tick(ip)

		xv = 0
		yv = 0

		if direct == 0:
			yv = -1
		if direct == 1:
			xv = 1
		if direct == 2:
			yv = 1
		if direct == 3:
			xv = -1

		x = self.players[player_index].x + xv
		y = self.players[player_index].y + yv
		print(f'mine: {direct}')
		print(f'b: {self.get_xy_block(x, y)}')
		if not (self.get_xy_block(x, y) is None):
			if self.get_xy_block(x, y).block.block_type!='diamond_block':
				for loot_name, loot_count in self.get_xy_block(x, y).block.loot.items():
					if not (loot_name in self.players[player_index].inventory):
						self.players[player_index].inventory[loot_name]=0
					self.players[player_index].inventory[loot_name] += loot_count

				b_id = self.get_block_index(x,y)
				self.map.blocks.pop(b_id)
				return True
			elif 'pickaxe' in self.players[player_index].inventory:
				if self.players[player_index].inventory['pickaxe']>0:
					for loot_name, loot_count in self.get_xy_block(x, y).block.loot.items():
						if not (loot_name in self.players[player_index].inventory):
							self.players[player_index].inventory[loot_name] = 0
						self.players[player_index].inventory[loot_name] += loot_count
					return True
		return False

	def player_move(self, ip: str, direct: int) -> bool:
		player_index = self.player_tick(ip)

		xv = 0
		yv = 0

		if direct == 0:
			yv = -1
		if direct == 1:
			xv = 1
		if direct == 2:
			yv = 1
		if direct == 3:
			xv = -1
		x = self.players[player_index].x + xv
		y = self.players[player_index].y + yv
		if self.collision_check(x, y):
			self.players[player_index].y += yv
			self.players[player_index].x += xv
			return True
		else:
			return False
	def player_build(self, ip: str, direct: int,inventory_key:str) -> bool:
		player_index = self.player_tick(ip)

		xv = 0
		yv = 0

		if direct == 0:
			yv = -1
		if direct == 1:
			xv = 1
		if direct == 2:
			yv = 1
		if direct == 3:
			xv = -1
		x = self.players[player_index].x + xv
		y = self.players[player_index].y + yv
		if self.collision_check(x, y):
			if inventory_key in self.players[player_index].inventory:
				if self.players[player_index].inventory[inventory_key] > 0:
					block_to_build = all_items[inventory_key].block
					self.map.blocks.append(MapBlock(block_to_build, x, y))
					self.players[player_index].inventory[inventory_key] -= 1

					if self.get_xy_block(5,0).block.block_type=='diamond_block':
						print(f"{ip} VIN!!!")
						sys.exit()


					return True
		return False

	def player_craft(self, ip:str,craft_index:int) -> bool:
		player_info = self.get_player_info(ip)
		player_index = self.get_player_index(ip)
		input_check = True
		input_items, output_items = all_crafts[craft_index]
		for item_name, item_count in input_items.items():
			if not (item_name in player_info.inventory):
				input_check=False
				break
			elif item_count>player_info.inventory[item_name]:
				input_check=False
				break


		if input_check:
			for item_name, item_count in input_items.items():
				self.players[player_index].inventory[item_name] -= item_count
			for item_name, item_count in output_items.items():
				if not (item_name in self.players[player_index].inventory):
					self.players[player_index].inventory[item_name] = 0
				self.players[player_index].inventory[item_name] += item_count
			return True
		return False



game = Game()


@app.route("/")
def hello_world():
	print(request.headers['Cf-Connecting-Ip'])
	return """<p>APICraft - це челендж від команди Dev is Art для програмістів. Це дуже проста 2д копія майнкрафт, з 1 спільним для всіх сервером на якому відбувається вайп. Особливість у тому що неіснує клінєту для цієї гри - лише серверна частина та API. На івенті по спідрану цієї гри вийграє той, хто з самописним клієнтом перший пройде гру.</p>
	<p>apicraft.devisart.xyz/p_move?direction={напрям} - рух персонажа на 1 блок, напрям задається числами. 0 верх, 1 вправо, 2 униз, 3 вліво.</p>
	<p>apicraft.devisart.xyz/p_mine?direction={напрям} - добути блок за напрямком, не всі блоки можна добути без кам'яного кайла. Напрям задається тими ж числами</p>
	<p>apicraft.devisart.xyz/p_build?direction={напрям}&block_name={назва блоку} - поставити блок, назву блоку можна побачити у інвентарі, запит на який буде нижче</p>
	<p>apicraft.devisart.xyz/p_craft?index={номер_крафту} - скрафтити предмет за його номером. 0 - 1 дерево у 4 дошки. 1 - 2 дошки у 4 палки. 2 - 2 палки та 3 камня у 1 кайло</p>
	<p>apicraft.devisart.xyz/get_floor?x={x}&y={y} - отримати назву блоку що відповідає за пол на цих координатах. 0 - відсутність блоку</p>
	<p>apicraft.devisart.xyz/get_block?x={x}&y={y} - те саме, але з блоком, блоки на цьому рівні можна добути через запит p_mine. 0 - відсутність блоку</p>
	<p>apicraft.devisart.xyz/get_all_blocks - отримати всі блоки на мапі гри за координатами</p>
	<p>apicraft.devisart.xyz/get_all_floor - отримати всі блоки полу на мапі гри за координатами</p>
	<p>apicraft.devisart.xyz/get_all_players - отримати всю інформацію про всіх гравців у грі</p>
	<p>apicraft.devisart.xyz/my_player_info - отримати інформацію про вашого гравця у грі. Щоб він створився використайте у будь-якому напрямку p_move</p>
	<p>apicraft.devisart.xyz/get_player?x={x}&y={y} - отримати інформацію про гравця за координатами. 0 - відсутній гравець по цим координатам</p>
	<p>apicraft.devisart.xyz/craft_list - всі крафти у грі"""


@app.route("/p_move", methods=["GET"])
def p_move():
	ip = request.headers['Cf-Connecting-Ip']
	direct = request.args.get('direction')
	return jsonify(game.player_move(ip, int(direct)))


@app.route("/p_mine", methods=["GET"])
def p_mine():
	ip = request.headers['Cf-Connecting-Ip']
	direct = request.args.get('direction')
	return jsonify(game.player_mine(ip, int(direct)))


@app.route("/p_build", methods=["GET"])
def p_build():
	print("build")
	ip = request.headers['Cf-Connecting-Ip']
	direct = request.args.get('direction')
	block_name = request.args.get('block_name')
	return jsonify(game.player_build(ip, int(direct),block_name))


@app.route("/p_craft", methods=["GET"])
def p_craft():
	ip = request.headers['Cf-Connecting-Ip']
	index = request.args.get('index')
	return jsonify(game.player_craft(ip, int(index)))


@app.route("/get_floor", methods=["GET"])
def get_floor():
	x = int(request.args.get('x'))
	y = int(request.args.get('y'))
	floor = game.map.get_floor(x, y)
	if floor is None:
		return "0"
	return jsonify(floor.block.block_type)

@app.route("/get_block", methods=["GET"])
def get_block():
	x = int(request.args.get('x'))
	y = int(request.args.get('y'))
	block = game.map.get_block(x, y)
	if block is None:
		return "0"
	return jsonify(block.block.block_type)
@app.route("/get_all_blocks", methods=["GET"])
def get_map():
	block_map = {}
	for i in range(20):
		for j in range(20):
			x = i - 10
			y = j - 10
			block = game.map.get_block(x, y)
			if block is None:
				block_map[f"{x}_{y}"]=0
			else:
				block_map[f"{x}_{y}"]=block.block.block_type
	return jsonify(block_map)
@app.route("/get_all_floor", methods=["GET"])
def get_map2():
	block_map = {}
	for i in range(20):
		for j in range(20):
			x = i - 10
			y = j - 10
			block = game.map.get_floor(x, y)
			if block is None:
				block_map[f"{x}_{y}"]=0
			else:
				block_map[f"{x}_{y}"]=block.block.block_type
	return jsonify(block_map)
@app.route("/get_all_players", methods=["GET"])
def get_players():
	retured = []

	for player in game.players:
		retured.append({'Health': player.health,
	                'Hungry': player.hungry,
	                'Inventory': player.inventory,
		                "X": player.x,
		                "Y": player.y})
	return jsonify(retured)
@app.route("/my_player_info", methods=["GET"])
def my_player_info():
	ip = request.headers['Cf-Connecting-Ip']
	player_info = game.get_player_info(ip)
	if player_info is None:
		return "0"
	return jsonify({'Health': player_info.health,
	                'Hungry': player_info.hungry,
	                'X': player_info.x,
	                'Y': player_info.y,
	                'Inventory': player_info.inventory})

@app.route("/get_player", methods=["GET"])
def get_player():
	x = int(request.args.get('x'))
	y = int(request.args.get('y'))
	player = game.get_xy_player(x, y)
	if player is None:
		return "0"
	player_info = game.players[player]
	return jsonify({'Health': player_info.health,
	                'Hungry': player_info.hungry,
	                'Inventory': player_info.inventory})


@app.route("/craft_list", methods=["GET"])
def craft_list():
	return jsonify(all_crafts)


def async_task():
	print("Game recreating....")
	global game
	del(game)

	game = Game()

	print("Game recreated!")


def run_scheduler():
	while True:
		schedule.run_pending()
		time.sleep(5)


async def main():
	schedule.every(6).hours.do(async_task)
	scheduler_thread = threading.Thread(target=run_scheduler)
	scheduler_thread.start()
	app.run()

asyncio.run(main())




