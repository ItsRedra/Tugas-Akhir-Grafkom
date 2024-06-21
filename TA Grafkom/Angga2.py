from ursina import *

# Inisialisasi aplikasi Ursina
app = Ursina()

# Membuat entitas background dengan model quad dan tekstur dari 'assets/BG', serta skala dan posisi tertentu
bg = Entity(model='quad', texture='assets/BG', scale=36, z=1)

# Mengaktifkan mode fullscreen pada jendela aplikasi
window.fullscreen = True

# Membuat entitas player dengan animasi dari 'assets/player', kolider berbentuk box, dan posisi awal di y=5
player = Animation('assets/player', collider='box', y=5)

# Membuat entitas fly (musuh) dengan model kubus, tekstur dari 'assets/fly1', kolider berbentuk box, skala 2, dan posisi awal di x=20, y=-10
fly = Entity(model='cube', texture='assets/fly1', collider='box', scale=2, x=20, y=-10)

# Daftar untuk menyimpan entitas musuh yang muncul di layar
flies = []

# Skor awal pemain
score = 0

# Kesehatan awal pemain
health = 3

# Kecepatan awal musuh
enemy_speed = 4

# Memuat efek suara untuk berbagai aksi dalam game
shoot_sound = Audio('assets/shoot.wav', autoplay=False)
enemy_dead_sound = Audio('assets/enemy_dead.wav', autoplay=False)
player_damage_sound = Audio('assets/player_damage.wav', autoplay=False)
game_over_sound = Audio('assets/game_over.wav', autoplay=False)

# Memutar background music (BGM) secara berulang
bgm = Audio('assets/bgm.wav', loop=True, autoplay=True)

# Menampilkan teks skor dengan warna putih pada posisi (0, 0.45) dengan skala 2 dan origin di (0, 0)
score_text = Text(text=f'Score: {score}', position=(0, 0.45), origin=(0, 0), scale=2, color=color.white)

# Menampilkan teks kesehatan dengan warna putih pada posisi (0, 0.35) dengan skala 2 dan origin di (0, 0)
health_text = Text(text=f'Health: {health}', position=(0, 0.35), origin=(0, 0), scale=2, color=color.white)

# Menampilkan teks "Game Over" dengan warna merah dan skala 3, tapi awalnya tidak diaktifkan (enabled=False)
game_over_text = Text(text='Game Over', origin=(0, 0), scale=3, color=color.red, enabled=False)

# Tombol untuk restart dan quit, tapi awalnya tidak diaktifkan (enabled=False)
restart_button = Button(text='Restart', position=(0, -0.1), scale=(0.2, 0.1), color=color.azure, enabled=False)
quit_button = Button(text='Quit', position=(0, -0.3), scale=(0.2, 0.1), color=color.red, enabled=False)

# Variabel untuk menentukan apakah permainan sedang berhenti
game_paused = False

# Variabel untuk menentukan apakah player sedang dalam keadaan tak tersentuh (invincible)
invincible = False

# Variabel untuk menentukan apakah player dapat menembak saat ini
can_shoot = True

# Fungsi untuk membuat musuh baru (fly) muncul setiap 1 detik
def newFly():
    if not game_paused:
        new = duplicate(fly, y=-5 + (5124 * time.dt) % 15)
        flies.append(new)
        invoke(newFly, delay=1)

# Memanggil fungsi newFly untuk pertama kali saat aplikasi dijalankan
newFly()

# Mengatur kamera ke mode ortografik dan menentukan fov (field of view) sebesar 20
camera.orthographic = True
camera.fov = 20

# Fungsi untuk menghentikan permainan dan menampilkan teks "Game Over" ketika kondisi game over terpenuhi
def game_over():
    global game_paused
    game_paused = True
    game_over_sound.play()
    game_over_text.enabled = True
    restart_button.enabled = True
    quit_button.enabled = True

# Fungsi untuk memulai ulang permainan
def restart_game():
    global score, health, game_paused, invincible, can_shoot, enemy_speed
    score = 0
    health = 3
    game_paused = False
    invincible = False
    can_shoot = True
    enemy_speed = 4
    score_text.text = f'Score: {score}'
    health_text.text = f'Health: {health}'
    game_over_text.enabled = False
    restart_button.enabled = False
    quit_button.enabled = False
    for fly in flies:
        destroy(fly)
    flies.clear()
    player.position = (0, 5)
    newFly()

# Fungsi untuk membuat player menjadi tak tersentuh (invincible) selama 0.7 detik setelah terkena musuh
def make_invincible():
    global invincible
    invincible = True
    invoke(end_invincible, delay=0.7)

# Fungsi untuk mengakhiri status tak tersentuh (invincible) pada player
def end_invincible():
    global invincible
    invincible = False

