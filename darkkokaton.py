import math
import os
import random
import sys
import time
import pygame as pg


WIDTH, HEIGHT = 1600, 900  # ゲームウィンドウの幅，高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct:pg.Rect) -> tuple[bool, bool]:
    """
    Rectの画面内外判定用の関数
    引数：こうかとんRect，または，爆弾Rect，またはビームRect
    戻り値：横方向判定結果，縦方向判定結果（True：画面内／False：画面外）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:  # 横方向のはみ出し判定
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,
            (+1, -1): img, 
            (0, -1): img, 
            (-1, -1): img,
            (-1, 0): img,  
            (-1, +1): img, 
            (0, +1): img,
            (+1, +1): img, 
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.health = 2


    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        cur_speed = self.speed
        if key_lst[pg.K_LSHIFT]:
            cur_speed = 20
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(cur_speed*sum_mv[0], cur_speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam0(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = (+1, 0)
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam1(pg.sprite.Sprite):
    """
    チャージビームSurfaceを生成する
    """
    def __init__(self, bird: Bird):
        """
        チャージビーム画像Surfaceを生成する
        引数はbeam0クラスの初期化メソッドと同様
        """
        super().__init__()
        self.vx, self.vy = (+1, 0)
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/charge_shot.png"), angle, 0.5)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 5

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if self.rect.centerx > WIDTH + 100:
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH, random.randint(0, HEIGHT)
        self.vx = -13
        self.bound = random.randint(250, WIDTH-100)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vxに基づき移動（左方向）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centerx < self.bound:
            self.vx = 0
            self.state = "stop"
        self.rect.centerx += self.vx


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Mode:
    """
    ビームの状態を表示するクラス
    """
    def __init__(self, mode):
        """
        現在のビームの状態に応じて表示内容を変更する
        引数 mode：ビームの状態を表す
        """
        self.mode = mode
        if mode == 0:
            self.font = pg.font.Font(None, 45)
            self.color = (0, 0, 0)
            self.value = 0
            self.image = self.font.render("Beam : Normal", 0, self.color)
            self.rect = self.image.get_rect()
            self.rect.center = WIDTH-150, HEIGHT-30
        elif mode == 1:
            self.font = pg.font.Font(None, 45)
            self.color = (0, 0, 0)
            self.image = self.font.render("Beam : Charge", 0, self.color)
            self.rect = self.image.get_rect()
            self.rect.center = WIDTH-150, HEIGHT-30

    def update(self, screen:pg.Surface):
        screen.blit(self.image, self.rect)


class Condition:
    """
    チャージビームのチャージ状態の表示
    """
    def __init__(self, mode=0):
        """
        チャージビームを打つ状態のときのみチャージ状態を表示する
        引数 mode：ビームの状態を表す
        """
        self.mode = mode
        if mode == 1:
            self.font = pg.font.Font(None, 40)
            self.color = (251, 224, 0)
            self.value = 0
            self.txt = self.font.render("Chrge OK!", 0, self.color)
            self.rect = self.txt.get_rect()
            self.rect.center = WIDTH-150, HEIGHT-60

        else:
            self.font = pg.font.Font(None, 45)
            self.color = (251, 224, 0)
            self.txt = self.font.render("Chrge OK!", 0, self.color)
            self.rect = self.txt.get_rect()
            self.rect.center = -100, -100

    def update(self, screen:pg.Surface):
        screen.blit(self.txt, self.rect)


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    bg_img2 = bg_img
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    beams_c = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()

    shield = pg.sprite.Group()
    beam_mode = 0  # ショットの種類に関する変数
    k_health = bird.health  #birdクラスの中のhealthを呼び出す
    health_img = pg.transform.rotozoom(pg.image.load(f"fig/health.png"), 0, 0.1)
    nohealth_img = pg.transform.rotozoom(pg.image.load(f"fig/nohealth.png"), 0, 0.385)
    tmr = 0
    ct_charge = 0  # チャージビームの時間計測
    clock = pg.time.Clock()

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_c:      # "c"キー押下でビームの切り替えを行う
                beam_mode += 1
                if beam_mode >= 2:
                    beam_mode = 0

            if beam_mode == 0:
                Bmode = Mode(beam_mode)
                condition_c = Condition()
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    beams.add(Beam0(bird))
            elif beam_mode == 1:
                Bmode = Mode(beam_mode)
                if ct_charge >= 150:
                    condition_c = Condition(beam_mode)
                    if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                        beams_c.add(Beam1(bird))
                        ct_charge = 0
                        condition_c = Condition()


        if beam_mode == 1:
            if beam_mode <= 160:
                ct_charge += 1

        x = tmr%4800
        screen.blit(bg_img, [-x, 0])
        screen.blit(bg_img,[-x+1600, 0])
        screen.blit(bg_img, [-x+3200, 0])
        screen.blit(bg_img, [-x+4800, 0])
        tmr += 10
        clock.tick(200)

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))
        
        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        # チャージビーム用の当たり判定
        for emy in pg.sprite.groupcollide(emys, beams_c, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams_c, True, False).keys():
            score.value += 1  # 1点アップ
        
        for bomb in pg.sprite.groupcollide(bombs, shield, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        #ここからHPをハートとして可視化するコード
        #healthはハートで、こうかとんが攻撃を食らうとnohealthとして枠のみのハートを呼び出す
        if k_health > 1:
            screen.blit(health_img, [100, 20])
        if 2 > k_health > -1:
            screen.blit(nohealth_img, [100, 20])
        if k_health > 0:
            screen.blit(health_img, [60, 20])
        if k_health > -1:
            screen.blit(health_img, [20, 20])
        if 1 > k_health > -1:
            screen.blit(nohealth_img, [60, 20])
        if k_health < 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            screen.blit(nohealth_img, [100, 20])
            screen.blit(nohealth_img, [60, 20])
            screen.blit(nohealth_img, [20, 20])
            rc = pg.Surface((WIDTH, HEIGHT))
            fonto = pg.font.Font(None, 80)
            txt = fonto.render("Game Over", True, (255, 255, 255))
            rc.set_alpha(50)
            screen.blit(txt, [WIDTH/2-150, HEIGHT/2])
            screen.blit(rc, [0, 0])
            pg.display.update()
            time.sleep(5)
            
            return
        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            k_health -= 1

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        beams_c.update()
        beams_c.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        Bmode.update(screen)
        condition_c.update(screen)
        shield.update()
        shield.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
