import pygame
from sys import exit
import numpy as np
from collections import defaultdict
import random

##PARAMETERS
width = 720
height = 1080
columns = 18
background_color = 'black'
starting_drop_rate = 50
drop_timer = 0
cooldown_rate = 10
block_border_color = 'black'
block_border_thickness = 1
ground_color = 'white'
score_color = 'black'
title = 'Tetris!!'

## !!!
ground_height = height * .10
default_drop_rate = starting_drop_rate / 1000
double_drop_rate = starting_drop_rate / 500
drop_rate = default_drop_rate
input_cooldown = cooldown_rate
block_dict = defaultdict(list)
unit = int(width / columns)
block_size = [unit,unit]
row_indexer, row_indexer_max, column_indexer_max = 0,0,0
double_drop_rate = drop_rate * 2
column_count = columns - 2
block_id = 0
stored_piece = None
swapped_this_turn = False
lock_delay_frames = 18
lock_timer = 0
moved_this_frame = False
touching_surface = False
score = 0
cleared_rows = 0

##GRID SETUP
unit = int(width / columns)
playable_height = height - ground_height
block_matrix_height = int(playable_height / unit) + 2
column_indexer =  int(column_count / 2) - 2


##BOARD MATRIX
block_array_len = block_matrix_height * (column_count)
block_matrix = np.arange(block_array_len)
block_matrix = block_matrix.reshape(block_matrix_height, (column_count))
block_matrix.fill(0)

# stores permanent block colors (None for empty / falling)
color_matrix = np.empty_like(block_matrix, dtype=object)
color_matrix.fill(None)

##GROUND RECTANGLE
ground_surface = pygame.Surface((width,ground_height))
ground_surface.fill(ground_color)
ground_rect = ground_surface.get_rect(topleft = (0,height-ground_height))

y_offset = ground_rect.top - (block_matrix_height * unit)

##PIECES !!!
class Piece:
    def __init__(self,shape, id, color):
        self.shape = shape
        self.id = id
        self.color = color

rhode_island_z_shape = [0,0,0,0,
                        0,1,1,0,
                        1,1,0,0,
                        0,0,0,0]
rhode_island_z_shape = np.reshape(rhode_island_z_shape, (4,4))
rhode_island_z = Piece(rhode_island_z_shape, 1,'light green')

orange_ricky_shape = [0,1,1,0,
                     0,0,1,0,
                     0,0,1,0,
                     0,0,0,0]
orange_ricky_shape = np.reshape(orange_ricky_shape, (4,4))
orange_ricky = Piece(orange_ricky_shape, 2, 'orange')

blue_ricky_shape =  [0,1,1,0,
                     0,1,0,0,
                     0,1,0,0,
                     0,0,0,0]
blue_ricky_shape = np.reshape(blue_ricky_shape, (4,4))
blue_ricky = Piece(blue_ricky_shape, 3, 'blue')

cleveland_z_shape = [0,0,0,0,
                     1,1,0,0,
                     0,1,1,0,
                     0,0,0,0]
cleveland_z_shape = np.reshape(cleveland_z_shape, (4,4))
cleveland_z = Piece(cleveland_z_shape, 4, 'red')

smash_boy_shape =   [0,0,0,0,
                     0,1,1,0,
                     0,1,1,0,
                     0,0,0,0]
smash_boy_shape = np.reshape(smash_boy_shape, (4,4))
smash_boy = Piece(smash_boy_shape, 5, 'yellow')

teewee_shape =      [0,0,0,0,
                     0,0,1,0,
                     0,1,1,0,
                     0,0,1,0]
teewee_shape = np.reshape(teewee_shape, (4,4))
teewee = Piece(teewee_shape, 6, 'purple')

hero_shape =        [0,0,1,0,
                     0,0,1,0,
                     0,0,1,0,
                     0,0,1,0]
hero_shape = np.reshape(hero_shape, (4,4))
hero = Piece(hero_shape, 7, 'light blue')

tetris_pieces_list = [rhode_island_z, orange_ricky,blue_ricky,cleveland_z,smash_boy,teewee,hero]

def assign_random_piece():
    global piece_assigner
    global active_piece
    global piece_h
    global piece_w
    global piece_assigner
    global player_block_color
    piece_assigner = random.randint(1,7)
    for t in tetris_pieces_list:
        if t.id == piece_assigner:
          active_piece = t
          piece_h, piece_w = active_piece.shape.shape
          player_block_color = active_piece.color
        
