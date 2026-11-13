# Worked example: a 95 s news explainer about a wave of company listings, cut from a talking-head video.
# The companies are made up. Times follow that example narration, so use this file as a pattern library:
# copy a scene, then replace its times with the word times in your own work/words.txt.
from lib import *  # noqa

TITLE = "Example - The listing race"
INPUT = "raw/example.mp4"
HAS_VIDEO = True
SCRIPT = None
LANG = "en"

DROPS = [(98.00, 110.25)]    # the speaker fluffed a line and said it again: drop the first take, keep the second
PAD = 0.10
MIN_PAUSE = 0.3

FACE_X, FACE_Y = 0.5, 0.26
FACES = [(6.30, 9.45), (24.65, 27.65), (30.40, 33.40), (52.50, 55.50)]

TOTAL = None
END_CARD = 2.25
SCENES = [(0.00, 6.30), (9.45, 14.50), (14.50, 21.50), (21.50, 24.65), (27.65, 30.40), (33.40, 38.70),
          (38.70, 45.90), (45.90, 52.50), (55.50, 65.20), (65.20, 71.70), (71.70, 75.80), (75.80, 81.40),
          (81.40, 90.40), (90.40, 95.50)]
WORLDS = [(0, "g"), (9.45, "n"), (14.5, "g"), (21.5, "n"), (27.65, "g"), (45.9, "n"), (71.7, "g"), (75.9, "r"), (81.5, "g")]
CAPS = [("c1", 0.12, 3.25), ("c2", 27.70, 30.40), ("c3", 87.10, 90.40)]


