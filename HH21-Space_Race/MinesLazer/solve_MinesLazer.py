from pwn import *

def get_next_move(x, y):
	if x < 7:
		x += 1
	else:
		x = 0
		y += 1
	return x, y


def board_to_binary(board):
	striped_board = board.replace('[', '').replace(']', '').replace('\r\n', '')
	return striped_board.replace('Ｄ', '1').replace('Ｘ', '1').replace('＿', '0')[::-1]


def rand_int_to_binary_board(next_board_rand):
	binary_board = []
	binary = f'{int(next_board_rand, 10):0>64b}'[::-1]
	for i in range(0, 64, 8):
		binary_board.append(binary[i:i+8])
	return binary_board


def binary_to_board(binary_board):
	board = ''
	for line in binary_board:
		board += '[' + line + ']\n'
	return board


def binary_to_moves(binary_board):
	moves = []
	for y, byte in enumerate(binary_board):
		for x, bit in enumerate(byte):
			if bit == '1':
				moves.append(str(x) + ',' + str(y))
	return moves


def solve_board(moves):
	client = remote('localhost', 1234)
	for move in moves:
		log.info("move: %s", move)
		# log.info(client.sendlineafter('Enter laser position: ', move))
		client.sendlineafter('Enter laser position: ', move)
		answer = client.recvlineS()
		log.info(answer)
		if 'Yikes' in answer:
			client.recvlineS()
			board = client.recvallS()
			log.info(board)

	log.info(client.recvallS())
	client.close()

# https://github.com/lemire/crackingxoroshiro128plus
def get_next_mines_rand(hex_list_string, mines_rand_hex):
	command = "python2 xoroshiftall.py " + hex_list_string + " | grep -A 3 " + mines_rand_hex
	next_board_rand_list = process(command, shell=True).recvallS().split("\n")[0:4]
	log.info("next board random numbers: %s", next_board_rand_list[2:])
	return next_board_rand_list[3]


def get_board_rand_hex():
	client = remote('localhost', 1234)
	game_over = False
	x = 0
	y = 0
	mines_rand_hex = ''
	while not game_over:
		log.info("move: %i,%i", x, y)
		log.info(client.sendlineafter('Enter laser position: ', str(x) + ',' + str(y)))
		x, y = get_next_move(x, y)
		answer = client.recvlineS()
		log.info(answer)
		if 'Yikes' in answer:
			log.info(client.recvlineS())
			board = client.recvallS()
			log.info(board)
			game_over = True
			binary_board = board_to_binary(board)
			log.info("mines random number binary: %s", binary_board)
			log.info("mines random number: %s", int(binary_board, 2))
			mines_rand_hex = '0x' + p64(int(binary_board, 2), signed='unsigned', endian='big').hex()
	client.close()
	return mines_rand_hex


mines_rand_hex_list = []
boards_count = 4

for i in range(0, boards_count):
	mines_rand_hex_list.append(get_board_rand_hex())

hex_list_string = ' '.join(mines_rand_hex_list)
log.info("mines random numbers: %s", hex_list_string)

next_board_rand = get_next_mines_rand(hex_list_string, mines_rand_hex_list[-1])
binary_board = rand_int_to_binary_board(next_board_rand)
log.info("next board:\n%s", binary_to_board(binary_board))
moves = binary_to_moves(binary_board)
log.info("next board moves:\n%s", moves)
solve_board(moves)
