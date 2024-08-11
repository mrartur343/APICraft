import requests, typing

class P:
	def __init__(self, health,hungry,x,y,inventory):
		self.inventory: typing.Dict[str,int] = inventory
		self.hungry = hungry
		self.health = health
		self.y = y
		self.x = x
def player_move(direct):
	r = requests.get(f'http://localhost/p_move?direction={direct}')
	return r.json()
def player_mine(direct):
	r = requests.get(f'http://localhost/p_mine?direction={direct}')
	return r.json()

def player_build(direct,block_name):
	r = requests.get(f'http://localhost/p_build?direction={direct}&block_name={block_name}')
	return r.json()
def player_craft(index):
	r = requests.get(f'http://localhost/p_craft?index={index}')
	return r.json()
def get_player_info():
	r = requests.get(f'http://localhost/my_player_info')
	p_info_d = r.json()
	return P(p_info_d['Health'],p_info_d['Hungry'],p_info_d['X'],p_info_d['Y'],p_info_d['Inventory'])
def get_xy_player(x,y):
	r = requests.get(f'http://localhost/get_player?x={x}&y={y}')
	p_info_d = r.json()
	return p_info_d
def get_xy_block(x,y):
	r = requests.get(f'http://localhost/get_block?x={x}&y={y}')
	p_info_d = r.json()
	return p_info_d
def get_all_map_blocks():
	r = requests.get(f'http://localhost/get_all_blocks')
	p_info_d = r.json()
	return p_info_d
def get_all_map_floor():
	r = requests.get(f'http://localhost/get_all_floor')
	p_info_d = r.json()
	return p_info_d
def get_all_players():
	r = requests.get(f'http://localhost/get_all_players')
	p_info_d = r.json()
	return p_info_d
def get_xy_floor(x,y):
	r = requests.get(f'http://localhost/get_floor?x={x}&y={y}')
	p_info_d = r.json()
	return p_info_d
player_move(1)

direct = None

while direct != 'end':
	all_map_blocks = get_all_map_blocks()
	all_map_floor = get_all_map_floor()
	all_players = get_all_players()
	player_info = get_player_info()
	players_by_xy = {}
	for p in all_players:
		players_by_xy[f"{p['X']}_{p['Y']}"] = p
	map_listed: typing.List[typing.List[str]] = []
	for i in range(9):
		line = []
		for j in range(9):
			x = player_info.x+j-4
			y = player_info.y+i-4
			if f"{x}_{y}" in players_by_xy:
				player=players_by_xy[f"{x}_{y}"]
			else:
				player=0
			if player  == 0:
				block = all_map_blocks[f"{x}_{y}"]
				if block == 0:
					floor = all_map_floor[f"{x}_{y}"]
					if floor  == 0:
						line.append(' ')
					elif x==5 and y==0:
						line.append('=')
					elif floor == "stone_floor":
						line.append('+')
					elif floor == "grass_floor":
						line.append('-')
					else:
						line.append(floor[0])
				else:
					line.append(block[0])
			else:
				line.append('P')
		map_listed.append(line)

	map_str: str = ''
	for line in map_listed:
		for s in line:
			map_str += s + ' '
		map_str += '\n'
	print(map_str)
	print(f"x: {player_info.x} y: {player_info.y}")
	print(f"HeP: {player_info.health} HuP: {player_info.hungry}")
	print(player_info.inventory)

	direct_str = input("Do: ")
	if direct_str in ['0', '1', '2', '3']:
		player_move(int(direct_str))
	elif direct_str.startswith('m'):
		player_mine(int(direct_str.split('m')[1]))
	elif direct_str.startswith('c'):
		player_craft(int(direct_str.split('c')[1]))
	elif direct_str.startswith('/'):
		player_build(int(direct_str.split('/')[1]),direct_str.split('/')[2])

