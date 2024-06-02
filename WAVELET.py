import pygame
import random
import math
import json
import os

# Initialize Pygame
pygame.init()

# Define constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BACKGROUND_COLOR = (0, 0, 0)
FPS = 60
LOVE_CLICK_ENERGY = 100  # Increased energy per click
ENERGY_LOSS_RATE = 0.1
LOVE_CLICK_DECAY = 1
FEED_ENERGY_BOOST = 200  # Increased energy per food item
LOVE_CLICK_COOLDOWN = 500  # milliseconds
REACTION_RADIUS = 50
CLICK_ATTRACTION_THRESHOLD = 4
ATTRACTION_RESET_TIME = 3000  # milliseconds
DRIFT_BACK_SPEED = 0.5  # Speed of drifting back to the home position
PAUSE_BEFORE_DRIFT = 2000  # milliseconds
FOOD_DURATION = 120000  # Food item duration in milliseconds
FOOD_APPEAR_INTERVAL = 30000  # Interval at which food appears in milliseconds

# Game modes
GAME_MODES = {
    'Classic': {'energy_loss_rate': 0.1, 'food_appear_interval': 30000},
    'Fast': {'energy_loss_rate': 0.2, 'food_appear_interval': 15000},
    'Long': {'energy_loss_rate': 0.05, 'food_appear_interval': 60000}
}

# Default game mode
current_mode = 'Classic'

# Define colors for moods
MOOD_COLORS = {
    'very happy': (0, 255, 0),
    'happy': (173, 255, 47),
    'neutral': (255, 255, 0),
    'sad': (255, 165, 0),
    'very sad': (255, 0, 0)
}
FOOD_COLOR = (0, 255, 255)  # Cyan color for food

# Define initial state of the life form
home_position = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
life_form = {
    'x': home_position[0],
    'y': home_position[1],
    'energy': 100,
    'mood': 'neutral',
    'size': 5,
    'growth_stage': 1,
    'attracted': False,
    'target_x': home_position[0],
    'target_y': home_position[1],
    'pause_drift': False,
    'last_pause_time': 0,
    'trail': [],
    'food_consumed': 0,
    'food_needed_for_growth': 5,
    'wandering': False
}

# Food item setup
FOOD_SIZE = 10
FOOD_ENERGY = 200  # Increased energy per food item
food_items = []

# Create the game window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Wavelet')

# Load sound effects
love_sound = pygame.mixer.Sound('love_click.wav')
feed_sound = pygame.mixer.Sound('feed.wav')

# Load background music
pygame.mixer.music.load('background_music.wav')
pygame.mixer.music.set_volume(0.2)  # Set volume to 20%

# Load settings
settings_file = 'settings.json'
if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        settings = json.load(f)
    music_enabled = settings.get('music_enabled', True)
    sound_enabled = settings.get('sound_enabled', True)
    always_on_top = settings.get('always_on_top', False)
else:
    music_enabled = True
    sound_enabled = True
    always_on_top = False

if music_enabled:
    pygame.mixer.music.play(-1)  # Loop the music

# Function to save settings
def save_settings():
    settings = {
        'music_enabled': music_enabled,
        'sound_enabled': sound_enabled,
        'always_on_top': always_on_top
    }
    with open(settings_file, 'w') as f:
        json.dump(settings, f)

# Function to generate a random food item
def generate_food():
    x = random.randint(50, WINDOW_WIDTH - 50)
    y = random.randint(50, WINDOW_HEIGHT - 50)
    print(f"Food generated at ({x}, {y})")
    return {'x': x, 'y': y, 'spawn_time': pygame.time.get_ticks(), 'pulse': 0}

# Function to check distance
def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

# Function to display text on the screen
def display_text(text, position, color=(255, 255, 255), align='left'):
    font = pygame.font.SysFont(None, 24)
    img = font.render(text, True, color)
    if align == 'center':
        position = (position[0] - img.get_width() // 2, position[1])
    elif align == 'right':
        position = (position[0] - img.get_width(), position[1])
    window.blit(img, position)

# Function to update mood based on energy
def update_mood(energy):
    if energy > 750:
        return 'very happy'
    elif energy > 500:
        return 'happy'
    elif energy > 250:
        return 'neutral'
    elif energy > 100:
        return 'sad'
    else:
        return 'very sad'

# Function to grow the life form
def grow_life_form(life_form):
    life_form['growth_stage'] += 1
    life_form['size'] += 1  # Increase size by 1 unit for simplicity
    life_form['food_needed_for_growth'] *= 2  # Double the food needed for the next growth

# Function to shrink the life form
def shrink_life_form(life_form):
    if life_form['growth_stage'] > 1:
        life_form['growth_stage'] -= 1
        life_form['size'] -= 1  # Decrease size by 1 unit for simplicity

# Function to toggle always on top
def set_always_on_top(value):
    global window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.NOFRAME if value else 0)
    pygame.display.set_caption('Wavelet')