# Fungsi untuk membuat efek kedipan (blink) pada player saat tak tersentuh (invincible)
def blink():
    if not invincible:
        return
    player.visible = not player.visible
    invoke(blink, delay=0.1)

# Fungsi untuk menampilkan efek ledakan pada musuh
def explode(entity):
    entity.blink_speed = 0.1
    def blink_explosion():
        if entity:
            entity.visible = not entity.visible
            invoke(blink_explosion, delay=entity.blink_speed)
    blink_explosion()
    destroy(entity, delay=0.8)

# Fungsi utama yang dijalankan setiap frame untuk mengupdate permainan
def update():
    global score, health, game_paused, invincible, enemy_speed
    if game_paused:
        return

    # Kontrol pergerakan player dengan tombol w, a, s, d
    player.y += held_keys['w'] * 6 * time.dt
    player.y -= held_keys['s'] * 6 * time.dt
    player.x -= held_keys['a'] * 6 * time.dt
    player.x += held_keys['d'] * 6 * time.dt

    # Mencegah player keluar dari batas layar
    if player.x < -camera.fov / 2:
        player.x = -camera.fov / 2
    if player.x > camera.fov / 2:
        player.x = camera.fov / 2
    if player.y < -camera.fov / 2:
        player.y = -camera.fov / 2
    if player.y > camera.fov / 2:
        player.y = camera.fov / 2

    # Mengatur rotasi player berdasarkan input tombol w dan s
    a = held_keys['w'] * -20
    b = held_keys['s'] * 20
    if a != 0:
        player.rotation_z = a
    else:
        player.rotation_z = b

    # Loop untuk mengupdate posisi musuh (fly) dan mendeteksi tabrakan dengan player atau peluru
    for fly in flies:
        fly.x -= enemy_speed * time.dt
        touch = fly.intersects()
        if touch.hit:
            flies.remove(fly)
            # Jika musuh (fly) menabrak player dan player tidak dalam keadaan invincible
            if touch.entity == player and not invincible:
                health -= 1
                health_text.text = f'Health: {health}'
                player_damage_sound.play()
                make_invincible()
                blink()
                # Jika kesehatan (health) player habis
                if health <= 0:
                    game_over()
            # Jika musuh (fly) tertembak oleh peluru
            else:
                score += 1
                score_text.text = f'Score: {score}'
                enemy_dead_sound.play()
                # Meningkatkan kecepatan musuh setiap 10 poin
                if score % 10 == 0:
                    enemy_speed += 1
                # Membuat efek ledakan pada posisi musuh (fly)
                explosion = Entity(model='quad', texture='assets/explosion', position=fly.position, scale=2)
                explode(explosion)
            destroy(fly)

    # Deteksi tabrakan antara player dan musuh (fly)
    t = player.intersects()
    if t.hit and t.entity.scale == 2 and not invincible:
        health -= 1
        health_text.text = f'Health: {health}'
        player_damage_sound.play()
        make_invincible()
        blink()
        # Jika kesehatan (health) player habis
        if health <= 0:
            game_over()

# Fungsi untuk mengaktifkan kembali kemampuan menembak player setelah jeda waktu
def reset_can_shoot():
    global can_shoot
    can_shoot = True

# Fungsi untuk mengatur input dari keyboard
def input(key):
    global can_shoot, score, enemy_speed
    if game_paused:
        return

    # Jika tombol spasi ditekan dan player dapat menembak saat ini
    if key == 'space' and can_shoot:
        shoot_sound.play()
        # Membuat entitas peluru (bullet) pada posisi player
        bullet = Entity(y=player.y, x=player.x + 1, model='cube', scale=1, texture='assets/Bullet', collider='box')
        bullet.animate_x(30, duration=2, curve=curve.linear)
        
        # Fungsi untuk mengupdate status tabrakan peluru dengan musuh
        def bullet_update():
            global score, enemy_speed
            touch = bullet.intersects()
            if touch.hit and touch.entity in flies:
                explosion_position = touch.entity.position
                flies.remove(touch.entity)
                destroy(touch.entity)
                destroy(bullet)
                score += 1
                score_text.text = f'Score: {score}'
                enemy_dead_sound.play()
                # Meningkatkan kecepatan musuh setiap 10 poin
                if score % 10 == 0:
                    enemy_speed += 1
                # Membuat efek ledakan pada posisi musuh (fly)
                explosion = Entity(model='quad', texture='assets/explosion', position=explosion_position, scale=2)
                explode(explosion)
        bullet.update = bullet_update
        invoke(destroy, bullet, delay=2)
        can_shoot = False
        invoke(reset_can_shoot, delay=1)

# Menambahkan fungsi untuk tombol restart dan quit
restart_button.on_click = restart_game
quit_button.on_click = application.quit

# Menjalankan aplikasi Ursina
app.run()
