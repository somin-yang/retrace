"""RE:TRACE — final game. Run beside the included assets folder.

Desktop: run this file (or RETRACE.py). Web: built with pygbag from this folder.
"""
import asyncio
import math
import random
import sys
from array import array
from pathlib import Path
import pygame

WIDTH, HEIGHT, FPS = 960, 720, 60
SPEED, CHARACTER_HEIGHT, BEAM_HEIGHT, POWER_SECONDS = 4, 88, 48, 9
FLOORS = ("B6", "B5", "B4", "B3", "B2", "B1")
WEB = sys.platform == "emscripten"  # True when running in a browser via pygbag
ASSETS = (Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()) / "assets"
INK, MUTED = (232, 236, 235), (155, 167, 175)
CYAN, GREEN = (111, 214, 232), (132, 225, 174)
RED, AMBER, VIOLET = (248, 83, 94), (238, 183, 105), (184, 154, 225)
ROOM_IMAGES = {name: name.lower() + "_room_revision" + ("2" if name == "B1" else "1") for name in FLOORS}
LIFT_CLOSE_TICKS = 15  # 0.25 seconds; puzzle-door timing is independent.
AMBIENCE_VOLUME, MUSIC_VOLUME, WIND_VOLUME = .12, .30, .10
# All audio is OGG: browsers (pygbag) do not play WAV reliably; desktop pygame-ce plays OGG too.
AUDIO_FILES = {"music": "glass_echo.ogg", "lift_music": "glass_echo_lift.ogg",
               "surface": "surface_release.ogg", "hum": "facility_hum.ogg",
               "wind": "outside_wind.ogg"}
EFFECT_FILES = {name: "sfx_" + name + ".ogg" for name in
                ("lever", "lever_reset", "button", "mirror", "panel", "shutdown", "start", "sputter", "failure")}
# A device keeps its sound family on every floor; a replay uses the same sound.
DEVICE_SOUNDS = {
    "B6": {"switch": "lever"},
    "B5": {"transmitter": "button", "mode": "lever"},
    "B4": {"pulse1": "button", "pulse2": "button", "decoy": "button", "selector": "lever"},
    "B3": {"terminal": "lever"},
    "B2": {"mirror1": "mirror", "mirror2": "mirror", "source_on": "button", "emergency_off": "button"},
    "B1": {"charge": "panel", "release": "panel", "mirror": "mirror", "mode": "lever"}}
FLOOR_TEXT = {
    "B6": (("여긴… 어디지?", "저 문 너머에는 뭐가 있을까."),
           ("움직임과 장치 조작을 기록할 수 있습니다.",
            "기록을 마치면 출발점으로 돌아갑니다.",
            "다시 움직이면 기록체가 저장된 행동을 재생합니다.",
            "재생이 끝난 기록체는 잔상으로만 남습니다."), "NEW SKILL"),
    "B5": (("내가 지나간 자리에…", "아직 내가 남아 있었다."), (), ""),
    "B4": (("다른 사람은… 없는 건가.",), (), ""),
    "B3": (("계속 올라가면… 나갈 수 있겠지.",),
           ("기록체가 재생되는 동안에도 새 기록을 만들 수 있습니다.",
            "새 기록은 지금 서 있는 위치에서 시작합니다."), "NEW SKILL"),
    "B2": (("…소독약 냄새가 나.",),
           ("레이저에 닿으면 이 층의 기록이 모두 지워집니다.",), "CAUTION"),
    "B1": (("이제 한 층만 더.", "밖에는 바람이 불고 있을까."),
           ("기록체는 저장된 경로를 따라 닫힌 문도 통과합니다.",
            "장치를 조작하려면 현재의 작동 조건이 맞아야 합니다."), "NEW SKILL")
}

HINTS = {'B6': ['기록체에게 레버 조작을 맡겨 보세요.'],
 'B5': ['끊어진 전선 사이의 틈을 어떻게 연결할 수 있을까요?', '기록체가 신호를 보내는 동안, 지금의 나는 무엇을 할 수 있을까요?'],
 'B4': ['모든 버튼을 사용할 필요가 있을까요?',
        '전환 레버는 다음 신호를 받을 문을 정합니다. 방향을 바꾸면 이전 연결은 끊어집니다.',
        '신호를 보내는 일과 신호의 방향을 바꾸는 일을, 서로 다른 내가 맡을 수 있을까요?'],
 'B3': ['방으로 들어가는 문은 무엇과 연결되어 있을까요? 전선을 따라가 보세요.',
        '방 안의 장치는 두 문이 모두 닫혀 있어야 작동합니다. 문이 하나라도 열리면 승강기의 전원이 다시 끊깁니다.',
        '돌아 나가는 문을 여는 센서가 있습니다. 장치를 작동시킨 사람이 그 문으로 나가도 괜찮을까요?',
        '기록은 방 안에서도 시작할 수 있습니다. 문이 닫힌 뒤의 조작을 기록체에게 맡길 수 있을까요?'],
 'B2': ['가까이 다가갔을 때 조작할 수 있는 장치부터 살펴보세요.',
        '거울의 방향을 바꾸면 빛이 닿는 곳은 어떻게 달라질까요?',
        '작은 방의 조작 장치는 멀리 있는 거울과 연결되어 있습니다. 빛은 어디에 닿아야 승강기가 작동할까요?',
        '승강기에 전원을 공급하는 빛이 내가 지나갈 길을 막고 있지는 않나요?',
        '마지막으로 거울을 돌리는 사람이 지금의 나여야 할까요?'],
 'B1': ['배터리 방의 바닥 격자를 지나면 저장된 전력이 사라집니다. 충전한 사람은 꼭 밖으로 나와야 할까요?',
        '승강기 옆의 조작 장치는 저장된 전력의 쓰임을 바꿉니다. 조작 전후에 모든 문과 전선의 상태를 비교해 보세요.',
        '거울과 연결된 두 경로는 서로 다른 역할을 합니다. 하나는 중앙 방의 입구로, 다른 하나는 승강기로 이어집니다.',
        '중앙 장치에는 전력, 알맞은 모드, 닫힌 두 문이 필요합니다. 작동할 준비가 되면 표시등이 초록색으로 바뀝니다.',
        '전력이 줄어들기 시작한 뒤에는 시간이 많지 않습니다. 그전에 끝내 둘 수 있는 준비는 무엇일까요?',
        '중앙 장치가 아직 작동하지 않아도 조작 시도는 기록할 수 있습니다. 그 조작이 재생될 순간에 조건이 갖춰져 있다면 어떨까요?']}
MANUAL_TABS = [pygame.Rect(100 + 254 * i, 161, 246, 36) for i in range(3)]
MANUAL_BODY = pygame.Rect(100, 223, 745, 354)
MANUAL_CLOSE = pygame.Rect(746, 82, 114, 36)
HINT_BUTTON = pygame.Rect(617, 588, 226, 38)
MANUAL_RECORDING = (
    ("기록", "R을 누르면 지금 있는 곳에서 움직임과 가까운 장치의 E 조작을 기록합니다. R을 다시 누르면 저장하고 층의 출발점으로 돌아갑니다."),
    ("재생", "출발점에서 움직이기 시작하면 기록체가 저장한 행동을 재생합니다. 움직이기 전에는 기다립니다."),
    ("여러 기록", "기록체의 수에는 제한이 없습니다. 기존 기록체가 움직이는 동안에도 새 기록을 만들 수 있습니다. 나중에 시작한 기록은 재생도 늦게 시작합니다."),
    ("조작 시점", "가까이에서 E를 눌렀다면 그때 작동하지 않은 시도도 기록됩니다. 기록체는 재생되는 순간의 조건으로 딱 한 번 시도하며, 나중에 조건이 맞아도 다시 누르지 않습니다."),
    ("기록이 끝나면", "끝난 기록체는 흐린 잔상으로 남고 더는 센서나 장치를 작동시키지 않습니다. 이미 바뀐 장치는 각자의 규칙을 따릅니다."),
    ("다시 시작과 힌트", "Q나 전력 고갈·방전 후 재시작은 현재 층의 모든 기록을 지웁니다. 레이저에 닿아도 기록이 사라집니다. 확인한 힌트와 힌트 대기 시간은 남고, R로 저장할 때는 기존 기록이 남습니다."),
)

# Three camera crops of B6 play in sequence inside the opening guide. The
# tutorial clock is independent of the paused puzzle simulation.
GUIDE_VIEW = pygame.Rect(70, 265, 570, 414)
GUIDE_SCENE_SIZE = (230, 167)
GUIDE_DURATIONS = (2.35, 2.40, 2.85)

LIFT_VIEW, LIFT_DISPLAY = pygame.Rect(40, 34, 880, 686), pygame.Rect(751, 68, 132, 48)

# Mobile web build: the CI copies this folder and adds a "mobile.flag" file.
# That build gets a wider canvas with a touch-control panel on each side.
# The PC web build and desktop Python keep the original 960x720 screen.
MOBILE = WEB and (ASSETS.parent / "mobile.flag").is_file()
SIDE = 240 if MOBILE else 0