# Function to display the options menu
def display_options():
    menu_font = pygame.font.SysFont(None, 36)
    options = [
        "Press 'M' to toggle music",
        "Press 'S' to toggle sound",
        "Press 'T' to toggle always on top",
        "Press '1' for Classic mode",
        "Press '2' for Fast mode",
        "Press '3' for Long mode",
        "Press 'ESC' to return to the game"
    ]
    window.fill(BACKGROUND_COLOR)
    for i, option in enumerate(options):
        text_surface = menu_font.render(option, True, (255, 255, 255))
        window.blit(text_surface, (WINDOW_WIDTH // 4, WINDOW_HEIGHT // 4 + i * 40))
    pygame.display.flip()

# Game loop
running = True
clock = pygame.time.Clock()
love_clicks = 0
last_love_click_time = 0
click_count = 0
last_click_time = 0
last_food_spawn_time = pygame.time.get_ticks()
wander_time = pygame.time.get_ticks()
showing_options = False

# Apply initial always on top setting
set_always_on_top(always_on_top)

while running:
    # Handle events
    current_time = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            save_settings()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not showing_options:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dist_to_life_form = distance(mouse_x, mouse_y, life_form['x'], life_form['y'])
                if dist_to_life_form < REACTION_RADIUS:
                    # Within reaction radius
                    love_clicks += 1
                    life_form['energy'] += LOVE_CLICK_ENERGY
                    if life_form['energy'] > 999:
                        life_form['energy'] = 999
                    if sound_enabled:
                        love_sound.play()
                    last_love_click_time = current_time
                    life_form['size'] *= 1.1  # Pulse effect
                    life_form['pause_drift'] = True
                    life_form['last_pause_time'] = current_time
                else:
                    # Outside reaction radius
                    click_count += 1
                    last_click_time = current_time
                    if click_count >= CLICK_ATTRACTION_THRESHOLD:
                        life_form['attracted'] = True
                        life_form['target_x'] = mouse_x
                        life_form['target_y'] = mouse_y
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                music_enabled = not music_enabled
                if music_enabled:
                    pygame.mixer.music.play(-1)  # Ensure music plays if enabled
                else:
                    pygame.mixer.music.stop()
                save_settings()
            elif event.key == pygame.K_s:
                sound_enabled = not sound_enabled
                save_settings()
            elif event.key == pygame.K_t:
                always_on_top = not always_on_top
                set_always_on_top(always_on_top)
                save_settings()
            elif event.key == pygame.K_o:  # Press 'O' to show options
                showing_options = not showing_options
            elif showing_options:
                if event.key == pygame.K_ESCAPE:
                    showing_options = False
                elif event.key == pygame.K_1:
                    current_mode = 'Classic'
                elif event.key == pygame.K_2:
                    current_mode = 'Fast'
                elif event.key == pygame.K_3:
                    current_mode = 'Long'
            elif event.key == pygame.K_f:  # Press 'F' to generate food
                print("F key pressed: Generating food")
                food_items.append(generate_food())

    if showing_options:
        display_options()
        continue

    # Update life form status
    life_form['energy'] -= GAME_MODES[current_mode]['energy_loss_rate']
    if life_form['energy'] <= 0:
        life_form['energy'] = 0
        shrink_life_form(life_form)  # Shrink if energy drops to 0
    elif life_form['energy'] > 999:
        life_form['energy'] = 999

    if love_clicks > 0:
        love_clicks -= LOVE_CLICK_DECAY
    if life_form['size'] > 5:
        life_form['size'] -= 0.1  # Gradually return to normal size after pulsing

    # Update mood based on energy
    life_form['mood'] = update_mood(life_form['energy'])

    # Move towards target if attracted
    if life_form['attracted']:
        step_size = 2  # Speed of movement
        dist_to_target = distance(life_form['x'], life_form['y'], life_form['target_x'], life_form['target_y'])
        if dist_to_target > step_size:
            angle = math.atan2(life_form['target_y'] - life_form['y'], life_form['target_x'] - life_form['x'])
            life_form['x'] += step_size * math.cos(angle)
            life_form['y'] += step_size * math.sin(angle)
        else:
            life_form['attracted'] = False
            click_count = 0

    # Reset attraction if no clicks for a while
    if current_time - last_click_time > ATTRACTION_RESET_TIME:
        life_form['attracted'] = False
        click_count = 0

    # Drift back to home position if not attracted and not paused
    if not life_form['attracted'] and not life_form['pause_drift']:
        dist_to_home = distance(life_form['x'], life_form['y'], home_position[0], home_position[1])
        if dist_to_home > DRIFT_BACK_SPEED:
            angle = math.atan2(home_position[1] - life_form['y'], home_position[0] - life_form['x'])
            life_form['x'] += DRIFT_BACK_SPEED * math.cos(angle)
            life_form['y'] += DRIFT_BACK_SPEED * math.sin(angle)
    elif life_form['pause_drift']:
        if current_time - life_form['last_pause_time'] > PAUSE_BEFORE_DRIFT:
            life_form['pause_drift'] = False

    # Wandering behavior
    if not life_form['attracted'] and not life_form['wandering']:
        if current_time - wander_time > 5000:  # Every 5 seconds
            wander_time = current_time
            random_angle = random.uniform(0, 2 * math.pi)
            random_distance = random.uniform(50, 150)
            life_form['target_x'] = home_position[0] + random_distance * math.cos(random_angle)
            life_form['target_y'] = home_position[1] + random_distance * math.sin(random_angle)
            life_form['wandering'] = True

    if life_form['wandering']:
        step_size = 1  # Speed of wandering
        dist_to_target = distance(life_form['x'], life_form['y'], life_form['target_x'], life_form['target_y'])
        if dist_to_target > step_size:
            angle = math.atan2(life_form['target_y'] - life_form['y'], life_form['target_x'] - life_form['x'])
            life_form['x'] += step_size * math.cos(angle)
            life_form['y'] += step_size * math.sin(angle)
        else:
            life_form['wandering'] = False

    # Clear screen
    window.fill(BACKGROUND_COLOR)

    # Update and draw food items
    for food in food_items[:]:
        food['pulse'] += 0.1
        pulse_radius = FOOD_SIZE + 3 * math.sin(food['pulse'])
        # print(f"Drawing food at ({food['x']}, {food['y']}) with radius {int(pulse_radius)}")
        pygame.draw.circle(window, FOOD_COLOR, (food['x'], food['y']), int(pulse_radius))
        pygame.draw.circle(window, (255, 255, 255), (food['x'], food['y']), FOOD_SIZE, 1)  # Draw outline for visibility
        dist_to_food = distance(food['x'], food['y'], life_form['x'], life_form['y'])
        if dist_to_food < FOOD_SIZE:
            life_form['energy'] += FOOD_ENERGY
            life_form['food_consumed'] += 1
            if life_form['food_consumed'] >= life_form['food_needed_for_growth']:
                grow_life_form(life_form)
                life_form['food_consumed'] = 0  # Reset count after growth
            if life_form['energy'] > 999:
                life_form['energy'] = 999
            if sound_enabled:
                feed_sound.play()
            food_items.remove(food)
        elif current_time - food['spawn_time'] > FOOD_DURATION:
            food_items.remove(food)

    # Generate new food item at intervals
    if current_time - last_food_spawn_time > GAME_MODES[current_mode]['food_appear_interval']:
        print("Generating food at interval")
        food_items.append(generate_food())
        last_food_spawn_time = current_time

    # Draw fading trail
    life_form['trail'].append((life_form['x'], life_form['y']))
    if len(life_form['trail']) > 20 + life_form['growth_stage'] * 10:  # Increase trail length with growth
        life_form['trail'].pop(0)

    for i in range(len(life_form['trail']) - 1):
        pygame.draw.line(window, MOOD_COLORS[life_form['mood']], life_form['trail'][i], life_form['trail'][i + 1], 2)

    # Draw the life form
    pygame.draw.circle(window, MOOD_COLORS[life_form['mood']], (life_form['x'], life_form['y']), int(life_form['size']))

    # Display stats
    display_text(f"Energy: {int(life_form['energy']):03d}", (10, 10), align='left')
    display_text(f"Mood: {life_form['mood'].capitalize()}", (WINDOW_WIDTH // 2, 10), align='center')
    display_text(f"Growth Stage: {life_form['growth_stage']}", (WINDOW_WIDTH - 10, 10), align='right')
    display_text(f"Food Status: {life_form['food_consumed']}/{life_form['food_needed_for_growth']}", (WINDOW_WIDTH - 10, 30), align='right')

    # Display options prompt
    options_text = "Press 'O' for Options"
    options_surface = pygame.font.SysFont(None, 24).render(options_text, True, (255, 255, 255))
    options_rect = options_surface.get_rect(bottomleft=(10, WINDOW_HEIGHT - 10))
    window.blit(options_surface, options_rect)

    # Display current mode
    mode_text = f"Mode: {current_mode}"
    mode_surface = pygame.font.SysFont(None, 24).render(mode_text, True, (255, 255, 255))
    mode_rect = mode_surface.get_rect(bottomright=(WINDOW_WIDTH - 10, WINDOW_HEIGHT - 10))
    window.blit(mode_surface, mode_rect)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(FPS)

pygame.quit()