def scenes():
    S = {}
    S[0] = (cap("c1", ["Wall", "Street's", "biggest"], [0.12, 0.31, 0.99], ["IPO", "wave", "in", "*history"], [1.48, 1.71, 2.02, 2.18], top=78)
            + chart_card(360, 330, 1200, 560, 0.0, "M60 470 C 260 460, 380 430, 520 380 S 760 300, 880 220 S 1060 110, 1140 70",
                         0.15, 2.7, label="US IPOs", label_at=0.45, bars=26, bars_at=1.71, cid="ch1")
            + f'<div id="rk1" class="rocket" style="left:1460px;top:1120px">{ico("rocket", 170, "rk")}<i class="flame"></i></div>'
            + pill("Founder-led", 1480, 560, 3.74, "g", "person"))
    S[1] = lanes(420, 160, [("Northstar", "rocket", 9.49, "g"), ("Helix AI", "hex", 11.06, ""), ("Cirrus Labs", "chip", 12.12, "")],
                 finish_at=9.5, finish_label="Listing", go_at=13.5, go_x=[1080, 820, 760])
    S[2] = (pill("Bank forecast", 180, 150, 14.55, "", "bank")
            + glass(360, 280, 1200, 640, 14.6,
                    bar(760, 70, 200, 440, 0, 18.10)
                    + '<div class="lbl" style="position:absolute;left:700px;top:590px;width:320px;text-align:center" data-at="16.4" data-fx="in">US IPO proceeds</div>'
                    + bignum(80, 150, 18.62, counter(160, 18.66, 1.0, "$", "B"))
                    + pill("Record", 90, 70, 18.10, "g sm", "up")
                    + '<div class="year" style="left:96px;top:380px" data-at="20.29" data-fx="tilt">in <b>2026</b></div>'))
    S[3] = (doc(820, 200, 21.55, "IPO filing", "Draft", "FILED", 23.22, "Submit", did="dk")
            + cursor("cu1", 1500, 900, 1270, 825, 22.2, 23.17))
    S[4] = (cap("c2", ["The", "biggest", "stock", "market"], [27.70, 27.80, 28.22, 28.49], ["listing", "in", "*history"], [29.06, 29.47, 29.84], top=70)
            + floor(27.65) + line("M180 900 L420 840 L560 870 L760 760 L900 790 L1120 600 L1260 640 L1500 420 L1620 300", 27.75, 2.0, "thick")
            + beam(1520, 200, 29.0) + badge(1530, 180, 29.06, "#1"))
    S[5] = (line("M120 960 C 600 940, 900 760, 1200 640 S 1700 300, 1840 160", 33.45, 5.0, "faint")
            + stat(250, 330, 33.42, "Aiming to raise", counter(75, 33.45, 0.9, "$", "B"), "rocket")
            + stat(1030, 330, 35.44, "Valuation nearing", counter(2, 36.79, 0.6, "~$", "T"), "up"))
    S[6] = (hbar(260, 520, "Northstar raise", 38.83, 560, 42.66, 1300, "rocket", bid="hb7")
            + threshold(1180, 39.80, 44.46, "th7")
            + f'<div class="pill" style="left:1060px;top:300px" data-at="39.80" data-fx="pop"><span>{counter(25.6, 39.82, 0.8, "$", "B", 1)}</span></div>'
            + pill("Previous IPO record", 1000, 810, 43.27, "", "drop"))
    S[7] = (timeline(260, 1660, 600, 46.05, 48.3, 51.8, "d8")
            + cal(420, 300, 47.64, "JUN", "4") + pill("Roadshow", 400, 680, 46.04, "", "mic")
            + cal(1290, 300, 51.92, "JUN", "11", "g") + pill("Listing", 1300, 680, 49.21, "g", "bell")
            + pill("As early as", 1250, 190, 50.84, "sm dim"))
    S[8] = (blob(330, 300, 1.25, "", 55.55, "up", "bl9") + pill("The CEO", 280, 700, 55.6, "", "person") + pill("Helix AI", 330, 800, 56.90, "", "hex")
            + pill("Reportedly", 520, 330, 57.81, "sm dim")
            + glass(820, 240, 900, 600, 58.55,
                    '<div class="chip" style="left:80px;top:70px">IPO</div>'
                    + pill("Chatbot maker", 430, 80, 61.84, "", "chat")
                    + line("M60 520 C 300 500, 420 420, 560 360 S 780 220, 850 170", 60.71, 2.6, "", "0 0 900 600", False)
                    + bignum(70, 250, 63.47, counter(1, 63.51, 0.5, "~$", "T"))))
    S[9] = (tile(300, 250, 65.39, "chip", "AI startup") + tile(1380, 250, 66.13, "cloud", "Cloud")
            + f'<div class="pill xl" style="left:735px;top:300px" data-at="67.27" data-fx="stamp">{ico("chip", 56)}<span>Cirrus Labs</span></div>'
            + progress(460, 640, 68.9, 69.02, 2.6, 0.72, "Preparing") + pill("Possible market debut", 1080, 730, 70.48, "sm", "bell"))
    S[10] = orbit([("Northstar", "rocket"), ("Helix AI", "hex"), ("Cirrus Labs", "chip")], 71.7, 4.3, "IPO", "super cycle") + crowd(73.71)
    S[11] = (f'<div {shake("rk12", 79.93)}>' + warn(300, 250, 76.10, "Risks remain") + globe(760, 250, 77.06, "Geopolitics")
             + glass(1180, 240, 560, 420, 78.80,
                     line("M30 210 L70 120 L110 280 L150 90 L190 300 L230 140 L270 330 L310 110 L350 290 L390 170 L430 360 L470 220 L530 380",
                          78.88, 0.9, "red", "0 0 560 420", False)
                     + '<div class="lbl" style="position:absolute;left:30px;top:24px">Volatility</div>')
             + pill("Wall Street", 1300, 760, 80.43, "r", "bank") + '</div>')
    S[12] = (cap("c3", ["The", "IPO", "race", "of", "the", "*decade"], [87.10, 87.38, 87.66, 88.03, 88.26, 88.51], ["has", "officially", "*begun"], [89.10, 89.32, 89.90], top=70)
             + '<div class="flash" data-flash="81.6"></div>'
             + lanes(520, 160, [("Northstar", "rocket", 83.65, "g"), ("Helix AI", "hex", 84.33, ""), ("Cirrus Labs", "chip", 85.04, "")],
                     finish_x=1660, finish_at=86.17, go_at=89.90, go_x=[1150, 960, 900], rid="r13", lane_at=81.7)
             + pill("Wall Street", 1500, 330, 86.17, "g", "bank"))
    S[13] = (floor(90.4) + line("M120 990 L360 930 L520 960 L740 850 L880 880 L1100 770 L1240 800 L1480 660 L1600 700 L1820 430", 90.45, 3.2, "thick")
             + button(660, 420, 91.02, "Subscribe", "bell", "fb", 91.47) + cursor("cu14", 1500, 860, 1180, 530, 91.05, 91.45))
    return S


CUSTOM_JS = """
tl.fromTo("#rk1",{x:0,y:0,rotation:28},{x:-240,y:-760,rotation:28,duration:.95,ease:"expo.out",immediateRender:false},3.7);
tl.fromTo("#rk1 .flame",{scaleY:.7},{scaleY:1.25,duration:.12,yoyo:true,repeat:21,ease:"sine.inOut",immediateRender:false},3.7);
tl.to("#rk1",{x:-20,y:-930,duration:.7,ease:"power3.inOut"},4.92);
tl.to("#rk1",{x:20,y:-990,duration:1.2,ease:"none"},5.62);
tl.to("#ch1",{x:-330,y:150,scale:.7,opacity:.5,duration:.8,ease:"expo.inOut"},3.15);
tl.to("#rc0",{x:110,duration:.45,ease:"back.out(1.6)"},10.19);
"""

CUES = [(0.05, "rise"), (5.5, "impact"), (9.3, "swish"), (14.4, "swish2"), (18.66, "bell"), (23.17, "click"),
        (24.5, "swish"), (29.06, "bell2"), (33.3, "swish2"), (34.4, "bell"), (38.6, "swish"), (44.46, "swell"),
        (45.8, "swish2"), (51.92, "bell"), (55.4, "swish"), (63.6, "bell2"), (65.1, "swish2"), (71.6, "swish"),
        (75.85, "down"), (81.4, "swish2"), (89.9, "impact"), (91.45, "click"), (93.2, "swell")]
MUSIC = None
MUSIC_VARIANT = 2