assign_random_piece()

def get_lowest_occupied_row(piece_shape):
    ones = np.where(piece_shape == 1)
    return int(np.max(ones[0])) if len(ones[0]) > 0 else 0

def stamp_piece_to_matrix(value):
    global block_matrix
    global color_matrix

    row_start = row_indexer
    col_start = column_indexer
    row_end = row_start + piece_h
    col_end = col_start + piece_w

    matrix_row_start = max(row_start, 0)
    matrix_col_start = max(col_start, 0)
    matrix_row_end = min(row_end, block_matrix_height)
    matrix_col_end = min(col_end, column_count)

    if matrix_row_start >= matrix_row_end or matrix_col_start >= matrix_col_end:
        return

    piece_row_start = matrix_row_start - row_start
    piece_col_start = matrix_col_start - col_start
    piece_row_end = piece_row_start + (matrix_row_end - matrix_row_start)
    piece_col_end = piece_col_start + (matrix_col_end - matrix_col_start)

    matrix_slice = block_matrix[matrix_row_start:matrix_row_end, matrix_col_start:matrix_col_end]
    mask = (active_piece.shape[piece_row_start:piece_row_end, piece_col_start:piece_col_end] == 1)

    if value == 1:
        matrix_slice[mask & (matrix_slice == 0)] = 1
    else:
        matrix_slice[mask] = value

    if value == 2: ##IF IT's A PERMANENT BLOCK, STORE THE COLOR
        color_matrix[matrix_row_start:matrix_row_end, matrix_col_start:matrix_col_end][mask] = active_piece.color


def increment_player_indexer(): ##Drop the block at constant rate. Double speed if holding UP
    global row_indexer
    global drop_timer
    global touching_surface

    if touching_surface:
        row_indexer = int(drop_timer)
        return

    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            drop_rate = double_drop_rate
    else:
        drop_rate = default_drop_rate
    
    drop_timer += drop_rate
    row_indexer = int(drop_timer)

    lowest_occupied_row = get_lowest_occupied_row(active_piece.shape)
    max_row_for_mask = block_matrix_height - 1 - lowest_occupied_row
    if row_indexer > max_row_for_mask:
        row_indexer = max_row_for_mask
        drop_timer = row_indexer

def rotate_piece():
    global block_matrix
    global piece_h
    global piece_w
    global column_indexer

    block_matrix[block_matrix == 1] = 0  ##clear falling piece so we only collide with 2s

    old_shape = active_piece.shape
    new_shape = np.rot90(old_shape, -1)  ##rotate clockwise

    rotation_is_valid = True

    for r in range(4):
        for c in range(4):

            if new_shape[r, c] == 1:

                board_r = row_indexer + r
                board_c = column_indexer + c

                if board_c < 0: ##left side of arena
                    active_piece.shape = new_shape
                    column_indexer = column_indexer + 1
                    break
               
                if board_c >= column_count: ##right side of arena
                    active_piece.shape = new_shape
                    column_indexer = column_indexer - 1
                    break

                if board_r < 0:
                    rotation_is_valid = False
                    break

                try:
                    if block_matrix[board_r, board_c] == 2:
                        rotation_is_valid = False
                        break
                except IndexError:
                    rotation_is_valid = False

        if rotation_is_valid == False:
            break

    if rotation_is_valid:
        active_piece.shape = new_shape
        piece_h, piece_w = active_piece.shape.shape
        return True

    active_piece.shape = old_shape
    piece_h, piece_w = active_piece.shape.shape
    stamp_piece_to_matrix(1)  ##re-stamp so it shows up again
    return False

def render_held_piece():
    global active_piece
    if stored_piece != None:
        preview_x = 50
        preview_y = height - (ground_height - 5) ##create padding for held block on bottom of screen
        color = stored_piece.color

        for r in range(stored_piece.shape.shape[0]):
            for c in range(stored_piece.shape.shape[1]):
                if stored_piece.shape[r, c] == 1:
                    held_surf = pygame.Surface([block_size[0] *.5, block_size[0] *.5])
                    held_surf.fill(color)
                    pygame.draw.rect(held_surf, block_border_color, held_surf.get_rect(), block_border_thickness)

                    held_surf_x = preview_x + (c * block_size[0] *.5)
                    held_surf_y = preview_y + (r * block_size[1] *.5)

                    screen.blit(held_surf, (held_surf_x, held_surf_y))