def initialize(start_floor="B6"):
    global window, screen, clock, fonts, images, sprites, echoes, faded
    global sounds, records, ui_tick, lift_panels, lever_image
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    if WEB:
        # In the browser the page scales the canvas; render at native size.
        window = pygame.display.set_mode((WIDTH + 2 * SIDE, HEIGHT))
    else:
        desktop = pygame.display.get_desktop_sizes()[0]
        scale = max(.5, min(1, (desktop[0] - 80) / WIDTH, (desktop[1] - 100) / HEIGHT))
        window = pygame.display.set_mode((int(WIDTH * scale), int(HEIGHT * scale)), pygame.RESIZABLE)
    pygame.display.set_caption("RE:TRACE")
    screen, clock = pygame.Surface((WIDTH, HEIGHT)), pygame.time.Clock()
    picture_names = (*ROOM_IMAGES.values(), "b5_shutter_closed", "b6_reference",
                     "b1_gate_panels", "elevator", "outside")
    required = tuple(name + ".png" for name in picture_names) + (
        "patient.png", "equipment.png", "GothicA1-Medium.ttf", "BarlowCondensed-Medium.ttf") + tuple(AUDIO_FILES.values()) + tuple(EFFECT_FILES.values())
    missing = [name for name in required if not (ASSETS / name).is_file()]
    if missing:
        raise FileNotFoundError("Extract the complete RE:TRACE ZIP and keep its assets folder "
                                "beside RETRACE.py. Missing: " + ", ".join(missing))
    fonts = {family: {size: pygame.font.Font(str(ASSETS / filename), size)
                     for size in (16, 18, 20, 22, 26, 28, 30, 38, 48, 110)}
             for family, filename in (("ko", "GothicA1-Medium.ttf"), ("en", "BarlowCondensed-Medium.ttf"))}
    images = {}
    for name in picture_names:
        picture = pygame.image.load(str(ASSETS / (name + ".png"))).convert()
        images[name] = pygame.transform.smoothscale(picture, (WIDTH, HEIGHT))
    lift_panels = [pygame.transform.smoothscale(
        images["elevator"].subsurface((40 + i * 440, 140, 440, 580)),
        (LIFT_VIEW.w // 2, LIFT_VIEW.h)) for i in range(2)]
    sheet = pygame.image.load(str(ASSETS / "patient.png")).convert_alpha()
    sprites, echoes, faded = {}, {}, {}
    for row, direction in enumerate(("down", "up", "left", "right")):
        for col in range(3):
            cell = sheet.subsurface((col * sheet.get_width() // 3, row * sheet.get_height() // 4,
                                    sheet.get_width() // 3, sheet.get_height() // 4))
            picture = prepare_actor(cell)
            key = direction, col
            sprites[key], echoes[key], faded[key] = picture, make_echo(picture, 175), make_echo(picture, 52)
    atlas = pygame.image.load(str(ASSETS / "equipment.png")).convert_alpha()
    cell = atlas.subsurface((atlas.get_width() // 2, 0, atlas.get_width() // 4, atlas.get_height() // 2))
    cell = cell.subsurface(cell.get_bounding_rect(min_alpha=80)).copy()
    lever_image = pygame.transform.smoothscale(cell, (round(cell.get_width() * 76 / cell.get_height()), 76))
    sounds = {"record": make_sound(880, .09), "save": make_sound(570, .12),
              "motor": make_sound(65, 2.3, .025),
              "chime": make_sound(880, .3), "refuse": make_sound(125, .08, .04),
              "tick": make_sound(460, .04, .03), "sensor": make_sound(740, .085, .055)}
    if pygame.mixer.get_init():
        sounds.update({name: pygame.mixer.Sound(str(ASSETS / filename))
                       for name, filename in EFFECT_FILES.items()})
    setup_audio()
    records, ui_tick = [], 0
    if SIDE:
        build_controls()
    reset_help()
    build_floor(start_floor)
    set_scene("title")


def cutout(shape):
    if isinstance(shape, pygame.Rect):
        return images[room_name].subsurface(shape).copy(), shape
    mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(mask, "white", shape)
    picture = images[room_name].convert_alpha()
    picture.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if floor == "B5":
        return picture
    bounds = mask.get_bounding_rect()
    return picture.subsurface(bounds).copy(), bounds


def build_floor(name, intro=True):
    global ACCESS_WIRE, BATTERY_WIRE, BRANCHES, BROKEN_CABLE, BUTTON_CENTERS, CABLE_IN, CABLE_OUT, COMMON_LIGHTS
    global CONTACT_WIRES, DOOR_ART, FEED, GATE_LIGHTS, INPUTS, LIFT_ART, LIFT_CABLE, LIFT_LIGHTS
    global LIFT_WIRE, OPTICS, POWER_WIRES, REMOTE_WIRE, RETURN_WIRE, SCANNER_WIRE, SENSOR_ART
    global SENSOR_WIRE, SERVICE_WIRE, SHUTTER_ART, SIGNAL_WIRE, SKILL, START, TARGETS, THOUGHT
    global beam_layer, cable_length, devices, doors, floor, gap_end, gap_start, obj
    global post_images, room_name, room_parts, solids, walk_mask, walls
    global SKILL_TITLE
    if name not in FLOORS:
        raise ValueError("Unknown floor: " + str(name))
    floor = name
    room_name = ROOM_IMAGES[name]
    room_parts, post_images = {}, []
    if floor == "B6":
        START = (480.0, 620.0)
        obj = {"lift": pygame.Rect(439, 266, 96, 21),
               "switch": pygame.Rect(96, 551, 54, 42),
               "gate": pygame.Rect(369, 459, 228, 12)}
        walls = [pygame.Rect(353, 440, 16, 44), pygame.Rect(597, 440, 16, 44)]
        DOOR_ART = {"gate": pygame.Rect(369, 387, 228, 76),
                    "lift": pygame.Rect(439, 159, 96, 120)}
        LIFT_LIGHTS = [((346, 323), (346, 334)), ((346, 253), (346, 264))]
        GATE_LIGHTS = [((421, 507), (430, 507))]
        COMMON_LIGHTS = [((275, 507), (286, 507))]
        devices = solids = ("switch",)
        doors = ("gate",)
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, "white", [(166, 486), (866, 486), (905, 698), (55, 698)])
        pygame.draw.rect(mask, "white", (369, 282, 228, 210))
        pygame.draw.rect(mask, "white", (446, 266, 82, 24))
        walk_mask = pygame.mask.from_surface(mask)
        # Only the painted post silhouettes are reapplied; no rectangular floor patches.
        post_images = []
        for polygon in (((350, 373), (365, 371), (369, 381), (369, 463), (350, 463)),
                        ((602, 371), (622, 373), (626, 384), (626, 463), (602, 463))):
            mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(mask, "white", polygon)
            post = images["b6_room_revision1"].convert_alpha()
            post.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            post_images.append(post)
    elif floor == "B5":
        START = (480.0, 620.0)
        obj = {"lift": pygame.Rect(684, 205, 85, 16),
               "transmitter": pygame.Rect(141, 594, 31, 18),
               "mode": pygame.Rect(505, 594, 53, 18),
               "shutter": pygame.Rect(356, 557, 28, 45)}
        devices = ("transmitter", "mode")
        walls = [pygame.Rect(356, 0, 28, 557), pygame.Rect(356, 602, 28, 118)]
        SHUTTER_ART = pygame.Rect(357, 543, 27, 59)
        LIFT_ART = pygame.Rect(684, 93, 85, 120)
        gap_start, gap_end, cable_length = 200, 228, 1108
        CABLE_IN = [(173, 586), (352, 586)]
        CABLE_OUT = [(391, 586), (438, 586), (438, 219), (673, 219)]
        solids = devices
        doors = ("shutter",)
        DOOR_ART = {"shutter": SHUTTER_ART, "lift": LIFT_ART}
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, "white", [(80, 228), (879, 228), (931, 700), (28, 700)])
        pygame.draw.rect(mask, "white", (684, 205, 85, 32))
        walk_mask = pygame.mask.from_surface(mask)
        # Only solid silhouettes are restored in front of actors, never floor rectangles.
        room_parts = {
            "north_wall": cutout([(359, 148), (383, 148), (383, 557), (357, 557), (357, 502)]),
            "south_wall": cutout([(358, 603), (383, 603), (383, 720), (357, 720)]),
            "transmitter": cutout([(143, 521), (169, 522), (170, 610), (140, 610), (140, 547)]),
            "mode": cutout([(507, 524), (554, 524), (558, 539), (558, 612), (504, 612), (504, 541)])}
    elif floor == "B4":
        START = (480.0, 620.0)
        obj = {"lift": pygame.Rect(675, 208, 88, 16),
               "pulse1": pygame.Rect(251, 562, 37, 17),
               "pulse2": pygame.Rect(135, 336, 39, 17),
               "decoy": pygame.Rect(251, 435, 38, 17),
               "selector": pygame.Rect(482, 447, 62, 18),
               "gate_a": pygame.Rect(440, 521, 90, 15),
               "gate_b": pygame.Rect(601, 320, 87, 16)}
        devices = ("pulse1", "pulse2", "decoy", "selector")
        doors = ("gate_a", "gate_b", "lift")
        walls = [pygame.Rect(384, 0, 24, 535),
                 pygame.Rect(408, 521, 32, 15), pygame.Rect(530, 521, 410, 15),
                 pygame.Rect(408, 320, 193, 16), pygame.Rect(688, 320, 252, 16)]
        DOOR_ART = {"gate_a": pygame.Rect(440, 484, 90, 51),
                    "gate_b": pygame.Rect(601, 286, 87, 49),
                    "lift": pygame.Rect(675, 96, 88, 119)}
        INPUTS = {"pulse1": [(288, 560), (360, 560), (360, 492), (382, 492)],
                  "pulse2": [(174, 333), (360, 333), (360, 492), (382, 492)]}
        FEED = [(408, 492), (418, 492), (418, 448), (482, 448)]
        BRANCHES = {"A": [(544, 448), (558, 448), (558, 488), (545, 488)],
                    "B": [(541, 419), (558, 419), (558, 327), (584, 327)]}
        LIFT_CABLE = [(704, 327), (768, 327), (768, 219), (764, 219)]
        BROKEN_CABLE = [(289, 431), (319, 431)]
        BUTTON_CENTERS = {"pulse1": (269, 540), "pulse2": (153, 313), "decoy": (269, 412)}
        solids = devices
        doors = ("gate_a", "gate_b")
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, "white", [(80, 228), (879, 228), (931, 700), (28, 700)])
        pygame.draw.rect(mask, "white", (675, 208, 88, 28))
        walk_mask = pygame.mask.from_surface(mask)
        # Restore only solid artwork silhouettes, never rectangular patches of floor.
        outlines = {
            "divider": [(384, 107), (407, 107), (408, 534), (384, 534)],
            "a_left": [(408, 483), (426, 483), (426, 535), (408, 535)],
            "a_right": [(545, 483), (918, 483), (922, 533), (545, 533)],
            "a_post1": [(426, 482), (440, 482), (440, 535), (426, 535)],
            "a_post2": [(530, 482), (544, 482), (545, 535), (530, 535)],
            "b_left": [(408, 286), (587, 286), (587, 332), (408, 332)],
            "b_right": [(703, 286), (904, 286), (906, 331), (703, 331)],
            "b_post1": [(587, 284), (600, 284), (601, 335), (587, 335)],
            "b_post2": [(688, 284), (702, 284), (703, 335), (688, 335)],
            "pulse1": [(254, 530), (285, 530), (289, 578), (250, 578), (250, 539)],
            "pulse2": [(139, 303), (168, 303), (173, 352), (134, 352), (135, 314)],
            "decoy": [(254, 402), (285, 402), (289, 451), (250, 451), (250, 412)],
            "selector": [(496, 403), (534, 403), (543, 464), (481, 464), (486, 432)]}
        room_parts = {key: cutout(points) for key, points in outlines.items()}
    elif floor == "B3":
        START = (480.0, 620.0)
        obj = {"lift": pygame.Rect(675, 210, 83, 14),
               "terminal": pygame.Rect(294, 377, 48, 14),
               "scanner": pygame.Rect(653, 535, 203, 66),
               "sensor": pygame.Rect(136, 380, 55, 20),
               "archive_in": pygame.Rect(307, 491, 72, 12),
               "archive_out": pygame.Rect(121, 491, 75, 12)}
        devices = ("terminal",)
        doors = ("archive_out", "archive_in")
        walls = [pygame.Rect(394, 0, 26, 503),
                 pygame.Rect(40, 491, 81, 12), pygame.Rect(196, 491, 111, 12),
                 pygame.Rect(379, 491, 15, 12),
                 pygame.Rect(100, 400, 21, 91), pygame.Rect(196, 400, 22, 91)]
        DOOR_ART = {"archive_in": pygame.Rect(307, 449, 72, 52),
                    "archive_out": pygame.Rect(121, 449, 75, 52),
                    "lift": pygame.Rect(675, 93, 83, 124)}
        SENSOR_ART = {"scanner": [(651, 534), (855, 534), (862, 602), (654, 602)],
                      "sensor": [(139, 380), (191, 380), (190, 399), (137, 399)]}
        SCANNER_WIRE = [(654, 602), (393, 602), (393, 506)]
        SENSOR_WIRE = [(191, 390), (200, 390), (200, 460)]
        CONTACT_WIRES = {
            "archive_out": [(220, 397), (277, 397), (277, 383), (294, 383)],
            "archive_in": [(296, 448), (296, 406), (323, 406), (323, 391)]}
        POWER_WIRES = [[(342, 358), (368, 358), (368, 242), (392, 242)],
                       [(420, 242), (640, 242), (640, 219), (675, 219)]]
        solids = devices
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, "white", [(78, 226), (879, 226), (931, 700), (28, 700)])
        pygame.draw.rect(mask, "white", (675, 210, 83, 28))
        walk_mask = pygame.mask.from_surface(mask)
        # Only solid silhouettes cover actors; floor and passages remain transparent.
        outlines = {
            "divider": [(394, 116), (413, 116), (420, 501), (394, 501)],
            "left": [(45, 451), (100, 451), (100, 502), (42, 502)],
            "middle": [(215, 451), (287, 451), (287, 501), (215, 501)],
            "right": [(398, 450), (420, 450), (420, 502), (398, 502)],
            "return_left": [(106, 359), (126, 359), (121, 446), (100, 446)],
            "return_right": [(199, 359), (218, 359), (216, 448), (196, 448)],
            "out_left": [(100, 445), (121, 445), (121, 502), (100, 502)],
            "out_right": [(196, 445), (215, 445), (215, 503), (196, 503)],
            "in_left": [(287, 447), (307, 447), (307, 503), (287, 503)],
            "in_right": [(379, 447), (398, 447), (398, 505), (379, 505)],
            "terminal": [(298, 324), (339, 324), (340, 376), (346, 377),
                         (346, 391), (294, 391), (294, 377), (297, 377)]}
        room_parts = {key: cutout(points) for key, points in outlines.items()}
    elif floor == "B2":
        START = (480.0, 620.0)
        obj = {"lift": pygame.Rect(676, 210, 84, 14),
               "service": pygame.Rect(450, 358, 112, 12),
               "mirror1": pygame.Rect(208, 432, 40, 14),
               "mirror2": pygame.Rect(497, 295, 40, 13),
               "optic2": pygame.Rect(760, 432, 40, 14),
               "source_on": pygame.Rect(350, 570, 29, 13),
               "emergency_off": pygame.Rect(761, 301, 35, 13),
               "service_receiver": pygame.Rect(211, 280, 37, 14),
               "lift_receiver": pygame.Rect(813, 280, 37, 14),
               "emitter": pygame.Rect(208, 576, 40, 12),
               "left_stop": pygame.Rect(100, 420, 35, 13),
               "right_stop": pygame.Rect(849, 437, 35, 12),
               "down_stop": pygame.Rect(769, 555, 36, 13)}
        devices = ("mirror1", "mirror2", "source_on", "emergency_off")
        solids = devices + ("optic2", "service_receiver", "lift_receiver", "emitter",
                            "left_stop", "right_stop", "down_stop")
        doors = ("service",)
        walls = [pygame.Rect(596, 0, 24, 498), pygame.Rect(360, 0, 22, 370),
                 pygame.Rect(360, 358, 90, 12), pygame.Rect(562, 358, 34, 12),
                 pygame.Rect(388, 218, 94, 62), pygame.Rect(796, 432, 164, 16)]
        DOOR_ART = {"service": pygame.Rect(450, 315, 112, 46),
                    "lift": pygame.Rect(676, 93, 84, 124)}
        OPTICS = {"emitter": (228, 576), "mirror1": (228, 442), "optic2": (780, 442),
                  "service_receiver": (230, 294), "lift_receiver": (832, 294),
                  "left_stop": (116, 454), "right_stop": (866, 475), "down_stop": (786, 592)}
        TARGETS = (("left_stop", "service_receiver", "optic2"),
                   ("down_stop", "right_stop", "lift_receiver"))
        SERVICE_WIRE = [(244, 250), (336, 250), (336, 364), (444, 364), (444, 336)]
        REMOTE_WIRE = [(538, 270), (562, 270), (562, 306), (828, 306), (828, 424), (806, 424)]
        LIFT_WIRE = [(814, 246), (814, 218), (792, 218), (792, 155)]
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, "white", [(78, 226), (879, 226), (931, 700), (28, 700)])
        pygame.draw.rect(mask, "white", (676, 210, 84, 28))
        walk_mask = pygame.mask.from_surface(mask)
        # Only solid silhouettes cover actors; floor and passages remain transparent.
        outlines = {
            "divider": [(596, 116), (618, 116), (620, 498), (596, 498)],
            "service_left": [(360, 184), (382, 184), (382, 370), (360, 370)],
            "service_front": [(360, 307), (450, 307), (450, 370), (360, 370)],
            "service_right": [(562, 307), (596, 307), (596, 370), (562, 370)],
            "right_barrier": [(796, 403), (913, 403), (914, 448), (796, 448)],
            "mirror1": [(214, 386), (240, 386), (241, 430), (249, 434),
                        (249, 446), (208, 446), (208, 436), (214, 434)],
            "optic2": [(767, 386), (792, 386), (793, 432), (801, 434),
                       (801, 446), (760, 446), (760, 434), (766, 432)],
            "mirror2": [(502, 232), (532, 232), (533, 292), (538, 296),
                        (538, 308), (497, 308), (497, 296), (502, 292)],
            "source_on": [(354, 532), (375, 532), (375, 568), (379, 570),
                          (379, 583), (350, 583), (350, 570), (354, 568)],
            "emergency_off": [(766, 264), (788, 264), (790, 297), (796, 301),
                              (796, 314), (761, 314), (761, 301), (765, 298)],
            "service_receiver": [(219, 225), (239, 225), (240, 278), (248, 281),
                                 (248, 294), (211, 294), (211, 281), (217, 278)],
            "lift_receiver": [(821, 225), (841, 225), (842, 278), (850, 281),
                              (850, 294), (813, 294), (813, 281), (819, 278)],
            "emitter": [(214, 521), (240, 521), (243, 574), (248, 576),
                        (248, 588), (208, 588), (208, 576), (212, 574)],
            "left_stop": [(106, 389), (132, 389), (132, 419), (135, 419),
                          (135, 433), (100, 433), (100, 419), (106, 419)],
            "right_stop": [(854, 413), (879, 413), (879, 435), (884, 435),
                           (884, 446), (849, 446), (849, 435), (854, 435)],
            "down_stop": [(774, 524), (800, 524), (800, 555), (805, 555),
                          (805, 568), (769, 568), (769, 555), (774, 555)]}
        room_parts = {key: cutout(points) for key, points in outlines.items()}
        beam_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    elif floor == "B1":
        START = (480.0, 628.0)
        obj = {"lift": pygame.Rect(767, 230, 76, 12),
               "charge": pygame.Rect(98, 234, 46, 10),
               "mode": pygame.Rect(865, 234, 28, 10),
               "release": pygame.Rect(502, 319, 40, 10),
               "mirror": pygame.Rect(403, 523, 28, 10),
               "charge_in": pygame.Rect(209, 434, 72, 10),
               "charge_out": pygame.Rect(92, 434, 72, 10),
               "power_gate": pygame.Rect(750, 462, 105, 10),
               "release_in": pygame.Rect(458, 523, 66, 10),
               "release_out": pygame.Rect(553, 523, 67, 10),
               "drain": pygame.Rect(93, 416, 70, 16),
               "sensor": pygame.Rect(561, 480, 50, 43)}
        devices = solids = ("charge", "mode", "release", "mirror")
        doors = ("charge_in", "charge_out", "power_gate", "release_in", "release_out")
        walls = [pygame.Rect(302, 233, 18, 211), pygame.Rect(30, 434, 62, 10),
                 pygame.Rect(164, 434, 45, 10), pygame.Rect(281, 434, 39, 10),
                 pygame.Rect(78, 395, 14, 49), pygame.Rect(164, 395, 16, 49),
                 pygame.Rect(411, 314, 17, 219), pygame.Rect(646, 234, 20, 299),
                 pygame.Rect(411, 314, 255, 10), pygame.Rect(428, 523, 30, 10),
                 pygame.Rect(524, 523, 29, 10), pygame.Rect(620, 523, 46, 10),
                 pygame.Rect(666, 462, 84, 10), pygame.Rect(855, 462, 75, 10),
                 pygame.Rect(554, 234, 145, 8)]
        DOOR_ART = {key: pygame.Rect(obj[key].x, obj[key].bottom - 31, obj[key].w, 31) for key in doors}
        DOOR_ART["lift"] = pygame.Rect(767, 99, 76, 136)
        BATTERY_WIRE = [(122, 244), (122, 300), (348, 300), (348, 606), (879, 606), (879, 244)]
        RETURN_WIRE = [(122, 244), (122, 416)]
        SIGNAL_WIRE = [(522, 329), (522, 358), (586, 358), (586, 580), (804, 580), (804, 234)]
        ACCESS_WIRE = [(388, 154), (348, 154), (348, 564), (491, 564), (491, 533)]
        LIFT_WIRE = [(640, 154), (710, 154), (710, 246), (804, 246), (804, 234)]
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, "white", [(70, 239), (892, 239), (924, 700), (32, 700)])
        pygame.draw.rect(mask, "white", (767, 230, 76, 20))
        walk_mask = pygame.mask.from_surface(mask)
        # Short wall sections have local depth. A long wall never hides the entire actor.
        room_parts = []
        for area in ((302, 229, 18, 215), (411, 295, 17, 238), (646, 229, 20, 304)):
            x, y, width, height = area
            for row in range(y, y + height, 4):
                rectangle = pygame.Rect(x, row, width, min(4, y + height - row))
                room_parts.append((min(y + height, row + 28), cutout(rectangle)))
        for area in ((48, 412, 30, 32), (78, 382, 14, 62), (164, 382, 16, 62),
                     (180, 412, 29, 32), (281, 412, 21, 32), (428, 295, 218, 29),
                     (431, 502, 27, 31), (524, 502, 29, 31), (620, 502, 26, 31),
                     (666, 442, 84, 30), (855, 442, 59, 30)):
            rectangle = pygame.Rect(area)
            room_parts.append((rectangle.bottom, cutout(rectangle)))
    THOUGHT, SKILL, SKILL_TITLE = FLOOR_TEXT[floor]
    prepare_doors()
    restart_run(clear=True)
    if intro:
        set_scene("thought")



def restart_run(clear=False):
    global px, py, facing, animation, walk_ticks, state, recording, pending_e
    global record_path, record_actions, record_start_frame, replay_frame, replay_started
    global ghost_positions, ghost_active, door_amounts, device_flashes, device_flash, sparks
    if clear:
        records.clear()
    px, py = START
    facing, animation, walk_ticks = "up", 0, 0
    recording, replay_started, pending_e = False, False, False
    record_path, record_actions = [], []
    record_start_frame = replay_frame = device_flash = 0
    ghost_positions, ghost_active = [None] * len(records), [False] * len(records)
    initial = {
        "B6": {"lift_power": False},
        "B5": {"sealed": False, "pulses": []},
        "B4": {"route": "A", "powered": False, "test_pulses": [], "fault_ticks": 0},
        "B3": {"scanner_on": False, "permit": False, "lever_on": False,
               "return_timer": 0, "return_sensor_on": False},
        "B2": {"m1": 0, "m2": 0, "source": True, "service_open": False,
               "beam_age": 18, "old_beams": [], "old_m1": 0, "old_m2": 0},
        "B1": {"lift_mode": False, "charge": 0, "stable": False, "mirror": 0,
               "mirror_turn": 0, "mirror_angle": 0.0, "charge_level": 0.0,
               "mode_blend": 0.0, "drain_flash": 0, "pulses": [], "sparks": [],
               "release_cooldown": 0, "failure": "POWER DEPLETED"}}
    state = initial[floor]
    opened = {"B6": ("gate",), "B5": ("shutter",), "B1": ("charge_in", "charge_out")}
    door_amounts = {key: float(key in opened.get(floor, ())) for key in (*doors, "lift")}
    device_flashes, sparks = {}, []
    if sounds.get("motor"):
        sounds["motor"].stop()
    set_scene("play")


def make_sound(frequency, seconds, volume=0.06, noise=False):
    settings = pygame.mixer.get_init()
    if not settings:
        return None
    rate, _, channels = settings
    count, samples, rng, previous = int(rate * seconds), array("h"), random.Random(9), 0
    for i in range(count):
        previous = previous * 0.97 + rng.uniform(-1, 1) * 0.03
        wave = previous * 5 if noise else math.sin(2 * math.pi * frequency * i / rate)
        fade = min(1, i / (rate * 0.03), (count - i) / (rate * 0.08))
        samples.extend([int(32767 * volume * fade * wave)] * channels)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def sound(name, source="player"):
    effect = sounds.get(name)
    if effect:
        channel = effect.play()
        if channel:
            # Set the individual voice, never the shared Sound, so a quiet echo
            # does not accidentally turn down a simultaneous player interaction.
            channel.set_volume(.72 if source == "ghost" else 1.0)


def prepare_actor(cell):
    silhouette = pygame.mask.from_surface(cell, 230).connected_component()
    bounds = silhouette.get_bounding_rects()[0]
    mask = silhouette.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    clean = cell.copy()
    clean.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    clean = clean.subsurface(bounds).copy()
    return pygame.transform.smoothscale(clean, (
        round(clean.get_width() * CHARACTER_HEIGHT / clean.get_height()), CHARACTER_HEIGHT))


def make_echo(image, opacity):
    echo = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    for y in range(image.get_height()):
        for x in range(image.get_width()):
            p = image.get_at((x, y))
            if p.a:
                echo.set_at((x, y), (100 + p.r // 5, 180 + p.g // 5,
                                     211 + p.b // 6, p.a * opacity // 255))
    return echo


def set_scene(name):
    global scene, scene_tick
    previous = globals().get("scene")
    scene, scene_tick = name, 0
    if name == "outside" and previous != "outside" and audio_channels:
        # The ending arrangement starts with the actual reveal, not silently
        # several minutes earlier while the player is still underground.
        audio_channels["surface"].play(audio_tracks["surface"], loops=-1)


def actor_rect(x, y):
    return pygame.Rect(round(x) - 8, round(y) - 7, 16, 10)


def pose():
    return px, py, facing, animation


def near(target, x, y):
    return actor_rect(x, y).colliderect(target.inflate(62, 54))


def on_floor(body):
    for x, y in (body.topleft, (body.right - 1, body.top),
                 (body.left, body.bottom - 1), (body.right - 1, body.bottom - 1)):
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT) or not walk_mask.get_at((x, y)):
            return False
    return True


def move_player(keys):
    global px, py, facing, animation, walk_ticks
    dx = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
    dy = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
    if dx or dy:
        facing = ("left" if dx < 0 else "right") if dx else ("up" if dy < 0 else "down")
    speed, before = SPEED / math.sqrt(2) if dx and dy else SPEED, (px, py)
    if dx and not blocked(actor_rect(px + dx * speed, py)):
        px += dx * speed
    if dy:
        destination = actor_rect(px, py + dy * speed)
        if not blocked(destination):
            py += dy * speed
        elif not on_floor(destination):
            # Follow a slanted outer edge with a small sideways adjustment.
            # Check every obstacle again and keep total movement within SPEED.
            slide_y = dy * math.sqrt(speed * speed - 1)
            for slide_x in (1, -1):
                candidate = (px + slide_x, py + slide_y)
                if (math.dist(before, candidate) <= SPEED + 1e-9
                        and not blocked(actor_rect(*candidate))):
                    px, py = candidate
                    break
    moved = before != (px, py)
    walk_ticks = walk_ticks + 1 if moved else 0
    animation = (1, 0, 2, 0)[(walk_ticks // 8) % 4] if moved else 0
    return moved


def occupied(area):
    if actor_rect(px, py).colliderect(area):
        return True
    return any(active and pos is not None and actor_rect(*pos[:2]).colliderect(area)
               for pos, active in zip(ghost_positions, ghost_active))


def get_action(x, y):
    nearby = [key for key in devices if can_use(key, x, y)]
    return min(nearby, key=lambda key: math.dist((x, y), obj[key].center)) if nearby else None


def interact(sample=None):
    action = get_action(px, py)
    # Store a deliberate, reachable-device attempt, even if its prerequisites
    # are not met yet. Playback tries once against the world at that moment.
    if action is None:
        return False
    if recording:
        if sample is None:
            sample = len(record_path) - 1
        record_actions.append((sample, action, px, py))
    return use_action(action, px, py)


def toggle_recording():
    global recording, record_path, record_actions, record_start_frame, pending_e
    if not recording:
        recording = True
        record_path, record_actions = [pose()], []
        record_start_frame = replay_frame if records else 0
        sound("record")
    else:
        if pending_e:
            interact()
            pending_e = False
        if len(record_path) > 1 or record_actions:
            records.append({"start_frame": record_start_frame, "path": record_path, "actions": record_actions})
        restart_run()
        sound("save")


def update_ghosts():
    global replay_frame
    opening, actions = [], []
    if not replay_started:
        return actions
    for i, record in enumerate(records):
        sample = replay_frame - record["start_frame"] + 1
        path, last = record["path"], len(record["path"]) - 1
        if sample <= 0:
            ghost_positions[i], ghost_active[i] = None, False
        elif sample <= max(1, last):
            ghost_positions[i], ghost_active[i] = path[min(sample, last)], True
            for frame, action, x, y in record["actions"]:
                if frame == 0 and sample == 1:
                    opening.append((action, x, y))
                elif frame == sample:
                    actions.append((action, x, y))
        else:
            ghost_positions[i], ghost_active[i] = path[-1], False
    replay_frame += 1
    return opening + actions


def text(words, x, y, size=22, color=INK, family="en", center=False, alpha=255, ink_center=False):
    image = fonts[family][size].render(words, True, color)
    if family == "ko":
        image = pygame.transform.smoothscale(image, (round(image.get_width() * .9), image.get_height()))
    if ink_center:
        # Remove invisible font padding before positioning the visible letters.
        image = image.subsurface(image.get_bounding_rect()).copy()
    image.set_alpha(alpha)
    screen.blit(image, image.get_rect(center=(x, y)) if center else (x, y))


def wire_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def wire_point(points, distance):
    for a, b in zip(points, points[1:]):
        length = math.dist(a, b)
        if distance <= length:
            fraction = max(0, distance) / length
            return (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)
        distance -= length
    return points[-1]


def draw_wire(points, color):
    pygame.draw.lines(screen, (26, 34, 38), False, points, 7)
    pygame.draw.lines(screen, (124, 133, 132), False, points, 4)
    pygame.draw.lines(screen, color, False, points, 2)
    for point in points[1:-1]:
        pygame.draw.circle(screen, (146, 153, 150), point, 3, 1)


def draw_hud():
    text(floor, 26, 10, 38, family="ko")
    ticks = max(0, len(record_path) - 1) if recording else replay_frame
    seconds = ticks // FPS
    text(f"{seconds // 60:02d}:{seconds % 60:02d}", 28, 57, 30,
         RED if recording else CYAN if replay_started else INK, "ko")
    if recording:
        pygame.draw.circle(screen, RED, (34, 110), 5)
        text("REC", 49, 91, 28, RED)
    controls = (("R", "SAVE" if recording else "RECORD", recording), ("E", "USE", bool(get_action(px, py))), ("Q", "RESET", False))
    widths = [32 + fonts["en"][20].size(label)[0] for _, label, _ in controls]
    x = WIDTH - 26 - sum(widths) - 28
    for (key, label, active), width in zip(controls, widths):
        color = RED if key == "R" and active else CYAN if active else MUTED
        pygame.draw.rect(screen, color, (x, 22, 24, 25), 1, border_radius=3)
        text(key, x + 12, 34, 20, color, center=True)
        picture = fonts["en"][20].render(label, True, color)
        screen.blit(picture, picture.get_rect(midleft=(x + 32, 34)))
        x += width + 14
    hud_help = pygame.Surface((150, 66), pygame.SRCALPHA)
    hud_help.fill((8, 15, 21, 168))
    screen.blit(hud_help, (778, 54))
    text("ESC  MANUAL", 790, 57, 20, MUTED)
    progress = help_progress[floor]
    blend = min(1, max(0, (progress["ticks"] - progress["next"]) / 30)) if hint_available() else 0
    color = tuple(round(a + (b - a) * blend) for a, b in zip((82, 96, 104), CYAN))
    text("H  HINT", 790, 88, 20, color)


def draw_lift():
    screen.blit(images["elevator"], (0, 0))
    pygame.draw.rect(screen, (10, 14, 20), LIFT_VIEW)
    offset = round(LIFT_VIEW.w / 2 * (1 - min(1, scene_tick / LIFT_CLOSE_TICKS)))
    old_clip = screen.get_clip()
    screen.set_clip(LIFT_VIEW)
    screen.blit(lift_panels[0], (LIFT_VIEW.left - offset, LIFT_VIEW.top))
    screen.blit(lift_panels[1], (LIFT_VIEW.centerx + offset, LIFT_VIEW.top))
    screen.set_clip(old_clip)
    screen.blit(images["elevator"], (728, 34), (728, 34, 192, 106))
    pygame.draw.line(screen, (62, 65, 65), (728, 34), (728, 140), 2)
    pygame.draw.line(screen, (62, 65, 65), (728, 140), (920, 140), 2)
    destination = FLOORS[FLOORS.index(floor) + 1] if floor != "B1" else "G"
    pygame.draw.rect(screen, (12, 22, 27), LIFT_DISPLAY)
    cx, cy = LIFT_DISPLAY.center
    if scene_tick < 130:
        text(floor, cx - 35, cy, 26, CYAN, "ko", True, ink_center=True)
        pygame.draw.polygon(screen, MUTED, [(cx - 6, cy + 5), (cx - 6, cy - 6), (cx + 2, cy - 1)])
        text(destination, cx + 33, cy, 22, MUTED, "ko", True, ink_center=True)
    else:
        text(destination, cx, cy, 26, CYAN, "ko", True, ink_center=True)


# ---------------------------------------------------------------------------
# Touch / mouse controls for the web version.
# Each on-screen button sends the same key the keyboard would, so the game
# logic is unchanged. Several fingers are tracked at once (move + press E).
# ---------------------------------------------------------------------------
CONTROLS = []          # dicts: rect, key, label, sub
PAD_CENTER, PAD_RADIUS, PAD_DEAD = (120, 470), 112, 20
pointers = {}          # pointer id -> (x, y) in window pixels
pointer_button = {}    # pointer id -> control currently pressed by that pointer
last_orientation_check, portrait_mode = -999, False


class VirtualKeys:
    """Behaves like pygame.key.get_pressed(), plus keys held on screen."""
    def __init__(self, real, held):
        self.real, self.held = real, held

    def __getitem__(self, key):
        return bool(self.real[key]) or key in self.held


def build_controls():
    right = WIDTH + SIDE

    def add(x, y, w, h, key, label, sub):
        CONTROLS.append({"rect": pygame.Rect(x - w // 2, y - h // 2, w, h),
                         "key": key, "label": label, "sub": sub})
    add(120, 70, 200, 58, pygame.K_ESCAPE, "ESC", "설명서")
    add(120, 140, 200, 58, pygame.K_h, "H", "힌트")
    add(120, 210, 200, 58, pygame.K_q, "Q", "층 초기화")
    add(right + 120, 300, 180, 120, pygame.K_r, "R", "기록 / 저장")
    add(right + 120, 450, 180, 120, pygame.K_e, "E", "장치 사용")
    add(right + 120, 618, 200, 92, pygame.K_SPACE, "SPACE", "확인 · 계속")


def pad_direction(pos):
    """Return held movement keys for a pointer on the round pad (8 directions)."""
    dx, dy = pos[0] - PAD_CENTER[0], pos[1] - PAD_CENTER[1]
    distance = math.hypot(dx, dy)
    if distance < PAD_DEAD or distance > PAD_RADIUS * 1.35:
        return set()
    nx, ny = dx / distance, dy / distance
    held = set()
    if nx > .38: held.add(pygame.K_d)
    if nx < -.38: held.add(pygame.K_a)
    if ny > .38: held.add(pygame.K_s)
    if ny < -.38: held.add(pygame.K_w)
    return held


def held_keys():
    held = set()
    for pointer, pos in pointers.items():
        if pointer_button.get(pointer) == "pad":
            held |= pad_direction(pos)
    return held


def pointer_down(pointer, pos):
    """Returns True when the game should reset its frame timing (like handle_key)."""
    pointers[pointer] = pos
    for control in CONTROLS:
        if control["rect"].collidepoint(pos):
            pointer_button[pointer] = control["key"]
            return handle_key(control["key"])
    if math.dist(pos, PAD_CENTER) <= PAD_RADIUS * 1.15:
        pointer_button[pointer] = "pad"
        if manual_open:
            # In the manual the pad pages (left/right) and scrolls (up/down).
            direction = pad_direction(pos)
            for game_key, manual_key_code in ((pygame.K_a, pygame.K_LEFT), (pygame.K_d, pygame.K_RIGHT),
                                              (pygame.K_w, pygame.K_UP), (pygame.K_s, pygame.K_DOWN)):
                if game_key in direction:
                    handle_key(manual_key_code)
        return False
    pointer_button[pointer] = None
    if SIDE <= pos[0] < SIDE + WIDTH:
        return handle_click(pos)       # taps on the game picture act like clicks
    return False


def pointer_move(pointer, pos):
    if pointer in pointers:
        pointers[pointer] = pos


def pointer_up(pointer):
    pointers.pop(pointer, None)
    pointer_button.pop(pointer, None)


def check_portrait():
    """Phones held upright show the game too small; ask the player to rotate."""
    global last_orientation_check, portrait_mode
    now = pygame.time.get_ticks()
    if not WEB or now - last_orientation_check < 500:
        return portrait_mode
    last_orientation_check = now
    try:
        import platform  # pygbag exposes the browser window here
        portrait_mode = platform.window.innerHeight > platform.window.innerWidth
    except Exception:
        portrait_mode = False
    return portrait_mode


def draw_controls():
    if not SIDE:
        return
    for x in (0, WIDTH + SIDE):
        pygame.draw.rect(window, (8, 11, 15), (x, 0, SIDE, HEIGHT))
    pressed = set(pointer_button.values())
    held = held_keys()
    # Movement pad
    pygame.draw.circle(window, (22, 30, 36), PAD_CENTER, PAD_RADIUS)
    pygame.draw.circle(window, (69, 82, 89), PAD_CENTER, PAD_RADIUS, 2)
    for key, (ax, ay) in ((pygame.K_w, (0, -1)), (pygame.K_s, (0, 1)),
                          (pygame.K_a, (-1, 0)), (pygame.K_d, (1, 0))):
        cx, cy = PAD_CENTER[0] + ax * 70, PAD_CENTER[1] + ay * 70
        tip, base = (cx + ax * 18, cy + ay * 18), (cx - ax * 12, cy - ay * 12)
        side = (-ay * 18, ax * 18)
        color = CYAN if key in held else MUTED
        pygame.draw.polygon(window, color, (tip, (base[0] + side[0], base[1] + side[1]),
                                            (base[0] - side[0], base[1] - side[1])))
    pygame.draw.circle(window, (45, 58, 66), PAD_CENTER, 26)
    label = fonts["en"][20].render("W A S D", True, MUTED)
    window.blit(label, label.get_rect(center=(PAD_CENTER[0], PAD_CENTER[1] + PAD_RADIUS + 26)))
    # Buttons
    for control in CONTROLS:
        rect, active = control["rect"], control["key"] in pressed
        pygame.draw.rect(window, (34, 48, 56) if active else (20, 28, 34), rect, border_radius=14)
        pygame.draw.rect(window, CYAN if active else (69, 82, 89), rect, 2, border_radius=14)
        big = rect.h >= 90
        title = fonts["en"][38 if big else 26].render(control["label"], True, INK)
        sub = fonts["ko"][18 if big else 16].render(control["sub"], True, MUTED)
        if big:
            window.blit(title, title.get_rect(center=(rect.centerx, rect.centery - 14)))
            window.blit(sub, sub.get_rect(center=(rect.centerx, rect.centery + 26)))
        else:
            window.blit(title, title.get_rect(midleft=(rect.x + 18, rect.centery)))
            window.blit(sub, sub.get_rect(midright=(rect.right - 16, rect.centery)))
    if check_portrait():
        veil = pygame.Surface(window.get_size(), pygame.SRCALPHA)
        veil.fill((6, 9, 13, 235))
        window.blit(veil, (0, 0))
        for i, line in enumerate(("휴대폰을 가로로 돌려 주세요", "Rotate your phone to landscape")):
            words = fonts["ko" if i == 0 else "en"][48 if i == 0 else 30].render(line, True, INK if i == 0 else MUTED)
            window.blit(words, words.get_rect(center=(window.get_width() // 2, HEIGHT // 2 - 30 + i * 70)))


async def main():
    initialize()
    running, accumulator = True, 0.0
    while running:
        elapsed = min(clock.tick(FPS) / 1000, .25)
        reset_frame = False
        for event in pygame.event.get():
            touch_mouse = getattr(event, "touch", False)  # mouse events SDL copies from touches
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not reset_frame:
                reset_frame = handle_key(event.key)
            elif SIDE and event.type == pygame.FINGERDOWN:
                w, h = window.get_size()
                reset_frame = pointer_down(("finger", event.finger_id), (event.x * w, event.y * h)) or reset_frame
            elif SIDE and event.type == pygame.FINGERMOTION:
                w, h = window.get_size()
                pointer_move(("finger", event.finger_id), (event.x * w, event.y * h))
            elif SIDE and event.type == pygame.FINGERUP:
                pointer_up(("finger", event.finger_id))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not touch_mouse:
                if SIDE:
                    reset_frame = pointer_down("mouse", event.pos) or reset_frame
                else:
                    reset_frame = handle_click(event.pos) or reset_frame
            elif SIDE and event.type == pygame.MOUSEMOTION and not touch_mouse:
                pointer_move("mouse", event.pos)
            elif SIDE and event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not touch_mouse:
                pointer_up("mouse")
            elif event.type == pygame.MOUSEWHEEL and manual_open:
                scroll_manual(-event.y * 52)
        if not running:
            break
        # Phones never give the canvas keyboard focus, so the web build does not pause on it.
        focused = True if WEB else bool(pygame.key.get_focused())
        set_audio_focus(focused)
        if reset_frame or not focused:
            accumulator = 0
        else:
            keys = pygame.key.get_pressed()
            if SIDE:
                keys = VirtualKeys(keys, held_keys())
            accumulator = advance_simulation(elapsed, keys, accumulator)
        draw_game()
        await asyncio.sleep(0)  # hand control back to the browser every frame
    if not WEB:
        pygame.quit()


def blocked(next_rect):
    current = actor_rect(px, py)
    if not on_floor(next_rect) or next_rect.collidelist(walls) >= 0:
        return True
    if any(next_rect.colliderect(obj[key]) for key in solids):
        return True
    for key in (*doors, "lift"):
        area = obj[key]
        if next_rect.colliderect(area) and not current.colliderect(area):
            if not door_open(key) or door_amounts[key] < .92:
                return True
    return False


def can_use(key, x, y):
    if key not in devices or not near(obj[key], x, y):
        return False
    if floor == "B1":
        if key == "mirror":
            return x < 411 or y > 533
        if key == "release":
            return 436 < x < 640 and y >= 336
        return y > obj[key].bottom
    blockers = doors if floor in ("B6", "B5") else (*doors, "lift")
    obstacles = walls + [obj[door] for door in blockers if door_amounts[door] < .92]
    return not any(wall.clipline((x, y), obj[key].center) for wall in obstacles)


def exit_open():
    if floor == "B6":
        return state["lift_power"]
    if floor == "B5":
        return any(gap_end <= distance < cable_length for distance in state["pulses"])
    if floor == "B4":
        return state["route"] == "B" and state["powered"]
    if floor == "B3":
        return state["lever_on"]
    if floor == "B2":
        return state["source"] and state["m1"] == 2 and state["m2"] == 2 and state["beam_age"] >= 18
    return state["stable"] and state["charge"] > 0 and state["lift_mode"]


def door_open(key):
    if key == "lift":
        return exit_open()
    if floor == "B6":
        return not state["lift_power"]
    if floor == "B5":
        return not state["sealed"]
    if floor == "B4":
        return state["powered"] and key[-1].upper() == state["route"]
    if floor == "B3":
        return state["scanner_on"] if key == "archive_in" else state["return_timer"] > 0
    if floor == "B2":
        return state["service_open"]
    if key == "charge_in":
        return state["charge"] == 0 and not state["lift_mode"]
    if key == "charge_out":
        return not state["lift_mode"]
    if key == "power_gate":
        return state["charge"] > 0 and not state["lift_mode"]
    if key == "release_in":
        return not state["lift_mode"] and state["mirror"] == 1 and state["mirror_turn"] == 0
    return occupied(obj["sensor"]) or occupied(obj["release_out"])


def use_action(action, x, y, source="player"):
    global device_flash
    if not can_use(action, x, y):
        return False
    if floor == "B6":
        state["lift_power"] = not state["lift_power"]
        device_flash = 18
    elif floor == "B5":
        if action == "mode":
            state["sealed"] = not state["sealed"]
        else:
            state["pulses"].append(0.0)
    elif floor == "B4":
        if action == "selector":
            state["route"] = "B" if state["route"] == "A" else "A"
            state["powered"] = False
        elif action == "decoy":
            state["test_pulses"].append(0)
        else:
            state["powered"] = True
    elif floor == "B3":
        if not state["permit"] or not all(door_closed(key) for key in doors):
            device_flashes["refused"] = 24
            sound("refuse", source)
            return False
        state["lever_on"] = True
    elif floor == "B2":
        if state["beam_age"] < 18:
            sound("refuse", source)
            return False
        state["old_beams"] = beam_paths()
        state["old_m1"], state["old_m2"] = state["m1"], state["m2"]
        if action in ("mirror1", "mirror2"):
            key = "m1" if action == "mirror1" else "m2"
            state[key] = (state[key] + 1) % 3
        else:
            state["source"] = action == "source_on"
        state["beam_age"] = 0
    elif action == "mirror":
        state["mirror"] = (state["mirror"] + 1) % 3
        state["mirror_turn"] = 18
        state["stable"] = False
    elif action == "mode":
        state["lift_mode"] = not state["lift_mode"]
        state["stable"] = False
    elif action == "charge" and not state["lift_mode"]:
        state["charge"], state["stable"] = POWER_SECONDS * FPS, False
    elif action == "release" and core_ready():
        state["pulses"].append(0.0)
        state["release_cooldown"] = 18
    else:
        sound("refuse", source)
        return False
    device_flashes[action] = 24 if floor == "B2" else 18
    sound(DEVICE_SOUNDS[floor][action], source)
    return True


def update_room(keys, pressed_e=False):
    global replay_started, recording, pending_e, device_flash
    if manual_open:
        return
    help_progress[floor]["ticks"] += 1
    if floor == "B5":
        update_pulses()  # Expiry closes the lift before the next movement.
    elif floor == "B2":
        update_optics()
    if move_player(keys):
        replay_started = True
    actions = update_ghosts()
    if floor == "B3":
        update_sensors()  # Current actor positions must reach sensors first.
    for action, x, y in actions:
        use_action(action, x, y, source="ghost")
    if pressed_e or pending_e:
        interact(len(record_path) if replay_started else 0)
        pending_e = False
    if recording and replay_started:
        record_path.append(pose())
    if floor == "B4":
        state["fault_ticks"] = max(0, state["fault_ticks"] - 1)
        travelling = []
        for age in state["test_pulses"]:
            if age + 1 >= 27:
                sparks.append([BROKEN_CABLE[-1], 30])
                state["fault_ticks"] = 42
                sound("sputter")
            else:
                travelling.append(age + 1)
        state["test_pulses"] = travelling
    elif floor == "B1":
        update_power()
    for key in (*doors, "lift"):
        target = float(door_open(key) or actor_rect(px, py).colliderect(obj[key]))
        value = door_amounts[key]
        door_amounts[key] = min(target, value + .12) if target > value else max(target, value - .12)
    device_flash = max(0, device_flash - 1)
    for key in device_flashes:
        device_flashes[key] = max(0, device_flashes[key] - 1)
    for spark in sparks:
        spark[1] -= 1
    sparks[:] = [spark for spark in sparks if spark[1] > 0]
    if floor == "B2" and beam_hits(pose(), dangerous_beams()):
        restart_run(clear=True)
        sound("failure")
        set_scene("failed")
    elif scene == "play" and exit_open() and door_amounts["lift"] > .92:
        if actor_rect(px, py).colliderect(obj["lift"]):
            recording = False
            set_scene("lift")
            sound("motor")


def handle_key(key):
    global pending_e
    if manual_open:
        return manual_key(key)
    if key == pygame.K_ESCAPE:
        open_manual()
        return True
    if key == pygame.K_h and scene == "play" and hint_available():
        open_manual(2)
        reveal_hint()
        return True
    if scene == "title":
        if key == pygame.K_SPACE:
            start_game()
            return True
        return False
    if key == pygame.K_q and scene in ("play", "thought", "skill", "failed"):
        restart_run(clear=True)
        return True
    if key == pygame.K_SPACE:
        if scene == "thought":
            set_scene("skill" if SKILL else "play")
        elif scene == "skill":
            set_scene("play")
        elif scene == "failed":
            restart_run(clear=True)
        elif scene == "outside" and scene_tick >= 300:
            set_scene("title")
        else:
            return False
        return True
    if scene == "play":
        if key == pygame.K_e:
            pending_e = True
        elif key == pygame.K_r:
            stopping = recording
            toggle_recording()
            return stopping
    return False


def start_game():
    reset_help()
    build_floor("B6")
    open_manual(startup=True)
    if audio_channels:
        # Start the ordinary and filtered copies together; Q never restarts them.
        for name in ("music", "lift_music"):
            audio_channels[name].play(audio_tracks[name], loops=-1)
    sound("start")


def advance_simulation(elapsed, keys, accumulator):
    global ui_tick, scene_tick
    if manual_open:
        return 0.0
    accumulator += min(elapsed, .25)
    while accumulator + 1e-10 >= 1 / FPS:
        accumulator -= 1 / FPS
        ui_tick += 1
        scene_tick += 1
        if scene == "play":
            update_room(keys)
        elif scene == "lift":
            if scene_tick == 130:
                sound("chime")
            if scene_tick >= 180:
                index = FLOORS.index(floor)
                if index + 1 < len(FLOORS):
                    build_floor(FLOORS[index + 1])
                else:
                    set_scene("outside")
        update_audio()
    return max(0.0, accumulator)


def draw_door(key):
    area = DOOR_ART[key]
    old_clip = screen.get_clip()
    screen.set_clip(area)
    amount = door_amounts[key]
    if floor == "B1" and key == "lift" and amount > 0:
        # Light is revealed by the opening leaves, after the final puzzle works.
        exit_inside_light.set_alpha(round(255 * amount))
        screen.blit(exit_inside_light, area)
    if floor == "B5" and key == "shutter":
        offset = round(area.h * amount)
        screen.blit(door_panels[key][0], (area.x, area.y - offset))
    else:
        left, right = door_panels[key]
        offset = round(area.w * amount / 2)
        screen.blit(left, (area.x - offset, area.y))
        screen.blit(right, (area.x + left.get_width() + offset, area.y))
    screen.set_clip(old_clip)
    color = GREEN if door_open(key) else AMBER
    if floor == "B6":
        if key == "gate":
            for post in post_images:
                screen.blit(post, (0, 0))
            for x in (364, 602):
                pygame.draw.rect(screen, color, (x, 382, 3, 8))
        else:
            pygame.draw.polygon(screen, color, [(487, 140), (482, 147), (492, 147)])
    elif floor == "B5":
        if key == "shutter":
            connected = state["sealed"] and amount <= .08
            if connected:
                pygame.draw.line(screen, (47, 38, 24), (352, 586), (391, 586), 7)
                pygame.draw.line(screen, (158, 118, 61), (352, 586), (391, 586), 4)
                pygame.draw.line(screen, (206, 169, 107), (352, 585), (391, 585), 1)
            for x in (352, 391):
                pygame.draw.line(screen, GREEN if connected else AMBER, (x, 583), (x, 589), 2)
        else:
            pygame.draw.polygon(screen, color, [(725, 76), (721, 82), (729, 82)])
    elif floor == "B1":
        for x in (area.left - 2, area.right + 1):
            pygame.draw.rect(screen, (30, 35, 37), (x - 2, area.y + 7, 5, 12))
            pygame.draw.line(screen, color, (x, area.y + 9), (x, area.y + 16), 2)
        if key == "lift" and amount <= .02:
            pygame.draw.line(screen, (239, 221, 176),
                             (area.centerx, area.top + 12), (area.centerx, area.bottom - 3), 1)
    elif key == "lift":
        pygame.draw.circle(screen, color, (793, 152) if floor == "B4" else (790, 155), 3)


def draw_actor(data, kind):
    x, y, direction, frame = data
    collection = sprites if kind == "player" else echoes if kind == "active" else faded
    picture = collection[(direction, frame)]
    point = round(x), round(y)
    if kind == "player":
        shadow = pygame.Surface((40, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        screen.blit(shadow, (point[0] - 20, point[1] - 6))
    bounds = picture.get_rect(midbottom=point)
    screen.blit(picture, bounds)
    if floor == "B2":
        # At screen row s the ray occupies floor depth s + BEAM_HEIGHT.
        # Restore only rays in front of this actor's feet. A ray farther back
        # stays occluded, irrespective of which way the sprite is facing.
        front = pygame.Surface(picture.get_size(), pygame.SRCALPHA)
        front.blit(beam_layer, (0, 0), bounds)
        split = round(y - BEAM_HEIGHT) - bounds.top
        front.fill((0, 0, 0, 0), (0, 0, bounds.w, max(0, min(bounds.h, split))))
        shape = picture.copy()
        shape.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
        front.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(front, bounds)


def draw_game():
    if scene == "play":
        draw_world()
    elif scene == "lift":
        draw_lift()
    elif scene == "outside":
        screen.blit(images["outside"], (0, 0))
        t = min(1, max(0, (scene_tick - 30) / 240))
        frame = (1, 0, 2, 0)[(scene_tick // 10) % 4] if t < 1 else 0
        picture = sprites[("up", frame)]
        height = round(88 - 19 * t)
        picture = pygame.transform.smoothscale(picture, (round(picture.get_width() * height / 88), height))
        screen.blit(picture, picture.get_rect(midbottom=(480, round(672 - 190 * t))))
        if scene_tick < 60:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, max(0, 255 - scene_tick * 255 // 60)))
            screen.blit(shade, (0, 0))
        if scene_tick >= 300:
            text("SPACE  TITLE", 480, 683, 20, (35, 46, 44), center=True)
    else:
        screen.fill((9, 12, 17))
        if scene == "title":
            text("RE:TRACE", 480, 270, 110, INK, center=True)
            pygame.draw.line(screen, (66, 84, 92), (270, 346), (690, 346), 1)
            text("PRESS SPACE TO START", 480, 430, 26, INK, center=True)
        elif scene in ("thought", "skill"):
            alpha = min(255, scene_tick * 255 // 36)
            lines = THOUGHT if scene == "thought" else SKILL
            y = HEIGHT / 2 - (len(lines) - 1) * 20
            if scene == "skill":
                text(SKILL_TITLE, 480, y - 62, 26, AMBER if SKILL_TITLE == "CAUTION" else CYAN,
                     "en", True, alpha, True)
            for i, line in enumerate(lines):
                text(line, 480, y + i * 40, 22 if scene == "skill" else 26, INK, "ko", True, alpha, True)
            if scene == "skill" and floor == "B6":
                # Static and easy to find; the normal HUD remains R / E / Q.
                text("WASD  —  MOVE", 480, y + len(lines) * 40 + 30,
                     26, CYAN, center=True, ink_center=True)
            text("SPACE  CONTINUE", 480, 605, 20, MUTED, center=True)
        elif scene == "failed" and floor == "B1":
            draw_world()
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((9, 12, 17, 218))
            screen.blit(veil, (0, 0))
            text(state["failure"], 480, 315, 48, INK, center=True)
            text("SPACE  RESTART FLOOR", 480, 405, 26, INK, center=True)
            text("All recordings will be cleared. Hints are kept.", 480, 448, 22, MUTED, center=True)
        elif scene == "failed":
            text("SIGNAL LOST", 480, 295, 48, RED, center=True)
            text("Laser contact. This floor has been reset.", 480, 365, 22, MUTED, center=True)
            text("SPACE  RETRY", 480, 455, 22, INK, center=True)
    if manual_open:
        draw_manual(min(.1, clock.get_time() / 1000))
    width, height = window.get_size()
    scale = min(width / WIDTH, height / HEIGHT)
    size = max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale))
    if size == (WIDTH, HEIGHT):
        window.blit(screen, ((width - WIDTH) // 2, (height - HEIGHT) // 2))
    else:
        window.fill((6, 9, 13))
        window.blit(pygame.transform.smoothscale(screen, size), ((width - size[0]) // 2, (height - size[1]) // 2))
    draw_controls()
    pygame.display.flip()


def along_path(points, fraction):
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    distance = max(0, min(1, fraction)) * sum(lengths)
    for a, b, length in zip(points, points[1:], lengths):
        if distance <= length:
            t = distance / length
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        distance -= length
    return points[-1]


def cable_point(distance):
    # Keep the original three timing sections while fitting the painted cable.
    if distance < gap_start:
        return along_path(CABLE_IN, distance / gap_start)
    if distance < gap_end:
        return along_path([CABLE_IN[-1], CABLE_OUT[0]],
                          (distance - gap_start) / (gap_end - gap_start))
    return along_path(CABLE_OUT, (distance - gap_end) / (cable_length - gap_end))


def update_pulses():
    remaining = []
    for old in state["pulses"]:
        new = old + 4
        connected = state["sealed"] and door_amounts["shutter"] <= .08
        if old < gap_end and new >= gap_start and not connected:
            sparks.append([cable_point(max(gap_start, old)), 30])
            sound("sputter")
        elif new >= cable_length:
            sparks.append([CABLE_OUT[-1], 30])
            sound("sputter")
        else:
            remaining.append(new)
    state["pulses"] = remaining


def door_closed(key):
    return not door_open(key) and door_amounts[key] <= .08


def update_sensors():
    state["scanner_on"] = occupied(obj["scanner"])
    state["permit"] |= state["scanner_on"]
    detected = occupied(obj["sensor"])
    player_body = actor_rect(px, py)
    # Announce a new detection once, not every tick someone remains on the panel.
    if detected and not state["return_sensor_on"]:
        sound("sensor", "player" if player_body.colliderect(obj["sensor"]) else "ghost")
    state["return_sensor_on"] = detected
    if detected or (door_amounts["archive_out"] > .08 and occupied(obj["archive_out"])):
        state["return_timer"] = 48
    else:
        state["return_timer"] = max(0, state["return_timer"] - 1)
    # Either open door drops the lever. The audible clunk belongs to that change.
    if state["lever_on"] and any(door_open(key) for key in doors):
        state["lever_on"] = False
        source = "player" if any(player_body.colliderect(obj[key])
                                 for key in ("scanner", "sensor", "archive_out")) else "ghost"
        sound("lever_reset", source)


def draw_sensor(key, active, color):
    corners = SENSOR_ART[key]
    dim = tuple(value // 3 for value in color)
    pygame.draw.polygon(screen, color if active else dim, corners, 1)
    for point in corners:
        pygame.draw.circle(screen, color if active else dim, point, 3, 1)
    if active:
        top_left, top_right, bottom_right, bottom_left = corners
        travel = max(1, obj[key].h - 4)
        amount = .04 + .92 * ((ui_tick * .8) % travel) / travel
        left = pygame.Vector2(top_left).lerp(bottom_left, amount)
        right = pygame.Vector2(top_right).lerp(bottom_right, amount)
        pygame.draw.line(screen, color, (round(left.x + 3), round(left.y)),
                         (round(right.x - 3), round(right.y)), 2)


def beam_paths():
    if not state["source"]:
        return []
    first, second = OPTICS["mirror1"], OPTICS["optic2"]
    paths = [(OPTICS["emitter"], first), (first, OPTICS[TARGETS[0][state["m1"]]])]
    if state["m1"] == 2:
        paths.append((second, OPTICS[TARGETS[1][state["m2"]]]))
    return paths


def dangerous_beams():
    if state["beam_age"] < 6:
        return state["old_beams"]
    return beam_paths() if state["beam_age"] >= 18 else []


def beam_body_rect(x, y):
    # A compact body footprint centred at the feet, in floor coordinates.
    # Height affects drawing, never a 48-pixel lethal strip behind the device.
    return pygame.Rect(round(x) - 8, round(y) - 10, 16, 20)


def beam_hits(actor, paths):
    # Elliptical ground footprint: rectangular corners must not catch a nearby
    # diagonal ray while the player's body is safely beside a mirror.
    body = beam_body_rect(actor[0], actor[1])
    rx, ry = body.w / 2 + 1, body.h / 2 + .5
    for a, b in paths:
        start = pygame.Vector2((a[0] - actor[0]) / rx, (a[1] - actor[1]) / ry)
        end = pygame.Vector2((b[0] - actor[0]) / rx, (b[1] - actor[1]) / ry)
        delta = end - start
        fraction = max(0, min(1, -start.dot(delta) / delta.length_squared())) if delta.length_squared() else 0
        if (start + fraction * delta).length_squared() <= 1:
            return True
    return False


def update_optics():
    state["beam_age"] = min(18, state["beam_age"] + 1)
    if state["source"] and state["beam_age"] >= 18 and state["m1"] == 1:
        state["service_open"] = True


def screen_point(point):
    return round(point[0]), round(point[1] - BEAM_HEIGHT)


def draw_beam(a, b, color, alpha=255, warning=False):
    start, end = pygame.Vector2(screen_point(a)), pygame.Vector2(screen_point(b))
    if warning:
        length = start.distance_to(end)
        for step in range(0, int(length), 15):
            left, right = start.lerp(end, step / length), start.lerp(end, min(1, (step + 6) / length))
            pygame.draw.line(beam_layer, (*color, alpha), left, right, 1)
    else:
        pygame.draw.line(beam_layer, (*color, alpha // 8), start, end, 13)
        pygame.draw.line(beam_layer, (*color, alpha // 3), start, end, 6)
        pygame.draw.line(beam_layer, (*color, alpha), start, end, 2)
        pygame.draw.circle(beam_layer, (*color, alpha), end, 3)


def prepare_beams():
    beam_layer.fill((0, 0, 0, 0))
    age = state["beam_age"]
    if age < 6:
        for a, b in state["old_beams"]:
            draw_beam(a, b, RED, 255 - age * 32)
    elif age < 18:
        for a, b in beam_paths():
            draw_beam(a, b, AMBER, 120 + (age - 6) * 10, True)
    else:
        for a, b in beam_paths():
            draw_beam(a, b, RED)


def mirror_angle(index, setting):
    origin = pygame.Vector2(OPTICS["mirror1" if index == 0 else "optic2"])
    incoming = pygame.Vector2(0, -1) if index == 0 else pygame.Vector2(1, 0)
    outgoing = (pygame.Vector2(OPTICS[TARGETS[index][setting]]) - origin).normalize()
    normal = incoming - outgoing
    tangent = incoming if normal.length_squared() < .01 else pygame.Vector2(-normal.y, normal.x)
    return math.atan2(tangent.y, tangent.x)


def draw_mirror(index):
    key = "m1" if index == 0 else "m2"
    optic = "mirror1" if index == 0 else "optic2"
    center = pygame.Vector2(screen_point(OPTICS[optic]))
    old, new = mirror_angle(index, state["old_" + key]), mirror_angle(index, state[key])
    turn = (new - old + math.pi / 2) % math.pi - math.pi / 2
    angle = old + turn * min(1, state["beam_age"] / 18)
    direction = pygame.Vector2(math.cos(angle), math.sin(angle))
    normal = pygame.Vector2(-direction.y, direction.x)
    corners = [center + direction * a + normal * b for a, b in ((-13, -3), (13, -3), (13, 3), (-13, 3))]
    pygame.draw.polygon(screen, (49, 64, 72), corners)
    pygame.draw.polygon(screen, (181, 201, 208), corners, 1)
    pygame.draw.line(screen, CYAN, center - direction * 11 - normal * 2,
                     center + direction * 11 - normal * 2, 2)


def draw_symbol(center, color):
    x, y = center
    pygame.draw.polygon(screen, color, [(x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y)], 1)
    pygame.draw.line(screen, color, (x - 3, y), (x + 3, y), 1)


def draw_wall(key):
    screen.blit(*room_parts[key])
    if key == "right_barrier":
        # This short ray travels in front of the partition into its absorber.
        bounds = room_parts[key][1]
        screen.blit(beam_layer, bounds, bounds)
    elif key == "service_front":
        color = GREEN if state["service_open"] else AMBER
        if state["service_open"]:
            pygame.draw.lines(screen, GREEN, False, [(360, 364), (444, 364), (444, 336)], 2)
        pygame.draw.rect(screen, (29, 39, 42), (434, 326, 15, 16), border_radius=2)
        pygame.draw.rect(screen, color, (438, 334, 7, 5), 1)
        pygame.draw.arc(screen, color, (438, 328, 7, 9), 0, math.pi, 1)
        if state["service_open"]:
            pygame.draw.line(screen, (29, 39, 42), (444, 332), (444, 334), 2)
    elif key == "divider":
        # A small optical port is separate from the solid pedestrian wall.
        pygame.draw.rect(screen, (67, 76, 81), (598, 383, 20, 36), border_radius=3)
        pygame.draw.rect(screen, (112, 121, 125), (598, 383, 20, 36), 1, border_radius=3)
        pygame.draw.circle(screen, (18, 27, 32), (608, 394), 6)
        crossing = state["source"] and state["m1"] == 2
        old_crossing = any(a[0] < 608 < b[0] for a, b in state["old_beams"])
        if crossing and state["beam_age"] >= 6 or old_crossing and state["beam_age"] < 6:
            color = RED if state["beam_age"] < 6 or state["beam_age"] >= 18 else AMBER
            pygame.draw.circle(screen, color, (608, 394), 4, 1)


def room_sealed():
    return all(not door_open(key) and door_amounts[key] < .08
               for key in ("release_in", "release_out"))


def update_power():
    global recording
    for key in ("drain_flash", "release_cooldown", "mirror_turn"):
        state[key] = max(0, state[key] - 1)
    angle = (0, -.75, .75)[state["mirror"]]
    state["mirror_angle"] += (angle - state["mirror_angle"]) * .24
    if occupied(obj["drain"]) and state["charge"] > 0:
        state["charge"], state["stable"], state["drain_flash"] = 0, False, 45
        sound("shutdown")
        if state["lift_mode"]:
            state["failure"] = "POWER DISCHARGED"
            recording = False
            set_scene("failed")
    connected = (state["lift_mode"] and state["charge"] > 0 and room_sealed()
                 and state["mirror"] == 2 and state["mirror_turn"] == 0)
    if not connected:
        state["stable"] = False
    remaining = []
    for distance in state["pulses"]:
        distance += 7
        if not connected:
            state["sparks"].append([wire_point(SIGNAL_WIRE, distance), 18])
            sound("sputter")
        elif distance < wire_length(SIGNAL_WIRE):
            remaining.append(distance)
        else:
            state["stable"] = True
            sound("chime")
    state["pulses"] = remaining
    state["sparks"] = [[p, life - 1] for p, life in state["sparks"] if life > 1]
    if state["lift_mode"] and state["charge"] > 0 and not state["stable"]:
        state["charge"] -= 1
        if state["charge"] <= 3 * FPS and state["charge"] % FPS == 0:
            sound("tick")
        if state["charge"] == 0:
            sound("shutdown")
            recording = False
            set_scene("failed")
    target = state["charge"] / (POWER_SECONDS * FPS)
    state["charge_level"] += max(-1 / 45, min(.08, target - state["charge_level"]))
    state["mode_blend"] += max(-.1, min(.1, float(state["lift_mode"]) - state["mode_blend"]))


def draw_optics():
    # The protected wall rail is separate from the walkable floor: no hidden laser hitbox.
    center = (512, 154)
    target = ((512, 194), (388, 154), (640, 154))[state["mirror"]]
    brightness = 1 - state["mirror_turn"] / 18
    if brightness > .05:
        color = tuple(int(c * brightness) for c in CYAN)
        path = [(512, 118), center] if state["mirror"] == 0 else [(512, 118), center, target]
        pygame.draw.lines(screen, (42, 71, 78), False, path, 7)
        pygame.draw.lines(screen, color, False, path, 2)
    # The upright setting has no outgoing route; only the two working side receivers remain.
    for point in ((512, 118), (388, 154), (640, 154)):
        pygame.draw.circle(screen, (35, 42, 43), point, 8)
        pygame.draw.circle(screen, MUTED, point, 8, 1)
        pygame.draw.circle(screen, CYAN if point == target and brightness > .8 else (61, 85, 90), point, 4)
    angle = state["mirror_angle"]
    dx, dy = math.sin(angle) * 14, math.cos(angle) * 14
    a, b = (512 - dx, 154 - dy), (512 + dx, 154 + dy)
    pygame.draw.circle(screen, (33, 43, 47), center, 17)
    pygame.draw.line(screen, MUTED, a, b, 8)
    pygame.draw.line(screen, CYAN, a, b, 3)


def draw_device(key):
    if floor == "B6":
        x, y = obj["switch"].centerx, obj["switch"].bottom
        box = lever_image.get_rect(midbottom=(x, y))
        screen.blit(lever_image, box)
        pivot = (x, box.y + 21)
        engaged = state["lift_power"]
        end = (x + (12 if engaged else -12), box.y + 4)
        pygame.draw.line(screen, (19, 26, 31), pivot, end, 7)
        pygame.draw.line(screen, (179, 180, 170), pivot, end, 4)
        pygame.draw.circle(screen, GREEN if engaged else RED, end, 4)
        pygame.draw.circle(screen, GREEN if engaged else (43, 61, 68), (x, box.bottom - 8), 3)
    elif floor == "B5":
        # The housing is painted into the background. Only its control changes.
        screen.blit(room_parts[key], (0, 0))
        if key == "transmitter":
            center = (155, 532 + int(device_flashes.get(key, 0) > 10))
            pygame.draw.circle(screen, (16, 29, 33), center, 8)
            pygame.draw.circle(screen, CYAN, center, 6, 2)
            pygame.draw.line(screen, INK, (151, center[1]), (159, center[1]), 2)
        else:
            angle = math.radians(-55 + 110 * (1 - door_amounts["shutter"]))
            end = (530 + round(math.sin(angle) * 14), 573 - round(math.cos(angle) * 14))
            pygame.draw.line(screen, (31, 32, 29), (530, 573), end, 5)
            pygame.draw.line(screen, AMBER, (530, 573), end, 2)
            pygame.draw.circle(screen, AMBER, end, 2)
            # A small physical diagram shows whether the contacts are joined.
            color = GREEN if state["sealed"] and door_amounts["shutter"] <= .08 else AMBER
            for x in (518, 542):
                pygame.draw.line(screen, color, (x, 533), (x, 541), 2)
            if state["sealed"] and door_amounts["shutter"] <= .08:
                pygame.draw.line(screen, color, (518, 537), (542, 537), 2)
    elif floor == "B4":
        screen.blit(*room_parts[key])
        if key != "selector":
            x, y = BUTTON_CENTERS[key]
            y += int(device_flashes.get(key, 0) > 10)
            color = AMBER if key == "decoy" and state["fault_ticks"] else CYAN
            pygame.draw.circle(screen, (15, 27, 30), (x, y), 8)
            pygame.draw.circle(screen, color, (x, y), 6, 2)
            pygame.draw.line(screen, INK, (x-4, y), (x+4, y), 2)
        else:
            # Arm position communicates selection; cable light communicates power.
            center = (513, 439)
            end = (526, 448 if state["route"] == "A" else 425)
            for y in (425, 448):
                pygame.draw.circle(screen, MUTED, (528, y), 2, 1)
            pygame.draw.line(screen, (28, 31, 29), center, end, 6)
            pygame.draw.line(screen, AMBER, center, end, 3)
            pygame.draw.circle(screen, AMBER, end, 3)
            pygame.draw.circle(screen, GREEN if state["powered"] else (35, 49, 50), (513, 414), 4)
    elif floor == "B3":
        screen.blit(*room_parts[key])
        pivot = (318, 330)
        end = (331, 311) if state["lever_on"] else (305, 315)
        pygame.draw.line(screen, (25, 30, 32), pivot, end, 6)
        pygame.draw.line(screen, (184, 188, 176), pivot, end, 3)
        pygame.draw.circle(screen, GREEN if state["lever_on"] else AMBER, end, 4)
        for i, door in enumerate(doors):
            ready = door_closed(door)
            color = GREEN if ready else RED if device_flashes.get("refused", 0) else AMBER
            pygame.draw.rect(screen, color, (309, 349 + i * 14, 19, 4), border_radius=1)
        color = CYAN if state["permit"] else RED if device_flashes.get("refused", 0) else (35, 49, 50)
        pygame.draw.circle(screen, color, (318, 383), 2)
    elif floor == "B2":
        picture, bounds = room_parts[key]
        screen.blit(picture, bounds)
        if key in OPTICS:
            # Restore the ray over its receiver face after drawing the upright body.
            screen.blit(beam_layer, bounds, bounds)
        if key in ("mirror1", "optic2"):
            draw_mirror(0 if key == "mirror1" else 1)
            if key == "optic2":
                draw_symbol((780, 417), CYAN)
        elif key == "mirror2":
            angle = -math.pi / 2 + state["m2"] * math.tau / 3
            pygame.draw.line(screen, CYAN, (518, 245),
                             (518 + math.cos(angle) * 9, 245 + math.sin(angle) * 9), 2)
            draw_symbol((518, 274), CYAN)
        elif key in ("service_receiver", "lift_receiver"):
            active = state["service_open"] if key == "service_receiver" else exit_open()
            point = screen_point(OPTICS[key])
            pygame.draw.circle(screen, GREEN if active else (48, 57, 59), point, 7, 2)
            pygame.draw.circle(screen, GREEN if active else AMBER, (point[0], point[1] + 25), 2)
        elif key == "source_on":
            pygame.draw.circle(screen, GREEN if state["source"] else (48, 93, 66), (364, 542), 6)
            pygame.draw.arc(screen, INK, (360, 538, 8, 8), .7, math.tau - .7, 1)
            pygame.draw.line(screen, INK, (364, 536), (364, 541), 1)
        elif key == "emergency_off":
            pygame.draw.rect(screen, RED if state["source"] else AMBER, (774, 277, 8, 8), border_radius=1)
        elif key == "emitter":
            pygame.draw.ellipse(screen, RED if state["source"] else (43, 51, 56), (222, 524, 12, 7))
    elif floor == "B1":
        areas = {"charge": (98, 129, 46, 115), "mode": (865, 183, 28, 61),
                 "release": (502, 264, 40, 65), "mirror": (403, 474, 28, 59)}
        screen.blit(*cutout(pygame.Rect(areas[key])))
        if key == "charge":
            pygame.draw.rect(screen, (16, 29, 33), (108, 158, 26, 63))
            level = state["charge_level"]
            color = GREEN if state["stable"] else AMBER if level < .34 else CYAN
            for i in range(6):
                pygame.draw.rect(screen, color if level > i / 6 else (39, 57, 61), (111, 211 - i * 9, 20, 6))
        elif key == "mode":
            # A recognizable lever face, matching the other floors' controls.
            center = (878, 210)
            pygame.draw.rect(screen, (27, 39, 45), (866, 183, 26, 43), border_radius=3)
            pygame.draw.rect(screen, (149, 164, 165), (866, 183, 26, 43), 1, border_radius=3)
            pygame.draw.circle(screen, (81, 95, 98), center, 8, 2)
            end = (round(870 + state["mode_blend"] * 16), 195)
            pygame.draw.line(screen, (12, 22, 27), center, end, 6)
            pygame.draw.line(screen, (207, 208, 189), center, end, 3)
            pygame.draw.circle(screen, AMBER, end, 4)
            for x, active in ((871, not state["lift_mode"]), (886, state["lift_mode"])):
                pygame.draw.circle(screen, CYAN if active else (57, 77, 84), (x, 221), 2)
        elif key == "mirror":
            angle, center = state["mirror_angle"], (418, 499)
            pygame.draw.circle(screen, (25, 40, 47), center, 9)
            dx, dy = math.sin(angle) * 7, math.cos(angle) * 7
            pygame.draw.line(screen, CYAN, (418 - dx, 499 - dy), (418 + dx, 499 + dy), 3)
            for i, x in enumerate((410, 418, 426)):
                pygame.draw.circle(screen, CYAN if state["mirror"] == i else MUTED, (x, 514), 2)
        else:
            color = GREEN if core_ready() else RED
            pygame.draw.rect(screen, (26, 41, 47), (511, 277, 22, 18), border_radius=2)
            pygame.draw.circle(screen, color, (522, 286), 7, 2)
            pygame.draw.circle(screen, color, (522, 286), 2)
            for x, door in ((508, "release_in"), (534, "release_out")):
                pygame.draw.circle(screen, GREEN if not door_open(door) and door_amounts[door] < .08 else AMBER, (x, 303), 2)


def draw_circuits():
    if floor == "B6":
        # A short floor-mounted connector joins the lever base to the painted conduit.
        points = [(137, 588), (145, 588), (145, 540)]
        pygame.draw.lines(screen, (22, 25, 28), False, [(x + 1, y + 2) for x, y in points], 6)
        pygame.draw.lines(screen, (83, 84, 78), False, points, 4)
        pygame.draw.lines(screen, (134, 132, 117), False, points, 1)
        for y in (555, 575):
            pygame.draw.line(screen, (55, 56, 54), (142, y), (148, y), 3)
        groups = ((COMMON_LIGHTS, True, AMBER),
                  (GATE_LIGHTS, not state["lift_power"], AMBER),
                  (LIFT_LIGHTS, state["lift_power"], CYAN))
        for windows, active, color in groups:
            for a, b in windows:
                pygame.draw.line(screen, (29, 42, 47), a, b, 5)
                if active:
                    pygame.draw.line(screen, tuple(v // 3 for v in color), a, b, 5)
                    pygame.draw.line(screen, color, a, b, 2)
        # A single small lamp on the actual wall-mounted junction at the lift.
        pygame.draw.rect(screen, CYAN if exit_open() else (43, 56, 62), (417, 174, 4, 9))
    elif floor == "B4":
        for key, path in INPUTS.items():
            if device_flashes.get(key, 0):
                pygame.draw.lines(screen, CYAN, False, path, 2)
        if any(device_flashes.get(key, 0) for key in INPUTS):
            pygame.draw.lines(screen, CYAN, False, FEED, 2)
        if state["powered"]:
            pygame.draw.lines(screen, GREEN, False, BRANCHES[state["route"]], 2)
            if state["route"] == "B":
                pygame.draw.lines(screen, GREEN, False, LIFT_CABLE, 2)
        for age in state["test_pulses"]:
            # An observable signal reaches the exposed break before the local fizzle.
            point = tuple(round(v) for v in along_path(BROKEN_CABLE, age / 27))
            pygame.draw.lines(screen, (62, 120, 130), False, [BROKEN_CABLE[0], point], 2)
            pygame.draw.circle(screen, CYAN, point, 5, 2)
            pygame.draw.circle(screen, INK, point, 2)
    elif floor == "B3":
        draw_sensor("scanner", state["scanner_on"], CYAN)
        draw_sensor("sensor", state["return_timer"] > 0, VIOLET)
        if state["scanner_on"]:
            pygame.draw.lines(screen, CYAN, False, SCANNER_WIRE, 2)
        # The short return-sensor lead follows the inside wall to its shutter contact.
        pygame.draw.lines(screen, VIOLET if state["return_timer"] else (78, 84, 90), False, SENSOR_WIRE, 2)
        for key, path in CONTACT_WIRES.items():
            if door_closed(key):
                pygame.draw.lines(screen, GREEN, False, path, 2)
        if exit_open():
            for path in POWER_WIRES:
                pygame.draw.lines(screen, GREEN, False, path, 2)
    elif floor == "B2":
        if state["service_open"]:
            pygame.draw.lines(screen, GREEN, False, SERVICE_WIRE, 2)
        color = CYAN if device_flashes.get("mirror2", 0) else (70, 107, 115)
        pygame.draw.lines(screen, color, False, REMOTE_WIRE, 2)
        if exit_open():
            pygame.draw.lines(screen, GREEN, False, LIFT_WIRE, 2)
    elif floor == "B1":
        powered, dim = state["charge"] > 0, (61, 75, 78)
        draw_wire(BATTERY_WIRE, CYAN if powered else dim)
        draw_wire(RETURN_WIRE, AMBER if state["drain_flash"] else dim)
        draw_wire(SIGNAL_WIRE, GREEN if exit_open() else dim)
        draw_wire(ACCESS_WIRE, CYAN if door_open("release_in") else dim)
        draw_wire(LIFT_WIRE, CYAN if state["mirror"] == 2 and not state["mirror_turn"] else dim)
        if powered or state["drain_flash"]:
            points = RETURN_WIRE if state["drain_flash"] else BATTERY_WIRE
            length = wire_length(points)
            for start in range(0, int(length), 90):
                position = wire_point(points, (start + ui_tick * 3) % length)
                pygame.draw.circle(screen, AMBER if state["drain_flash"] else CYAN, position, 2)
        for distance in state["pulses"]:
            for tail in range(5, -1, -1):
                point = wire_point(SIGNAL_WIRE, max(0, distance - tail * 5))
                pygame.draw.circle(screen, CYAN if tail else INK, point, 2 if tail else 4)
        for (x, y), life in state["sparks"]:
            for i in range(6):
                angle, radius = math.tau * i / 6 + life * .13, 2 + (18 - life) * .5
                pygame.draw.circle(screen, AMBER, (x + math.cos(angle) * radius, y + math.sin(angle) * radius), 1)
        color = AMBER if powered or state["drain_flash"] else MUTED
        for width, y in ((14, 419), (9, 423), (4, 427)):
            pygame.draw.line(screen, color, (128 - width / 2, y), (128 + width / 2, y), 1)
        # Visible inside-only sensor strip, with no directional arrows.
        area = pygame.Rect(563, 501, 46, 7)
        pygame.draw.rect(screen, (35, 46, 48), area, border_radius=2)
        for x in range(566, 608, 7):
            pygame.draw.line(screen, GREEN if occupied(obj["sensor"]) else MUTED, (x, 503), (x, 506), 1)


def draw_world():
    if floor == "B6":
        screen.blit(images["b6_room_revision1"], (0, 0))
        draw_circuits()
        # Ground contact depth orders both doors and actors. Farther objects draw first.
        items = [(obj[key].centery, "door", key) for key in ("gate", "lift")]
        items.append((obj["switch"].bottom, "device", None))
        items += [(pos[1], "actor", (pos, "active" if active else "faded"))
                  for pos, active in zip(ghost_positions, ghost_active) if pos is not None]
        items.append((py, "actor", (pose(), "player")))
        for _, kind, data in sorted(items, key=lambda item: item[0]):
            if kind == "door":
                draw_door(data)
            elif kind == "device":
                draw_device("switch")
            else:
                draw_actor(*data)
        draw_hud()
    elif floor == "B5":
        screen.blit(images["b5_room_revision1"], (0, 0))
        items = [(221, "door", "lift"), (602, "door", "shutter"),
                 (557, "wall", "north_wall"), (720, "wall", "south_wall")]
        items += [(obj[key].bottom, "device", key) for key in devices]
        items += [(pos[1], "actor", (pos, "active" if active else "faded"))
                  for pos, active in zip(ghost_positions, ghost_active) if pos is not None]
        items.append((py, "actor", (pose(), "player")))
        for _, kind, data in sorted(items, key=lambda item: item[0]):
            if kind == "door":
                draw_door(data)
            elif kind == "wall":
                screen.blit(room_parts[data], (0, 0))
            elif kind == "device":
                draw_device(data)
            else:
                draw_actor(*data)
        # Preserve the existing pulse's size, colour and white centre.
        for distance in state["pulses"]:
            point = tuple(round(v) for v in cable_point(distance))
            pygame.draw.circle(screen, CYAN, point, 9, 2)
            pygame.draw.circle(screen, INK, point, 4)
        for point, remaining in sparks:
            x, y = point
            radius = 5 + (30 - remaining) * .6
            for degrees in range(0, 360, 45):
                angle = math.radians(degrees)
                pygame.draw.line(screen, AMBER,
                                 (x + math.cos(angle) * radius, y + math.sin(angle) * radius),
                                 (x + math.cos(angle) * (radius + 5), y + math.sin(angle) * (radius + 5)), 2)
        draw_hud()
    elif floor == "B4":
        screen.blit(images["b4_room_revision1"], (0, 0))
        draw_circuits()
        items = [(224, "door", "lift"), (535, "wall", "divider")]
        for letter, depth in (("a", 536), ("b", 336)):
            items.append((depth, "door", "gate_" + letter))
            items += [(depth, "wall", letter + suffix)
                      for suffix in ("_left", "_right", "_post1", "_post2")]
        items += [(obj[key].bottom, "device", key) for key in devices]
        items += [(pos[1], "actor", (pos, "active" if active else "faded"))
                  for pos, active in zip(ghost_positions, ghost_active) if pos is not None]
        items.append((py, "actor", (pose(), "player")))
        for _, kind, data in sorted(items, key=lambda item: item[0]):
            if kind == "door":
                draw_door(data)
            elif kind == "wall":
                screen.blit(*room_parts[data])
                if "_post" in data:
                    gate = "gate_" + data[0]
                    x = room_parts[data][1].centerx
                    y = DOOR_ART[gate].top + 10
                    pygame.draw.circle(screen, GREEN if door_open(gate) else AMBER, (x, y), 2)
            elif kind == "device":
                draw_device(data)
            else:
                draw_actor(*data)
        for point, remaining in sparks:
            x, y = point
            radius = 3 + (30 - remaining) * .35
            for degrees in range(0, 360, 60):
                angle = math.radians(degrees)
                pygame.draw.line(screen, AMBER,
                                 (x + math.cos(angle) * radius, y + math.sin(angle) * radius),
                                 (x + math.cos(angle) * (radius + 4), y + math.sin(angle) * (radius + 4)), 2)
        draw_hud()
    elif floor == "B3":
        screen.blit(images["b3_room_revision1"], (0, 0))
        draw_circuits()
        items = [(224, "door", "lift"), (obj["terminal"].bottom, "device", "terminal")]
        items += [(503, "door", key) for key in doors]
        items += [(503, "wall", key) for key in room_parts if key != "terminal"]
        items += [(pos[1], "actor", (pos, "active" if active else "faded"))
                  for pos, active in zip(ghost_positions, ghost_active) if pos is not None]
        items.append((py, "actor", (pose(), "player")))
        for _, kind, data in sorted(items, key=lambda item: item[0]):
            if kind == "door":
                draw_door(data)
            elif kind == "wall":
                screen.blit(*room_parts[data])
                if data in ("out_left", "in_right"):
                    key = "archive_out" if data == "out_left" else "archive_in"
                    pygame.draw.circle(screen, GREEN if door_open(key) else AMBER,
                                       (room_parts[data][1].centerx, 458), 2)
            elif kind == "device":
                draw_device(data)
            else:
                draw_actor(*data)
        draw_hud()
    elif floor == "B2":
        screen.blit(images["b2_room_revision1"], (0, 0))
        draw_circuits()
        prepare_beams()
        screen.blit(beam_layer, (0, 0))
        items = [(224, "door", "lift"), (370, "door", "service")]
        items += [(obj[key].bottom, "device", key) for key in solids]
        wall_depths = {"divider": 498, "service_left": 370, "service_front": 370,
                       "service_right": 370, "right_barrier": 448}
        items += [(depth, "wall", key) for key, depth in wall_depths.items()]
        items += [(pos[1], "actor", (pos, "active" if active else "faded"))
                  for pos, active in zip(ghost_positions, ghost_active) if pos is not None]
        items.append((py, "actor", (pose(), "player")))
        for _, kind, data in sorted(items, key=lambda item: item[0]):
            if kind == "door":
                draw_door(data)
            elif kind == "wall":
                draw_wall(data)
            elif kind == "device":
                draw_device(data)
            else:
                draw_actor(*data)
        draw_hud()
    elif floor == "B1":
        screen.blit(images["b1_room_revision2"], (0, 0))
        draw_exit_light()
        draw_circuits()
        draw_optics()
        items = [(obj[key].bottom, "door", key) for key in (*doors, "lift")]
        items += [(obj[key].bottom, "device", key) for key in devices]
        items += [(depth, "wall", picture) for depth, picture in room_parts]
        items += [(pos[1], "actor", (pos, "active" if active else "faded"))
                  for pos, active in zip(ghost_positions, ghost_active) if pos is not None]
        items.append((py, "actor", (pose(), "player")))
        for _, kind, data in sorted(items, key=lambda item: item[0]):
            if kind == "door":
                draw_door(data)
            elif kind == "device":
                draw_device(data)
            elif kind == "wall":
                screen.blit(*data)
            else:
                draw_actor(*data)
        draw_hud()


def prepare_doors():
    global door_panels, exit_floor_light, exit_inside_light
    door_panels = {}
    for key, area in DOOR_ART.items():
        if floor == "B5" and key == "shutter":
            door_panels[key] = [images["b5_shutter_closed"].subsurface(area).copy()]
            continue
        left_width = (area.w + 1) // 2
        widths = (left_width, area.w - left_width)
        door_panels[key] = []
        for i, width in enumerate(widths):
            if floor == "B1":
                original = (lift_panels[i] if key == "lift" else
                            images["b1_gate_panels"].subsurface((40 + i * 440, 140, 440, 580)))
            else:
                original = images["b6_reference"].subsurface((369 + i * 114, 387, 114, 76))
            door_panels[key].append(pygame.transform.smoothscale(original, (width, area.h)))
    exit_floor_light = exit_inside_light = None
    if floor == "B1":
        area = DOOR_ART["lift"]
        exit_inside_light = pygame.Surface(area.size, pygame.SRCALPHA)
        for y in range(area.h):
            for x in range(area.w):
                side = max(0, 1 - (abs(x - area.w / 2) / (area.w / 2)) ** 4)
                alpha = round((95 + 95 * y / area.h) * side)
                exit_inside_light.set_at((x, y), (255, 241, 206, alpha))
        # A soft runtime light, independent of the painted floor and puzzle state.
        exit_floor_light = pygame.Surface((220, 210), pygame.SRCALPHA)
        for y in range(210):
            width = 35 + y * .27
            strength = (1 - y / 210) ** 1.6
            for x in range(220):
                side = max(0, 1 - abs(x - 110) / width)
                alpha = round(135 * strength * side ** .7)
                if alpha:
                    exit_floor_light.set_at((x, y), (255, 236, 187, alpha))


def setup_audio():
    global audio_channels, audio_levels, audio_tracks, audio_paused
    audio_channels, audio_levels, audio_tracks, audio_paused = {}, {}, {}, False
    if not pygame.mixer.get_init():
        return
    pygame.mixer.set_num_channels(24)
    pygame.mixer.set_reserved(len(AUDIO_FILES))
    for index, (name, filename) in enumerate(AUDIO_FILES.items()):
        track = pygame.mixer.Sound(str(ASSETS / filename))
        channel = pygame.mixer.Channel(index)
        channel.set_volume(0)
        if name != "surface":
            channel.play(track, loops=-1)
        audio_tracks[name] = track
        audio_channels[name], audio_levels[name] = channel, 0.0


def update_audio():
    if not audio_channels:
        return
    room_scale = {"title": .3, "thought": .28, "skill": .28,
                  "lift": .2, "failed": .35, "outside": 0}.get(scene, 1)
    music_scale = {"title": .65, "thought": .6, "skill": .6,
                   "failed": .45, "lift": 0, "outside": 0}.get(scene, 1)
    targets = {"music": MUSIC_VOLUME * music_scale,
               "lift_music": MUSIC_VOLUME * .65 if scene == "lift" else 0,
               "surface": MUSIC_VOLUME * 1.2 if scene == "outside" else 0,
               "hum": AMBIENCE_VOLUME * room_scale,
               "wind": WIND_VOLUME if scene == "outside" else 0}
    for name, channel in audio_channels.items():
        value, target = audio_levels[name], targets[name]
        value += max(-.004, min(.004, target - value))
        audio_levels[name] = value
        channel.set_volume(value)


def set_audio_focus(focused):
    global audio_paused
    if focused == (not audio_paused):
        return
    if pygame.mixer.get_init():
        # Pause SFX too; the whole simulation is paused when the window loses focus.
        pygame.mixer.unpause() if focused else pygame.mixer.pause()
    audio_paused = not focused


def draw_exit_light():
    if floor == "B1" and exit_floor_light is not None:
        amount = door_amounts["lift"]
        if amount > 0:
            exit_floor_light.set_alpha(round(255 * amount))
            screen.blit(exit_floor_light, (obj["lift"].centerx - 110, obj["lift"].bottom - 1))


def core_ready():
    return (state["lift_mode"] and state["charge"] > 0 and room_sealed()
            and state["release_cooldown"] == 0)


def reset_help():
    global manual_open, manual_tab, manual_scroll, manual_startup, help_progress
    global hint_fade, manual_max_scroll, manual_animation_time
    manual_open, manual_tab, manual_scroll, manual_startup = False, 0, 0, False
    hint_fade, manual_max_scroll, manual_animation_time = 0.0, 0, 0.0
    help_progress = {name: {"ticks": 0, "revealed": 0, "next": 60 * FPS} for name in FLOORS}


def hint_available():
    progress = help_progress[floor]
    return progress["revealed"] < len(HINTS[floor]) and progress["ticks"] >= progress["next"]


def open_manual(tab=0, startup=False):
    global manual_open, manual_tab, manual_scroll, manual_startup, pending_e, hint_fade, manual_animation_time
    manual_open, manual_tab, manual_scroll, manual_startup = True, tab, 0, startup
    manual_animation_time = 0.0
    # E already queued immediately before Esc still belongs to that game frame;
    # it is held until resuming, never consumed while reading the manual.
    hint_fade = 1.0 if hint_available() else 0.0


def close_manual():
    global manual_open, manual_startup
    manual_open, manual_startup = False, False


def reveal_hint():
    global manual_scroll, hint_fade
    if not manual_open or manual_tab != 2 or not hint_available():
        return False
    progress = help_progress[floor]
    progress["revealed"] += 1
    progress["next"] = progress["ticks"] + 60 * FPS
    hint_fade = 0.0
    # Focus the newly revealed clue, leaving every older clue accessible above.
    manual_scroll = max(0, hint_content_height() - MANUAL_BODY.h)
    sound("panel")
    return True


def manual_key(key):
    global manual_tab, manual_scroll, manual_animation_time
    if key == pygame.K_ESCAPE:
        close_manual()
    elif key == pygame.K_SPACE and manual_startup:
        close_manual()
    elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
        delta = -1 if key == pygame.K_LEFT else 1
        manual_tab = (manual_tab + delta) % 3
        manual_scroll = 0
        if manual_tab == 0:
            manual_animation_time = 0.0
    elif key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
        amount = 240 if key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) else 52
        if key in (pygame.K_UP, pygame.K_PAGEUP):
            amount = -amount
        manual_scroll = max(0, min(manual_max_scroll, manual_scroll + amount))
    elif key == pygame.K_h and manual_tab == 2:
        reveal_hint()
    # Space dismisses only the opening guide; the other game controls remain paused.
    return True


def scroll_manual(amount):
    global manual_scroll
    manual_scroll = max(0, min(manual_max_scroll, manual_scroll + amount))


def logical_point(point):
    w, h = window.get_size()
    scale = min(w / WIDTH, h / HEIGHT)
    return ((point[0] - (w - WIDTH * scale) / 2) / scale,
            (point[1] - (h - HEIGHT * scale) / 2) / scale)


def handle_click(point):
    global manual_tab, manual_scroll, manual_animation_time
    point = logical_point(point)
    if manual_open:
        if MANUAL_CLOSE.collidepoint(point):
            close_manual()
        else:
            for i, rect in enumerate(MANUAL_TABS):
                if rect.collidepoint(point):
                    manual_tab, manual_scroll = i, 0
                    if i == 0:
                        manual_animation_time = 0.0
            if manual_tab == 2 and HINT_BUTTON.collidepoint(point):
                reveal_hint()
        return True
    if scene == "title" and pygame.Rect(310, 406, 340, 50).collidepoint(point):
        start_game()
        return True
    if scene == "play" and pygame.Rect(773, 88, 166, 30).collidepoint(point) and hint_available():
        open_manual(2)
        reveal_hint()
        return True
    if scene == "play" and pygame.Rect(773, 55, 166, 33).collidepoint(point):
        open_manual()
        return True
    return False


def wrap_korean(words, width, size=20):
    # Prefer word boundaries; split by glyph only for a word wider than the row.
    lines, current = [], ""
    for word in words.split():
        candidate = (current + " " + word).strip()
        if fonts["ko"][size].size(candidate)[0] * .9 <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = ""
        for char in word:
            if current and fonts["ko"][size].size(current + char)[0] * .9 > width:
                lines.append(current)
                current = ""
            current += char
    if current:
        lines.append(current.rstrip())
    return lines


def hint_content_height():
    return sum(38 + 29 * len(wrap_korean(clue, 674)) for clue in
               HINTS[floor][:help_progress[floor]["revealed"]])


def guide_scene(stage, progress):
    """Draw a paused B6 example using its real background, gate, lever and sprites."""
    world = images["b6_room_revision1"].copy()
    if stage == 0:
        travel = min(1, max(0, (progress - .14) / .59))
        player = (480 - 312 * travel, 620 - 61 * travel)
        ghost = None
        gate_closed = min(1, max(0, (progress - .78) / .16))
    elif stage == 1:
        player = (168, 559) if progress < .45 else None if progress < .55 else (480, 620)
        ghost = None  # Saved recordings wait until the current player moves.
        gate_closed = 1 if progress < .55 else max(0, 1 - (progress - .55) / .17)
    else:
        player = (480 + 50 * min(1, progress / .23), 620)
        travel = min(1, max(0, (progress - .11) / .71))
        ghost = (480 - 312 * travel, 620 - 61 * travel) if progress > .11 else None
        gate_closed = min(1, max(0, (progress - .85) / .13))

    pygame.draw.lines(world, (22, 25, 28), False, [(138, 590), (145, 590), (145, 540)], 6)
    pygame.draw.lines(world, (134, 132, 117), False, [(137, 588), (145, 588), (145, 540)], 2)
    if gate_closed:
        old_clip = world.get_clip()
        world.set_clip((369, 387, 228, 76))
        offset = round(114 * (1 - gate_closed))
        for i in range(2):
            source = pygame.Rect(369 + i * 114, 387, 114, 76)
            world.blit(images["b6_reference"], (source.x + (-offset if i == 0 else offset), source.y), source)
        world.set_clip(old_clip)
    pygame.draw.rect(world, GREEN if gate_closed else AMBER, (364, 382, 3, 8))
    pygame.draw.rect(world, GREEN if gate_closed else AMBER, (602, 382, 3, 8))

    # Actors are ordered by their feet, as they are in B6 gameplay.
    actors = [(xy[1], xy, active) for xy, active in ((player, False), (ghost, True)) if xy]
    items = [(y, "actor", xy, active) for y, xy, active in actors]
    items.append((593, "lever", None, False))
    for _, kind, xy, active in sorted(items, key=lambda item: item[0]):
        if kind == "lever":
            world.blit(lever_image, lever_image.get_rect(midbottom=(123, 593)))
            pivot = (123, 538)
            tip = (135 if gate_closed >= .8 else 111, 521)
            pygame.draw.line(world, (19, 26, 31), pivot, tip, 7)
            pygame.draw.line(world, (179, 180, 170), pivot, tip, 4)
            pygame.draw.circle(world, GREEN if gate_closed >= .8 else RED, tip, 4)
        else:
            x, y = xy
            moving = (stage == 0 and .14 < progress < .73) or (stage == 2 and active and .11 < progress < .82)
            picture = (echoes if active else sprites)[("up", 1 if moving and int(progress * 18) % 2 else 0)]
            if not active:
                shadow = pygame.Surface((40, 12), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
                world.blit(shadow, (round(x) - 20, round(y) - 6))
            world.blit(picture, picture.get_rect(midbottom=(round(x), round(y))))
    if stage == 1 and .45 <= progress < .72:
        # Straight scanlines make the reset legible without a circular halo.
        flash = 1 - abs(progress - .56) / .16
        for x, y in (((168, 559) if progress < .55 else (480, 620)),):
            for dx in (-13, -4, 7, 16):
                tint = pygame.Surface((2, 70), pygame.SRCALPHA)
                tint.fill((*CYAN, round(130 * max(0, flash))))
                world.blit(tint, (x + dx, y - 78))
    return pygame.transform.smoothscale(world.subsurface(GUIDE_VIEW), GUIDE_SCENE_SIZE)


def guide_key(x, world_pos, letter):
    """Place the key above the character's head in the cropped game camera."""
    px = x + 3 + round((world_pos[0] - GUIDE_VIEW.x) * GUIDE_SCENE_SIZE[0] / GUIDE_VIEW.w)
    py = 300 + round((world_pos[1] - GUIDE_VIEW.y) * GUIDE_SCENE_SIZE[1] / GUIDE_VIEW.h)
    pygame.draw.rect(screen, (16, 27, 32), (px - 13, py - 59, 26, 23), border_radius=4)
    pygame.draw.rect(screen, CYAN, (px - 13, py - 59, 26, 23), 2, border_radius=4)
    text(letter, px, py - 48, 18, CYAN, "en", True, ink_center=True)


def draw_quick_guide(elapsed):
    """Play record, save/return and replay in order while gameplay is paused."""
    global manual_animation_time
    total = sum(GUIDE_DURATIONS)
    manual_animation_time = (manual_animation_time + elapsed) % total
    running = manual_animation_time
    stage = 0
    for duration in GUIDE_DURATIONS:
        if running < duration:
            progress = running / duration
            break
        running -= duration
        stage += 1
    cards = ((100, "01  R  기록", "움직임과 E 조작을 담아요"),
             (354, "02  R  저장", "다시 R: 출발점으로 이동"),
             (608, "03  이동하면 재생", "기록체가 행동을 반복해요"))
    for i, (x, heading, caption) in enumerate(cards):
        active = i == stage
        pygame.draw.rect(screen, (23, 35, 42), (x, 239, 236, 255), border_radius=7)
        pygame.draw.rect(screen, CYAN if active else (54, 75, 83), (x, 239, 236, 255),
                         2 if active else 1, border_radius=7)
        text(heading, x + 118, 273, 20, CYAN if active else (124, 178, 188),
             "ko", True, ink_center=True)
        phase = progress if active else 1 if i < stage else 0
        screen.blit(guide_scene(i, phase), (x + 3, 300))
        if not active:
            dim = pygame.Surface(GUIDE_SCENE_SIZE, pygame.SRCALPHA)
            dim.fill((8, 13, 18, 82))
            screen.blit(dim, (x + 3, 300))
        else:
            if i == 0:
                if progress < .14:
                    guide_key(x, (480, 620), "R")
                else:
                    pygame.draw.rect(screen, RED, (x + 11, 307, 5, 5))
                    text("REC", x + 22, 302, 16, INK)
                    if progress > .72:
                        guide_key(x, (168, 559), "E")
            elif i == 1:
                guide_key(x, (168, 559) if progress < .55 else (480, 620), "R")
            elif progress > .80:
                guide_key(x, (168, 559), "E")
        text(caption, x + 118, 483, 16, INK if active else MUTED,
             "ko", True, ink_center=True)
    text("WASD  이동     E  조작     R  기록 / 저장     Q  층 초기화", 472, 530,
         18, MUTED, "ko", True, ink_center=True)


def draw_manual(elapsed=0):
    global manual_max_scroll, manual_scroll, hint_fade
    if manual_startup:
        screen.fill((9, 12, 17))
    else:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((4, 8, 12, 205))
        screen.blit(shade, (0, 0))
    panel = pygame.Rect(62, 54, 836, 612)
    pygame.draw.rect(screen, (17, 24, 29), panel, border_radius=8)
    pygame.draw.rect(screen, (66, 85, 94), panel, 1, border_radius=8)
    text("사용 안내", 100, 78, 30, INK, "ko")
    text("읽는 동안 게임이 일시 정지됩니다.", 100, 120, 18, MUTED, "ko")
    pygame.draw.rect(screen, (38, 51, 58), MANUAL_CLOSE, border_radius=4)
    text("ESC  닫기", MANUAL_CLOSE.centerx, MANUAL_CLOSE.centery, 18, INK, "ko", True, ink_center=True)
    for i, (label, area) in enumerate(zip(("시작하기", "기록과 재생", "층별 힌트"), MANUAL_TABS)):
        active = manual_tab == i
        pygame.draw.rect(screen, (35, 59, 67) if active else (23, 33, 39), area, border_radius=4)
        text(label, area.centerx, area.centery, 22, CYAN if active else MUTED, "ko", True, ink_center=True)
    pygame.draw.line(screen, (53, 70, 79), (100, 207), (860, 207))
    old_clip = screen.get_clip()
    screen.set_clip(MANUAL_BODY)
    if manual_tab == 0:
        manual_max_scroll = 0
        draw_quick_guide(elapsed)
    elif manual_tab == 1:
        entries = MANUAL_RECORDING
        blocks = [(title, wrap_korean(body, 720)) for title, body in entries]
        total = sum(38 + 27 * len(lines) for _, lines in blocks)
        manual_max_scroll = max(0, total - MANUAL_BODY.h)
        manual_scroll = min(manual_scroll, manual_max_scroll)
        y = MANUAL_BODY.y - manual_scroll
        for i, (title, lines) in enumerate(blocks):
            text(f"{i + 1:02d}  {title}", 104, y, 20, CYAN, "ko")
            for j, line in enumerate(lines):
                text(line, 114, y + 29 + j * 27, 20, INK, "ko")
            y += 38 + 27 * len(lines)
    else:
        shown = help_progress[floor]["revealed"]
        manual_max_scroll = max(0, hint_content_height() - MANUAL_BODY.h)
        manual_scroll = min(manual_scroll, manual_max_scroll)
        y = MANUAL_BODY.y - manual_scroll
        if not shown:
            text("아직 확인한 힌트가 없습니다.", 110, y + 25, 22, INK, "ko")
            text("방을 살펴본 뒤, 필요할 때 아래 버튼을 눌러 보세요.", 110, y + 72, 20, MUTED, "ko")
        for i, clue in enumerate(HINTS[floor][:shown]):
            text(f"{floor}  ·  {i + 1:02d}", 105, y, 20, CYAN, "en")
            lines = wrap_korean(clue, 674)
            for j, line in enumerate(lines):
                text(line, 117, y + 29 + 29 * j, 20, INK, "ko")
            y += 38 + 29 * len(lines)
    screen.set_clip(old_clip)
    if manual_max_scroll:
        thumb_h = max(28, MANUAL_BODY.h ** 2 / (MANUAL_BODY.h + manual_max_scroll))
        ty = MANUAL_BODY.y + (MANUAL_BODY.h - thumb_h) * manual_scroll / manual_max_scroll
        pygame.draw.rect(screen, (37, 48, 54), (855, MANUAL_BODY.y, 3, MANUAL_BODY.h))
        pygame.draw.rect(screen, (103, 135, 146), (855, ty, 3, thumb_h))
    if manual_tab == 2:
        available = hint_available()
        hint_fade += ((1.0 if available else 0.0) - hint_fade) * min(1, elapsed * 8)
        shown, total = help_progress[floor]["revealed"], len(HINTS[floor])
        tint = tuple(round(a + (b - a) * hint_fade) for a, b in zip((69, 82, 89), CYAN))
        pygame.draw.rect(screen, (25, 34, 40), HINT_BUTTON, border_radius=4)
        pygame.draw.rect(screen, tint, HINT_BUTTON, 1, border_radius=4)
        label = "힌트 확인 완료" if shown == total else "H  새 힌트 확인"
        text(label, HINT_BUTTON.centerx, HINT_BUTTON.centery, 20, tint, "ko", True, ink_center=True)
        text(f"{floor} · {shown} / {total}", 106, 592, 20, MUTED)
        text("새 힌트는 1분 간격으로 확인할 수 있습니다.", 106, 622, 18, MUTED, "ko")
    else:
        footer = ("SPACE  계속하기   ·   ESC로 다시 볼 수 있어요" if manual_startup else
                  "↑↓ / 휠  스크롤" if manual_max_scroll else "필요할 때 ESC로 다시 확인할 수 있습니다.")
        text(footer, 105, 618, 18, MUTED, "ko")
    text("← →  페이지", 764, 641, 16, MUTED, "ko")


# pygbag runs this file directly in the browser; keep asyncio.run at top level
# and add nothing after it (no sys.exit / pygame.quit).
asyncio.run(main())