def hold_piece():
    global stored_piece
    global active_piece
    global swapped_this_turn
    if not swapped_this_turn:
        if stored_piece == None: ##store piece
            stored_piece = active_piece
            assign_random_piece()
            reset_player_block()
            swapped_this_turn = True
            render_held_piece()
            
        else: ## swap piece
            new_stored = active_piece
            active_piece = stored_piece
            stored_piece = new_stored
            reset_player_block()
            swapped_this_turn = True
            render_held_piece()

def game_over():
    global score
    global block_matrix
    global stored_piece
    global cleared_rows
    block_matrix.fill(0)
    score = 0
    stored_piece = None
    cleared_rows = 0
    print('game over')

def reset_player_block():
    global block_id
    global swapped_this_turn
    global drop_timer
    global lock_timer
    global touching_surface
    global column_indexer
    global cleared_rows
    global starting_drop_rate
    global default_drop_rate
    global double_drop_rate
    drop_timer = 0 #sends player to top
    if row_indexer == 0:
        game_over()
    lock_timer = 0
    touching_surface = False
    column_indexer = int(column_count / 2) - 2
    swapped_this_turn = False

    if cleared_rows >= 10: ##GRADUALLY INCREASE DROP SPEEDS BASED ON NUMBER OF CLEARED ROWS
        default_drop_rate = starting_drop_rate / 800
        double_drop_rate = starting_drop_rate / 400
    if cleared_rows >= 20:
        default_drop_rate = starting_drop_rate / 700
        double_drop_rate = starting_drop_rate / 350
    if cleared_rows >= 30:
        default_drop_rate = starting_drop_rate / 600
        double_drop_rate = starting_drop_rate / 300
    if cleared_rows >= 40:
        default_drop_rate = starting_drop_rate / 500
        double_drop_rate = starting_drop_rate / 250
    if cleared_rows >= 50:
        default_drop_rate = starting_drop_rate / 400
        double_drop_rate = starting_drop_rate / 200
    if cleared_rows >= 60:
        default_drop_rate = starting_drop_rate / 300
        double_drop_rate = starting_drop_rate / 150


##UPDATE BOARD BASED ON MATRIX
def update_board():
    global block_id
    global score
    block_id = 0
    for row, row_values in enumerate(block_matrix):
        for col in range((column_count)):
            if row_values[col] == 1 or row_values[col] == 2:
                x_pos = (col + 1) * unit
                y_pos = ((row * unit) + y_offset)
                block_coords = [x_pos,y_pos]
                surf = pygame.Surface(block_size)

                if row_values[col] == 1:
                    surf.fill(player_block_color)
                else:
                    perm_color = color_matrix[row, col]
                    surf.fill(perm_color)

                pygame.draw.rect(surf,block_border_color, surf.get_rect(), block_border_thickness) ## add border to block 
                rect = surf.get_rect(topleft = (block_coords))
                block_dict[block_id] = [surf,rect]
                block_id = block_id + 1

    screen.fill(background_color) ##blit everything so it shows up in pygame
    for i in block_dict:
        screen.blit(block_dict[i][0], block_dict[i][1])

    screen.blit(ground_surface,ground_rect)
    #print('board state \n', block_matrix)
    screen.blit(text_surface, (width - (width * .15),height - ground_height * .85))
    render_held_piece()


##CLEAR SURRONDING MATRIX VALUES WHILE PLAYER DROPS
def clear_prev_pos():
    global row_indexer_max, column_indexer_max

    block_matrix[block_matrix == 1] = 0 ## clear out the matrix of old values from falling block

    row_indexer_max = row_indexer + piece_h
    column_indexer_max = column_indexer + piece_w

    stamp_piece_to_matrix(1)

##BOTTOM OF MATRIX CHECKER, PERMANENT BLOCK CHECKER, RETURN TO TOP IF PRESENT
def check_for_obstacle():
    global drop_timer
    global row_indexer
    global active_piece
    global player_block_color
    global piece_assigner
    global column_indexer
    global lock_timer
    global moved_this_frame
    global touching_surface

    lowest_occupied_row = get_lowest_occupied_row(active_piece.shape)

    touching_bottom = (row_indexer + lowest_occupied_row + 1 >= block_matrix_height)

    perm_block_present = False
    
    for c in range(piece_w): ##CHeck the value below the lowest 1 in each column
        col_ones = np.where(active_piece.shape[:, c] == 1)[0]

        if len(col_ones) == 0:
            continue

        bottom_r = int(np.max(col_ones))

        check_r = row_indexer + bottom_r + 1
        check_c = column_indexer + c

        if 0 <= check_r < block_matrix_height and 0 <= check_c < column_count:
            if block_matrix[check_r, check_c] == 2:
                perm_block_present = True
                break

    touching_surface = touching_bottom or perm_block_present

    if touching_bottom:
        row_indexer = block_matrix_height - 1 - lowest_occupied_row
        drop_timer = row_indexer

    if perm_block_present:
        drop_timer = row_indexer

    if touching_surface:
        if moved_this_frame:
            lock_timer = 0
        else:
            lock_timer += 1

        if lock_timer >= lock_delay_frames:
            block_matrix[block_matrix == 1] = 0
            stamp_piece_to_matrix(2)
            reset_player_block()
            increment_score()
            assign_random_piece()
            clear_completed_rows()
            return
    else:
        lock_timer = 0

def clear_completed_rows():
    global block_matrix
    global color_matrix
    global text_surface
    global cleared_rows

    for index, i in enumerate(block_matrix):
        global score
        checker = True
        for j in i:
            if j == 0:
                checker = False
        if checker:
            block_matrix = np.delete(block_matrix,index,axis=0)
            block_matrix = np.vstack([np.zeros((1, block_matrix.shape[1]), dtype=block_matrix.dtype), block_matrix])
            color_matrix = np.delete(color_matrix, index, axis=0)
            color_matrix = np.vstack([np.full((1, color_matrix.shape[1]), None, dtype=object), color_matrix])
            score = score + 10
            text_surface = my_font.render(str(score), False, score_color)
            cleared_rows = cleared_rows + 1
            print(cleared_rows)

    block_dict.clear()

def increment_score():
    global text_surface
    global score
    score = score + 1
    text_surface = my_font.render(str(score), True, score_color)

        
## GAME RUN
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption(title)
clock = pygame.time.Clock()
pygame.font.init()
my_font = pygame.font.SysFont('Arial',30)
text_surface = my_font.render(str(score), True, score_color)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

##CONTROLS AND INPUT COOLDOWN
    keys = pygame.key.get_pressed()
    moved_this_frame = False

    if input_cooldown  == 0:
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            block_matrix[block_matrix == 1] = 0 #remove the falling block so we can only hit twos

            can_move_left = True

            for r in range(piece_h):
                for c in range(piece_w):
                    if active_piece.shape[r, c] == 1:

                        check_r = row_indexer + r
                        check_c = column_indexer + c - 1

                        if check_c < 0:
                            can_move_left = False
                            break

                        if 0 <= check_r < block_matrix_height:
                            if block_matrix[check_r, check_c] == 2:
                                can_move_left = False
                                break

                if not can_move_left:
                    break

            if can_move_left:
                column_indexer -= 1
                moved_this_frame = True

            input_cooldown = cooldown_rate

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            block_matrix[block_matrix == 1] = 0  # remove the falling block so we can only hit twos

            can_move_right = True
            matrix_w = block_matrix.shape[1]  # number of columns

            for r in range(piece_h):
                for c in range(piece_w):
                    if active_piece.shape[r, c] == 1:

                        check_r = row_indexer + r
                        check_c = column_indexer + c + 1
                        if check_c >= matrix_w:
                            can_move_right = False
                            break

                        if 0 <= check_r < block_matrix_height:
                            if block_matrix[check_r, check_c] == 2:
                                can_move_right = False
                                break

                if not can_move_right:
                    break

            if can_move_right:
                column_indexer += 1
                moved_this_frame = True

            input_cooldown = cooldown_rate

        if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_j] or keys[pygame.K_f]:
            rotated = rotate_piece()
            if rotated:
                moved_this_frame = True
            input_cooldown = cooldown_rate * 2

        if keys[pygame.K_SPACE]:
            hold_piece()
            input_cooldown = cooldown_rate
    
    if input_cooldown > 0: ##run input cooldown timer
        input_cooldown = input_cooldown - 1

#### MAIN LOOP -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    increment_player_indexer()
    clear_prev_pos()
    check_for_obstacle()
    update_board()
### -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    pygame.display.update()
    clock.tick(120)